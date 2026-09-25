from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.common.enums import ProjectStatus


class ProjectCreateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=200)
    address: str = Field(min_length=1, max_length=500)
    province_code: str = Field(min_length=1, max_length=10)
    ward_code: str = Field(min_length=1, max_length=10)
    description: str | None = Field(default=None, max_length=10_000)
    status: ProjectStatus = ProjectStatus.ACTIVE


class ProjectUpdateRequest(BaseModel):
    """PATCH từng phần: chỉ các trường client gửi lên mới được cập nhật. `code`
    không sửa được vì là khóa nghiệp vụ dùng cho import căn hộ (SPEC SP-06)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=1, max_length=200)
    address: str | None = Field(default=None, min_length=1, max_length=500)
    province_code: str | None = Field(default=None, min_length=1, max_length=10)
    ward_code: str | None = Field(default=None, min_length=1, max_length=10)
    description: str | None = Field(default=None, max_length=10_000)
    status: ProjectStatus | None = None
    row_version: int


class ProjectView(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    address: str
    province_code: str
    ward_code: str
    description: str | None
    status: str
    row_version: int
    created_at: datetime
    updated_at: datetime


ProjectSort = Literal["code", "-code", "name", "-name", "created_at", "-created_at"]


class LocationView(BaseModel):
    province_code: str
    ward_code: str
    province_name: str
    ward_name: str


class CatalogProjectView(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    province_code: str
    ward_code: str


class CatalogView(BaseModel):
    """Danh mục cho bộ lọc tìm kiếm công khai: địa bàn và dự án đang hoạt động."""

    locations: list[LocationView]
    projects: list[CatalogProjectView]
