"""PostgreSQL persistence operations for the Phase 1 foundation use case."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import Connection

from homesearch.adapters.database.schema import (
    configuration_snapshots,
    listings,
    observations,
    parse_runs,
    polling_runs,
    raw_objects,
    source_facts,
    source_runs,
    sources,
    users,
)
from homesearch.application import (
    ConfigurationSnapshotWrite,
    IngestionReceipt,
    IngestionWrite,
    PersistenceConflictError,
)


class SqlAlchemyFoundationRepository:
    """Narrow repository bound to one caller-owned SQLAlchemy transaction."""

    def __init__(self, connection: Connection) -> None:
        self._connection = connection

    def persist_configuration_snapshot(
        self,
        snapshot: ConfigurationSnapshotWrite,
    ) -> UUID:
        statement = insert(configuration_snapshots).values(
            configuration_snapshot_id=snapshot.configuration_snapshot_id,
            config_id=snapshot.config_id,
            config_version=snapshot.config_version,
            schema_version=snapshot.schema_version,
            effective_from=snapshot.effective_from,
            recorded_at=snapshot.recorded_at,
            digest=snapshot.digest,
            document=dict(snapshot.document),
        )
        self._connection.execute(statement.on_conflict_do_nothing())

        row = (
            self._connection.execute(
                sa.select(configuration_snapshots).where(
                    configuration_snapshots.c.digest == snapshot.digest
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            raise PersistenceConflictError(
                "Configuration snapshot ID conflicts with persisted state"
            )
        persisted_document = row["document"]
        if (
            row["config_id"] != snapshot.config_id
            or row["config_version"] != snapshot.config_version
            or row["schema_version"] != snapshot.schema_version
            or row["effective_from"] != snapshot.effective_from
            or persisted_document != dict(snapshot.document)
        ):
            raise PersistenceConflictError(
                "Configuration digest conflicts with persisted snapshot content"
            )
        return UUID(str(row["configuration_snapshot_id"]))

    def ensure_user(self, user_id: UUID, created_at: datetime) -> None:
        statement = insert(users).values(user_id=user_id, created_at=created_at)
        self._connection.execute(statement.on_conflict_do_nothing())

    def ensure_source(
        self,
        source_id: UUID,
        source_key: str,
        created_at: datetime,
    ) -> None:
        statement = insert(sources).values(
            source_id=source_id,
            source_key=source_key,
            created_at=created_at,
        )
        self._connection.execute(statement.on_conflict_do_nothing())

        rows = (
            self._connection.execute(
                sa.select(sources.c.source_id, sources.c.source_key).where(
                    sa.or_(
                        sources.c.source_id == source_id,
                        sources.c.source_key == source_key,
                    )
                )
            )
            .mappings()
            .all()
        )
        if len(rows) != 1 or (
            rows[0]["source_id"] != source_id or rows[0]["source_key"] != source_key
        ):
            raise PersistenceConflictError(
                "Configured source identity conflicts with persisted state"
            )


class SqlAlchemyIngestionRepository:
    """Fixture-ingestion writes bound to one caller-owned transaction."""

    def __init__(self, connection: Connection) -> None:
        self._connection = connection

    def persist_ingestion(self, write: IngestionWrite) -> IngestionReceipt:
        polling_run_id = self._insert_polling_run(write)
        if polling_run_id is None:
            return self._existing_receipt(write)

        self._connection.execute(
            insert(source_runs).values(
                source_run_id=write.source_run_id,
                polling_run_id=write.polling_run_id,
                source_id=write.source_id,
                search_id=write.search_id,
                search_version=write.search_version,
                adapter_name=write.adapter_name,
                adapter_version=write.adapter_version,
                state="SUCCEEDED",
                idempotency_key=write.command_idempotency_key,
                started_at=write.recorded_at,
                finished_at=write.recorded_at,
                recorded_at=write.recorded_at,
                aggregate_counts={
                    "listings": 1,
                    "observations": 1,
                    "parse_runs": 1,
                    "source_facts": len(write.result.facts),
                },
                outcome={
                    "result": write.result.parse_result.value,
                    "reference": write.result.reference,
                },
            )
        )
        raw_object_id = self._ensure_raw_object(write)
        listing_id = self._ensure_listing(write)
        observation_id = self._ensure_observation(
            write,
            raw_object_id=raw_object_id,
            listing_id=listing_id,
        )
        parse_run_id, parse_created = self._ensure_parse_run(
            write,
            observation_id=observation_id,
        )
        if parse_created:
            self._persist_source_facts(
                write,
                observation_id=observation_id,
                parse_run_id=parse_run_id,
            )

        return IngestionReceipt(
            polling_run_id=write.polling_run_id,
            source_run_id=write.source_run_id,
            listing_id=listing_id,
            observation_id=observation_id,
            parse_run_id=parse_run_id,
            correlation_id=write.correlation_id,
            created=True,
        )

    def _insert_polling_run(self, write: IngestionWrite) -> UUID | None:
        statement = (
            insert(polling_runs)
            .values(
                polling_run_id=write.polling_run_id,
                user_id=write.user_id,
                configuration_snapshot_id=write.configuration_snapshot_id,
                configuration_digest=write.configuration_digest,
                run_kind="fixture_ingestion",
                trigger_kind="manual_fixture",
                state="SUCCEEDED",
                idempotency_key=write.command_idempotency_key,
                correlation_id=write.correlation_id,
                started_at=write.recorded_at,
                finished_at=write.recorded_at,
                recorded_at=write.recorded_at,
                aggregate_counts={
                    "source_runs": 1,
                    "listings": 1,
                    "observations": 1,
                    "parse_runs": 1,
                    "source_facts": len(write.result.facts),
                },
                outcome={
                    "result": write.result.parse_result.value,
                    "transport": "FIXTURE",
                },
            )
            .on_conflict_do_nothing(
                constraint="uq_polling_runs_kind_idempotency",
            )
            .returning(polling_runs.c.polling_run_id)
        )
        return self._connection.execute(statement).scalar_one_or_none()

    def _existing_receipt(self, write: IngestionWrite) -> IngestionReceipt:
        row = (
            self._connection.execute(
                sa.select(
                    polling_runs.c.polling_run_id,
                    source_runs.c.source_run_id,
                    observations.c.listing_id,
                    observations.c.observation_id,
                    parse_runs.c.parse_run_id,
                    polling_runs.c.correlation_id,
                    polling_runs.c.configuration_snapshot_id,
                    polling_runs.c.configuration_digest,
                    source_runs.c.search_id,
                    source_runs.c.search_version,
                )
                .join(
                    source_runs,
                    source_runs.c.polling_run_id == polling_runs.c.polling_run_id,
                )
                .join(
                    observations,
                    observations.c.source_run_id == source_runs.c.source_run_id,
                )
                .join(
                    parse_runs,
                    parse_runs.c.observation_id == observations.c.observation_id,
                )
                .where(
                    polling_runs.c.run_kind == "fixture_ingestion",
                    polling_runs.c.idempotency_key == write.command_idempotency_key,
                    source_runs.c.source_id == write.source_id,
                    parse_runs.c.idempotency_key == write.parse_idempotency_key,
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            raise PersistenceConflictError(
                "Fixture-ingestion idempotency key conflicts with incomplete persisted state"
            )
        if (
            row["configuration_snapshot_id"] != write.configuration_snapshot_id
            or row["configuration_digest"] != write.configuration_digest
            or row["search_id"] != write.search_id
            or row["search_version"] != write.search_version
        ):
            raise PersistenceConflictError(
                "Fixture-ingestion idempotency key conflicts with persisted context"
            )
        return IngestionReceipt(
            polling_run_id=row["polling_run_id"],
            source_run_id=row["source_run_id"],
            listing_id=row["listing_id"],
            observation_id=row["observation_id"],
            parse_run_id=row["parse_run_id"],
            correlation_id=row["correlation_id"],
            created=False,
        )

    def _ensure_raw_object(self, write: IngestionWrite) -> UUID:
        statement = (
            insert(raw_objects)
            .values(
                raw_object_id=write.raw_object_id,
                source_id=write.source_id,
                checksum=write.result.content_checksum,
                byte_size=write.result.content_size,
                media_type=write.result.media_type,
                storage_adapter=write.result.storage_adapter,
                storage_key=write.result.storage_key,
                lifecycle_state="AVAILABLE",
                replay_eligible=write.result.replay_eligible,
                retention_policy_reference=write.result.retention_policy_reference,
                compliance_reference=write.result.compliance_reference,
                created_at=write.recorded_at,
                verified_at=write.recorded_at,
            )
            .on_conflict_do_nothing(
                constraint="uq_raw_objects_source_storage_identity",
            )
            .returning(raw_objects.c.raw_object_id)
        )
        inserted_id = self._connection.execute(statement).scalar_one_or_none()
        if inserted_id is not None:
            return UUID(str(inserted_id))

        row = (
            self._connection.execute(
                sa.select(raw_objects).where(
                    raw_objects.c.source_id == write.source_id,
                    raw_objects.c.checksum == write.result.content_checksum,
                    raw_objects.c.storage_adapter == write.result.storage_adapter,
                    raw_objects.c.storage_key == write.result.storage_key,
                )
            )
            .mappings()
            .one()
        )
        if (
            row["byte_size"] != write.result.content_size
            or row["media_type"] != write.result.media_type
            or row["replay_eligible"] != write.result.replay_eligible
            or row["retention_policy_reference"] != write.result.retention_policy_reference
            or row["compliance_reference"] != write.result.compliance_reference
        ):
            raise PersistenceConflictError("Raw-object identity conflicts with persisted metadata")
        return UUID(str(row["raw_object_id"]))

    def _ensure_listing(self, write: IngestionWrite) -> UUID:
        statement = (
            insert(listings)
            .values(
                listing_id=write.listing_id,
                source_id=write.source_id,
                source_external_id=write.result.source_external_id,
                source_listing_key=write.result.source_listing_key,
                canonical_url=write.result.canonical_url,
                created_at=write.recorded_at,
            )
            .on_conflict_do_nothing(
                constraint="uq_listings_source_listing_key",
            )
            .returning(listings.c.listing_id)
        )
        inserted_id = self._connection.execute(statement).scalar_one_or_none()
        if inserted_id is not None:
            return UUID(str(inserted_id))

        row = (
            self._connection.execute(
                sa.select(
                    listings.c.listing_id,
                    listings.c.source_external_id,
                ).where(
                    listings.c.source_id == write.source_id,
                    listings.c.source_listing_key == write.result.source_listing_key,
                )
            )
            .mappings()
            .one()
        )
        if row["source_external_id"] != write.result.source_external_id:
            raise PersistenceConflictError(
                "Normalized listing identity conflicts with persisted source identity"
            )
        return UUID(str(row["listing_id"]))

    def _ensure_observation(
        self,
        write: IngestionWrite,
        *,
        raw_object_id: UUID,
        listing_id: UUID,
    ) -> UUID:
        statement = (
            insert(observations)
            .values(
                observation_id=write.observation_id,
                source_id=write.source_id,
                listing_id=listing_id,
                source_run_id=write.source_run_id,
                raw_object_id=raw_object_id,
                observed_at=write.result.observed_at,
                recorded_at=write.recorded_at,
                requested_url=write.result.requested_url,
                final_url=write.result.final_url,
                outcome=write.result.outcome.value,
                page_classification=write.result.page_classification,
                capture_mode=write.result.capture_mode.value,
                content_checksum=write.result.content_checksum,
                content_size=write.result.content_size,
                media_type=write.result.media_type,
                replay_eligible=write.result.replay_eligible,
                retention_policy_reference=write.result.retention_policy_reference,
                compliance_reference=write.result.compliance_reference,
                correlation_id=write.correlation_id,
                idempotency_fingerprint=write.observation_fingerprint,
            )
            .on_conflict_do_nothing(
                constraint="uq_observations_source_fingerprint",
            )
            .returning(observations.c.observation_id)
        )
        inserted_id = self._connection.execute(statement).scalar_one_or_none()
        if inserted_id is not None:
            return UUID(str(inserted_id))
        persisted_id = self._connection.execute(
            sa.select(observations.c.observation_id).where(
                observations.c.source_id == write.source_id,
                observations.c.idempotency_fingerprint == write.observation_fingerprint,
            )
        ).scalar_one()
        return UUID(str(persisted_id))

    def _ensure_parse_run(
        self,
        write: IngestionWrite,
        *,
        observation_id: UUID,
    ) -> tuple[UUID, bool]:
        statement = (
            insert(parse_runs)
            .values(
                parse_run_id=write.parse_run_id,
                observation_id=observation_id,
                parser_name=write.result.parser_name,
                parser_version=write.result.parser_version,
                schema_version=write.result.parser_schema_version,
                input_checksum=write.result.content_checksum,
                result=write.result.parse_result.value,
                idempotency_key=write.parse_idempotency_key,
                started_at=write.recorded_at,
                finished_at=write.recorded_at,
                recorded_at=write.recorded_at,
                warnings=list(write.result.warnings),
            )
            .on_conflict_do_nothing(
                constraint="uq_parse_runs_observation_parser_input",
            )
            .returning(parse_runs.c.parse_run_id)
        )
        inserted_id = self._connection.execute(statement).scalar_one_or_none()
        if inserted_id is not None:
            return inserted_id, True
        existing_id = self._connection.execute(
            sa.select(parse_runs.c.parse_run_id).where(
                parse_runs.c.observation_id == observation_id,
                parse_runs.c.parser_name == write.result.parser_name,
                parse_runs.c.parser_version == write.result.parser_version,
                parse_runs.c.input_checksum == write.result.content_checksum,
            )
        ).scalar_one()
        return existing_id, False

    def _persist_source_facts(
        self,
        write: IngestionWrite,
        *,
        observation_id: UUID,
        parse_run_id: UUID,
    ) -> None:
        for source_fact_id, fact in zip(
            write.source_fact_ids,
            write.result.facts,
            strict=True,
        ):
            self._connection.execute(
                insert(source_facts).values(
                    source_fact_id=source_fact_id,
                    parse_run_id=parse_run_id,
                    observation_id=observation_id,
                    fact_key=fact.fact_key,
                    fact_type=fact.fact_type,
                    field_path=fact.field_path,
                    value_state=fact.value_state.value,
                    raw_value=fact.raw_value,
                    normalized_value=fact.normalized_value,
                    language=fact.language,
                    unit=fact.unit,
                    schema_version=write.result.parser_schema_version,
                    recorded_at=write.recorded_at,
                )
            )
