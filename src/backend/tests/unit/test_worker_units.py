"""Unit test không cần hạ tầng: phân loại lỗi SMTP, kho tệp cục bộ, helper tệp,
chính sách backoff và cấu hình Celery."""

from __future__ import annotations

import smtplib
from pathlib import Path
from typing import Any, ClassVar

import pytest

from app.common.utils.file import (
    content_disposition,
    extension_of,
    is_utf8_csv,
    sanitize_filename,
    sniff_image_or_pdf,
)
from app.integrations.email.service import (
    EmailRejectedError,
    EmailUnavailableError,
    OutgoingEmail,
    SmtpEmailSender,
)
from app.integrations.file_storage.service import LocalFileStorage, StorageNotFoundError
from app.modules.notifications.exceptions import backoff_seconds


def test_backoff_5_roi_15_giay() -> None:
    assert [backoff_seconds(n) for n in (1, 2, 3, 10)] == [5, 15, 15, 15]


# --- SMTP -----------------------------------------------------------------------------


class _FakeSMTP:
    error: ClassVar[Exception | None] = None
    sent: ClassVar[list[Any]] = []

    def __init__(self, host: str, port: int, timeout: float) -> None:
        self.args = (host, port, timeout)

    def __enter__(self) -> _FakeSMTP:
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def send_message(self, message: Any) -> None:
        if _FakeSMTP.error is not None:
            raise _FakeSMTP.error
        _FakeSMTP.sent.append(message)


@pytest.fixture
def fake_smtp(monkeypatch: pytest.MonkeyPatch) -> type[_FakeSMTP]:
    _FakeSMTP.error = None
    _FakeSMTP.sent = []
    monkeypatch.setattr(smtplib, "SMTP", _FakeSMTP)
    return _FakeSMTP


def _sender() -> SmtpEmailSender:
    return SmtpEmailSender(host="mailhog", port=1025, sender="REM <no-reply@demo.com>", timeout=1.0)


_MESSAGE = OutgoingEmail(to="khach@example.com", subject="Chủ đề", text_body="Nội dung")


def test_smtp_gui_thanh_cong_tra_message_id(fake_smtp: type[_FakeSMTP]) -> None:
    message_id = _sender().send(_MESSAGE)
    assert message_id.endswith("@demo.com>")
    sent = fake_smtp.sent[0]
    assert sent["To"] == "khach@example.com"
    assert sent["Subject"] == "Chủ đề"


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (ConnectionRefusedError(), EmailUnavailableError),
        (TimeoutError(), EmailUnavailableError),
        (smtplib.SMTPServerDisconnected(), EmailUnavailableError),
        (smtplib.SMTPDataError(451, b"try later"), EmailUnavailableError),
        (smtplib.SMTPDataError(554, b"rejected"), EmailRejectedError),
        (smtplib.SMTPRecipientsRefused({"x@y": (550, b"no")}), EmailRejectedError),
    ],
)
def test_smtp_phan_loai_loi(
    fake_smtp: type[_FakeSMTP], error: Exception, expected: type[Exception]
) -> None:
    fake_smtp.error = error
    with pytest.raises(expected):
        _sender().send(_MESSAGE)


# --- kho tệp ----------------------------------------------------------------------------


def test_kho_tep_ghi_doc_xoa(tmp_path: Path) -> None:
    storage = LocalFileStorage(tmp_path)
    storage.save("kyc/2026/09/abc", b"data")
    assert storage.read("kyc/2026/09/abc") == b"data"
    # Không để lại tệp tạm sau khi ghi.
    assert [p.name for p in (tmp_path / "kyc/2026/09").iterdir()] == ["abc"]
    storage.delete("kyc/2026/09/abc")
    storage.delete("kyc/2026/09/abc")
    with pytest.raises(StorageNotFoundError):
        storage.read("kyc/2026/09/abc")


@pytest.mark.parametrize("key", ["../etc/passwd", "/abs/path", "kyc/../../x", "KYC/A", ""])
def test_kho_tep_chan_path_traversal(tmp_path: Path, key: str) -> None:
    with pytest.raises(ValueError):
        LocalFileStorage(tmp_path).save(key, b"x")


# --- helper tệp ---------------------------------------------------------------------------


def test_nhan_dien_noi_dung() -> None:
    assert sniff_image_or_pdf(b"\xff\xd8\xff\xe0rest") == "image/jpeg"
    assert sniff_image_or_pdf(b"%PDF-1.4") == "application/pdf"
    assert sniff_image_or_pdf(b"<svg/>") is None
    assert is_utf8_csv("mã,tên\n".encode()) is True
    assert is_utf8_csv(b"a,b\x00") is False
    assert extension_of("Bao.Cao.XLSX") == ".xlsx"
    assert extension_of("khong-duoi") == ""


def test_ten_tep_va_content_disposition() -> None:
    assert sanitize_filename("C:\\Users\\a\\hồ sơ\x07.pdf") == "hồ sơ.pdf"
    assert sanitize_filename("   ") is None
    assert sanitize_filename(None) is None

    header = content_disposition('hợp "đồng"\r\n.pdf')
    assert "\r" not in header
    assert "\n" not in header
    assert header.startswith('attachment; filename="hop_dong_.pdf"')
    assert "filename*=UTF-8''h%E1%BB%A3p%20%22%C4%91%E1%BB%93ng%22%0D%0A.pdf" in header


def test_celery_dang_ky_task_va_beat() -> None:
    from app.workers.celery import PROCESS_JOB_TASK, celery_app

    assert {PROCESS_JOB_TASK, "app.workers.dispatch_outbox", "app.workers.reconcile_jobs"} <= set(
        celery_app.tasks
    )
    assert celery_app.conf.task_acks_late is True
    assert set(celery_app.conf.beat_schedule) == {"dispatch-outbox", "reconcile-jobs"}
