"""HTTP↔schema mapping cho tệp private (SPEC §11 nhóm "Nhập/tệp").

Tải xuống luôn là `attachment` + MIME do server nhận diện + `nosniff`, không
cache ở trình duyệt/proxy dùng chung.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, Form, Response, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import FilePurpose
from app.common.utils.file import content_disposition
from app.core.database import get_db
from app.dependencies import get_current_user
from app.integrations.file_storage.service import FileStorage, get_file_storage
from app.modules.files import service as files_service
from app.modules.files.schemas import FileView, UploadPurpose
from app.modules.users.repository import UserRow


router = APIRouter(prefix="/files", tags=["files"])


@router.post("", response_model=FileView, status_code=201)
async def upload_file(
    purpose: UploadPurpose = Form(),
    file: UploadFile = File(),
    actor: UserRow = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    storage: FileStorage = Depends(get_file_storage),
) -> FileView:
    # Đọc dư một byte để phát hiện vượt giới hạn mà không nạp cả tệp lớn.
    data = await file.read(files_service.MAX_UPLOAD_BYTES + 1)
    return await files_service.upload(
        db,
        actor=actor,
        purpose=FilePurpose(purpose),
        filename=file.filename,
        data=data,
        storage=storage,
    )


@router.get("/{file_id}/download", response_class=Response)
async def download_file(
    file_id: uuid.UUID,
    actor: UserRow = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    storage: FileStorage = Depends(get_file_storage),
) -> Response:
    record, data = await files_service.read_for_download(
        db, actor=actor, file_id=file_id, storage=storage
    )
    return Response(
        content=data,
        media_type=record.mime_type,
        headers={
            "Content-Disposition": content_disposition(files_service.download_name(record)),
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "private, no-store",
        },
    )
