from __future__ import annotations

import uuid

from pydantic import BaseModel, EmailStr, Field

from app.core.security import PASSWORD_MAX_LENGTH, PASSWORD_MIN_LENGTH


class CreateAgentRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)
    full_name: str = Field(min_length=1, max_length=150)
    phone: str | None = Field(default=None, max_length=32)


class UserAdminView(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    phone: str | None
    status: str
    auth_version: int
    row_version: int
    roles: list[str]


class ReplaceRolesRequest(BaseModel):
    role_codes: list[str]
    row_version: int


class LockRequest(BaseModel):
    row_version: int


class UnlockRequest(BaseModel):
    row_version: int
