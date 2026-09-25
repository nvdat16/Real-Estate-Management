"""Truy vấn `users` — chủ sở hữu: module users.

Mọi SQL trên bảng `users` (kể cả từ luồng đăng ký/đăng nhập của module `auth`,
hay đồng bộ tên/điện thoại từ PATCH hồ sơ của `customers`/`agents`) đi qua đây,
theo đúng quy tắc "mỗi bảng có một repository sở hữu" (ARCHITECTURE mục 5).
"""

from __future__ import annotations

import uuid

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.utils.pagination import PageParams
from app.common.utils.row_version import conditional_update
from app.modules.users.models import User


async def get_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    return await db.get(User, user_id)


async def get_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def create(
    db: AsyncSession, *, email: str, password_hash: str, full_name: str, phone: str | None
) -> User:
    user = User(email=email, password_hash=password_hash, full_name=full_name, phone=phone)
    db.add(user)
    await db.flush()
    return user


async def list_page(db: AsyncSession, page_params: PageParams) -> tuple[list[User], int]:
    total = await db.scalar(select(func.count()).select_from(User)) or 0
    items_stmt = (
        select(User)
        .order_by(User.created_at.desc(), User.id)
        .offset(page_params.offset)
        .limit(page_params.page_size)
    )
    result = await db.execute(items_stmt)
    return list(result.scalars().all()), total


async def update_fields(
    db: AsyncSession, user_id: uuid.UUID, expected_row_version: int, **fields: object
) -> bool:
    return await conditional_update(db, User, user_id, expected_row_version, fields)


async def set_contact_fields(
    db: AsyncSession, user_id: uuid.UUID, *, full_name: str, phone: str | None
) -> None:
    """Cập nhật không điều kiện `full_name`/`phone`.

    Dùng khi caller (PATCH /customers/{id}, /agents/{id}) đã tự khóa bằng
    `row_version` của chính bảng đó — không khóa lại theo `users.row_version`.
    """
    await db.execute(
        update(User).where(User.id == user_id).values(full_name=full_name, phone=phone)
    )


async def bump_auth_version(db: AsyncSession, user_id: uuid.UUID) -> None:
    await db.execute(
        update(User).where(User.id == user_id).values(auth_version=User.auth_version + 1)
    )


async def set_password_and_revoke(db: AsyncSession, user_id: uuid.UUID, password_hash: str) -> None:
    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(
            password_hash=password_hash,
            auth_version=User.auth_version + 1,
            row_version=User.row_version + 1,
        )
    )
