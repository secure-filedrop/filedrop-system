"""Shared SQLAlchemy metadata for explicit, reviewed migrations."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
