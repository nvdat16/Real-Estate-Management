"""Factory tạo bản ghi hợp lệ tối thiểu cho integration test.

Mục đích là dựng nhanh tiền đề để test *vi phạm* một ràng buộc cụ thể, nên mỗi
hàm chỉ điền các trường bắt buộc và trả về đối tượng đã flush.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import (
    ActorType,
    ContractStatus,
    ListingStatus,
    ListingType,
    PartyRole,
    PriceUnit,
)
from app.models import (
    Agent,
    AuditLog,
    Contract,
    ContractParty,
    ContractVersion,
    Customer,
    Listing,
    Permission,
    Project,
    Property,
    Role,
    RolePermission,
    SigningChallenge,
    User,
    UserRole,
)


def _unique(prefix: str) -> str:
    return f"{prefix}{uuid.uuid4().hex[:10]}"


async def make_user(session: AsyncSession, *, email: str | None = None) -> User:
    user = User(
        email=email or f"{_unique('user')}@example.test",
        password_hash="not-a-real-hash",
        full_name="Người dùng kiểm thử",
    )
    session.add(user)
    await session.flush()
    return user


async def make_agent(session: AsyncSession) -> Agent:
    user = await make_user(session)
    agent = Agent(user_id=user.id, agent_code=_unique("MG"))
    session.add(agent)
    await session.flush()
    return agent


async def make_customer(session: AsyncSession) -> Customer:
    user = await make_user(session)
    customer = Customer(user_id=user.id, customer_code=_unique("KH"))
    session.add(customer)
    await session.flush()
    return customer


async def make_project(session: AsyncSession) -> Project:
    project = Project(
        code=_unique("DA"),
        name="Dự án kiểm thử",
        address="Địa chỉ kiểm thử",
        province_code="01",
        ward_code="00004",
    )
    session.add(project)
    await session.flush()
    return project


async def make_property(
    session: AsyncSession,
    *,
    project: Project | None = None,
    unit_code: str | None = None,
) -> Property:
    project = project or await make_project(session)
    item = Property(
        project_id=project.id,
        unit_code=unit_code or _unique("A"),
        area_m2=Decimal("60.00"),
        bedrooms=2,
    )
    session.add(item)
    await session.flush()
    return item


async def make_listing(
    session: AsyncSession,
    *,
    property_obj: Property | None = None,
    agent: Agent | None = None,
    status: ListingStatus = ListingStatus.APPROVED,
    listing_type: ListingType = ListingType.SALE,
    price_unit: PriceUnit | None = None,
    reviewer: User | None = None,
) -> Listing:
    property_obj = property_obj or await make_property(session)
    agent = agent or await make_agent(session)
    needs_review = status in (ListingStatus.APPROVED, ListingStatus.REJECTED)
    reviewer_id = None
    if needs_review:
        reviewer = reviewer or await make_user(session)
        reviewer_id = reviewer.id

    listing = Listing(
        property_id=property_obj.id,
        agent_id=agent.id,
        reviewed_by=reviewer_id,
        reviewed_at=datetime.now(UTC) if needs_review else None,
        listing_type=listing_type.value,
        asking_price=Decimal("2000000000.00"),
        price_unit=(
            price_unit.value
            if price_unit is not None
            else (PriceUnit.TOTAL if listing_type is ListingType.SALE else PriceUnit.MONTH).value
        ),
        title="Tin kiểm thử",
        description="Nội dung kiểm thử",
        status=status.value,
        rejection_reason="Lý do kiểm thử" if status is ListingStatus.REJECTED else None,
    )
    session.add(listing)
    await session.flush()
    return listing


async def make_contract(
    session: AsyncSession,
    *,
    property_obj: Property | None = None,
    agent: Agent | None = None,
    listing: Listing | None = None,
    status: ContractStatus = ContractStatus.DRAFT,
    contract_type: ListingType = ListingType.SALE,
) -> Contract:
    """Tạo hợp đồng kèm tiền đề.

    Truyền `listing` khi cần nhiều hợp đồng trên cùng một căn: nếu để factory tự
    tạo tin mới thì partial unique index của `listings` sẽ chặn trước, không tới
    được ràng buộc của `contracts` mà test muốn kiểm tra.
    """
    if listing is not None:
        agent = agent or await session.get(Agent, listing.agent_id)
        property_obj = property_obj or await session.get(Property, listing.property_id)
    else:
        agent = agent or await make_agent(session)
        property_obj = property_obj or await make_property(session)
        listing = await make_listing(session, property_obj=property_obj, agent=agent)
    assert agent is not None and property_obj is not None
    customer = await make_customer(session)
    creator = await make_user(session)

    contract = Contract(
        contract_no=_unique("HD"),
        listing_id=listing.id,
        property_id=property_obj.id,
        customer_id=customer.id,
        agent_id=agent.id,
        created_by=creator.id,
        contract_type=contract_type.value,
        status=status.value,
        signed_at=datetime.now(UTC) if status is ContractStatus.SIGNED else None,
    )
    session.add(contract)
    await session.flush()
    return contract


async def make_contract_version(
    session: AsyncSession,
    *,
    contract: Contract,
    version_no: int = 1,
    contract_type: str | None = None,
) -> ContractVersion:
    effective_type = contract_type or contract.contract_type
    is_rent = effective_type == ListingType.RENT.value
    creator = await make_user(session)
    version = ContractVersion(
        contract_id=contract.id,
        contract_type=effective_type,
        version_no=version_no,
        content_snapshot={"terms": "Điều khoản kiểm thử"},
        content_hash=uuid.uuid4().hex,
        total_amount=Decimal("2000000000.00"),
        commission_base=Decimal("2000000000.00"),
        commission_rate=Decimal("1.5000"),
        start_date=date(2026, 1, 1) if is_rent else None,
        end_date=date(2027, 1, 1) if is_rent else None,
        created_by=creator.id,
    )
    session.add(version)
    await session.flush()
    return version


async def make_party(
    session: AsyncSession,
    *,
    version: ContractVersion,
    role: PartyRole = PartyRole.CUSTOMER,
    user: User | None = None,
) -> ContractParty:
    user = user or await make_user(session)
    party = ContractParty(
        contract_version_id=version.id,
        user_id=user.id,
        party_role=role.value,
        display_name_snapshot="Bên ký kiểm thử",
    )
    session.add(party)
    await session.flush()
    return party


async def get_or_create_role(session: AsyncSession, code: str) -> Role:
    existing = await session.scalar(select(Role).where(Role.code == code))
    if existing is not None:
        return existing
    role = Role(code=code, name=code)
    session.add(role)
    await session.flush()
    return role


async def get_or_create_permission(session: AsyncSession, code: str) -> Permission:
    existing = await session.scalar(select(Permission).where(Permission.code == code))
    if existing is not None:
        return existing
    permission = Permission(code=code, description=code)
    session.add(permission)
    await session.flush()
    return permission


async def grant_permission(session: AsyncSession, role: Role, permission_code: str) -> None:
    """Idempotent: nhiều actor cùng role trong một test cấp lại cùng permission."""
    permission = await get_or_create_permission(session, permission_code)
    if await session.get(RolePermission, (role.id, permission.id)) is None:
        session.add(RolePermission(role_id=role.id, permission_id=permission.id))
        await session.flush()


async def assign_role(session: AsyncSession, user: User, role_code: str) -> Role:
    role = await get_or_create_role(session, role_code)
    session.add(UserRole(user_id=user.id, role_id=role.id))
    await session.flush()
    return role


async def make_actor(
    session: AsyncSession,
    *,
    role_code: str,
    permission_codes: tuple[str, ...] = (),
    email: str | None = None,
) -> User:
    """Tài khoản kèm role + các permission cụ thể — dùng cho test permission/scope."""
    user = await make_user(session, email=email)
    role = await assign_role(session, user, role_code)
    for code in permission_codes:
        await grant_permission(session, role, code)
    return user


async def make_agent_actor(
    session: AsyncSession, *, permission_codes: tuple[str, ...] = ("listing.manage",)
) -> tuple[User, Agent]:
    """Tài khoản môi giới đăng nhập được: role agent, permission và hồ sơ agent."""
    user = await make_actor(session, role_code="agent", permission_codes=permission_codes)
    agent = Agent(user_id=user.id, agent_code=_unique("MG"))
    session.add(agent)
    await session.flush()
    return user, agent


async def make_audit_log(
    session: AsyncSession,
    *,
    action: str = "test.action",
    entity_type: str = "users",
    entity_id: uuid.UUID | None = None,
    actor_user_id: uuid.UUID | None = None,
) -> AuditLog:
    log = AuditLog(
        actor_user_id=actor_user_id,
        actor_type=(ActorType.USER if actor_user_id else ActorType.SYSTEM).value,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id or uuid.uuid4(),
    )
    session.add(log)
    await session.flush()
    return log


async def make_challenge(session: AsyncSession, *, party: ContractParty) -> SigningChallenge:
    challenge = SigningChallenge(
        party_id=party.id,
        otp_hash=uuid.uuid4().hex,
        content_hash=uuid.uuid4().hex,
        expires_at=datetime.now(UTC) + timedelta(minutes=5),
    )
    session.add(challenge)
    await session.flush()
    return challenge
