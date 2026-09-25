"""Bảng `files` — chủ sở hữu: module files.

`storage_key` là khóa trong kho tệp riêng tư, không phải URL công khai. Chỉ khi
`status = ready` mới có `sha256` và `size_bytes`, và chỉ tệp ready được cấp tải
(ERD mục 4, SPEC SP-06).
"""

from __future__ import annotations

import uuid

from sqlalchemy import BigInteger, CheckConstraint, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.common.enums import FilePurpose, FileStatus, sql_in
from app.common.mixins import TimestampMixin, uuid_fk, uuid_pk
from app.core.database import Base


class File(Base, TimestampMixin):
    __tablename__ = "files"

    id: Mapped[uuid.UUID] = uuid_pk()
    # Nullable cho tệp do hệ thống sinh sau khi ký (worker ghi thay người yêu cầu).
    uploaded_by: Mapped[uuid.UUID | None] = uuid_fk("users.id", nullable=True)
    storage_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    original_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    purpose: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        server_default=text(f"'{FileStatus.PENDING}'"),
    )

    __table_args__ = (
        CheckConstraint(sql_in("purpose", FilePurpose), name="purpose_valid"),
        CheckConstraint(sql_in("status", FileStatus), name="status_valid"),
        CheckConstraint("size_bytes IS NULL OR size_bytes >= 0", name="size_non_negative"),
        CheckConstraint(
            "status <> 'ready' OR (sha256 IS NOT NULL AND size_bytes IS NOT NULL)",
            name="ready_needs_hash_and_size",
        ),
    )
