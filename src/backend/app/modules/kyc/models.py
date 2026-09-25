"""Bảng `kyc_verifications` — chủ sở hữu: module kyc.

Mỗi lần gửi là một bản ghi mới; lịch sử không bị ghi đè. Trạng thái hiện tại của
khách là yêu cầu mới nhất. `verified` bắt buộc có `verified_at`; `verified` đã
quá `expires_at` bị coi là không đủ điều kiện ký mà không cần thêm enum
(SPEC SP-03).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, Index, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.common.enums import KycStatus, sql_in
from app.common.mixins import TimestampMixin, uuid_fk, uuid_pk
from app.core.database import Base


class KycVerification(Base, TimestampMixin):
    __tablename__ = "kyc_verifications"

    id: Mapped[uuid.UUID] = uuid_pk()
    customer_id: Mapped[uuid.UUID] = uuid_fk("customers.id")
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    provider_request_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        server_default=text(f"'{KycStatus.PENDING}'"),
    )
    evidence_file_id: Mapped[uuid.UUID | None] = uuid_fk("files.id", nullable=True)
    reviewed_by: Mapped[uuid.UUID | None] = uuid_fk("users.id", nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(nullable=True)
    reason: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    __table_args__ = (
        CheckConstraint(sql_in("status", KycStatus), name="status_valid"),
        CheckConstraint(
            "status <> 'verified' OR verified_at IS NOT NULL",
            name="verified_needs_timestamp",
        ),
        # NULL không xung đột trong UNIQUE của PostgreSQL nên yêu cầu chưa gửi
        # sang nhà cung cấp vẫn tạo được.
        UniqueConstraint(
            "provider",
            "provider_request_id",
            name="uq_kyc_verifications_provider_provider_request_id",
        ),
        # Mỗi khách tối đa một yêu cầu đang chờ.
        Index(
            "uq_kyc_verifications_pending_customer",
            "customer_id",
            unique=True,
            postgresql_where=text("status = 'pending'"),
        ),
        Index("ix_kyc_verifications_customer_id_created_at", "customer_id", "created_at"),
    )
