"""Hồ sơ môi giới (PLAN task 2.6): môi giới tự xem/sửa hồ sơ của mình, Admin xem
danh sách; tên và điện thoại lưu ở `users` nên PATCH cập nhật cả hai bảng."""

from __future__ import annotations

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import PermissionCode
from app.core.security import create_access_token
from app.models import User
from tests.integration import factories as f


pytestmark = [pytest.mark.integration]


def _auth(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user.id, user.auth_version)}"}


async def test_moi_gioi_xem_va_sua_ho_so_cua_minh(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    agent_user, agent = await f.make_agent_actor(db_session)

    detail = await client.get(f"/api/v1/agents/{agent.id}", headers=_auth(agent_user))
    assert detail.status_code == 200
    assert detail.json()["email"] == agent_user.email

    updated = await client.patch(
        f"/api/v1/agents/{agent.id}",
        json={"full_name": "Tên Môi Giới Mới", "phone": "0911222333", "row_version": 1},
        headers=_auth(agent_user),
    )
    assert updated.status_code == 200
    assert updated.json()["full_name"] == "Tên Môi Giới Mới"
    assert updated.json()["row_version"] == 2

    me = await client.get("/api/v1/me", headers=_auth(agent_user))
    assert me.json()["full_name"] == "Tên Môi Giới Mới"

    stale = await client.patch(
        f"/api/v1/agents/{agent.id}",
        json={"full_name": "Ghi đè", "row_version": 1},
        headers=_auth(agent_user),
    )
    assert stale.status_code == 409


async def test_admin_xem_danh_sach_moi_gioi(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    admin = await f.make_actor(
        db_session, role_code="admin", permission_codes=(PermissionCode.USER_MANAGE,)
    )
    _, agent = await f.make_agent_actor(db_session)

    response = await client.get("/api/v1/agents", headers=_auth(admin))
    assert response.status_code == 200
    assert [item["id"] for item in response.json()["items"]] == [str(agent.id)]
