"""Truy vấn `agents` — chủ sở hữu: module agents. SQL tay (ADR-011).

Tên/email/điện thoại hiển thị lấy live từ `users`, nên các hàm đọc hồ sơ trả
`AgentProfileRow` đã join sẵn thay vì chỉ dòng `agents`.
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
class AgentRow:
    id: uuid.UUID
    user_id: uuid.UUID
    agent_code: str
    status: str
    row_version: int
    deleted_at: datetime | None


@dataclass(frozen=True)
class AgentProfileRow:
    id: uuid.UUID
    agent_code: str
    status: str
    row_version: int
    user_id: uuid.UUID
    full_name: str
    email: str
    phone: str | None


_COLUMNS = "id, user_id, agent_code, status, row_version, deleted_at"
_PROFILE_COLUMNS = """
    a.id, a.agent_code, a.status, a.row_version,
    u.id AS user_id, u.full_name, u.email, u.phone
"""
_PROFILE_FROM = "FROM agents a JOIN users u ON u.id = a.user_id"
_UPDATABLE_COLUMNS: tuple[str, ...] = ()


async def get_by_id(db: AsyncSession, agent_id: uuid.UUID) -> AgentRow | None:
    return await sql.query_one(
        db, AgentRow, f"SELECT {_COLUMNS} FROM agents WHERE id = :id", id=agent_id
    )


async def get_by_user_id(db: AsyncSession, user_id: uuid.UUID) -> AgentRow | None:
    return await sql.query_one(
        db, AgentRow, f"SELECT {_COLUMNS} FROM agents WHERE user_id = :user_id", user_id=user_id
    )


async def insert(db: AsyncSession, *, user_id: uuid.UUID, agent_code: str) -> AgentRow:
    row = await sql.query_one(
        db,
        AgentRow,
        f"""
        INSERT INTO agents (user_id, agent_code) VALUES (:user_id, :agent_code)
        RETURNING {_COLUMNS}
        """,
        user_id=user_id,
        agent_code=agent_code,
    )
    return expect(row, "INSERT ... RETURNING không trả dòng nào")


async def get_profile(db: AsyncSession, agent_id: uuid.UUID) -> AgentProfileRow | None:
    return await sql.query_one(
        db,
        AgentProfileRow,
        f"SELECT {_PROFILE_COLUMNS} {_PROFILE_FROM} WHERE a.id = :id",
        id=agent_id,
    )


async def list_page(db: AsyncSession, page_params: PageParams) -> tuple[list[AgentProfileRow], int]:
    total = await sql.scalar(db, "SELECT COUNT(*) FROM agents")
    items = await sql.query(
        db,
        AgentProfileRow,
        f"""
        SELECT {_PROFILE_COLUMNS} {_PROFILE_FROM}
        ORDER BY a.created_at DESC, a.id ASC
        LIMIT :limit OFFSET :offset
        """,
        limit=page_params.page_size,
        offset=page_params.offset,
    )
    return items, int(total or 0)


async def update_fields(
    db: AsyncSession, agent_id: uuid.UUID, expected_row_version: int, **fields: Any
) -> bool:
    """Hiện chỉ tăng `row_version` (tên/điện thoại nằm ở `users`); vẫn qua đây để
    PATCH hồ sơ môi giới có khóa lạc quan trên chính bảng `agents`."""
    return await sql.update_versioned(
        db,
        table="agents",
        record_id=agent_id,
        expected_row_version=expected_row_version,
        fields=fields,
        allowed_columns=_UPDATABLE_COLUMNS,
    )
