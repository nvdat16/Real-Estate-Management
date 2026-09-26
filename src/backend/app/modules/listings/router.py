"""HTTP↔schema mapping cho tin đăng.

`router` là API nội bộ (Admin/môi giới phụ trách, quyền và scope kiểm ở
service). `public_router` phục vụ khách chưa đăng nhập với projection công khai.
Các lệnh đổi trạng thái là endpoint riêng, không nhận trạng thái đích từ client.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import ListingStatus, ListingType
from app.common.schemas.pagination import Page
from app.common.utils.pagination import PageParams, page_params
from app.core.database import get_db
from app.dependencies import get_current_user
from app.modules.listings import service as listings_service
from app.modules.listings.repository import ListingFilters
from app.modules.listings.schemas import (
    ListingCommandRequest,
    ListingCreateRequest,
    ListingRejectRequest,
    ListingSort,
    ListingUpdateRequest,
    ListingView,
    PublicListingSort,
    PublicListingView,
)
from app.modules.users.repository import UserRow


router = APIRouter(prefix="/listings", tags=["listings"])
public_router = APIRouter(prefix="/public/listings", tags=["public"])


@router.get("", response_model=Page[ListingView])
async def list_listings(
    status: ListingStatus | None = Query(default=None),
    listing_type: ListingType | None = Query(default=None),
    property_id: uuid.UUID | None = Query(default=None),
    project_id: uuid.UUID | None = Query(default=None),
    agent_id: uuid.UUID | None = Query(default=None),
    q: str | None = Query(default=None, max_length=200),
    sort: ListingSort = Query(default="-created_at"),
    pagination: PageParams = Depends(page_params),
    user: UserRow = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Page[ListingView]:
    filters = ListingFilters(
        status=status,
        listing_type=listing_type,
        property_id=property_id,
        project_id=project_id,
        agent_id=agent_id,
        q=q,
    )
    return await listings_service.list_(
        db, user=user, page_params=pagination, sort=sort, filters=filters
    )


@router.post("", response_model=ListingView, status_code=201)
async def create_listing(
    payload: ListingCreateRequest,
    user: UserRow = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ListingView:
    return await listings_service.create(db, user=user, payload=payload)


@router.get("/{listing_id}", response_model=ListingView)
async def get_listing(
    listing_id: uuid.UUID,
    user: UserRow = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ListingView:
    return await listings_service.get(db, user=user, listing_id=listing_id)


@router.patch("/{listing_id}", response_model=ListingView)
async def update_listing(
    listing_id: uuid.UUID,
    payload: ListingUpdateRequest,
    user: UserRow = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ListingView:
    return await listings_service.update(db, user=user, listing_id=listing_id, payload=payload)


@router.delete("/{listing_id}", status_code=204)
async def delete_listing(
    listing_id: uuid.UUID,
    row_version: int = Query(),
    user: UserRow = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await listings_service.delete(
        db, user=user, listing_id=listing_id, expected_row_version=row_version
    )


@router.post("/{listing_id}/submit", response_model=ListingView)
async def submit_listing(
    listing_id: uuid.UUID,
    payload: ListingCommandRequest,
    user: UserRow = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ListingView:
    return await listings_service.submit(
        db, user=user, listing_id=listing_id, expected_row_version=payload.row_version
    )


@router.post("/{listing_id}/withdraw", response_model=ListingView)
async def withdraw_listing(
    listing_id: uuid.UUID,
    payload: ListingCommandRequest,
    user: UserRow = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ListingView:
    return await listings_service.withdraw(
        db, user=user, listing_id=listing_id, expected_row_version=payload.row_version
    )


@router.post("/{listing_id}/approve", response_model=ListingView)
async def approve_listing(
    listing_id: uuid.UUID,
    payload: ListingCommandRequest,
    user: UserRow = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ListingView:
    return await listings_service.approve(
        db, user=user, listing_id=listing_id, expected_row_version=payload.row_version
    )


@router.post("/{listing_id}/reject", response_model=ListingView)
async def reject_listing(
    listing_id: uuid.UUID,
    payload: ListingRejectRequest,
    user: UserRow = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ListingView:
    return await listings_service.reject(
        db,
        user=user,
        listing_id=listing_id,
        expected_row_version=payload.row_version,
        reason=payload.reason,
    )


@router.post("/{listing_id}/close", response_model=ListingView)
async def close_listing(
    listing_id: uuid.UUID,
    payload: ListingCommandRequest,
    user: UserRow = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ListingView:
    return await listings_service.close(
        db, user=user, listing_id=listing_id, expected_row_version=payload.row_version
    )


@public_router.get("", response_model=Page[PublicListingView])
async def list_public_listings(
    listing_type: ListingType | None = Query(default=None),
    min_price: Decimal | None = Query(default=None, ge=0, max_digits=18, decimal_places=2),
    max_price: Decimal | None = Query(default=None, ge=0, max_digits=18, decimal_places=2),
    province_code: str | None = Query(default=None, max_length=10),
    ward_code: str | None = Query(default=None, max_length=10),
    project_id: uuid.UUID | None = Query(default=None),
    min_bedrooms: int | None = Query(default=None, ge=0, le=100),
    q: str | None = Query(default=None, max_length=200),
    sort: PublicListingSort = Query(default="-published_at"),
    pagination: PageParams = Depends(page_params),
    db: AsyncSession = Depends(get_db),
) -> Page[PublicListingView]:
    return await listings_service.public_list(
        db,
        page_params=pagination,
        sort=sort,
        listing_type=listing_type,
        min_price=min_price,
        max_price=max_price,
        province_code=province_code,
        ward_code=ward_code,
        project_id=project_id,
        min_bedrooms=min_bedrooms,
        q=q,
    )


@public_router.get("/{listing_id}", response_model=PublicListingView)
async def get_public_listing(
    listing_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> PublicListingView:
    return await listings_service.public_get(db, listing_id=listing_id)
