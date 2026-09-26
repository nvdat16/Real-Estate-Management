"""Celery app và task bọc đồng bộ (PLAN task 4.2).

Chạy: `celery -A app.workers.celery worker --beat` (compose service `worker`).

Celery/Redis chỉ là phương tiện vận chuyển job ID (ADR-008): trạng thái bền vững
nằm ở `jobs`/`outbox_events`, nên không bật result backend và không dùng retry
của Celery — retry/backoff đi qua outbox để sống sót khi broker mất message.

Mỗi task chạy một event loop riêng (`asyncio.run`) với engine NullPool tạo mới:
kết nối asyncpg gắn với event loop, không dùng lại được giữa các lần `asyncio.run`.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from collections.abc import Awaitable, Callable
from typing import Any

from celery import Celery
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.logging import configure_logging
from app.integrations.email.service import get_email_sender
from app.integrations.file_storage.service import get_file_storage
from app.workers.dispatcher import dispatch_outbox
from app.workers.handlers import JOB_HANDLERS
from app.workers.runner import SessionFactory, process_job, reconcile_jobs


configure_logging()
logger = logging.getLogger(__name__)

PROCESS_JOB_TASK = "app.workers.process_job"

celery_app = Celery("real_estate", broker=settings.CELERY_BROKER_URL)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    task_ignore_result=True,
    timezone="UTC",
    enable_utc=True,
    # Worker chết giữa task thì message được giao lại; `claim_job` chặn xử lý đôi.
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
    broker_transport_options={"visibility_timeout": 3600},
    beat_schedule={
        "dispatch-outbox": {
            "task": "app.workers.dispatch_outbox",
            "schedule": 2.0,
            # Worker bận thì bỏ lượt cũ, không để lượt dispatch dồn trong hàng đợi.
            "options": {"expires": 10},
        },
        "reconcile-jobs": {
            "task": "app.workers.reconcile_jobs",
            "schedule": 30.0,
            "options": {"expires": 60},
        },
    },
)


def _run[T](work: Callable[[SessionFactory], Awaitable[T]]) -> T:
    async def main() -> T:
        engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
        try:
            return await work(
                async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
            )
        finally:
            await engine.dispose()

    return asyncio.run(main())


def _publish(job_id: uuid.UUID) -> None:
    # `retry=False`: broker lỗi thì raise ngay để dispatcher trả sự kiện về pending.
    celery_app.send_task(PROCESS_JOB_TASK, args=[str(job_id)], retry=False)


@celery_app.task(name=PROCESS_JOB_TASK)
def process_job_task(job_id: str) -> str:
    outcome = _run(
        lambda session_factory: process_job(
            uuid.UUID(job_id),
            session_factory=session_factory,
            handlers=JOB_HANDLERS,
            email_sender=get_email_sender(),
            storage=get_file_storage(),
        )
    )
    return outcome.value


@celery_app.task(name="app.workers.dispatch_outbox")
def dispatch_outbox_task() -> dict[str, Any]:
    result = _run(
        lambda session_factory: dispatch_outbox(session_factory=session_factory, publish=_publish)
    )
    return {"published": result.published, "failed": result.failed}


@celery_app.task(name="app.workers.reconcile_jobs")
def reconcile_jobs_task() -> dict[str, Any]:
    result = _run(lambda session_factory: reconcile_jobs(session_factory=session_factory))
    return {"requeued": result.requeued, "failed": result.failed, "republished": result.republished}
