"""HTTP↔schema mapping cho hồ sơ môi giới. `GET /agents` là admin-only (danh
sách môi giới không có khái niệm "scope" như customers)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.schemas.pagination import Page
from app.common.utils.pagination import PageParams, page_params
from app.core.constants import PermissionCode
from app.core.database import get_db
from app.dependencies import get_current_user, require_permission
from app.modules.agents import service as agents_service
from app.modules.agents.schemas import AgentUpdateRequest, AgentView
from app.modules.users.repository import UserRow


router = APIRouter(prefix="/agents", tags=["agents"])


@router.get(
    "",
    response_model=Page[AgentView],
    dependencies=[Depends(require_permission(PermissionCode.USER_MANAGE))],
)
async def list_agents(
    pagination: PageParams = Depends(page_params),
    db: AsyncSession = Depends(get_db),
) -> Page[AgentView]:
    return await agents_service.list_(db, page_params=pagination)


@router.get("/{agent_id}", response_model=AgentView)
async def get_agent(
    agent_id: uuid.UUID,
    actor: UserRow = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AgentView:
    return await agents_service.get(db, actor=actor, agent_id=agent_id)


@router.patch("/{agent_id}", response_model=AgentView)
async def update_agent(
    agent_id: uuid.UUID,
    payload: AgentUpdateRequest,
    actor: UserRow = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AgentView:
    return await agents_service.update(
        db,
        actor=actor,
        agent_id=agent_id,
        full_name=payload.full_name,
        phone=payload.phone,
        expected_row_version=payload.row_version,
    )
