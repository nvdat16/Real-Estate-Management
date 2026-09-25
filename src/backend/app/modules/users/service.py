"""Use case quản lý tài khoản/role cho Admin (PLAN task 2.5).

Gọi trực tiếp `roles/repository.py` và `customers_service`/`agents_service` —
ngoại lệ có chủ đích cho bảng bridge `user_roles` (không có nghiệp vụ độc lập)
và cho việc kiểm "role customer/agent phải khớp hồ sơ" (ERD mục 4)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import UserStatus
from app.common.schemas.pagination import Page
from app.common.utils import expect
from app.common.utils.pagination import PageParams
from app.core.constants import RoleCode
from app.core.exceptions import (
    duplicate_resource,
    invalid_state,
    resource_not_found,
    validation_error,
    version_conflict,
)
from app.core.security import hash_password
from app.modules.agents import service as agents_service
from app.modules.audit_logs.service import record_audit
from app.modules.customers import service as customers_service
from app.modules.roles import repository as roles_repository
from app.modules.users import repository as users_repository
from app.modules.users.models import User
from app.modules.users.schemas import UserAdminView


def _to_view(user: User, role_codes: list[str]) -> UserAdminView:
    return UserAdminView(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        status=user.status,
        auth_version=user.auth_version,
        row_version=user.row_version,
        roles=role_codes,
    )


async def create_agent(
    db: AsyncSession,
    *,
    actor: User,
    email: str,
    full_name: str,
    phone: str | None,
    password: str,
) -> UserAdminView:
    normalized_email = email.strip().lower()
    role_id = await roles_repository.get_id_by_code(db, RoleCode.AGENT)
    if role_id is None:
        raise invalid_state("Vai trò agent chưa được khởi tạo.")

    try:
        user = await users_repository.create(
            db,
            email=normalized_email,
            password_hash=hash_password(password),
            full_name=full_name.strip(),
            phone=phone,
        )
    except IntegrityError as exc:
        await db.rollback()
        raise duplicate_resource("email") from exc

    await roles_repository.assign(db, user.id, role_id)
    await agents_service.create_agent_profile(db, user.id)
    await record_audit(
        db, actor=actor, action="user.create_agent", entity_type="users", entity_id=user.id
    )
    await db.commit()

    role_codes = await roles_repository.get_codes_for_user(db, user.id)
    return _to_view(user, role_codes)


async def list_users(db: AsyncSession, *, page_params: PageParams) -> Page[UserAdminView]:
    users, total = await users_repository.list_page(db, page_params)
    items = [
        _to_view(user, await roles_repository.get_codes_for_user(db, user.id)) for user in users
    ]
    return Page(items=items, page=page_params.page, page_size=page_params.page_size, total=total)


async def replace_roles(
    db: AsyncSession,
    *,
    actor: User,
    target_id: uuid.UUID,
    role_codes: list[str],
    expected_row_version: int,
) -> UserAdminView:
    target = await users_repository.get_by_id(db, target_id)
    if target is None:
        raise resource_not_found()

    resolved = await roles_repository.get_ids_by_codes(db, role_codes)
    unknown = [code for code in role_codes if code not in resolved]
    if unknown:
        raise validation_error({"role_codes": unknown})

    if RoleCode.CUSTOMER in role_codes and not await customers_service.has_profile(db, target_id):
        raise invalid_state("Cần hồ sơ khách hàng trước khi gán quyền customer.")
    if RoleCode.AGENT in role_codes and not await agents_service.has_profile(db, target_id):
        raise invalid_state("Cần hồ sơ môi giới trước khi gán quyền agent.")

    await roles_repository.replace_for_user(db, target_id, list(resolved.values()))
    ok = await users_repository.update_fields(
        db, target_id, expected_row_version, auth_version=User.auth_version + 1
    )
    if not ok:
        await db.rollback()
        raise version_conflict()

    await record_audit(
        db,
        actor=actor,
        action="user.roles_replace",
        entity_type="users",
        entity_id=target_id,
        change_summary={"role_codes": role_codes},
    )
    await db.commit()

    refreshed = expect(await users_repository.get_by_id(db, target_id))
    role_codes_now = await roles_repository.get_codes_for_user(db, target_id)
    return _to_view(refreshed, role_codes_now)


async def lock(
    db: AsyncSession, *, actor: User, target_id: uuid.UUID, expected_row_version: int
) -> UserAdminView:
    if await users_repository.get_by_id(db, target_id) is None:
        raise resource_not_found()
    ok = await users_repository.update_fields(
        db,
        target_id,
        expected_row_version,
        status=UserStatus.LOCKED.value,
        locked_at=datetime.now(UTC),
        auth_version=User.auth_version + 1,
    )
    if not ok:
        raise version_conflict()
    await record_audit(
        db, actor=actor, action="user.lock", entity_type="users", entity_id=target_id
    )
    await db.commit()

    target = expect(await users_repository.get_by_id(db, target_id))
    role_codes = await roles_repository.get_codes_for_user(db, target_id)
    return _to_view(target, role_codes)


async def unlock(
    db: AsyncSession, *, actor: User, target_id: uuid.UUID, expected_row_version: int
) -> UserAdminView:
    if await users_repository.get_by_id(db, target_id) is None:
        raise resource_not_found()
    ok = await users_repository.update_fields(
        db, target_id, expected_row_version, status=UserStatus.ACTIVE.value, locked_at=None
    )
    if not ok:
        raise version_conflict()
    await record_audit(
        db, actor=actor, action="user.unlock", entity_type="users", entity_id=target_id
    )
    await db.commit()

    target = expect(await users_repository.get_by_id(db, target_id))
    role_codes = await roles_repository.get_codes_for_user(db, target_id)
    return _to_view(target, role_codes)
