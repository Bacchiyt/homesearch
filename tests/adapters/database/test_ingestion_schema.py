"""PostgreSQL migration tests for the first Phase 2 ingestion schema."""

from __future__ import annotations

from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.migration import MigrationContext
from sqlalchemy.engine import Engine

from homesearch.adapters.database import create_database_engine
from homesearch.config import LoadedConfiguration
from tests.adapters.database.postgresql import alembic_config, temporary_database

FOUNDATION_REVISION = "20260731_0001"
INGESTION_REVISION = "20260731_0002"
INGESTION_TABLES = {
    "observations",
    "parse_runs",
    "raw_objects",
    "source_facts",
    "source_runs",
}


def _current_revision(engine: Engine) -> str | None:
    with engine.connect() as connection:
        return MigrationContext.configure(connection).get_current_revision()


@pytest.mark.postgresql
def test_ingestion_migration_upgrades_and_downgrades_to_phase_1(
    server_configuration: LoadedConfiguration,
    tmp_path: Path,
) -> None:
    with temporary_database(
        server_configuration,
        tmp_path / "ingestion-migration",
    ) as database_configuration:
        config = alembic_config(database_configuration)
        command.upgrade(config, FOUNDATION_REVISION)
        engine = create_database_engine(database_configuration)
        try:
            inspector = sa.inspect(engine)
            assert not INGESTION_TABLES.intersection(inspector.get_table_names())
            assert "source_listing_key" not in {
                column["name"] for column in inspector.get_columns("listings")
            }

            command.upgrade(config, "head")

            inspector = sa.inspect(engine)
            assert INGESTION_TABLES.issubset(inspector.get_table_names())
            assert "source_listing_key" in {
                column["name"] for column in inspector.get_columns("listings")
            }
            assert _current_revision(engine) == INGESTION_REVISION

            command.downgrade(config, FOUNDATION_REVISION)

            inspector = sa.inspect(engine)
            assert not INGESTION_TABLES.intersection(inspector.get_table_names())
            assert "source_listing_key" not in {
                column["name"] for column in inspector.get_columns("listings")
            }
            assert _current_revision(engine) == FOUNDATION_REVISION
        finally:
            engine.dispose()
