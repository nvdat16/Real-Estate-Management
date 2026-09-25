"""Bảng `properties` — chủ sở hữu: module properties.

`status` chỉ đổi như hệ quả của luồng hợp đồng (available → reserved →
sold/rented, hoặc về available khi hủy). Module này không cho sửa trạng thái
bằng CRUD (ARCHITECTURE mục 5.5, SPEC SP-02).
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import CheckConstraint, Index, Numeric, String, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.common.enums import PropertyStatus, sql_in
from app.common.mixins import RowVersionMixin, SoftDeleteMixin, TimestampMixin, uuid_fk, uuid_pk
from app.core.database import Base


class Property(Base, TimestampMixin, SoftDeleteMixin, RowVersionMixin):
    __tablename__ = "properties"

    id: Mapped[uuid.UUID] = uuid_pk()
    project_id: Mapped[uuid.UUID] = uuid_fk("projects.id")
    unit_code: Mapped[str] = mapped_column(String(50), nullable=False)
    area_m2: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    bedrooms: Mapped[int] = mapped_column(nullable=False)
    floor: Mapped[int | None] = mapped_column(nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        server_default=text(f"'{PropertyStatus.AVAILABLE}'"),
    )

    __table_args__ = (
        # Mã căn không tái sử dụng sau xóa mềm nên UNIQUE không lọc deleted_at.
        UniqueConstraint("project_id", "unit_code", name="uq_properties_project_id_unit_code"),
        CheckConstraint(sql_in("status", PropertyStatus), name="status_valid"),
        CheckConstraint("area_m2 > 0", name="area_positive"),
        CheckConstraint("bedrooms >= 0", name="bedrooms_non_negative"),
        Index("ix_properties_project_id_status", "project_id", "status"),
    )
