"""Scope bản ghi cho hồ sơ môi giới — chỉ self-or-admin (PLAN task 2.6)."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import PermissionCode
from app.core.exceptions import permission_denied, resource_not_found
from app.core.permissions import user_has_permission
from app.modules.agents import repository as agents_repository
from app.modules.agents.repository import AgentRow
from app.modules.users.repository import UserRow


async def ensure_agent_scope(db: AsyncSession, actor: UserRow, agent_id: uuid.UUID) -> AgentRow:
    record = await agents_repository.get_by_id(db, agent_id)
    if record is not None and record.user_id == actor.id:
        return record

    if not await user_has_permission(db, actor.id, PermissionCode.USER_MANAGE):
        raise permission_denied()

    if record is None or record.deleted_at is not None:
        raise resource_not_found()
    return record
