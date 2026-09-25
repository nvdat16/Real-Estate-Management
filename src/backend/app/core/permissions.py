"""Kiểm tra permission thuần logic, không phụ thuộc FastAPI (PLAN task 2.2).

Quyền = permission hành động + scope bản ghi (SPEC SP-01). Hàm ở đây chỉ trả
lời "actor có permission hành động X không?" — scope bản ghi được kiểm riêng ở
`permissions.py` của từng module sở hữu (không có engine scope chung).
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.roles.models import Permission, RolePermission, UserRole


async def user_has_permission(db: AsyncSession, user_id: uuid.UUID, code: str) -> bool:
    stmt = (
        select(UserRole.role_id)
        .join(RolePermission, RolePermission.role_id == UserRole.role_id)
        .join(Permission, Permission.id == RolePermission.permission_id)
        .where(UserRole.user_id == user_id, Permission.code == code)
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.first() is not None
