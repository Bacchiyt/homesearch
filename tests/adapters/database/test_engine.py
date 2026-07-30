"""Tests for safe synchronous PostgreSQL engine construction."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest
from pydantic import SecretStr
from sqlalchemy.engine import Engine

from homesearch.adapters.database import (
    DatabaseConfigurationError,
    create_database_engine,
    resolve_database_url,
)
from homesearch.config import LoadedConfiguration, OperationalSettings, load_configuration

DEFAULTS = Path("config/defaults.toml")


def _load_with_database_url(
    tmp_path: Path,
    database_url: str,
) -> LoadedConfiguration:
    profile = tmp_path / "database-profile.toml"
    profile.write_text(
        dedent(
            """
            schema_version = 4
            config_id = "database-profile"
            config_version = 1
            effective_from = 2026-07-30T00:00:00Z

            [[secret_references]]
            secret_id = "primary-store"
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


def test_database_url_is_resolved_by_setting_and_remains_redacted(
    tmp_path: Path,
) -> None:
    password = "synthetic-sensitive-password"
    configuration = _load_with_database_url(
        tmp_path,
        f"postgresql+psycopg://homesearch:{password}@localhost:5432/homesearch",
    )

    url = resolve_database_url(configuration)

    assert url.drivername == "postgresql+psycopg"
    assert url.database == "homesearch"
    assert password not in str(url)
    assert password not in repr(url)


def test_engine_construction_is_synchronous_and_does_not_connect(
    tmp_path: Path,
) -> None:
    configuration = _load_with_database_url(
        tmp_path,
        "postgresql+psycopg://homesearch:unused@does-not-exist.invalid:5432/homesearch",
    )

    engine = create_database_engine(configuration)

    try:
        assert isinstance(engine, Engine)
        assert engine.dialect.name == "postgresql"
        assert engine.dialect.driver == "psycopg"
        assert not engine.dialect.is_async
        assert "unused" not in repr(engine)
    finally:
        engine.dispose()


def test_missing_database_secret_reference_fails_safely() -> None:
    configuration = load_configuration(OperationalSettings(config_path=DEFAULTS))

    with pytest.raises(
        DatabaseConfigurationError,
        match="Database URL secret reference is not configured",
    ):
        create_database_engine(configuration)


def test_unresolved_optional_database_secret_fails_safely(tmp_path: Path) -> None:
    profile = tmp_path / "optional-database-profile.toml"
    profile.write_text(
        dedent(
            """
            schema_version = 4
            config_id = "optional-database-profile"
            config_version = 1
            effective_from = 2026-07-30T00:00:00Z

            [[secret_references]]
            secret_id = "optional-store"
            setting = "database_url"
            required = false
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    configuration = load_configuration(
        OperationalSettings(
            config_path=DEFAULTS,
            profile_path=profile,
        )
    )

    with pytest.raises(
        DatabaseConfigurationError,
        match="Database URL secret reference is unresolved",
    ):
        create_database_engine(configuration)


@pytest.mark.parametrize(
    "database_url",
    [
        "not-a-database-url-with-sensitive-content",
        "sqlite:///:memory:",
        "postgresql://homesearch:sensitive@localhost/homesearch",
        "postgresql+psycopg://homesearch:sensitive@localhost/",
        "postgresql+psycopg://homesearch:sensitive@localhost:not-a-port/homesearch",
    ],
)
def test_invalid_database_urls_fail_without_exposing_input(
    tmp_path: Path,
    database_url: str,
) -> None:
    configuration = _load_with_database_url(tmp_path, database_url)

    with pytest.raises(DatabaseConfigurationError) as error:
        create_database_engine(configuration)

    assert database_url not in str(error.value)
    assert "sensitive" not in str(error.value)
