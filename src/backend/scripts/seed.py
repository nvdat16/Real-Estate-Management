"""Seed dữ liệu mẫu (PLAN task 1.5).

Tạo RBAC, ba tài khoản demo theo NFR-06 và ít nhất 2.000 bản ghi nghiệp vụ để đo
hiệu năng theo NFR-04.

    python scripts/seed.py            # bỏ qua nếu đã seed
    python scripts/seed.py --reset    # xóa dữ liệu nghiệp vụ rồi seed lại

Dữ liệu là giả lập, sinh từ seed random cố định nên hai lần chạy cho cùng kết quả.
Script tôn trọng các invariant ở database: mỗi căn chỉ có một tin pending/approved,
mã căn duy nhất trong dự án, cặp sale/total và rent/month.
"""

from __future__ import annotations

import argparse
import asyncio
import random
import sys
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import insert, select, text

from app.common.enums import (
    AgentStatus,
    ListingStatus,
    ListingType,
    PriceUnit,
    ProjectStatus,
    PropertyStatus,
    UserStatus,
)
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models import (
    Agent,
    Customer,
    Listing,
    Permission,
    Project,
    Property,
    Role,
    RolePermission,
    User,
    UserRole,
)


DEMO_PASSWORD = "Demo@12345678"  # noqa: S105 - mật khẩu tài khoản demo, không phải secret

COUNT_AGENTS = 10
COUNT_CUSTOMERS = 200
COUNT_PROJECTS = 20
COUNT_PROPERTIES = 1_200
COUNT_PUBLIC_LISTINGS = 800
COUNT_DRAFT_LISTINGS = 100

# Danh mục địa bàn tối giản cho dữ liệu mẫu; danh mục thật được cấu hình riêng
# theo ERD mục 4 (không hardcode một hệ thống mã trong tài liệu nghiệp vụ).
LOCATIONS = [
    ("01", "00004", "Hà Nội", "Ba Đình"),
    ("01", "00008", "Hà Nội", "Hoàn Kiếm"),
    ("79", "26734", "TP Hồ Chí Minh", "Quận 1"),
    ("79", "26746", "TP Hồ Chí Minh", "Quận 3"),
    ("48", "20194", "Đà Nẵng", "Hải Châu"),
    ("31", "11317", "Hải Phòng", "Hồng Bàng"),
]

PERMISSIONS: list[tuple[str, str]] = [
    ("project.manage", "CRUD dự án"),
    ("property.manage", "CRUD căn hộ"),
    ("listing.manage", "Tạo và sửa tin phụ trách"),
    ("listing.approve", "Duyệt hoặc từ chối tin"),
    ("customer.read_scope", "Xem khách trong phạm vi giao dịch"),
    ("kyc.read_sensitive", "Xem dữ liệu định danh của khách"),
    ("contract.manage", "Lập, gửi ký và hủy hợp đồng"),
    ("contract.sign_representative", "Ký hợp đồng với tư cách đại diện đơn vị"),
    ("invoice.manage", "Tạo, phát hành và ghi nhận thanh toán hóa đơn"),
    ("commission.read_own", "Xem hoa hồng của mình"),
    ("commission.approve", "Duyệt khoản hoa hồng"),
    ("commission.pay", "Ghi nhận chi hoa hồng"),
    ("report.read_all", "Xem dashboard toàn hệ thống"),
    ("report.read_scope", "Xem báo cáo trong phạm vi phụ trách"),
    ("data.import", "Nhập dữ liệu Excel/CSV"),
    ("data.export", "Xuất dữ liệu theo phạm vi"),
    ("audit.read", "Tra cứu audit log"),
    ("user.manage", "Quản lý tài khoản và vai trò"),
]

ROLE_PERMISSIONS: dict[str, list[str]] = {
    "admin": [code for code, _ in PERMISSIONS],
    "agent": [
        "listing.manage",
        "customer.read_scope",
        "contract.manage",
        "commission.read_own",
        "report.read_scope",
        "data.export",
    ],
    "customer": ["data.export"],
}

BUSINESS_TABLES = [
    "commissions",
    "invoices",
    "contract_signatures",
    "signing_challenges",
    "contract_parties",
    "contract_versions",
    "contracts",
    "listings",
    "properties",
    "projects",
    "kyc_verifications",
    "email_deliveries",
    "outbox_events",
    "jobs",
    "audit_logs",
    "password_reset_tokens",
    "files",
    "customers",
    "agents",
    "user_roles",
    "role_permissions",
    "permissions",
    "roles",
    "users",
]


def _now() -> datetime:
    return datetime.now(UTC)


async def _already_seeded(session) -> bool:
    existing = await session.scalar(select(User.id).where(User.email == "admin@demo.local"))
    return existing is not None


async def _reset(session) -> None:
    joined = ", ".join(f'"{name}"' for name in BUSINESS_TABLES)
    await session.execute(text(f"TRUNCATE TABLE {joined} RESTART IDENTITY CASCADE"))
    await session.commit()
    print("Đã xóa dữ liệu nghiệp vụ cũ")


async def _seed_rbac(session) -> dict[str, uuid.UUID]:
    role_ids = {code: uuid.uuid4() for code in ("admin", "agent", "customer")}
    await session.execute(
        insert(Role),
        [
            {"id": role_ids["admin"], "code": "admin", "name": "Quản trị viên"},
            {"id": role_ids["agent"], "code": "agent", "name": "Môi giới"},
            {"id": role_ids["customer"], "code": "customer", "name": "Khách hàng"},
        ],
    )

    permission_ids = {code: uuid.uuid4() for code, _ in PERMISSIONS}
    await session.execute(
        insert(Permission),
        [
            {"id": permission_ids[code], "code": code, "description": description}
            for code, description in PERMISSIONS
        ],
    )

    await session.execute(
        insert(RolePermission),
        [
            {"role_id": role_ids[role_code], "permission_id": permission_ids[code]}
            for role_code, codes in ROLE_PERMISSIONS.items()
            for code in codes
        ],
    )
    return role_ids


def _user_row(email: str, full_name: str, phone: str) -> dict:
    return {
        "id": uuid.uuid4(),
        "email": email,
        "password_hash": hash_password(DEMO_PASSWORD),
        "full_name": full_name,
        "phone": phone,
        "status": UserStatus.ACTIVE.value,
    }


async def _seed_people(session, role_ids: dict[str, uuid.UUID]) -> tuple[list[uuid.UUID], int]:
    """Tạo admin demo, môi giới và khách hàng. Trả về danh sách agent_id."""
    shared_hash = hash_password(DEMO_PASSWORD)

    admin = _user_row("admin@demo.local", "Nguyễn Quản Trị", "0900000001")
    agent_demo = _user_row("agent@demo.local", "Trần Môi Giới", "0900000002")
    customer_demo = _user_row("customer@demo.local", "Lê Khách Hàng", "0900000003")

    user_rows = [admin, agent_demo, customer_demo]
    agent_users = [agent_demo]
    customer_users = [customer_demo]

    for index in range(1, COUNT_AGENTS):
        agent_users.append(
            {
                "id": uuid.uuid4(),
                "email": f"agent{index:02d}@demo.local",
                "password_hash": shared_hash,
                "full_name": f"Môi giới {index:02d}",
                "phone": f"09010{index:05d}",
                "status": UserStatus.ACTIVE.value,
            }
        )
    for index in range(1, COUNT_CUSTOMERS):
        customer_users.append(
            {
                "id": uuid.uuid4(),
                "email": f"customer{index:03d}@demo.local",
                "password_hash": shared_hash,
                "full_name": f"Khách hàng {index:03d}",
                "phone": f"09020{index:05d}",
                "status": UserStatus.ACTIVE.value,
            }
        )

    user_rows.extend(agent_users[1:])
    user_rows.extend(customer_users[1:])
    await session.execute(insert(User), user_rows)

    await session.execute(
        insert(UserRole),
        [{"user_id": admin["id"], "role_id": role_ids["admin"]}]
        + [{"user_id": row["id"], "role_id": role_ids["agent"]} for row in agent_users]
        + [{"user_id": row["id"], "role_id": role_ids["customer"]} for row in customer_users],
    )

    agent_ids = [uuid.uuid4() for _ in agent_users]
    await session.execute(
        insert(Agent),
        [
            {
                "id": agent_ids[index],
                "user_id": row["id"],
                "agent_code": f"MG{index + 1:04d}",
                "status": AgentStatus.ACTIVE.value,
            }
            for index, row in enumerate(agent_users)
        ],
    )

    await session.execute(
        insert(Customer),
        [
            {
                "id": uuid.uuid4(),
                "user_id": row["id"],
                "customer_code": f"KH{index + 1:05d}",
                "address": f"Số {index + 1} đường Mẫu, Phường Mẫu",
            }
            for index, row in enumerate(customer_users)
        ],
    )

    return agent_ids, len(user_rows)


async def _seed_catalog(session, rng: random.Random) -> list[uuid.UUID]:
    project_rows = []
    for index in range(COUNT_PROJECTS):
        province_code, ward_code, province_name, ward_name = LOCATIONS[index % len(LOCATIONS)]
        project_rows.append(
            {
                "id": uuid.uuid4(),
                "code": f"DA{index + 1:03d}",
                "name": f"Dự án {ward_name} {index + 1:02d}",
                "address": f"Lô {index + 1}, {ward_name}, {province_name}",
                "province_code": province_code,
                "ward_code": ward_code,
                "description": "Dữ liệu mẫu phục vụ demo và đo hiệu năng",
                "status": ProjectStatus.ACTIVE.value,
            }
        )
    await session.execute(insert(Project), project_rows)

    property_rows = []
    for index in range(COUNT_PROPERTIES):
        project = project_rows[index % COUNT_PROJECTS]
        floor = index % 25 + 1
        property_rows.append(
            {
                "id": uuid.uuid4(),
                "project_id": project["id"],
                "unit_code": f"{floor:02d}-{index // COUNT_PROJECTS + 1:03d}",
                "area_m2": Decimal(str(rng.choice([45.5, 62.0, 78.5, 95.0, 120.5]))),
                "bedrooms": rng.choice([1, 2, 2, 3, 3, 4]),
                "floor": floor,
                "description": "Căn hộ mẫu",
                "status": PropertyStatus.AVAILABLE.value,
            }
        )
    await session.execute(insert(Property), property_rows)
    return [row["id"] for row in property_rows]


async def _seed_listings(
    session,
    rng: random.Random,
    property_ids: list[uuid.UUID],
    agent_ids: list[uuid.UUID],
    admin_user_id: uuid.UUID,
) -> int:
    rows = []
    now = _now()

    # Tin pending/approved phải nằm trên các căn khác nhau (partial unique index).
    for index in range(COUNT_PUBLIC_LISTINGS):
        property_id = property_ids[index]
        is_rent = index % 4 == 0
        status = ListingStatus.APPROVED if index % 5 else ListingStatus.PENDING
        price = (
            Decimal(rng.randrange(8, 40)) * Decimal("1000000")
            if is_rent
            else Decimal(rng.randrange(1_200, 9_000)) * Decimal("1000000")
        )
        rows.append(
            {
                "id": uuid.uuid4(),
                "property_id": property_id,
                "agent_id": agent_ids[index % len(agent_ids)],
                "reviewed_by": admin_user_id if status is ListingStatus.APPROVED else None,
                "reviewed_at": now - timedelta(days=index % 30)
                if status is ListingStatus.APPROVED
                else None,
                "listing_type": (ListingType.RENT if is_rent else ListingType.SALE).value,
                "asking_price": price,
                "price_unit": (PriceUnit.MONTH if is_rent else PriceUnit.TOTAL).value,
                "title": f"{'Cho thuê' if is_rent else 'Bán'} căn hộ mẫu {index + 1:04d}",
                "description": "Nội dung tin mẫu dùng cho demo, tìm kiếm và đo hiệu năng.",
                "status": status.value,
                "created_at": now - timedelta(days=index % 60, hours=index % 24),
            }
        )

    # Bản nháp có thể trùng căn, dùng để kiểm tra bộ lọc và quyền.
    for index in range(COUNT_DRAFT_LISTINGS):
        property_id = property_ids[index % len(property_ids)]
        rows.append(
            {
                "id": uuid.uuid4(),
                "property_id": property_id,
                "agent_id": agent_ids[index % len(agent_ids)],
                "reviewed_by": None,
                "reviewed_at": None,
                "listing_type": ListingType.SALE.value,
                "asking_price": Decimal(rng.randrange(1_200, 9_000)) * Decimal("1000000"),
                "price_unit": PriceUnit.TOTAL.value,
                "title": f"Bản nháp tin {index + 1:03d}",
                "description": "Bản nháp chưa gửi duyệt.",
                "status": ListingStatus.DRAFT.value,
                "created_at": now - timedelta(days=index % 15),
            }
        )

    await session.execute(insert(Listing), rows)
    return len(rows)


async def _count_rows(session) -> int:
    total = 0
    for table in BUSINESS_TABLES:
        # Tên bảng lấy từ BUSINESS_TABLES, không phải dữ liệu từ bên ngoài.
        total += await session.scalar(text(f'SELECT count(*) FROM "{table}"')) or 0  # noqa: S608
    return total


async def seed(reset: bool) -> None:
    rng = random.Random(20260917)

    async with SessionLocal() as session:
        if reset:
            await _reset(session)
        elif await _already_seeded(session):
            print("Dữ liệu đã được seed trước đó. Dùng --reset để seed lại.")
            return

        role_ids = await _seed_rbac(session)
        agent_ids, user_count = await _seed_people(session, role_ids)
        admin_user_id = await session.scalar(
            select(User.id).where(User.email == "admin@demo.local")
        )
        property_ids = await _seed_catalog(session, rng)
        listing_count = await _seed_listings(session, rng, property_ids, agent_ids, admin_user_id)
        await session.commit()

        total = await _count_rows(session)

    print(
        "Seed xong:\n"
        f"  tài khoản        : {user_count}\n"
        f"  môi giới         : {len(agent_ids)}\n"
        f"  khách hàng       : {COUNT_CUSTOMERS}\n"
        f"  dự án            : {COUNT_PROJECTS}\n"
        f"  căn hộ           : {len(property_ids)}\n"
        f"  tin đăng         : {listing_count}\n"
        f"  tổng bản ghi     : {total}\n"
        f"Tài khoản demo (mật khẩu {DEMO_PASSWORD}):\n"
        "  admin@demo.local / agent@demo.local / customer@demo.local"
    )
    if total < 2000:
        raise SystemExit(f"Chỉ có {total} bản ghi, yêu cầu tối thiểu 2.000 theo NFR-06")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed dữ liệu mẫu")
    parser.add_argument("--reset", action="store_true", help="Xóa dữ liệu nghiệp vụ rồi seed lại")
    args = parser.parse_args()
    asyncio.run(seed(reset=args.reset))


if __name__ == "__main__":
    main()
