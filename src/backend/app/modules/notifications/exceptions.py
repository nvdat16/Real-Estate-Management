"""Lỗi xử lý job và chính sách retry (SPEC SP-07, PLAN task 4.3).

`jobs.error_code` chỉ chứa một mã trong `JobErrorCode` — không lưu message,
stack trace hay dữ liệu từ nhà cung cấp, nên người yêu cầu đọc được lỗi đã làm
sạch mà không lộ chi tiết nội bộ.

Hai nhóm lỗi:

- tạm thời (SMTP/kho tệp/worker mất tín hiệu): tự thử lại theo backoff trong
  ngân sách `max_attempts`, hết lượt thì người yêu cầu được retry thủ công;
- vĩnh viễn (payload sai, người nhận không còn, mất quyền): failed ngay, không
  tự retry và không cho retry thủ công vì chạy lại vẫn cho cùng kết quả.
"""

from __future__ import annotations

from app.common.enums import JobType


class JobErrorCode:
    SMTP_UNAVAILABLE = "SMTP_UNAVAILABLE"
    STORAGE_UNAVAILABLE = "STORAGE_UNAVAILABLE"
    WORKER_LOST = "WORKER_LOST"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    EMAIL_REJECTED = "EMAIL_REJECTED"
    INVALID_PAYLOAD = "INVALID_PAYLOAD"
    RECIPIENT_UNAVAILABLE = "RECIPIENT_UNAVAILABLE"
    PERMISSION_REVOKED = "PERMISSION_REVOKED"
    UNSUPPORTED_JOB_TYPE = "UNSUPPORTED_JOB_TYPE"


RETRYABLE_ERROR_CODES = frozenset(
    {
        JobErrorCode.SMTP_UNAVAILABLE,
        JobErrorCode.STORAGE_UNAVAILABLE,
        JobErrorCode.WORKER_LOST,
        # Lỗi chưa phân loại: coi là tạm thời để không bỏ job vì một lỗi thoáng
        # qua, nhưng vẫn bị chặn bởi `max_attempts`.
        JobErrorCode.INTERNAL_ERROR,
    }
)

DEFAULT_MAX_ATTEMPTS = 3
# SPEC SP-07: backoff 5 rồi 15 giây giữa các lần thử.
RETRY_BACKOFF_SECONDS = (5, 15)

# Heartbeat là `jobs.updated_at`. Timeout theo loại job để không đánh dấu chết một
# job dài hợp lệ chỉ vì chạy lâu hơn email vài giây (SPEC SP-07).
STALE_RUNNING_TIMEOUT_SECONDS: dict[str, int] = {
    JobType.SEND_EMAIL: 120,
    JobType.GENERATE_CONTRACT_PDF: 300,
    JobType.GENERATE_INVOICE_PDF: 300,
    JobType.EXPORT_REPORT: 900,
    JobType.EXPORT_DATA: 900,
    JobType.IMPORT_PROJECTS: 900,
    JobType.IMPORT_PROPERTIES: 900,
}
DEFAULT_STALE_RUNNING_TIMEOUT_SECONDS = 900


def backoff_seconds(attempts: int) -> int:
    """Thời gian chờ trước lần thử kế tiếp sau `attempts` lần đã chạy."""
    index = min(max(attempts, 1), len(RETRY_BACKOFF_SECONDS)) - 1
    return RETRY_BACKOFF_SECONDS[index]


class JobError(Exception):
    retryable: bool = False

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class TransientJobError(JobError):
    retryable = True


class PermanentJobError(JobError):
    retryable = False
