"""T-12 (SPEC §12) và Gate 4: outbox, dispatcher, worker, retry, đối soát.

Worker chạy qua đúng các hàm async mà task Celery bọc lại, với session riêng
(chỉ thấy dữ liệu đã commit, như container worker thật). Broker và SMTP được
thay bằng hàm/đối tượng giả để tạo lỗi theo ý muốn; PostgreSQL là thật.
"""

from __future__ import annotations

import re
import uuid
from urllib.parse import unquote

import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.common.enums import EmailDeliveryStatus, JobStatus, JobType, OutboxStatus
from app.integrations.email.service import (
    EmailRejectedError,
    EmailUnavailableError,
    OutgoingEmail,
)
from app.integrations.file_storage.service import LocalFileStorage
from app.modules.notifications import repository as notifications_repository
from app.modules.notifications import service as notifications_service
from app.modules.notifications.exceptions import JobErrorCode
from app.modules.notifications.repository import JobRow
from app.workers.dispatcher import dispatch_outbox
from app.workers.handlers import JOB_HANDLERS
from app.workers.runner import JobOutcome, process_job, reconcile_jobs
from tests.integration import factories as f


pytestmark = [pytest.mark.integration]

SessionFactory = async_sessionmaker[AsyncSession]


class FakeEmailSender:
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error
        self.sent: list[OutgoingEmail] = []

    def send(self, message: OutgoingEmail) -> str:
        if self.error is not None:
            raise self.error
        self.sent.append(message)
        return f"<fake-{len(self.sent)}@test>"


class FakeBroker:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.published: list[uuid.UUID] = []

    def publish(self, job_id: uuid.UUID) -> None:
        if self.fail:
            raise ConnectionError("Redis không kết nối được")
        self.published.append(job_id)


async def _run(
    session_factory: SessionFactory,
    job_id: uuid.UUID,
    sender: FakeEmailSender,
    storage: LocalFileStorage,
) -> JobOutcome:
    return await process_job(
        job_id,
        session_factory=session_factory,
        handlers=JOB_HANDLERS,
        email_sender=sender,
        storage=storage,
    )


async def _request_reset(client: httpx.AsyncClient, db_session: AsyncSession) -> JobRow:
    """Tạo user rồi gọi API quên mật khẩu; trả job email duy nhất vừa sinh."""
    email = f"reset-{uuid.uuid4().hex[:8]}@example.com"
    await f.make_user(db_session, email=email)
    await db_session.commit()
    response = await client.post("/api/v1/auth/password-reset/request", json={"email": email})
    assert response.status_code == 200
    jobs = await _jobs(db_session)
    assert len(jobs) == 1
    return jobs[0]


async def _jobs(db: AsyncSession) -> list[JobRow]:
    ids = (await db.execute(text("SELECT id FROM jobs ORDER BY created_at"))).scalars().all()
    return [row for job_id in ids if (row := await notifications_repository.get_job(db, job_id))]


async def _job(db: AsyncSession, job_id: uuid.UUID) -> JobRow:
    job = await notifications_repository.get_job(db, job_id)
    assert job is not None
    return job


async def _outbox(db: AsyncSession, job_id: uuid.UUID) -> dict:
    rows = (
        (
            await db.execute(
                text(
                    "SELECT status, attempts, published_at, "
                    "EXTRACT(EPOCH FROM available_at - clock_timestamp()) AS due_in "
                    "FROM outbox_events WHERE job_id = :job_id"
                ),
                {"job_id": job_id},
            )
        )
        .mappings()
        .all()
    )
    assert len(rows) == 1, "mỗi job đúng một outbox event"
    return dict(rows[0])


async def _count(db: AsyncSession, table: str) -> int:
    return int(await db.scalar(text(f"SELECT COUNT(*) FROM {table}")) or 0)  # noqa: S608


async def _make_due(db: AsyncSession) -> None:
    """Bỏ qua backoff thay vì sleep trong test."""
    await db.execute(text("UPDATE outbox_events SET available_at = now()"))
    await db.commit()


async def _age_running_jobs(db: AsyncSession, minutes: int = 10) -> None:
    await db.execute(
        text("UPDATE jobs SET updated_at = now() - make_interval(mins => :m)"), {"m": minutes}
    )
    await db.commit()


# --- tạo job cùng transaction ------------------------------------------------------


async def test_reset_tao_job_outbox_email_cung_transaction_khong_chua_token(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    job = await _request_reset(client, db_session)

    assert job.job_type == JobType.SEND_EMAIL
    assert job.status == JobStatus.PENDING
    # Người gọi chưa đăng nhập: job hệ thống, không ai dò được qua GET /jobs.
    assert job.requested_by is None
    assert set(job.payload) == {"template_code", "user_id"}
    assert (await _outbox(db_session, job.id))["status"] == OutboxStatus.PENDING

    delivery = await notifications_repository.get_email_delivery_by_job(db_session, job.id)
    assert delivery is not None
    assert delivery.status == EmailDeliveryStatus.PENDING
    assert delivery.template_code == "password_reset"
    # Token chỉ được worker sinh lúc gửi.
    assert await _count(db_session, "password_reset_tokens") == 0

    # Email không tồn tại: cùng response, không tạo job.
    response = await client.post(
        "/api/v1/auth/password-reset/request", json={"email": "khong-co@example.com"}
    )
    assert response.status_code == 200
    assert await _count(db_session, "jobs") == 1


async def test_payload_chua_secret_bi_tu_choi(db_session: AsyncSession) -> None:
    with pytest.raises(ValueError, match="nhạy cảm"):
        await notifications_service.enqueue_job(
            db_session,
            job_type=JobType.SEND_EMAIL,
            idempotency_key="k-secret",
            requested_by=None,
            payload={"nested": {"otp": "123456"}},
        )


async def test_idempotency_key_trung_khong_tao_job_thu_hai(db_session: AsyncSession) -> None:
    user = await f.make_user(db_session)
    kwargs = {
        "template_code": "password_reset",
        "recipient_email": user.email,
        "recipient_user_id": user.id,
        "requested_by": None,
        "idempotency_key": "email:test:same-key",
        "payload": {"user_id": str(user.id)},
    }
    first = await notifications_service.enqueue_email(db_session, **kwargs)
    second = await notifications_service.enqueue_email(db_session, **kwargs)
    await db_session.commit()

    assert first.id == second.id
    assert await _count(db_session, "jobs") == 1
    assert await _count(db_session, "outbox_events") == 1
    assert await _count(db_session, "email_deliveries") == 1


# --- end-to-end qua dispatcher và worker -----------------------------------------


async def test_email_reset_end_to_end_lien_ket_dung_duoc(
    client: httpx.AsyncClient,
    db_session: AsyncSession,
    session_factory: SessionFactory,
    file_storage: LocalFileStorage,
) -> None:
    job = await _request_reset(client, db_session)
    broker, sender = FakeBroker(), FakeEmailSender()

    result = await dispatch_outbox(session_factory=session_factory, publish=broker.publish)
    assert result.published == 1
    assert broker.published == [job.id]
    outbox = await _outbox(db_session, job.id)
    assert outbox["status"] == OutboxStatus.PUBLISHED
    assert outbox["published_at"] is not None

    # Dispatcher chạy lại không publish sự kiện đã published.
    again = await dispatch_outbox(session_factory=session_factory, publish=broker.publish)
    assert again.published == 0
    assert broker.published == [job.id]

    assert await _run(session_factory, job.id, sender, file_storage) == JobOutcome.SUCCEEDED
    done = await _job(db_session, job.id)
    assert done.status == JobStatus.SUCCEEDED
    assert done.attempts == 1
    assert done.finished_at is not None

    delivery = await notifications_repository.get_email_delivery_by_job(db_session, job.id)
    assert delivery is not None
    assert delivery.status == EmailDeliveryStatus.SENT
    assert delivery.provider_message_id == "<fake-1@test>"

    assert len(sender.sent) == 1
    message = sender.sent[0]
    assert message.to == delivery.recipient_email
    match = re.search(r"reset-password\?token=(\S+)", message.text_body)
    assert match is not None
    token = unquote(match.group(1))

    confirm = await client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": token, "new_password": "MatKhauMoi123456"},
    )
    assert confirm.status_code == 200


# --- Redis lỗi sau commit ------------------------------------------------------------


async def test_redis_loi_sau_commit_outbox_con_nguyen_va_phat_lai(
    client: httpx.AsyncClient,
    db_session: AsyncSession,
    session_factory: SessionFactory,
) -> None:
    job = await _request_reset(client, db_session)

    down = FakeBroker(fail=True)
    result = await dispatch_outbox(session_factory=session_factory, publish=down.publish)
    assert (result.published, result.failed) == (0, 1)

    outbox = await _outbox(db_session, job.id)
    assert outbox["status"] == OutboxStatus.PENDING
    assert outbox["attempts"] == 1
    assert outbox["published_at"] is None
    assert outbox["due_in"] > 0, "publish lỗi phải lùi lịch, không quay vòng ngay"
    # Thay đổi nghiệp vụ đã commit không bị ảnh hưởng.
    assert (await _job(db_session, job.id)).status == JobStatus.PENDING
    assert await _count(db_session, "audit_logs") == 1

    # Chưa đến hạn: dispatcher bỏ qua.
    up = FakeBroker()
    assert (
        await dispatch_outbox(session_factory=session_factory, publish=up.publish)
    ).published == 0

    await _make_due(db_session)
    assert (
        await dispatch_outbox(session_factory=session_factory, publish=up.publish)
    ).published == 1
    assert up.published == [job.id]
    assert await _count(db_session, "jobs") == 1


async def test_lease_het_han_duoc_dispatcher_khac_lay_lai(
    client: httpx.AsyncClient,
    db_session: AsyncSession,
    session_factory: SessionFactory,
) -> None:
    """Dispatcher chết sau khi nhận lease, trước khi publish."""
    job = await _request_reset(client, db_session)
    await db_session.execute(
        text(
            "UPDATE outbox_events SET status = 'publishing', "
            "locked_until = now() + interval '1 minute'"
        )
    )
    await db_session.commit()

    broker = FakeBroker()
    assert (
        await dispatch_outbox(session_factory=session_factory, publish=broker.publish)
    ).published == 0

    await db_session.execute(
        text("UPDATE outbox_events SET locked_until = now() - interval '1 second'")
    )
    await db_session.commit()
    assert (
        await dispatch_outbox(session_factory=session_factory, publish=broker.publish)
    ).published == 1
    assert broker.published == [job.id]


async def test_broker_mat_message_doi_soat_phat_lai(
    client: httpx.AsyncClient,
    db_session: AsyncSession,
    session_factory: SessionFactory,
) -> None:
    job = await _request_reset(client, db_session)
    await dispatch_outbox(session_factory=session_factory, publish=FakeBroker().publish)

    # Mới publish: chưa coi là mất.
    assert (await reconcile_jobs(session_factory=session_factory)).republished == 0

    await db_session.execute(
        text("UPDATE outbox_events SET published_at = now() - interval '10 minutes'")
    )
    await db_session.commit()
    assert (await reconcile_jobs(session_factory=session_factory)).republished == 1
    assert (await _outbox(db_session, job.id))["status"] == OutboxStatus.PENDING

    broker = FakeBroker()
    await dispatch_outbox(session_factory=session_factory, publish=broker.publish)
    assert broker.published == [job.id]


# --- SMTP lỗi: retry có backoff, hết lượt thì failed, retry thủ công ------------


async def test_smtp_loi_retry_backoff_roi_failed_va_retry_thu_cong(
    client: httpx.AsyncClient,
    db_session: AsyncSession,
    session_factory: SessionFactory,
    file_storage: LocalFileStorage,
) -> None:
    job = await _request_reset(client, db_session)
    smtp_down = FakeEmailSender(error=EmailUnavailableError("connection refused"))

    assert (
        await _run(session_factory, job.id, smtp_down, file_storage) == JobOutcome.RETRY_SCHEDULED
    )
    after_first = await _job(db_session, job.id)
    assert (after_first.status, after_first.attempts) == (JobStatus.PENDING, 1)
    assert after_first.error_code == JobErrorCode.SMTP_UNAVAILABLE
    outbox = await _outbox(db_session, job.id)
    assert outbox["status"] == OutboxStatus.PENDING
    assert 3 < outbox["due_in"] <= 5

    assert (
        await _run(session_factory, job.id, smtp_down, file_storage) == JobOutcome.RETRY_SCHEDULED
    )
    assert 13 < (await _outbox(db_session, job.id))["due_in"] <= 15

    assert await _run(session_factory, job.id, smtp_down, file_storage) == JobOutcome.FAILED
    failed = await _job(db_session, job.id)
    assert (failed.status, failed.attempts) == (JobStatus.FAILED, 3)
    assert failed.error_code == JobErrorCode.SMTP_UNAVAILABLE
    delivery = await notifications_repository.get_email_delivery_by_job(db_session, job.id)
    assert delivery is not None
    assert delivery.status == EmailDeliveryStatus.FAILED
    # Mỗi lần thử sinh token mới và thu hồi token cũ: chỉ còn một token dùng được.
    live_tokens = await db_session.scalar(
        text("SELECT COUNT(*) FROM password_reset_tokens WHERE used_at IS NULL")
    )
    assert live_tokens == 1

    # Job hệ thống: chỉ người có job.manage retry được.
    admin = await f.make_actor(db_session, role_code="admin", permission_codes=("job.manage",))
    await db_session.commit()
    response = await client.post(f"/api/v1/jobs/{job.id}/retry", headers=f.auth_headers(admin))
    assert response.status_code == 200
    body = response.json()
    assert (body["status"], body["attempts"], body["error_code"]) == ("pending", 0, None)

    retried_outbox = await _outbox(db_session, job.id)
    assert retried_outbox["status"] == OutboxStatus.PENDING
    assert retried_outbox["due_in"] <= 0
    audit_action = await db_session.scalar(
        text("SELECT action FROM audit_logs WHERE entity_type = 'jobs' AND entity_id = :id"),
        {"id": job.id},
    )
    assert audit_action == "job.retry"

    sender = FakeEmailSender()
    assert await _run(session_factory, job.id, sender, file_storage) == JobOutcome.SUCCEEDED
    assert len(sender.sent) == 1
    # Retry giữ nguyên job ID và idempotency key, không tạo job mới.
    assert await _count(db_session, "jobs") == 1

    # Retry job đã succeeded bị chặn.
    again = await client.post(f"/api/v1/jobs/{job.id}/retry", headers=f.auth_headers(admin))
    assert again.status_code == 409
    assert again.json()["error"]["code"] == "INVALID_STATE"


async def test_loi_vinh_vien_failed_ngay_khong_cho_retry(
    client: httpx.AsyncClient,
    db_session: AsyncSession,
    session_factory: SessionFactory,
    file_storage: LocalFileStorage,
) -> None:
    job = await _request_reset(client, db_session)
    rejected = FakeEmailSender(error=EmailRejectedError("550 mailbox unavailable"))

    assert await _run(session_factory, job.id, rejected, file_storage) == JobOutcome.FAILED
    failed = await _job(db_session, job.id)
    assert (failed.attempts, failed.error_code) == (1, JobErrorCode.EMAIL_REJECTED)

    admin = await f.make_actor(db_session, role_code="admin", permission_codes=("job.manage",))
    await db_session.commit()
    response = await client.post(f"/api/v1/jobs/{job.id}/retry", headers=f.auth_headers(admin))
    assert response.status_code == 409


async def test_job_type_chua_co_handler_failed(
    db_session: AsyncSession, session_factory: SessionFactory, file_storage: LocalFileStorage
) -> None:
    job = await notifications_service.enqueue_job(
        db_session,
        job_type=JobType.EXPORT_DATA,
        idempotency_key="export:test",
        requested_by=None,
        payload={},
    )
    await db_session.commit()

    assert await _run(session_factory, job.id, FakeEmailSender(), file_storage) == JobOutcome.FAILED
    assert (await _job(db_session, job.id)).error_code == JobErrorCode.UNSUPPORTED_JOB_TYPE


# --- worker chết giữa job, job lặp --------------------------------------------------


async def test_worker_chet_giua_job_doi_soat_chay_lai_mot_lan(
    client: httpx.AsyncClient,
    db_session: AsyncSession,
    session_factory: SessionFactory,
    file_storage: LocalFileStorage,
) -> None:
    job = await _request_reset(client, db_session)
    # Worker nhận job rồi chết trước khi gửi thư.
    async with session_factory() as db:
        assert await notifications_repository.claim_job(db, job.id) is not None
        await db.commit()

    # Còn trong hạn heartbeat: không coi là chết.
    assert (await reconcile_jobs(session_factory=session_factory)).requeued == 0

    await _age_running_jobs(db_session)
    result = await reconcile_jobs(session_factory=session_factory)
    assert (result.requeued, result.failed) == (1, 0)
    lost = await _job(db_session, job.id)
    assert (lost.status, lost.error_code) == (JobStatus.PENDING, JobErrorCode.WORKER_LOST)
    assert (await _outbox(db_session, job.id))["status"] == OutboxStatus.PENDING

    sender = FakeEmailSender()
    assert await _run(session_factory, job.id, sender, file_storage) == JobOutcome.SUCCEEDED
    # Message cũ bị broker giao lại sau khi worker khởi động: không gửi lần hai.
    assert await _run(session_factory, job.id, sender, file_storage) == JobOutcome.SKIPPED
    assert len(sender.sent) == 1
    assert await _count(db_session, "email_deliveries") == 1
    assert (await _job(db_session, job.id)).attempts == 2


async def test_worker_chet_sau_khi_gui_khong_gui_lai(
    client: httpx.AsyncClient,
    db_session: AsyncSession,
    session_factory: SessionFactory,
    file_storage: LocalFileStorage,
) -> None:
    """Thư đã gửi và ghi `sent`, worker chết trước khi đóng job."""
    job = await _request_reset(client, db_session)
    async with session_factory() as db:
        await notifications_repository.claim_job(db, job.id)
        delivery = await notifications_repository.get_email_delivery_by_job(db, job.id)
        assert delivery is not None
        await notifications_repository.mark_email_sent(db, delivery.id, provider_message_id="<x>")
        await db.commit()

    await _age_running_jobs(db_session)
    await reconcile_jobs(session_factory=session_factory)

    sender = FakeEmailSender()
    assert await _run(session_factory, job.id, sender, file_storage) == JobOutcome.SUCCEEDED
    assert sender.sent == []


async def test_worker_mat_tin_hieu_het_luot_thanh_failed(
    client: httpx.AsyncClient,
    db_session: AsyncSession,
    session_factory: SessionFactory,
) -> None:
    job = await _request_reset(client, db_session)
    await db_session.execute(
        text("UPDATE jobs SET status = 'running', attempts = max_attempts WHERE id = :id"),
        {"id": job.id},
    )
    await db_session.commit()
    await _age_running_jobs(db_session)

    result = await reconcile_jobs(session_factory=session_factory)
    assert (result.requeued, result.failed) == (0, 1)
    failed = await _job(db_session, job.id)
    assert (failed.status, failed.error_code) == (JobStatus.FAILED, JobErrorCode.WORKER_LOST)
    # WORKER_LOST là lỗi tạm thời: vẫn được retry thủ công.
    assert notifications_service.is_retryable(failed)


async def test_job_succeeded_nhan_trung_khong_nhan_doi(
    client: httpx.AsyncClient,
    db_session: AsyncSession,
    session_factory: SessionFactory,
    file_storage: LocalFileStorage,
) -> None:
    job = await _request_reset(client, db_session)
    sender = FakeEmailSender()

    assert await _run(session_factory, job.id, sender, file_storage) == JobOutcome.SUCCEEDED
    for _ in range(3):
        assert await _run(session_factory, job.id, sender, file_storage) == JobOutcome.SKIPPED

    assert len(sender.sent) == 1
    assert await _count(db_session, "password_reset_tokens") == 1
    assert (await _job(db_session, job.id)).attempts == 1
