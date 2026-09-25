"""Truy vấn `roles`/`user_roles` — bảng bridge không có nghiệp vụ độc lập nên
`auth`/`users`/`services` khác gọi trực tiếp module này (ngoại lệ có chủ đích,
xem PLAN Phase 2 — không có endpoint `/roles` riêng)."""

from __future__ import annotations

import uuid

from sqlalchemy import delete, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.roles.models import Role, UserRole


async def get_id_by_code(db: AsyncSession, code: str) -> uuid.UUID | None:
    result = await db.execute(select(Role.id).where(Role.code == code))
    return result.scalar_one_or_none()


async def get_ids_by_codes(db: AsyncSession, codes: list[str]) -> dict[str, uuid.UUID]:
    if not codes:
        return {}
    result = await db.execute(select(Role.code, Role.id).where(Role.code.in_(codes)))
    return {code: role_id for code, role_id in result.all()}  # noqa: C416 - mypy chặn dict()


async def get_codes_for_user(db: AsyncSession, user_id: uuid.UUID) -> list[str]:
    stmt = (
        select(Role.code)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user_id)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def assign(db: AsyncSession, user_id: uuid.UUID, role_id: uuid.UUID) -> None:
    await db.execute(insert(UserRole).values(user_id=user_id, role_id=role_id))


async def replace_for_user(db: AsyncSession, user_id: uuid.UUID, role_ids: list[uuid.UUID]) -> None:
    await db.execute(delete(UserRole).where(UserRole.user_id == user_id))
    if role_ids:
        await db.execute(
            insert(UserRole),
            [{"user_id": user_id, "role_id": role_id} for role_id in role_ids],
        )
