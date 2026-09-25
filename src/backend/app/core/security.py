"""Băm mật khẩu và JWT (SPEC SP-01, PLAN task 2.1).

bcrypt cắt đầu vào ở 72 byte nên mật khẩu được pre-hash bằng SHA-256 trước khi
băm. Nhờ vậy giới hạn 12–128 ký tự của SPEC được hỗ trợ trọn vẹn, không cắt ngầm.

Claims JWT chỉ gồm `sub/exp/iat/auth_version` — không nhúng role/permission vào
token; RBAC luôn được kiểm tra lại theo trạng thái DB hiện tại ở mỗi request
(ARCHITECTURE mục 8 "Authorization"). File này không phụ thuộc FastAPI: lỗi
token được báo bằng exception nội bộ, tầng dependency (app/dependencies.py) mới
map sang AppError/HTTP.
"""

from __future__ import annotations

import base64
import hashlib
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError
from passlib.context import CryptContext

from app.core.config import settings


PASSWORD_MIN_LENGTH = 12
PASSWORD_MAX_LENGTH = 128

_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _prepare(password: str) -> bytes:
    digest = hashlib.sha256(password.encode("utf-8")).digest()
    return base64.b64encode(digest)


def hash_password(password: str) -> str:
    return _context.hash(_prepare(password))


def verify_password(password: str, password_hash: str) -> bool:
    return _context.verify(_prepare(password), password_hash)


def hash_reset_token(token: str) -> str:
    """Hash token reset mật khẩu để tra cứu chính xác (không dùng bcrypt salted)."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class TokenPayload:
    sub: uuid.UUID
    auth_version: int


class TokenError(Exception):
    """Token không giải mã được hoặc sai định dạng claim."""


class TokenExpiredError(TokenError):
    """Token đã hết hạn (`exp` claim ở quá khứ)."""


def create_access_token(user_id: uuid.UUID, auth_version: int) -> str:
    now = datetime.now(UTC)
    claims = {
        "sub": str(user_id),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp()),
        "auth_version": auth_version,
    }
    return jwt.encode(claims, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> TokenPayload:
    try:
        claims = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except ExpiredSignatureError as exc:
        raise TokenExpiredError("Token đã hết hạn") from exc
    except JWTError as exc:
        raise TokenError("Token không hợp lệ") from exc

    try:
        return TokenPayload(
            sub=uuid.UUID(str(claims["sub"])),
            auth_version=int(claims["auth_version"]),
        )
    except (KeyError, ValueError, TypeError) as exc:
        raise TokenError("Token thiếu claim bắt buộc") from exc
