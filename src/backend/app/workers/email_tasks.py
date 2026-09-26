"""Job `send_email` (PLAN task 4.4, SPEC SP-07): một job gửi một người nhận.

Nội dung nhạy cảm (token reset, sau này là OTP) được sinh ngay trong task, chỉ
nằm trong bộ nhớ để đưa vào thư; DB chỉ giữ hash. Mỗi lần chạy lại sinh giá trị
mới và vô hiệu giá trị cũ, nên thư gửi trùng do SMTP timeout chỉ có thư mới
nhất dùng được (không hứa exactly-once với email).
"""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import Awaitable, Callable
from urllib.parse import quote

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import EmailDeliveryStatus
from app.core.config import settings
from app.integrations.email.service import EmailRejectedError, EmailUnavailableError, OutgoingEmail
from app.modules.auth import service as auth_service
from app.modules.notifications import repository as notifications_repository
from app.modules.notifications.exceptions import (
    JobErrorCode,
    PermanentJobError,
    TransientJobError,
)
from app.modules.notifications.repository import EmailDeliveryRow, JobRow
from app.modules.users import repository as users_repository
from app.workers.runner import JobContext


EmailBuilder = Callable[[AsyncSession, EmailDeliveryRow, JobRow], Awaitable[OutgoingEmail]]


def _payload_uuid(job: JobRow, key: str) -> uuid.UUID:
    try:
        return uuid.UUID(str(job.payload[key]))
    except (KeyError, ValueError) as exc:
        raise PermanentJobError(JobErrorCode.INVALID_PAYLOAD) from exc


async def _build_password_reset(
    db: AsyncSession, delivery: EmailDeliveryRow, job: JobRow
) -> OutgoingEmail:
    user = await users_repository.get_by_id(db, _payload_uuid(job, "user_id"))
    if user is None or user.deleted_at is not None:
        raise PermanentJobError(JobErrorCode.RECIPIENT_UNAVAILABLE)

    raw_token = await auth_service.issue_password_reset_token(db, user)
    link = f"{settings.PUBLIC_APP_URL.rstrip('/')}/reset-password?token={quote(raw_token)}"
    minutes = int(auth_service.RESET_TOKEN_TTL.total_seconds() // 60)
    body = (
        f"Xin chào {user.full_name},\n\n"
        "Chúng tôi nhận được yêu cầu đặt lại mật khẩu cho tài khoản của bạn.\n"
        f"Mở liên kết sau trong vòng {minutes} phút để đặt mật khẩu mới:\n\n"
        f"{link}\n\n"
        "Liên kết chỉ dùng được một lần. Nếu bạn nhận được nhiều thư, chỉ thư mới nhất"
        " còn hiệu lực.\n"
        "Nếu bạn không yêu cầu, hãy bỏ qua thư này; mật khẩu hiện tại vẫn giữ nguyên.\n"
    )
    return OutgoingEmail(
        to=delivery.recipient_email,
        subject="Đặt lại mật khẩu — Real Estate Management",
        text_body=body,
    )


EMAIL_TEMPLATES: dict[str, EmailBuilder] = {
    auth_service.PASSWORD_RESET_TEMPLATE: _build_password_reset,
}


async def handle_send_email(context: JobContext) -> uuid.UUID | None:
    async with context.session_factory() as db:
        delivery = await notifications_repository.get_email_delivery_by_job(db, context.job.id)
        if delivery is None:
            raise PermanentJobError(JobErrorCode.INVALID_PAYLOAD)
        if delivery.status == EmailDeliveryStatus.SENT:
            # Worker trước đã gửi và ghi `sent` nhưng chết trước khi đóng job.
            return None
        builder = EMAIL_TEMPLATES.get(delivery.template_code)
        if builder is None:
            raise PermanentJobError(JobErrorCode.INVALID_PAYLOAD)
        message = await builder(db, delivery, context.job)
        # Kết thúc transaction trước khi gọi SMTP: không giữ kết nối/khóa DB khi chờ mạng.
        await db.commit()

    try:
        message_id = await asyncio.to_thread(context.email_sender.send, message)
    except EmailRejectedError as exc:
        raise PermanentJobError(JobErrorCode.EMAIL_REJECTED) from exc
    except EmailUnavailableError as exc:
        raise TransientJobError(JobErrorCode.SMTP_UNAVAILABLE) from exc

    async with context.session_factory() as db:
        await notifications_repository.mark_email_sent(
            db, delivery.id, provider_message_id=message_id
        )
        await db.commit()
    return None
