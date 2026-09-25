"""Dependency FastAPI cho auth/RBAC (PLAN task 2.2).

Tách theo mức phụ thuộc FastAPI: những gì cần `Depends`/`Request` sống ở đây;
logic thuần (JWT, kiểm permission qua DB) sống ở `app/core/security.py` và
`app/core/permissions.py` để tái dùng được ngoài context HTTP (ví dụ test).
"""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from typing import Any

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import UserStatus
from app.core.database import get_db
from app.core.exceptions import permission_denied, token_expired, unauthenticated
from app.core.permissions import user_has_permission
from app.core.security import TokenError, TokenExpiredError, decode_access_token
from app.modules.users.models import User


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


async def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        payload = decode_access_token(token)
    except TokenExpiredError as exc:
        raise token_expired() from exc
    except TokenError as exc:
        raise unauthenticated() from exc

    user = await db.get(User, payload.sub)
    if user is None or user.deleted_at is not None or user.status != UserStatus.ACTIVE:
        raise unauthenticated()
    if user.auth_version != payload.auth_version:
        # Phiên đã bị thu hồi (logout/reset mật khẩu/khóa/đổi quyền) — SPEC không
        # có mã riêng cho "revoked", coi như hết hạn để client đăng nhập lại.
        raise token_expired()

    request.state.user = user
    return user


def require_permission(code: str) -> Callable[..., Coroutine[Any, Any, User]]:
    """Dependency factory cho các endpoint gắn cứng một permission (không có
    nhánh self-access/scope — dùng `Depends(get_current_user)` trực tiếp và tự
    rẽ nhánh trong service khi cần, ví dụ hồ sơ customers/agents)."""

    async def _dependency(
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        if not await user_has_permission(db, user.id, code):
            raise permission_denied()
        return user

    return _dependency
