"""Bảng `projects` — chủ sở hữu: module projects.

Địa bàn lưu theo mã để lọc (ERD mục 4); chỉ mục `(province_code, ward_code)` phục
vụ tìm kiếm theo vị trí của FR-06.
"""

from __future__ import annotations

import uuid

from sqlalchemy import CheckConstraint, Index, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.common.enums import ProjectStatus, sql_in
from app.common.mixins import RowVersionMixin, SoftDeleteMixin, TimestampMixin, uuid_pk
from app.core.database import Base


class Project(Base, TimestampMixin, SoftDeleteMixin, RowVersionMixin):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = uuid_pk()
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    province_code: Mapped[str] = mapped_column(String(10), nullable=False)
    ward_code: Mapped[str] = mapped_column(String(10), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        server_default=text(f"'{ProjectStatus.ACTIVE}'"),
    )

    __table_args__ = (
        CheckConstraint(sql_in("status", ProjectStatus), name="status_valid"),
        Index("ix_projects_province_code_ward_code", "province_code", "ward_code"),
    )
