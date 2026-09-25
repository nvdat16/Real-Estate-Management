"""initial schema

Revision ID: 32cc7c72e1e3
Revises:
Create Date: 2026-09-17 07:25:41.697392

"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "32cc7c72e1e3"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_roles")),
        sa.UniqueConstraint("code", name=op.f("uq_roles_code")),
    )
    op.create_table(
        "permissions",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_permissions")),
        sa.UniqueConstraint("code", name=op.f("uq_permissions_code")),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=150), nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=True),
        sa.Column(
            "status", sa.String(length=16), server_default=sa.text("'active'"), nullable=False
        ),
        sa.Column("auth_version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.UUID(), nullable=True),
        sa.Column("row_version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.CheckConstraint("status IN ('active', 'locked')", name=op.f("ck_users_status_valid")),
        sa.CheckConstraint("auth_version >= 1", name=op.f("ck_users_auth_version_positive")),
        sa.CheckConstraint("email = lower(email)", name=op.f("ck_users_email_normalized")),
        sa.ForeignKeyConstraint(
            ["deleted_by"], ["users.id"], name=op.f("fk_users_deleted_by"), ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )
    op.create_table(
        "agents",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("agent_code", sa.String(length=32), nullable=False),
        sa.Column(
            "status", sa.String(length=16), server_default=sa.text("'active'"), nullable=False
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.UUID(), nullable=True),
        sa.Column("row_version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.CheckConstraint("status IN ('active', 'inactive')", name=op.f("ck_agents_status_valid")),
        sa.ForeignKeyConstraint(
            ["deleted_by"], ["users.id"], name=op.f("fk_agents_deleted_by"), ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_agents_user_id"), ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_agents")),
        sa.UniqueConstraint("agent_code", name=op.f("uq_agents_agent_code")),
        sa.UniqueConstraint("user_id", name=op.f("uq_agents_user_id")),
    )
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("actor_user_id", sa.UUID(), nullable=True),
        sa.Column(
            "actor_type", sa.String(length=8), server_default=sa.text("'user'"), nullable=False
        ),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("entity_id", sa.UUID(), nullable=False),
        sa.Column("change_summary", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "(actor_type = 'system' AND actor_user_id IS NULL) OR (actor_type = 'user' AND actor_user_id IS NOT NULL)",
            name=op.f("ck_audit_logs_actor_matches_type"),
        ),
        sa.CheckConstraint(
            "actor_type IN ('user', 'system')", name=op.f("ck_audit_logs_actor_type_valid")
        ),
        sa.ForeignKeyConstraint(
            ["actor_user_id"],
            ["users.id"],
            name=op.f("fk_audit_logs_actor_user_id"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_logs")),
    )
    op.create_index(
        "ix_audit_logs_actor_user_id_created_at",
        "audit_logs",
        ["actor_user_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_audit_logs_entity_type_entity_id_created_at",
        "audit_logs",
        ["entity_type", "entity_id", "created_at"],
        unique=False,
    )
    op.create_table(
        "password_reset_tokens",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_password_reset_tokens_user_id"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_password_reset_tokens")),
        sa.UniqueConstraint("token_hash", name=op.f("uq_password_reset_tokens_token_hash")),
    )
    op.create_index(
        op.f("ix_password_reset_tokens_user_id"), "password_reset_tokens", ["user_id"], unique=False
    )
    op.create_table(
        "customers",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("customer_code", sa.String(length=32), nullable=False),
        sa.Column("address", sa.String(length=500), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.UUID(), nullable=True),
        sa.Column("row_version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.ForeignKeyConstraint(
            ["deleted_by"], ["users.id"], name=op.f("fk_customers_deleted_by"), ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_customers_user_id"), ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_customers")),
        sa.UniqueConstraint("customer_code", name=op.f("uq_customers_customer_code")),
        sa.UniqueConstraint("user_id", name=op.f("uq_customers_user_id")),
        comment="Hồ sơ khách hàng, mỗi tài khoản tối đa một hồ sơ",
    )
    op.create_table(
        "files",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("uploaded_by", sa.UUID(), nullable=True),
        sa.Column("storage_key", sa.String(length=255), nullable=False),
        sa.Column("original_name", sa.String(length=255), nullable=True),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("sha256", sa.String(length=64), nullable=True),
        sa.Column("purpose", sa.String(length=32), nullable=False),
        sa.Column(
            "status", sa.String(length=16), server_default=sa.text("'pending'"), nullable=False
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "purpose IN ('contract_pdf', 'invoice_pdf', 'report', 'data_export', 'import', 'kyc')",
            name=op.f("ck_files_purpose_valid"),
        ),
        sa.CheckConstraint(
            "status <> 'ready' OR (sha256 IS NOT NULL AND size_bytes IS NOT NULL)",
            name=op.f("ck_files_ready_needs_hash_and_size"),
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'ready', 'failed')", name=op.f("ck_files_status_valid")
        ),
        sa.CheckConstraint(
            "size_bytes IS NULL OR size_bytes >= 0", name=op.f("ck_files_size_non_negative")
        ),
        sa.ForeignKeyConstraint(
            ["uploaded_by"], ["users.id"], name=op.f("fk_files_uploaded_by"), ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_files")),
        sa.UniqueConstraint("storage_key", name=op.f("uq_files_storage_key")),
    )
    op.create_table(
        "projects",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("address", sa.String(length=500), nullable=False),
        sa.Column("province_code", sa.String(length=10), nullable=False),
        sa.Column("ward_code", sa.String(length=10), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status", sa.String(length=16), server_default=sa.text("'active'"), nullable=False
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.UUID(), nullable=True),
        sa.Column("row_version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.CheckConstraint(
            "status IN ('active', 'inactive')", name=op.f("ck_projects_status_valid")
        ),
        sa.ForeignKeyConstraint(
            ["deleted_by"], ["users.id"], name=op.f("fk_projects_deleted_by"), ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_projects")),
        sa.UniqueConstraint("code", name=op.f("uq_projects_code")),
    )
    op.create_index(
        "ix_projects_province_code_ward_code",
        "projects",
        ["province_code", "ward_code"],
        unique=False,
    )
    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("role_id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["role_id"], ["roles.id"], name=op.f("fk_user_roles_role_id"), ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_user_roles_user_id"), ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("user_id", "role_id", name=op.f("pk_user_roles")),
    )
    op.create_table(
        "role_permissions",
        sa.Column("role_id", sa.UUID(), nullable=False),
        sa.Column("permission_id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["permission_id"],
            ["permissions.id"],
            name=op.f("fk_role_permissions_permission_id"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["role_id"], ["roles.id"], name=op.f("fk_role_permissions_role_id"), ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("role_id", "permission_id", name=op.f("pk_role_permissions")),
    )
    op.create_table(
        "kyc_verifications",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("customer_id", sa.UUID(), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("provider_request_id", sa.String(length=100), nullable=True),
        sa.Column(
            "status", sa.String(length=16), server_default=sa.text("'pending'"), nullable=False
        ),
        sa.Column("evidence_file_id", sa.UUID(), nullable=True),
        sa.Column("reviewed_by", sa.UUID(), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reason", sa.String(length=1000), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status <> 'verified' OR verified_at IS NOT NULL",
            name=op.f("ck_kyc_verifications_verified_needs_timestamp"),
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'verified', 'rejected', 'failed')",
            name=op.f("ck_kyc_verifications_status_valid"),
        ),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["customers.id"],
            name=op.f("fk_kyc_verifications_customer_id"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["evidence_file_id"],
            ["files.id"],
            name=op.f("fk_kyc_verifications_evidence_file_id"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["reviewed_by"],
            ["users.id"],
            name=op.f("fk_kyc_verifications_reviewed_by"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_kyc_verifications")),
        sa.UniqueConstraint(
            "provider",
            "provider_request_id",
            name="uq_kyc_verifications_provider_provider_request_id",
        ),
    )
    op.create_index(
        "ix_kyc_verifications_customer_id_created_at",
        "kyc_verifications",
        ["customer_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "uq_kyc_verifications_pending_customer",
        "kyc_verifications",
        ["customer_id"],
        unique=True,
        postgresql_where=sa.text("status = 'pending'"),
    )
    op.create_table(
        "jobs",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("requested_by", sa.UUID(), nullable=True),
        sa.Column("job_type", sa.String(length=50), nullable=False),
        sa.Column("idempotency_key", sa.String(length=200), nullable=False),
        sa.Column(
            "status", sa.String(length=16), server_default=sa.text("'pending'"), nullable=False
        ),
        sa.Column(
            "payload",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("input_file_id", sa.UUID(), nullable=True),
        sa.Column("output_file_id", sa.UUID(), nullable=True),
        sa.Column("attempts", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("max_attempts", sa.Integer(), server_default=sa.text("3"), nullable=False),
        sa.Column("error_code", sa.String(length=50), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "job_type IN ('send_email', 'generate_contract_pdf', 'generate_invoice_pdf', 'export_report', 'export_data', 'import_projects', 'import_properties')",
            name=op.f("ck_jobs_job_type_valid"),
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'running', 'succeeded', 'failed')",
            name=op.f("ck_jobs_status_valid"),
        ),
        sa.CheckConstraint("attempts >= 0", name=op.f("ck_jobs_attempts_non_negative")),
        sa.CheckConstraint("max_attempts > 0", name=op.f("ck_jobs_max_attempts_positive")),
        sa.ForeignKeyConstraint(
            ["input_file_id"], ["files.id"], name=op.f("fk_jobs_input_file_id"), ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["output_file_id"],
            ["files.id"],
            name=op.f("fk_jobs_output_file_id"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["requested_by"], ["users.id"], name=op.f("fk_jobs_requested_by"), ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_jobs")),
        sa.UniqueConstraint("idempotency_key", name=op.f("uq_jobs_idempotency_key")),
    )
    op.create_index(
        "ix_jobs_requested_by_created_at", "jobs", ["requested_by", "created_at"], unique=False
    )
    op.create_index("ix_jobs_status_created_at", "jobs", ["status", "created_at"], unique=False)
    op.create_table(
        "properties",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("unit_code", sa.String(length=50), nullable=False),
        sa.Column("area_m2", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("bedrooms", sa.Integer(), nullable=False),
        sa.Column("floor", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status", sa.String(length=16), server_default=sa.text("'available'"), nullable=False
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.UUID(), nullable=True),
        sa.Column("row_version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.CheckConstraint(
            "status IN ('available', 'reserved', 'sold', 'rented')",
            name=op.f("ck_properties_status_valid"),
        ),
        sa.CheckConstraint("area_m2 > 0", name=op.f("ck_properties_area_positive")),
        sa.CheckConstraint("bedrooms >= 0", name=op.f("ck_properties_bedrooms_non_negative")),
        sa.ForeignKeyConstraint(
            ["deleted_by"], ["users.id"], name=op.f("fk_properties_deleted_by"), ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name=op.f("fk_properties_project_id"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_properties")),
        sa.UniqueConstraint("project_id", "unit_code", name="uq_properties_project_id_unit_code"),
    )
    op.create_index(
        "ix_properties_project_id_status", "properties", ["project_id", "status"], unique=False
    )
    op.create_table(
        "listings",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("property_id", sa.UUID(), nullable=False),
        sa.Column("agent_id", sa.UUID(), nullable=False),
        sa.Column("reviewed_by", sa.UUID(), nullable=True),
        sa.Column("listing_type", sa.String(length=8), nullable=False),
        sa.Column("asking_price", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("price_unit", sa.String(length=8), nullable=False),
        sa.Column("currency", sa.String(length=3), server_default=sa.text("'VND'"), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "status", sa.String(length=16), server_default=sa.text("'draft'"), nullable=False
        ),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejection_reason", sa.String(length=1000), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.UUID(), nullable=True),
        sa.Column("row_version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.CheckConstraint(
            "(listing_type = 'sale' AND price_unit = 'total') OR (listing_type = 'rent' AND price_unit = 'month')",
            name=op.f("ck_listings_type_price_unit_pair"),
        ),
        sa.CheckConstraint("currency = 'VND'", name=op.f("ck_listings_currency_vnd")),
        sa.CheckConstraint("listing_type IN ('sale', 'rent')", name=op.f("ck_listings_type_valid")),
        sa.CheckConstraint(
            "price_unit IN ('total', 'month')", name=op.f("ck_listings_price_unit_valid")
        ),
        sa.CheckConstraint(
            "status <> 'rejected' OR rejection_reason IS NOT NULL",
            name=op.f("ck_listings_rejected_needs_reason"),
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'pending', 'approved', 'rejected', 'closed')",
            name=op.f("ck_listings_status_valid"),
        ),
        sa.CheckConstraint(
            "status NOT IN ('approved', 'rejected') OR (reviewed_by IS NOT NULL AND reviewed_at IS NOT NULL)",
            name=op.f("ck_listings_reviewed_fields_present"),
        ),
        sa.CheckConstraint("asking_price > 0", name=op.f("ck_listings_price_positive")),
        sa.ForeignKeyConstraint(
            ["agent_id"], ["agents.id"], name=op.f("fk_listings_agent_id"), ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["deleted_by"], ["users.id"], name=op.f("fk_listings_deleted_by"), ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["property_id"],
            ["properties.id"],
            name=op.f("fk_listings_property_id"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["reviewed_by"], ["users.id"], name=op.f("fk_listings_reviewed_by"), ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_listings")),
    )
    op.create_index(
        "ix_listings_agent_id_status_created_at_id",
        "listings",
        ["agent_id", "status", "created_at", "id"],
        unique=False,
    )
    op.create_index(
        "ix_listings_public_search",
        "listings",
        ["listing_type", "asking_price", "id"],
        unique=False,
        postgresql_where=sa.text("status = 'approved' AND deleted_at IS NULL"),
    )
    op.create_index(
        "ix_listings_status_created_at_id", "listings", ["status", "created_at", "id"], unique=False
    )
    op.create_index(
        "uq_listings_active_property",
        "listings",
        ["property_id"],
        unique=True,
        postgresql_where=sa.text("status IN ('pending', 'approved') AND deleted_at IS NULL"),
    )
    op.create_table(
        "outbox_events",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("job_id", sa.UUID(), nullable=False),
        sa.Column("event_key", sa.String(length=200), nullable=False),
        sa.Column(
            "status", sa.String(length=16), server_default=sa.text("'pending'"), nullable=False
        ),
        sa.Column(
            "available_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempts", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status <> 'published' OR published_at IS NOT NULL",
            name=op.f("ck_outbox_events_published_needs_timestamp"),
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'publishing', 'published')",
            name=op.f("ck_outbox_events_status_valid"),
        ),
        sa.CheckConstraint("attempts >= 0", name=op.f("ck_outbox_events_attempts_non_negative")),
        sa.ForeignKeyConstraint(
            ["job_id"], ["jobs.id"], name=op.f("fk_outbox_events_job_id"), ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_outbox_events")),
        sa.UniqueConstraint("event_key", name=op.f("uq_outbox_events_event_key")),
    )
    op.create_index(
        "ix_outbox_events_status_available_at",
        "outbox_events",
        ["status", "available_at"],
        unique=False,
    )
    op.create_table(
        "email_deliveries",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("job_id", sa.UUID(), nullable=False),
        sa.Column("recipient_user_id", sa.UUID(), nullable=True),
        sa.Column("recipient_email", sa.String(length=254), nullable=False),
        sa.Column("template_code", sa.String(length=50), nullable=False),
        sa.Column(
            "status", sa.String(length=16), server_default=sa.text("'pending'"), nullable=False
        ),
        sa.Column("provider_message_id", sa.String(length=200), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status <> 'sent' OR sent_at IS NOT NULL",
            name=op.f("ck_email_deliveries_sent_needs_timestamp"),
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'sent', 'failed')", name=op.f("ck_email_deliveries_status_valid")
        ),
        sa.ForeignKeyConstraint(
            ["job_id"], ["jobs.id"], name=op.f("fk_email_deliveries_job_id"), ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["recipient_user_id"],
            ["users.id"],
            name=op.f("fk_email_deliveries_recipient_user_id"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_email_deliveries")),
        sa.UniqueConstraint("job_id", name=op.f("uq_email_deliveries_job_id")),
    )
    op.create_table(
        "contracts",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("contract_no", sa.String(length=50), nullable=False),
        sa.Column("listing_id", sa.UUID(), nullable=False),
        sa.Column("property_id", sa.UUID(), nullable=False),
        sa.Column("customer_id", sa.UUID(), nullable=False),
        sa.Column("agent_id", sa.UUID(), nullable=False),
        sa.Column("created_by", sa.UUID(), nullable=False),
        sa.Column("contract_type", sa.String(length=8), nullable=False),
        sa.Column(
            "status", sa.String(length=24), server_default=sa.text("'draft'"), nullable=False
        ),
        sa.Column("signed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_by", sa.UUID(), nullable=True),
        sa.Column("cancellation_reason", sa.String(length=1000), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.UUID(), nullable=True),
        sa.Column("row_version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.CheckConstraint(
            "contract_type IN ('sale', 'rent')", name=op.f("ck_contracts_type_valid")
        ),
        sa.CheckConstraint(
            "status <> 'cancelled' OR (cancelled_at IS NOT NULL AND cancelled_by IS NOT NULL AND cancellation_reason IS NOT NULL)",
            name=op.f("ck_contracts_cancelled_needs_reason"),
        ),
        sa.CheckConstraint(
            "status <> 'signed' OR signed_at IS NOT NULL",
            name=op.f("ck_contracts_signed_needs_timestamp"),
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'pending_signatures', 'signed', 'cancelled')",
            name=op.f("ck_contracts_status_valid"),
        ),
        sa.ForeignKeyConstraint(
            ["agent_id"], ["agents.id"], name=op.f("fk_contracts_agent_id"), ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["cancelled_by"],
            ["users.id"],
            name=op.f("fk_contracts_cancelled_by"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"], ["users.id"], name=op.f("fk_contracts_created_by"), ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["customers.id"],
            name=op.f("fk_contracts_customer_id"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["deleted_by"], ["users.id"], name=op.f("fk_contracts_deleted_by"), ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["listing_id"],
            ["listings.id"],
            name=op.f("fk_contracts_listing_id"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["property_id"],
            ["properties.id"],
            name=op.f("fk_contracts_property_id"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_contracts")),
        sa.UniqueConstraint("contract_no", name=op.f("uq_contracts_contract_no")),
        sa.UniqueConstraint("id", "agent_id", name="uq_contracts_id_agent_id"),
        sa.UniqueConstraint("id", "contract_type", name="uq_contracts_id_contract_type"),
    )
    op.create_index(
        "ix_contracts_agent_id_status_created_at_id",
        "contracts",
        ["agent_id", "status", "created_at", "id"],
        unique=False,
    )
    op.create_index(
        "ix_contracts_customer_id_created_at_id",
        "contracts",
        ["customer_id", "created_at", "id"],
        unique=False,
    )
    op.create_index(
        "ix_contracts_signed_at",
        "contracts",
        ["signed_at"],
        unique=False,
        postgresql_where=sa.text("status = 'signed'"),
    )
    op.create_index(
        "ix_contracts_status_created_at", "contracts", ["status", "created_at"], unique=False
    )
    op.create_index(
        "uq_contracts_active_property",
        "contracts",
        ["property_id"],
        unique=True,
        postgresql_where=sa.text(
            "status IN ('pending_signatures', 'signed') AND deleted_at IS NULL"
        ),
    )
    op.create_table(
        "contract_versions",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("contract_id", sa.UUID(), nullable=False),
        sa.Column("contract_type", sa.String(length=8), nullable=False),
        sa.Column("version_no", sa.Integer(), nullable=False),
        sa.Column("content_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("total_amount", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("commission_base", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("commission_rate", sa.Numeric(precision=7, scale=4), nullable=False),
        sa.Column("currency", sa.String(length=3), server_default=sa.text("'VND'"), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("pdf_file_id", sa.UUID(), nullable=True),
        sa.Column("frozen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "contract_type <> 'rent' OR (start_date IS NOT NULL AND end_date IS NOT NULL)",
            name=op.f("ck_contract_versions_rent_needs_dates"),
        ),
        sa.CheckConstraint("currency = 'VND'", name=op.f("ck_contract_versions_currency_vnd")),
        sa.CheckConstraint(
            "commission_base >= 0", name=op.f("ck_contract_versions_commission_base_non_negative")
        ),
        sa.CheckConstraint(
            "commission_rate >= 0 AND commission_rate <= 100",
            name=op.f("ck_contract_versions_commission_rate_range"),
        ),
        sa.CheckConstraint(
            "start_date IS NULL OR end_date IS NULL OR end_date > start_date",
            name=op.f("ck_contract_versions_end_after_start"),
        ),
        sa.CheckConstraint(
            "total_amount > 0", name=op.f("ck_contract_versions_total_amount_positive")
        ),
        sa.CheckConstraint("version_no > 0", name=op.f("ck_contract_versions_version_positive")),
        sa.ForeignKeyConstraint(
            ["contract_id", "contract_type"],
            ["contracts.id", "contracts.contract_type"],
            name="fk_contract_versions_contract_id_contract_type",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            name=op.f("fk_contract_versions_created_by"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["pdf_file_id"],
            ["files.id"],
            name=op.f("fk_contract_versions_pdf_file_id"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_contract_versions")),
        sa.UniqueConstraint("contract_id", "id", name="uq_contract_versions_contract_id_id"),
        sa.UniqueConstraint(
            "contract_id", "version_no", name="uq_contract_versions_contract_id_version_no"
        ),
    )
    op.create_table(
        "invoices",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("invoice_no", sa.String(length=50), nullable=False),
        sa.Column("contract_id", sa.UUID(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), server_default=sa.text("'VND'"), nullable=False),
        sa.Column(
            "status", sa.String(length=16), server_default=sa.text("'draft'"), nullable=False
        ),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("content_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("pdf_file_id", sa.UUID(), nullable=True),
        sa.Column("created_by", sa.UUID(), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paid_by", sa.UUID(), nullable=True),
        sa.Column("payment_reference", sa.String(length=100), nullable=True),
        sa.Column("voided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("voided_by", sa.UUID(), nullable=True),
        sa.Column("void_reason", sa.String(length=1000), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("row_version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.CheckConstraint("currency = 'VND'", name=op.f("ck_invoices_currency_vnd")),
        sa.CheckConstraint(
            "status <> 'issued' OR issued_at IS NOT NULL",
            name=op.f("ck_invoices_issued_needs_timestamp"),
        ),
        sa.CheckConstraint(
            "status <> 'paid' OR (paid_at IS NOT NULL AND paid_by IS NOT NULL AND payment_reference IS NOT NULL)",
            name=op.f("ck_invoices_paid_needs_payment_info"),
        ),
        sa.CheckConstraint(
            "status <> 'void' OR (voided_at IS NOT NULL AND voided_by IS NOT NULL AND void_reason IS NOT NULL)",
            name=op.f("ck_invoices_void_needs_reason"),
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'issued', 'paid', 'void')", name=op.f("ck_invoices_status_valid")
        ),
        sa.CheckConstraint("amount > 0", name=op.f("ck_invoices_amount_positive")),
        sa.ForeignKeyConstraint(
            ["contract_id"],
            ["contracts.id"],
            name=op.f("fk_invoices_contract_id"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"], ["users.id"], name=op.f("fk_invoices_created_by"), ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["paid_by"], ["users.id"], name=op.f("fk_invoices_paid_by"), ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["pdf_file_id"], ["files.id"], name=op.f("fk_invoices_pdf_file_id"), ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["voided_by"], ["users.id"], name=op.f("fk_invoices_voided_by"), ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_invoices")),
        sa.UniqueConstraint("invoice_no", name=op.f("uq_invoices_invoice_no")),
    )
    op.create_index(
        "ix_invoices_contract_id_status", "invoices", ["contract_id", "status"], unique=False
    )
    op.create_table(
        "commissions",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("contract_id", sa.UUID(), nullable=False),
        sa.Column("contract_version_id", sa.UUID(), nullable=False),
        sa.Column("agent_id", sa.UUID(), nullable=False),
        sa.Column("base_amount", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("rate_percent", sa.Numeric(precision=7, scale=4), nullable=False),
        sa.Column("amount", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), server_default=sa.text("'VND'"), nullable=False),
        sa.Column(
            "status", sa.String(length=16), server_default=sa.text("'pending'"), nullable=False
        ),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_by", sa.UUID(), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paid_by", sa.UUID(), nullable=True),
        sa.Column("payment_reference", sa.String(length=100), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_by", sa.UUID(), nullable=True),
        sa.Column("cancellation_reason", sa.String(length=1000), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("row_version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.CheckConstraint("currency = 'VND'", name=op.f("ck_commissions_currency_vnd")),
        sa.CheckConstraint(
            "status <> 'cancelled' OR (cancelled_at IS NOT NULL AND cancelled_by IS NOT NULL AND cancellation_reason IS NOT NULL)",
            name=op.f("ck_commissions_cancelled_needs_reason"),
        ),
        sa.CheckConstraint(
            "status <> 'paid' OR (paid_at IS NOT NULL AND paid_by IS NOT NULL AND payment_reference IS NOT NULL)",
            name=op.f("ck_commissions_paid_needs_payment_info"),
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'approved', 'paid', 'cancelled')",
            name=op.f("ck_commissions_status_valid"),
        ),
        sa.CheckConstraint(
            "status NOT IN ('approved', 'paid') OR (approved_at IS NOT NULL AND approved_by IS NOT NULL)",
            name=op.f("ck_commissions_approved_needs_approver"),
        ),
        sa.CheckConstraint(
            "amount = round(base_amount * rate_percent / 100, 0)",
            name=op.f("ck_commissions_amount_matches_formula"),
        ),
        sa.CheckConstraint(
            "base_amount >= 0", name=op.f("ck_commissions_base_amount_non_negative")
        ),
        sa.CheckConstraint(
            "rate_percent >= 0 AND rate_percent <= 100",
            name=op.f("ck_commissions_rate_percent_range"),
        ),
        sa.ForeignKeyConstraint(
            ["approved_by"],
            ["users.id"],
            name=op.f("fk_commissions_approved_by"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["cancelled_by"],
            ["users.id"],
            name=op.f("fk_commissions_cancelled_by"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["contract_id", "agent_id"],
            ["contracts.id", "contracts.agent_id"],
            name="fk_commissions_contract_id_agent_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["contract_id", "contract_version_id"],
            ["contract_versions.contract_id", "contract_versions.id"],
            name="fk_commissions_contract_id_contract_version_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["paid_by"], ["users.id"], name=op.f("fk_commissions_paid_by"), ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_commissions")),
        sa.UniqueConstraint("contract_id", name="uq_commissions_contract_id"),
    )
    op.create_index(
        "ix_commissions_agent_id_status_created_at",
        "commissions",
        ["agent_id", "status", "created_at"],
        unique=False,
    )
    op.create_table(
        "contract_parties",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("contract_version_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("party_role", sa.String(length=16), nullable=False),
        sa.Column("display_name_snapshot", sa.String(length=150), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "party_role IN ('customer', 'representative')",
            name=op.f("ck_contract_parties_party_role_valid"),
        ),
        sa.ForeignKeyConstraint(
            ["contract_version_id"],
            ["contract_versions.id"],
            name=op.f("fk_contract_parties_contract_version_id"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_contract_parties_user_id"), ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_contract_parties")),
        sa.UniqueConstraint(
            "contract_version_id",
            "party_role",
            name="uq_contract_parties_contract_version_id_party_role",
        ),
        sa.UniqueConstraint(
            "contract_version_id", "user_id", name="uq_contract_parties_contract_version_id_user_id"
        ),
    )
    op.create_index(
        "ix_contract_parties_user_id_contract_version_id",
        "contract_parties",
        ["user_id", "contract_version_id"],
        unique=False,
    )
    op.create_table(
        "signing_challenges",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("party_id", sa.UUID(), nullable=False),
        sa.Column("otp_hash", sa.String(length=128), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("attempt_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "attempt_count >= 0 AND attempt_count <= 5",
            name=op.f("ck_signing_challenges_attempt_count_range"),
        ),
        sa.ForeignKeyConstraint(
            ["party_id"],
            ["contract_parties.id"],
            name=op.f("fk_signing_challenges_party_id"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_signing_challenges")),
        sa.UniqueConstraint("id", "party_id", name="uq_signing_challenges_id_party_id"),
    )
    op.create_index(
        "uq_signing_challenges_open_party",
        "signing_challenges",
        ["party_id"],
        unique=True,
        postgresql_where=sa.text("consumed_at IS NULL AND revoked_at IS NULL"),
    )
    op.create_table(
        "contract_signatures",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("party_id", sa.UUID(), nullable=False),
        sa.Column("challenge_id", sa.UUID(), nullable=False),
        sa.Column("kyc_verification_id", sa.UUID(), nullable=True),
        sa.Column(
            "method", sa.String(length=16), server_default=sa.text("'email_otp'"), nullable=False
        ),
        sa.Column("signed_content_hash", sa.String(length=64), nullable=False),
        sa.Column("signed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("evidence", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "method IN ('email_otp')", name=op.f("ck_contract_signatures_method_valid")
        ),
        sa.ForeignKeyConstraint(
            ["challenge_id", "party_id"],
            ["signing_challenges.id", "signing_challenges.party_id"],
            name="fk_contract_signatures_challenge_id_party_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["kyc_verification_id"],
            ["kyc_verifications.id"],
            name=op.f("fk_contract_signatures_kyc_verification_id"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["party_id"],
            ["contract_parties.id"],
            name=op.f("fk_contract_signatures_party_id"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_contract_signatures")),
        sa.UniqueConstraint("challenge_id", name=op.f("uq_contract_signatures_challenge_id")),
        sa.UniqueConstraint("party_id", name=op.f("uq_contract_signatures_party_id")),
    )


def downgrade() -> None:
    op.drop_table("contract_signatures")
    op.drop_index(
        "uq_signing_challenges_open_party",
        table_name="signing_challenges",
        postgresql_where=sa.text("consumed_at IS NULL AND revoked_at IS NULL"),
    )
    op.drop_table("signing_challenges")
    op.drop_index("ix_contract_parties_user_id_contract_version_id", table_name="contract_parties")
    op.drop_table("contract_parties")
    op.drop_index("ix_commissions_agent_id_status_created_at", table_name="commissions")
    op.drop_table("commissions")
    op.drop_index("ix_invoices_contract_id_status", table_name="invoices")
    op.drop_table("invoices")
    op.drop_table("contract_versions")
    op.drop_index(
        "uq_contracts_active_property",
        table_name="contracts",
        postgresql_where=sa.text(
            "status IN ('pending_signatures', 'signed') AND deleted_at IS NULL"
        ),
    )
    op.drop_index("ix_contracts_status_created_at", table_name="contracts")
    op.drop_index(
        "ix_contracts_signed_at",
        table_name="contracts",
        postgresql_where=sa.text("status = 'signed'"),
    )
    op.drop_index("ix_contracts_customer_id_created_at_id", table_name="contracts")
    op.drop_index("ix_contracts_agent_id_status_created_at_id", table_name="contracts")
    op.drop_table("contracts")
    op.drop_table("email_deliveries")
    op.drop_index("ix_outbox_events_status_available_at", table_name="outbox_events")
    op.drop_table("outbox_events")
    op.drop_index(
        "uq_listings_active_property",
        table_name="listings",
        postgresql_where=sa.text("status IN ('pending', 'approved') AND deleted_at IS NULL"),
    )
    op.drop_index("ix_listings_status_created_at_id", table_name="listings")
    op.drop_index(
        "ix_listings_public_search",
        table_name="listings",
        postgresql_where=sa.text("status = 'approved' AND deleted_at IS NULL"),
    )
    op.drop_index("ix_listings_agent_id_status_created_at_id", table_name="listings")
    op.drop_table("listings")
    op.drop_index("ix_properties_project_id_status", table_name="properties")
    op.drop_table("properties")
    op.drop_index("ix_jobs_status_created_at", table_name="jobs")
    op.drop_index("ix_jobs_requested_by_created_at", table_name="jobs")
    op.drop_table("jobs")
    op.drop_index(
        "uq_kyc_verifications_pending_customer",
        table_name="kyc_verifications",
        postgresql_where=sa.text("status = 'pending'"),
    )
    op.drop_index("ix_kyc_verifications_customer_id_created_at", table_name="kyc_verifications")
    op.drop_table("kyc_verifications")
    op.drop_table("role_permissions")
    op.drop_table("user_roles")
    op.drop_index("ix_projects_province_code_ward_code", table_name="projects")
    op.drop_table("projects")
    op.drop_table("files")
    op.drop_table("customers")
    op.drop_index(op.f("ix_password_reset_tokens_user_id"), table_name="password_reset_tokens")
    op.drop_table("password_reset_tokens")
    op.drop_index("ix_audit_logs_entity_type_entity_id_created_at", table_name="audit_logs")
    op.drop_index("ix_audit_logs_actor_user_id_created_at", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_table("agents")
    op.drop_table("users")
    op.drop_table("permissions")
    op.drop_table("roles")
