"""Điểm tập hợp model cho Alembic.

Module này chỉ import để đăng ký toàn bộ bảng vào `Base.metadata`; không chứa
logic. Service nghiệp vụ import model từ module sở hữu, không import từ đây.

Thêm bảng mới: tạo model trong module sở hữu rồi thêm import vào danh sách dưới,
nếu không `alembic revision --autogenerate` sẽ bỏ sót hoặc coi bảng là dư.
"""

from __future__ import annotations

from app.core.database import Base
from app.modules.agents.models import Agent
from app.modules.audit_logs.models import AuditLog
from app.modules.auth.models import PasswordResetToken
from app.modules.commissions.models import Commission
from app.modules.contracts.models import (
    Contract,
    ContractParty,
    ContractSignature,
    ContractVersion,
    SigningChallenge,
)
from app.modules.customers.models import Customer
from app.modules.files.models import File
from app.modules.invoices.models import Invoice
from app.modules.kyc.models import KycVerification
from app.modules.listings.models import Listing
from app.modules.notifications.models import EmailDelivery, Job, OutboxEvent
from app.modules.projects.models import Project
from app.modules.properties.models import Property
from app.modules.roles.models import Permission, Role, RolePermission, UserRole
from app.modules.users.models import User


__all__ = [
    "Agent",
    "AuditLog",
    "Base",
    "Commission",
    "Contract",
    "ContractParty",
    "ContractSignature",
    "ContractVersion",
    "Customer",
    "EmailDelivery",
    "File",
    "Invoice",
    "Job",
    "KycVerification",
    "Listing",
    "OutboxEvent",
    "PasswordResetToken",
    "Permission",
    "Project",
    "Property",
    "Role",
    "RolePermission",
    "SigningChallenge",
    "User",
    "UserRole",
]
