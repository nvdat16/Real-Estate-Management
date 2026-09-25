"""Bảng `audit_logs` — chủ sở hữu: module audit_logs.

Chỉ ghi thêm, không có API sửa/xóa. `entity_type/entity_id` là tham chiếu đa
hình nên **không phải FK**. `change_summary` đã loại token, OTP, mật khẩu và dữ
liệu định danh thô trước khi ghi (ERD mục 4, SPEC SP-07).
"""

from __future__ import annotations

import uuid

from sqlalchemy import CheckConstraint, Index, String, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.common.enums import ActorType, sql_in
from app.common.mixins import CreatedAtMixin, uuid_fk, uuid_pk
from app.core.database import Base


class AuditLog(Base, CreatedAtMixin):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = uuid_pk()
    actor_user_id: Mapped[uuid.UUID | None] = uuid_fk("users.id", nullable=True)
    actor_type: Mapped[str] = mapped_column(
        String(8),
        nullable=False,
        server_default=text(f"'{ActorType.USER}'"),
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    change_summary: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    __table_args__ = (
        CheckConstraint(sql_in("actor_type", ActorType), name="actor_type_valid"),
        CheckConstraint(
            "(actor_type = 'system' AND actor_user_id IS NULL)"
            " OR (actor_type = 'user' AND actor_user_id IS NOT NULL)",
            name="actor_matches_type",
        ),
        Index(
            "ix_audit_logs_entity_type_entity_id_created_at",
            "entity_type",
            "entity_id",
            "created_at",
        ),
        Index("ix_audit_logs_actor_user_id_created_at", "actor_user_id", "created_at"),
    )
