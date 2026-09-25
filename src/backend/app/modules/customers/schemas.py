from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class CustomerView(BaseModel):
    id: uuid.UUID
    customer_code: str
    full_name: str
    email: str
    phone: str | None
    address: str | None
    row_version: int


class CustomerUpdateRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=150)
    phone: str | None = Field(default=None, max_length=32)
    address: str | None = Field(default=None, max_length=500)
    row_version: int
