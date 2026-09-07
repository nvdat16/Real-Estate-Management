"""Application-wide JSON error responses."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.middleware.request_id import get_request_id

logger = logging.getLogger(__name__)


class AppError(Exception):
    """A safe, intentional API error raised by application services."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        status_code: int = 400,
        details: Mapping[str, Any] | list[Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
        self.headers = dict(headers or {})


_HTTP_ERROR_CODES = {
    400: "BAD_REQUEST",
    401: "UNAUTHENTICATED",
    403: "PERMISSION_DENIED",
    404: "RESOURCE_NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    413: "PAYLOAD_TOO_LARGE",
    415: "UNSUPPORTED_MEDIA_TYPE",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMITED",
    503: "DEPENDENCY_UNAVAILABLE",
}


def _request_id(request: Request) -> str:
    state_request_id = getattr(request.state, "request_id", None)
    return state_request_id or get_request_id() or "unknown"


def error_response(
    request: Request,
    *,
    status_code: int,
    code: str,
    message: str,
    details: Mapping[str, Any] | list[Any] | None = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    error: dict[str, Any] = {"code": code, "message": message}
    if details is not None:
        error["details"] = details
    return JSONResponse(
        status_code=status_code,
        content={"error": error, "request_id": _request_id(request)},
        headers=dict(headers or {}),
    )


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return error_response(
        request,
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
        details=exc.details,
        headers=exc.headers,
    )


async def http_error_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    detail = exc.detail
    code = _HTTP_ERROR_CODES.get(exc.status_code, "HTTP_ERROR")
    details = None
    if isinstance(detail, Mapping):
        code = str(detail.get("code", code))
        message = str(detail.get("message", "Yêu cầu không thể xử lý."))
        candidate_details = detail.get("details")
        if isinstance(candidate_details, (Mapping, list)):
            details = candidate_details
    else:
        message = (
            detail if isinstance(detail, str) else "Yêu cầu không thể xử lý."
        )
    return error_response(
        request,
        status_code=exc.status_code,
        code=code,
        message=message,
        details=details,
        headers=exc.headers,
    )


async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    # Do not include ``input`` from Pydantic's errors: it can contain a
    # password, token, OTP, or raw identity data.
    details = [
        {
            "location": [str(part) for part in error.get("loc", ())],
            "message": error.get("msg", "Invalid value"),
            "type": error.get("type", "value_error"),
        }
        for error in exc.errors()
    ]
    return error_response(
        request,
        status_code=422,
        code="VALIDATION_ERROR",
        message="Dữ liệu đầu vào không hợp lệ.",
        details=details,
    )


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(
        "Unhandled request error",
        extra={"request_id": _request_id(request)},
    )
    return error_response(
        request,
        status_code=500,
        code="INTERNAL_SERVER_ERROR",
        message="Đã xảy ra lỗi hệ thống.",
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register handlers in one place so the response contract stays stable."""

    app.add_exception_handler(AppError, app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(
        RequestValidationError,
        validation_error_handler,  # type: ignore[arg-type]
    )
    app.add_exception_handler(
        HTTPException,
        http_error_handler,  # type: ignore[arg-type]
    )
    app.add_exception_handler(
        StarletteHTTPException,
        http_error_handler,  # type: ignore[arg-type]
    )
    app.add_exception_handler(Exception, unhandled_error_handler)
