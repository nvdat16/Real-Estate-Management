from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class AgentView(BaseModel):
    id: uuid.UUID
    agent_code: str
    full_name: str
    email: str
    phone: str | None
    status: str
    row_version: int


class AgentUpdateRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=150)
    phone: str | None = Field(default=None, max_length=32)
    row_version: int
