from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.common.enums import FilePurpose


# Client chỉ upload được giấy tờ KYC và tệp nhập liệu; PDF hợp đồng/hóa đơn, báo
# cáo và tệp xuất do worker sinh, không nhận từ client.
UploadPurpose = Literal[FilePurpose.KYC, FilePurpose.IMPORT]


class FileView(BaseModel):
    """Không có `storage_key` hay đường dẫn nội bộ (SPEC SP-06)."""

    id: uuid.UUID
    original_name: str | None
    mime_type: str
    size_bytes: int | None
    sha256: str | None
    purpose: str
    status: str
    created_at: datetime
