"""HTTP↔schema mapping cho tra cứu audit log — chỉ Admin, chỉ đọc."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.schemas.pagination import Page
from app.common.utils.pagination import PageParams, page_params
from app.core.constants import PermissionCode
from app.core.database import get_db
from app.dependencies import require_permission
from app.modules.audit_logs import repository as audit_logs_repository
from app.modules.audit_logs.schemas import AuditLogView


router = APIRouter(
    prefix="/audit-logs",
    tags=["audit-logs"],
    dependencies=[Depends(require_permission(PermissionCode.AUDIT_READ))],
)


@router.get("", response_model=Page[AuditLogView])
async def list_audit_logs(
    entity_type: str | None = Query(default=None),
    entity_id: uuid.UUID | None = Query(default=None),
    actor_user_id: uuid.UUID | None = Query(default=None),
    pagination: PageParams = Depends(page_params),
    db: AsyncSession = Depends(get_db),
) -> Page[AuditLogView]:
    items, total = await audit_logs_repository.list_page(
        db,
        pagination,
        entity_type=entity_type,
        entity_id=entity_id,
        actor_user_id=actor_user_id,
    )
    return Page(
        items=[AuditLogView.model_validate(item, from_attributes=True) for item in items],
        page=pagination.page,
        page_size=pagination.page_size,
        total=total,
    )
