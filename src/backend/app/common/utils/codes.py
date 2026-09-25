"""Sinh mã hồ sơ ngắn (customer_code/agent_code) cho tài khoản tạo mới.

Không có định dạng nào được PLAN/SPEC/ERD quy định cho hồ sơ tạo ngoài seed
(seed dùng dãy tuần tự KH00001/MG0001 riêng) — dùng hex ngẫu nhiên và để caller
retry khi trùng UNIQUE, thay vì đoán một định dạng tuần tự có thể đụng seed.
"""

from __future__ import annotations

import secrets


def generate_code(prefix: str) -> str:
    return f"{prefix}{secrets.token_hex(4).upper()}"
