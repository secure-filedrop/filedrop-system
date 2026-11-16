"""Unit checks plus opt-in integration tests on an empty disposable PostgreSQL DB."""

import os
from pathlib import Path
import subprocess
import sys

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import JSON, delete, inspect, null, select, text
from sqlalchemy.exc import InvalidRequestError

from app.core.config import ConfigurationError, get_database_url, parse_database_url
from app.database.db import DatabaseOperationError, create_database_engine, session_scope
from app.models.user import User
from app.models.file import File
from app.models.audit_log import AuditLog

BACKEND = Path(__file__).resolve().parents[1]


def confirmed_test_url(value, reset_consent, development_url=None):
    """Refuse unsafe targets before creating an engine or running any SQL."""
    if reset_consent != "1":
        raise RuntimeError("Set FILEDROP_ALLOW_TEST_DATABASE_RESET=1 only for a disposable test database.")
    url = parse_database_url(value, "TEST_DATABASE_URL")
    if url.database != "filedrop_test" and not url.database.startswith("filedrop_test_"):
        raise RuntimeError("Integration tests require a database named filedrop_test or filedrop_test_*.")
    if development_url:
        development = parse_database_url(development_url)

        def target(candidate):
            host = candidate.query.get("host") or candidate.host or "localhost"
            if host in {"127.0.0.1", "::1"}:
                host = "localhost"
            port = str(candidate.query.get("port") or candidate.port or 5432)
            return host, port, candidate.database

        if target(url) == target(development):
            raise RuntimeError("Test and development database targets must be different.")
    return url


def require_empty_database(connection):
    has_relations = connection.scalar(text("""
        WITH application_namespaces AS (
            SELECT oid FROM pg_namespace
            WHERE nspname !~ '^pg_' AND nspname <> 'information_schema'
        )
        SELECT EXISTS (
            SELECT 1 FROM pg_class WHERE relnamespace IN (SELECT oid FROM application_namespaces)
            UNION ALL
            SELECT 1 FROM pg_proc WHERE pronamespace IN (SELECT oid FROM application_namespaces)
            UNION ALL
            SELECT 1 FROM pg_type WHERE typnamespace IN (SELECT oid FROM application_namespaces)
        )
    """))
    if has_relations:
        raise RuntimeError("Test database must be empty; refusing to alter existing objects.")


def alembic_config(connection):
    config = Config(str(BACKEND / "alembic.ini"))
    config.attributes["connection"] = connection
    return config


@pytest.fixture(scope="module")
def migrated_engine():
    value = os.environ.get("TEST_DATABASE_URL")
    if not value:
        pytest.skip("PostgreSQL integration tests require TEST_DATABASE_URL and explicit reset consent.")
    url = confirmed_test_url(
        value, os.environ.get("FILEDROP_ALLOW_TEST_DATABASE_RESET"), os.environ.get("DATABASE_URL")
    )
    engine = create_database_engine(url)
    migrated = False
    try:
        with engine.begin() as connection:
            if connection.dialect.server_version_info[0] != 18:
                raise RuntimeError("Integration tests require PostgreSQL major version 18.")
            require_empty_database(connection)
            command.upgrade(alembic_config(connection), "head")
        migrated = True
        yield engine
    finally:
        try:
            if migrated:
                # Only remove objects this fixture created in the initially empty DB.
                with engine.begin() as connection:
                    command.downgrade(alembic_config(connection), "base")
                    connection.exec_driver_sql("DROP TABLE alembic_version")
        finally:
            engine.dispose()


@pytest.fixture
def database(migrated_engine):
    try:
        yield migrated_engine
    finally:
        with migrated_engine.begin() as connection:
            connection.execute(delete(AuditLog))
            connection.execute(delete(File))
            connection.execute(delete(User))


@pytest.mark.parametrize("value", ["", "not-a-url", "sqlite:///test.db", "postgresql://localhost", "postgresql://user:sentinel@localhost:bad/test"])
def test_invalid_configuration_is_sanitized(value):
    with pytest.raises(ConfigurationError) as error:
        parse_database_url(value)
    assert str(error.value) == "DATABASE_URL must be a PostgreSQL URL with a database name."
    assert error.value.__suppress_context__


def test_missing_configuration_and_lazy_engine(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(ConfigurationError, match="required for database operations"):
        get_database_url()
    monkeypatch.setenv("DATABASE_URL", "postgresql://example:sentinel@127.0.0.1:1/filedrop")
    url = get_database_url()
    assert url.drivername == "postgresql+psycopg"
    engine = create_database_engine(url)
    try:
        assert engine.pool.checkedout() == 0  # No attempted connection to port 1.
        assert engine.hide_parameters
    finally:
        engine.dispose()


def test_migration_configuration_failure_does_not_print_url(monkeypatch):
    marker = "synthetic-private-marker"
    monkeypatch.setenv("DATABASE_URL", f"postgresql://example:{marker}@localhost:bad/filedrop")
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=BACKEND, capture_output=True, text=True,
    )
    output = result.stdout + result.stderr
    assert result.returncode != 0
    assert "Database migration failed" in output
    assert marker not in output
    assert "postgresql://" not in output


@pytest.mark.parametrize("url, consent, dev", [
    ("postgresql:///filedrop_test", None, None),
    ("postgresql:///filedrop_test", "0", None),
    ("postgresql:///filedrop", "1", None),
    ("postgresql:///filedrop_test_backup_prod", "1", "postgresql:///filedrop_test_backup_prod"),
    ("postgresql://127.0.0.1/filedrop_test", "1", "postgresql://localhost:5432/filedrop_test"),
    ("postgresql://unused/filedrop_test?host=127.0.0.1&port=55432", "1", "postgresql://localhost:55432/filedrop_test"),
])
def test_guard_refuses_unconfirmed_or_development_targets(url, consent, dev):
    with pytest.raises(RuntimeError):
        confirmed_test_url(url, consent, dev)


def test_guard_accepts_explicit_disposable_target():
    url = confirmed_test_url("postgresql:///filedrop_test_local", "1", "postgresql:///filedrop")
    assert url.database == "filedrop_test_local"


def test_migration_matches_models_and_documented_tables(migrated_engine):
    with migrated_engine.begin() as connection:
        assert set(inspect(connection).get_table_names()) == {"users", "files", "audit_logs", "alembic_version"}
        assert {c["name"] for c in inspect(connection).get_columns("users")} == {
            "id", "email", "password_hash", "role", "is_active", "created_at"
        }
        assert {c["name"] for c in inspect(connection).get_columns("files")} == {
            "id", "owner_user_id", "original_filename", "stored_filename", "storage_key",
            "storage_type", "file_size", "content_type", "expires_at", "is_deleted", "created_at",
        }
        assert {c["name"] for c in inspect(connection).get_columns("audit_logs")} == {
            "id", "user_id", "file_id", "action", "ip_address", "details", "created_at",
        }
        command.check(alembic_config(connection))
        with pytest.raises(RuntimeError, match="must be empty"):
            require_empty_database(connection)
        assert "users" in inspect(connection).get_table_names()


def test_user_defaults_commit_and_session_close(database):
    with session_scope(database) as session:
        user = User(email="Example@example.test", password_hash="synthetic-test-hash")
        session.add(user)
        session.commit()
        assert user.id > 0
        assert user.role == "user"
        assert user.is_active is True
        assert user.created_at.utcoffset() is not None
    with pytest.raises(InvalidRequestError):
        session.execute(select(User))
    with session_scope(database) as fresh:
        assert fresh.scalar(select(User.email)) == "Example@example.test"
    assert database.pool.checkedout() == 0


@pytest.mark.parametrize("definition", [
    "CREATE TYPE test_only_type AS ENUM ('example')",
    "CREATE FUNCTION test_only_function() RETURNS integer LANGUAGE sql AS 'SELECT 1'",
])
def test_empty_database_guard_includes_types_and_functions(migrated_engine, definition):
    # These tables were created by this fixture in the confirmed empty test DB.
    # Roll back all DDL so the migration/model test schema is restored afterward.
    with migrated_engine.connect() as connection:
        transaction = connection.begin()
        try:
            for table in ("audit_logs", "files", "users", "alembic_version"):
                connection.exec_driver_sql(f"DROP TABLE {table}")
            require_empty_database(connection)
            connection.exec_driver_sql(definition)
            with pytest.raises(RuntimeError, match="must be empty"):
                require_empty_database(connection)
        finally:
            transaction.rollback()


def test_case_insensitive_email_uniqueness_hides_row_values(database):
    with session_scope(database) as session:
        session.add(User(email="Existing@example.test", password_hash="synthetic-test-hash"))
        session.commit()
    with pytest.raises(DatabaseOperationError) as error:
        with session_scope(database) as session:
            session.add(User(email="existing@EXAMPLE.test", password_hash="synthetic-private-marker"))
            session.commit()
    assert str(error.value) == "Database operation failed."
    assert error.value.sqlstate == "23505"  # PostgreSQL unique_violation.
    assert error.value.__suppress_context__
    assert database.pool.checkedout() == 0


def test_connection_failure_uses_generic_error(database):
    engine = create_database_engine(database.url.set(database="filedrop_missing_database"))
    try:
        with pytest.raises(DatabaseOperationError) as error:
            with session_scope(engine) as session:
                session.execute(text("SELECT 1"))
        assert str(error.value) == "Database operation failed."
        # libpq connection failures may omit SQLSTATE; do not parse error text.
        assert error.value.sqlstate in {None, "3D000"}
        assert error.value.__suppress_context__
    finally:
        engine.dispose()


@pytest.mark.parametrize("changes", [
    {"email": ""}, {"email": " spaced@example.test"}, {"email": "spaced@example.test "},
    {"email": "x" * 321}, {"email": None}, {"password_hash": ""},
    {"password_hash": None}, {"role": "superadmin"},
])
def test_user_constraints_reject_invalid_rows(database, changes):
    values = {"email": "valid@example.test", "password_hash": "synthetic-test-hash"}
    values.update(changes)
    with pytest.raises(DatabaseOperationError):
        with session_scope(database) as session:
            session.add(User(**values))
            session.commit()
    with session_scope(database) as session:
        assert session.scalar(select(User)) is None


@pytest.mark.parametrize("raise_error", [False, True])
def test_uncommitted_work_is_rolled_back(database, raise_error):
    def work():
        with session_scope(database) as session:
            session.add(User(email="rollback@example.test", password_hash="synthetic-test-hash"))
            session.flush()
            if raise_error:
                raise ValueError("caller failure")
    if raise_error:
        with pytest.raises(ValueError, match="caller failure"):
            work()
    else:
        work()
    with session_scope(database) as session:
        assert session.scalar(select(User)) is None
    assert database.pool.checkedout() == 0


def create_owner(engine):
    with session_scope(engine) as session:
        user = User(email="owner@example.test", password_hash="synthetic-test-hash")
        session.add(user)
        session.commit()
        return user.id


def file_record(owner_id, **changes):
    values = dict(
        owner_user_id=owner_id, original_filename="example.txt",
        stored_filename="stored-example.txt", storage_key="stored-example.txt", file_size=0,
    )
    values.update(changes)
    return File(**values)


def test_file_defaults_and_metadata_round_trip(database):
    owner_id = create_owner(database)
    with session_scope(database) as session:
        item = file_record(owner_id)
        session.add(item)
        session.commit()
        assert item.id > 0
        assert item.storage_type == "local"
        assert item.content_type == "application/octet-stream"
        assert item.file_size == 0
        assert item.is_deleted is False
        assert item.expires_at is None
        assert item.created_at.utcoffset() is not None
    with session_scope(database) as session:
        saved = session.scalar(select(File))
        assert saved.owner_user_id == owner_id
        assert saved.original_filename == "example.txt"


@pytest.mark.parametrize("changes", [
    {"original_filename": ""}, {"stored_filename": ""}, {"storage_key": ""},
    {"file_size": -1}, {"file_size": None}, {"storage_type": "s3"},
    {"content_type": ""}, {"stored_filename": "x" * 256}, {"owner_user_id": None},
])
def test_file_constraints(database, changes):
    owner_id = create_owner(database)
    with pytest.raises(DatabaseOperationError):
        with session_scope(database) as session:
            session.add(file_record(owner_id, **changes))
            session.commit()
    with session_scope(database) as session:
        assert session.scalar(select(File)) is None


def test_storage_location_must_be_unique(database):
    owner_id = create_owner(database)
    with session_scope(database) as session:
        session.add(file_record(owner_id))
        session.commit()
    with pytest.raises(DatabaseOperationError) as error:
        with session_scope(database) as session:
            session.add(file_record(owner_id, original_filename="another.txt", stored_filename="another-stored.txt"))
            session.commit()
    assert error.value.sqlstate == "23505"


def test_stored_filename_must_be_unique(database):
    owner_id = create_owner(database)
    with session_scope(database) as session:
        session.add(file_record(owner_id))
        session.commit()
    with pytest.raises(DatabaseOperationError) as error:
        with session_scope(database) as session:
            session.add(file_record(owner_id, storage_key="another-key"))
            session.commit()
    assert error.value.sqlstate == "23505"


def test_original_display_names_may_repeat(database):
    owner_id = create_owner(database)
    with session_scope(database) as session:
        session.add_all([
            file_record(owner_id),
            file_record(owner_id, stored_filename="another-stored.txt", storage_key="another-key"),
        ])
        session.commit()
    with session_scope(database) as session:
        assert session.scalars(select(File.original_filename)).all() == ["example.txt", "example.txt"]


@pytest.mark.parametrize("model, values", [
    (File, dict(owner_user_id=2147483647, original_filename="a", stored_filename="a", storage_key="a", file_size=1)),
    (AuditLog, dict(action="login_success", user_id=2147483647)),
    (AuditLog, dict(action="file_downloaded", file_id=2147483647)),
])
def test_non_null_foreign_keys_must_exist(database, model, values):
    with pytest.raises(DatabaseOperationError) as error:
        with session_scope(database) as session:
            session.add(model(**values))
            session.commit()
    assert error.value.sqlstate == "23503"


def test_audit_allows_unknown_actor_and_missing_file(database):
    with session_scope(database) as session:
        event = AuditLog(action="login_failed")
        session.add(event)
        session.commit()
        assert event.user_id is None
        assert event.file_id is None
        assert event.ip_address is None
        assert event.details == {}
        assert event.created_at.utcoffset() is not None


@pytest.mark.parametrize("address", ["198.51.100.10", "2001:db8::1"])
def test_audit_ip_and_structured_details_round_trip(database, address):
    details = {"reason": "unknown_user", "attempt": 1, "flags": ["example"], "accepted": False}
    with session_scope(database) as session:
        event = AuditLog(action="login_failed", ip_address=address, details=details)
        session.add(event)
        session.commit()
        event_id = event.id
    with session_scope(database) as session:
        event = session.get(AuditLog, event_id)
        assert str(event.ip_address) == address
        assert event.details == details


@pytest.mark.parametrize("changes", [
    {"action": ""}, {"action": " spaced"}, {"action": "x" * 65},
    {"ip_address": "not-an-address"}, {"details": []}, {"details": "text"},
    {"details": None}, {"details": JSON.NULL}, {"details": null()},
])
def test_audit_constraints(database, changes):
    values = {"action": "login_failed"}
    values.update(changes)
    with pytest.raises(DatabaseOperationError):
        with session_scope(database) as session:
            session.add(AuditLog(**values))
            session.commit()


def test_soft_delete_retains_audit_and_hard_delete_is_restricted(database):
    owner_id = create_owner(database)
    with session_scope(database) as session:
        item = file_record(owner_id)
        session.add(item)
        session.flush()
        event = AuditLog(user_id=owner_id, file_id=item.id, action="file_uploaded")
        session.add(event)
        session.commit()
        item_id, event_id = item.id, event.id
        item.is_deleted = True
        session.get(User, owner_id).is_active = False
        session.commit()
    with session_scope(database) as session:
        event = session.get(AuditLog, event_id)
        assert event.user_id == owner_id and event.file_id == item_id
        assert session.get(File, item_id).is_deleted is True
    for model, record_id in ((File, item_id), (User, owner_id)):
        with pytest.raises(DatabaseOperationError) as error:
            with session_scope(database) as session:
                session.delete(session.get(model, record_id))
                session.commit()
        assert error.value.sqlstate == "23001"  # PostgreSQL restrict_violation on hard delete.


def test_file_audit_migration_preserves_existing_user_rows(database):
    with database.begin() as connection:
        command.downgrade(alembic_config(connection), "20261108_01")
        assert set(inspect(connection).get_table_names()) == {"users", "alembic_version"}
        owner_id = connection.scalar(
            User.__table__.insert().values(email="retained@example.test", password_hash="synthetic-test-hash").returning(User.id)
        )
        command.upgrade(alembic_config(connection), "head")
        assert connection.scalar(select(User.email).where(User.id == owner_id)) == "retained@example.test"
        command.check(alembic_config(connection))
        command.downgrade(alembic_config(connection), "20261108_01")
        assert connection.scalar(select(User.email).where(User.id == owner_id)) == "retained@example.test"
        command.upgrade(alembic_config(connection), "head")
