"""File metadata only; physical storage and permission checks are service tasks."""

from datetime import datetime

from sqlalchemy import (
    BigInteger, Boolean, CheckConstraint, DateTime, ForeignKey, Identity,
    Index, Integer, String, Text, UniqueConstraint, func, text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.user import User  # noqa: F401 -- registers the foreign-key target


class File(Base):
    __tablename__ = "files"
    __table_args__ = (
        CheckConstraint("length(original_filename) > 0", name="ck_files_original_filename_nonempty"),
        CheckConstraint("length(stored_filename) > 0", name="ck_files_stored_filename_nonempty"),
        CheckConstraint("length(storage_key) > 0", name="ck_files_storage_key_nonempty"),
        CheckConstraint("storage_type = 'local'", name="ck_files_storage_type"),
        CheckConstraint("file_size >= 0", name="ck_files_size_nonnegative"),
        CheckConstraint("length(content_type) > 0", name="ck_files_content_type_nonempty"),
        UniqueConstraint("storage_type", "storage_key", name="uq_files_storage_location"),
        UniqueConstraint("stored_filename", name="uq_files_stored_filename"),
        Index("ix_files_owner_user_id", "owner_user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    owner_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", name="fk_files_owner_user_id_users", ondelete="RESTRICT"), nullable=False,
    )
    original_filename: Mapped[str] = mapped_column(Text, nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str] = mapped_column(Text, nullable=False)
    storage_type: Mapped[str] = mapped_column(String(16), nullable=False, server_default=text("'local'"))
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    content_type: Mapped[str] = mapped_column(
        String(255), nullable=False, server_default=text("'application/octet-stream'"),
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
