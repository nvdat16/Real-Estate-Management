"""Truy vấn `agents` — chủ sở hữu: module agents.

Tên/email/điện thoại hiển thị lấy live từ `users` nên các hàm đọc trả về cặp
`(Agent, User)` thay vì chỉ `Agent`.
"""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.utils.pagination import PageParams
from app.common.utils.row_version import conditional_update
from app.modules.agents.models import Agent
from app.modules.users.models import User


async def get_by_id(db: AsyncSession, agent_id: uuid.UUID) -> Agent | None:
    return await db.get(Agent, agent_id)


async def get_by_user_id(db: AsyncSession, user_id: uuid.UUID) -> Agent | None:
    result = await db.execute(select(Agent).where(Agent.user_id == user_id))
    return result.scalar_one_or_none()


async def get_with_user(db: AsyncSession, agent_id: uuid.UUID) -> tuple[Agent, User] | None:
    stmt = select(Agent, User).join(User, User.id == Agent.user_id).where(Agent.id == agent_id)
    result = await db.execute(stmt)
    row = result.first()
    return (row[0], row[1]) if row else None


async def list_page(
    db: AsyncSession, page_params: PageParams
) -> tuple[list[tuple[Agent, User]], int]:
    query = select(Agent, User).join(User, User.id == Agent.user_id)
    total_stmt = select(func.count()).select_from(query.with_only_columns(Agent.id).subquery())
    total = await db.scalar(total_stmt) or 0

    items_stmt = (
        query.order_by(Agent.created_at.desc(), Agent.id)
        .offset(page_params.offset)
        .limit(page_params.page_size)
    )
    result = await db.execute(items_stmt)
    return [(row[0], row[1]) for row in result.all()], total


async def update_fields(
    db: AsyncSession, agent_id: uuid.UUID, expected_row_version: int, **fields: object
) -> bool:
    return await conditional_update(db, Agent, agent_id, expected_row_version, fields)
