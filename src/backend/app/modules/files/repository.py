"""Truy vấn `files` — chủ sở hữu: module files. SQL tay + dataclass (ADR-011).

`storage_key` có trong `FileRow` cho service đọc kho tệp, nhưng không schema
response nào lấy trường này (SPEC SP-06: không trả đường dẫn nội bộ).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.common import db as sql
from app.common.enums import FileStatus
from app.common.utils import expect


@dataclass(frozen=True)
class FileRow:
    id: uuid.UUID
    uploaded_by: uuid.UUID | None
    storage_key: str
    original_name: str | None
    mime_type: str
    size_bytes: int | None
    sha256: str | None
    purpose: str
    status: str
    created_at: datetime
    updated_at: datetime


_COLUMNS = """
    id, uploaded_by, storage_key, original_name, mime_type, size_bytes, sha256, purpose,
    status, created_at, updated_at
"""


async def insert_ready(
    db: AsyncSession,
    *,
    uploaded_by: uuid.UUID | None,
    storage_key: str,
    original_name: str | None,
    mime_type: str,
    size_bytes: int,
    sha256: str,
    purpose: str,
) -> FileRow:
    """Tệp đã nằm trọn trong kho (ghi xong rồi mới insert), nên vào thẳng `ready`."""
    row = await sql.query_one(
        db,
        FileRow,
        f"""
        INSERT INTO files
            (uploaded_by, storage_key, original_name, mime_type, size_bytes, sha256, purpose,
             status)
        VALUES
            (:uploaded_by, :storage_key, :original_name, :mime_type, :size_bytes, :sha256,
             :purpose, :status)
        RETURNING {_COLUMNS}
        """,
        uploaded_by=uploaded_by,
        storage_key=storage_key,
        original_name=original_name,
        mime_type=mime_type,
        size_bytes=size_bytes,
        sha256=sha256,
        purpose=purpose,
        status=FileStatus.READY.value,
    )
    return expect(row, "INSERT ... RETURNING không trả dòng nào")


async def get_by_id(db: AsyncSession, file_id: uuid.UUID) -> FileRow | None:
    return await sql.query_one(
        db, FileRow, f"SELECT {_COLUMNS} FROM files WHERE id = :id", id=file_id
    )
