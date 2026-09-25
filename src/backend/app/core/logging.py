"""Structured logging và redaction (PLAN task 2.3).

Đây là lớp phòng thủ thứ hai: code gọi không nên log mật khẩu/token/OTP ngay từ
đầu (ARCHITECTURE mục 8 "Logging"), nhưng `redact` vẫn che các key nhạy cảm nếu
lọt vào `change_summary`/structured `extra=` để giảm rủi ro.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any


_SENSITIVE_KEYS = frozenset(
    {
        "password",
        "password_hash",
        "token",
        "token_hash",
        "access_token",
        "raw_token",
        "otp",
        "otp_hash",
        "secret",
    }
)
_MASK = "***"


def redact(data: Mapping[str, Any] | None) -> dict[str, Any] | None:
    """Che giá trị của các key nhạy cảm, đệ quy vào dict/list con."""
    if data is None:
        return None
    result: dict[str, Any] = {}
    for key, value in data.items():
        if key.lower() in _SENSITIVE_KEYS:
            result[key] = _MASK
        elif isinstance(value, Mapping):
            result[key] = redact(value)
        elif isinstance(value, list):
            result[key] = [redact(item) if isinstance(item, Mapping) else item for item in value]
        else:
            result[key] = value
    return result


class SensitiveDataFilter(logging.Filter):
    """Che các field nhạy cảm trong `record.__dict__` (structured `extra=`)."""

    def filter(self, record: logging.LogRecord) -> bool:
        for key in _SENSITIVE_KEYS:
            if hasattr(record, key):
                setattr(record, key, _MASK)
        return True


def configure_logging(level: str = "INFO") -> None:
    """Cấu hình root logger một lần khi ứng dụng khởi động."""
    root = logging.getLogger()
    if root.handlers:
        return
    handler = logging.StreamHandler()
    handler.addFilter(SensitiveDataFilter())
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    root.addHandler(handler)
    root.setLevel(level)
