"""PLAN task 2.5: Admin tạo tài khoản môi giới, gán role, khóa/mở khóa."""

from __future__ import annotations

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import PermissionCode
from app.core.security import create_access_token
from app.models import User
from tests.integration import factories as f


pytestmark = [pytest.mark.integration]


def _auth_headers(user: User) -> dict[str, str]:
    token = create_access_token(user.id, user.auth_version)
    return {"Authorization": f"Bearer {token}"}


async def _make_admin(db_session: AsyncSession) -> User:
    return await f.make_actor(
        db_session, role_code="admin", permission_codes=(PermissionCode.USER_MANAGE,)
    )


async def test_admin_tao_tai_khoan_moi_gioi_kem_ho_so(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    admin = await _make_admin(db_session)

    response = await client.post(
        "/api/v1/users",
        json={
            "email": "new.agent@example.com",
            "password": "MatKhauManh12345",
            "full_name": "Môi Giới Mới",
            "phone": "0900000001",
        },
        headers=_auth_headers(admin),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["roles"] == ["agent"]


async def test_gan_role_customer_khi_chua_co_ho_so_bi_409(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    admin = await _make_admin(db_session)
    target = await f.make_user(db_session)

    response = await client.put(
        f"/api/v1/users/{target.id}/roles",
        json={"role_codes": ["customer"], "row_version": 1},
        headers=_auth_headers(admin),
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "INVALID_STATE"


async def test_gan_role_khong_ton_tai_bi_422(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    admin = await _make_admin(db_session)
    target = await f.make_user(db_session)

    response = await client.put(
        f"/api/v1/users/{target.id}/roles",
        json={"role_codes": ["khong-ton-tai"], "row_version": 1},
        headers=_auth_headers(admin),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


async def test_khoa_tai_khoan_thu_hoi_token_hien_tai(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    admin = await _make_admin(db_session)
    target = await f.make_actor(db_session, role_code="customer")
    target_headers = _auth_headers(target)

    lock_response = await client.post(
        f"/api/v1/users/{target.id}/lock",
        json={"row_version": 1},
        headers=_auth_headers(admin),
    )
    assert lock_response.status_code == 200
    assert lock_response.json()["status"] == "locked"

    me_response = await client.get("/api/v1/me", headers=target_headers)
    assert me_response.status_code == 401

    unlock_response = await client.post(
        f"/api/v1/users/{target.id}/unlock",
        json={"row_version": lock_response.json()["row_version"]},
        headers=_auth_headers(admin),
    )
    assert unlock_response.status_code == 200
    assert unlock_response.json()["status"] == "active"


async def test_khoa_voi_row_version_cu_tra_409(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    admin = await _make_admin(db_session)
    target = await f.make_user(db_session)

    response = await client.post(
        f"/api/v1/users/{target.id}/lock",
        json={"row_version": 999},
        headers=_auth_headers(admin),
    )

    assert response.status_code == 409
