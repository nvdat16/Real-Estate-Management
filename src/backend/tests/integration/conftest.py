"""Fixture riêng cho integration test của Phase 2.

`roles.customer`/`roles.agent` luôn tồn tại trong môi trường thật vì
`scripts/seed.py` seed trước khi ứng dụng chạy. Database test chỉ chạy
migration (không seed), nên `auth.register`/`users.create_agent` sẽ báo lỗi
"vai trò chưa khởi tạo" nếu không có fixture này.
"""

from __future__ import annotations

import pytest_asyncio
from redis.asyncio import from_url as redis_from_url
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from tests.integration import factories as f


@pytest_asyncio.fixture(autouse=True)
async def _base_roles(db_session: AsyncSession) -> None:
    await f.get_or_create_role(db_session, "customer")
    await f.get_or_create_role(db_session, "agent")


@pytest_asyncio.fixture(autouse=True)
async def _flush_rate_limit_redis() -> None:
    """Redis là service thật (không mock), không tự dọn giữa các lần chạy
    pytest như DB test (truncate). Không flush thì bộ đếm `login_email`/
    `reset_email` của một lần chạy trước có thể còn hạn trong cửa sổ 60s/900s
    kế tiếp và làm test rate-limit-theo-email flaky."""
    redis = redis_from_url(settings.REDIS_URL)
    try:
        await redis.flushdb()
    finally:
        await redis.aclose()
