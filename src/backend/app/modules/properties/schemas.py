from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PropertyCreateRequest(BaseModel):
    """Không nhận `status`: căn mới luôn `available`, các trạng thái khác chỉ do
    luồng hợp đồng đặt (SPEC SP-02)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    project_id: uuid.UUID
    unit_code: str = Field(min_length=1, max_length=50)
    area_m2: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    bedrooms: int = Field(ge=0, le=100)
    floor: int | None = Field(default=None, ge=-10, le=300)
    description: str | None = Field(default=None, max_length=10_000)


class PropertyUpdateRequest(BaseModel):
    """PATCH từng phần. `project_id`, `unit_code` và `status` không có ở đây: dự
    án/mã căn không đổi sau khi tạo, trạng thái chỉ đổi qua hợp đồng."""

    model_config = ConfigDict(str_strip_whitespace=True)

    area_m2: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    bedrooms: int | None = Field(default=None, ge=0, le=100)
    floor: int | None = Field(default=None, ge=-10, le=300)
    description: str | None = Field(default=None, max_length=10_000)
    row_version: int


class PropertyView(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    unit_code: str
    area_m2: Decimal
    bedrooms: int
    floor: int | None
    description: str | None
    status: str
    row_version: int
    created_at: datetime
    updated_at: datetime


PropertySort = Literal[
    "unit_code", "-unit_code", "area_m2", "-area_m2", "created_at", "-created_at"
]
