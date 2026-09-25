"""Tác vụ nền và thông báo — chủ sở hữu: module notifications.

Bảng: `jobs`, `outbox_events`, `email_deliveries`. PostgreSQL là nguồn trạng thái
bền vững; Redis/Celery chỉ là phương tiện vận chuyển. `idempotency_key` và
`event_key` là lớp chặn để job lặp không tạo side effect lần hai (SPEC SP-07).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, Index, String, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.common.enums import (
    EmailDeliveryStatus,
    JobStatus,
    JobType,
    OutboxStatus,
    sql_in,
)
from app.common.mixins import TimestampMixin, uuid_fk, uuid_pk
from app.core.database import Base


class Job(Base, TimestampMixin):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = uuid_pk()
    # Nullable cho tác vụ hệ thống (đối soát, job sinh sau khi ký).
    requested_by: Mapped[uuid.UUID | None] = uuid_fk("users.id", nullable=True)
    job_type: Mapped[str] = mapped_column(String(50), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        server_default=text(f"'{JobStatus.PENDING}'"),
    )
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    input_file_id: Mapped[uuid.UUID | None] = uuid_fk("files.id", nullable=True)
    output_file_id: Mapped[uuid.UUID | None] = uuid_fk("files.id", nullable=True)
    attempts: Mapped[int] = mapped_column(nullable=False, server_default=text("0"), default=0)
    max_attempts: Mapped[int] = mapped_column(nullable=False, server_default=text("3"), default=3)
    error_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(nullable=True)

    __table_args__ = (
        CheckConstraint(sql_in("status", JobStatus), name="status_valid"),
        CheckConstraint(sql_in("job_type", JobType), name="job_type_valid"),
        CheckConstraint("attempts >= 0", name="attempts_non_negative"),
        CheckConstraint("max_attempts > 0", name="max_attempts_positive"),
        Index("ix_jobs_status_created_at", "status", "created_at"),
        Index("ix_jobs_requested_by_created_at", "requested_by", "created_at"),
    )


class OutboxEvent(Base, TimestampMixin):
    """Sự kiện được commit cùng thay đổi nghiệp vụ, dispatcher lấy theo lease."""

    __tablename__ = "outbox_events"

    id: Mapped[uuid.UUID] = uuid_pk()
    job_id: Mapped[uuid.UUID] = uuid_fk("jobs.id")
    event_key: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        server_default=text(f"'{OutboxStatus.PENDING}'"),
    )
    available_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    locked_until: Mapped[datetime | None] = mapped_column(nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(nullable=True)
    attempts: Mapped[int] = mapped_column(nullable=False, server_default=text("0"), default=0)

    __table_args__ = (
        CheckConstraint(sql_in("status", OutboxStatus), name="status_valid"),
        CheckConstraint("attempts >= 0", name="attempts_non_negative"),
        CheckConstraint(
            "status <> 'published' OR published_at IS NOT NULL",
            name="published_needs_timestamp",
        ),
        Index("ix_outbox_events_status_available_at", "status", "available_at"),
    )


class EmailDelivery(Base, TimestampMixin):
    """Một job gửi cho đúng một người nhận; gửi hai bên tạo hai job."""

    __tablename__ = "email_deliveries"

    id: Mapped[uuid.UUID] = uuid_pk()
    job_id: Mapped[uuid.UUID] = uuid_fk("jobs.id", unique=True)
    recipient_user_id: Mapped[uuid.UUID | None] = uuid_fk("users.id", nullable=True)
    recipient_email: Mapped[str] = mapped_column(String(254), nullable=False)
    template_code: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        server_default=text(f"'{EmailDeliveryStatus.PENDING}'"),
    )
    provider_message_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(nullable=True)

    __table_args__ = (
        CheckConstraint(sql_in("status", EmailDeliveryStatus), name="status_valid"),
        CheckConstraint(
            "status <> 'sent' OR sent_at IS NOT NULL",
            name="sent_needs_timestamp",
        ),
    )
