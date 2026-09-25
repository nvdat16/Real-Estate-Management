"""Bảng `agents` — chủ sở hữu: module agents.

`status = inactive` chặn nhận giao dịch mới nhưng giữ toàn bộ lịch sử cũ
(ERD mục 4).
"""

from __future__ import annotations

import uuid

from sqlalchemy import CheckConstraint, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.common.enums import AgentStatus, sql_in
from app.common.mixins import RowVersionMixin, SoftDeleteMixin, TimestampMixin, uuid_fk, uuid_pk
from app.core.database import Base


class Agent(Base, TimestampMixin, SoftDeleteMixin, RowVersionMixin):
    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = uuid_fk("users.id", unique=True)
    agent_code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        server_default=text(f"'{AgentStatus.ACTIVE}'"),
    )

    __table_args__ = (CheckConstraint(sql_in("status", AgentStatus), name="status_valid"),)
