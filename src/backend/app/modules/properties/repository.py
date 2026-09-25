"""Truy vấn `properties` — chủ sở hữu: module properties. SQL tay + dataclass (ADR-011)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.common import db as sql
from app.common.enums import ContractStatus, ListingStatus, PropertyStatus
from app.common.utils import expect
from app.common.utils.pagination import PageParams, escape_like


@dataclass(frozen=True)
class PropertyRow:
    id: uuid.UUID
    project_id: uuid.UUID
    unit_code: str
    area_m2: Decimal
    bedrooms: int
    floor: int | None
    description: str | None
    status: str
    row_version: int
    created_at: datetime
    updated_at: datetime


_COLUMNS = """
    id, project_id, unit_code, area_m2, bedrooms, floor, description, status,
    row_version, created_at, updated_at
"""
_SORT_COLUMNS = {"unit_code": "unit_code", "area_m2": "area_m2", "created_at": "created_at"}
_UPDATABLE_COLUMNS = ("area_m2", "bedrooms", "floor", "description", "deleted_at", "deleted_by")


async def get_active_by_id(
    db: AsyncSession, property_id: uuid.UUID, *, for_update: bool = False
) -> PropertyRow | None:
    """Căn chưa xóa mềm. `for_update` khóa dòng để kiểm tra trạng thái rồi đổi
    trạng thái tin trong cùng transaction (thứ tự khóa căn → tin, PLAN task 6.2)."""
    lock = "FOR UPDATE" if for_update else ""
    return await sql.query_one(
        db,
        PropertyRow,
        f"SELECT {_COLUMNS} FROM properties WHERE id = :id AND deleted_at IS NULL {lock}",
        id=property_id,
    )


async def insert(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    unit_code: str,
    area_m2: Decimal,
    bedrooms: int,
    floor: int | None,
    description: str | None,
) -> PropertyRow:
    row = await sql.query_one(
        db,
        PropertyRow,
        f"""
        INSERT INTO properties
            (project_id, unit_code, area_m2, bedrooms, floor, description, status)
        VALUES
            (:project_id, :unit_code, :area_m2, :bedrooms, :floor, :description, :status)
        RETURNING {_COLUMNS}
        """,
        project_id=project_id,
        unit_code=unit_code,
        area_m2=area_m2,
        bedrooms=bedrooms,
        floor=floor,
        description=description,
        # Căn mới luôn available; trạng thái khác chỉ do luồng hợp đồng đặt.
        status=PropertyStatus.AVAILABLE.value,
    )
    return expect(row, "INSERT ... RETURNING không trả dòng nào")


async def list_page(
    db: AsyncSession,
    page_params: PageParams,
    *,
    sort: str,
    project_id: uuid.UUID | None = None,
    status: str | None = None,
    q: str | None = None,
) -> tuple[list[PropertyRow], int]:
    clauses = ["deleted_at IS NULL"]
    params: dict[str, Any] = {}
    if project_id is not None:
        clauses.append("project_id = :project_id")
        params["project_id"] = project_id
    if status:
        clauses.append("status = :status")
        params["status"] = status
    if q:
        clauses.append("unit_code ILIKE :q ESCAPE '\\'")
        params["q"] = f"%{escape_like(q)}%"
    where = sql.where(clauses)

    total = await sql.scalar(db, f"SELECT COUNT(*) FROM properties {where}", **params)
    items = await sql.query(
        db,
        PropertyRow,
        f"""
        SELECT {_COLUMNS} FROM properties {where}
        {sql.order_by(sort, _SORT_COLUMNS, "id")}
        LIMIT :limit OFFSET :offset
        """,
        **params,
        limit=page_params.page_size,
        offset=page_params.offset,
    )
    return items, int(total or 0)


async def has_open_listing(db: AsyncSession, property_id: uuid.UUID) -> bool:
    """Tin chưa đóng: mọi trạng thái trừ `closed`, bỏ qua tin đã xóa mềm."""
    return bool(
        await sql.scalar(
            db,
            """
            SELECT EXISTS (
                SELECT 1 FROM listings
                WHERE property_id = :property_id AND deleted_at IS NULL AND status <> :closed
            )
            """,
            property_id=property_id,
            closed=ListingStatus.CLOSED.value,
        )
    )


async def has_binding_contract(db: AsyncSession, property_id: uuid.UUID) -> bool:
    return bool(
        await sql.scalar(
            db,
            """
            SELECT EXISTS (
                SELECT 1 FROM contracts
                WHERE property_id = :property_id
                  AND deleted_at IS NULL
                  AND status IN (:pending_signatures, :signed)
            )
            """,
            property_id=property_id,
            pending_signatures=ContractStatus.PENDING_SIGNATURES.value,
            signed=ContractStatus.SIGNED.value,
        )
    )


async def update_fields(
    db: AsyncSession, property_id: uuid.UUID, expected_row_version: int, **fields: Any
) -> bool:
    return await sql.update_versioned(
        db,
        table="properties",
        record_id=property_id,
        expected_row_version=expected_row_version,
        fields=fields,
        allowed_columns=_UPDATABLE_COLUMNS,
    )
