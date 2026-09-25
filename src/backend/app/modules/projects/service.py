"""Use case cho dự án (PLAN task 3.1, UC-05) và danh mục công khai (task 3.5)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import ProjectStatus
from app.common.schemas.pagination import Page
from app.common.utils.pagination import PageParams
from app.core import cache
from app.core.exceptions import (
    dependency_exists,
    duplicate_resource,
    invalid_state,
    resource_not_found,
    validation_error,
    version_conflict,
)
from app.modules.audit_logs.service import record_audit
from app.modules.projects import repository as projects_repository
from app.modules.projects.locations import LOCATIONS, is_known_location
from app.modules.projects.repository import ProjectRow
from app.modules.projects.schemas import (
    CatalogProjectView,
    CatalogView,
    LocationView,
    ProjectCreateRequest,
    ProjectUpdateRequest,
    ProjectView,
)
from app.modules.users.models import User


CATALOG_CACHE_KEY = "catalog:v1"
CATALOG_CACHE_TTL_SECONDS = 60

# Cột NOT NULL: PATCH gửi `null` tường minh cho các trường này là dữ liệu sai.
_REQUIRED_FIELDS = ("name", "address", "province_code", "ward_code", "status")


def _to_view(project: ProjectRow) -> ProjectView:
    return ProjectView.model_validate(project, from_attributes=True)


def _ensure_location(province_code: str, ward_code: str) -> None:
    if not is_known_location(province_code, ward_code):
        raise validation_error(
            {"province_code": province_code, "ward_code": ward_code, "reason": "unknown_location"}
        )


async def _get_or_404(db: AsyncSession, project_id: uuid.UUID) -> ProjectRow:
    project = await projects_repository.get_active_by_id(db, project_id)
    if project is None:
        raise resource_not_found()
    return project


async def create(db: AsyncSession, *, actor: User, payload: ProjectCreateRequest) -> ProjectView:
    _ensure_location(payload.province_code, payload.ward_code)
    try:
        async with db.begin_nested():
            project = await projects_repository.insert(db, **payload.model_dump(mode="json"))
    except IntegrityError as exc:
        raise duplicate_resource("code") from exc

    await record_audit(
        db,
        actor=actor,
        action="project.create",
        entity_type="projects",
        entity_id=project.id,
        change_summary={"code": project.code, "status": project.status},
    )
    await db.commit()
    await cache.delete(CATALOG_CACHE_KEY)
    return _to_view(project)


async def get(db: AsyncSession, *, project_id: uuid.UUID) -> ProjectView:
    return _to_view(await _get_or_404(db, project_id))


async def list_(
    db: AsyncSession,
    *,
    page_params: PageParams,
    sort: str,
    q: str | None,
    province_code: str | None,
    ward_code: str | None,
    status: str | None,
) -> Page[ProjectView]:
    items, total = await projects_repository.list_page(
        db,
        page_params,
        sort=sort,
        q=q,
        province_code=province_code,
        ward_code=ward_code,
        status=status,
    )
    return Page(
        items=[_to_view(item) for item in items],
        page=page_params.page,
        page_size=page_params.page_size,
        total=total,
    )


async def update(
    db: AsyncSession, *, actor: User, project_id: uuid.UUID, payload: ProjectUpdateRequest
) -> ProjectView:
    project = await _get_or_404(db, project_id)
    fields: dict[str, Any] = payload.model_dump(mode="json", exclude_unset=True)
    fields.pop("row_version")

    null_required = [name for name in _REQUIRED_FIELDS if name in fields and fields[name] is None]
    if null_required:
        raise validation_error({"fields": null_required, "reason": "must_not_be_null"})
    if "province_code" in fields or "ward_code" in fields:
        _ensure_location(
            fields.get("province_code", project.province_code),
            fields.get("ward_code", project.ward_code),
        )
    # Căn `reserved` đang giữ cho hợp đồng chờ ký: không đổi thông tin dự án mà
    # hợp đồng đó tham chiếu, cũng không chuyển dự án sang inactive (SPEC SP-02).
    if fields and await projects_repository.has_reserved_properties(db, project.id):
        raise invalid_state("Dự án có căn đang giữ cho hợp đồng chờ ký, chưa thể sửa.")

    ok = await projects_repository.update_fields(db, project.id, payload.row_version, **fields)
    if not ok:
        raise version_conflict()
    await record_audit(
        db,
        actor=actor,
        action="project.update",
        entity_type="projects",
        entity_id=project.id,
        change_summary=fields,
    )
    await db.commit()
    await cache.delete(CATALOG_CACHE_KEY)
    return _to_view(await _get_or_404(db, project.id))


async def delete(
    db: AsyncSession, *, actor: User, project_id: uuid.UUID, expected_row_version: int
) -> None:
    project = await _get_or_404(db, project_id)
    if await projects_repository.has_live_properties(db, project.id):
        raise dependency_exists("Dự án còn căn hộ chưa xóa.")

    ok = await projects_repository.update_fields(
        db,
        project.id,
        expected_row_version,
        deleted_at=datetime.now(UTC),
        deleted_by=actor.id,
    )
    if not ok:
        raise version_conflict()
    await record_audit(
        db,
        actor=actor,
        action="project.delete",
        entity_type="projects",
        entity_id=project.id,
        change_summary={"code": project.code},
    )
    await db.commit()
    await cache.delete(CATALOG_CACHE_KEY)


async def get_catalog(db: AsyncSession) -> CatalogView:
    cached = await cache.get_json(CATALOG_CACHE_KEY)
    if cached is not None:
        return CatalogView.model_validate(cached)

    projects = await projects_repository.list_active_for_catalog(db)
    catalog = CatalogView(
        locations=[
            LocationView(
                province_code=item.province_code,
                ward_code=item.ward_code,
                province_name=item.province_name,
                ward_name=item.ward_name,
            )
            for item in LOCATIONS
        ],
        projects=[CatalogProjectView.model_validate(p, from_attributes=True) for p in projects],
    )
    await cache.set_json(
        CATALOG_CACHE_KEY, catalog.model_dump(mode="json"), ttl_seconds=CATALOG_CACHE_TTL_SECONDS
    )
    return catalog


async def is_active(db: AsyncSession, project_id: uuid.UUID) -> bool:
    project = await projects_repository.get_active_by_id(db, project_id)
    return project is not None and project.status == ProjectStatus.ACTIVE
