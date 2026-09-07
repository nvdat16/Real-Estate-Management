"""Redis-backed fixed-window HTTP rate limiting."""

from __future__ import annotations

import hashlib
import json
import logging
import math
import time
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from redis.asyncio import Redis
from redis.asyncio import from_url as redis_from_url
from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RateLimit:
    requests: int
    window_seconds: int

    def __post_init__(self) -> None:
        if self.requests < 1 or self.window_seconds < 1:
            raise ValueError("Rate-limit values must be positive")


DEFAULT_RATE_LIMIT = RateLimit(100, 60)
DEFAULT_ROUTE_LIMITS: dict[tuple[str, str], RateLimit] = {
    ("POST", "/auth/token"): RateLimit(10, 60),
    ("POST", "/auth/password-reset/request"): RateLimit(20, 900),
}


class RateLimitMiddleware:
    """Limit requests by client IP without storing the raw address in Redis.

    Redis failures fail closed for explicitly sensitive routes and fail open for
    ordinary traffic. Per-account/email limits belong in the auth service where
    normalized identifiers are available without reading request bodies here.
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        redis_url: str | None = None,
        redis: Redis | None = None,
        route_limits: Mapping[tuple[str, str], RateLimit] | None = None,
        default_limit: RateLimit | None = DEFAULT_RATE_LIMIT,
        excluded_paths: Iterable[str] = ("/health", "/docs", "/openapi.json"),
        fail_closed_paths: Iterable[str] | None = None,
        key_prefix: str = "real_estate:rate_limit",
    ) -> None:
        if redis is None and redis_url is None:
            raise ValueError("redis or redis_url is required")
        self.app = app
        self.redis = redis if redis is not None else redis_from_url(
            redis_url, encoding="utf-8", decode_responses=True
        )
        self._owns_redis = redis is None
        self.route_limits = dict(
            DEFAULT_ROUTE_LIMITS if route_limits is None else route_limits
        )
        self.default_limit = default_limit
        self.excluded_paths = frozenset(excluded_paths)
        self.fail_closed_paths = frozenset(
            fail_closed_paths
            if fail_closed_paths is not None
            else (path for _, path in self.route_limits)
        )
        self.key_prefix = key_prefix

    async def __call__(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        if scope["type"] == "lifespan":
            await self._handle_lifespan(scope, receive, send)
            return
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if path in self.excluded_paths:
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "GET").upper()
        limit = self.route_limits.get((method, path), self.default_limit)
        if limit is None:
            await self.app(scope, receive, send)
            return

        try:
            current, retry_after = await self._increment(scope, method, path, limit)
        except Exception:
            logger.exception(
                "Rate-limit backend unavailable",
                extra={"path": path, "method": method},
            )
            if path in self.fail_closed_paths:
                await self._send_error(
                    send,
                    scope,
                    status_code=503,
                    code="DEPENDENCY_UNAVAILABLE",
                    message="Dịch vụ bảo vệ tạm thời không khả dụng.",
                )
                return
            await self.app(scope, receive, send)
            return

        remaining = max(0, limit.requests - current)
        if current > limit.requests:
            await self._send_error(
                send,
                scope,
                status_code=429,
                code="RATE_LIMITED",
                message="Gửi quá nhiều yêu cầu. Vui lòng thử lại sau.",
                retry_after=retry_after,
                limit=limit.requests,
                remaining=0,
            )
            return

        async def add_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.extend(
                    [
                        (b"x-ratelimit-limit", str(limit.requests).encode()),
                        (b"x-ratelimit-remaining", str(remaining).encode()),
                    ]
                )
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, add_headers)

    async def _increment(
        self, scope: Scope, method: str, path: str, limit: RateLimit
    ) -> tuple[int, int]:
        now = int(time.time())
        window = now // limit.window_seconds
        retry_after = max(1, (window + 1) * limit.window_seconds - now)
        client = scope.get("client")
        client_ip = client[0] if client else "unknown"
        identity = hashlib.sha256(client_ip.encode("utf-8")).hexdigest()
        route = hashlib.sha256(f"{method}:{path}".encode()).hexdigest()[:20]
        key = f"{self.key_prefix}:{route}:{identity}:{window}"

        pipeline = self.redis.pipeline(transaction=True)
        pipeline.incr(key)
        pipeline.expire(key, limit.window_seconds + 1)
        result = await pipeline.execute()
        return int(result[0]), retry_after

    async def _send_error(
        self,
        send: Send,
        scope: Scope,
        *,
        status_code: int,
        code: str,
        message: str,
        retry_after: int | None = None,
        limit: int | None = None,
        remaining: int | None = None,
    ) -> None:
        request_id = scope.get("state", {}).get("request_id", "unknown")
        body = json.dumps(
            {
                "error": {"code": code, "message": message},
                "request_id": request_id,
            },
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        headers = [
            (b"content-type", b"application/json; charset=utf-8"),
            (b"content-length", str(len(body)).encode()),
        ]
        if retry_after is not None:
            headers.append((b"retry-after", str(math.ceil(retry_after)).encode()))
        if limit is not None:
            headers.append((b"x-ratelimit-limit", str(limit).encode()))
        if remaining is not None:
            headers.append((b"x-ratelimit-remaining", str(remaining).encode()))
        await send(
            {"type": "http.response.start", "status": status_code, "headers": headers}
        )
        await send({"type": "http.response.body", "body": body})

    async def _handle_lifespan(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        async def close_after_shutdown(message: Message) -> None:
            await send(message)
            if message["type"] == "lifespan.shutdown.complete" and self._owns_redis:
                await self.redis.aclose()

        await self.app(scope, receive, close_after_shutdown)
