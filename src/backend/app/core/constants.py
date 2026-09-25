"""Hằng số mã role/permission khớp `scripts/seed.py` (PLAN task 2.2).

Role/permission là dữ liệu DB (bảng `roles`/`permissions`), không phải enum
type — các class dưới đây chỉ là hằng chuỗi tránh gõ nhầm trong code Phase 2,
không phải nguồn sự thật (nguồn sự thật là `scripts/seed.py::PERMISSIONS`).
"""

from __future__ import annotations


class RoleCode:
    ADMIN = "admin"
    AGENT = "agent"
    CUSTOMER = "customer"


class PermissionCode:
    USER_MANAGE = "user.manage"
    CUSTOMER_READ_SCOPE = "customer.read_scope"
    AUDIT_READ = "audit.read"
