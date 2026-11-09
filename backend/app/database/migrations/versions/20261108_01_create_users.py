"""Create the users foundation; no accounts or other planned tables are seeded."""

from alembic import op
import sqlalchemy as sa

revision = "20261108_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("role", sa.String(16), server_default=sa.text("'user'"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("email = btrim(email) AND length(email) > 0", name="ck_users_email_spaces"),
        sa.CheckConstraint("length(password_hash) > 0", name="ck_users_password_hash_nonempty"),
        sa.CheckConstraint("role IN ('user', 'admin')", name="ck_users_role"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("uq_users_email_lower", "users", [sa.text("lower(email)")], unique=True)


def downgrade():
    op.drop_index("uq_users_email_lower", table_name="users")
    op.drop_table("users")
