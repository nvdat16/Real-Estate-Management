"""Quyền đọc danh mục dự án/căn hộ (SPEC §11: "Admin ghi; môi giới đọc").

Ghi danh mục gắn cứng `project.manage`/`property.manage` ở router. Đọc thì
người quản lý danh mục hoặc người lập tin (`listing.manage`) đều cần thấy dự án
và căn để chọn khi tạo tin; khách hàng xem danh mục qua API công khai.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import PermissionCode
from app.core.exceptions import permission_denied
from app.core.permissions import user_has_permission
from app.modules.users.models import User


_CATALOG_READ_PERMISSIONS = (
    PermissionCode.PROJECT_MANAGE,
    PermissionCode.PROPERTY_MANAGE,
    PermissionCode.LISTING_MANAGE,
)


async def ensure_catalog_reader(db: AsyncSession, actor: User) -> None:
    for code in _CATALOG_READ_PERMISSIONS:
        if await user_has_permission(db, actor.id, code):
            return
    raise permission_denied()
