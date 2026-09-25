"""Tập giá trị trạng thái dùng chung giữa model, service và schema.

Giá trị phải khớp bảng chuyển trạng thái ở PRD mục 5.1 và ERD mục 4. Cột trong
database là varchar kèm CHECK (không dùng enum type của PostgreSQL) để thêm/bớt
giá trị chỉ cần đổi CHECK trong migration.
"""

from __future__ import annotations

from enum import StrEnum


class UserStatus(StrEnum):
    ACTIVE = "active"
    LOCKED = "locked"


class AgentStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class ProjectStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class PropertyStatus(StrEnum):
    AVAILABLE = "available"
    RESERVED = "reserved"
    SOLD = "sold"
    RENTED = "rented"


class ListingStatus(StrEnum):
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CLOSED = "closed"


class ListingType(StrEnum):
    SALE = "sale"
    RENT = "rent"


class PriceUnit(StrEnum):
    TOTAL = "total"
    MONTH = "month"


class ContractStatus(StrEnum):
    DRAFT = "draft"
    PENDING_SIGNATURES = "pending_signatures"
    SIGNED = "signed"
    CANCELLED = "cancelled"


class PartyRole(StrEnum):
    CUSTOMER = "customer"
    REPRESENTATIVE = "representative"


class SignatureMethod(StrEnum):
    EMAIL_OTP = "email_otp"


class KycStatus(StrEnum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    FAILED = "failed"


class InvoiceStatus(StrEnum):
    DRAFT = "draft"
    ISSUED = "issued"
    PAID = "paid"
    VOID = "void"


class CommissionStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    PAID = "paid"
    CANCELLED = "cancelled"


class FilePurpose(StrEnum):
    CONTRACT_PDF = "contract_pdf"
    INVOICE_PDF = "invoice_pdf"
    REPORT = "report"
    DATA_EXPORT = "data_export"
    IMPORT = "import"
    KYC = "kyc"


class FileStatus(StrEnum):
    PENDING = "pending"
    READY = "ready"
    FAILED = "failed"


class JobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class JobType(StrEnum):
    SEND_EMAIL = "send_email"
    GENERATE_CONTRACT_PDF = "generate_contract_pdf"
    GENERATE_INVOICE_PDF = "generate_invoice_pdf"
    EXPORT_REPORT = "export_report"
    EXPORT_DATA = "export_data"
    IMPORT_PROJECTS = "import_projects"
    IMPORT_PROPERTIES = "import_properties"


class OutboxStatus(StrEnum):
    PENDING = "pending"
    PUBLISHING = "publishing"
    PUBLISHED = "published"


class EmailDeliveryStatus(StrEnum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class ActorType(StrEnum):
    USER = "user"
    SYSTEM = "system"


def values(enum_cls: type[StrEnum]) -> tuple[str, ...]:
    """Dùng để dựng biểu thức CHECK trong model."""
    return tuple(member.value for member in enum_cls)


def sql_in(column: str, enum_cls: type[StrEnum]) -> str:
    quoted = ", ".join(f"'{value}'" for value in values(enum_cls))
    return f"{column} IN ({quoted})"
