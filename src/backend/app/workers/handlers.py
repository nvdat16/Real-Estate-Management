"""Bảng job_type → handler. Phase 6 thêm PDF hợp đồng, Phase 7 PDF hóa đơn,
Phase 8 nhập/xuất; job_type chưa có handler sẽ failed `UNSUPPORTED_JOB_TYPE`."""

from __future__ import annotations

from app.common.enums import JobType
from app.workers.email_tasks import handle_send_email
from app.workers.runner import JobHandler


JOB_HANDLERS: dict[str, JobHandler] = {
    JobType.SEND_EMAIL.value: handle_send_email,
}
