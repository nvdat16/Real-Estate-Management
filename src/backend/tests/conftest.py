"""Fixture dùng chung cho unit test và integration test.

Unit test không cần hạ tầng ngoài. Integration test cần một PostgreSQL thật vì
các invariant quan trọng nhất của hệ thống (partial unique index, FK ghép, CHECK)
chỉ tồn tại ở tầng database — xem PLAN task 1.6 và ERD mục 5.

Đặt `TEST_DATABASE_URL` để bật nhóm integration. Nếu biến này trống, các test có
marker `integration` sẽ được bỏ qua thay vì làm đỏ toàn bộ bộ test.
"""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool


BACKEND_ROOT = Path(__file__).resolve().parents[1]

# Settings được khởi tạo lúc import app.core.config, trước khi fixture chạy, nên
# secret cho test phải có sẵn ở thời điểm import conftest.
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-not-for-production")

from app.core.database import get_db  # noqa: E402 - cần JWT_SECRET_KEY đặt trước
from app.middleware import register_exception_handlers  # noqa: E402
from app.modules.agents.router import router as agents_router  # noqa: E402
from app.modules.audit_logs.router import router as audit_logs_router  # noqa: E402
from app.modules.auth.router import me_router  # noqa: E402
from app.modules.auth.router import router as auth_router  # noqa: E402
from app.modules.customers.router import router as customers_router  # noqa: E402
from app.modules.users.router import router as users_router  # noqa: E402


_PHASE_2_ROUTERS = (
    auth_router,
    me_router,
    users_router,
    customers_router,
    agents_router,
    audit_logs_router,
)


def _test_database_url() -> str:
    return os.getenv("TEST_DATABASE_URL", "").strip()


@pytest.fixture(scope="session")
def database_url() -> str:
    url = _test_database_url()
    if not url:
        pytest.skip("TEST_DATABASE_URL chưa được đặt, bỏ qua integration test")
    return url


@pytest.fixture(scope="session")
def migrated_database(database_url: str) -> str:
    """Chạy `alembic upgrade head` một lần cho cả session test.

    Dùng subprocess để đi đúng đường mà môi trường thật dùng, thay vì gọi
    Alembic trong tiến trình test và phải tự xử lý event loop.
    """
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=BACKEND_ROOT,
        env={**os.environ, "DATABASE_URL": database_url},
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        pytest.fail(
            f"alembic upgrade head thất bại:\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return database_url


@pytest_asyncio.fixture
async def db_engine(migrated_database: str) -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(migrated_database, poolclass=NullPool)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    """Một session cho mỗi test, dọn sạch dữ liệu sau khi test kết thúc."""
    factory = async_sessionmaker(bind=db_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        try:
            yield session
        finally:
            await session.rollback()

    async with db_engine.begin() as connection:
        tables = (
            (
                await connection.execute(
                    text(
                        "SELECT tablename FROM pg_tables "
                        "WHERE schemaname = 'public' AND tablename <> 'alembic_version'"
                    )
                )
            )
            .scalars()
            .all()
        )
        if tables:
            joined = ", ".join(f'"{name}"' for name in tables)
            await connection.execute(text(f"TRUNCATE TABLE {joined} RESTART IDENTITY CASCADE"))


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncIterator[httpx.AsyncClient]:
    """Client HTTP cho router Phase 2, KHÔNG dùng `app.main.app` trực tiếp.

    `app.main.app` gắn `RateLimitMiddleware` thật (cần Redis) — dùng nó ở đây
    sẽ làm test đăng nhập/reset liên tiếp trong một session bị chính rate limit
    của chính nó chặn. App test chỉ có exception handler + router, override
    `get_db` để mọi request trong test dùng chung `db_session` (cùng transaction
    với dữ liệu factory đã tạo).
    """
    test_app = FastAPI()
    register_exception_handlers(test_app)
    for router in _PHASE_2_ROUTERS:
        test_app.include_router(router, prefix="/api/v1")
    test_app.dependency_overrides[get_db] = lambda: db_session

    transport = httpx.ASGITransport(app=test_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client


@pytest.fixture(autouse=True)
def _isolated_settings(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Không để test đọc nhầm .env của máy phát triển."""
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-not-for-production")
    yield
