"""Kiểm chứng các invariant được thực thi ở tầng database (PLAN task 1.6).

Đây là những quy tắc mà service không được phép làm sai; nếu chỉ kiểm tra trong
Python thì hai request đồng thời vẫn lọt. Bộ test này tương ứng kịch bản 2–5 của
ERD mục 9 và các mã T-03, T-05, T-07, T-09 trong SPEC mục 12.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import ContractStatus, ListingStatus, ListingType, PartyRole, PriceUnit
from app.models import (
    Commission,
    ContractSignature,
    Listing,
    Property,
    User,
)
from tests.integration import factories as f


pytestmark = [pytest.mark.integration]


async def test_email_phai_duy_nhat(db_session: AsyncSession) -> None:
    await f.make_user(db_session, email="trung@example.test")

    db_session.add(
        User(
            email="trung@example.test",
            password_hash="x",
            full_name="Trùng email",
        )
    )
    with pytest.raises(IntegrityError, match="uq_users_email"):
        await db_session.flush()


async def test_ma_can_duy_nhat_trong_du_an(db_session: AsyncSession) -> None:
    project = await f.make_project(db_session)
    await f.make_property(db_session, project=project, unit_code="A-101")

    db_session.add(
        Property(
            project_id=project.id,
            unit_code="A-101",
            area_m2=Decimal("50.00"),
            bedrooms=1,
        )
    )
    with pytest.raises(IntegrityError, match="uq_properties_project_id_unit_code"):
        await db_session.flush()


async def test_khong_tron_gia_ban_va_gia_thue(db_session: AsyncSession) -> None:
    """FR-06: chỉ cho phép cặp sale/total hoặc rent/month."""
    property_obj = await f.make_property(db_session)
    agent = await f.make_agent(db_session)

    db_session.add(
        Listing(
            property_id=property_obj.id,
            agent_id=agent.id,
            listing_type=ListingType.SALE.value,
            asking_price=Decimal("15000000.00"),
            price_unit=PriceUnit.MONTH.value,
            title="Tin sai đơn vị giá",
            description="sale không được đi với month",
            status=ListingStatus.DRAFT.value,
        )
    )
    with pytest.raises(IntegrityError, match="ck_listings_type_price_unit_pair"):
        await db_session.flush()


async def test_mot_can_chi_co_mot_tin_dang_cho_duyet_hoac_da_duyet(
    db_session: AsyncSession,
) -> None:
    """A-07, T-03: nhiều bản nháp được phép, nhưng chỉ một tin pending/approved."""
    property_obj = await f.make_property(db_session)
    await f.make_listing(db_session, property_obj=property_obj, status=ListingStatus.APPROVED)

    # Bản nháp thứ hai trên cùng căn vẫn hợp lệ.
    await f.make_listing(db_session, property_obj=property_obj, status=ListingStatus.DRAFT)

    with pytest.raises(IntegrityError, match="uq_listings_active_property"):
        await f.make_listing(db_session, property_obj=property_obj, status=ListingStatus.PENDING)


async def test_mot_can_chi_co_mot_hop_dong_giu_cho(db_session: AsyncSession) -> None:
    """T-05: hai hợp đồng không thể cùng giữ một căn."""
    property_obj = await f.make_property(db_session)
    listing = await f.make_listing(db_session, property_obj=property_obj)
    await f.make_contract(
        db_session,
        listing=listing,
        status=ContractStatus.PENDING_SIGNATURES,
    )

    with pytest.raises(IntegrityError, match="uq_contracts_active_property"):
        await f.make_contract(
            db_session,
            listing=listing,
            status=ContractStatus.PENDING_SIGNATURES,
        )


async def test_phien_ban_phai_cung_loai_giao_dich_voi_hop_dong(
    db_session: AsyncSession,
) -> None:
    """FK ghép (contract_id, contract_type) chặn phiên bản lệch loại giao dịch."""
    contract = await f.make_contract(db_session, contract_type=ListingType.SALE)

    with pytest.raises(IntegrityError, match="fk_contract_versions_contract_id_contract_type"):
        await f.make_contract_version(
            db_session,
            contract=contract,
            contract_type=ListingType.RENT.value,
        )


async def test_hop_dong_thue_bat_buoc_co_khoang_thoi_gian(db_session: AsyncSession) -> None:
    contract = await f.make_contract(db_session, contract_type=ListingType.RENT)
    version = await f.make_contract_version(db_session, contract=contract)
    version.start_date = None
    version.end_date = None

    with pytest.raises(IntegrityError, match="ck_contract_versions_rent_needs_dates"):
        await db_session.flush()


async def test_khong_ky_bang_challenge_cua_ben_khac(db_session: AsyncSession) -> None:
    """T-07: challenge dùng để ký phải thuộc đúng bên ký đó."""
    contract = await f.make_contract(db_session, status=ContractStatus.PENDING_SIGNATURES)
    version = await f.make_contract_version(db_session, contract=contract)
    customer_party = await f.make_party(db_session, version=version, role=PartyRole.CUSTOMER)
    representative_party = await f.make_party(
        db_session, version=version, role=PartyRole.REPRESENTATIVE
    )
    challenge_of_representative = await f.make_challenge(db_session, party=representative_party)

    db_session.add(
        ContractSignature(
            party_id=customer_party.id,
            challenge_id=challenge_of_representative.id,
            signed_content_hash=uuid.uuid4().hex,
            signed_at=datetime.now(UTC),
        )
    )
    with pytest.raises(IntegrityError, match="fk_contract_signatures_challenge_id_party_id"):
        await db_session.flush()


async def test_mot_ben_chi_co_mot_chu_ky(db_session: AsyncSession) -> None:
    contract = await f.make_contract(db_session, status=ContractStatus.PENDING_SIGNATURES)
    version = await f.make_contract_version(db_session, contract=contract)
    party = await f.make_party(db_session, version=version)
    first = await f.make_challenge(db_session, party=party)

    db_session.add(
        ContractSignature(
            party_id=party.id,
            challenge_id=first.id,
            signed_content_hash=uuid.uuid4().hex,
            signed_at=datetime.now(UTC),
        )
    )
    await db_session.flush()

    first.consumed_at = datetime.now(UTC)
    await db_session.flush()
    second = await f.make_challenge(db_session, party=party)

    db_session.add(
        ContractSignature(
            party_id=party.id,
            challenge_id=second.id,
            signed_content_hash=uuid.uuid4().hex,
            signed_at=datetime.now(UTC),
        )
    )
    with pytest.raises(IntegrityError, match="uq_contract_signatures_party_id"):
        await db_session.flush()


async def test_mot_ben_chi_co_mot_challenge_dang_mo(db_session: AsyncSession) -> None:
    contract = await f.make_contract(db_session, status=ContractStatus.PENDING_SIGNATURES)
    version = await f.make_contract_version(db_session, contract=contract)
    party = await f.make_party(db_session, version=version)
    await f.make_challenge(db_session, party=party)

    with pytest.raises(IntegrityError, match="uq_signing_challenges_open_party"):
        await f.make_challenge(db_session, party=party)


async def test_hoa_hong_phai_dung_cong_thuc(db_session: AsyncSession) -> None:
    """T-09: số tiền hoa hồng không thể lệch khỏi base × rate."""
    contract = await f.make_contract(db_session, status=ContractStatus.SIGNED)
    version = await f.make_contract_version(db_session, contract=contract)

    db_session.add(
        Commission(
            contract_id=contract.id,
            contract_version_id=version.id,
            agent_id=contract.agent_id,
            base_amount=Decimal("2000000000.00"),
            rate_percent=Decimal("1.5000"),
            amount=Decimal("99000000.00"),
        )
    )
    with pytest.raises(IntegrityError, match="ck_commissions_amount_matches_formula"):
        await db_session.flush()


async def test_hoa_hong_phai_thuoc_moi_gioi_cua_hop_dong(db_session: AsyncSession) -> None:
    contract = await f.make_contract(db_session, status=ContractStatus.SIGNED)
    version = await f.make_contract_version(db_session, contract=contract)
    other_agent = await f.make_agent(db_session)

    db_session.add(
        Commission(
            contract_id=contract.id,
            contract_version_id=version.id,
            agent_id=other_agent.id,
            base_amount=Decimal("2000000000.00"),
            rate_percent=Decimal("1.5000"),
            amount=Decimal("30000000.00"),
        )
    )
    with pytest.raises(IntegrityError, match="fk_commissions_contract_id_agent_id"):
        await db_session.flush()


async def test_mot_hop_dong_chi_co_mot_khoan_hoa_hong(db_session: AsyncSession) -> None:
    """T-07: job lặp không được tạo khoản hoa hồng thứ hai."""
    contract = await f.make_contract(db_session, status=ContractStatus.SIGNED)
    version = await f.make_contract_version(db_session, contract=contract)

    for _ in range(2):
        db_session.add(
            Commission(
                contract_id=contract.id,
                contract_version_id=version.id,
                agent_id=contract.agent_id,
                base_amount=Decimal("2000000000.00"),
                rate_percent=Decimal("1.5000"),
                amount=Decimal("30000000.00"),
            )
        )

    with pytest.raises(IntegrityError, match="uq_commissions_contract_id"):
        await db_session.flush()
