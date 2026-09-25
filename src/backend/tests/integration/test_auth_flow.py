"""T-01 (SPEC §12): đăng ký không nâng role; reset một lần; JWT cũ bị thu hồi."""

from __future__ import annotations

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth import service as auth_service
from app.modules.users import repository as users_repository


pytestmark = [pytest.mark.integration]


async def test_dang_ky_bo_qua_role_client_gui(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "  New.Customer@Example.com ",
            "password": "MatKhauManh12345",
            "full_name": "Người Dùng Mới",
            "phone": "0900000099",
            "role": "admin",
            "status": "locked",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "new.customer@example.com"
    assert body["roles"] == ["customer"]
    assert body["status"] == "active"


async def test_dang_ky_trung_email_tra_409(client: httpx.AsyncClient) -> None:
    payload = {
        "email": "dup@example.com",
        "password": "MatKhauManh12345",
        "full_name": "Người Một",
    }
    first = await client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 201

    second = await client.post("/api/v1/auth/register", json=payload)
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "DUPLICATE_RESOURCE"


async def test_luong_dang_nhap_reset_thu_hoi_jwt_cu(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    email = "flow@example.com"
    old_password = "MatKhauCu123456"
    new_password = "MatKhauMoi654321"

    register_response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": old_password, "full_name": "Người Luồng"},
    )
    assert register_response.status_code == 201

    login_response = await client.post(
        "/api/v1/auth/token", data={"username": email, "password": old_password}
    )
    assert login_response.status_code == 200
    old_token = login_response.json()["access_token"]

    me_response = await client.get("/api/v1/me", headers={"Authorization": f"Bearer {old_token}"})
    assert me_response.status_code == 200
    assert me_response.json()["email"] == email

    # Reset trả cùng message bất kể email tồn tại hay không.
    accepted_message = (
        await client.post("/api/v1/auth/password-reset/request", json={"email": email})
    ).json()["message"]
    unknown_message = (
        await client.post(
            "/api/v1/auth/password-reset/request", json={"email": "khong-ton-tai@example.com"}
        )
    ).json()["message"]
    assert accepted_message == unknown_message

    # API không bao giờ trả token thô — test lấy token qua hàm nội bộ mà chính
    # endpoint /request dùng, mô phỏng bước "worker gửi email" (chưa có worker).
    user = await users_repository.get_by_email(db_session, email)
    assert user is not None
    raw_token = await auth_service.issue_password_reset_token(db_session, user)

    confirm_response = await client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": raw_token, "new_password": new_password},
    )
    assert confirm_response.status_code == 200

    # Token reset đã dùng không thể dùng lại.
    replay_response = await client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": raw_token, "new_password": "MatKhauKhac000000"},
    )
    assert replay_response.status_code == 422
    assert replay_response.json()["error"]["code"] == "RESET_TOKEN_INVALID"

    # JWT phát trước khi reset phải bị thu hồi (auth_version đã tăng).
    old_token_response = await client.get(
        "/api/v1/me", headers={"Authorization": f"Bearer {old_token}"}
    )
    assert old_token_response.status_code == 401

    # Mật khẩu cũ không còn đăng nhập được; mật khẩu mới thì được.
    old_login = await client.post(
        "/api/v1/auth/token", data={"username": email, "password": old_password}
    )
    assert old_login.status_code == 401

    new_login = await client.post(
        "/api/v1/auth/token", data={"username": email, "password": new_password}
    )
    assert new_login.status_code == 200
    new_token = new_login.json()["access_token"]

    new_me = await client.get("/api/v1/me", headers={"Authorization": f"Bearer {new_token}"})
    assert new_me.status_code == 200


async def test_dang_xuat_thu_hoi_token_hien_tai(client: httpx.AsyncClient) -> None:
    email = "logout@example.com"
    password = "MatKhauManh12345"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Người Đăng Xuất"},
    )
    login_response = await client.post(
        "/api/v1/auth/token", data={"username": email, "password": password}
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    logout_response = await client.post("/api/v1/auth/logout", headers=headers)
    assert logout_response.status_code == 204

    after_logout = await client.get("/api/v1/me", headers=headers)
    assert after_logout.status_code == 401


async def test_sai_mat_khau_va_email_khong_ton_tai_tra_cung_loi(
    client: httpx.AsyncClient,
) -> None:
    email = "wrongpass@example.com"
    password = "MatKhauManh12345"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Người Kiểm Thử"},
    )

    wrong_password = await client.post(
        "/api/v1/auth/token", data={"username": email, "password": "SaiMatKhau000000"}
    )
    unknown_email = await client.post(
        "/api/v1/auth/token",
        data={"username": "khong-ai@example.com", "password": "SaiMatKhau000000"},
    )

    assert wrong_password.status_code == 401
    assert unknown_email.status_code == 401
    assert wrong_password.json()["error"]["code"] == unknown_email.json()["error"]["code"]
