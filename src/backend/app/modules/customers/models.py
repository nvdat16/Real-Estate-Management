"""Bảng `customers` — chủ sở hữu: module customers.

Tên/email/điện thoại hiện tại lấy từ `users`; hồ sơ này không dùng để dựng lại
hợp đồng đã ký (hợp đồng có snapshot riêng theo ERD mục 4).
"""

from __future__ import annotations

import uuid

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.common.mixins import RowVersionMixin, SoftDeleteMixin, TimestampMixin, uuid_fk, uuid_pk
from app.core.database import Base


class Customer(Base, TimestampMixin, SoftDeleteMixin, RowVersionMixin):
    __tablename__ = "customers"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = uuid_fk("users.id", unique=True)
    customer_code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)

    __table_args__ = ({"comment": "Hồ sơ khách hàng, mỗi tài khoản tối đa một hồ sơ"},)
