"""Safe construction of the accepted synchronous PostgreSQL engine."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.engine import URL, Engine, make_url
from sqlalchemy.exc import ArgumentError

from homesearch.config.models import LoadedConfiguration, SecretSetting

_POSTGRESQL_DRIVER = "postgresql+psycopg"


class DatabaseConfigurationError(RuntimeError):
    """Safe startup failure for unusable database connection configuration."""


def resolve_database_url(configuration: LoadedConfiguration) -> URL:
    """Resolve and validate the configured PostgreSQL URL without exposing it."""

    reference = next(
        (
            reference
            for reference in configuration.configuration.secret_references
            if reference.setting is SecretSetting.DATABASE_URL
        ),
        None,
    )
    if reference is None:
        raise DatabaseConfigurationError("Database URL secret reference is not configured")

    secret = configuration.get_secret(reference.secret_id)
    if secret is None:
        raise DatabaseConfigurationError("Database URL secret reference is unresolved")

    try:
        url = make_url(secret.get_secret_value())
        _ = url.port
    except ArgumentError, ValueError:
        raise DatabaseConfigurationError("Database URL is invalid") from None

    if url.drivername != _POSTGRESQL_DRIVER:
        raise DatabaseConfigurationError("Database URL must use the postgresql+psycopg driver")
    if not url.database:
        raise DatabaseConfigurationError("Database URL must name a database")
    return url


def create_database_engine(configuration: LoadedConfiguration) -> Engine:
    """Build a lazy synchronous engine; callers own connection/transaction scope."""

    return create_engine(
        resolve_database_url(configuration),
        pool_pre_ping=True,
    )
