"""Request correlation support.

The request id is deliberately kept in both ``request.state`` and a context
variable.  The former is convenient in handlers while the latter lets code
that does not have a Request object (for example a log formatter) access it.
"""

from __future__ import annotations

import re
import uuid
from contextvars import ContextVar, Token

from starlette.types import ASGIApp, Message, Receive, Scope, Send

REQUEST_ID_HEADER = b"x-request-id"
MAX_REQUEST_ID_LENGTH = 128
_SAFE_REQUEST_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")

request_id_context: ContextVar[str | None] = ContextVar(
    "request_id", default=None
)


def get_request_id() -> str | None:
    """Return the id of the current request, if called in a request context."""

    return request_id_context.get()


def _new_request_id() -> str:
    return f"req-{uuid.uuid4().hex}"


def _request_id_from_headers(scope: Scope) -> str:
    for name, value in scope.get("headers", []):
        if name.lower() != REQUEST_ID_HEADER:
            continue
        try:
            candidate = value.decode("ascii")
        except UnicodeDecodeError:
            break
        if (
            len(candidate) <= MAX_REQUEST_ID_LENGTH
            and _SAFE_REQUEST_ID.fullmatch(candidate)
        ):
            return candidate
        break
    return _new_request_id()


class RequestIDMiddleware:
    """Attach a safe correlation id to every HTTP request and response.

    A caller supplied id is retained only when it contains log-safe ASCII
    characters. Invalid values are replaced instead of returning an error so
    observability metadata can never make an otherwise valid request fail.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = _request_id_from_headers(scope)
        scope.setdefault("state", {})["request_id"] = request_id
        token: Token[str | None] = request_id_context.set(request_id)

        async def send_with_request_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers = [
                    (name, value)
                    for name, value in headers
                    if name.lower() != REQUEST_ID_HEADER
                ]
                headers.append((REQUEST_ID_HEADER, request_id.encode("ascii")))
                message["headers"] = headers
            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        finally:
            request_id_context.reset(token)
