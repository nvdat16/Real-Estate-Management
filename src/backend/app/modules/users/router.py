"""HTTP↔schema mapping cho quản lý tài khoản — toàn bộ endpoint admin-only."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.schemas.pagination import Page
from app.common.utils.pagination import PageParams, page_params
from app.core.constants import PermissionCode
from app.core.database import get_db
from app.dependencies import get_current_user, require_permission
from app.modules.users import service as users_service
from app.modules.users.repository import UserRow
from app.modules.users.schemas import (
    CreateAgentRequest,
    LockRequest,
    ReplaceRolesRequest,
    UnlockRequest,
    UserAdminView,
)


router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(require_permission(PermissionCode.USER_MANAGE))],
)


@router.get("", response_model=Page[UserAdminView])
async def list_users(
    pagination: PageParams = Depends(page_params),
    db: AsyncSession = Depends(get_db),
) -> Page[UserAdminView]:
    return await users_service.list_users(db, page_params=pagination)


@router.post("", response_model=UserAdminView, status_code=201)
async def create_agent(
    payload: CreateAgentRequest,
    actor: UserRow = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserAdminView:
    return await users_service.create_agent(
        db,
        actor=actor,
        email=payload.email,
        full_name=payload.full_name,
        phone=payload.phone,
        password=payload.password,
    )


@router.put("/{user_id}/roles", response_model=UserAdminView)
async def replace_roles(
    user_id: uuid.UUID,
    payload: ReplaceRolesRequest,
    actor: UserRow = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserAdminView:
    return await users_service.replace_roles(
        db,
        actor=actor,
        target_id=user_id,
        role_codes=payload.role_codes,
        expected_row_version=payload.row_version,
    )


@router.post("/{user_id}/lock", response_model=UserAdminView)
async def lock_user(
    user_id: uuid.UUID,
    payload: LockRequest,
    actor: UserRow = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserAdminView:
    return await users_service.lock(
        db, actor=actor, target_id=user_id, expected_row_version=payload.row_version
    )


@router.post("/{user_id}/unlock", response_model=UserAdminView)
async def unlock_user(
    user_id: uuid.UUID,
    payload: UnlockRequest,
    actor: UserRow = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserAdminView:
    return await users_service.unlock(
        db, actor=actor, target_id=user_id, expected_row_version=payload.row_version
    )
