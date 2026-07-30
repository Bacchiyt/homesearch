"""PostgreSQL integration tests for the first migration-backed schema."""

from __future__ import annotations

import json
import os
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from textwrap import dedent
from uuid import UUID, uuid7

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from pydantic import SecretStr
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError

from homesearch.adapters.database import (
    create_database_engine,
    resolve_database_url,
)
from homesearch.config import LoadedConfiguration, OperationalSettings, load_configuration

DEFAULTS = Path("config/defaults.toml")
ALEMBIC_CONFIG = Path("alembic.ini")
CONFIGURATION_ATTRIBUTE = "homesearch_configuration"
TEST_DATABASE_URL_ENV = "HOMESEARCH_TEST_DATABASE_URL"
INITIAL_REVISION = "20260731_0001"
APPLICATION_TABLES = {
    "configuration_snapshots",
    "listings",
    "polling_runs",
    "properties",
    "sources",
    "users",
}


def _load_with_database_url(
    tmp_path: Path,
    database_url: str,
) -> LoadedConfiguration:
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


def _alembic_config(configuration: LoadedConfiguration) -> Config:
    config = Config(str(ALEMBIC_CONFIG))
    config.attributes[CONFIGURATION_ATTRIBUTE] = configuration
    return config


def _quote_database_name(name: str) -> str:
    if not name.isascii() or not name.replace("_", "").isalnum():
        raise ValueError("temporary database name is not safe")
    return f'"{name}"'


@contextmanager
def _temporary_database(
    server_configuration: LoadedConfiguration,
    tmp_path: Path,
) -> Iterator[LoadedConfiguration]:
    database_name = f"homesearch_test_{uuid7().hex}"
    quoted_name = _quote_database_name(database_name)
    server_engine = create_database_engine(server_configuration)
    database_created = False
    try:
        with server_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
            connection.exec_driver_sql(f"CREATE DATABASE {quoted_name} TEMPLATE template0")
        database_created = True

        database_url = resolve_database_url(server_configuration).set(database=database_name)
        database_configuration = _load_with_database_url(
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


@pytest.fixture(scope="module")
def server_configuration(
    tmp_path_factory: pytest.TempPathFactory,
) -> LoadedConfiguration:
    database_url = os.environ.get(TEST_DATABASE_URL_ENV)
    if database_url is None:
        pytest.skip(f"{TEST_DATABASE_URL_ENV} is required for PostgreSQL integration tests")
    return _load_with_database_url(
        tmp_path_factory.mktemp("postgresql-server-configuration"),
        database_url,
    )


def _application_tables(engine: Engine) -> set[str]:
    return set(sa.inspect(engine).get_table_names()).intersection(APPLICATION_TABLES)


def _current_revision(engine: Engine) -> str | None:
    with engine.connect() as connection:
        return MigrationContext.configure(connection).get_current_revision()


@pytest.mark.postgresql
def test_initial_migration_is_repeatable_from_empty_and_downgrades_to_base(
    server_configuration: LoadedConfiguration,
    tmp_path: Path,
) -> None:
    for cycle in range(2):
        with _temporary_database(
            server_configuration,
            tmp_path / f"cycle-{cycle}",
        ) as database_configuration:
            engine = create_database_engine(database_configuration)
            try:
                assert _application_tables(engine) == set()
                assert _current_revision(engine) is None

                command.upgrade(_alembic_config(database_configuration), "head")

                assert _application_tables(engine) == APPLICATION_TABLES
                assert _current_revision(engine) == INITIAL_REVISION

                command.downgrade(_alembic_config(database_configuration), "base")

                assert _application_tables(engine) == set()
                assert _current_revision(engine) is None
            finally:
                engine.dispose()


def _assert_uuid_column_without_default(
    inspector: sa.Inspector,
    table_name: str,
    column_name: str,
) -> None:
    column = next(
        column for column in inspector.get_columns(table_name) if column["name"] == column_name
    )
    assert isinstance(column["type"], postgresql.UUID)
    assert column["default"] is None


def _assert_timestamptz_column(
    inspector: sa.Inspector,
    table_name: str,
    column_name: str,
) -> None:
    column = next(
        column for column in inspector.get_columns(table_name) if column["name"] == column_name
    )
    assert isinstance(column["type"], postgresql.TIMESTAMP)
    assert column["type"].timezone is True


def _insert_valid_foundation_rows(engine: Engine) -> dict[str, UUID]:
    identifiers = {
        "configuration_snapshot_id": uuid7(),
        "user_id": uuid7(),
        "source_id": uuid7(),
        "property_id": uuid7(),
        "listing_id": uuid7(),
        "polling_run_id": uuid7(),
        "correlation_id": uuid7(),
    }
    now = datetime.now(UTC)
    digest = f"sha256:{'a' * 64}"
    configuration_document = json.dumps(
        {
            "schema_version": 4,
            "config_id": "integration-profile",
            "config_version": 1,
            "secret_references": [],
        }
    )

    with engine.begin() as connection:
        connection.execute(
            sa.text(
                """
                INSERT INTO configuration_snapshots (
                    configuration_snapshot_id,
                    config_id,
                    config_version,
                    schema_version,
                    effective_from,
                    recorded_at,
                    digest,
                    document
                )
                VALUES (
                    :configuration_snapshot_id,
                    :config_id,
                    :config_version,
                    :schema_version,
                    :effective_from,
                    :recorded_at,
                    :digest,
                    CAST(:document AS jsonb)
                )
                """
            ),
            {
                "configuration_snapshot_id": identifiers["configuration_snapshot_id"],
                "config_id": "integration-profile",
                "config_version": 1,
                "schema_version": 4,
                "effective_from": now,
                "recorded_at": now,
                "digest": digest,
                "document": configuration_document,
            },
        )
        connection.execute(
            sa.text("INSERT INTO users (user_id, created_at) VALUES (:user_id, :created_at)"),
            {"user_id": identifiers["user_id"], "created_at": now},
        )
        connection.execute(
            sa.text(
                """
                INSERT INTO sources (source_id, source_key, created_at)
                VALUES (:source_id, :source_key, :created_at)
                """
            ),
            {
                "source_id": identifiers["source_id"],
                "source_key": "synthetic-source",
                "created_at": now,
            },
        )
        connection.execute(
            sa.text(
                """
                INSERT INTO properties (property_id, created_at)
                VALUES (:property_id, :created_at)
                """
            ),
            {"property_id": identifiers["property_id"], "created_at": now},
        )
        connection.execute(
            sa.text(
                """
                INSERT INTO listings (
                    listing_id,
                    source_id,
                    source_external_id,
                    canonical_url,
                    created_at
                )
                VALUES (
                    :listing_id,
                    :source_id,
                    :source_external_id,
                    :canonical_url,
                    :created_at
                )
                """
            ),
            {
                "listing_id": identifiers["listing_id"],
                "source_id": identifiers["source_id"],
                "source_external_id": "synthetic-listing",
                "canonical_url": "https://example.invalid/listing/synthetic",
                "created_at": now,
            },
        )
        connection.execute(
            sa.text(
                """
                INSERT INTO polling_runs (
                    polling_run_id,
                    user_id,
                    configuration_snapshot_id,
                    configuration_digest,
                    run_kind,
                    trigger_kind,
                    state,
                    idempotency_key,
                    correlation_id,
                    started_at,
                    finished_at,
                    recorded_at,
                    aggregate_counts,
                    outcome
                )
                VALUES (
                    :polling_run_id,
                    :user_id,
                    :configuration_snapshot_id,
                    :configuration_digest,
                    :run_kind,
                    :trigger_kind,
                    :state,
                    :idempotency_key,
                    :correlation_id,
                    :started_at,
                    :finished_at,
                    :recorded_at,
                    CAST(:aggregate_counts AS jsonb),
                    CAST(:outcome AS jsonb)
                )
                """
            ),
            {
                "polling_run_id": identifiers["polling_run_id"],
                "user_id": identifiers["user_id"],
                "configuration_snapshot_id": identifiers["configuration_snapshot_id"],
                "configuration_digest": digest,
                "run_kind": "synthetic",
                "trigger_kind": "manual",
                "state": "succeeded",
                "idempotency_key": "synthetic-run-1",
                "correlation_id": identifiers["correlation_id"],
                "started_at": now,
                "finished_at": now + timedelta(seconds=1),
                "recorded_at": now,
                "aggregate_counts": json.dumps({"listings": 1}),
                "outcome": json.dumps({"result": "synthetic"}),
            },
        )

    return identifiers


@pytest.mark.postgresql
def test_initial_schema_uses_postgresql_types_and_enforces_core_constraints(
    server_configuration: LoadedConfiguration,
    tmp_path: Path,
) -> None:
    with _temporary_database(
        server_configuration,
        tmp_path / "constraints",
    ) as database_configuration:
        command.upgrade(_alembic_config(database_configuration), "head")
        engine = create_database_engine(database_configuration)
        try:
            inspector = sa.inspect(engine)
            for table_name, column_name in [
                ("configuration_snapshots", "configuration_snapshot_id"),
                ("users", "user_id"),
                ("sources", "source_id"),
                ("properties", "property_id"),
                ("listings", "listing_id"),
                ("polling_runs", "polling_run_id"),
            ]:
                _assert_uuid_column_without_default(inspector, table_name, column_name)

            for table_name, column_name in [
                ("configuration_snapshots", "recorded_at"),
                ("users", "created_at"),
                ("sources", "created_at"),
                ("properties", "created_at"),
                ("listings", "created_at"),
                ("polling_runs", "started_at"),
            ]:
                _assert_timestamptz_column(inspector, table_name, column_name)

            identifiers = _insert_valid_foundation_rows(engine)
            with engine.connect() as connection:
                persisted_id, persisted_at = connection.execute(
                    sa.text(
                        """
                        SELECT polling_run_id, started_at
                        FROM polling_runs
                        WHERE polling_run_id = :polling_run_id
                        """
                    ),
                    {"polling_run_id": identifiers["polling_run_id"]},
                ).one()
            assert persisted_id == identifiers["polling_run_id"]
            assert persisted_id.version == 7
            assert persisted_at.utcoffset() == UTC.utcoffset(persisted_at)

            with (
                pytest.raises(IntegrityError),
                engine.begin() as connection,
            ):
                connection.execute(
                    sa.text(
                        """
                        INSERT INTO sources (source_id, source_key, created_at)
                        VALUES (:source_id, 'synthetic-source', :created_at)
                        """
                    ),
                    {"source_id": uuid7(), "created_at": datetime.now(UTC)},
                )

            with (
                pytest.raises(IntegrityError),
                engine.begin() as connection,
            ):
                connection.execute(
                    sa.text(
                        """
                        INSERT INTO listings (listing_id, source_id, created_at)
                        VALUES (:listing_id, :source_id, :created_at)
                        """
                    ),
                    {
                        "listing_id": uuid7(),
                        "source_id": uuid7(),
                        "created_at": datetime.now(UTC),
                    },
                )

            with (
                pytest.raises(IntegrityError),
                engine.begin() as connection,
            ):
                now = datetime.now(UTC)
                connection.execute(
                    sa.text(
                        """
                        INSERT INTO polling_runs (
                            polling_run_id,
                            user_id,
                            configuration_snapshot_id,
                            configuration_digest,
                            run_kind,
                            trigger_kind,
                            state,
                            idempotency_key,
                            correlation_id,
                            started_at,
                            finished_at,
                            recorded_at,
                            aggregate_counts
                        )
                        SELECT
                            :polling_run_id,
                            :user_id,
                            configuration_snapshot_id,
                            digest,
                            'synthetic',
                            'manual',
                            'failed',
                            'invalid-time-order',
                            :correlation_id,
                            :started_at,
                            :finished_at,
                            :recorded_at,
                            '{}'::jsonb
                        FROM configuration_snapshots
                        """
                    ),
                    {
                        "polling_run_id": uuid7(),
                        "user_id": identifiers["user_id"],
                        "correlation_id": uuid7(),
                        "started_at": now,
                        "finished_at": now - timedelta(seconds=1),
                        "recorded_at": now,
                    },
                )
        finally:
            engine.dispose()
