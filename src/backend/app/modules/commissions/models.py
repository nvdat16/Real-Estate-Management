"""Bảng `commissions` — chủ sở hữu: module commissions.

Một hợp đồng sinh đúng một khoản (UNIQUE contract_id). Số tiền là snapshot từ
phiên bản đã ký và không được sửa sau khi tạo; công thức được kiểm tra ngay ở
database để job lặp hay lỗi service không tạo ra số tiền khác (SPEC SP-05).

Hai FK ghép thay cho FK đơn lẻ: khoản hoa hồng phải trỏ đúng môi giới của hợp
đồng và đúng phiên bản thuộc chính hợp đồng đó (ERD mục 5.1).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    ForeignKeyConstraint,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.common.enums import CommissionStatus, sql_in
from app.common.mixins import RowVersionMixin, TimestampMixin, uuid_fk, uuid_pk
from app.core.database import Base


class Commission(Base, TimestampMixin, RowVersionMixin):
    __tablename__ = "commissions"

    id: Mapped[uuid.UUID] = uuid_pk()
    contract_id: Mapped[uuid.UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    contract_version_id: Mapped[uuid.UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    agent_id: Mapped[uuid.UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    base_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    rate_percent: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, server_default=text("'VND'"))
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        server_default=text(f"'{CommissionStatus.PENDING}'"),
    )
    approved_at: Mapped[datetime | None] = mapped_column(nullable=True)
    approved_by: Mapped[uuid.UUID | None] = uuid_fk("users.id", nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(nullable=True)
    paid_by: Mapped[uuid.UUID | None] = uuid_fk("users.id", nullable=True)
    payment_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(nullable=True)
    cancelled_by: Mapped[uuid.UUID | None] = uuid_fk("users.id", nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ["contract_id", "agent_id"],
            ["contracts.id", "contracts.agent_id"],
            name="fk_commissions_contract_id_agent_id",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["contract_id", "contract_version_id"],
            ["contract_versions.contract_id", "contract_versions.id"],
            name="fk_commissions_contract_id_contract_version_id",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("contract_id", name="uq_commissions_contract_id"),
        CheckConstraint(sql_in("status", CommissionStatus), name="status_valid"),
        CheckConstraint("base_amount >= 0", name="base_amount_non_negative"),
        CheckConstraint("rate_percent >= 0 AND rate_percent <= 100", name="rate_percent_range"),
        CheckConstraint("currency = 'VND'", name="currency_vnd"),
        CheckConstraint(
            "amount = round(base_amount * rate_percent / 100, 0)",
            name="amount_matches_formula",
        ),
        CheckConstraint(
            "status NOT IN ('approved', 'paid')"
            " OR (approved_at IS NOT NULL AND approved_by IS NOT NULL)",
            name="approved_needs_approver",
        ),
        CheckConstraint(
            "status <> 'paid'"
            " OR (paid_at IS NOT NULL AND paid_by IS NOT NULL"
            " AND payment_reference IS NOT NULL)",
            name="paid_needs_payment_info",
        ),
        CheckConstraint(
            "status <> 'cancelled'"
            " OR (cancelled_at IS NOT NULL AND cancelled_by IS NOT NULL"
            " AND cancellation_reason IS NOT NULL)",
            name="cancelled_needs_reason",
        ),
        Index("ix_commissions_agent_id_status_created_at", "agent_id", "status", "created_at"),
    )
