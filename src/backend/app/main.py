from fastapi import FastAPI

from app.core.config import settings
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
from app.modules.users.router import router as users_router


API_PREFIX = "/api/v1"

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


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
    }
