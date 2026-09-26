"""Truy vấn `audit_logs` — chủ sở hữu: module audit_logs. SQL tay (ADR-011).

Chỉ ghi thêm và đọc; không có hàm sửa/xóa (SPEC SP-07).
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.common import db as sql
from app.common.utils.pagination import PageParams


@dataclass(frozen=True)
class AuditLogRow:
    id: uuid.UUID
    actor_user_id: uuid.UUID | None
    actor_type: str
    action: str
    entity_type: str
    entity_id: uuid.UUID
    change_summary: dict[str, Any] | None
    request_id: str | None
    created_at: datetime


_COLUMNS = """
    id, actor_user_id, actor_type, action, entity_type, entity_id, change_summary,
    request_id, created_at
"""


async def insert(
    db: AsyncSession,
    *,
    actor_user_id: uuid.UUID | None,
    actor_type: str,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID,
    change_summary: dict[str, Any] | None,
    request_id: str | None,
) -> None:
    await sql.execute(
        db,
        """
        INSERT INTO audit_logs
            (actor_user_id, actor_type, action, entity_type, entity_id, change_summary,
             request_id)
        VALUES
            (:actor_user_id, :actor_type, :action, :entity_type, :entity_id,
             CAST(:change_summary AS jsonb), :request_id)
        """,
        actor_user_id=actor_user_id,
        actor_type=actor_type,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        # JSONB đi qua text() dưới dạng chuỗi JSON; `default=str` cho UUID/Decimal/datetime.
        change_summary=(
            json.dumps(change_summary, ensure_ascii=False, default=str)
            if change_summary is not None
            else None
        ),
        request_id=request_id,
    )


async def list_page(
    db: AsyncSession,
    page_params: PageParams,
    *,
    entity_type: str | None = None,
    entity_id: uuid.UUID | None = None,
    actor_user_id: uuid.UUID | None = None,
) -> tuple[list[AuditLogRow], int]:
    clauses: list[str] = []
    params: dict[str, Any] = {}
    if entity_type is not None:
        clauses.append("entity_type = :entity_type")
        params["entity_type"] = entity_type
    if entity_id is not None:
        clauses.append("entity_id = :entity_id")
        params["entity_id"] = entity_id
    if actor_user_id is not None:
        clauses.append("actor_user_id = :actor_user_id")
        params["actor_user_id"] = actor_user_id
    where = sql.where(clauses)

    total = await sql.scalar(db, f"SELECT COUNT(*) FROM audit_logs {where}", **params)
    items = await sql.query(
        db,
        AuditLogRow,
        f"""
        SELECT {_COLUMNS} FROM audit_logs {where}
        ORDER BY created_at DESC, id ASC
        LIMIT :limit OFFSET :offset
        """,
        **params,
        limit=page_params.page_size,
        offset=page_params.offset,
    )
    return items, int(total or 0)
