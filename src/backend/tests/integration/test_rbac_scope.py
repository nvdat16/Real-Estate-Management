"""T-02 (SPEC §12): user đổi UUID không đọc/sửa dữ liệu ngoài scope.

Môi giới chỉ thấy khách có hợp đồng cùng mình (404 nếu ngoài scope); khách
thường không có permission nào liên quan bị 403; tự truy cập bản thân luôn
được phép không cần permission.
"""

from __future__ import annotations

import uuid

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import ContractStatus, ListingType
from app.core.constants import PermissionCode
from app.core.security import create_access_token
from app.models import Agent, Contract, User
from tests.integration import factories as f


pytestmark = [pytest.mark.integration]


def _auth_headers(user: User) -> dict[str, str]:
    token = create_access_token(user.id, user.auth_version)
    return {"Authorization": f"Bearer {token}"}


async def _link_agent_to_customer(
    db_session: AsyncSession, *, agent: Agent, customer_id: uuid.UUID, creator: User
) -> Contract:
    listing = await f.make_listing(db_session)
    contract = Contract(
        contract_no=f"HD-{uuid.uuid4().hex[:10]}",
        listing_id=listing.id,
        property_id=listing.property_id,
        customer_id=customer_id,
        agent_id=agent.id,
        created_by=creator.id,
        contract_type=ListingType.SALE.value,
        status=ContractStatus.DRAFT.value,
    )
    db_session.add(contract)
    await db_session.flush()
    return contract


async def test_khach_tu_xem_ho_so_cua_chinh_minh(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    customer_actor = await f.make_actor(db_session, role_code="customer")
    customer = await f.make_customer(db_session)
    # Gắn hồ sơ customer cho đúng user đang gọi API (self-access).
    customer.user_id = customer_actor.id
    await db_session.flush()

    response = await client.get(
        f"/api/v1/customers/{customer.id}", headers=_auth_headers(customer_actor)
    )
    assert response.status_code == 200


async def test_khach_thuong_khong_co_permission_bi_403(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    customer_actor = await f.make_actor(db_session, role_code="customer")
    other_customer = await f.make_customer(db_session)

    detail_response = await client.get(
        f"/api/v1/customers/{other_customer.id}", headers=_auth_headers(customer_actor)
    )
    list_response = await client.get("/api/v1/customers", headers=_auth_headers(customer_actor))

    assert detail_response.status_code == 403
    assert detail_response.json()["error"]["code"] == "PERMISSION_DENIED"
    assert list_response.status_code == 403


async def test_moi_gioi_chi_thay_khach_trong_scope(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    agent_actor = await f.make_actor(
        db_session, role_code="agent", permission_codes=(PermissionCode.CUSTOMER_READ_SCOPE,)
    )
    agent_profile = await f.make_agent(db_session)
    agent_profile.user_id = agent_actor.id
    await db_session.flush()

    in_scope_customer = await f.make_customer(db_session)
    out_of_scope_customer = await f.make_customer(db_session)
    await _link_agent_to_customer(
        db_session, agent=agent_profile, customer_id=in_scope_customer.id, creator=agent_actor
    )

    in_scope_response = await client.get(
        f"/api/v1/customers/{in_scope_customer.id}", headers=_auth_headers(agent_actor)
    )
    out_of_scope_response = await client.get(
        f"/api/v1/customers/{out_of_scope_customer.id}", headers=_auth_headers(agent_actor)
    )
    unknown_id_response = await client.get(
        f"/api/v1/customers/{uuid.uuid4()}", headers=_auth_headers(agent_actor)
    )

    assert in_scope_response.status_code == 200
    assert out_of_scope_response.status_code == 404
    assert unknown_id_response.status_code == 404
    # Ngoài scope và không tồn tại phải trả lỗi giống nhau (không tiết lộ tồn tại).
    assert out_of_scope_response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"

    list_response = await client.get("/api/v1/customers", headers=_auth_headers(agent_actor))
    assert list_response.status_code == 200
    listed_ids = {item["id"] for item in list_response.json()["items"]}
    assert str(in_scope_customer.id) in listed_ids
    assert str(out_of_scope_customer.id) not in listed_ids


async def test_admin_thay_toan_bo_khach(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    admin_actor = await f.make_actor(
        db_session, role_code="admin", permission_codes=(PermissionCode.USER_MANAGE,)
    )
    await f.make_customer(db_session)
    await f.make_customer(db_session)

    response = await client.get("/api/v1/customers", headers=_auth_headers(admin_actor))

    assert response.status_code == 200
    assert response.json()["total"] >= 2


async def test_moi_gioi_khong_xem_duoc_ho_so_moi_gioi_khac(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    agent_actor = await f.make_actor(db_session, role_code="agent")
    other_agent = await f.make_agent(db_session)

    response = await client.get(
        f"/api/v1/agents/{other_agent.id}", headers=_auth_headers(agent_actor)
    )

    assert response.status_code == 403


async def test_khach_khong_goi_duoc_endpoint_admin_only(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    customer_actor = await f.make_actor(db_session, role_code="customer")

    users_response = await client.get("/api/v1/users", headers=_auth_headers(customer_actor))
    agents_response = await client.get("/api/v1/agents", headers=_auth_headers(customer_actor))
    audit_response = await client.get("/api/v1/audit-logs", headers=_auth_headers(customer_actor))

    assert users_response.status_code == 403
    assert agents_response.status_code == 403
    assert audit_response.status_code == 403
