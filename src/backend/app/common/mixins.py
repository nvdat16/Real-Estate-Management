"""Cột dùng chung cho các bảng nghiệp vụ.

Phạm vi áp dụng theo ERD mục 5.3:

- `TimestampMixin`: bảng nghiệp vụ có created_at/updated_at.
- `CreatedAtMixin`: bảng chỉ ghi thêm (append-only) chỉ có created_at.
- `SoftDeleteMixin` + `RowVersionMixin`: users, customers, agents, projects,
  properties, listings, contracts; invoices và commissions chỉ lấy row_version.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import ForeignKey, func, text
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, declarative_mixin, declared_attr, mapped_column


def uuid_pk() -> Any:
    """Khóa chính UUID, sinh được ở cả ORM và ở database."""
    return mapped_column(
        PgUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )


def uuid_fk(
    target: str,
    *,
    nullable: bool = False,
    index: bool = False,
    unique: bool = False,
) -> Any:
    """FK UUID; mặc định RESTRICT theo ERD mục 1 (không cascade xóa nghiệp vụ)."""
    return mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey(target, ondelete="RESTRICT"),
        nullable=nullable,
        index=index,
        unique=unique,
    )


@declarative_mixin
class CreatedAtMixin:
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)


@declarative_mixin
class TimestampMixin(CreatedAtMixin):
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


@declarative_mixin
class RowVersionMixin:
    row_version: Mapped[int] = mapped_column(server_default=text("1"), default=1, nullable=False)


@declarative_mixin
class SoftDeleteMixin:
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True)

    @declared_attr
    def deleted_by(cls) -> Mapped[uuid.UUID | None]:
        return mapped_column(
            PgUUID(as_uuid=True),
            ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=True,
        )
