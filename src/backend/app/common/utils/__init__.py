"""Helper nhỏ dùng chung, không thuộc domain cụ thể nào."""

from __future__ import annotations


def expect[T](value: T | None, message: str = "Bản ghi liên quan không tồn tại") -> T:
    """Thu hẹp `T | None` thành `T` khi service đã tự đảm bảo giá trị tồn tại
    (ví dụ ngay sau một scope check vừa xác nhận record có thật). Raise thay
    vì `assert` vì bandit S101/`assert` có thể bị strip bởi `python -O`."""
    if value is None:
        raise RuntimeError(message)
    return value
