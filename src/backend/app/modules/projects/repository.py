"""Truy vấn `projects` — chủ sở hữu: module projects. SQL tay + dataclass (ADR-011)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.common import db as sql
from app.common.enums import ProjectStatus, PropertyStatus
from app.common.utils import expect
from app.common.utils.pagination import PageParams, escape_like


@dataclass(frozen=True)
class ProjectRow:
    id: uuid.UUID
    code: str
    name: str
    address: str
    province_code: str
    ward_code: str
    description: str | None
    status: str
    row_version: int
    created_at: datetime
    updated_at: datetime


_COLUMNS = """
    id, code, name, address, province_code, ward_code, description, status,
    row_version, created_at, updated_at
"""
_SORT_COLUMNS = {"code": "code", "name": "name", "created_at": "created_at"}
_UPDATABLE_COLUMNS = (
    "name",
    "address",
    "province_code",
    "ward_code",
    "description",
    "status",
    "deleted_at",
    "deleted_by",
)


async def get_active_by_id(db: AsyncSession, project_id: uuid.UUID) -> ProjectRow | None:
    """Dự án chưa xóa mềm (không xét `status`)."""
    return await sql.query_one(
        db,
        ProjectRow,
        f"SELECT {_COLUMNS} FROM projects WHERE id = :id AND deleted_at IS NULL",
        id=project_id,
    )


async def insert(
    db: AsyncSession,
    *,
    code: str,
    name: str,
    address: str,
    province_code: str,
    ward_code: str,
    description: str | None,
    status: str,
) -> ProjectRow:
    row = await sql.query_one(
        db,
        ProjectRow,
        f"""
        INSERT INTO projects (code, name, address, province_code, ward_code, description, status)
        VALUES (:code, :name, :address, :province_code, :ward_code, :description, :status)
        RETURNING {_COLUMNS}
        """,
        code=code,
        name=name,
        address=address,
        province_code=province_code,
        ward_code=ward_code,
        description=description,
        status=status,
    )
    return expect(row, "INSERT ... RETURNING không trả dòng nào")


async def list_page(
    db: AsyncSession,
    page_params: PageParams,
    *,
    sort: str,
    q: str | None = None,
    province_code: str | None = None,
    ward_code: str | None = None,
    status: str | None = None,
) -> tuple[list[ProjectRow], int]:
    clauses = ["deleted_at IS NULL"]
    params: dict[str, Any] = {}
    if q:
        clauses.append("(code ILIKE :q ESCAPE '\\' OR name ILIKE :q ESCAPE '\\')")
        params["q"] = f"%{escape_like(q)}%"
    if province_code:
        clauses.append("province_code = :province_code")
        params["province_code"] = province_code
    if ward_code:
        clauses.append("ward_code = :ward_code")
        params["ward_code"] = ward_code
    if status:
        clauses.append("status = :status")
        params["status"] = status
    where = sql.where(clauses)

    total = await sql.scalar(db, f"SELECT COUNT(*) FROM projects {where}", **params)
    items = await sql.query(
        db,
        ProjectRow,
        f"""
        SELECT {_COLUMNS} FROM projects {where}
        {sql.order_by(sort, _SORT_COLUMNS, "id")}
        LIMIT :limit OFFSET :offset
        """,
        **params,
        limit=page_params.page_size,
        offset=page_params.offset,
    )
    return items, int(total or 0)


async def list_active_for_catalog(db: AsyncSession) -> list[ProjectRow]:
    return await sql.query(
        db,
        ProjectRow,
        f"""
        SELECT {_COLUMNS} FROM projects
        WHERE deleted_at IS NULL AND status = :status
        ORDER BY name, id
        """,
        status=ProjectStatus.ACTIVE.value,
    )


async def has_live_properties(db: AsyncSession, project_id: uuid.UUID) -> bool:
    return bool(
        await sql.scalar(
            db,
            """
            SELECT EXISTS (
                SELECT 1 FROM properties WHERE project_id = :project_id AND deleted_at IS NULL
            )
            """,
            project_id=project_id,
        )
    )


async def has_reserved_properties(db: AsyncSession, project_id: uuid.UUID) -> bool:
    """Căn `reserved` nghĩa là có hợp đồng đang chờ ký trên dự án (SPEC SP-02)."""
    return bool(
        await sql.scalar(
            db,
            """
            SELECT EXISTS (
                SELECT 1 FROM properties
                WHERE project_id = :project_id AND deleted_at IS NULL AND status = :status
            )
            """,
            project_id=project_id,
            status=PropertyStatus.RESERVED.value,
        )
    )


async def update_fields(
    db: AsyncSession, project_id: uuid.UUID, expected_row_version: int, **fields: Any
) -> bool:
    return await sql.update_versioned(
        db,
        table="projects",
        record_id=project_id,
        expected_row_version=expected_row_version,
        fields=fields,
        allowed_columns=_UPDATABLE_COLUMNS,
    )
