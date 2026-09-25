"""Truy vấn đọc `audit_logs` — chỉ đọc, không có API sửa/xóa (SPEC SP-07)."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.utils.pagination import PageParams
from app.modules.audit_logs.models import AuditLog


async def list_page(
    db: AsyncSession,
    page_params: PageParams,
    *,
    entity_type: str | None = None,
    entity_id: uuid.UUID | None = None,
    actor_user_id: uuid.UUID | None = None,
) -> tuple[list[AuditLog], int]:
    query = select(AuditLog)
    if entity_type is not None:
        query = query.where(AuditLog.entity_type == entity_type)
    if entity_id is not None:
        query = query.where(AuditLog.entity_id == entity_id)
    if actor_user_id is not None:
        query = query.where(AuditLog.actor_user_id == actor_user_id)

    total_stmt = select(func.count()).select_from(query.with_only_columns(AuditLog.id).subquery())
    total = await db.scalar(total_stmt) or 0

    items_stmt = (
        query.order_by(AuditLog.created_at.desc(), AuditLog.id)
        .offset(page_params.offset)
        .limit(page_params.page_size)
    )
    result = await db.execute(items_stmt)
    return list(result.scalars().all()), total
