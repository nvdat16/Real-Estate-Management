"""Truy vấn `listings` — chủ sở hữu: module listings. SQL tay + dataclass (ADR-011)."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.common import db as sql
from app.common.enums import ContractStatus, ListingStatus, ProjectStatus, PropertyStatus
from app.common.utils import expect
from app.common.utils.pagination import PageParams, escape_like


@dataclass(frozen=True)
class ListingRow:
    id: uuid.UUID
    property_id: uuid.UUID
    agent_id: uuid.UUID
    listing_type: str
    asking_price: Decimal
    price_unit: str
    currency: str
    title: str
    description: str
    status: str
    reviewed_by: uuid.UUID | None
    reviewed_at: datetime | None
    rejection_reason: str | None
    row_version: int
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class PublicListingRow:
    """Một dòng join tin → căn → dự án cho API công khai; cột căn/dự án đặt tiền tố
    để không trùng tên với cột của tin."""

    id: uuid.UUID
    title: str
    description: str
    listing_type: str
    asking_price: Decimal
    price_unit: str
    currency: str
    published_at: datetime
    unit_code: str
    area_m2: Decimal
    bedrooms: int
    floor: int | None
    project_id: uuid.UUID
    project_name: str
    project_address: str
    province_code: str
    ward_code: str


@dataclass(frozen=True)
class ListingFilters:
    status: str | None = None
    listing_type: str | None = None
    property_id: uuid.UUID | None = None
    project_id: uuid.UUID | None = None
    agent_id: uuid.UUID | None = None
    q: str | None = None


@dataclass(frozen=True)
class PublicFilters:
    listing_type: str | None = None
    min_price: Decimal | None = None
    max_price: Decimal | None = None
    province_code: str | None = None
    ward_code: str | None = None
    project_id: uuid.UUID | None = None
    min_bedrooms: int | None = None
    q: str | None = None


_COLUMNS = """
    l.id, l.property_id, l.agent_id, l.listing_type, l.asking_price, l.price_unit,
    l.currency, l.title, l.description, l.status, l.reviewed_by, l.reviewed_at,
    l.rejection_reason, l.row_version, l.created_at, l.updated_at
"""
_SORT_COLUMNS = {
    "created_at": "l.created_at",
    "updated_at": "l.updated_at",
    "asking_price": "l.asking_price",
}
_UPDATABLE_COLUMNS = (
    "listing_type",
    "asking_price",
    "price_unit",
    "title",
    "description",
    "status",
    "reviewed_by",
    "reviewed_at",
    "rejection_reason",
    "deleted_at",
    "deleted_by",
)

_PUBLIC_COLUMNS = """
    l.id, l.title, l.description, l.listing_type, l.asking_price, l.price_unit, l.currency,
    l.reviewed_at AS published_at,
    p.unit_code, p.area_m2, p.bedrooms, p.floor,
    pr.id AS project_id, pr.name AS project_name, pr.address AS project_address,
    pr.province_code, pr.ward_code
"""
# Điều kiện công khai (SPEC SP-02): tin approved, căn available, dự án active,
# cả ba chưa xóa mềm. Tên tham số có tiền tố `pub_` để không đụng bộ lọc.
_PUBLIC_FROM = """
    FROM listings l
    JOIN properties p ON p.id = l.property_id
    JOIN projects pr ON pr.id = p.project_id
"""
_PUBLIC_CLAUSES = (
    "l.status = :pub_listing_status",
    "l.deleted_at IS NULL",
    "p.status = :pub_property_status",
    "p.deleted_at IS NULL",
    "pr.status = :pub_project_status",
    "pr.deleted_at IS NULL",
)
_PUBLIC_PARAMS = {
    "pub_listing_status": ListingStatus.APPROVED.value,
    "pub_property_status": PropertyStatus.AVAILABLE.value,
    "pub_project_status": ProjectStatus.ACTIVE.value,
}
_PUBLIC_SORT_COLUMNS = {"published_at": "l.reviewed_at", "asking_price": "l.asking_price"}


async def get_active_by_id(db: AsyncSession, listing_id: uuid.UUID) -> ListingRow | None:
    return await sql.query_one(
        db,
        ListingRow,
        f"SELECT {_COLUMNS} FROM listings l WHERE l.id = :id AND l.deleted_at IS NULL",
        id=listing_id,
    )


async def insert(
    db: AsyncSession,
    *,
    property_id: uuid.UUID,
    agent_id: uuid.UUID,
    listing_type: str,
    asking_price: Decimal,
    price_unit: str,
    title: str,
    description: str,
) -> ListingRow:
    row = await sql.query_one(
        db,
        ListingRow,
        f"""
        INSERT INTO listings AS l
            (property_id, agent_id, listing_type, asking_price, price_unit, title,
             description, status)
        VALUES
            (:property_id, :agent_id, :listing_type, :asking_price, :price_unit, :title,
             :description, :status)
        RETURNING {_COLUMNS}
        """,
        property_id=property_id,
        agent_id=agent_id,
        listing_type=listing_type,
        asking_price=asking_price,
        price_unit=price_unit,
        title=title,
        description=description,
        status=ListingStatus.DRAFT.value,
    )
    return expect(row, "INSERT ... RETURNING không trả dòng nào")


async def list_page(
    db: AsyncSession,
    page_params: PageParams,
    *,
    sort: str,
    filters: ListingFilters,
    scope_agent_id: uuid.UUID | None = None,
) -> tuple[list[ListingRow], int]:
    clauses = ["l.deleted_at IS NULL"]
    params: dict[str, Any] = {}
    if scope_agent_id is not None:
        clauses.append("l.agent_id = :scope_agent_id")
        params["scope_agent_id"] = scope_agent_id
    if filters.status:
        clauses.append("l.status = :status")
        params["status"] = filters.status
    if filters.listing_type:
        clauses.append("l.listing_type = :listing_type")
        params["listing_type"] = filters.listing_type
    if filters.property_id is not None:
        clauses.append("l.property_id = :property_id")
        params["property_id"] = filters.property_id
    if filters.agent_id is not None:
        clauses.append("l.agent_id = :agent_id")
        params["agent_id"] = filters.agent_id
    if filters.project_id is not None:
        clauses.append(
            "l.property_id IN (SELECT id FROM properties WHERE project_id = :project_id)"
        )
        params["project_id"] = filters.project_id
    if filters.q:
        clauses.append("l.title ILIKE :q ESCAPE '\\'")
        params["q"] = f"%{escape_like(filters.q)}%"
    where = sql.where(clauses)

    total = await sql.scalar(db, f"SELECT COUNT(*) FROM listings l {where}", **params)
    items = await sql.query(
        db,
        ListingRow,
        f"""
        SELECT {_COLUMNS} FROM listings l {where}
        {sql.order_by(sort, _SORT_COLUMNS, "l.id")}
        LIMIT :limit OFFSET :offset
        """,
        **params,
        limit=page_params.page_size,
        offset=page_params.offset,
    )
    return items, int(total or 0)


async def has_contract(
    db: AsyncSession, listing_id: uuid.UUID, statuses: Sequence[ContractStatus]
) -> bool:
    return bool(
        await sql.scalar(
            db,
            """
            SELECT EXISTS (
                SELECT 1 FROM contracts
                WHERE listing_id = :listing_id
                  AND deleted_at IS NULL
                  AND status = ANY(:statuses)
            )
            """,
            listing_id=listing_id,
            statuses=[status.value for status in statuses],
        )
    )


async def update_fields(
    db: AsyncSession, listing_id: uuid.UUID, expected_row_version: int, **fields: Any
) -> bool:
    return await sql.update_versioned(
        db,
        table="listings",
        record_id=listing_id,
        expected_row_version=expected_row_version,
        fields=fields,
        allowed_columns=_UPDATABLE_COLUMNS,
    )


async def public_list_page(
    db: AsyncSession, page_params: PageParams, *, sort: str, filters: PublicFilters
) -> tuple[list[PublicListingRow], int]:
    clauses = list(_PUBLIC_CLAUSES)
    params: dict[str, Any] = dict(_PUBLIC_PARAMS)
    if filters.listing_type:
        clauses.append("l.listing_type = :listing_type")
        params["listing_type"] = filters.listing_type
    if filters.min_price is not None:
        clauses.append("l.asking_price >= :min_price")
        params["min_price"] = filters.min_price
    if filters.max_price is not None:
        clauses.append("l.asking_price <= :max_price")
        params["max_price"] = filters.max_price
    if filters.province_code:
        clauses.append("pr.province_code = :province_code")
        params["province_code"] = filters.province_code
    if filters.ward_code:
        clauses.append("pr.ward_code = :ward_code")
        params["ward_code"] = filters.ward_code
    if filters.project_id is not None:
        clauses.append("pr.id = :project_id")
        params["project_id"] = filters.project_id
    if filters.min_bedrooms is not None:
        clauses.append("p.bedrooms >= :min_bedrooms")
        params["min_bedrooms"] = filters.min_bedrooms
    if filters.q:
        clauses.append("(l.title ILIKE :q ESCAPE '\\' OR pr.name ILIKE :q ESCAPE '\\')")
        params["q"] = f"%{escape_like(filters.q)}%"
    where = sql.where(clauses)

    total = await sql.scalar(db, f"SELECT COUNT(*) {_PUBLIC_FROM} {where}", **params)
    items = await sql.query(
        db,
        PublicListingRow,
        f"""
        SELECT {_PUBLIC_COLUMNS} {_PUBLIC_FROM} {where}
        {sql.order_by(sort, _PUBLIC_SORT_COLUMNS, "l.id")}
        LIMIT :limit OFFSET :offset
        """,
        **params,
        limit=page_params.page_size,
        offset=page_params.offset,
    )
    return items, int(total or 0)


async def public_get(db: AsyncSession, listing_id: uuid.UUID) -> PublicListingRow | None:
    clauses = [*_PUBLIC_CLAUSES, "l.id = :id"]
    return await sql.query_one(
        db,
        PublicListingRow,
        f"SELECT {_PUBLIC_COLUMNS} {_PUBLIC_FROM} {sql.where(clauses)}",
        **_PUBLIC_PARAMS,
        id=listing_id,
    )
