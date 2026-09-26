"""Truy vấn `roles`/`user_roles`/`role_permissions` — SQL tay (ADR-011).

Bảng bridge không có nghiệp vụ độc lập nên `auth`/`users`/service khác gọi trực
tiếp module này (ngoại lệ có chủ đích, xem PLAN Phase 2 — không có endpoint
`/roles` riêng).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.common import db as sql


@dataclass(frozen=True)
class RoleRef:
    code: str
    id: uuid.UUID


async def get_id_by_code(db: AsyncSession, code: str) -> uuid.UUID | None:
    role = await sql.query_one(
        db, RoleRef, "SELECT code, id FROM roles WHERE code = :code", code=code
    )
    return role.id if role is not None else None


async def get_ids_by_codes(db: AsyncSession, codes: list[str]) -> dict[str, uuid.UUID]:
    if not codes:
        return {}
    roles = await sql.query(
        db, RoleRef, "SELECT code, id FROM roles WHERE code = ANY(:codes)", codes=codes
    )
    return {role.code: role.id for role in roles}


async def get_codes_for_user(db: AsyncSession, user_id: uuid.UUID) -> list[str]:
    return await sql.column(
        db,
        """
        SELECT r.code FROM roles r
        JOIN user_roles ur ON ur.role_id = r.id
        WHERE ur.user_id = :user_id
        ORDER BY r.code
        """,
        user_id=user_id,
    )


async def user_has_permission(db: AsyncSession, user_id: uuid.UUID, code: str) -> bool:
    return bool(
        await sql.scalar(
            db,
            """
            SELECT EXISTS (
                SELECT 1 FROM user_roles ur
                JOIN role_permissions rp ON rp.role_id = ur.role_id
                JOIN permissions p ON p.id = rp.permission_id
                WHERE ur.user_id = :user_id AND p.code = :code
            )
            """,
            user_id=user_id,
            code=code,
        )
    )


async def assign(db: AsyncSession, user_id: uuid.UUID, role_id: uuid.UUID) -> None:
    await sql.execute(
        db,
        "INSERT INTO user_roles (user_id, role_id) VALUES (:user_id, :role_id)",
        user_id=user_id,
        role_id=role_id,
    )


async def replace_for_user(db: AsyncSession, user_id: uuid.UUID, role_ids: list[uuid.UUID]) -> None:
    await sql.execute(db, "DELETE FROM user_roles WHERE user_id = :user_id", user_id=user_id)
    if role_ids:
        await sql.execute(
            db,
            """
            INSERT INTO user_roles (user_id, role_id)
            SELECT :user_id, role_id FROM unnest(CAST(:role_ids AS uuid[])) AS role_id
            """,
            user_id=user_id,
            role_ids=role_ids,
        )
