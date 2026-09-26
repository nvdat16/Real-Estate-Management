"""Quyền tải tệp private (SPEC SP-06, PLAN task 4.5).

Quyền suy từ `purpose` và quan hệ của tệp, không chỉ từ `uploaded_by`:

- `kyc`: chính khách đã upload, hoặc người có `kyc.read_sensitive`; môi giới chỉ
  thấy trạng thái KYC, không tải được giấy tờ thô (SPEC SP-03);
- `import`: người đã upload, hoặc người có `data.import`;
- tệp hệ thống sinh (`contract_pdf`, `invoice_pdf`, `report`, `data_export`):
  người yêu cầu job sinh ra tệp. Phase 6/7 bổ sung bên hợp đồng/hóa đơn theo
  scope; Phase 8 kiểm tra lại quyền export hiện tại lúc tải.

Tệp chưa `ready`, không tồn tại hay ngoài quyền đều trả 404 như nhau.
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import FilePurpose, FileStatus
from app.core.constants import PermissionCode
from app.core.exceptions import resource_not_found
from app.core.permissions import user_has_permission
from app.modules.files import repository as files_repository
from app.modules.files.repository import FileRow
from app.modules.notifications import repository as notifications_repository
from app.modules.users.repository import UserRow


_UPLOADER_OR_PERMISSION = {
    FilePurpose.KYC: PermissionCode.KYC_READ_SENSITIVE,
    FilePurpose.IMPORT: PermissionCode.DATA_IMPORT,
}


async def _can_download(db: AsyncSession, actor: UserRow, file: FileRow) -> bool:
    permission = _UPLOADER_OR_PERMISSION.get(FilePurpose(file.purpose))
    if permission is not None:
        return file.uploaded_by == actor.id or await user_has_permission(db, actor.id, permission)
    return await notifications_repository.user_requested_job_for_file(
        db, file_id=file.id, user_id=actor.id
    )


async def ensure_can_download(db: AsyncSession, actor: UserRow, file_id: uuid.UUID) -> FileRow:
    file = await files_repository.get_by_id(db, file_id)
    if file is None or file.status != FileStatus.READY:
        raise resource_not_found()
    if not await _can_download(db, actor, file):
        raise resource_not_found()
    return file
