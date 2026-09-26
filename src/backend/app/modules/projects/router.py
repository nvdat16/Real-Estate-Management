"""HTTP↔schema mapping cho dự án. Ghi cần `project.manage`; đọc cho người quản
lý danh mục và người lập tin. `public_router` phục vụ danh mục cho trang tìm
kiếm công khai, không cần đăng nhập."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import ProjectStatus
from app.common.schemas.pagination import Page
from app.common.utils.pagination import PageParams, page_params
from app.core.constants import PermissionCode
from app.core.database import get_db
from app.dependencies import get_current_user, require_permission
from app.modules.projects import service as projects_service
from app.modules.projects.permissions import ensure_catalog_reader
from app.modules.projects.schemas import (
    CatalogView,
    ProjectCreateRequest,
    ProjectSort,
    ProjectUpdateRequest,
    ProjectView,
)
from app.modules.users.repository import UserRow


router = APIRouter(prefix="/projects", tags=["projects"])
public_router = APIRouter(prefix="/public", tags=["public"])

_require_manage = require_permission(PermissionCode.PROJECT_MANAGE)


@router.get("", response_model=Page[ProjectView])
async def list_projects(
    q: str | None = Query(default=None, max_length=200),
    province_code: str | None = Query(default=None, max_length=10),
    ward_code: str | None = Query(default=None, max_length=10),
    status: ProjectStatus | None = Query(default=None),
    sort: ProjectSort = Query(default="-created_at"),
    pagination: PageParams = Depends(page_params),
    actor: UserRow = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Page[ProjectView]:
    await ensure_catalog_reader(db, actor)
    return await projects_service.list_(
        db,
        page_params=pagination,
        sort=sort,
        q=q,
        province_code=province_code,
        ward_code=ward_code,
        status=status,
    )


@router.post("", response_model=ProjectView, status_code=201)
async def create_project(
    payload: ProjectCreateRequest,
    actor: UserRow = Depends(_require_manage),
    db: AsyncSession = Depends(get_db),
) -> ProjectView:
    return await projects_service.create(db, actor=actor, payload=payload)


@router.get("/{project_id}", response_model=ProjectView)
async def get_project(
    project_id: uuid.UUID,
    actor: UserRow = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectView:
    await ensure_catalog_reader(db, actor)
    return await projects_service.get(db, project_id=project_id)


@router.patch("/{project_id}", response_model=ProjectView)
async def update_project(
    project_id: uuid.UUID,
    payload: ProjectUpdateRequest,
    actor: UserRow = Depends(_require_manage),
    db: AsyncSession = Depends(get_db),
) -> ProjectView:
    return await projects_service.update(db, actor=actor, project_id=project_id, payload=payload)


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: uuid.UUID,
    row_version: int = Query(),
    actor: UserRow = Depends(_require_manage),
    db: AsyncSession = Depends(get_db),
) -> None:
    await projects_service.delete(
        db, actor=actor, project_id=project_id, expected_row_version=row_version
    )


@public_router.get("/catalog", response_model=CatalogView)
async def get_public_catalog(db: AsyncSession = Depends(get_db)) -> CatalogView:
    return await projects_service.get_catalog(db)
