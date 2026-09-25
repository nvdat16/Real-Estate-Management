"""Vòng đời tin đăng (PLAN task 3.3, 3.6; UC-07; bảng chuyển trạng thái SP-02).

Môi giới chỉ quản lý tin của mình và không duyệt được tin; Admin duyệt/từ chối.
Sửa tin đã duyệt đưa tin về nháp và gỡ khỏi trang công khai; mỗi căn chỉ có
một tin chờ duyệt/đã duyệt.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import ContractStatus, ListingStatus, PropertyStatus
from app.core.security import create_access_token
from app.models import Agent, Property, User
from tests.integration import factories as f


pytestmark = [pytest.mark.integration]

ADMIN_PERMISSIONS = ("project.manage", "property.manage", "listing.manage", "listing.approve")


def _auth(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user.id, user.auth_version)}"}


async def _admin(db_session: AsyncSession) -> User:
    return await f.make_actor(db_session, role_code="admin", permission_codes=ADMIN_PERMISSIONS)


def _draft_payload(unit: Property, **overrides: Any) -> dict[str, Any]:
    return {
        "property_id": str(unit.id),
        "listing_type": "sale",
        "asking_price": "2500000000",
        "title": "Bán căn 2 phòng ngủ",
        "description": "Căn góc, nhiều ánh sáng.",
        **overrides,
    }


async def _create_draft(
    client: httpx.AsyncClient, user: User, unit: Property, **overrides: Any
) -> dict[str, Any]:
    response = await client.post(
        "/api/v1/listings", json=_draft_payload(unit, **overrides), headers=_auth(user)
    )
    assert response.status_code == 201, response.text
    return dict(response.json())


async def _command(
    client: httpx.AsyncClient, user: User, listing: dict[str, Any], command: str, **body: Any
) -> httpx.Response:
    return await client.post(
        f"/api/v1/listings/{listing['id']}/{command}",
        json={"row_version": listing["row_version"], **body},
        headers=_auth(user),
    )


async def test_luong_nhap_gui_duyet_cong_khai_sua_ve_nhap(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    admin = await _admin(db_session)
    agent_user, agent = await f.make_agent_actor(db_session)
    unit = await f.make_property(db_session)

    draft = await _create_draft(client, agent_user, unit)
    assert draft["status"] == "draft"
    assert draft["agent_id"] == str(agent.id)
    assert draft["price_unit"] == "total"

    submitted = await _command(client, agent_user, draft, "submit")
    assert submitted.status_code == 200
    assert submitted.json()["status"] == "pending"

    approved = await _command(client, admin, submitted.json(), "approve")
    assert approved.status_code == 200
    assert approved.json()["reviewed_by"] == str(admin.id)
    public = await client.get(f"/api/v1/public/listings/{draft['id']}")
    assert public.status_code == 200

    edited = await client.patch(
        f"/api/v1/listings/{draft['id']}",
        json={"asking_price": "2400000000", "row_version": approved.json()["row_version"]},
        headers=_auth(agent_user),
    )
    assert edited.status_code == 200
    body = edited.json()
    assert body["status"] == "draft"
    assert body["reviewed_by"] is None and body["reviewed_at"] is None
    hidden = await client.get(f"/api/v1/public/listings/{draft['id']}")
    assert hidden.status_code == 404


async def test_tu_choi_can_ly_do_va_sua_lai_ve_nhap(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    admin = await _admin(db_session)
    agent_user, _ = await f.make_agent_actor(db_session)
    unit = await f.make_property(db_session)
    draft = await _create_draft(client, agent_user, unit)
    pending = (await _command(client, agent_user, draft, "submit")).json()

    missing_reason = await _command(client, admin, pending, "reject")
    assert missing_reason.status_code == 422

    rejected = await _command(client, admin, pending, "reject", reason="Ảnh không rõ ràng")
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "rejected"
    assert rejected.json()["rejection_reason"] == "Ảnh không rõ ràng"

    edited = await client.patch(
        f"/api/v1/listings/{draft['id']}",
        json={"title": "Tiêu đề đã sửa", "row_version": rejected.json()["row_version"]},
        headers=_auth(agent_user),
    )
    assert edited.status_code == 200
    assert edited.json()["status"] == "draft"
    assert edited.json()["rejection_reason"] is None


async def test_moi_gioi_khong_duyet_duoc_tin(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    agent_user, _ = await f.make_agent_actor(db_session)
    unit = await f.make_property(db_session)
    draft = await _create_draft(client, agent_user, unit)
    pending = (await _command(client, agent_user, draft, "submit")).json()

    for command, body in (("approve", {}), ("reject", {"reason": "Tự từ chối"})):
        response = await _command(client, agent_user, pending, command, **body)
        assert response.status_code == 403, command


async def test_moi_gioi_khong_doc_sua_tin_cua_nguoi_khac(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    owner_user, _ = await f.make_agent_actor(db_session)
    other_user, _ = await f.make_agent_actor(db_session)
    unit = await f.make_property(db_session)
    draft = await _create_draft(client, owner_user, unit)

    read = await client.get(f"/api/v1/listings/{draft['id']}", headers=_auth(other_user))
    assert read.status_code == 404
    edit = await client.patch(
        f"/api/v1/listings/{draft['id']}",
        json={"title": "Chiếm tin", "row_version": 1},
        headers=_auth(other_user),
    )
    assert edit.status_code == 404
    listed = await client.get("/api/v1/listings", headers=_auth(other_user))
    assert listed.json()["total"] == 0


async def test_moi_gioi_khong_lap_tin_duoi_ten_nguoi_khac(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    agent_user, _ = await f.make_agent_actor(db_session)
    _, other_agent = await f.make_agent_actor(db_session)
    unit = await f.make_property(db_session)

    response = await client.post(
        "/api/v1/listings",
        json=_draft_payload(unit, agent_id=str(other_agent.id)),
        headers=_auth(agent_user),
    )
    assert response.status_code == 403


async def test_admin_lap_tin_thay_moi_gioi(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    admin = await _admin(db_session)
    _, agent = await f.make_agent_actor(db_session)
    unit = await f.make_property(db_session)

    without_agent = await client.post(
        "/api/v1/listings", json=_draft_payload(unit), headers=_auth(admin)
    )
    assert without_agent.status_code == 422

    created = await _create_draft(client, admin, unit, agent_id=str(agent.id))
    assert created["agent_id"] == str(agent.id)


async def test_mot_can_chi_mot_tin_cho_duyet_qua_api(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    agent_user, _ = await f.make_agent_actor(db_session)
    unit = await f.make_property(db_session)
    first = await _create_draft(client, agent_user, unit)
    second = await _create_draft(client, agent_user, unit, title="Tin thứ hai")

    assert (await _command(client, agent_user, first, "submit")).status_code == 200
    conflict = await _command(client, agent_user, second, "submit")
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "PROPERTY_UNAVAILABLE"


async def test_tin_cho_duyet_phai_rut_truoc_khi_sua(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    agent_user, _ = await f.make_agent_actor(db_session)
    unit = await f.make_property(db_session)
    draft = await _create_draft(client, agent_user, unit)
    pending = (await _command(client, agent_user, draft, "submit")).json()

    edit = await client.patch(
        f"/api/v1/listings/{draft['id']}",
        json={"title": "Sửa khi chờ duyệt", "row_version": pending["row_version"]},
        headers=_auth(agent_user),
    )
    assert edit.status_code == 409
    assert edit.json()["error"]["code"] == "INVALID_STATE"

    withdrawn = await _command(client, agent_user, pending, "withdraw")
    assert withdrawn.status_code == 200
    assert withdrawn.json()["status"] == "draft"


async def test_gia_sai_don_vi_hoac_co_phan_le_bi_422(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    agent_user, _ = await f.make_agent_actor(db_session)
    unit = await f.make_property(db_session)

    for overrides in (
        {"listing_type": "rent", "price_unit": "total"},
        {"listing_type": "sale", "price_unit": "month"},
        {"asking_price": "2500000000.50"},
        {"asking_price": "0"},
    ):
        response = await client.post(
            "/api/v1/listings", json=_draft_payload(unit, **overrides), headers=_auth(agent_user)
        )
        assert response.status_code == 422, overrides


async def test_status_client_gui_khi_sua_bi_bo_qua(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    agent_user, _ = await f.make_agent_actor(db_session)
    unit = await f.make_property(db_session)
    draft = await _create_draft(client, agent_user, unit)

    response = await client.patch(
        f"/api/v1/listings/{draft['id']}",
        json={"title": "Tự duyệt", "status": "approved", "row_version": draft["row_version"]},
        headers=_auth(agent_user),
    )
    assert response.status_code == 200
    assert response.json()["status"] == "draft"


async def test_duyet_bi_chan_khi_can_da_duoc_giu(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    admin = await _admin(db_session)
    agent_user, _ = await f.make_agent_actor(db_session)
    unit = await f.make_property(db_session)
    draft = await _create_draft(client, agent_user, unit)
    pending = (await _command(client, agent_user, draft, "submit")).json()

    unit.status = PropertyStatus.RESERVED.value
    await db_session.flush()

    response = await _command(client, admin, pending, "approve")
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "PROPERTY_UNAVAILABLE"


async def test_khong_dong_tin_khi_co_hop_dong_cho_ky(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    admin = await _admin(db_session)
    listing = await f.make_listing(db_session, status=ListingStatus.APPROVED)
    await f.make_contract(db_session, listing=listing, status=ContractStatus.PENDING_SIGNATURES)

    response = await client.post(
        f"/api/v1/listings/{listing.id}/close", json={"row_version": 1}, headers=_auth(admin)
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "INVALID_STATE"


async def test_xoa_tin_theo_trang_thai_va_phu_thuoc(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    admin = await _admin(db_session)
    approved = await f.make_listing(db_session, status=ListingStatus.APPROVED)
    blocked_state = await client.delete(
        f"/api/v1/listings/{approved.id}", params={"row_version": 1}, headers=_auth(admin)
    )
    assert blocked_state.status_code == 409
    assert blocked_state.json()["error"]["code"] == "INVALID_STATE"

    rejected = await f.make_listing(db_session, status=ListingStatus.REJECTED)
    await f.make_contract(db_session, listing=rejected, status=ContractStatus.DRAFT)
    blocked_dependency = await client.delete(
        f"/api/v1/listings/{rejected.id}", params={"row_version": 1}, headers=_auth(admin)
    )
    assert blocked_dependency.status_code == 409
    assert blocked_dependency.json()["error"]["code"] == "DEPENDENCY_EXISTS"

    draft = await f.make_listing(db_session, status=ListingStatus.DRAFT)
    removed = await client.delete(
        f"/api/v1/listings/{draft.id}", params={"row_version": 1}, headers=_auth(admin)
    )
    assert removed.status_code == 204
    gone = await client.get(f"/api/v1/listings/{draft.id}", headers=_auth(admin))
    assert gone.status_code == 404


async def test_moi_gioi_inactive_khong_gui_duyet_duoc(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    agent_user, agent = await f.make_agent_actor(db_session)
    unit = await f.make_property(db_session)
    draft = await _create_draft(client, agent_user, unit)

    profile = await db_session.get(Agent, agent.id)
    assert profile is not None
    profile.status = "inactive"
    await db_session.flush()

    response = await _command(client, agent_user, draft, "submit")
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "INVALID_STATE"


async def test_lenh_voi_row_version_cu_tra_409(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    agent_user, _ = await f.make_agent_actor(db_session)
    unit = await f.make_property(db_session)
    draft = await _create_draft(client, agent_user, unit)
    await _command(client, agent_user, draft, "submit")

    stale = await _command(client, agent_user, {**draft, "status": "pending"}, "withdraw")
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "VERSION_CONFLICT"


async def test_hang_cho_duyet_cua_admin_va_bo_loc_cua_moi_gioi(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    admin = await _admin(db_session)
    agent_user, agent = await f.make_agent_actor(db_session)
    _, other_agent = await f.make_agent_actor(db_session)
    mine_pending = await f.make_listing(db_session, agent=agent, status=ListingStatus.PENDING)
    mine_draft = await f.make_listing(db_session, agent=agent, status=ListingStatus.DRAFT)
    others_pending = await f.make_listing(
        db_session, agent=other_agent, status=ListingStatus.PENDING
    )
    # Cùng transaction thì `now()` như nhau: gán mốc riêng để thứ tự sắp xếp xác định.
    base = datetime(2026, 1, 1, tzinfo=UTC)
    for offset, item in enumerate((mine_pending, mine_draft, others_pending)):
        item.created_at = base + timedelta(minutes=offset)
    await db_session.flush()

    queue = await client.get(
        "/api/v1/listings", params={"status": "pending", "sort": "created_at"}, headers=_auth(admin)
    )
    assert [item["id"] for item in queue.json()["items"]] == [
        str(mine_pending.id),
        str(others_pending.id),
    ]

    by_agent = await client.get(
        "/api/v1/listings", params={"agent_id": str(other_agent.id)}, headers=_auth(admin)
    )
    assert [item["id"] for item in by_agent.json()["items"]] == [str(others_pending.id)]

    # Môi giới lọc theo agent_id của người khác vẫn chỉ nhận tin của chính mình.
    own = await client.get(
        "/api/v1/listings",
        params={"agent_id": str(other_agent.id), "sort": "created_at"},
        headers=_auth(agent_user),
    )
    assert [item["id"] for item in own.json()["items"]] == [
        str(mine_pending.id),
        str(mine_draft.id),
    ]
