"""Truy vấn `customers` — chủ sở hữu: module customers.

Tên/email/điện thoại hiển thị lấy live từ `users` nên các hàm đọc trả về cặp
`(Customer, User)` thay vì chỉ `Customer`.
"""

from __future__ import annotations

import uuid

from sqlalchemy import exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.utils.pagination import PageParams
from app.common.utils.row_version import conditional_update
from app.modules.contracts.models import Contract
from app.modules.customers.models import Customer
from app.modules.users.models import User


async def get_by_id(db: AsyncSession, customer_id: uuid.UUID) -> Customer | None:
    return await db.get(Customer, customer_id)


async def get_by_user_id(db: AsyncSession, user_id: uuid.UUID) -> Customer | None:
    result = await db.execute(select(Customer).where(Customer.user_id == user_id))
    return result.scalar_one_or_none()


async def get_with_user(db: AsyncSession, customer_id: uuid.UUID) -> tuple[Customer, User] | None:
    stmt = (
        select(Customer, User)
        .join(User, User.id == Customer.user_id)
        .where(Customer.id == customer_id)
    )
    result = await db.execute(stmt)
    row = result.first()
    return (row[0], row[1]) if row else None


async def has_contract_with_agent(
    db: AsyncSession, *, customer_id: uuid.UUID, agent_id: uuid.UUID
) -> bool:
    stmt = select(
        exists().where(Contract.customer_id == customer_id, Contract.agent_id == agent_id)
    )
    return bool(await db.scalar(stmt))


async def list_page(
    db: AsyncSession,
    page_params: PageParams,
    *,
    scope_agent_id: uuid.UUID | None = None,
) -> tuple[list[tuple[Customer, User]], int]:
    query = select(Customer, User).join(User, User.id == Customer.user_id)
    if scope_agent_id is not None:
        query = query.where(
            exists().where(Contract.customer_id == Customer.id, Contract.agent_id == scope_agent_id)
        )

    total_stmt = select(func.count()).select_from(query.with_only_columns(Customer.id).subquery())
    total = await db.scalar(total_stmt) or 0

    items_stmt = (
        query.order_by(Customer.created_at.desc(), Customer.id)
        .offset(page_params.offset)
        .limit(page_params.page_size)
    )
    result = await db.execute(items_stmt)
    return [(row[0], row[1]) for row in result.all()], total


async def update_fields(
    db: AsyncSession, customer_id: uuid.UUID, expected_row_version: int, **fields: object
) -> bool:
    return await conditional_update(db, Customer, customer_id, expected_row_version, fields)
