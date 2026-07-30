"""PostgreSQL integration tests for the Phase 1 application persistence slice."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from textwrap import dedent
from typing import cast
from uuid import UUID, uuid7

import pytest
import sqlalchemy as sa
from alembic import command
from pydantic import SecretStr
from sqlalchemy.pool import QueuePool

from homesearch.adapters.database import (
    SqlAlchemyUnitOfWork,
    create_database_engine,
    resolve_database_url,
)
from homesearch.adapters.database.schema import (
    configuration_snapshots,
    sources,
    users,
)
from homesearch.application import (
    PersistenceConflictError,
    persist_configuration_foundation,
)
from homesearch.config import LoadedConfiguration, OperationalSettings, load_configuration
from tests.adapters.database.postgresql import alembic_config, temporary_database

DEFAULTS = Path("config/defaults.toml")
DEFAULT_USER_ID = UUID("019fb31c-0022-70cf-afee-7644241d7ba8")
SOURCE_ONE_ID = UUID("019fb31c-545a-7073-8899-2b73e89d99c8")
SOURCE_TWO_ID = UUID("019fb31c-8bca-7693-a1fe-3db06530d6b7")


def _foundation_configuration(
    tmp_path: Path,
    database_url: str,
    *,
    config_id: str,
    source_id: UUID,
    source_key: str = "synthetic-source",
) -> LoadedConfiguration:
    configuration_path = tmp_path / f"{config_id}.toml"
    configuration_path.write_text(
        dedent(
            f"""
            schema_version = 4
            config_id = "{config_id}"
            config_version = 1
            effective_from = 2026-07-30T00:00:00Z

            [user_scope]
            default_user_id = "{DEFAULT_USER_ID}"

            [[user_scope.users]]
            user_id = "{DEFAULT_USER_ID}"

            [[source_registry.sources]]
            source_id = "{source_id}"
            source_key = "{source_key}"
            source_version = 1
            effective_from = 2026-07-30T00:00:00Z
            lifecycle = "DISABLED"
            access_status = "NOT_ASSESSED"
            capabilities = []

            [source_registry.sources.capture_policy]
            capture_mode = "METADATA_ONLY"
            storage_adapter = "NONE"
            raw_payload_retention_days = 0

            [search_registry]
            searches = []

            [runtime]
            log_level = "INFO"
            log_format = "json"

            [[secret_references]]
            secret_id = "foundation-store"
            setting = "database_url"
            required = true
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    return load_configuration(
        OperationalSettings(
            config_path=configuration_path,
            database_url=SecretStr(database_url),
        )
    )


@pytest.mark.postgresql
def test_safe_configuration_and_identities_persist_atomically_and_idempotently(
    server_configuration: LoadedConfiguration,
    tmp_path: Path,
) -> None:
    with temporary_database(
        server_configuration,
        tmp_path / "idempotent",
    ) as database_configuration:
        command.upgrade(alembic_config(database_configuration), "head")
        database_url = resolve_database_url(database_configuration)
        loaded = _foundation_configuration(
            tmp_path,
            database_url.render_as_string(hide_password=False),
            config_id="foundation-one",
            source_id=SOURCE_ONE_ID,
        )
        engine = create_database_engine(database_configuration)
        recorded_at = datetime(2026, 7, 31, 0, 0, tzinfo=UTC)
        first_snapshot_id = uuid7()
        second_snapshot_id = uuid7()
        generated_ids = iter((first_snapshot_id, second_snapshot_id))

        def unit_of_work_factory() -> SqlAlchemyUnitOfWork:
            return SqlAlchemyUnitOfWork(engine)

        try:
            first_result = persist_configuration_foundation(
                loaded,
                unit_of_work_factory,
                clock=lambda: recorded_at,
                id_factory=lambda: next(generated_ids),
            )
            second_result = persist_configuration_foundation(
                loaded,
                unit_of_work_factory,
                clock=lambda: recorded_at,
                id_factory=lambda: next(generated_ids),
            )

            assert first_result == first_snapshot_id
            assert second_result == first_snapshot_id
            assert first_result.version == 7

            with engine.connect() as connection:
                snapshot = connection.execute(sa.select(configuration_snapshots)).mappings().one()
                persisted_users = connection.execute(
                    sa.select(users.c.user_id, users.c.created_at)
                ).all()
                persisted_sources = connection.execute(
                    sa.select(sources.c.source_id, sources.c.source_key)
                ).all()

            assert snapshot["recorded_at"] == recorded_at
            assert snapshot["digest"] == loaded.digest
            assert snapshot["document"] == loaded.configuration.model_dump(mode="json")
            assert "resolved_secrets" not in snapshot["document"]
            serialized_snapshot = json.dumps(snapshot["document"], sort_keys=True)
            assert database_url.password is not None
            assert database_url.password not in serialized_snapshot
            assert [tuple(row) for row in persisted_users] == [(DEFAULT_USER_ID, recorded_at)]
            assert [tuple(row) for row in persisted_sources] == [
                (SOURCE_ONE_ID, "synthetic-source")
            ]
        finally:
            engine.dispose()


@pytest.mark.postgresql
def test_identity_conflict_and_uncommitted_work_roll_back_and_release_connection(
    server_configuration: LoadedConfiguration,
    tmp_path: Path,
) -> None:
    with temporary_database(
        server_configuration,
        tmp_path / "rollback",
    ) as database_configuration:
        command.upgrade(alembic_config(database_configuration), "head")
        database_url = resolve_database_url(database_configuration).render_as_string(
            hide_password=False
        )
        first = _foundation_configuration(
            tmp_path,
            database_url,
            config_id="foundation-first",
            source_id=SOURCE_ONE_ID,
        )
        conflicting = _foundation_configuration(
            tmp_path,
            database_url,
            config_id="foundation-conflict",
            source_id=SOURCE_TWO_ID,
        )
        engine = create_database_engine(database_configuration)
        recorded_at = datetime(2026, 7, 31, 1, 0, tzinfo=UTC)

        def unit_of_work_factory() -> SqlAlchemyUnitOfWork:
            return SqlAlchemyUnitOfWork(engine)

        try:
            persist_configuration_foundation(
                first,
                unit_of_work_factory,
                clock=lambda: recorded_at,
                id_factory=uuid7,
            )

            with pytest.raises(
                PersistenceConflictError,
                match="Configured source identity conflicts",
            ):
                persist_configuration_foundation(
                    conflicting,
                    unit_of_work_factory,
                    clock=lambda: recorded_at,
                    id_factory=uuid7,
                )

            rolled_back_user_id = uuid7()
            with SqlAlchemyUnitOfWork(engine) as unit_of_work:
                unit_of_work.foundation.ensure_user(
                    rolled_back_user_id,
                    recorded_at,
                )

            with engine.connect() as connection:
                snapshot_digests = (
                    connection.execute(sa.select(configuration_snapshots.c.digest)).scalars().all()
                )
                persisted_users = connection.execute(sa.select(users.c.user_id)).scalars().all()
                persisted_sources = connection.execute(
                    sa.select(sources.c.source_id, sources.c.source_key)
                ).all()

            assert snapshot_digests == [first.digest]
            assert persisted_users == [DEFAULT_USER_ID]
            assert rolled_back_user_id not in persisted_users
            assert [tuple(row) for row in persisted_sources] == [
                (SOURCE_ONE_ID, "synthetic-source")
            ]
            assert cast(QueuePool, engine.pool).checkedout() == 0
        finally:
            engine.dispose()


@pytest.mark.postgresql
def test_sqlalchemy_metadata_matches_the_migration_head(
    server_configuration: LoadedConfiguration,
    tmp_path: Path,
) -> None:
    with temporary_database(
        server_configuration,
        tmp_path / "metadata",
    ) as database_configuration:
        config = alembic_config(database_configuration)
        command.upgrade(config, "head")

        command.check(config)
