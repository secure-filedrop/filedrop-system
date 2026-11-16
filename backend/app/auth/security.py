"""Password hashing and session-token primitives; no database access here."""

from functools import cache
import hashlib
import re
import secrets

from pwdlib import PasswordHash
from pwdlib.exceptions import PwdlibError
from pwdlib.hashers.argon2 import Argon2Hasher

from app.core.constants import (
    EMAIL_MAX_LENGTH,
    PASSWORD_MAX_LENGTH,
    PASSWORD_MIN_LENGTH,
    SESSION_TOKEN_BYTES,
)

# Explicit Argon2id parameters (argon2-cffi's RFC 9106 low-memory profile:
# 64 MiB, 3 passes, 4 lanes). Stored hashes with other parameters are flagged
# for rehash on the next successful verification.
_password_hash = PasswordHash((Argon2Hasher(time_cost=3, memory_cost=65536, parallelism=4),))

_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_-]{%d}" % len(secrets.token_urlsafe(SESSION_TOKEN_BYTES)))
_EMAIL_PATTERN = re.compile(r"[^@\s]+@[^@\s]+")


class CredentialPolicyError(ValueError):
    """An input-policy failure whose message never includes the supplied value."""


def normalize_email(value: str) -> str:
    """Trim surrounding spaces and apply minimal shape checks; casing is preserved.

    Lookups compare lower(email), matching the users unique index.
    """
    email = value.strip() if isinstance(value, str) else ""
    if not email or len(email) > EMAIL_MAX_LENGTH or not _EMAIL_PATTERN.fullmatch(email):
        raise CredentialPolicyError("Enter a valid email address.")
    if any(ord(character) < 32 or ord(character) == 127 for character in email):
        raise CredentialPolicyError("Enter a valid email address.")
    return email


def validate_new_password(password: str) -> None:
    """Policy for passwords being set; never truncates or alters the value."""
    if not isinstance(password, str):
        raise CredentialPolicyError("Password must be text.")
    if len(password) < PASSWORD_MIN_LENGTH:
        raise CredentialPolicyError(f"Password must be at least {PASSWORD_MIN_LENGTH} characters.")
    if len(password) > PASSWORD_MAX_LENGTH:
        raise CredentialPolicyError(f"Password must be at most {PASSWORD_MAX_LENGTH} characters.")


def hash_password(password: str) -> str:
    validate_new_password(password)
    return _password_hash.hash(password)


def verify_password(password: str, password_hash: str) -> tuple[bool, str | None]:
    """Return (valid, replacement_hash). Malformed hashes and oversized input fail closed.

    A replacement hash is returned only for a valid password whose stored hash
    uses outdated parameters; the caller decides whether to persist it.
    """
    if not isinstance(password, str) or len(password) > PASSWORD_MAX_LENGTH:
        verify_dummy_password()
        return False, None
    try:
        return _password_hash.verify_and_update(password, password_hash)
    except (PwdlibError, ValueError, TypeError):
        return False, None


@cache
def _dummy_hash() -> str:
    return _password_hash.hash(secrets.token_urlsafe(32))


def verify_dummy_password(password: str = "") -> None:
    """Spend comparable hashing time for unknown accounts to reduce enumeration timing."""
    candidate = password if isinstance(password, str) and len(password) <= PASSWORD_MAX_LENGTH else ""
    _password_hash.verify(candidate, _dummy_hash())


def generate_session_token() -> str:
    """A fresh, server-generated opaque token with 256 bits of randomness."""
    return secrets.token_urlsafe(SESSION_TOKEN_BYTES)


def is_well_formed_session_token(token: object) -> bool:
    return isinstance(token, str) and _TOKEN_PATTERN.fullmatch(token) is not None


def hash_session_token(token: str) -> bytes:
    """SHA-256 digest stored instead of the raw token.

    A fast hash is appropriate because tokens are long and random, not
    user-chosen; only this digest reaches the database.
    """
    return hashlib.sha256(token.encode("ascii")).digest()
