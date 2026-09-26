"""Use case tác vụ nền và email (SPEC SP-07, PLAN task 4.1, UC-22).

`enqueue_job`/`enqueue_email` được module khác gọi **bên trong transaction
nghiệp vụ của chúng** và không commit: job, outbox và thay đổi nghiệp vụ cùng
commit hoặc cùng rollback. Không gọi broker ở đây — dispatcher trong worker đọc
outbox và publish, nên Redis lỗi lúc commit không làm mất job (T-12).
"""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import EmailDeliveryStatus, JobStatus, JobType
from app.common.schemas.pagination import Page
from app.common.utils import expect
from app.common.utils.pagination import PageParams
from app.core.exceptions import invalid_state
from app.core.logging import SENSITIVE_KEYS
from app.modules.audit_logs.service import record_audit
from app.modules.notifications import repository as notifications_repository
from app.modules.notifications.exceptions import DEFAULT_MAX_ATTEMPTS, RETRYABLE_ERROR_CODES
from app.modules.notifications.permissions import ensure_can_list_all, ensure_job_scope
from app.modules.notifications.repository import JobRow
from app.modules.notifications.schemas import JobAccepted, JobScope, JobView
from app.modules.users.repository import UserRow


JOBS_PATH = "/api/v1/jobs"


def _ensure_no_secrets(payload: Mapping[str, Any]) -> None:
    """Payload chỉ chứa tham chiếu và bộ lọc (ERD mục 4); token/OTP/mật khẩu thô
    không bao giờ được ghi vào job — worker tự sinh khi xử lý (SPEC SP-01/SP-04)."""
    for key, value in payload.items():
        if key.lower() in SENSITIVE_KEYS:
            raise ValueError(f"Payload job không được chứa trường nhạy cảm: {key}")
        if isinstance(value, Mapping):
            _ensure_no_secrets(value)


def is_retryable(job: JobRow) -> bool:
    return job.status == JobStatus.FAILED and job.error_code in RETRYABLE_ERROR_CODES


def to_view(job: JobRow) -> JobView:
    return JobView(
        id=job.id,
        job_type=job.job_type,
        status=job.status,
        requested_by=job.requested_by,
        attempts=job.attempts,
        max_attempts=job.max_attempts,
        error_code=job.error_code,
        retryable=is_retryable(job),
        input_file_id=job.input_file_id,
        output_file_id=job.output_file_id,
        created_at=job.created_at,
        updated_at=job.updated_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
    )


def to_accepted(job: JobRow) -> JobAccepted:
    return JobAccepted(job_id=job.id, status=job.status, status_url=f"{JOBS_PATH}/{job.id}")


async def enqueue_job(
    db: AsyncSession,
    *,
    job_type: JobType,
    idempotency_key: str,
    requested_by: uuid.UUID | None,
    payload: Mapping[str, Any],
    input_file_id: uuid.UUID | None = None,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
) -> JobRow:
    """Tạo job + outbox trong transaction của caller. Gọi lại cùng
    `idempotency_key` trả job đã có và không tạo thêm outbox (SPEC SP-07)."""
    _ensure_no_secrets(payload)
    job = await notifications_repository.insert_job(
        db,
        job_type=job_type.value,
        idempotency_key=idempotency_key,
        requested_by=requested_by,
        payload=payload,
        input_file_id=input_file_id,
        max_attempts=max_attempts,
    )
    if job is None:
        return expect(
            await notifications_repository.get_job_by_idempotency_key(db, idempotency_key)
        )

    await notifications_repository.insert_outbox_event(db, job_id=job.id, event_key=f"job:{job.id}")
    return job


async def enqueue_email(
    db: AsyncSession,
    *,
    template_code: str,
    recipient_email: str,
    recipient_user_id: uuid.UUID | None,
    requested_by: uuid.UUID | None,
    idempotency_key: str,
    payload: Mapping[str, Any] | None = None,
) -> JobRow:
    """Một job cho đúng một người nhận; gửi hai bên hợp đồng thì gọi hai lần
    (ERD mục 4). `recipient_email` là snapshot nơi nhận lúc tạo job."""
    job = await enqueue_job(
        db,
        job_type=JobType.SEND_EMAIL,
        idempotency_key=idempotency_key,
        requested_by=requested_by,
        payload={"template_code": template_code, **(payload or {})},
    )
    await notifications_repository.insert_email_delivery(
        db,
        job_id=job.id,
        recipient_user_id=recipient_user_id,
        recipient_email=recipient_email,
        template_code=template_code,
    )
    return job


async def list_jobs(
    db: AsyncSession,
    *,
    actor: UserRow,
    scope: JobScope,
    page_params: PageParams,
    sort: str,
    status: JobStatus | None,
    job_type: JobType | None,
) -> Page[JobView]:
    if scope == "all":
        await ensure_can_list_all(db, actor)
    items, total = await notifications_repository.list_jobs_page(
        db,
        page_params,
        sort=sort,
        requested_by=actor.id if scope == "mine" else None,
        status=status.value if status else None,
        job_type=job_type.value if job_type else None,
    )
    return Page(
        items=[to_view(item) for item in items],
        page=page_params.page,
        page_size=page_params.page_size,
        total=total,
    )


async def get_job(db: AsyncSession, *, actor: UserRow, job_id: uuid.UUID) -> JobView:
    return to_view(await ensure_job_scope(db, actor, job_id))


async def retry_job(db: AsyncSession, *, actor: UserRow, job_id: uuid.UUID) -> JobView:
    """Thử lại job failed do lỗi tạm thời: reset ngân sách thử, giữ job ID và
    idempotency key, phát lại qua outbox và ghi audit (SPEC SP-07)."""
    job = await ensure_job_scope(db, actor, job_id)
    if not is_retryable(job):
        raise invalid_state("Chỉ thử lại được tác vụ thất bại do lỗi tạm thời.")

    if not await notifications_repository.reset_failed_job(db, job.id):
        # Một request retry khác vừa thắng: job không còn failed.
        raise invalid_state("Tác vụ đã được thử lại hoặc đổi trạng thái.")
    await notifications_repository.schedule_outbox(db, job.id, delay_seconds=0)
    await notifications_repository.set_email_status_for_job(
        db, job.id, status=EmailDeliveryStatus.PENDING.value
    )
    await record_audit(
        db,
        actor=actor,
        action="job.retry",
        entity_type="jobs",
        entity_id=job.id,
        change_summary={
            "job_type": job.job_type,
            "previous_error_code": job.error_code,
            "previous_attempts": job.attempts,
        },
    )
    await db.commit()
    return to_view(expect(await notifications_repository.get_job(db, job.id)))
