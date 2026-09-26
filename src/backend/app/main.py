import logging

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from redis.asyncio import from_url as redis_from_url
from sqlalchemy import text

from app.core.config import settings
from app.core.database import engine
from app.core.logging import configure_logging
from app.middleware import (
    AuditMiddleware,
    RateLimitMiddleware,
    RequestIDMiddleware,
    register_exception_handlers,
)
from app.modules.agents.router import router as agents_router
from app.modules.audit_logs.router import router as audit_logs_router
from app.modules.auth.router import me_router
from app.modules.auth.router import router as auth_router
from app.modules.customers.router import router as customers_router
from app.modules.files.router import router as files_router
from app.modules.listings.router import public_router as public_listings_router
from app.modules.listings.router import router as listings_router
from app.modules.notifications.router import router as jobs_router
from app.modules.projects.router import public_router as public_catalog_router
from app.modules.projects.router import router as projects_router
from app.modules.properties.router import router as properties_router
from app.modules.users.router import router as users_router


API_PREFIX = "/api/v1"

logger = logging.getLogger(__name__)

configure_logging()

app = FastAPI(
    title="Real Estate Management API",
    version="1.0.0",
)

register_exception_handlers(app)

app.add_middleware(RateLimitMiddleware, redis_url=settings.REDIS_URL)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(AuditMiddleware)

app.include_router(auth_router, prefix=API_PREFIX)
app.include_router(me_router, prefix=API_PREFIX)
app.include_router(users_router, prefix=API_PREFIX)
app.include_router(customers_router, prefix=API_PREFIX)
app.include_router(agents_router, prefix=API_PREFIX)
app.include_router(audit_logs_router, prefix=API_PREFIX)
app.include_router(projects_router, prefix=API_PREFIX)
app.include_router(properties_router, prefix=API_PREFIX)
app.include_router(listings_router, prefix=API_PREFIX)
app.include_router(public_catalog_router, prefix=API_PREFIX)
app.include_router(public_listings_router, prefix=API_PREFIX)
app.include_router(jobs_router, prefix=API_PREFIX)
app.include_router(files_router, prefix=API_PREFIX)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
    }


@app.get("/ready")
async def readiness_check() -> JSONResponse:
    """Readiness (SPEC SP-08): DB và Redis đều phải trả lời; không lộ credential
    hay chi tiết lỗi trong response. Worker có heartbeat riêng qua `jobs`."""
    checks: dict[str, str] = {}
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        logger.warning("Readiness: database không phản hồi")
        checks["database"] = "unavailable"

    redis = redis_from_url(settings.REDIS_URL)
    try:
        await redis.ping()
        checks["redis"] = "ok"
    except Exception:
        logger.warning("Readiness: Redis không phản hồi")
        checks["redis"] = "unavailable"
    finally:
        await redis.aclose()

    ready = all(value == "ok" for value in checks.values())
    return JSONResponse(
        status_code=200 if ready else 503,
        content={"status": "ready" if ready else "unavailable", "checks": checks},
    )
