from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class AuditLogView(BaseModel):
    id: uuid.UUID
    actor_user_id: uuid.UUID | None
    actor_type: str
    action: str
    entity_type: str
    entity_id: uuid.UUID
    change_summary: dict | None
    request_id: str | None
    created_at: datetime
