from __future__ import annotations

import uuid

from pydantic import BaseModel, EmailStr, Field

from app.core.security import PASSWORD_MAX_LENGTH, PASSWORD_MIN_LENGTH


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)
    full_name: str = Field(min_length=1, max_length=150)
    phone: str | None = Field(default=None, max_length=32)


class UserPublic(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    phone: str | None
    status: str
    roles: list[str]
    # Client cần giá trị này để gửi lại trong `PATCH /me` (khóa lạc quan).
    row_version: int


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"  # noqa: S105 - loại token OAuth2, không phải secret


class PasswordResetRequestSchema(BaseModel):
    email: EmailStr


class PasswordResetConfirmSchema(BaseModel):
    token: str
    new_password: str = Field(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)


class MeUpdateRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=150)
    phone: str | None = Field(default=None, max_length=32)
    row_version: int


class MessageResponse(BaseModel):
    message: str
