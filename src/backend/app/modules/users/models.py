"""Bảng `users` — chủ sở hữu: module users (ARCHITECTURE mục 5.5)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.common.enums import UserStatus, sql_in
from app.common.mixins import RowVersionMixin, SoftDeleteMixin, TimestampMixin, uuid_pk
from app.core.database import Base


class User(Base, TimestampMixin, SoftDeleteMixin, RowVersionMixin):
    """Tài khoản đăng nhập.

    `auth_version` tăng khi đăng xuất, reset mật khẩu, khóa tài khoản hoặc đổi
    quyền; API so sánh với claim trong JWT để thu hồi phiên cũ (SPEC SP-01).
    Email giữ UNIQUE toàn cục kể cả bản ghi đã xóa mềm, để không tái sử dụng
    danh tính lịch sử (ERD mục 5.1).
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = uuid_pk()
    email: Mapped[str] = mapped_column(String(254), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        server_default=text(f"'{UserStatus.ACTIVE}'"),
    )
    auth_version: Mapped[int] = mapped_column(nullable=False, server_default=text("1"), default=1)
    locked_at: Mapped[datetime | None] = mapped_column(nullable=True)

    __table_args__ = (
        CheckConstraint(sql_in("status", UserStatus), name="status_valid"),
        CheckConstraint("email = lower(email)", name="email_normalized"),
        CheckConstraint("auth_version >= 1", name="auth_version_positive"),
    )
