from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

from app.common.enums import ListingType, PriceUnit


def _whole_vnd(value: Decimal) -> Decimal:
    """SPEC mục 3.1: tiền VND có phần lẻ khác 0 bị từ chối."""
    if value != value.to_integral_value():
        raise ValueError("Giá VND không được có phần lẻ")
    return value


AskingPrice = Annotated[
    Decimal, Field(gt=0, max_digits=18, decimal_places=2), AfterValidator(_whole_vnd)
]


class ListingCreateRequest(BaseModel):
    """`price_unit` có thể bỏ trống để server suy ra từ `listing_type`; nếu gửi
    thì phải đúng cặp `sale/total` hoặc `rent/month`. `agent_id` chỉ dành cho
    người duyệt tin (Admin) lập tin thay môi giới; môi giới luôn gắn chính mình."""

    model_config = ConfigDict(str_strip_whitespace=True)

    property_id: uuid.UUID
    listing_type: ListingType
    asking_price: AskingPrice
    price_unit: PriceUnit | None = None
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=10_000)
    agent_id: uuid.UUID | None = None


class ListingUpdateRequest(BaseModel):
    """PATCH từng phần. Không nhận `status`/`property_id`/`agent_id`: trạng thái
    đổi qua lệnh riêng, căn và môi giới cố định sau khi tạo tin."""

    model_config = ConfigDict(str_strip_whitespace=True)

    listing_type: ListingType | None = None
    asking_price: AskingPrice | None = None
    price_unit: PriceUnit | None = None
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, min_length=1, max_length=10_000)
    row_version: int


class ListingCommandRequest(BaseModel):
    row_version: int


class ListingRejectRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    row_version: int
    reason: str = Field(min_length=1, max_length=1000)


class ListingView(BaseModel):
    id: uuid.UUID
    property_id: uuid.UUID
    agent_id: uuid.UUID
    listing_type: str
    asking_price: Decimal
    price_unit: str
    currency: str
    title: str
    description: str
    status: str
    reviewed_by: uuid.UUID | None
    reviewed_at: datetime | None
    rejection_reason: str | None
    row_version: int
    created_at: datetime
    updated_at: datetime


ListingSort = Literal[
    "created_at", "-created_at", "updated_at", "-updated_at", "asking_price", "-asking_price"
]


class PublicPropertyView(BaseModel):
    unit_code: str
    area_m2: Decimal
    bedrooms: int
    floor: int | None


class PublicProjectView(BaseModel):
    id: uuid.UUID
    name: str
    address: str
    province_code: str
    ward_code: str


class PublicListingView(BaseModel):
    """Projection công khai (SPEC SP-02): chỉ nội dung tin, thông số căn và vị trí
    dự án. Không có môi giới, người duyệt, trạng thái nội bộ hay dữ liệu khách."""

    id: uuid.UUID
    title: str
    description: str
    listing_type: str
    asking_price: Decimal
    price_unit: str
    currency: str
    published_at: datetime
    property: PublicPropertyView
    project: PublicProjectView


PublicListingSort = Literal["-published_at", "published_at", "asking_price", "-asking_price"]
