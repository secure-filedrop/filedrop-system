"""Add file metadata and audit logs without changing existing user rows."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20261108_02"
down_revision = "20261108_01"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "files",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("owner_user_id", sa.Integer(), nullable=False),
        sa.Column("original_filename", sa.Text(), nullable=False),
        sa.Column("stored_filename", sa.String(255), nullable=False),
        sa.Column("storage_key", sa.Text(), nullable=False),
        sa.Column("storage_type", sa.String(16), server_default=sa.text("'local'"), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=False),
        sa.Column("content_type", sa.String(255), server_default=sa.text("'application/octet-stream'"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("length(original_filename) > 0", name="ck_files_original_filename_nonempty"),
        sa.CheckConstraint("length(stored_filename) > 0", name="ck_files_stored_filename_nonempty"),
        sa.CheckConstraint("length(storage_key) > 0", name="ck_files_storage_key_nonempty"),
        sa.CheckConstraint("storage_type = 'local'", name="ck_files_storage_type"),
        sa.CheckConstraint("file_size >= 0", name="ck_files_size_nonnegative"),
        sa.CheckConstraint("length(content_type) > 0", name="ck_files_content_type_nonempty"),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], name="fk_files_owner_user_id_users", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("storage_type", "storage_key", name="uq_files_storage_location"),
        sa.UniqueConstraint("stored_filename", name="uq_files_stored_filename"),
    )
    op.create_index("ix_files_owner_user_id", "files", ["owner_user_id"])
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("file_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("ip_address", postgresql.INET(), nullable=True),
        sa.Column("details", postgresql.JSONB(none_as_null=False), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("action = btrim(action) AND length(action) > 0", name="ck_audit_logs_action"),
        sa.CheckConstraint("jsonb_typeof(details) = 'object'", name="ck_audit_logs_details_object"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_audit_logs_user_id_users", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["file_id"], ["files.id"], name="fk_audit_logs_file_id_files", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_file_id", "audit_logs", ["file_id"])


def downgrade():
    op.drop_table("audit_logs")
    op.drop_table("files")
