"""Scope job (SPEC SP-07, UC-22): mỗi actor chỉ xem/thử lại job do mình yêu cầu;
người có `job.manage` xem mọi job, kể cả job hệ thống (`requested_by` rỗng).

Job ngoài scope trả 404 như job không tồn tại, để không dò được UUID job của
người khác — nhất là job reset mật khẩu, vốn lộ việc email có tài khoản.
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import PermissionCode
from app.core.exceptions import permission_denied, resource_not_found
from app.core.permissions import user_has_permission
from app.modules.notifications import repository as notifications_repository
from app.modules.notifications.repository import JobRow
from app.modules.users.repository import UserRow


async def can_manage_jobs(db: AsyncSession, actor: UserRow) -> bool:
    return await user_has_permission(db, actor.id, PermissionCode.JOB_MANAGE)


async def ensure_can_list_all(db: AsyncSession, actor: UserRow) -> None:
    if not await can_manage_jobs(db, actor):
        raise permission_denied()


async def ensure_job_scope(db: AsyncSession, actor: UserRow, job_id: uuid.UUID) -> JobRow:
    job = await notifications_repository.get_job(db, job_id)
    if job is None:
        raise resource_not_found()
    if job.requested_by == actor.id or await can_manage_jobs(db, actor):
        return job
    raise resource_not_found()
