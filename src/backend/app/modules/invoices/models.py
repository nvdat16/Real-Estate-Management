"""Bảng `invoices` — chủ sở hữu: module invoices.

Chứng từ nội bộ gắn hợp đồng đã ký (A-08). Nội dung đóng băng khi phát hành;
sai sót xử lý bằng `void` kèm lý do rồi lập chứng từ mới. MVP không có thanh
toán từng phần nên `paid` là thanh toán toàn bộ (SPEC SP-05).
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, Index, Numeric, String, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.common.enums import InvoiceStatus, sql_in
from app.common.mixins import RowVersionMixin, TimestampMixin, uuid_fk, uuid_pk
from app.core.database import Base


class Invoice(Base, TimestampMixin, RowVersionMixin):
    __tablename__ = "invoices"

    id: Mapped[uuid.UUID] = uuid_pk()
    invoice_no: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    contract_id: Mapped[uuid.UUID] = uuid_fk("contracts.id")
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, server_default=text("'VND'"))
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        server_default=text(f"'{InvoiceStatus.DRAFT}'"),
    )
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    content_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    pdf_file_id: Mapped[uuid.UUID | None] = uuid_fk("files.id", nullable=True)
    created_by: Mapped[uuid.UUID] = uuid_fk("users.id")
    issued_at: Mapped[datetime | None] = mapped_column(nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(nullable=True)
    paid_by: Mapped[uuid.UUID | None] = uuid_fk("users.id", nullable=True)
    payment_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    voided_at: Mapped[datetime | None] = mapped_column(nullable=True)
    voided_by: Mapped[uuid.UUID | None] = uuid_fk("users.id", nullable=True)
    void_reason: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    __table_args__ = (
        CheckConstraint(sql_in("status", InvoiceStatus), name="status_valid"),
        CheckConstraint("amount > 0", name="amount_positive"),
        CheckConstraint("currency = 'VND'", name="currency_vnd"),
        CheckConstraint(
            "status <> 'issued' OR issued_at IS NOT NULL",
            name="issued_needs_timestamp",
        ),
        CheckConstraint(
            "status <> 'paid'"
            " OR (paid_at IS NOT NULL AND paid_by IS NOT NULL"
            " AND payment_reference IS NOT NULL)",
            name="paid_needs_payment_info",
        ),
        CheckConstraint(
            "status <> 'void'"
            " OR (voided_at IS NOT NULL AND voided_by IS NOT NULL AND void_reason IS NOT NULL)",
            name="void_needs_reason",
        ),
        Index("ix_invoices_contract_id_status", "contract_id", "status"),
    )
