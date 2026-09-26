"""Outbox dispatcher (PLAN task 4.2, ERD mục 8 "Outbox").

Lấy sự kiện đến hạn theo lease, publish job ID vào broker và chỉ đánh dấu
`published` **sau khi** broker nhận. Nếu dispatcher chết sau publish nhưng trước
khi ghi DB, lease hết hạn và sự kiện được publish lại; worker nhận trùng sẽ bị
`claim_job` chặn (job không còn pending).
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from collections.abc import Callable
from dataclasses import dataclass

from app.modules.notifications import repository as notifications_repository
from app.workers.runner import SessionFactory


logger = logging.getLogger(__name__)

# Publisher đồng bộ (Celery `apply_async`), raise nếu broker không nhận.
Publisher = Callable[[uuid.UUID], None]

DISPATCH_BATCH_SIZE = 100
# Lease đủ dài cho một lượt publish cả batch; hết hạn thì dispatcher khác lấy lại.
OUTBOX_LEASE_SECONDS = 30
# Broker lỗi: thử publish lại sau khoảng này thay vì quay vòng liên tục.
PUBLISH_RETRY_SECONDS = 10


@dataclass(frozen=True)
class DispatchResult:
    published: int
    failed: int


async def dispatch_outbox(
    *,
    session_factory: SessionFactory,
    publish: Publisher,
    batch_size: int = DISPATCH_BATCH_SIZE,
) -> DispatchResult:
    async with session_factory() as db:
        claims = await notifications_repository.claim_outbox_batch(
            db, lease_seconds=OUTBOX_LEASE_SECONDS, limit=batch_size
        )
        await db.commit()

    published = 0
    for index, claim in enumerate(claims):
        try:
            await asyncio.to_thread(publish, claim.job_id)
        except Exception:
            # Broker lỗi thì các sự kiện còn lại trong batch cũng sẽ lỗi: trả hết
            # về pending một lần, không chờ timeout từng cái.
            remaining = claims[index:]
            logger.warning(
                "Publish outbox thất bại, sẽ thử lại",
                extra={"job_id": str(claim.job_id), "released": len(remaining)},
            )
            async with session_factory() as db:
                for item in remaining:
                    await notifications_repository.release_outbox(
                        db, item.id, delay_seconds=PUBLISH_RETRY_SECONDS
                    )
                await db.commit()
            return DispatchResult(published=published, failed=len(remaining))

        async with session_factory() as db:
            await notifications_repository.mark_outbox_published(db, claim.id)
            await db.commit()
        published += 1

    return DispatchResult(published=published, failed=0)
