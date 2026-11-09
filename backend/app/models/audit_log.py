"""Structured audit records, including events without a known actor or file."""

from datetime import datetime
from ipaddress import IPv4Address, IPv6Address
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Identity, Index, Integer, String, func, text
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.file import File  # noqa: F401 -- registers file and user targets


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        CheckConstraint("action = btrim(action) AND length(action) > 0", name="ck_audit_logs_action"),
        CheckConstraint("jsonb_typeof(details) = 'object'", name="ck_audit_logs_details_object"),
        Index("ix_audit_logs_user_id", "user_id"),
        Index("ix_audit_logs_file_id", "file_id"),
    )

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", name="fk_audit_logs_user_id_users", ondelete="RESTRICT"), nullable=True,
    )
    file_id: Mapped[int | None] = mapped_column(
        ForeignKey("files.id", name="fk_audit_logs_file_id_files", ondelete="RESTRICT"), nullable=True,
    )
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    ip_address: Mapped[IPv4Address | IPv6Address | None] = mapped_column(INET, nullable=True)
    details: Mapped[dict[str, Any]] = mapped_column(
        # Bind explicit None as JSON null so the object check rejects it, rather
        # than silently treating it as omission and using the default object.
        JSONB(none_as_null=False), nullable=False, server_default=text("'{}'::jsonb"),
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
