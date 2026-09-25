"""T-03 (SPEC §12): tin chưa duyệt không public; giá bán/thuê không trộn (PLAN
task 3.4, UC-08). Không cần đăng nhập; projection không có dữ liệu nội bộ."""

from __future__ import annotations

from decimal import Decimal

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import ListingStatus, ListingType, ProjectStatus, PropertyStatus
from app.models import Project
from tests.integration import factories as f


pytestmark = [pytest.mark.integration]


@pytest.mark.parametrize(
    "status",
    [ListingStatus.DRAFT, ListingStatus.PENDING, ListingStatus.REJECTED, ListingStatus.CLOSED],
)
async def test_biet_uuid_tin_chua_duyet_van_khong_doc_duoc(
    client: httpx.AsyncClient, db_session: AsyncSession, status: ListingStatus
) -> None:
    listing = await f.make_listing(db_session, status=status)

    detail = await client.get(f"/api/v1/public/listings/{listing.id}")
    assert detail.status_code == 404
    listed = await client.get("/api/v1/public/listings")
    assert listed.json()["total"] == 0


async def test_tin_da_duyet_tra_projection_cong_khai(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    listing = await f.make_listing(db_session, status=ListingStatus.APPROVED)

    response = await client.get(f"/api/v1/public/listings/{listing.id}")
    assert response.status_code == 200
    body = response.json()
    assert body["asking_price"] == "2000000000.00"
    assert body["price_unit"] == "total"
    assert set(body["property"]) == {"unit_code", "area_m2", "bedrooms", "floor"}
    for internal in ("agent_id", "reviewed_by", "status", "rejection_reason", "row_version"):
        assert internal not in body


async def test_can_da_giu_hoac_du_an_inactive_khong_con_cong_khai(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    reserved_unit = await f.make_property(db_session)
    reserved_unit.status = PropertyStatus.RESERVED.value
    reserved = await f.make_listing(db_session, property_obj=reserved_unit)

    inactive_project = await f.make_project(db_session)
    inactive_project.status = ProjectStatus.INACTIVE.value
    in_inactive = await f.make_listing(
        db_session, property_obj=await f.make_property(db_session, project=inactive_project)
    )
    visible = await f.make_listing(db_session)
    await db_session.flush()

    listed = await client.get("/api/v1/public/listings")
    assert [item["id"] for item in listed.json()["items"]] == [str(visible.id)]
    for hidden in (reserved, in_inactive):
        assert (await client.get(f"/api/v1/public/listings/{hidden.id}")).status_code == 404


async def test_loc_theo_loai_khong_tron_gia_ban_va_gia_thue(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    sale = await f.make_listing(db_session, listing_type=ListingType.SALE)
    rent = await f.make_listing(db_session, listing_type=ListingType.RENT)
    rent.asking_price = Decimal("15000000")
    await db_session.flush()

    rents = await client.get(
        "/api/v1/public/listings",
        params={"listing_type": "rent", "max_price": "20000000", "sort": "asking_price"},
    )
    assert rents.status_code == 200
    assert [item["id"] for item in rents.json()["items"]] == [str(rent.id)]
    assert rents.json()["items"][0]["price_unit"] == "month"

    sales = await client.get("/api/v1/public/listings", params={"listing_type": "sale"})
    assert [item["id"] for item in sales.json()["items"]] == [str(sale.id)]


@pytest.mark.parametrize(
    ("params", "field"),
    [
        ({"min_price": "1000"}, "listing_type"),
        ({"sort": "-asking_price"}, "listing_type"),
        ({"listing_type": "sale", "min_price": "5", "max_price": "1"}, "min_price"),
        ({"province_code": "99"}, "province_code"),
        ({"province_code": "01", "ward_code": "26734"}, "ward_code"),
    ],
)
async def test_bo_loc_sai_bi_422(
    client: httpx.AsyncClient, params: dict[str, str], field: str
) -> None:
    response = await client.get("/api/v1/public/listings", params=params)
    assert response.status_code == 422
    assert field in response.json()["error"]["details"]


async def test_gia_am_bi_422(client: httpx.AsyncClient) -> None:
    response = await client.get(
        "/api/v1/public/listings", params={"listing_type": "sale", "min_price": "-1"}
    )
    assert response.status_code == 422


async def test_tu_khoa_khop_tieu_de_hoac_ten_du_an_va_escape_ky_tu_dai_dien(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    project = await f.make_project(db_session)
    project.name = "Vinhomes Sông Hồng"
    by_project = await f.make_listing(
        db_session, property_obj=await f.make_property(db_session, project=project)
    )
    by_title = await f.make_listing(db_session)
    by_title.title = "Căn góc view hồ Tây"
    await db_session.flush()

    project_hit = await client.get("/api/v1/public/listings", params={"q": "sông hồng"})
    assert [item["id"] for item in project_hit.json()["items"]] == [str(by_project.id)]

    title_hit = await client.get("/api/v1/public/listings", params={"q": "hồ tây"})
    assert [item["id"] for item in title_hit.json()["items"]] == [str(by_title.id)]

    wildcard = await client.get("/api/v1/public/listings", params={"q": "%"})
    assert wildcard.json()["total"] == 0


async def test_loc_theo_dia_ban(client: httpx.AsyncClient, db_session: AsyncSession) -> None:
    hanoi = await f.make_listing(db_session)
    hcm_project: Project = await f.make_project(db_session)
    hcm_project.province_code, hcm_project.ward_code = "79", "26734"
    await f.make_listing(
        db_session, property_obj=await f.make_property(db_session, project=hcm_project)
    )
    await db_session.flush()

    response = await client.get(
        "/api/v1/public/listings", params={"province_code": "01", "ward_code": "00004"}
    )
    assert [item["id"] for item in response.json()["items"]] == [str(hanoi.id)]
