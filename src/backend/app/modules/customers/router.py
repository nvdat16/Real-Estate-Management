"""HTTP↔schema mapping cho hồ sơ khách hàng.

`GET /customers` không gắn `require_permission`: rẽ nhánh admin/agent-scope/403
nằm trong `service.list_` để agent xem được "khách của tôi" mà không cần một
permission dành riêng cho self-access (PLAN Phase 2, quyết định đã chốt với
người dùng)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.schemas.pagination import Page
from app.common.utils.pagination import PageParams, page_params
from app.core.database import get_db
from app.dependencies import get_current_user
from app.modules.customers import service as customers_service
from app.modules.customers.schemas import CustomerUpdateRequest, CustomerView
from app.modules.users.repository import UserRow


router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("", response_model=Page[CustomerView])
async def list_customers(
    pagination: PageParams = Depends(page_params),
    actor: UserRow = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Page[CustomerView]:
    return await customers_service.list_(db, actor=actor, page_params=pagination)


@router.get("/{customer_id}", response_model=CustomerView)
async def get_customer(
    customer_id: uuid.UUID,
    actor: UserRow = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CustomerView:
    return await customers_service.get(db, actor=actor, customer_id=customer_id)


@router.patch("/{customer_id}", response_model=CustomerView)
async def update_customer(
    customer_id: uuid.UUID,
    payload: CustomerUpdateRequest,
    actor: UserRow = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CustomerView:
    return await customers_service.update(
        db,
        actor=actor,
        customer_id=customer_id,
        full_name=payload.full_name,
        phone=payload.phone,
        address=payload.address,
        expected_row_version=payload.row_version,
    )
