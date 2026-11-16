"""Session lifecycle and initial-administrator bootstrap (Issue #12 foundation).

Write helpers flush but do not commit, so a later service operation (for
example login plus its audit event) can commit them in one transaction.
`create_initial_admin` is a complete operation and commits itself.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from sqlalchemy import delete, exists, func, insert, or_, select, text, update
from sqlalchemy.orm import Session

from app.auth.security import (
    generate_session_token,
    hash_password,
    hash_session_token,
    is_well_formed_session_token,
    normalize_email,
)
from app.core.constants import SESSION_LIFETIME_MINUTES
from app.models.auth_session import AuthSession
from app.models.user import User

# Arbitrary application-specific key serializing concurrent bootstrap runs.
_INITIAL_ADMIN_LOCK_KEY = 0x46494C4544524F50  # "FILEDROP"


class InitialAdminExistsError(RuntimeError):
    def __init__(self):
        super().__init__("An administrator account already exists; no account was created.")


class AccountExistsError(RuntimeError):
    def __init__(self):
        super().__init__("An account with this email already exists; no account was created.")


@dataclass(frozen=True)
class NewSession:
    """The raw token is returned once for the cookie and is never stored."""

    token: str = field(repr=False)  # Keep the token out of logs and tracebacks.
    session_id: int
    expires_at: datetime


@dataclass(frozen=True)
class AuthenticatedUser:
    """The minimal identity exposed to routes; never includes password data."""

    id: int
    email: str
    role: str
    session_id: int


def create_session(session: Session, user_id: int) -> NewSession:
    """Create a fresh session for an already-authenticated user (caller commits)."""
    token = generate_session_token()
    row = session.execute(
        insert(AuthSession)
        .values(
            user_id=user_id,
            token_hash=hash_session_token(token),
            expires_at=func.now() + timedelta(minutes=SESSION_LIFETIME_MINUTES),
        )
        .returning(AuthSession.id, AuthSession.expires_at)
    ).one()
    return NewSession(token=token, session_id=row.id, expires_at=row.expires_at)


def get_session_user(session: Session, token: object) -> AuthenticatedUser | None:
    """Return the active user for an unexpired, unrevoked session, or None."""
    if not is_well_formed_session_token(token):
        return None
    row = session.execute(
        select(AuthSession.id, User.id.label("user_id"), User.email, User.role)
        .join(User, User.id == AuthSession.user_id)
        .where(
            AuthSession.token_hash == hash_session_token(token),
            AuthSession.revoked_at.is_(None),
            AuthSession.expires_at > func.now(),
            User.is_active.is_(True),
        )
    ).one_or_none()
    if row is None:
        return None
    return AuthenticatedUser(id=row.user_id, email=row.email, role=row.role, session_id=row.id)


def revoke_session(session: Session, token: object) -> bool:
    """Revoke one session by its token (caller commits). True if a live row changed."""
    if not is_well_formed_session_token(token):
        return False
    result = session.execute(
        update(AuthSession)
        .where(AuthSession.token_hash == hash_session_token(token), AuthSession.revoked_at.is_(None))
        .values(revoked_at=func.now())
    )
    return result.rowcount == 1


def revoke_all_user_sessions(session: Session, user_id: int) -> int:
    """Revoke every unrevoked session for a user (admin action, password change/reset)."""
    result = session.execute(
        update(AuthSession)
        .where(AuthSession.user_id == user_id, AuthSession.revoked_at.is_(None))
        .values(revoked_at=func.now())
    )
    return result.rowcount


def delete_expired_sessions(session: Session) -> int:
    """Remove rows that can no longer authenticate: expired or revoked (caller commits)."""
    result = session.execute(
        delete(AuthSession).where(or_(AuthSession.expires_at <= func.now(), AuthSession.revoked_at.is_not(None)))
    )
    return result.rowcount


def create_initial_admin(session: Session, email: str, password: str) -> int:
    """Create the first administrator; refuses if any administrator exists. Commits."""
    email = normalize_email(email)
    password_hash = hash_password(password)  # Hash before taking the lock.
    session.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": _INITIAL_ADMIN_LOCK_KEY})
    if session.scalar(select(exists().where(User.role == "admin"))):
        raise InitialAdminExistsError()
    if session.scalar(select(exists().where(func.lower(User.email) == func.lower(email)))):
        raise AccountExistsError()
    user = User(email=email, password_hash=password_hash, role="admin")
    session.add(user)
    session.commit()
    return user.id
