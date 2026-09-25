"""Use case đăng ký/đăng nhập/đăng xuất/reset mật khẩu/hồ sơ cá nhân
(SPEC SP-01, PLAN task 2.4)."""

from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import ActorType, UserStatus
from app.common.utils import expect
from app.core.constants import RoleCode
from app.core.exceptions import (
    duplicate_resource,
    invalid_state,
    reset_token_invalid,
    unauthenticated,
    version_conflict,
)
from app.core.rate_limit import enforce_fixed_window
from app.core.security import (
    create_access_token,
    hash_password,
    hash_reset_token,
    verify_password,
)
from app.modules.audit_logs.service import record_audit
from app.modules.auth import repository as auth_repository
from app.modules.auth.schemas import UserPublic
from app.modules.customers import service as customers_service
from app.modules.roles import repository as roles_repository
from app.modules.users import repository as users_repository
from app.modules.users.models import User


# Hash cố định để `verify_password` luôn tốn thời gian tương đương dù email có
# tồn tại hay không (chặn timing oracle dò tài khoản).
_DUMMY_PASSWORD_HASH = hash_password("dummy-password-for-timing-safety")
_RESET_TOKEN_TTL = timedelta(minutes=15)


def _normalize_email(email: str) -> str:
    return email.strip().lower()


async def register(
    db: AsyncSession, *, email: str, password: str, full_name: str, phone: str | None
) -> User:
    normalized_email = _normalize_email(email)
    role_id = await roles_repository.get_id_by_code(db, RoleCode.CUSTOMER)
    if role_id is None:
        raise invalid_state("Vai trò customer chưa được khởi tạo.")

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
    await customers_service.create_customer_profile(db, user.id)
    await record_audit(
        db, actor=user, action="auth.register", entity_type="users", entity_id=user.id
    )
    await db.commit()
    return user


async def login(db: AsyncSession, *, email: str, password: str) -> str:
    normalized_email = _normalize_email(email)
    await enforce_fixed_window(key=f"login_email:{normalized_email}", limit=5, window_seconds=60)

    user = await users_repository.get_by_email(db, normalized_email)
    password_hash = user.password_hash if user is not None else _DUMMY_PASSWORD_HASH
    password_ok = verify_password(password, password_hash)

    if (
        user is None
        or not password_ok
        or user.deleted_at is not None
        or user.status != UserStatus.ACTIVE
    ):
        # Một thông báo chung cho mọi lý do (không tồn tại/sai mật khẩu/khóa)
        # để không tiết lộ tài khoản có tồn tại hay không (SPEC SP-01).
        raise unauthenticated()

    return create_access_token(user.id, user.auth_version)


async def logout(db: AsyncSession, *, user: User) -> None:
    await users_repository.bump_auth_version(db, user.id)
    await record_audit(db, actor=user, action="auth.logout", entity_type="users", entity_id=user.id)
    await db.commit()


async def request_password_reset(db: AsyncSession, *, email: str) -> None:
    normalized_email = _normalize_email(email)
    await enforce_fixed_window(key=f"reset_email:{normalized_email}", limit=3, window_seconds=900)

    user = await users_repository.get_by_email(db, normalized_email)
    if user is not None:
        await issue_password_reset_token(db, user)
    # Luôn coi như "đã tiếp nhận" bất kể email có tồn tại hay không — router
    # trả cùng message trong mọi trường hợp (SPEC SP-01).


async def issue_password_reset_token(db: AsyncSession, user: User) -> str:
    """Sinh token, lưu hash, thu hồi token cũ; trả token thô.

    API không bao giờ trả token thô cho client — hàm này chỉ được router gọi
    nội bộ để mô phỏng "worker gửi email" (chưa có worker ở Phase 2, xem task
    4.4) và được test integration gọi trực tiếp để lấy token cho bước confirm.
    """
    await auth_repository.invalidate_prior_tokens(db, user.id)
    raw_token = secrets.token_urlsafe(32)
    await auth_repository.create_reset_token(
        db,
        user_id=user.id,
        token_hash=hash_reset_token(raw_token),
        expires_at=datetime.now(UTC) + _RESET_TOKEN_TTL,
    )
    await record_audit(
        db,
        actor=user,
        action="auth.password_reset_requested",
        entity_type="users",
        entity_id=user.id,
    )
    await db.commit()
    return raw_token


async def confirm_password_reset(db: AsyncSession, *, token: str, new_password: str) -> None:
    user_id = await auth_repository.consume_token(db, hash_reset_token(token))
    if user_id is None:
        raise reset_token_invalid()

    # FK đảm bảo user tồn tại khi token còn tham chiếu.
    user = expect(await users_repository.get_by_id(db, user_id))

    await users_repository.set_password_and_revoke(db, user_id, hash_password(new_password))
    await record_audit(
        db,
        actor=user,
        actor_type=ActorType.USER,
        action="auth.password_reset_confirmed",
        entity_type="users",
        entity_id=user_id,
    )
    await db.commit()


async def get_me(db: AsyncSession, *, user: User) -> UserPublic:
    role_codes = await roles_repository.get_codes_for_user(db, user.id)
    return UserPublic(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        status=user.status,
        roles=role_codes,
    )


async def update_me(
    db: AsyncSession,
    *,
    user: User,
    full_name: str,
    phone: str | None,
    expected_row_version: int,
) -> UserPublic:
    ok = await users_repository.update_fields(
        db, user.id, expected_row_version, full_name=full_name.strip(), phone=phone
    )
    if not ok:
        raise version_conflict()
    await db.commit()

    refreshed = expect(await users_repository.get_by_id(db, user.id))
    return await get_me(db, user=refreshed)
