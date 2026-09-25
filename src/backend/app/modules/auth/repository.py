"""Truy vấn `password_reset_tokens` — chủ sở hữu: module auth.

SQL trên bảng `users` (đăng ký, cập nhật mật khẩu/`auth_version`...) đi qua
`users/repository.py` — `users` là bảng của module `users`, không phải `auth`.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import PasswordResetToken


async def create_reset_token(
    db: AsyncSession, *, user_id: uuid.UUID, token_hash: str, expires_at: datetime
) -> PasswordResetToken:
    token = PasswordResetToken(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
    db.add(token)
    await db.flush()
    return token


async def invalidate_prior_tokens(db: AsyncSession, user_id: uuid.UUID) -> None:
    await db.execute(
        update(PasswordResetToken)
        .where(
            PasswordResetToken.user_id == user_id,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > func.now(),
        )
        .values(used_at=func.now())
    )


async def consume_token(db: AsyncSession, token_hash: str) -> uuid.UUID | None:
    """Xác nhận + đánh dấu đã dùng trong một câu lệnh atomic, tránh race giữa
    kiểm tra hợp lệ và tiêu thụ token (không có window để dùng lại)."""
    result = await db.execute(
        update(PasswordResetToken)
        .where(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > func.now(),
        )
        .values(used_at=func.now())
        .returning(PasswordResetToken.user_id)
    )
    row = result.first()
    return row[0] if row else None
