"""Shared PostgreSQL integration-test setup using application boundaries."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from textwrap import dedent
from uuid import uuid7

from alembic.config import Config
from pydantic import SecretStr

from homesearch.adapters.database import (
    create_database_engine,
    resolve_database_url,
)
from homesearch.config import LoadedConfiguration, OperationalSettings, load_configuration

DEFAULTS = Path("config/defaults.toml")
ALEMBIC_CONFIG = Path("alembic.ini")
CONFIGURATION_ATTRIBUTE = "homesearch_configuration"


def load_with_database_url(
    tmp_path: Path,
    database_url: str,
) -> LoadedConfiguration:
    """Load a test-only profile through the production configuration boundary."""

    tmp_path.mkdir(parents=True, exist_ok=True)
    profile = tmp_path / "integration-profile.toml"
    profile.write_text(
        dedent(
            """
            schema_version = 4
            config_id = "integration-profile"
            config_version = 1
            effective_from = 2026-07-30T00:00:00Z

            [[secret_references]]
            secret_id = "integration-store"
            setting = "database_url"
            required = true
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    return load_configuration(
        OperationalSettings(
            config_path=DEFAULTS,
            profile_path=profile,
            database_url=SecretStr(database_url),
        )
    )


def alembic_config(configuration: LoadedConfiguration) -> Config:
    """Inject a loaded configuration into the production Alembic environment."""

    config = Config(str(ALEMBIC_CONFIG))
    config.attributes[CONFIGURATION_ATTRIBUTE] = configuration
    return config


def _quote_database_name(name: str) -> str:
    if not name.isascii() or not name.replace("_", "").isalnum():
        raise ValueError("temporary database name is not safe")
    return f'"{name}"'


@contextmanager
def temporary_database(
    server_configuration: LoadedConfiguration,
    tmp_path: Path,
) -> Iterator[LoadedConfiguration]:
    """Create and drop one exact disposable PostgreSQL database."""

    database_name = f"homesearch_test_{uuid7().hex}"
    quoted_name = _quote_database_name(database_name)
    server_engine = create_database_engine(server_configuration)
    database_created = False
    try:
        with server_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
            connection.exec_driver_sql(f"CREATE DATABASE {quoted_name} TEMPLATE template0")
        database_created = True

        database_url = resolve_database_url(server_configuration).set(database=database_name)
        database_configuration = load_with_database_url(
            tmp_path / database_name,
            database_url.render_as_string(hide_password=False),
        )
        yield database_configuration
    finally:
        if database_created:
            with server_engine.connect().execution_options(
                isolation_level="AUTOCOMMIT"
            ) as connection:
                connection.exec_driver_sql(f"DROP DATABASE IF EXISTS {quoted_name} WITH (FORCE)")
        server_engine.dispose()
