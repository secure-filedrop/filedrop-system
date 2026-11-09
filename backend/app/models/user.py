"""The first implemented table from docs/database-schema.md."""

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Identity, Index, Integer, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("email = btrim(email) AND length(email) > 0", name="ck_users_email_spaces"),
        CheckConstraint("length(password_hash) > 0", name="ck_users_password_hash_nonempty"),
        CheckConstraint("role IN ('user', 'admin')", name="ck_users_role"),
    )

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False, server_default=text("'user'"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


Index("uq_users_email_lower", func.lower(User.email), unique=True)
