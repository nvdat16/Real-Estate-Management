"""Adapter SMTP (PLAN task 4.4). Chỉ worker gọi (ARCHITECTURE §5.3), không bao
giờ gọi bên trong transaction đang giữ khóa DB.

`smtplib` là đồng bộ: worker async gọi `send` qua `asyncio.to_thread`. Adapter
chỉ phân loại lỗi thành tạm thời (mất kết nối, timeout, 4xx) và vĩnh viễn (máy
chủ từ chối người nhận/nội dung 5xx); quyết định retry thuộc về worker.
"""

from __future__ import annotations

import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from email.utils import make_msgid, parseaddr
from typing import Protocol

from app.core.config import settings


@dataclass(frozen=True)
class OutgoingEmail:
    to: str
    subject: str
    text_body: str


class EmailDeliveryError(Exception):
    """Lỗi gửi thư; message không chứa nội dung thư (có thể có token/OTP)."""


class EmailUnavailableError(EmailDeliveryError):
    """Máy chủ SMTP không kết nối được hoặc từ chối tạm thời — thử lại được."""


class EmailRejectedError(EmailDeliveryError):
    """Máy chủ từ chối vĩnh viễn (người nhận/nội dung) — thử lại cũng vô ích."""


class EmailSender(Protocol):
    def send(self, message: OutgoingEmail) -> str:
        """Gửi thư, trả Message-ID để lưu `email_deliveries.provider_message_id`."""
        ...


class SmtpEmailSender:
    def __init__(
        self,
        *,
        host: str,
        port: int,
        sender: str,
        timeout: float,
        username: str | None = None,
        password: str | None = None,
        starttls: bool = False,
    ) -> None:
        self._host = host
        self._port = port
        self._sender = sender
        self._timeout = timeout
        self._username = username
        self._password = password
        self._starttls = starttls

    def _build(self, message: OutgoingEmail) -> EmailMessage:
        _, sender_address = parseaddr(self._sender)
        domain = sender_address.rpartition("@")[2] or None
        email = EmailMessage()
        email["From"] = self._sender
        email["To"] = message.to
        email["Subject"] = message.subject
        email["Message-ID"] = make_msgid(domain=domain)
        email.set_content(message.text_body)
        return email

    def send(self, message: OutgoingEmail) -> str:
        email = self._build(message)
        try:
            with smtplib.SMTP(self._host, self._port, timeout=self._timeout) as smtp:
                if self._starttls:
                    smtp.starttls()
                if self._username and self._password:
                    smtp.login(self._username, self._password)
                smtp.send_message(email)
        except smtplib.SMTPRecipientsRefused as exc:
            raise EmailRejectedError("SMTP từ chối người nhận") from exc
        except smtplib.SMTPResponseException as exc:
            if 500 <= exc.smtp_code < 600:
                raise EmailRejectedError(f"SMTP từ chối thư ({exc.smtp_code})") from exc
            raise EmailUnavailableError(f"SMTP tạm lỗi ({exc.smtp_code})") from exc
        except (smtplib.SMTPException, OSError) as exc:
            raise EmailUnavailableError("Không kết nối được SMTP") from exc
        return str(email["Message-ID"])


def get_email_sender() -> SmtpEmailSender:
    return SmtpEmailSender(
        host=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        sender=settings.SMTP_FROM,
        timeout=settings.SMTP_TIMEOUT_SECONDS,
        username=settings.SMTP_USERNAME,
        password=settings.SMTP_PASSWORD,
        starttls=settings.SMTP_STARTTLS,
    )
