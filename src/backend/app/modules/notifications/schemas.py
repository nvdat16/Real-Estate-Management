from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel


JobSort = Literal["created_at", "-created_at"]
# `mine` là mặc định cho mọi người; `all` (kể cả job hệ thống) cần `job.manage`.
JobScope = Literal["mine", "all"]


class JobView(BaseModel):
    """Không trả `payload`/`idempotency_key`: payload có thể chứa tham chiếu nội
    bộ (ví dụ user_id của job reset mật khẩu), không cần cho việc theo dõi."""

    id: uuid.UUID
    job_type: str
    status: str
    requested_by: uuid.UUID | None
    attempts: int
    max_attempts: int
    error_code: str | None
    # Người xem được thử lại job này hay không (failed do lỗi tạm thời).
    retryable: bool
    input_file_id: uuid.UUID | None
    output_file_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None
    finished_at: datetime | None


class JobAccepted(BaseModel):
    """Body của response 202 cho lệnh tạo tác vụ nền (SPEC mục 3.1)."""

    job_id: uuid.UUID
    status: str
    status_url: str
