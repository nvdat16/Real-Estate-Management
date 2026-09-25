"""Hợp đồng và chuỗi ký — chủ sở hữu: module contracts.

Bảng: `contracts`, `contract_versions`, `contract_parties`, `signing_challenges`,
`contract_signatures`. Các ràng buộc ở đây là lớp chặn cuối cùng cho những
invariant mà service không được phép làm sai (ERD mục 5.1, 5.2):

- một căn chỉ có một hợp đồng đang giữ (`pending_signatures`) hoặc đã ký;
- phiên bản hợp đồng và loại giao dịch luôn khớp hợp đồng cha (FK ghép);
- một bên ký chỉ có một chữ ký, và challenge dùng để ký phải thuộc đúng bên đó
  (FK ghép sang `signing_challenges(id, party_id)`).
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKeyConstraint,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.common.enums import (
    ContractStatus,
    ListingType,
    PartyRole,
    SignatureMethod,
    sql_in,
)
from app.common.mixins import (
    CreatedAtMixin,
    RowVersionMixin,
    SoftDeleteMixin,
    TimestampMixin,
    uuid_fk,
    uuid_pk,
)
from app.core.database import Base


class Contract(Base, TimestampMixin, SoftDeleteMixin, RowVersionMixin):
    __tablename__ = "contracts"

    id: Mapped[uuid.UUID] = uuid_pk()
    contract_no: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    listing_id: Mapped[uuid.UUID] = uuid_fk("listings.id")
    property_id: Mapped[uuid.UUID] = uuid_fk("properties.id")
    customer_id: Mapped[uuid.UUID] = uuid_fk("customers.id")
    agent_id: Mapped[uuid.UUID] = uuid_fk("agents.id")
    created_by: Mapped[uuid.UUID] = uuid_fk("users.id")
    contract_type: Mapped[str] = mapped_column(String(8), nullable=False)
    status: Mapped[str] = mapped_column(
        String(24),
        nullable=False,
        server_default=text(f"'{ContractStatus.DRAFT}'"),
    )
    signed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(nullable=True)
    cancelled_by: Mapped[uuid.UUID | None] = uuid_fk("users.id", nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    __table_args__ = (
        CheckConstraint(sql_in("status", ContractStatus), name="status_valid"),
        CheckConstraint(sql_in("contract_type", ListingType), name="type_valid"),
        CheckConstraint(
            "status <> 'signed' OR signed_at IS NOT NULL",
            name="signed_needs_timestamp",
        ),
        CheckConstraint(
            "status <> 'cancelled'"
            " OR (cancelled_at IS NOT NULL AND cancelled_by IS NOT NULL"
            " AND cancellation_reason IS NOT NULL)",
            name="cancelled_needs_reason",
        ),
        # A-07: chỉ một hợp đồng được giữ hoặc đã chốt trên một căn.
        Index(
            "uq_contracts_active_property",
            "property_id",
            unique=True,
            postgresql_where=text(
                "status IN ('pending_signatures', 'signed') AND deleted_at IS NULL"
            ),
        ),
        # UNIQUE phụ trợ: đích cho FK ghép ở contract_versions và commissions.
        UniqueConstraint("id", "agent_id", name="uq_contracts_id_agent_id"),
        UniqueConstraint("id", "contract_type", name="uq_contracts_id_contract_type"),
        Index("ix_contracts_customer_id_created_at_id", "customer_id", "created_at", "id"),
        Index(
            "ix_contracts_agent_id_status_created_at_id", "agent_id", "status", "created_at", "id"
        ),
        Index("ix_contracts_status_created_at", "status", "created_at"),
        Index(
            "ix_contracts_signed_at",
            "signed_at",
            postgresql_where=text("status = 'signed'"),
        ),
    )


class ContractVersion(Base, CreatedAtMixin):
    """Snapshot bất biến của một lần soạn nội dung hợp đồng.

    `contract_type` được sao chép từ hợp đồng cha để snapshot tự đủ và để CHECK
    được quy tắc ngày thuê; FK ghép bảo đảm hai giá trị luôn bằng nhau.
    """

    __tablename__ = "contract_versions"

    id: Mapped[uuid.UUID] = uuid_pk()
    contract_id: Mapped[uuid.UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    contract_type: Mapped[str] = mapped_column(String(8), nullable=False)
    version_no: Mapped[int] = mapped_column(nullable=False)
    content_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    commission_base: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    commission_rate: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, server_default=text("'VND'"))
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    pdf_file_id: Mapped[uuid.UUID | None] = uuid_fk("files.id", nullable=True)
    frozen_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_by: Mapped[uuid.UUID] = uuid_fk("users.id")

    __table_args__ = (
        ForeignKeyConstraint(
            ["contract_id", "contract_type"],
            ["contracts.id", "contracts.contract_type"],
            name="fk_contract_versions_contract_id_contract_type",
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "contract_id", "version_no", name="uq_contract_versions_contract_id_version_no"
        ),
        # UNIQUE phụ trợ: đích cho FK ghép ở commissions.
        UniqueConstraint("contract_id", "id", name="uq_contract_versions_contract_id_id"),
        CheckConstraint("version_no > 0", name="version_positive"),
        CheckConstraint("total_amount > 0", name="total_amount_positive"),
        CheckConstraint("commission_base >= 0", name="commission_base_non_negative"),
        CheckConstraint(
            "commission_rate >= 0 AND commission_rate <= 100",
            name="commission_rate_range",
        ),
        CheckConstraint("currency = 'VND'", name="currency_vnd"),
        # Thuê bắt buộc có khoảng thời gian; bán thì không cần.
        CheckConstraint(
            "contract_type <> 'rent' OR (start_date IS NOT NULL AND end_date IS NOT NULL)",
            name="rent_needs_dates",
        ),
        CheckConstraint(
            "start_date IS NULL OR end_date IS NULL OR end_date > start_date",
            name="end_after_start",
        ),
    )


class ContractParty(Base, CreatedAtMixin):
    """Đúng hai bên cho mỗi phiên bản: khách và đại diện đơn vị (A-02)."""

    __tablename__ = "contract_parties"

    id: Mapped[uuid.UUID] = uuid_pk()
    contract_version_id: Mapped[uuid.UUID] = uuid_fk("contract_versions.id")
    user_id: Mapped[uuid.UUID] = uuid_fk("users.id")
    party_role: Mapped[str] = mapped_column(String(16), nullable=False)
    display_name_snapshot: Mapped[str] = mapped_column(String(150), nullable=False)

    __table_args__ = (
        CheckConstraint(sql_in("party_role", PartyRole), name="party_role_valid"),
        UniqueConstraint(
            "contract_version_id",
            "party_role",
            name="uq_contract_parties_contract_version_id_party_role",
        ),
        UniqueConstraint(
            "contract_version_id",
            "user_id",
            name="uq_contract_parties_contract_version_id_user_id",
        ),
        Index("ix_contract_parties_user_id_contract_version_id", "user_id", "contract_version_id"),
    )


class SigningChallenge(Base, TimestampMixin):
    """Thách thức OTP cho một bên ký.

    Chỉ lưu hash OTP. Gửi lại phải revoke mã cũ, kể cả mã đã hết hạn, nên
    predicate của partial unique index không dùng `now()` (không immutable).
    """

    __tablename__ = "signing_challenges"

    id: Mapped[uuid.UUID] = uuid_pk()
    party_id: Mapped[uuid.UUID] = uuid_fk("contract_parties.id")
    otp_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    attempt_count: Mapped[int] = mapped_column(nullable=False, server_default=text("0"), default=0)
    expires_at: Mapped[datetime] = mapped_column(nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(nullable=True)

    __table_args__ = (
        CheckConstraint(
            "attempt_count >= 0 AND attempt_count <= 5",
            name="attempt_count_range",
        ),
        # UNIQUE phụ trợ: đích cho FK ghép ở contract_signatures.
        UniqueConstraint("id", "party_id", name="uq_signing_challenges_id_party_id"),
        Index(
            "uq_signing_challenges_open_party",
            "party_id",
            unique=True,
            postgresql_where=text("consumed_at IS NULL AND revoked_at IS NULL"),
        ),
    )


class ContractSignature(Base, CreatedAtMixin):
    """Bằng chứng ký, chỉ ghi thêm, không xóa để ký lại."""

    __tablename__ = "contract_signatures"

    id: Mapped[uuid.UUID] = uuid_pk()
    party_id: Mapped[uuid.UUID] = uuid_fk("contract_parties.id", unique=True)
    challenge_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True),
        nullable=False,
        unique=True,
    )
    kyc_verification_id: Mapped[uuid.UUID | None] = uuid_fk("kyc_verifications.id", nullable=True)
    method: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        server_default=text(f"'{SignatureMethod.EMAIL_OTP}'"),
    )
    signed_content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    signed_at: Mapped[datetime] = mapped_column(nullable=False)
    evidence: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        # Challenge phải thuộc đúng bên ký này.
        ForeignKeyConstraint(
            ["challenge_id", "party_id"],
            ["signing_challenges.id", "signing_challenges.party_id"],
            name="fk_contract_signatures_challenge_id_party_id",
            ondelete="RESTRICT",
        ),
        CheckConstraint(sql_in("method", SignatureMethod), name="method_valid"),
    )
