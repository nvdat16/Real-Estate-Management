"""Kiểm tra permission thuần logic, không phụ thuộc FastAPI (PLAN task 2.2).

Quyền = permission hành động + scope bản ghi (SPEC SP-01). Hàm ở đây chỉ trả
lời "actor có permission hành động X không?" — scope bản ghi được kiểm riêng ở
`permissions.py` của từng module sở hữu (không có engine scope chung).
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.roles import repository as roles_repository


async def user_has_permission(db: AsyncSession, user_id: uuid.UUID, code: str) -> bool:
    return await roles_repository.user_has_permission(db, user_id, code)
