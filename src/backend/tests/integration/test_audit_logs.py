"""T-13 (SPEC §12): audit đúng actor, không chứa secret, không có API sửa/xóa."""

from __future__ import annotations

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import PermissionCode
from app.core.security import create_access_token
from app.models import AuditLog, User
from app.modules.audit_logs.router import router as audit_logs_router
from tests.integration import factories as f


pytestmark = [pytest.mark.integration]


def _auth_headers(user: User) -> dict[str, str]:
    token = create_access_token(user.id, user.auth_version)
    return {"Authorization": f"Bearer {token}"}


def test_audit_router_chi_doc() -> None:
    methods = {method for route in audit_logs_router.routes for method in route.methods}
    assert "GET" in methods
    assert methods <= {"GET", "HEAD"}


async def test_dang_ky_ghi_audit_dung_actor_khong_chua_secret(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "audited@example.com",
            "password": "MatKhauManh12345",
            "full_name": "Người Được Ghi Audit",
        },
    )
    assert response.status_code == 201
    user_id = response.json()["id"]

    log = await db_session.scalar(
        select(AuditLog).where(
            AuditLog.entity_type == "users",
            AuditLog.action == "auth.register",
        )
    )
    assert log is not None
    assert str(log.actor_user_id) == user_id
    assert log.actor_type == "user"
    assert log.change_summary is None or "password" not in str(log.change_summary).lower()


async def test_chi_admin_tra_cuu_duoc_audit_log(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    admin_actor = await f.make_actor(
        db_session, role_code="admin", permission_codes=(PermissionCode.AUDIT_READ,)
    )
    non_admin_actor = await f.make_actor(db_session, role_code="customer")
    await f.make_audit_log(db_session, action="user.lock", entity_type="users")

    admin_response = await client.get("/api/v1/audit-logs", headers=_auth_headers(admin_actor))
    non_admin_response = await client.get(
        "/api/v1/audit-logs", headers=_auth_headers(non_admin_actor)
    )

    assert admin_response.status_code == 200
    assert admin_response.json()["total"] >= 1
    assert non_admin_response.status_code == 403
