from fastapi import FastAPI

from app.core.config import settings
from app.middleware import (
    AuditMiddleware,
    RateLimitMiddleware,
    RequestIDMiddleware,
    register_exception_handlers,
)

app = FastAPI(
    title="Real Estate Management API",
    version="1.0.0",
)

register_exception_handlers(app)

app.add_middleware(RateLimitMiddleware, redis_url=settings.REDIS_URL)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(AuditMiddleware)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
    }
