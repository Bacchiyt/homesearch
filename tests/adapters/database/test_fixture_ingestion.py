"""End-to-end PostgreSQL integration for deterministic fixture ingestion."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from textwrap import dedent
from uuid import UUID, uuid7

import pytest
import sqlalchemy as sa
from alembic import command
from pydantic import SecretStr

from homesearch.adapters.database import (
    SqlAlchemyUnitOfWork,
    create_database_engine,
    resolve_database_url,
)
from homesearch.adapters.database.schema import (
    listings,
    observations,
    parse_runs,
    polling_runs,
    raw_objects,
    source_facts,
    source_runs,
)
from homesearch.adapters.sources import FixtureSourceAdapter
from homesearch.application import (
    IngestSourceCommand,
    ingest_source,
    persist_configuration_foundation,
)
from homesearch.config import LoadedConfiguration, OperationalSettings, load_configuration
from tests.adapters.database.postgresql import alembic_config, temporary_database

FIXTURE_MANIFEST = Path("tests/fixtures/ingestion/manifest.json")
USER_ID = UUID("019fb31c-0022-70cf-afee-7644241d7ba8")
SOURCE_ID = UUID("019fb5f4-cf78-7c5f-85f5-7c8d8dfe7bb9")
SEARCH_ID = UUID("019fb5f5-61eb-7da6-aa3b-945b3ac03d38")


def _ingestion_configuration(
    tmp_path: Path,
    database_url: str,
) -> LoadedConfiguration:
    configuration_path = tmp_path / "fixture-ingestion.toml"
    configuration_path.write_text(
        dedent(
            f"""
            schema_version = 4
            config_id = "fixture-ingestion"
            config_version = 1
            effective_from = 2026-08-01T00:00:00Z

            [user_scope]
            default_user_id = "{USER_ID}"

            [[user_scope.users]]
            user_id = "{USER_ID}"

            [[source_registry.sources]]
            source_id = "{SOURCE_ID}"
            source_key = "synthetic-fixture"
            source_version = 1
            effective_from = 2026-08-01T00:00:00Z
            lifecycle = "DISABLED"
            access_status = "NOT_ASSESSED"
            capabilities = ["MANUAL_IMPORT"]

            [source_registry.sources.capture_policy]
            capture_mode = "FULL_PAYLOAD"
            storage_adapter = "FILESYSTEM"
            raw_payload_retention_days = 30

            [[search_registry.searches]]
            search_id = "{SEARCH_ID}"
            search_key = "synthetic-search"
            search_version = 1
            effective_from = 2026-08-01T00:00:00Z
            user_id = "{USER_ID}"
            lifecycle = "DISABLED"
            source_ids = ["{SOURCE_ID}"]
            property_types = ["DETACHED_HOUSE"]
            property_conditions = ["NEW"]
            discovery_interval_minutes = 720
            maximum_results_per_run = 10

            [[search_registry.searches.areas]]
            area_key = "synthetic-area"
            prefecture = "Synthetic Prefecture"
            municipality = "Synthetic Municipality"
            localities = ["Synthetic Locality"]

            [search_registry.searches.price]
            maximum_jpy = 45000000

            [runtime]
            log_level = "INFO"
            log_format = "json"

            [[secret_references]]
            secret_id = "fixture-store"
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
def test_fixture_ingests_end_to_end_atomically_and_idempotently(
    server_configuration: LoadedConfiguration,
    tmp_path: Path,
) -> None:
    with temporary_database(
        server_configuration,
        tmp_path / "fixture-ingestion",
    ) as database_configuration:
        command.upgrade(alembic_config(database_configuration), "head")
        database_url = resolve_database_url(database_configuration).render_as_string(
            hide_password=False
        )
        configuration = _ingestion_configuration(tmp_path, database_url)
        engine = create_database_engine(database_configuration)
        adapter = FixtureSourceAdapter(
            FIXTURE_MANIFEST,
            source_id=SOURCE_ID,
            source_key="synthetic-fixture",
        )
        foundation_time = datetime(2026, 8, 1, 0, 1, tzinfo=UTC)
        first_ingestion_time = datetime(2026, 8, 1, 0, 2, tzinfo=UTC)
        second_ingestion_time = first_ingestion_time + timedelta(hours=1)

        def unit_of_work_factory() -> SqlAlchemyUnitOfWork:
            return SqlAlchemyUnitOfWork(engine)

        try:
            configuration_snapshot_id = persist_configuration_foundation(
                configuration,
                unit_of_work_factory,
                clock=lambda: foundation_time,
                id_factory=uuid7,
            )
            command_input = IngestSourceCommand(
                configuration_snapshot_id=configuration_snapshot_id,
                source_id=SOURCE_ID,
                search_id=SEARCH_ID,
                reference="listing-001",
            )

            first = ingest_source(
                configuration,
                command_input,
                adapter,
                unit_of_work_factory,
                clock=lambda: first_ingestion_time,
                id_factory=uuid7,
            )
            second = ingest_source(
                configuration,
                command_input,
                adapter,
                unit_of_work_factory,
                clock=lambda: second_ingestion_time,
                id_factory=uuid7,
            )

            assert first.created is True
            assert second.created is False
            assert second == type(second)(
                polling_run_id=first.polling_run_id,
                source_run_id=first.source_run_id,
                listing_id=first.listing_id,
                observation_id=first.observation_id,
                parse_run_id=first.parse_run_id,
                correlation_id=first.correlation_id,
                created=False,
            )
            assert all(
                identifier.version == 7
                for identifier in (
                    first.polling_run_id,
                    first.source_run_id,
                    first.listing_id,
                    first.observation_id,
                    first.parse_run_id,
                    first.correlation_id,
                )
            )

            with engine.connect() as connection:
                counts = {
                    table.name: connection.scalar(sa.select(sa.func.count()).select_from(table))
                    for table in (
                        listings,
                        polling_runs,
                        source_runs,
                        raw_objects,
                        observations,
                        parse_runs,
                        source_facts,
                    )
                }
                polling_run = connection.execute(sa.select(polling_runs)).mappings().one()
                source_run = connection.execute(sa.select(source_runs)).mappings().one()
                raw_object = connection.execute(sa.select(raw_objects)).mappings().one()
                observation = connection.execute(sa.select(observations)).mappings().one()
                parse_run = connection.execute(sa.select(parse_runs)).mappings().one()
                facts = (
                    connection.execute(sa.select(source_facts).order_by(source_facts.c.fact_key))
                    .mappings()
                    .all()
                )

            assert counts == {
                "listings": 1,
                "polling_runs": 1,
                "source_runs": 1,
                "raw_objects": 1,
                "observations": 1,
                "parse_runs": 1,
                "source_facts": 4,
            }
            assert polling_run["user_id"] == USER_ID
            assert polling_run["configuration_snapshot_id"] == configuration_snapshot_id
            assert polling_run["configuration_digest"] == configuration.digest
            assert source_run["source_id"] == SOURCE_ID
            assert source_run["search_id"] == SEARCH_ID
            assert source_run["search_version"] == 1
            assert raw_object["checksum"] == observation["content_checksum"]
            assert raw_object["storage_adapter"] == "FIXTURE"
            assert raw_object["replay_eligible"] is True
            assert observation["recorded_at"] == first_ingestion_time
            assert observation["observed_at"] == datetime(2026, 8, 1, tzinfo=UTC)
            assert observation["correlation_id"] == first.correlation_id
            assert parse_run["parser_version"] == "1"
            assert parse_run["input_checksum"] == observation["content_checksum"]
            assert {fact["fact_key"] for fact in facts} == {
                "address",
                "headline",
                "price",
                "source-status",
            }
            price = next(fact for fact in facts if fact["fact_key"] == "price")
            assert price["raw_value"] == "4280万円"
            assert price["normalized_value"] == {
                "amount": 42_800_000,
                "currency": "JPY",
            }
        finally:
            engine.dispose()
