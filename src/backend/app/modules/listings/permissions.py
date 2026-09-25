"""Quyền và scope cho tin đăng (SPEC SP-02, bảng chuyển trạng thái).

- `listing.approve` (Admin) là người duyệt: thấy và quản lý mọi tin.
- `listing.manage` không kèm `listing.approve` (môi giới): chỉ tin có
  `agent_id` là hồ sơ môi giới của chính mình; tin của người khác trả 404 để
  không lộ sự tồn tại (SPEC §3.2).
- Không có permission nào ở trên: 403 dù tin có tồn tại hay không.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import PermissionCode
from app.core.exceptions import permission_denied, resource_not_found
from app.core.permissions import user_has_permission
from app.modules.agents import repository as agents_repository
from app.modules.agents.models import Agent
from app.modules.listings.repository import ListingRow
from app.modules.users.models import User


@dataclass(frozen=True)
class ListingActor:
    user: User
    can_manage: bool
    can_review: bool
    agent: Agent | None

    @property
    def sees_all(self) -> bool:
        return self.can_review


async def resolve_actor(db: AsyncSession, user: User) -> ListingActor:
    can_manage = await user_has_permission(db, user.id, PermissionCode.LISTING_MANAGE)
    can_review = await user_has_permission(db, user.id, PermissionCode.LISTING_APPROVE)
    if not can_manage and not can_review:
        raise permission_denied()
    agent = await agents_repository.get_by_user_id(db, user.id)
    if agent is not None and agent.deleted_at is not None:
        agent = None
    return ListingActor(user=user, can_manage=can_manage, can_review=can_review, agent=agent)


def ensure_in_scope(actor: ListingActor, listing: ListingRow | None) -> ListingRow:
    if listing is None:
        raise resource_not_found()
    if actor.sees_all:
        return listing
    if actor.agent is not None and listing.agent_id == actor.agent.id:
        return listing
    raise resource_not_found()


def ensure_can_manage(actor: ListingActor) -> None:
    if not actor.can_manage:
        raise permission_denied()


def ensure_can_review(actor: ListingActor) -> None:
    if not actor.can_review:
        raise permission_denied()
