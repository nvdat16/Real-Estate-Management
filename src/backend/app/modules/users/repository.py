"""Truy vấn `users` — chủ sở hữu: module users. SQL tay + dataclass (ADR-011).

Mọi SQL trên bảng `users` (kể cả từ luồng đăng ký/đăng nhập của module `auth`,
hay đồng bộ tên/điện thoại từ PATCH hồ sơ của `customers`/`agents`) đi qua đây,
theo đúng quy tắc "mỗi bảng có một repository sở hữu" (ARCHITECTURE mục 5).
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
class UserRow:
    """Tài khoản đã xác thực/đang thao tác. Có `password_hash` vì luồng đăng nhập
    cần; schema response không bao giờ lấy trường này."""

    id: uuid.UUID
    email: str
    password_hash: str
    full_name: str
    phone: str | None
    status: str
    auth_version: int
    locked_at: datetime | None
    row_version: int
    deleted_at: datetime | None
    created_at: datetime
    updated_at: datetime


_COLUMNS = """
    id, email, password_hash, full_name, phone, status, auth_version, locked_at,
    row_version, deleted_at, created_at, updated_at
"""
_UPDATABLE_COLUMNS = ("full_name", "phone", "status", "locked_at", "auth_version")


async def get_by_id(db: AsyncSession, user_id: uuid.UUID) -> UserRow | None:
    return await sql.query_one(
        db, UserRow, f"SELECT {_COLUMNS} FROM users WHERE id = :id", id=user_id
    )


async def get_by_email(db: AsyncSession, email: str) -> UserRow | None:
    return await sql.query_one(
        db, UserRow, f"SELECT {_COLUMNS} FROM users WHERE email = :email", email=email
    )


async def create(
    db: AsyncSession, *, email: str, password_hash: str, full_name: str, phone: str | None
) -> UserRow:
    row = await sql.query_one(
        db,
        UserRow,
        f"""
        INSERT INTO users (email, password_hash, full_name, phone)
        VALUES (:email, :password_hash, :full_name, :phone)
        RETURNING {_COLUMNS}
        """,
        email=email,
        password_hash=password_hash,
        full_name=full_name,
        phone=phone,
    )
    return expect(row, "INSERT ... RETURNING không trả dòng nào")


async def list_page(db: AsyncSession, page_params: PageParams) -> tuple[list[UserRow], int]:
    total = await sql.scalar(db, "SELECT COUNT(*) FROM users")
    items = await sql.query(
        db,
        UserRow,
        f"""
        SELECT {_COLUMNS} FROM users
        ORDER BY created_at DESC, id ASC
        LIMIT :limit OFFSET :offset
        """,
        limit=page_params.page_size,
        offset=page_params.offset,
    )
    return items, int(total or 0)


async def update_fields(
    db: AsyncSession,
    user_id: uuid.UUID,
    expected_row_version: int,
    *,
    bump_auth_version: bool = False,
    **fields: Any,
) -> bool:
    """`bump_auth_version` thu hồi mọi JWT đang có của tài khoản (SPEC SP-01)."""
    return await sql.update_versioned(
        db,
        table="users",
        record_id=user_id,
        expected_row_version=expected_row_version,
        fields=fields,
        allowed_columns=_UPDATABLE_COLUMNS,
        increments=("auth_version",) if bump_auth_version else (),
    )


async def set_contact_fields(
    db: AsyncSession, user_id: uuid.UUID, *, full_name: str, phone: str | None
) -> None:
    """Cập nhật không điều kiện `full_name`/`phone`.

    Dùng khi caller (PATCH /customers/{id}, /agents/{id}) đã tự khóa bằng
    `row_version` của chính bảng đó — không khóa lại theo `users.row_version`.
    """
    await sql.execute(
        db,
        """
        UPDATE users SET full_name = :full_name, phone = :phone, updated_at = now()
        WHERE id = :id
        """,
        id=user_id,
        full_name=full_name,
        phone=phone,
    )


async def bump_auth_version(db: AsyncSession, user_id: uuid.UUID) -> None:
    await sql.execute(
        db,
        "UPDATE users SET auth_version = auth_version + 1, updated_at = now() WHERE id = :id",
        id=user_id,
    )


async def set_password_and_revoke(db: AsyncSession, user_id: uuid.UUID, password_hash: str) -> None:
    await sql.execute(
        db,
        """
        UPDATE users
        SET password_hash = :password_hash,
            auth_version = auth_version + 1,
            row_version = row_version + 1,
            updated_at = now()
        WHERE id = :id
        """,
        id=user_id,
        password_hash=password_hash,
    )
