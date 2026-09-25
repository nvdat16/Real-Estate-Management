"""Use case cho hồ sơ khách hàng (PLAN task 2.6, cộng slice `has_profile`/
`create_customer_profile` mà `auth.register` và `users.replace_roles` cần)."""

from __future__ import annotations

import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.schemas.pagination import Page
from app.common.utils import expect
from app.common.utils.codes import generate_code
from app.common.utils.pagination import PageParams
from app.core.constants import PermissionCode
from app.core.exceptions import permission_denied, version_conflict
from app.core.permissions import user_has_permission
from app.modules.agents import repository as agents_repository
from app.modules.customers import repository as customers_repository
from app.modules.customers.models import Customer
from app.modules.customers.permissions import ensure_customer_scope
from app.modules.customers.schemas import CustomerView
from app.modules.users import repository as users_repository
from app.modules.users.models import User


async def has_profile(db: AsyncSession, user_id: uuid.UUID) -> bool:
    return await customers_repository.get_by_user_id(db, user_id) is not None


async def create_customer_profile(db: AsyncSession, user_id: uuid.UUID) -> Customer:
    for _ in range(5):
        try:
            async with db.begin_nested():
                customer = Customer(user_id=user_id, customer_code=generate_code("KH"))
                db.add(customer)
                await db.flush()
        except IntegrityError:
            continue
        return customer
    raise RuntimeError("Không sinh được customer_code duy nhất sau nhiều lần thử")


def _to_view(customer: Customer, user: User) -> CustomerView:
    return CustomerView(
        id=customer.id,
        customer_code=customer.customer_code,
        full_name=user.full_name,
        email=user.email,
        phone=user.phone,
        address=customer.address,
        row_version=customer.row_version,
    )


async def get(db: AsyncSession, *, actor: User, customer_id: uuid.UUID) -> CustomerView:
    await ensure_customer_scope(db, actor, customer_id)
    pair = expect(await customers_repository.get_with_user(db, customer_id))
    return _to_view(*pair)


async def list_(db: AsyncSession, *, actor: User, page_params: PageParams) -> Page[CustomerView]:
    if await user_has_permission(db, actor.id, PermissionCode.USER_MANAGE):
        pairs, total = await customers_repository.list_page(db, page_params)
    elif await user_has_permission(db, actor.id, PermissionCode.CUSTOMER_READ_SCOPE):
        agent = await agents_repository.get_by_user_id(db, actor.id)
        if agent is None:
            pairs, total = [], 0
        else:
            pairs, total = await customers_repository.list_page(
                db, page_params, scope_agent_id=agent.id
            )
    else:
        raise permission_denied()

    items = [_to_view(customer, user) for customer, user in pairs]
    return Page(items=items, page=page_params.page, page_size=page_params.page_size, total=total)


async def update(
    db: AsyncSession,
    *,
    actor: User,
    customer_id: uuid.UUID,
    full_name: str,
    phone: str | None,
    address: str | None,
    expected_row_version: int,
) -> CustomerView:
    customer = await ensure_customer_scope(db, actor, customer_id)
    ok = await customers_repository.update_fields(
        db, customer_id, expected_row_version, address=address
    )
    if not ok:
        raise version_conflict()
    await users_repository.set_contact_fields(
        db, customer.user_id, full_name=full_name, phone=phone
    )
    await db.commit()

    pair = expect(await customers_repository.get_with_user(db, customer_id))
    return _to_view(*pair)
