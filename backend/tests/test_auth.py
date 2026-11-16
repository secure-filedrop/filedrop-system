"""Password, session, dependency, and bootstrap checks for the Issue #12 foundation.

Integration tests reuse the guarded disposable-database fixture from
test_database.py and skip without TEST_DATABASE_URL and reset consent.
"""

from datetime import timedelta
import importlib.util
from pathlib import Path
import secrets

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
import pytest
from sqlalchemy import delete, func, select, update

from app.auth import dependencies
from app.auth.security import (
    CredentialPolicyError,
    generate_session_token,
    hash_password,
    hash_session_token,
    is_well_formed_session_token,
    normalize_email,
    validate_new_password,
    verify_dummy_password,
    verify_password,
)
from app.core.constants import SESSION_COOKIE_NAME, SESSION_LIFETIME_MINUTES
from app.database.db import DatabaseOperationError, create_database_engine, session_scope
from app.models.auth_session import AuthSession
from app.models.user import User
from app.services.auth_service import (
    AccountExistsError,
    AuthenticatedUser,
    InitialAdminExistsError,
    create_initial_admin,
    create_session,
    delete_expired_sessions,
    get_session_user,
    revoke_all_user_sessions,
    revoke_session,
)
from test_database import migrated_engine  # noqa: F401 -- shared guarded fixture

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "create_initial_admin.py"
PASSWORD = "synthetic test passphrase"  # Test-only value, not a real credential.


def load_bootstrap_script():
    spec = importlib.util.spec_from_file_location("create_initial_admin", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# --- Password and token helpers (no database) ---------------------------------

def test_hash_uses_argon2id_and_verifies():
    stored = hash_password(PASSWORD)
    assert stored.startswith("$argon2id$v=19$m=65536,t=3,p=4$")
    assert PASSWORD not in stored
    assert verify_password(PASSWORD, stored) == (True, None)
    assert verify_password(PASSWORD + "x", stored) == (False, None)
    assert hash_password(PASSWORD) != stored  # Fresh random salt.


@pytest.mark.parametrize("password", ["", "x" * 14, "y" * 1025, None, b"bytes are not accepted"])
def test_new_password_policy_rejects_without_echoing(password):
    with pytest.raises(CredentialPolicyError) as error:
        hash_password(password)
    if isinstance(password, str) and password:
        assert password not in str(error.value)


def test_password_bounds_are_inclusive_and_never_truncated():
    validate_new_password("a" * 15)
    validate_new_password("b" * 1024)
    long_password = "p" * 200
    stored = hash_password(long_password)
    # Differences after bcrypt's 72-byte limit must still matter.
    assert verify_password(long_password[:-1] + "q", stored) == (False, None)
    assert verify_password(long_password[:72], stored) == (False, None)
    assert verify_password(long_password, stored)[0] is True


def test_outdated_parameters_return_rehash():
    weak = PasswordHash((Argon2Hasher(time_cost=1, memory_cost=8192, parallelism=1),)).hash(PASSWORD)
    valid, replacement = verify_password(PASSWORD, weak)
    assert valid is True
    assert replacement.startswith("$argon2id$v=19$m=65536,t=3,p=4$")
    assert verify_password(PASSWORD, replacement) == (True, None)
    assert verify_password("wrong" + PASSWORD, weak) == (False, None)


@pytest.mark.parametrize("stored", ["", "not-a-hash", "$2b$12$invalidbcryptstyle", "$argon2id$v=19$broken"])
def test_malformed_hashes_fail_closed(stored):
    assert verify_password(PASSWORD, stored) == (False, None)


def test_oversized_or_non_text_verification_input_fails_closed():
    stored = hash_password(PASSWORD)
    assert verify_password("z" * 1025, stored) == (False, None)
    assert verify_password(None, stored) == (False, None)
    verify_dummy_password(PASSWORD)  # Must not raise for unknown-account timing work.
    verify_dummy_password("z" * 5000)


def test_session_tokens_are_random_urlsafe_and_hashed():
    tokens = {generate_session_token() for _ in range(50)}
    assert len(tokens) == 50
    for token in tokens:
        assert len(token) == 43  # 32 random bytes = 256 bits.
        assert is_well_formed_session_token(token)
        digest = hash_session_token(token)
        assert len(digest) == 32 and token.encode() not in digest


@pytest.mark.parametrize("token", [None, "", "short", "a" * 42, "a" * 44, "a" * 42 + "=", "a" * 42 + "+", 123])
def test_malformed_session_tokens_are_rejected(token):
    assert not is_well_formed_session_token(token)


@pytest.mark.parametrize("value, expected", [
    ("Admin@Example.test", "Admin@Example.test"),
    ("  admin@example.test\n", "admin@example.test"),
])
def test_email_normalization_trims_and_preserves_case(value, expected):
    assert normalize_email(value) == expected


@pytest.mark.parametrize("value", ["", "   ", "no-at-sign", "a@b@c", "@example.test", "a@", "a b@example.test",
                                   "a\x00@example.test", "x" * 310 + "@example.test", None])
def test_invalid_emails_are_rejected(value):
    with pytest.raises(CredentialPolicyError, match="valid email"):
        normalize_email(value)


def test_new_session_repr_hides_token():
    from app.services.auth_service import NewSession
    token = generate_session_token()
    assert token not in repr(NewSession(token=token, session_id=1, expires_at=None))


# --- Dependency without a database --------------------------------------------

protected = FastAPI()


@protected.get("/protected")
def protected_route(user: AuthenticatedUser = Depends(dependencies.get_current_user)):
    return {"id": user.id, "email": user.email, "role": user.role}


@pytest.fixture
def no_engine(monkeypatch):
    def unavailable():
        raise AssertionError("A request without a cookie must not reach the database.")
    monkeypatch.setattr(dependencies, "get_auth_engine", unavailable)


def test_missing_cookie_is_401_without_database(no_engine):
    with TestClient(protected) as client:
        response = client.get("/protected")
    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required."}
    assert response.headers["cache-control"] == "no-store"


def test_missing_database_configuration_is_generic_503(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    dependencies.get_auth_engine.cache_clear()
    try:
        with TestClient(protected) as client:
            client.cookies.set(SESSION_COOKIE_NAME, generate_session_token())
            response = client.get("/protected")
    finally:
        dependencies.get_auth_engine.cache_clear()
    assert response.status_code == 503
    assert response.json() == {"detail": "Authentication is temporarily unavailable."}
    assert response.headers["cache-control"] == "no-store"


def test_health_still_needs_no_auth_or_database(monkeypatch):
    from app.main import app
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with TestClient(app) as client:
        assert client.get("/health").json() == {"status": "ok"}


# --- Bootstrap command without a database -------------------------------------

def test_bootstrap_accepts_no_arguments():
    script = load_bootstrap_script()
    with pytest.raises(SystemExit) as error:
        script.main(["--password", PASSWORD], interactive=True)
    assert error.value.code == 2


def test_bootstrap_refuses_non_interactive_input(capsys):
    script = load_bootstrap_script()
    def no_prompt(_):
        raise AssertionError("must not prompt")
    assert script.main([], read_line=no_prompt, read_secret=no_prompt, interactive=False) == 2
    assert "interactive terminal" in capsys.readouterr().err


def test_bootstrap_rejects_mismatched_confirmation(capsys):
    script = load_bootstrap_script()
    answers = iter([PASSWORD, PASSWORD + "!"])
    result = script.main([], read_line=lambda _: "admin@example.test",
                         read_secret=lambda _: next(answers), interactive=True)
    assert result == 1
    output = capsys.readouterr()
    assert "did not match" in output.err
    assert PASSWORD not in output.err + output.out


def test_bootstrap_without_database_url_creates_nothing(monkeypatch, capsys):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    script = load_bootstrap_script()
    result = script.main([], read_line=lambda _: "admin@example.test",
                         read_secret=lambda _: PASSWORD, interactive=True)
    assert result == 1
    output = capsys.readouterr()
    assert "DATABASE_URL is required" in output.err
    assert PASSWORD not in output.err + output.out


# --- PostgreSQL integration ----------------------------------------------------

@pytest.fixture
def database(migrated_engine):  # noqa: F811
    try:
        yield migrated_engine
    finally:
        with migrated_engine.begin() as connection:
            connection.execute(delete(AuthSession))
            connection.execute(delete(User))


def add_user(engine, email="member@example.test", **changes):
    with session_scope(engine) as session:
        user = User(email=email, password_hash=hash_password(PASSWORD), **changes)
        session.add(user)
        session.commit()
        return user.id


def new_session(engine, user_id):
    with session_scope(engine) as session:
        created = create_session(session, user_id)
        session.commit()
        return created


def lookup(engine, token):
    with session_scope(engine) as session:
        return get_session_user(session, token)


def test_create_session_stores_only_hash_with_fixed_expiry(database):
    user_id = add_user(database, email="Member@Example.test")
    created = new_session(database, user_id)
    with session_scope(database) as session:
        row = session.scalar(select(AuthSession))
        assert row.id == created.session_id
        assert row.token_hash == hash_session_token(created.token)
        assert created.token.encode() not in row.token_hash
        assert row.expires_at - row.created_at == timedelta(minutes=SESSION_LIFETIME_MINUTES)
        assert row.expires_at == created.expires_at and row.revoked_at is None
    user = lookup(database, created.token)
    assert user == AuthenticatedUser(id=user_id, email="Member@Example.test", role="user",
                                     session_id=created.session_id)
    assert not hasattr(user, "password_hash")


def test_each_session_gets_a_fresh_token(database):
    user_id = add_user(database)
    first, second = new_session(database, user_id), new_session(database, user_id)
    assert first.token != second.token
    assert lookup(database, first.token).session_id != lookup(database, second.token).session_id


def test_unknown_tampered_and_malformed_tokens_fail(database):
    created = new_session(database, add_user(database))
    tampered = created.token[:-1] + ("A" if created.token[-1] != "A" else "B")
    for token in [generate_session_token(), tampered, created.token + "x", "", None]:
        assert lookup(database, token) is None


def test_expired_session_fails(database):
    created = new_session(database, add_user(database))
    with session_scope(database) as session:
        session.execute(update(AuthSession).values(
            created_at=func.now() - timedelta(minutes=31), expires_at=func.now() - timedelta(seconds=1)))
        session.commit()
    assert lookup(database, created.token) is None


def test_revoked_session_cannot_be_replayed(database):
    created = new_session(database, add_user(database))
    with session_scope(database) as session:
        assert revoke_session(session, created.token) is True
        session.commit()
    with session_scope(database) as session:
        assert revoke_session(session, created.token) is False
        assert revoke_session(session, "malformed") is False
    assert lookup(database, created.token) is None


def test_uncommitted_revocation_is_rolled_back(database):
    created = new_session(database, add_user(database))
    with session_scope(database) as session:
        assert revoke_session(session, created.token) is True
    assert lookup(database, created.token) is not None


def test_deactivated_user_loses_existing_session(database):
    user_id = add_user(database)
    created = new_session(database, user_id)
    with session_scope(database) as session:
        session.execute(update(User).where(User.id == user_id).values(is_active=False))
        session.commit()
    assert lookup(database, created.token) is None


def test_revoke_all_affects_only_that_user(database):
    target, other = add_user(database), add_user(database, email="other@example.test")
    target_sessions = [new_session(database, target) for _ in range(3)]
    other_session = new_session(database, other)
    with session_scope(database) as session:
        assert revoke_all_user_sessions(session, target) == 3
        session.commit()
    assert all(lookup(database, item.token) is None for item in target_sessions)
    assert lookup(database, other_session.token).id == other


def test_delete_expired_sessions_keeps_live_ones(database):
    user_id = add_user(database)
    live, revoked, expired = (new_session(database, user_id) for _ in range(3))
    with session_scope(database) as session:
        revoke_session(session, revoked.token)
        session.execute(update(AuthSession).where(AuthSession.id == expired.session_id).values(
            created_at=func.now() - timedelta(hours=1), expires_at=func.now() - timedelta(minutes=30)))
        session.commit()
    with session_scope(database) as session:
        assert delete_expired_sessions(session) == 2
        session.commit()
    with session_scope(database) as session:
        assert session.scalars(select(AuthSession.id)).all() == [live.session_id]


def test_deleting_user_cascades_sessions(database):
    user_id = add_user(database)
    new_session(database, user_id)
    with session_scope(database) as session:
        session.execute(delete(User).where(User.id == user_id))
        session.commit()
        assert session.scalar(select(func.count()).select_from(AuthSession)) == 0


@pytest.mark.parametrize("changes", [
    {"token_hash": b"short"}, {"token_hash": None}, {"user_id": None}, {"user_id": 999999},
    {"expires_at": None}, {"expires_at": func.now()},
    {"revoked_at": func.now() - timedelta(minutes=1)},
])
def test_session_constraints_reject_invalid_rows(database, changes):
    values = {"user_id": add_user(database), "token_hash": secrets.token_bytes(32),
              "expires_at": func.now() + timedelta(minutes=30)}
    values.update(changes)
    with pytest.raises(DatabaseOperationError):
        with session_scope(database) as session:
            session.add(AuthSession(**values))
            session.commit()


def test_duplicate_token_hash_is_rejected(database):
    user_id = add_user(database)
    digest = secrets.token_bytes(32)
    with session_scope(database) as session:
        session.add(AuthSession(user_id=user_id, token_hash=digest, expires_at=func.now() + timedelta(minutes=1)))
        session.commit()
    with pytest.raises(DatabaseOperationError) as error:
        with session_scope(database) as session:
            session.add(AuthSession(user_id=user_id, token_hash=digest, expires_at=func.now() + timedelta(minutes=1)))
            session.commit()
    assert error.value.sqlstate == "23505"


def test_dependency_with_real_sessions(database, monkeypatch):
    monkeypatch.setattr(dependencies, "get_auth_engine", lambda: database)
    user_id = add_user(database, email="web@example.test")
    created = new_session(database, user_id)
    with TestClient(protected) as client:
        client.cookies.set(SESSION_COOKIE_NAME, created.token)
        ok = client.get("/protected")
        assert ok.status_code == 200
        assert ok.json() == {"id": user_id, "email": "web@example.test", "role": "user"}
        assert created.token not in ok.text
        with session_scope(database) as session:
            revoke_session(session, created.token)
            session.commit()
        denied = client.get("/protected")
        assert denied.status_code == 401
        assert denied.headers["cache-control"] == "no-store"
        client.cookies.set(SESSION_COOKIE_NAME, "tampered-value")
        assert client.get("/protected").status_code == 401


def test_dependency_database_failure_is_generic_503(database, monkeypatch):
    broken = create_database_engine(database.url.set(database="filedrop_missing_database"))
    monkeypatch.setattr(dependencies, "get_auth_engine", lambda: broken)
    try:
        with TestClient(protected) as client:
            client.cookies.set(SESSION_COOKIE_NAME, generate_session_token())
            response = client.get("/protected")
    finally:
        broken.dispose()
    assert response.status_code == 503
    assert response.json() == {"detail": "Authentication is temporarily unavailable."}
    assert "filedrop_missing_database" not in response.text


def test_initial_admin_created_once_with_argon2_hash(database):
    with session_scope(database) as session:
        admin_id = create_initial_admin(session, "  Admin@Example.test ", PASSWORD)
    with session_scope(database) as session:
        admin = session.get(User, admin_id)
        assert (admin.email, admin.role, admin.is_active) == ("Admin@Example.test", "admin", True)
        assert admin.password_hash.startswith("$argon2id$")
        assert verify_password(PASSWORD, admin.password_hash) == (True, None)
    with pytest.raises(InitialAdminExistsError):
        with session_scope(database) as session:
            create_initial_admin(session, "second@example.test", PASSWORD)
    with session_scope(database) as session:
        assert session.scalar(select(func.count()).select_from(User)) == 1


def test_initial_admin_refuses_existing_email_and_invalid_input(database):
    add_user(database, email="taken@example.test")
    with pytest.raises(AccountExistsError):
        with session_scope(database) as session:
            create_initial_admin(session, "TAKEN@example.test", PASSWORD)
    for email, password in [("bad-email", PASSWORD), ("ok@example.test", "too short")]:
        with pytest.raises(CredentialPolicyError):
            with session_scope(database) as session:
                create_initial_admin(session, email, password)
    with session_scope(database) as session:
        assert session.scalars(select(User.role)).all() == ["user"]


def test_bootstrap_script_end_to_end(database, monkeypatch, capsys):
    monkeypatch.setenv("DATABASE_URL", database.url.render_as_string(hide_password=False))
    script = load_bootstrap_script()
    prompts = []

    def read_line(prompt):
        prompts.append(prompt)
        return "script-admin@example.test"

    def read_secret(prompt):
        prompts.append(prompt)
        return PASSWORD

    assert script.main([], read_line=read_line, read_secret=read_secret, interactive=True) == 0
    assert prompts == ["Administrator email: ", "Password: ", "Confirm password: "]
    assert script.main([], read_line=read_line, read_secret=read_secret, interactive=True) == 1
    output = capsys.readouterr()
    assert "Created the initial administrator account." in output.out
    assert "already exists" in output.err
    assert PASSWORD not in output.out + output.err
    with session_scope(database) as session:
        assert session.scalars(select(User.email).where(User.role == "admin")).all() == [
            "script-admin@example.test"
        ]
