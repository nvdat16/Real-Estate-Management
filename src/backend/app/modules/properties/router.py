"""HTTP↔schema mapping cho căn hộ. Ghi cần `property.manage`; đọc cho người
quản lý danh mục và người lập tin (`ensure_catalog_reader`)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import PropertyStatus
from app.common.schemas.pagination import Page
from app.common.utils.pagination import PageParams, page_params
from app.core.constants import PermissionCode
from app.core.database import get_db
from app.dependencies import get_current_user, require_permission
from app.modules.projects.permissions import ensure_catalog_reader
from app.modules.properties import service as properties_service
from app.modules.properties.schemas import (
    PropertyCreateRequest,
    PropertySort,
    PropertyUpdateRequest,
    PropertyView,
)
from app.modules.users.models import User


router = APIRouter(prefix="/properties", tags=["properties"])

_require_manage = require_permission(PermissionCode.PROPERTY_MANAGE)


@router.get("", response_model=Page[PropertyView])
async def list_properties(
    project_id: uuid.UUID | None = Query(default=None),
    status: PropertyStatus | None = Query(default=None),
    q: str | None = Query(default=None, max_length=50),
    sort: PropertySort = Query(default="unit_code"),
    pagination: PageParams = Depends(page_params),
    actor: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Page[PropertyView]:
    await ensure_catalog_reader(db, actor)
    return await properties_service.list_(
        db, page_params=pagination, sort=sort, project_id=project_id, status=status, q=q
    )


@router.post("", response_model=PropertyView, status_code=201)
async def create_property(
    payload: PropertyCreateRequest,
    actor: User = Depends(_require_manage),
    db: AsyncSession = Depends(get_db),
) -> PropertyView:
    return await properties_service.create(db, actor=actor, payload=payload)


@router.get("/{property_id}", response_model=PropertyView)
async def get_property(
    property_id: uuid.UUID,
    actor: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PropertyView:
    await ensure_catalog_reader(db, actor)
    return await properties_service.get(db, property_id=property_id)


@router.patch("/{property_id}", response_model=PropertyView)
async def update_property(
    property_id: uuid.UUID,
    payload: PropertyUpdateRequest,
    actor: User = Depends(_require_manage),
    db: AsyncSession = Depends(get_db),
) -> PropertyView:
    return await properties_service.update(
        db, actor=actor, property_id=property_id, payload=payload
    )


@router.delete("/{property_id}", status_code=204)
async def delete_property(
    property_id: uuid.UUID,
    row_version: int = Query(),
    actor: User = Depends(_require_manage),
    db: AsyncSession = Depends(get_db),
) -> None:
    await properties_service.delete(
        db, actor=actor, property_id=property_id, expected_row_version=row_version
    )
