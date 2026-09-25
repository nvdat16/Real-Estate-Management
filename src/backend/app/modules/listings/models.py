"""Bảng `listings` — chủ sở hữu: module listings.

Hai ràng buộc quan trọng ở tầng database:

- cặp `(listing_type, price_unit)` chỉ được là `sale/total` hoặc `rent/month`,
  để không trộn giá bán toàn căn với giá thuê tháng (FR-06);
- mỗi căn chỉ có một tin `pending` hoặc `approved` chưa xóa (A-07), thực thi
  bằng partial unique index chứ không chỉ kiểm tra ở service.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Index, Numeric, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.common.enums import ListingStatus, ListingType, PriceUnit, sql_in
from app.common.mixins import RowVersionMixin, SoftDeleteMixin, TimestampMixin, uuid_fk, uuid_pk
from app.core.database import Base


class Listing(Base, TimestampMixin, SoftDeleteMixin, RowVersionMixin):
    __tablename__ = "listings"

    id: Mapped[uuid.UUID] = uuid_pk()
    property_id: Mapped[uuid.UUID] = uuid_fk("properties.id")
    agent_id: Mapped[uuid.UUID] = uuid_fk("agents.id")
    reviewed_by: Mapped[uuid.UUID | None] = uuid_fk("users.id", nullable=True)
    listing_type: Mapped[str] = mapped_column(String(8), nullable=False)
    asking_price: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    price_unit: Mapped[str] = mapped_column(String(8), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, server_default=text("'VND'"))
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        server_default=text(f"'{ListingStatus.DRAFT}'"),
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    __table_args__ = (
        CheckConstraint(sql_in("status", ListingStatus), name="status_valid"),
        CheckConstraint(sql_in("listing_type", ListingType), name="type_valid"),
        CheckConstraint(sql_in("price_unit", PriceUnit), name="price_unit_valid"),
        CheckConstraint("asking_price > 0", name="price_positive"),
        CheckConstraint("currency = 'VND'", name="currency_vnd"),
        CheckConstraint(
            "(listing_type = 'sale' AND price_unit = 'total')"
            " OR (listing_type = 'rent' AND price_unit = 'month')",
            name="type_price_unit_pair",
        ),
        CheckConstraint(
            "status <> 'rejected' OR rejection_reason IS NOT NULL",
            name="rejected_needs_reason",
        ),
        CheckConstraint(
            "status NOT IN ('approved', 'rejected')"
            " OR (reviewed_by IS NOT NULL AND reviewed_at IS NOT NULL)",
            name="reviewed_fields_present",
        ),
        # A-07: một căn chỉ có một tin đang chờ duyệt hoặc đã duyệt.
        Index(
            "uq_listings_active_property",
            "property_id",
            unique=True,
            postgresql_where=text("status IN ('pending', 'approved') AND deleted_at IS NULL"),
        ),
        # FR-06: lọc/sắp xếp theo loại giao dịch và giá trên tập tin đã duyệt.
        Index(
            "ix_listings_public_search",
            "listing_type",
            "asking_price",
            "id",
            postgresql_where=text("status = 'approved' AND deleted_at IS NULL"),
        ),
        Index(
            "ix_listings_agent_id_status_created_at_id", "agent_id", "status", "created_at", "id"
        ),
        Index("ix_listings_status_created_at_id", "status", "created_at", "id"),
    )
