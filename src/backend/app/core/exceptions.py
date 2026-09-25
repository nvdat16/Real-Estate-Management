"""Factory tạo `AppError` đúng mã lỗi SPEC §3.2 cho các tình huống service cần
raise trực tiếp (những gì pydantic không tự diễn tả được).

Lỗi validate schema thông thường vẫn đi qua `validation_error_handler` sẵn có
(RequestValidationError) — các hàm ở đây chỉ dùng cho business-level check.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.middleware.error_handler import AppError


def unauthenticated(message: str = "Sai thông tin đăng nhập.") -> AppError:
    return AppError("UNAUTHENTICATED", message, status_code=401)


def token_expired() -> AppError:
    return AppError("TOKEN_EXPIRED", "Token đã hết hạn, vui lòng đăng nhập lại.", status_code=401)


def permission_denied() -> AppError:
    return AppError(
        "PERMISSION_DENIED", "Bạn không có quyền thực hiện hành động này.", status_code=403
    )


def resource_not_found() -> AppError:
    return AppError("RESOURCE_NOT_FOUND", "Không tìm thấy tài nguyên.", status_code=404)


def version_conflict(field: str = "row_version") -> AppError:
    return AppError(
        "VERSION_CONFLICT",
        "Dữ liệu đã thay đổi. Vui lòng tải lại trước khi lưu.",
        status_code=409,
        details={"field": field},
    )


def duplicate_resource(field: str | None = None) -> AppError:
    details = {"field": field} if field else None
    return AppError("DUPLICATE_RESOURCE", "Dữ liệu đã tồn tại.", status_code=409, details=details)


def invalid_state(message: str) -> AppError:
    return AppError("INVALID_STATE", message, status_code=409)


def reset_token_invalid() -> AppError:
    return AppError(
        "RESET_TOKEN_INVALID",
        "Liên kết đặt lại mật khẩu không hợp lệ hoặc đã được dùng.",
        status_code=422,
    )


def validation_error(details: Mapping[str, Any] | list[Any] | None = None) -> AppError:
    return AppError(
        "VALIDATION_ERROR", "Dữ liệu đầu vào không hợp lệ.", status_code=422, details=details
    )


def rate_limited(retry_after: int | None = None) -> AppError:
    headers = {"Retry-After": str(retry_after)} if retry_after is not None else None
    return AppError(
        "RATE_LIMITED",
        "Gửi quá nhiều yêu cầu. Vui lòng thử lại sau.",
        status_code=429,
        headers=headers,
    )


def dependency_unavailable() -> AppError:
    return AppError(
        "DEPENDENCY_UNAVAILABLE",
        "Dịch vụ tạm thời không khả dụng.",
        status_code=503,
    )
