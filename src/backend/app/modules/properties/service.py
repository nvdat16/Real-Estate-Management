"""Use case cho căn hộ (PLAN task 3.2, UC-06)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import PropertyStatus
from app.common.schemas.pagination import Page
from app.common.utils.pagination import PageParams
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
from app.modules.properties import repository as properties_repository
from app.modules.properties.repository import PropertyRow
from app.modules.properties.schemas import (
    PropertyCreateRequest,
    PropertyUpdateRequest,
    PropertyView,
)
from app.modules.users.repository import UserRow


_REQUIRED_FIELDS = ("area_m2", "bedrooms")


def _to_view(item: PropertyRow) -> PropertyView:
    return PropertyView.model_validate(item, from_attributes=True)


async def _get_or_404(db: AsyncSession, property_id: uuid.UUID) -> PropertyRow:
    item = await properties_repository.get_active_by_id(db, property_id)
    if item is None:
        raise resource_not_found()
    return item


async def create(
    db: AsyncSession, *, actor: UserRow, payload: PropertyCreateRequest
) -> PropertyView:
    if await projects_repository.get_active_by_id(db, payload.project_id) is None:
        raise validation_error({"project_id": str(payload.project_id), "reason": "not_found"})

    try:
        async with db.begin_nested():
            item = await properties_repository.insert(db, **payload.model_dump())
    except IntegrityError as exc:
        raise duplicate_resource("unit_code") from exc

    await record_audit(
        db,
        actor=actor,
        action="property.create",
        entity_type="properties",
        entity_id=item.id,
        change_summary={"project_id": str(item.project_id), "unit_code": item.unit_code},
    )
    await db.commit()
    return _to_view(item)


async def get(db: AsyncSession, *, property_id: uuid.UUID) -> PropertyView:
    return _to_view(await _get_or_404(db, property_id))


async def list_(
    db: AsyncSession,
    *,
    page_params: PageParams,
    sort: str,
    project_id: uuid.UUID | None,
    status: str | None,
    q: str | None,
) -> Page[PropertyView]:
    items, total = await properties_repository.list_page(
        db, page_params, sort=sort, project_id=project_id, status=status, q=q
    )
    return Page(
        items=[_to_view(item) for item in items],
        page=page_params.page,
        page_size=page_params.page_size,
        total=total,
    )


async def update(
    db: AsyncSession, *, actor: UserRow, property_id: uuid.UUID, payload: PropertyUpdateRequest
) -> PropertyView:
    item = await _get_or_404(db, property_id)
    fields: dict[str, Any] = payload.model_dump(exclude_unset=True)
    fields.pop("row_version")

    null_required = [name for name in _REQUIRED_FIELDS if name in fields and fields[name] is None]
    if null_required:
        raise validation_error({"fields": null_required, "reason": "must_not_be_null"})
    # Căn đang giữ cho hợp đồng chờ ký: mô tả căn là một phần nội dung hợp đồng
    # sắp ký nên không được đổi (SPEC SP-02).
    if fields and item.status == PropertyStatus.RESERVED:
        raise invalid_state("Căn đang giữ cho hợp đồng chờ ký, chưa thể sửa.")

    ok = await properties_repository.update_fields(db, item.id, payload.row_version, **fields)
    if not ok:
        raise version_conflict()
    await record_audit(
        db,
        actor=actor,
        action="property.update",
        entity_type="properties",
        entity_id=item.id,
        change_summary=payload.model_dump(mode="json", exclude_unset=True, exclude={"row_version"}),
    )
    await db.commit()
    return _to_view(await _get_or_404(db, item.id))


async def delete(
    db: AsyncSession, *, actor: UserRow, property_id: uuid.UUID, expected_row_version: int
) -> None:
    item = await _get_or_404(db, property_id)
    if await properties_repository.has_open_listing(db, item.id):
        raise dependency_exists("Căn còn tin đăng chưa đóng.")
    if await properties_repository.has_binding_contract(db, item.id):
        raise dependency_exists("Căn có hợp đồng đang chờ ký hoặc đã ký.")

    ok = await properties_repository.update_fields(
        db,
        item.id,
        expected_row_version,
        deleted_at=datetime.now(UTC),
        deleted_by=actor.id,
    )
    if not ok:
        raise version_conflict()
    await record_audit(
        db,
        actor=actor,
        action="property.delete",
        entity_type="properties",
        entity_id=item.id,
        change_summary={"unit_code": item.unit_code},
    )
    await db.commit()
