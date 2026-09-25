"""Use case cho tin đăng (PLAN task 3.3–3.4, UC-07/UC-08).

Mọi lệnh đổi trạng thái đi theo bảng chuyển trạng thái của SPEC SP-02. Trạng
thái hiện tại đọc từ bản ghi đã tải rồi mới UPDATE có điều kiện `row_version`:
nếu bản ghi đổi giữa hai bước, UPDATE không khớp dòng nào và trả 409, nên không
có lệnh nào chạy trên trạng thái cũ.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import (
    AgentStatus,
    ContractStatus,
    ListingStatus,
    ListingType,
    PriceUnit,
    ProjectStatus,
    PropertyStatus,
)
from app.common.schemas.pagination import Page
from app.common.utils import expect
from app.common.utils.pagination import PageParams
from app.core.exceptions import (
    dependency_exists,
    invalid_state,
    permission_denied,
    property_unavailable,
    resource_not_found,
    validation_error,
    version_conflict,
)
from app.modules.agents import repository as agents_repository
from app.modules.agents.models import Agent
from app.modules.audit_logs.service import record_audit
from app.modules.listings import repository as listings_repository
from app.modules.listings.permissions import (
    ListingActor,
    ensure_can_manage,
    ensure_can_review,
    ensure_in_scope,
    resolve_actor,
)
from app.modules.listings.repository import (
    ListingFilters,
    ListingRow,
    PublicFilters,
    PublicListingRow,
)
from app.modules.listings.schemas import (
    ListingCreateRequest,
    ListingUpdateRequest,
    ListingView,
    PublicListingView,
    PublicProjectView,
    PublicPropertyView,
)
from app.modules.projects import repository as projects_repository
from app.modules.projects.locations import is_known_location, is_known_province
from app.modules.properties import repository as properties_repository
from app.modules.properties.repository import PropertyRow
from app.modules.users.models import User


_PRICE_UNIT_FOR = {ListingType.SALE: PriceUnit.TOTAL, ListingType.RENT: PriceUnit.MONTH}
_UNIQUE_ACTIVE_PROPERTY = "uq_listings_active_property"
_LIVE_CONTRACT_STATUSES = (
    ContractStatus.DRAFT,
    ContractStatus.PENDING_SIGNATURES,
    ContractStatus.SIGNED,
)
_REQUIRED_FIELDS = ("listing_type", "asking_price", "title", "description")


def _to_view(listing: ListingRow) -> ListingView:
    return ListingView.model_validate(listing, from_attributes=True)


def _resolve_price_unit(listing_type: str, price_unit: str | None) -> str:
    """Chỉ nhận cặp `sale/total` hoặc `rent/month` (FR-06); DB có CHECK cùng
    điều kiện, ở đây trả 422 rõ ràng thay vì để lỗi CHECK nổ ra."""
    expected = _PRICE_UNIT_FOR[ListingType(listing_type)]
    if price_unit is not None and price_unit != expected:
        raise validation_error(
            {"price_unit": price_unit, "listing_type": listing_type, "reason": "unit_mismatch"}
        )
    return expected.value


async def _load(db: AsyncSession, actor: ListingActor, listing_id: uuid.UUID) -> ListingRow:
    return ensure_in_scope(actor, await listings_repository.get_active_by_id(db, listing_id))


def _ensure_status(listing: ListingRow, *allowed: ListingStatus, message: str) -> None:
    if listing.status not in allowed:
        raise invalid_state(message)


async def _ensure_agent_active(db: AsyncSession, agent_id: uuid.UUID) -> Agent:
    agent = await agents_repository.get_by_id(db, agent_id)
    if agent is None or agent.deleted_at is not None or agent.status != AgentStatus.ACTIVE:
        raise invalid_state("Môi giới phụ trách không hoạt động.")
    return agent


async def _ensure_property_open(
    db: AsyncSession, property_id: uuid.UUID, *, lock: bool = False
) -> PropertyRow:
    """Căn available thuộc dự án active, cả hai chưa xóa. `lock` giữ khóa dòng căn
    tới hết transaction để không có luồng hợp đồng nào giữ căn xen vào giữa lúc
    kiểm tra và lúc đổi trạng thái tin."""
    item = await properties_repository.get_active_by_id(db, property_id, for_update=lock)
    if item is None or item.status != PropertyStatus.AVAILABLE:
        raise property_unavailable()
    project = await projects_repository.get_active_by_id(db, item.project_id)
    if project is None or project.status != ProjectStatus.ACTIVE:
        raise invalid_state("Dự án của căn đang không hoạt động.")
    return item


async def _save(
    db: AsyncSession,
    actor: ListingActor,
    listing: ListingRow,
    expected_row_version: int,
    *,
    action: str,
    fields: dict[str, Any],
    summary: dict[str, Any],
) -> ListingView:
    try:
        async with db.begin_nested():
            ok = await listings_repository.update_fields(
                db, listing.id, expected_row_version, **fields
            )
    except IntegrityError as exc:
        if _UNIQUE_ACTIVE_PROPERTY in str(exc.orig):
            raise property_unavailable("Căn đã có tin khác đang chờ duyệt hoặc đã duyệt.") from exc
        raise
    if not ok:
        raise version_conflict()

    await record_audit(
        db,
        actor=actor.user,
        action=action,
        entity_type="listings",
        entity_id=listing.id,
        change_summary=summary,
    )
    await db.commit()
    return _to_view(expect(await listings_repository.get_active_by_id(db, listing.id)))


def _transition_summary(listing: ListingRow, to: ListingStatus, **extra: Any) -> dict[str, Any]:
    return {"from": listing.status, "to": to.value, **extra}


async def _resolve_owner_agent(
    db: AsyncSession, actor: ListingActor, requested_agent_id: uuid.UUID | None
) -> Agent:
    if requested_agent_id is not None and actor.sees_all:
        agent = await agents_repository.get_by_id(db, requested_agent_id)
        if agent is None or agent.deleted_at is not None:
            raise validation_error({"agent_id": str(requested_agent_id), "reason": "not_found"})
        return await _ensure_agent_active(db, agent.id)

    if requested_agent_id is not None and (
        actor.agent is None or requested_agent_id != actor.agent.id
    ):
        # Môi giới không được lập tin dưới tên môi giới khác (SPEC SP-02).
        raise permission_denied()
    if actor.agent is None:
        if actor.sees_all:
            raise validation_error({"agent_id": None, "reason": "required"})
        raise invalid_state("Tài khoản chưa có hồ sơ môi giới.")
    return await _ensure_agent_active(db, actor.agent.id)


async def create(db: AsyncSession, *, user: User, payload: ListingCreateRequest) -> ListingView:
    actor = await resolve_actor(db, user)
    ensure_can_manage(actor)
    agent = await _resolve_owner_agent(db, actor, payload.agent_id)
    if await properties_repository.get_active_by_id(db, payload.property_id) is None:
        raise validation_error({"property_id": str(payload.property_id), "reason": "not_found"})
    await _ensure_property_open(db, payload.property_id)

    listing = await listings_repository.insert(
        db,
        property_id=payload.property_id,
        agent_id=agent.id,
        listing_type=payload.listing_type.value,
        asking_price=payload.asking_price,
        price_unit=_resolve_price_unit(
            payload.listing_type, payload.price_unit.value if payload.price_unit else None
        ),
        title=payload.title,
        description=payload.description,
    )
    await record_audit(
        db,
        actor=user,
        action="listing.create",
        entity_type="listings",
        entity_id=listing.id,
        change_summary={
            "property_id": str(listing.property_id),
            "agent_id": str(listing.agent_id),
            "listing_type": listing.listing_type,
            "asking_price": str(listing.asking_price),
        },
    )
    await db.commit()
    return _to_view(listing)


async def get(db: AsyncSession, *, user: User, listing_id: uuid.UUID) -> ListingView:
    actor = await resolve_actor(db, user)
    return _to_view(await _load(db, actor, listing_id))


async def list_(
    db: AsyncSession,
    *,
    user: User,
    page_params: PageParams,
    sort: str,
    filters: ListingFilters,
) -> Page[ListingView]:
    actor = await resolve_actor(db, user)
    if actor.sees_all:
        items, total = await listings_repository.list_page(
            db, page_params, sort=sort, filters=filters
        )
    elif actor.agent is None:
        items, total = [], 0
    else:
        # `agent_id` trong bộ lọc chỉ có nghĩa với người thấy mọi tin; môi giới
        # luôn bị giới hạn về tin của chính mình.
        own_filters = ListingFilters(**{**filters.__dict__, "agent_id": None})
        items, total = await listings_repository.list_page(
            db, page_params, sort=sort, filters=own_filters, scope_agent_id=actor.agent.id
        )
    return Page(
        items=[_to_view(item) for item in items],
        page=page_params.page,
        page_size=page_params.page_size,
        total=total,
    )


async def update(
    db: AsyncSession, *, user: User, listing_id: uuid.UUID, payload: ListingUpdateRequest
) -> ListingView:
    actor = await resolve_actor(db, user)
    ensure_can_manage(actor)
    listing = await _load(db, actor, listing_id)
    if listing.status == ListingStatus.PENDING:
        raise invalid_state("Tin đang chờ duyệt, hãy rút duyệt trước khi sửa.")
    if listing.status == ListingStatus.CLOSED:
        raise invalid_state("Tin đã đóng, không sửa được.")

    fields: dict[str, Any] = payload.model_dump(exclude_unset=True)
    fields.pop("row_version")
    null_required = [name for name in _REQUIRED_FIELDS if name in fields and fields[name] is None]
    if null_required:
        raise validation_error({"fields": null_required, "reason": "must_not_be_null"})

    if "listing_type" in fields or "price_unit" in fields:
        new_type = str(fields.get("listing_type") or listing.listing_type)
        if new_type != listing.listing_type and await listings_repository.has_contract(
            db, listing.id, _LIVE_CONTRACT_STATUSES
        ):
            raise invalid_state("Tin đã có hợp đồng, không đổi được loại giao dịch.")
        requested_unit = fields.get("price_unit")
        fields["listing_type"] = new_type
        fields["price_unit"] = _resolve_price_unit(
            new_type, str(requested_unit) if requested_unit else None
        )

    summary: dict[str, Any] = payload.model_dump(
        mode="json", exclude_unset=True, exclude={"row_version"}
    )
    if listing.status in (ListingStatus.APPROVED, ListingStatus.REJECTED):
        if await listings_repository.has_contract(
            db, listing.id, (ContractStatus.PENDING_SIGNATURES,)
        ):
            raise invalid_state("Tin có hợp đồng đang chờ ký, không sửa được.")
        # Sửa tin đã duyệt/bị từ chối đưa tin về nháp và bỏ quyết định duyệt hiện
        # tại; quyết định cũ vẫn còn trong audit (SPEC SP-02).
        fields.update(
            status=ListingStatus.DRAFT.value,
            reviewed_by=None,
            reviewed_at=None,
            rejection_reason=None,
        )
        summary.update(_transition_summary(listing, ListingStatus.DRAFT))

    return await _save(
        db,
        actor,
        listing,
        payload.row_version,
        action="listing.update",
        fields=fields,
        summary=summary,
    )


async def submit(
    db: AsyncSession, *, user: User, listing_id: uuid.UUID, expected_row_version: int
) -> ListingView:
    actor = await resolve_actor(db, user)
    ensure_can_manage(actor)
    listing = await _load(db, actor, listing_id)
    _ensure_status(listing, ListingStatus.DRAFT, message="Chỉ gửi duyệt được tin nháp.")
    await _ensure_agent_active(db, listing.agent_id)
    await _ensure_property_open(db, listing.property_id, lock=True)
    return await _save(
        db,
        actor,
        listing,
        expected_row_version,
        action="listing.submit",
        fields={"status": ListingStatus.PENDING.value},
        summary=_transition_summary(listing, ListingStatus.PENDING),
    )


async def withdraw(
    db: AsyncSession, *, user: User, listing_id: uuid.UUID, expected_row_version: int
) -> ListingView:
    actor = await resolve_actor(db, user)
    ensure_can_manage(actor)
    listing = await _load(db, actor, listing_id)
    _ensure_status(listing, ListingStatus.PENDING, message="Chỉ rút duyệt được tin đang chờ duyệt.")
    return await _save(
        db,
        actor,
        listing,
        expected_row_version,
        action="listing.withdraw",
        fields={"status": ListingStatus.DRAFT.value},
        summary=_transition_summary(listing, ListingStatus.DRAFT),
    )


async def approve(
    db: AsyncSession, *, user: User, listing_id: uuid.UUID, expected_row_version: int
) -> ListingView:
    actor = await resolve_actor(db, user)
    ensure_can_review(actor)
    listing = await _load(db, actor, listing_id)
    _ensure_status(listing, ListingStatus.PENDING, message="Chỉ duyệt được tin đang chờ duyệt.")
    # Kiểm tra lại lúc duyệt: căn/dự án/môi giới có thể đã đổi kể từ lúc gửi.
    await _ensure_agent_active(db, listing.agent_id)
    await _ensure_property_open(db, listing.property_id, lock=True)
    return await _save(
        db,
        actor,
        listing,
        expected_row_version,
        action="listing.approve",
        fields={
            "status": ListingStatus.APPROVED.value,
            "reviewed_by": user.id,
            "reviewed_at": datetime.now(UTC),
            "rejection_reason": None,
        },
        summary=_transition_summary(listing, ListingStatus.APPROVED),
    )


async def reject(
    db: AsyncSession,
    *,
    user: User,
    listing_id: uuid.UUID,
    expected_row_version: int,
    reason: str,
) -> ListingView:
    actor = await resolve_actor(db, user)
    ensure_can_review(actor)
    listing = await _load(db, actor, listing_id)
    _ensure_status(listing, ListingStatus.PENDING, message="Chỉ từ chối được tin đang chờ duyệt.")
    return await _save(
        db,
        actor,
        listing,
        expected_row_version,
        action="listing.reject",
        fields={
            "status": ListingStatus.REJECTED.value,
            "reviewed_by": user.id,
            "reviewed_at": datetime.now(UTC),
            "rejection_reason": reason,
        },
        summary=_transition_summary(listing, ListingStatus.REJECTED, reason=reason),
    )


async def close(
    db: AsyncSession, *, user: User, listing_id: uuid.UUID, expected_row_version: int
) -> ListingView:
    actor = await resolve_actor(db, user)
    ensure_can_manage(actor)
    listing = await _load(db, actor, listing_id)
    _ensure_status(listing, ListingStatus.APPROVED, message="Chỉ đóng được tin đã duyệt.")
    if await listings_repository.has_contract(db, listing.id, (ContractStatus.PENDING_SIGNATURES,)):
        raise invalid_state("Tin có hợp đồng đang chờ ký, không đóng được.")
    return await _save(
        db,
        actor,
        listing,
        expected_row_version,
        action="listing.close",
        fields={"status": ListingStatus.CLOSED.value},
        summary=_transition_summary(listing, ListingStatus.CLOSED),
    )


async def delete(
    db: AsyncSession, *, user: User, listing_id: uuid.UUID, expected_row_version: int
) -> None:
    actor = await resolve_actor(db, user)
    ensure_can_manage(actor)
    listing = await _load(db, actor, listing_id)
    _ensure_status(
        listing,
        ListingStatus.DRAFT,
        ListingStatus.REJECTED,
        ListingStatus.CLOSED,
        message="Tin đang chờ duyệt phải rút duyệt, tin đã duyệt phải đóng trước khi xóa.",
    )
    if await listings_repository.has_contract(db, listing.id, _LIVE_CONTRACT_STATUSES):
        raise dependency_exists("Tin đang gắn với hợp đồng.")

    ok = await listings_repository.update_fields(
        db,
        listing.id,
        expected_row_version,
        deleted_at=datetime.now(UTC),
        deleted_by=user.id,
    )
    if not ok:
        raise version_conflict()
    await record_audit(
        db,
        actor=user,
        action="listing.delete",
        entity_type="listings",
        entity_id=listing.id,
        change_summary={"status": listing.status},
    )
    await db.commit()


def _to_public(row: PublicListingRow) -> PublicListingView:
    return PublicListingView(
        id=row.id,
        title=row.title,
        description=row.description,
        listing_type=row.listing_type,
        asking_price=row.asking_price,
        price_unit=row.price_unit,
        currency=row.currency,
        published_at=row.published_at,
        property=PublicPropertyView(
            unit_code=row.unit_code, area_m2=row.area_m2, bedrooms=row.bedrooms, floor=row.floor
        ),
        project=PublicProjectView(
            id=row.project_id,
            name=row.project_name,
            address=row.project_address,
            province_code=row.province_code,
            ward_code=row.ward_code,
        ),
    )


async def public_list(
    db: AsyncSession,
    *,
    page_params: PageParams,
    sort: str,
    listing_type: ListingType | None,
    min_price: Decimal | None,
    max_price: Decimal | None,
    province_code: str | None,
    ward_code: str | None,
    project_id: uuid.UUID | None,
    min_bedrooms: int | None,
    q: str | None,
) -> Page[PublicListingView]:
    errors: dict[str, str] = {}
    if min_price is not None and max_price is not None and min_price > max_price:
        errors["min_price"] = "must_be_lte_max_price"
    # Không so sánh chung giá bán toàn căn với giá thuê tháng (FR-06).
    uses_price = min_price is not None or max_price is not None or "asking_price" in sort
    if uses_price and listing_type is None:
        errors["listing_type"] = "required_for_price_filter_or_sort"
    if province_code and not is_known_province(province_code):
        errors["province_code"] = "unknown_location"
    if ward_code and not (province_code and is_known_location(province_code, ward_code)):
        errors["ward_code"] = "unknown_location"
    if errors:
        raise validation_error(errors)

    rows, total = await listings_repository.public_list_page(
        db,
        page_params,
        sort=sort,
        filters=PublicFilters(
            listing_type=listing_type.value if listing_type else None,
            min_price=min_price,
            max_price=max_price,
            province_code=province_code,
            ward_code=ward_code,
            project_id=project_id,
            min_bedrooms=min_bedrooms,
            q=q,
        ),
    )
    return Page(
        items=[_to_public(row) for row in rows],
        page=page_params.page,
        page_size=page_params.page_size,
        total=total,
    )


async def public_get(db: AsyncSession, *, listing_id: uuid.UUID) -> PublicListingView:
    row = await listings_repository.public_get(db, listing_id)
    if row is None:
        # Tin nháp, bị từ chối, đã đóng hoặc căn vừa được giữ đều trả 404 như
        # nhau, không tiết lộ tin có tồn tại hay không.
        raise resource_not_found()
    return _to_public(row)
