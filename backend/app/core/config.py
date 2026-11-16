"""Read database configuration only when database work is requested."""

import os

from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import ArgumentError


class ConfigurationError(ValueError):
    """A configuration error safe to display without the supplied value."""


def parse_database_url(value: str, name: str = "DATABASE_URL") -> URL:
    """Accept PostgreSQL URLs and select the Psycopg 3 driver explicitly."""
    try:
        url = make_url(value)
        if url.drivername not in {"postgresql", "postgresql+psycopg"} or not url.database:
            raise ValueError
    except (ArgumentError, TypeError, ValueError):
        raise ConfigurationError(f"{name} must be a PostgreSQL URL with a database name.") from None
    return url.set(drivername="postgresql+psycopg")


def get_database_url(name: str = "DATABASE_URL") -> URL:
    """Never include the URL or credentials in a configuration error."""
    value = os.environ.get(name)
    if not value or not value.strip():
        raise ConfigurationError(f"{name} is required for database operations.")
    return parse_database_url(value, name)
