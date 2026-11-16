"""Explicit database engines and short-lived synchronous sessions."""

from collections.abc import Iterator
from contextlib import contextmanager
import re

from sqlalchemy import create_engine
from sqlalchemy.engine import Connection, Engine, URL
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import get_database_url


class DatabaseOperationError(RuntimeError):
    """A database failure without SQL parameters or connection details."""

    def __init__(self, sqlstate: str | None = None):
        super().__init__("Database operation failed.")
        self.sqlstate = sqlstate


def create_database_engine(url: URL | None = None) -> Engine:
    """Create a lazy engine; this does not connect or create any tables."""
    return create_engine(
        url if url is not None else get_database_url(),
        pool_pre_ping=True,
        hide_parameters=True,
        connect_args={"connect_timeout": 5},
    )


@contextmanager
def session_scope(bind: Engine | Connection) -> Iterator[Session]:
    """Services commit explicitly; closing rolls back uncommitted work."""
    try:
        with Session(bind, expire_on_commit=False, close_resets_only=False) as session:
            yield session
    except SQLAlchemyError as error:
        # Driver errors may contain row values even with hide_parameters=True.
        sqlstate = getattr(getattr(error, "orig", None), "sqlstate", None)
        if not isinstance(sqlstate, str) or not re.fullmatch(r"[0-9A-Z]{5}", sqlstate):
            sqlstate = None
        raise DatabaseOperationError(sqlstate) from None
