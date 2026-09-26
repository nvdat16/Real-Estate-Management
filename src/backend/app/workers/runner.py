"""Chạy một job và đối soát job treo (PLAN task 4.2, 4.3; SPEC SP-07).

Viết bằng async trên cùng tầng SQL với API để test gọi thẳng được; task Celery ở
`app/workers/celery.py` chỉ là lớp bọc đồng bộ. Mỗi bước là một transaction
ngắn: nhận job → (không giữ transaction) gọi SMTP/kho tệp → ghi kết quả. Không
transaction nào mở trong lúc chờ nhà cung cấp ngoài.
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from enum import StrEnum

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.common.enums import EmailDeliveryStatus
from app.integrations.email.service import EmailSender
from app.integrations.file_storage.service import FileStorage
from app.modules.notifications import repository as notifications_repository
from app.modules.notifications.exceptions import (
    DEFAULT_STALE_RUNNING_TIMEOUT_SECONDS,
    STALE_RUNNING_TIMEOUT_SECONDS,
    JobError,
    JobErrorCode,
    PermanentJobError,
    backoff_seconds,
)
from app.modules.notifications.repository import JobRow


logger = logging.getLogger(__name__)

SessionFactory = async_sessionmaker[AsyncSession]

# Sự kiện đã publish mà job vẫn pending sau khoảng này: coi như broker mất message.
LOST_PUBLICATION_SECONDS = 120
RECONCILE_BATCH_SIZE = 100


@dataclass(frozen=True)
class JobContext:
    job: JobRow
    session_factory: SessionFactory
    email_sender: EmailSender
    storage: FileStorage


# Handler trả `output_file_id` nếu job sinh tệp. Handler phải idempotent theo
# trạng thái bền vững của chính nó (ví dụ thư đã `sent` thì không gửi lại), vì
# job có thể chạy lại sau khi worker chết giữa chừng.
JobHandler = Callable[[JobContext], Awaitable[uuid.UUID | None]]


class JobOutcome(StrEnum):
    SKIPPED = "skipped"
    SUCCEEDED = "succeeded"
    RETRY_SCHEDULED = "retry_scheduled"
    FAILED = "failed"


@dataclass(frozen=True)
class ReconcileResult:
    requeued: int
    failed: int
    republished: int


async def process_job(
    job_id: uuid.UUID,
    *,
    session_factory: SessionFactory,
    handlers: Mapping[str, JobHandler],
    email_sender: EmailSender,
    storage: FileStorage,
) -> JobOutcome:
    async with session_factory() as db:
        job = await notifications_repository.claim_job(db, job_id)
        await db.commit()
    if job is None:
        # Message trùng (dispatcher phát lại, broker giao lại) hoặc job đã xong:
        # không làm gì, đây là chốt chặn side effect lần hai.
        logger.info("Bỏ qua job không còn pending", extra={"job_id": str(job_id)})
        return JobOutcome.SKIPPED

    context = JobContext(
        job=job, session_factory=session_factory, email_sender=email_sender, storage=storage
    )
    try:
        handler = handlers.get(job.job_type)
        if handler is None:
            raise PermanentJobError(JobErrorCode.UNSUPPORTED_JOB_TYPE)
        output_file_id = await handler(context)
    except JobError as exc:
        logger.warning(
            "Job lỗi",
            extra={"job_id": str(job.id), "error_code": exc.code, "attempt": job.attempts},
        )
        return await _record_failure(session_factory, job, exc.code, retryable=exc.retryable)
    except Exception:
        # Log đầy đủ ở worker để điều tra; `jobs.error_code` chỉ nhận mã chung.
        logger.exception("Job lỗi chưa phân loại", extra={"job_id": str(job.id)})
        return await _record_failure(
            session_factory, job, JobErrorCode.INTERNAL_ERROR, retryable=True
        )

    async with session_factory() as db:
        await notifications_repository.mark_job_succeeded(db, job.id, output_file_id=output_file_id)
        await db.commit()
    return JobOutcome.SUCCEEDED


async def _record_failure(
    session_factory: SessionFactory, job: JobRow, error_code: str, *, retryable: bool
) -> JobOutcome:
    async with session_factory() as db:
        if retryable and job.attempts < job.max_attempts:
            await notifications_repository.return_job_to_pending(db, job.id, error_code=error_code)
            await notifications_repository.schedule_outbox(
                db, job.id, delay_seconds=backoff_seconds(job.attempts)
            )
            outcome = JobOutcome.RETRY_SCHEDULED
        else:
            await notifications_repository.mark_job_failed(db, job.id, error_code=error_code)
            await notifications_repository.set_email_status_for_job(
                db, job.id, status=EmailDeliveryStatus.FAILED.value
            )
            outcome = JobOutcome.FAILED
        await db.commit()
    return outcome


async def reconcile_jobs(*, session_factory: SessionFactory) -> ReconcileResult:
    """Phục hồi job mà tín hiệu đã mất (SPEC SP-07, UC-22):

    - running quá timeout heartbeat (worker chết giữa job) → pending để chạy lại,
      hoặc failed `WORKER_LOST` nếu đã hết lượt;
    - pending nhưng sự kiện đã published từ lâu (broker mất message) → phát lại.
    """
    requeued = failed = 0
    async with session_factory() as db:
        stale_jobs = await notifications_repository.lock_stale_running_jobs(
            db,
            timeouts=STALE_RUNNING_TIMEOUT_SECONDS,
            default_timeout=DEFAULT_STALE_RUNNING_TIMEOUT_SECONDS,
            limit=RECONCILE_BATCH_SIZE,
        )
        for job in stale_jobs:
            if job.attempts < job.max_attempts:
                await notifications_repository.return_job_to_pending(
                    db, job.id, error_code=JobErrorCode.WORKER_LOST
                )
                await notifications_repository.schedule_outbox(db, job.id, delay_seconds=0)
                requeued += 1
            else:
                await notifications_repository.mark_job_failed(
                    db, job.id, error_code=JobErrorCode.WORKER_LOST
                )
                await notifications_repository.set_email_status_for_job(
                    db, job.id, status=EmailDeliveryStatus.FAILED.value
                )
                failed += 1
        republished = await notifications_repository.requeue_lost_publications(
            db, older_than_seconds=LOST_PUBLICATION_SECONDS
        )
        await db.commit()

    if requeued or failed or republished:
        logger.warning(
            "Đối soát job",
            extra={"requeued": requeued, "failed": failed, "republished": republished},
        )
    return ReconcileResult(requeued=requeued, failed=failed, republished=republished)
