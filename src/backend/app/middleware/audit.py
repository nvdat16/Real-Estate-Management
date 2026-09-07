"""Sanitized HTTP access audit logging.

Business audit records must still be written by services in the same database
transaction as the change. This middleware covers request-level operational
and security traceability only.
"""

from __future__ import annotations

import logging
import time

from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = logging.getLogger("app.audit")


def _clean(value: str | None, max_length: int) -> str | None:
    if value is None:
        return None
    return value.replace("\r", " ").replace("\n", " ")[:max_length]


class AuditMiddleware:
    """Emit one body-free structured log record for each HTTP request."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        started = time.perf_counter()
        status_code = 500

        async def capture_status(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, capture_status)
        finally:
            state = scope.get("state", {})
            route = scope.get("route")
            # A route template avoids logging identifiers embedded in URLs.
            path = getattr(route, "path", None) or scope.get("path", "")
            client = scope.get("client")
            headers = dict(scope.get("headers", []))
            user = state.get("user")
            actor_id = (
                getattr(user, "id", None)
                or state.get("user_id")
                or state.get("actor_id")
            )
            logger.info(
                "HTTP request completed",
                extra={
                    "audit_event": "http_request",
                    "request_id": state.get("request_id"),
                    "method": scope.get("method"),
                    "path": _clean(str(path), 500),
                    "status_code": status_code,
                    "duration_ms": round(
                        (time.perf_counter() - started) * 1000, 2
                    ),
                    "client_ip": client[0] if client else None,
                    "actor_id": str(actor_id) if actor_id is not None else None,
                    "user_agent": _clean(
                        headers.get(b"user-agent", b"").decode(
                            "utf-8", errors="replace"
                        ),
                        300,
                    ),
                },
            )
