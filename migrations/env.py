"""Alembic runtime wired to Homesearch configuration and database adapters."""

from __future__ import annotations

from alembic import context
from alembic.config import Config
from alembic.script import ScriptDirectory

from homesearch.adapters.database import (
    create_database_engine,
    resolve_database_url,
)
from homesearch.config import LoadedConfiguration, load_configuration

_CONFIGURATION_ATTRIBUTE = "homesearch_configuration"
target_metadata = None


def _has_revisions(alembic_config: Config) -> bool:
    return bool(ScriptDirectory.from_config(alembic_config).get_heads())


def _load_migration_configuration(alembic_config: Config) -> LoadedConfiguration:
    injected = alembic_config.attributes.get(_CONFIGURATION_ATTRIBUTE)
    if injected is None:
        return load_configuration()
    if not isinstance(injected, LoadedConfiguration):
        raise RuntimeError("Injected migration configuration is invalid")
    return injected


def run_migrations_offline() -> None:
    """Render PostgreSQL SQL without opening a database connection."""

    configuration = _load_migration_configuration(context.config)
    context.configure(
        url=resolve_database_url(configuration),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        transactional_ddl=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations through the accepted synchronous engine boundary."""

    configuration = _load_migration_configuration(context.config)
    engine = create_database_engine(configuration)
    try:
        with engine.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                transactional_ddl=True,
            )

            with context.begin_transaction():
                context.run_migrations()
    finally:
        engine.dispose()


if _has_revisions(context.config):
    if context.is_offline_mode():
        run_migrations_offline()
    else:
        run_migrations_online()
