"""Truy vấn `jobs`, `outbox_events`, `email_deliveries` — chủ sở hữu: module
notifications. SQL tay + dataclass (ADR-011).

Mọi chuyển trạng thái job là UPDATE có điều kiện trạng thái nguồn (`WHERE status
= ...`), nên hai worker nhận trùng một job ID chỉ có một bên nhận được dòng trả
về; đây là khóa "một lần xử lý" của SPEC SP-07, không cần khóa phân tán.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.common import db as sql
from app.common.enums import EmailDeliveryStatus, JobStatus, OutboxStatus
from app.common.utils.pagination import PageParams


@dataclass(frozen=True)
class JobRow:
    id: uuid.UUID
    requested_by: uuid.UUID | None
    job_type: str
    idempotency_key: str
    status: str
    payload: dict[str, Any]
    input_file_id: uuid.UUID | None
    output_file_id: uuid.UUID | None
    attempts: int
    max_attempts: int
    error_code: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class EmailDeliveryRow:
    id: uuid.UUID
    job_id: uuid.UUID
    recipient_user_id: uuid.UUID | None
    recipient_email: str
    template_code: str
    status: str
    provider_message_id: str | None
    sent_at: datetime | None


@dataclass(frozen=True)
class OutboxClaim:
    id: uuid.UUID
    job_id: uuid.UUID


_JOB_COLUMNS = """
    id, requested_by, job_type, idempotency_key, status, payload, input_file_id,
    output_file_id, attempts, max_attempts, error_code, started_at, finished_at,
    created_at, updated_at
"""
_EMAIL_COLUMNS = """
    id, job_id, recipient_user_id, recipient_email, template_code, status,
    provider_message_id, sent_at
"""
_JOB_SORT_COLUMNS = {"created_at": "created_at"}


# --- jobs: tạo và đọc ----------------------------------------------------------


async def insert_job(
    db: AsyncSession,
    *,
    job_type: str,
    idempotency_key: str,
    requested_by: uuid.UUID | None,
    payload: Mapping[str, Any],
    input_file_id: uuid.UUID | None,
    max_attempts: int,
) -> JobRow | None:
    """`None` nếu `idempotency_key` đã tồn tại (job đã được tạo trước đó)."""
    return await sql.query_one(
        db,
        JobRow,
        f"""
        INSERT INTO jobs
            (job_type, idempotency_key, requested_by, payload, input_file_id, max_attempts)
        VALUES
            (:job_type, :idempotency_key, :requested_by, CAST(:payload AS jsonb),
             :input_file_id, :max_attempts)
        ON CONFLICT (idempotency_key) DO NOTHING
        RETURNING {_JOB_COLUMNS}
        """,
        job_type=job_type,
        idempotency_key=idempotency_key,
        requested_by=requested_by,
        payload=json.dumps(dict(payload), ensure_ascii=False, default=str),
        input_file_id=input_file_id,
        max_attempts=max_attempts,
    )


async def get_job(db: AsyncSession, job_id: uuid.UUID) -> JobRow | None:
    return await sql.query_one(
        db, JobRow, f"SELECT {_JOB_COLUMNS} FROM jobs WHERE id = :id", id=job_id
    )


async def get_job_by_idempotency_key(db: AsyncSession, idempotency_key: str) -> JobRow | None:
    return await sql.query_one(
        db,
        JobRow,
        f"SELECT {_JOB_COLUMNS} FROM jobs WHERE idempotency_key = :key",
        key=idempotency_key,
    )


async def list_jobs_page(
    db: AsyncSession,
    page_params: PageParams,
    *,
    sort: str,
    requested_by: uuid.UUID | None,
    status: str | None = None,
    job_type: str | None = None,
) -> tuple[list[JobRow], int]:
    """`requested_by=None` nghĩa là không lọc theo người yêu cầu (chỉ dành cho
    người có quyền vận hành — service quyết định, không phải repository)."""
    clauses: list[str] = []
    params: dict[str, Any] = {}
    if requested_by is not None:
        clauses.append("requested_by = :requested_by")
        params["requested_by"] = requested_by
    if status:
        clauses.append("status = :status")
        params["status"] = status
    if job_type:
        clauses.append("job_type = :job_type")
        params["job_type"] = job_type
    where = sql.where(clauses)

    total = await sql.scalar(db, f"SELECT COUNT(*) FROM jobs {where}", **params)
    items = await sql.query(
        db,
        JobRow,
        f"""
        SELECT {_JOB_COLUMNS} FROM jobs {where}
        {sql.order_by(sort, _JOB_SORT_COLUMNS, "id")}
        LIMIT :limit OFFSET :offset
        """,
        **params,
        limit=page_params.page_size,
        offset=page_params.offset,
    )
    return items, int(total or 0)


# --- jobs: chuyển trạng thái ----------------------------------------------------


async def claim_job(db: AsyncSession, job_id: uuid.UUID) -> JobRow | None:
    """pending → running và tính một lần thử. `None` nếu job không còn pending
    (worker khác đã nhận, đã xong, hoặc đã failed)."""
    return await sql.query_one(
        db,
        JobRow,
        f"""
        UPDATE jobs
        SET status = :running, attempts = attempts + 1, started_at = now(),
            finished_at = NULL, updated_at = now()
        WHERE id = :id AND status = :pending
        RETURNING {_JOB_COLUMNS}
        """,
        id=job_id,
        running=JobStatus.RUNNING.value,
        pending=JobStatus.PENDING.value,
    )


async def touch_job(db: AsyncSession, job_id: uuid.UUID) -> None:
    """Heartbeat cho job chạy lâu: đối soát dựa vào `updated_at` (SPEC SP-07)."""
    await sql.execute(
        db,
        "UPDATE jobs SET updated_at = now() WHERE id = :id AND status = :running",
        id=job_id,
        running=JobStatus.RUNNING.value,
    )


async def mark_job_succeeded(
    db: AsyncSession, job_id: uuid.UUID, *, output_file_id: uuid.UUID | None = None
) -> bool:
    return (
        await sql.execute(
            db,
            """
            UPDATE jobs
            SET status = :succeeded, error_code = NULL, finished_at = now(), updated_at = now(),
                output_file_id = COALESCE(:output_file_id, output_file_id)
            WHERE id = :id AND status = :running
            """,
            id=job_id,
            output_file_id=output_file_id,
            succeeded=JobStatus.SUCCEEDED.value,
            running=JobStatus.RUNNING.value,
        )
        == 1
    )


async def mark_job_failed(db: AsyncSession, job_id: uuid.UUID, *, error_code: str) -> bool:
    return (
        await sql.execute(
            db,
            """
            UPDATE jobs
            SET status = :failed, error_code = :error_code, finished_at = now(),
                updated_at = now()
            WHERE id = :id AND status = :running
            """,
            id=job_id,
            error_code=error_code,
            failed=JobStatus.FAILED.value,
            running=JobStatus.RUNNING.value,
        )
        == 1
    )


async def return_job_to_pending(db: AsyncSession, job_id: uuid.UUID, *, error_code: str) -> bool:
    """running → pending để thử lại tự động; giữ `attempts` đã tiêu."""
    return (
        await sql.execute(
            db,
            """
            UPDATE jobs
            SET status = :pending, error_code = :error_code, updated_at = now()
            WHERE id = :id AND status = :running
            """,
            id=job_id,
            error_code=error_code,
            pending=JobStatus.PENDING.value,
            running=JobStatus.RUNNING.value,
        )
        == 1
    )


async def reset_failed_job(db: AsyncSession, job_id: uuid.UUID) -> bool:
    """failed → pending cho lệnh retry thủ công: reset ngân sách thử, giữ nguyên
    job ID và idempotency key (SPEC SP-07)."""
    return (
        await sql.execute(
            db,
            """
            UPDATE jobs
            SET status = :pending, attempts = 0, error_code = NULL, started_at = NULL,
                finished_at = NULL, updated_at = now()
            WHERE id = :id AND status = :failed
            """,
            id=job_id,
            pending=JobStatus.PENDING.value,
            failed=JobStatus.FAILED.value,
        )
        == 1
    )


async def lock_stale_running_jobs(
    db: AsyncSession, *, timeouts: Mapping[str, int], default_timeout: int, limit: int
) -> list[JobRow]:
    """Job running không có heartbeat quá timeout theo loại job. Khóa dòng
    (SKIP LOCKED) để hai vòng đối soát chạy song song không xử lý cùng job."""
    # CAST tường minh: tham số trong nhánh CASE không có ngữ cảnh kiểu, PostgreSQL
    # sẽ suy ra `text` và `make_interval(secs => text)` không tồn tại.
    cases = " ".join(
        f"WHEN :type_{index} THEN CAST(:secs_{index} AS double precision)"
        for index in range(len(timeouts))
    )
    params: dict[str, Any] = {}
    for index, (job_type, seconds) in enumerate(timeouts.items()):
        params[f"type_{index}"] = job_type
        params[f"secs_{index}"] = float(seconds)
    return await sql.query(
        db,
        JobRow,
        f"""
        SELECT {_JOB_COLUMNS} FROM jobs
        WHERE status = :running
          AND updated_at < now() - make_interval(
              secs => CASE job_type {cases} ELSE CAST(:default_timeout AS double precision) END
          )
        ORDER BY updated_at, id
        LIMIT :limit
        FOR UPDATE SKIP LOCKED
        """,
        **params,
        running=JobStatus.RUNNING.value,
        default_timeout=float(default_timeout),
        limit=limit,
    )


# --- outbox_events ----------------------------------------------------------------


async def insert_outbox_event(db: AsyncSession, *, job_id: uuid.UUID, event_key: str) -> None:
    await sql.execute(
        db,
        """
        INSERT INTO outbox_events (job_id, event_key)
        VALUES (:job_id, :event_key)
        ON CONFLICT (event_key) DO NOTHING
        """,
        job_id=job_id,
        event_key=event_key,
    )


async def schedule_outbox(db: AsyncSession, job_id: uuid.UUID, *, delay_seconds: float) -> int:
    """Đưa sự kiện của job về pending để dispatcher phát lại sau `delay_seconds`
    (backoff của lần thử kế tiếp, hoặc phát lại khi đối soát/retry thủ công)."""
    return await sql.execute(
        db,
        """
        UPDATE outbox_events
        SET status = :pending, available_at = now() + make_interval(secs => :delay_seconds),
            locked_until = NULL, published_at = NULL, updated_at = now()
        WHERE job_id = :job_id
        """,
        job_id=job_id,
        delay_seconds=float(delay_seconds),
        pending=OutboxStatus.PENDING.value,
    )


async def claim_outbox_batch(
    db: AsyncSession, *, lease_seconds: float, limit: int
) -> list[OutboxClaim]:
    """Lấy sự kiện đến hạn và đặt lease. Sự kiện `publishing` có lease đã hết
    hạn (dispatcher chết giữa chừng) được lấy lại như pending."""
    return await sql.query(
        db,
        OutboxClaim,
        """
        UPDATE outbox_events
        SET status = :publishing,
            locked_until = now() + make_interval(secs => :lease_seconds),
            updated_at = now()
        WHERE id IN (
            SELECT id FROM outbox_events
            WHERE (status = :pending AND available_at <= now())
               OR (status = :publishing AND locked_until < now())
            ORDER BY available_at, id
            LIMIT :limit
            FOR UPDATE SKIP LOCKED
        )
        RETURNING id, job_id
        """,
        lease_seconds=float(lease_seconds),
        limit=limit,
        pending=OutboxStatus.PENDING.value,
        publishing=OutboxStatus.PUBLISHING.value,
    )


async def mark_outbox_published(db: AsyncSession, event_id: uuid.UUID) -> None:
    await sql.execute(
        db,
        """
        UPDATE outbox_events
        SET status = :published, published_at = now(), locked_until = NULL, updated_at = now()
        WHERE id = :id AND status = :publishing
        """,
        id=event_id,
        published=OutboxStatus.PUBLISHED.value,
        publishing=OutboxStatus.PUBLISHING.value,
    )


async def release_outbox(db: AsyncSession, event_id: uuid.UUID, *, delay_seconds: float) -> None:
    """Publish lỗi: quay lại pending và tăng attempts (ERD mục 4)."""
    await sql.execute(
        db,
        """
        UPDATE outbox_events
        SET status = :pending, attempts = attempts + 1, locked_until = NULL,
            available_at = now() + make_interval(secs => :delay_seconds), updated_at = now()
        WHERE id = :id AND status = :publishing
        """,
        id=event_id,
        delay_seconds=float(delay_seconds),
        pending=OutboxStatus.PENDING.value,
        publishing=OutboxStatus.PUBLISHING.value,
    )


async def requeue_lost_publications(db: AsyncSession, *, older_than_seconds: float) -> int:
    """Job vẫn pending dù sự kiện đã published từ lâu: broker đã mất message
    (Redis restart không persist). Phát lại; nếu message cũ vẫn tới sau thì
    `claim_job` chỉ cho một bên xử lý."""
    return await sql.execute(
        db,
        """
        UPDATE outbox_events o
        SET status = :pending, available_at = now(), locked_until = NULL,
            published_at = NULL, updated_at = now()
        FROM jobs j
        WHERE j.id = o.job_id
          AND j.status = :job_pending
          AND o.status = :published
          AND o.published_at < now() - make_interval(secs => :older_than_seconds)
        """,
        older_than_seconds=float(older_than_seconds),
        pending=OutboxStatus.PENDING.value,
        published=OutboxStatus.PUBLISHED.value,
        job_pending=JobStatus.PENDING.value,
    )


# --- email_deliveries -------------------------------------------------------------


async def insert_email_delivery(
    db: AsyncSession,
    *,
    job_id: uuid.UUID,
    recipient_user_id: uuid.UUID | None,
    recipient_email: str,
    template_code: str,
) -> None:
    await sql.execute(
        db,
        """
        INSERT INTO email_deliveries (job_id, recipient_user_id, recipient_email, template_code)
        VALUES (:job_id, :recipient_user_id, :recipient_email, :template_code)
        ON CONFLICT (job_id) DO NOTHING
        """,
        job_id=job_id,
        recipient_user_id=recipient_user_id,
        recipient_email=recipient_email,
        template_code=template_code,
    )


async def get_email_delivery_by_job(db: AsyncSession, job_id: uuid.UUID) -> EmailDeliveryRow | None:
    return await sql.query_one(
        db,
        EmailDeliveryRow,
        f"SELECT {_EMAIL_COLUMNS} FROM email_deliveries WHERE job_id = :job_id",
        job_id=job_id,
    )


async def mark_email_sent(
    db: AsyncSession, delivery_id: uuid.UUID, *, provider_message_id: str | None
) -> None:
    await sql.execute(
        db,
        """
        UPDATE email_deliveries
        SET status = :sent, sent_at = now(), provider_message_id = :provider_message_id,
            updated_at = now()
        WHERE id = :id AND status <> :sent
        """,
        id=delivery_id,
        provider_message_id=provider_message_id,
        sent=EmailDeliveryStatus.SENT.value,
    )


async def set_email_status_for_job(db: AsyncSession, job_id: uuid.UUID, *, status: str) -> None:
    """Đồng bộ trạng thái thư theo job (failed khi job hết lượt, pending khi
    retry). Thư đã `sent` không bị đổi ngược."""
    await sql.execute(
        db,
        """
        UPDATE email_deliveries SET status = :status, updated_at = now()
        WHERE job_id = :job_id AND status <> :sent
        """,
        job_id=job_id,
        status=status,
        sent=EmailDeliveryStatus.SENT.value,
    )


async def user_requested_job_for_file(
    db: AsyncSession, *, file_id: uuid.UUID, user_id: uuid.UUID
) -> bool:
    """Tệp là đầu vào/kết quả của một job do `user_id` yêu cầu — căn cứ cấp quyền
    tải tệp do hệ thống sinh (module files hỏi qua hàm này, không tự đọc `jobs`)."""
    return bool(
        await sql.scalar(
            db,
            """
            SELECT EXISTS (
                SELECT 1 FROM jobs
                WHERE requested_by = :user_id
                  AND (output_file_id = :file_id OR input_file_id = :file_id)
            )
            """,
            user_id=user_id,
            file_id=file_id,
        )
    )
