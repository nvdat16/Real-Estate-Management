"""SPEC §3.1: PATCH thiếu `row_version` → 422; `row_version` cũ → 409."""

from __future__ import annotations

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models import User
from tests.integration import factories as f


pytestmark = [pytest.mark.integration]


def _auth_headers(user: User) -> dict[str, str]:
    token = create_access_token(user.id, user.auth_version)
    return {"Authorization": f"Bearer {token}"}


async def test_patch_thanh_cong_tang_row_version(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    customer_actor = await f.make_actor(db_session, role_code="customer")
    customer = await f.make_customer(db_session)
    customer.user_id = customer_actor.id
    await db_session.flush()

    response = await client.patch(
        f"/api/v1/customers/{customer.id}",
        json={"full_name": "Tên Mới", "phone": "0911111111", "row_version": 1},
        headers=_auth_headers(customer_actor),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["full_name"] == "Tên Mới"
    assert body["row_version"] == 2


async def test_patch_thieu_row_version_tra_422(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    customer_actor = await f.make_actor(db_session, role_code="customer")
    customer = await f.make_customer(db_session)
    customer.user_id = customer_actor.id
    await db_session.flush()

    response = await client.patch(
        f"/api/v1/customers/{customer.id}",
        json={"full_name": "Tên Mới"},
        headers=_auth_headers(customer_actor),
    )

    assert response.status_code == 422


async def test_patch_row_version_cu_tra_409(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    customer_actor = await f.make_actor(db_session, role_code="customer")
    customer = await f.make_customer(db_session)
    customer.user_id = customer_actor.id
    await db_session.flush()

    response = await client.patch(
        f"/api/v1/customers/{customer.id}",
        json={"full_name": "Tên Mới", "row_version": 999},
        headers=_auth_headers(customer_actor),
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "VERSION_CONFLICT"
