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
from app.modules.customers.permissions import ensure_customer_scope
from app.modules.customers.repository import CustomerProfileRow, CustomerRow
from app.modules.customers.schemas import CustomerView
from app.modules.users import repository as users_repository
from app.modules.users.repository import UserRow


async def has_profile(db: AsyncSession, user_id: uuid.UUID) -> bool:
    return await customers_repository.get_by_user_id(db, user_id) is not None


async def create_customer_profile(db: AsyncSession, user_id: uuid.UUID) -> CustomerRow:
    for _ in range(5):
        try:
            async with db.begin_nested():
                customer = await customers_repository.insert(
                    db, user_id=user_id, customer_code=generate_code("KH")
                )
        except IntegrityError:
            continue
        return customer
    raise RuntimeError("Không sinh được customer_code duy nhất sau nhiều lần thử")


def _to_view(profile: CustomerProfileRow) -> CustomerView:
    return CustomerView.model_validate(profile, from_attributes=True)


async def get(db: AsyncSession, *, actor: UserRow, customer_id: uuid.UUID) -> CustomerView:
    await ensure_customer_scope(db, actor, customer_id)
    return _to_view(expect(await customers_repository.get_profile(db, customer_id)))


async def list_(db: AsyncSession, *, actor: UserRow, page_params: PageParams) -> Page[CustomerView]:
    if await user_has_permission(db, actor.id, PermissionCode.USER_MANAGE):
        profiles, total = await customers_repository.list_page(db, page_params)
    elif await user_has_permission(db, actor.id, PermissionCode.CUSTOMER_READ_SCOPE):
        agent = await agents_repository.get_by_user_id(db, actor.id)
        if agent is None:
            profiles, total = [], 0
        else:
            profiles, total = await customers_repository.list_page(
                db, page_params, scope_agent_id=agent.id
            )
    else:
        raise permission_denied()

    items = [_to_view(profile) for profile in profiles]
    return Page(items=items, page=page_params.page, page_size=page_params.page_size, total=total)


async def update(
    db: AsyncSession,
    *,
    actor: UserRow,
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

    return _to_view(expect(await customers_repository.get_profile(db, customer_id)))
