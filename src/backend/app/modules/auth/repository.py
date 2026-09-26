"""Truy vấn `password_reset_tokens` — chủ sở hữu: module auth. SQL tay (ADR-011).

SQL trên bảng `users` (đăng ký, cập nhật mật khẩu/`auth_version`...) đi qua
`users/repository.py` — `users` là bảng của module `users`, không phải `auth`.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.common import db as sql


async def create_reset_token(
    db: AsyncSession, *, user_id: uuid.UUID, token_hash: str, expires_at: datetime
) -> None:
    await sql.execute(
        db,
        """
        INSERT INTO password_reset_tokens (user_id, token_hash, expires_at)
        VALUES (:user_id, :token_hash, :expires_at)
        """,
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
    )


async def invalidate_prior_tokens(db: AsyncSession, user_id: uuid.UUID) -> None:
    await sql.execute(
        db,
        """
        UPDATE password_reset_tokens SET used_at = now(), updated_at = now()
        WHERE user_id = :user_id AND used_at IS NULL AND expires_at > now()
        """,
        user_id=user_id,
    )


async def consume_token(db: AsyncSession, token_hash: str) -> uuid.UUID | None:
    """Xác nhận + đánh dấu đã dùng trong một câu lệnh atomic, tránh race giữa
    kiểm tra hợp lệ và tiêu thụ token (không có window để dùng lại)."""
    user_id = await sql.scalar(
        db,
        """
        UPDATE password_reset_tokens SET used_at = now(), updated_at = now()
        WHERE token_hash = :token_hash AND used_at IS NULL AND expires_at > now()
        RETURNING user_id
        """,
        token_hash=token_hash,
    )
    return user_id if isinstance(user_id, uuid.UUID) else None
