"""FastAPI dependency resolving the session cookie to an active user."""

from functools import cache

from fastapi import HTTPException, Request, status
from sqlalchemy.engine import Engine

from app.core.config import ConfigurationError
from app.core.constants import SESSION_COOKIE_NAME
from app.database.db import DatabaseOperationError, create_database_engine, session_scope
from app.services.auth_service import AuthenticatedUser, get_session_user

_NO_STORE = {"Cache-Control": "no-store"}


@cache
def get_auth_engine() -> Engine:
    """Lazily create one shared engine; only reached when a session cookie is present."""
    return create_database_engine()


def get_current_user(request: Request) -> AuthenticatedUser:
    """Synchronous dependency (runs in FastAPI's threadpool) for protected routes.

    Missing, malformed, tampered, expired, or revoked sessions and inactive users
    all receive the same 401. Configuration or database failures deny access
    with a generic 503. Neither response includes token or database details.
    """
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Authentication required.", headers=_NO_STORE)
    try:
        with session_scope(get_auth_engine()) as session:
            user = get_session_user(session, token)
    except (ConfigurationError, DatabaseOperationError):
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "Authentication is temporarily unavailable.", headers=_NO_STORE
        ) from None
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Authentication required.", headers=_NO_STORE)
    return user
