"""Dự án và căn hộ (PLAN task 3.1, 3.2, 3.5; UC-05/UC-06; một phần T-03).

Admin ghi danh mục, môi giới chỉ đọc, khách không truy cập API nội bộ. Xóa bị
chặn khi còn phụ thuộc; căn đang giữ cho hợp đồng chờ ký khóa việc sửa dự án và
căn; `status` của căn không đổi được qua payload CRUD.
"""

from __future__ import annotations

from datetime import UTC, datetime

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import ContractStatus, ListingStatus, PropertyStatus
from app.core.security import create_access_token
from app.models import User
from tests.integration import factories as f


pytestmark = [pytest.mark.integration]

ADMIN_PERMISSIONS = ("project.manage", "property.manage", "listing.manage", "listing.approve")


def _auth(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user.id, user.auth_version)}"}


async def _admin(db_session: AsyncSession) -> User:
    return await f.make_actor(db_session, role_code="admin", permission_codes=ADMIN_PERMISSIONS)


def _project_payload(code: str = "DA-TEST-01") -> dict[str, object]:
    return {
        "code": code,
        "name": "Dự án kiểm thử",
        "address": "Số 1, Ba Đình, Hà Nội",
        "province_code": "01",
        "ward_code": "00004",
    }


async def test_admin_tao_du_an_va_chan_ma_trung(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    admin = await _admin(db_session)

    created = await client.post("/api/v1/projects", json=_project_payload(), headers=_auth(admin))
    assert created.status_code == 201
    assert created.json()["status"] == "active"
    assert created.json()["row_version"] == 1

    duplicate = await client.post("/api/v1/projects", json=_project_payload(), headers=_auth(admin))
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "DUPLICATE_RESOURCE"


async def test_dia_ban_ngoai_danh_muc_bi_422(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    admin = await _admin(db_session)
    payload = {**_project_payload(), "ward_code": "99999"}

    response = await client.post("/api/v1/projects", json=payload, headers=_auth(admin))
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


async def test_moi_gioi_doc_duoc_danh_muc_nhung_khong_ghi(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    agent_user, _ = await f.make_agent_actor(db_session)
    await f.make_project(db_session)

    listed = await client.get("/api/v1/projects", headers=_auth(agent_user))
    assert listed.status_code == 200
    assert listed.json()["total"] == 1

    created = await client.post(
        "/api/v1/projects", json=_project_payload(), headers=_auth(agent_user)
    )
    assert created.status_code == 403


async def test_khach_hang_khong_doc_duoc_danh_muc_noi_bo(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    customer = await f.make_actor(db_session, role_code="customer")

    for path in ("/api/v1/projects", "/api/v1/properties"):
        response = await client.get(path, headers=_auth(customer))
        assert response.status_code == 403, path


async def test_xoa_du_an_bi_chan_khi_con_can(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    admin = await _admin(db_session)
    project = await f.make_project(db_session)
    unit = await f.make_property(db_session, project=project)

    blocked = await client.delete(
        f"/api/v1/projects/{project.id}", params={"row_version": 1}, headers=_auth(admin)
    )
    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] == "DEPENDENCY_EXISTS"

    removed_unit = await client.delete(
        f"/api/v1/properties/{unit.id}", params={"row_version": 1}, headers=_auth(admin)
    )
    assert removed_unit.status_code == 204

    removed = await client.delete(
        f"/api/v1/projects/{project.id}", params={"row_version": 1}, headers=_auth(admin)
    )
    assert removed.status_code == 204
    gone = await client.get(f"/api/v1/projects/{project.id}", headers=_auth(admin))
    assert gone.status_code == 404


async def test_du_an_co_can_reserved_khong_chuyen_inactive(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    admin = await _admin(db_session)
    project = await f.make_project(db_session)
    unit = await f.make_property(db_session, project=project)
    unit.status = PropertyStatus.RESERVED.value
    await db_session.flush()

    response = await client.patch(
        f"/api/v1/projects/{project.id}",
        json={"status": "inactive", "row_version": 1},
        headers=_auth(admin),
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "INVALID_STATE"


async def test_sua_du_an_voi_row_version_cu_tra_409(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    admin = await _admin(db_session)
    project = await f.make_project(db_session)

    first = await client.patch(
        f"/api/v1/projects/{project.id}",
        json={"name": "Tên mới", "row_version": 1},
        headers=_auth(admin),
    )
    assert first.status_code == 200
    assert first.json()["row_version"] == 2

    stale = await client.patch(
        f"/api/v1/projects/{project.id}",
        json={"name": "Ghi đè", "row_version": 1},
        headers=_auth(admin),
    )
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "VERSION_CONFLICT"


async def test_ma_can_duy_nhat_trong_du_an_qua_api(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    admin = await _admin(db_session)
    project = await f.make_project(db_session)
    other_project = await f.make_project(db_session)
    payload = {
        "project_id": str(project.id),
        "unit_code": "A-101",
        "area_m2": "65.5",
        "bedrooms": 2,
    }

    first = await client.post("/api/v1/properties", json=payload, headers=_auth(admin))
    assert first.status_code == 201
    assert first.json()["status"] == "available"

    duplicate = await client.post("/api/v1/properties", json=payload, headers=_auth(admin))
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "DUPLICATE_RESOURCE"

    same_code_elsewhere = await client.post(
        "/api/v1/properties",
        json={**payload, "project_id": str(other_project.id)},
        headers=_auth(admin),
    )
    assert same_code_elsewhere.status_code == 201


async def test_status_can_khong_sua_duoc_qua_payload(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    admin = await _admin(db_session)
    unit = await f.make_property(db_session)

    response = await client.patch(
        f"/api/v1/properties/{unit.id}",
        json={"bedrooms": 3, "status": "sold", "row_version": 1},
        headers=_auth(admin),
    )
    assert response.status_code == 200
    assert response.json()["bedrooms"] == 3
    assert response.json()["status"] == "available"


async def test_can_reserved_khong_sua_duoc(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    admin = await _admin(db_session)
    unit = await f.make_property(db_session)
    unit.status = PropertyStatus.RESERVED.value
    await db_session.flush()

    response = await client.patch(
        f"/api/v1/properties/{unit.id}",
        json={"description": "Đổi mô tả", "row_version": 1},
        headers=_auth(admin),
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "INVALID_STATE"


async def test_xoa_can_bi_chan_khi_con_tin_chua_dong(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    admin = await _admin(db_session)
    listing = await f.make_listing(db_session, status=ListingStatus.DRAFT)

    response = await client.delete(
        f"/api/v1/properties/{listing.property_id}",
        params={"row_version": 1},
        headers=_auth(admin),
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "DEPENDENCY_EXISTS"


async def test_xoa_can_bi_chan_khi_co_hop_dong_da_ky(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    admin = await _admin(db_session)
    listing = await f.make_listing(db_session, status=ListingStatus.CLOSED)
    await f.make_contract(db_session, listing=listing, status=ContractStatus.SIGNED)

    response = await client.delete(
        f"/api/v1/properties/{listing.property_id}",
        params={"row_version": 1},
        headers=_auth(admin),
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "DEPENDENCY_EXISTS"


async def test_danh_muc_cong_khai_cap_nhat_ngay_sau_khi_tao_du_an(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    admin = await _admin(db_session)

    before = await client.get("/api/v1/public/catalog")
    assert before.status_code == 200
    assert before.json()["projects"] == []
    assert len(before.json()["locations"]) > 0

    await client.post("/api/v1/projects", json=_project_payload(), headers=_auth(admin))

    after = await client.get("/api/v1/public/catalog")
    assert [p["code"] for p in after.json()["projects"]] == ["DA-TEST-01"]


async def test_danh_sach_du_an_loc_sap_xep_va_bo_ban_da_xoa(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    admin = await _admin(db_session)
    for code, name in (("DA-B", "Sông Hồng"), ("DA-A", "Hồ Tây"), ("DA-C", "Sông Hàn")):
        project = await f.make_project(db_session)
        project.code, project.name = code, name
    deleted = await f.make_project(db_session)
    deleted.code, deleted.name = "DA-D", "Sông Đà"
    deleted.deleted_at = datetime.now(UTC)
    await db_session.flush()

    by_name = await client.get(
        "/api/v1/projects", params={"q": "sông", "sort": "code"}, headers=_auth(admin)
    )
    assert [p["code"] for p in by_name.json()["items"]] == ["DA-B", "DA-C"]

    first_page = await client.get(
        "/api/v1/projects", params={"sort": "-code", "page_size": 2}, headers=_auth(admin)
    )
    second_page = await client.get(
        "/api/v1/projects",
        params={"sort": "-code", "page_size": 2, "page": 2},
        headers=_auth(admin),
    )
    assert first_page.json()["total"] == 3
    assert [p["code"] for p in first_page.json()["items"]] == ["DA-C", "DA-B"]
    assert [p["code"] for p in second_page.json()["items"]] == ["DA-A"]

    bad_sort = await client.get(
        "/api/v1/projects", params={"sort": "address"}, headers=_auth(admin)
    )
    assert bad_sort.status_code == 422


async def test_danh_sach_can_loc_theo_du_an_va_trang_thai(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    agent_user, _ = await f.make_agent_actor(db_session)
    project = await f.make_project(db_session)
    await f.make_property(db_session, project=project, unit_code="A-02")
    reserved = await f.make_property(db_session, project=project, unit_code="A-01")
    reserved.status = PropertyStatus.RESERVED.value
    await f.make_property(db_session, unit_code="B-01")
    await db_session.flush()

    in_project = await client.get(
        "/api/v1/properties", params={"project_id": str(project.id)}, headers=_auth(agent_user)
    )
    assert [p["unit_code"] for p in in_project.json()["items"]] == ["A-01", "A-02"]

    available = await client.get(
        "/api/v1/properties",
        params={"project_id": str(project.id), "status": "available", "q": "a-0"},
        headers=_auth(agent_user),
    )
    assert [p["unit_code"] for p in available.json()["items"]] == ["A-02"]


async def test_sua_bang_sql_tay_van_cap_nhat_updated_at(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    """Repository SQL tay không có `onupdate` của ORM: `update_versioned` phải tự
    đặt `updated_at = now()` (ADR-011)."""
    admin = await _admin(db_session)
    created = await client.post("/api/v1/projects", json=_project_payload(), headers=_auth(admin))

    updated = await client.patch(
        f"/api/v1/projects/{created.json()['id']}",
        json={"name": "Tên mới", "row_version": 1},
        headers=_auth(admin),
    )
    assert updated.json()["updated_at"] > created.json()["updated_at"]
