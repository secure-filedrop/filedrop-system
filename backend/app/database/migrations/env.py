"""Run explicit migrations; importing the application never invokes this file."""

from alembic import context
from alembic.util import CommandError
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import ConfigurationError, get_database_url
from app.database.base import Base
from app.database.db import create_database_engine
from app.models.user import User  # noqa: F401 -- registers the implemented model
from app.models.file import File  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401

config = context.config


def migrate(connection):
    context.configure(
        connection=connection,
        target_metadata=Base.metadata,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations():
    if context.is_offline_mode():
        context.configure(
            url=get_database_url(),
            target_metadata=Base.metadata,
            literal_binds=True,
            dialect_opts={"paramstyle": "named"},
        )
        with context.begin_transaction():
            context.run_migrations()
        return

    # Tests supply a connection to the explicitly guarded disposable database.
    connection = config.attributes.get("connection")
    if connection is not None:
        migrate(connection)
        return

    engine = create_database_engine()
    try:
        with engine.connect() as connection:
            migrate(connection)
    finally:
        engine.dispose()


try:
    run_migrations()
except (ConfigurationError, SQLAlchemyError):
    raise CommandError("Database migration failed; check configuration and database access.") from None
