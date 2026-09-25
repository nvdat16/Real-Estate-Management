"""Use case cho hồ sơ môi giới (PLAN task 2.6, cộng slice
`create_agent_profile` mà `users.create_agent` cần)."""

from __future__ import annotations

import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.schemas.pagination import Page
from app.common.utils import expect
from app.common.utils.codes import generate_code
from app.common.utils.pagination import PageParams
from app.core.exceptions import version_conflict
from app.modules.agents import repository as agents_repository
from app.modules.agents.models import Agent
from app.modules.agents.permissions import ensure_agent_scope
from app.modules.agents.schemas import AgentView
from app.modules.users import repository as users_repository
from app.modules.users.models import User


async def has_profile(db: AsyncSession, user_id: uuid.UUID) -> bool:
    return await agents_repository.get_by_user_id(db, user_id) is not None


async def create_agent_profile(db: AsyncSession, user_id: uuid.UUID) -> Agent:
    for _ in range(5):
        try:
            async with db.begin_nested():
                agent = Agent(user_id=user_id, agent_code=generate_code("MG"))
                db.add(agent)
                await db.flush()
        except IntegrityError:
            continue
        return agent
    raise RuntimeError("Không sinh được agent_code duy nhất sau nhiều lần thử")


def _to_view(agent: Agent, user: User) -> AgentView:
    return AgentView(
        id=agent.id,
        agent_code=agent.agent_code,
        full_name=user.full_name,
        email=user.email,
        phone=user.phone,
        status=agent.status,
        row_version=agent.row_version,
    )


async def get(db: AsyncSession, *, actor: User, agent_id: uuid.UUID) -> AgentView:
    await ensure_agent_scope(db, actor, agent_id)
    pair = expect(await agents_repository.get_with_user(db, agent_id))
    return _to_view(*pair)


async def list_(db: AsyncSession, *, page_params: PageParams) -> Page[AgentView]:
    """Chỉ Admin gọi được (chặn ở router bằng `require_permission`)."""
    pairs, total = await agents_repository.list_page(db, page_params)
    items = [_to_view(agent, user) for agent, user in pairs]
    return Page(items=items, page=page_params.page, page_size=page_params.page_size, total=total)


async def update(
    db: AsyncSession,
    *,
    actor: User,
    agent_id: uuid.UUID,
    full_name: str,
    phone: str | None,
    expected_row_version: int,
) -> AgentView:
    agent = await ensure_agent_scope(db, actor, agent_id)
    ok = await agents_repository.update_fields(db, agent_id, expected_row_version)
    if not ok:
        raise version_conflict()
    await users_repository.set_contact_fields(db, agent.user_id, full_name=full_name, phone=phone)
    await db.commit()

    pair = expect(await agents_repository.get_with_user(db, agent_id))
    return _to_view(*pair)
