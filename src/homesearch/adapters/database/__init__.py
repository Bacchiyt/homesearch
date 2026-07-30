"""Synchronous PostgreSQL connection boundary."""

from homesearch.adapters.database.engine import (
    DatabaseConfigurationError,
    create_database_engine,
    resolve_database_url,
)
from homesearch.adapters.database.schema import metadata
from homesearch.adapters.database.unit_of_work import SqlAlchemyUnitOfWork

__all__ = [
    "DatabaseConfigurationError",
    "SqlAlchemyUnitOfWork",
    "create_database_engine",
    "metadata",
    "resolve_database_url",
]
