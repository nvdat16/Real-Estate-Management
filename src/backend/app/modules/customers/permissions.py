"""Scope bản ghi cho hồ sơ khách hàng (SPEC SP-01, PLAN task 2.6).

Không có engine scope chung — mỗi module tự định nghĩa. Thứ tự kiểm ở đây có
chủ đích: tự truy cập bản thân bỏ qua permission check; thiếu permission hành
động (không phải admin, không có `customer.read_scope`) luôn là 403 dù record
có tồn tại hay không; còn lại (thiếu quyền/ngoài scope trên record cụ thể) là
404 để không tiết lộ sự tồn tại của bản ghi (SPEC §3.2).
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import PermissionCode
from app.core.exceptions import permission_denied, resource_not_found
from app.core.permissions import user_has_permission
from app.modules.agents import repository as agents_repository
from app.modules.customers import repository as customers_repository
from app.modules.customers.models import Customer
from app.modules.users.models import User


async def ensure_customer_scope(db: AsyncSession, actor: User, customer_id: uuid.UUID) -> Customer:
    record = await customers_repository.get_by_id(db, customer_id)
    if record is not None and record.user_id == actor.id:
        return record

    is_admin = await user_has_permission(db, actor.id, PermissionCode.USER_MANAGE)
    is_agent_scope = await user_has_permission(db, actor.id, PermissionCode.CUSTOMER_READ_SCOPE)
    if not is_admin and not is_agent_scope:
        raise permission_denied()

    if record is None or record.deleted_at is not None:
        raise resource_not_found()

    if is_admin:
        return record

    agent = await agents_repository.get_by_user_id(db, actor.id)
    if agent is not None and await customers_repository.has_contract_with_agent(
        db, customer_id=record.id, agent_id=agent.id
    ):
        return record
    raise resource_not_found()
