"""Truy vấn `customers` — chủ sở hữu: module customers. SQL tay (ADR-011).

Tên/email/điện thoại hiển thị lấy live từ `users`, nên các hàm đọc hồ sơ trả
`CustomerProfileRow` đã join sẵn thay vì chỉ dòng `customers`.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.common import db as sql
from app.common.utils import expect
from app.common.utils.pagination import PageParams


@dataclass(frozen=True)
class CustomerRow:
    id: uuid.UUID
    user_id: uuid.UUID
    customer_code: str
    address: str | None
    row_version: int
    deleted_at: datetime | None


@dataclass(frozen=True)
class CustomerProfileRow:
    id: uuid.UUID
    customer_code: str
    address: str | None
    row_version: int
    user_id: uuid.UUID
    full_name: str
    email: str
    phone: str | None


_COLUMNS = "id, user_id, customer_code, address, row_version, deleted_at"
_PROFILE_COLUMNS = """
    c.id, c.customer_code, c.address, c.row_version,
    u.id AS user_id, u.full_name, u.email, u.phone
"""
_UPDATABLE_COLUMNS = ("address",)


async def get_by_id(db: AsyncSession, customer_id: uuid.UUID) -> CustomerRow | None:
    return await sql.query_one(
        db, CustomerRow, f"SELECT {_COLUMNS} FROM customers WHERE id = :id", id=customer_id
    )


async def get_by_user_id(db: AsyncSession, user_id: uuid.UUID) -> CustomerRow | None:
    return await sql.query_one(
        db,
        CustomerRow,
        f"SELECT {_COLUMNS} FROM customers WHERE user_id = :user_id",
        user_id=user_id,
    )


async def insert(db: AsyncSession, *, user_id: uuid.UUID, customer_code: str) -> CustomerRow:
    row = await sql.query_one(
        db,
        CustomerRow,
        f"""
        INSERT INTO customers (user_id, customer_code) VALUES (:user_id, :customer_code)
        RETURNING {_COLUMNS}
        """,
        user_id=user_id,
        customer_code=customer_code,
    )
    return expect(row, "INSERT ... RETURNING không trả dòng nào")


async def get_profile(db: AsyncSession, customer_id: uuid.UUID) -> CustomerProfileRow | None:
    return await sql.query_one(
        db,
        CustomerProfileRow,
        f"""
        SELECT {_PROFILE_COLUMNS}
        FROM customers c JOIN users u ON u.id = c.user_id
        WHERE c.id = :id
        """,
        id=customer_id,
    )


async def has_contract_with_agent(
    db: AsyncSession, *, customer_id: uuid.UUID, agent_id: uuid.UUID
) -> bool:
    return bool(
        await sql.scalar(
            db,
            """
            SELECT EXISTS (
                SELECT 1 FROM contracts WHERE customer_id = :customer_id AND agent_id = :agent_id
            )
            """,
            customer_id=customer_id,
            agent_id=agent_id,
        )
    )


async def list_page(
    db: AsyncSession,
    page_params: PageParams,
    *,
    scope_agent_id: uuid.UUID | None = None,
) -> tuple[list[CustomerProfileRow], int]:
    clauses: list[str] = []
    params: dict[str, Any] = {}
    if scope_agent_id is not None:
        # Scope môi giới: chỉ khách có hợp đồng với môi giới này (SPEC SP-01).
        clauses.append(
            "EXISTS (SELECT 1 FROM contracts k"
            " WHERE k.customer_id = c.id AND k.agent_id = :scope_agent_id)"
        )
        params["scope_agent_id"] = scope_agent_id
    where = sql.where(clauses)
    from_ = "FROM customers c JOIN users u ON u.id = c.user_id"

    total = await sql.scalar(db, f"SELECT COUNT(*) {from_} {where}", **params)
    items = await sql.query(
        db,
        CustomerProfileRow,
        f"""
        SELECT {_PROFILE_COLUMNS} {from_} {where}
        ORDER BY c.created_at DESC, c.id ASC
        LIMIT :limit OFFSET :offset
        """,
        **params,
        limit=page_params.page_size,
        offset=page_params.offset,
    )
    return items, int(total or 0)


async def update_fields(
    db: AsyncSession, customer_id: uuid.UUID, expected_row_version: int, **fields: Any
) -> bool:
    return await sql.update_versioned(
        db,
        table="customers",
        record_id=customer_id,
        expected_row_version=expected_row_version,
        fields=fields,
        allowed_columns=_UPDATABLE_COLUMNS,
    )
