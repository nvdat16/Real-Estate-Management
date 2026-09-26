"""Upload và tải tệp private (SPEC SP-06, PLAN task 4.5).

Thứ tự upload: kiểm tra quyền và nội dung → ghi kho → insert `files` ready +
audit trong một transaction. Không có bản ghi nào trỏ tới tệp ghi dở; nếu insert
lỗi sau khi đã ghi kho thì xóa tệp mồ côi (best effort). Gọi kho tệp qua
`asyncio.to_thread` vì adapter là I/O đồng bộ.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import uuid
from datetime import UTC, datetime
from typing import NoReturn

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import FilePurpose
from app.common.utils.file import (
    EXTENSIONS,
    MIME_CSV,
    MIME_XLSX,
    extension_of,
    is_safe_xlsx,
    is_utf8_csv,
    sanitize_filename,
    sniff_image_or_pdf,
)
from app.core.constants import PermissionCode
from app.core.exceptions import dependency_unavailable, permission_denied, validation_error
from app.core.permissions import user_has_permission
from app.integrations.file_storage.service import FileStorage, StorageError
from app.modules.audit_logs.service import record_audit
from app.modules.customers import repository as customers_repository
from app.modules.files import repository as files_repository
from app.modules.files.permissions import ensure_can_download
from app.modules.files.repository import FileRow
from app.modules.files.schemas import FileView
from app.modules.users.repository import UserRow


logger = logging.getLogger(__name__)

MAX_UPLOAD_BYTES = 10 * 1024 * 1024


def to_view(file: FileRow) -> FileView:
    return FileView.model_validate(file, from_attributes=True)


def _reject(reason: str, **details: object) -> NoReturn:
    raise validation_error({"field": "file", "reason": reason, **details})


async def _ensure_can_upload(db: AsyncSession, actor: UserRow, purpose: FilePurpose) -> None:
    if purpose == FilePurpose.KYC:
        # Giấy tờ KYC là của khách hàng: phải có hồ sơ customer (SPEC SP-03).
        customer = await customers_repository.get_by_user_id(db, actor.id)
        if customer is None or customer.deleted_at is not None:
            raise permission_denied()
    elif not await user_has_permission(db, actor.id, PermissionCode.DATA_IMPORT):
        raise permission_denied()


def _detect_mime(purpose: FilePurpose, filename: str | None, data: bytes) -> str:
    if purpose == FilePurpose.KYC:
        mime = sniff_image_or_pdf(data)
        if mime is None:
            _reject("unsupported_type", allowed=["jpeg", "png", "pdf"])
        return mime

    extension = extension_of(filename)
    if extension == ".xlsx" and is_safe_xlsx(data):
        return MIME_XLSX
    if extension == ".csv" and is_utf8_csv(data):
        return MIME_CSV
    # .xlsm, macro, external link, CSV không phải UTF-8 hoặc nội dung không khớp đuôi.
    _reject("unsupported_type", allowed=["xlsx", "csv"])


async def upload(
    db: AsyncSession,
    *,
    actor: UserRow,
    purpose: FilePurpose,
    filename: str | None,
    data: bytes,
    storage: FileStorage,
) -> FileView:
    await _ensure_can_upload(db, actor, purpose)
    if not data:
        _reject("empty")
    if len(data) > MAX_UPLOAD_BYTES:
        _reject("too_large", max_bytes=MAX_UPLOAD_BYTES)
    mime_type = _detect_mime(purpose, filename, data)

    # Tên lưu do server sinh, không ghép từ tên tệp client gửi (SPEC SP-06).
    storage_key = f"{purpose.value}/{datetime.now(UTC):%Y/%m}/{uuid.uuid4().hex}"
    try:
        await asyncio.to_thread(storage.save, storage_key, data)
    except StorageError as exc:
        logger.error("Ghi kho tệp thất bại", extra={"purpose": purpose.value})
        raise dependency_unavailable() from exc

    try:
        file = await files_repository.insert_ready(
            db,
            uploaded_by=actor.id,
            storage_key=storage_key,
            original_name=sanitize_filename(filename),
            mime_type=mime_type,
            size_bytes=len(data),
            sha256=hashlib.sha256(data).hexdigest(),
            purpose=purpose.value,
        )
        await record_audit(
            db,
            actor=actor,
            action="file.upload",
            entity_type="files",
            entity_id=file.id,
            change_summary={"purpose": file.purpose, "mime_type": file.mime_type},
        )
        await db.commit()
    except BaseException:
        await db.rollback()
        try:
            await asyncio.to_thread(storage.delete, storage_key)
        except StorageError:
            logger.warning("Không dọn được tệp mồ côi", extra={"storage_key": storage_key})
        raise
    return to_view(file)


def download_name(file: FileRow) -> str:
    return file.original_name or f"{file.id}{EXTENSIONS.get(file.mime_type, '')}"


async def read_for_download(
    db: AsyncSession, *, actor: UserRow, file_id: uuid.UUID, storage: FileStorage
) -> tuple[FileRow, bytes]:
    file = await ensure_can_download(db, actor, file_id)
    try:
        data = await asyncio.to_thread(storage.read, file.storage_key)
    except StorageError as exc:
        logger.error("Đọc kho tệp thất bại", extra={"file_id": str(file.id)})
        raise dependency_unavailable() from exc
    if hashlib.sha256(data).hexdigest() != file.sha256:
        # Tệp trong kho bị hỏng/ghi đè: không phát nội dung sai lệch cho người dùng.
        logger.error("Tệp trong kho sai hash", extra={"file_id": str(file.id)})
        raise dependency_unavailable()
    return file, data
