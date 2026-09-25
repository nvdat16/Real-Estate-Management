"""Ghi audit log (PLAN task 2.7 — phần ghi, xây sớm vì auth/users/customers/
agents cần gọi trước khi phần đọc `GET /audit-logs` hoàn chỉnh).

Chỉ `flush`, không `commit`: hàm này luôn được gọi bên trong transaction
nghiệp vụ của caller, nên lỗi ghi audit (ví dụ vi phạm CHECK
`actor_matches_type`) làm rollback toàn bộ thay đổi — đúng yêu cầu "audit cùng
transaction, mất audit insert làm thất bại transaction" của SPEC SP-07.
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import ActorType
from app.core.logging import redact
from app.middleware.request_id import get_request_id
from app.modules.audit_logs.models import AuditLog
from app.modules.users.models import User


async def record_audit(
    db: AsyncSession,
    *,
    actor: User | None,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID,
    actor_type: ActorType = ActorType.USER,
    change_summary: dict | None = None,
) -> None:
    db.add(
        AuditLog(
            actor_user_id=actor.id if actor is not None else None,
            actor_type=actor_type.value,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            change_summary=redact(change_summary),
            request_id=get_request_id(),
        )
    )
    await db.flush()
