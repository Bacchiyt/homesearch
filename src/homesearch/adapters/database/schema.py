"""SQLAlchemy Core mappings for the migration-backed Phase 1 schema."""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

metadata = sa.MetaData()

configuration_snapshots = sa.Table(
    "configuration_snapshots",
    metadata,
    sa.Column(
        "configuration_snapshot_id",
        postgresql.UUID(as_uuid=True),
        nullable=False,
    ),
    sa.Column("config_id", sa.String(length=64), nullable=False),
    sa.Column("config_version", sa.Integer(), nullable=False),
    sa.Column("schema_version", sa.Integer(), nullable=False),
    sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False),
    sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("digest", sa.String(length=71), nullable=False),
    sa.Column("document", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.CheckConstraint(
        "config_id ~ '^[a-z][a-z0-9-]*$'",
        name="ck_configuration_snapshots_config_id",
    ),
    sa.CheckConstraint(
        "config_version > 0",
        name="ck_configuration_snapshots_config_version_positive",
    ),
    sa.CheckConstraint(
        "schema_version > 0",
        name="ck_configuration_snapshots_schema_version_positive",
    ),
    sa.CheckConstraint(
        "digest ~ '^sha256:[0-9a-f]{64}$'",
        name="ck_configuration_snapshots_digest",
    ),
    sa.CheckConstraint(
        "jsonb_typeof(document) = 'object'",
        name="ck_configuration_snapshots_document_object",
    ),
    sa.PrimaryKeyConstraint(
        "configuration_snapshot_id",
        name="pk_configuration_snapshots",
    ),
    sa.UniqueConstraint(
        "digest",
        name="uq_configuration_snapshots_digest",
    ),
    sa.UniqueConstraint(
        "configuration_snapshot_id",
        "digest",
        name="uq_configuration_snapshots_id_digest",
    ),
)

users = sa.Table(
    "users",
    metadata,
    sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint("user_id", name="pk_users"),
)

sources = sa.Table(
    "sources",
    metadata,
    sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column("source_key", sa.String(length=64), nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("retired_at", sa.DateTime(timezone=True), nullable=True),
    sa.CheckConstraint(
        "source_key ~ '^[a-z][a-z0-9-]*$'",
        name="ck_sources_source_key",
    ),
    sa.CheckConstraint(
        "retired_at IS NULL OR retired_at >= created_at",
        name="ck_sources_retired_after_created",
    ),
    sa.PrimaryKeyConstraint("source_id", name="pk_sources"),
    sa.UniqueConstraint("source_key", name="uq_sources_source_key"),
)

properties = sa.Table(
    "properties",
    metadata,
    sa.Column("property_id", postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint("property_id", name="pk_properties"),
)

listings = sa.Table(
    "listings",
    metadata,
    sa.Column("listing_id", postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column("source_external_id", sa.String(length=512), nullable=True),
    sa.Column("source_listing_key", sa.String(length=512), nullable=True),
    sa.Column("canonical_url", sa.Text(), nullable=True),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(
        ["source_id"],
        ["sources.source_id"],
        name="fk_listings_source_id_sources",
        ondelete="RESTRICT",
    ),
    sa.CheckConstraint(
        "source_listing_key IS NULL OR "
        "(source_listing_key = btrim(source_listing_key) AND length(source_listing_key) > 0)",
        name="ck_listings_source_listing_key",
    ),
    sa.PrimaryKeyConstraint("listing_id", name="pk_listings"),
    sa.UniqueConstraint(
        "source_id",
        "source_listing_key",
        name="uq_listings_source_listing_key",
    ),
    sa.UniqueConstraint(
        "listing_id",
        "source_id",
        name="uq_listings_id_source",
    ),
)

polling_runs = sa.Table(
    "polling_runs",
    metadata,
    sa.Column("polling_run_id", postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column(
        "configuration_snapshot_id",
        postgresql.UUID(as_uuid=True),
        nullable=False,
    ),
    sa.Column("configuration_digest", sa.String(length=71), nullable=False),
    sa.Column("run_kind", sa.String(length=64), nullable=False),
    sa.Column("trigger_kind", sa.String(length=32), nullable=False),
    sa.Column("state", sa.String(length=32), nullable=False),
    sa.Column("idempotency_key", sa.String(length=255), nullable=False),
    sa.Column("correlation_id", postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=True),
    sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column(
        "aggregate_counts",
        postgresql.JSONB(astext_type=sa.Text()),
        nullable=False,
    ),
    sa.Column(
        "outcome",
        postgresql.JSONB(astext_type=sa.Text()),
        nullable=True,
    ),
    sa.CheckConstraint(
        "configuration_digest ~ '^sha256:[0-9a-f]{64}$'",
        name="ck_polling_runs_configuration_digest",
    ),
    sa.CheckConstraint(
        "run_kind = btrim(run_kind) AND length(run_kind) > 0",
        name="ck_polling_runs_run_kind",
    ),
    sa.CheckConstraint(
        "trigger_kind = btrim(trigger_kind) AND length(trigger_kind) > 0",
        name="ck_polling_runs_trigger_kind",
    ),
    sa.CheckConstraint(
        "state = btrim(state) AND length(state) > 0",
        name="ck_polling_runs_state",
    ),
    sa.CheckConstraint(
        "idempotency_key = btrim(idempotency_key) AND length(idempotency_key) > 0",
        name="ck_polling_runs_idempotency_key",
    ),
    sa.CheckConstraint(
        "finished_at IS NULL OR finished_at >= started_at",
        name="ck_polling_runs_finished_after_started",
    ),
    sa.CheckConstraint(
        "jsonb_typeof(aggregate_counts) = 'object'",
        name="ck_polling_runs_aggregate_counts_object",
    ),
    sa.CheckConstraint(
        "outcome IS NULL OR jsonb_typeof(outcome) = 'object'",
        name="ck_polling_runs_outcome_object",
    ),
    sa.ForeignKeyConstraint(
        ["configuration_snapshot_id", "configuration_digest"],
        [
            "configuration_snapshots.configuration_snapshot_id",
            "configuration_snapshots.digest",
        ],
        name="fk_polling_runs_configuration_snapshot",
        ondelete="RESTRICT",
    ),
    sa.ForeignKeyConstraint(
        ["user_id"],
        ["users.user_id"],
        name="fk_polling_runs_user_id_users",
        ondelete="RESTRICT",
    ),
    sa.PrimaryKeyConstraint("polling_run_id", name="pk_polling_runs"),
    sa.UniqueConstraint(
        "run_kind",
        "idempotency_key",
        name="uq_polling_runs_kind_idempotency",
    ),
)

source_runs = sa.Table(
    "source_runs",
    metadata,
    sa.Column("source_run_id", postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column("polling_run_id", postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column("search_id", postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column("search_version", sa.Integer(), nullable=False),
    sa.Column("adapter_name", sa.String(length=64), nullable=False),
    sa.Column("adapter_version", sa.String(length=64), nullable=False),
    sa.Column("state", sa.String(length=32), nullable=False),
    sa.Column("idempotency_key", sa.String(length=255), nullable=False),
    sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("finished_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column(
        "aggregate_counts",
        postgresql.JSONB(astext_type=sa.Text()),
        nullable=False,
    ),
    sa.Column(
        "outcome",
        postgresql.JSONB(astext_type=sa.Text()),
        nullable=True,
    ),
    sa.CheckConstraint(
        "search_version > 0",
        name="ck_source_runs_search_version_positive",
    ),
    sa.CheckConstraint(
        "adapter_name = btrim(adapter_name) AND length(adapter_name) > 0",
        name="ck_source_runs_adapter_name",
    ),
    sa.CheckConstraint(
        "adapter_version = btrim(adapter_version) AND length(adapter_version) > 0",
        name="ck_source_runs_adapter_version",
    ),
    sa.CheckConstraint(
        "state = btrim(state) AND length(state) > 0",
        name="ck_source_runs_state",
    ),
    sa.CheckConstraint(
        "idempotency_key = btrim(idempotency_key) AND length(idempotency_key) > 0",
        name="ck_source_runs_idempotency_key",
    ),
    sa.CheckConstraint(
        "finished_at >= started_at",
        name="ck_source_runs_finished_after_started",
    ),
    sa.CheckConstraint(
        "jsonb_typeof(aggregate_counts) = 'object'",
        name="ck_source_runs_aggregate_counts_object",
    ),
    sa.CheckConstraint(
        "outcome IS NULL OR jsonb_typeof(outcome) = 'object'",
        name="ck_source_runs_outcome_object",
    ),
    sa.ForeignKeyConstraint(
        ["polling_run_id"],
        ["polling_runs.polling_run_id"],
        name="fk_source_runs_polling_run_id_polling_runs",
        ondelete="RESTRICT",
    ),
    sa.ForeignKeyConstraint(
        ["source_id"],
        ["sources.source_id"],
        name="fk_source_runs_source_id_sources",
        ondelete="RESTRICT",
    ),
    sa.PrimaryKeyConstraint("source_run_id", name="pk_source_runs"),
    sa.UniqueConstraint(
        "source_id",
        "idempotency_key",
        name="uq_source_runs_source_idempotency",
    ),
    sa.UniqueConstraint(
        "source_run_id",
        "source_id",
        name="uq_source_runs_id_source",
    ),
    sa.Index("ix_source_runs_source_started_at", "source_id", "started_at"),
)

raw_objects = sa.Table(
    "raw_objects",
    metadata,
    sa.Column("raw_object_id", postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column("checksum", sa.String(length=71), nullable=False),
    sa.Column("byte_size", sa.BigInteger(), nullable=False),
    sa.Column("media_type", sa.String(length=255), nullable=False),
    sa.Column("storage_adapter", sa.String(length=64), nullable=False),
    sa.Column("storage_key", sa.Text(), nullable=False),
    sa.Column("lifecycle_state", sa.String(length=32), nullable=False),
    sa.Column("replay_eligible", sa.Boolean(), nullable=False),
    sa.Column("retention_policy_reference", sa.String(length=128), nullable=False),
    sa.Column("compliance_reference", sa.String(length=128), nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("verified_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    sa.CheckConstraint(
        "checksum ~ '^sha256:[0-9a-f]{64}$'",
        name="ck_raw_objects_checksum",
    ),
    sa.CheckConstraint("byte_size > 0", name="ck_raw_objects_byte_size_positive"),
    sa.CheckConstraint(
        "media_type = btrim(media_type) AND length(media_type) > 0",
        name="ck_raw_objects_media_type",
    ),
    sa.CheckConstraint(
        "storage_adapter = btrim(storage_adapter) AND length(storage_adapter) > 0",
        name="ck_raw_objects_storage_adapter",
    ),
    sa.CheckConstraint("length(storage_key) > 0", name="ck_raw_objects_storage_key"),
    sa.CheckConstraint(
        "lifecycle_state = btrim(lifecycle_state) AND length(lifecycle_state) > 0",
        name="ck_raw_objects_lifecycle_state",
    ),
    sa.CheckConstraint(
        "verified_at >= created_at",
        name="ck_raw_objects_verified_after_created",
    ),
    sa.CheckConstraint(
        "expires_at IS NULL OR expires_at >= created_at",
        name="ck_raw_objects_expires_after_created",
    ),
    sa.ForeignKeyConstraint(
        ["source_id"],
        ["sources.source_id"],
        name="fk_raw_objects_source_id_sources",
        ondelete="RESTRICT",
    ),
    sa.PrimaryKeyConstraint("raw_object_id", name="pk_raw_objects"),
    sa.UniqueConstraint(
        "source_id",
        "checksum",
        "storage_adapter",
        "storage_key",
        name="uq_raw_objects_source_storage_identity",
    ),
    sa.UniqueConstraint(
        "raw_object_id",
        "source_id",
        name="uq_raw_objects_id_source",
    ),
)

observations = sa.Table(
    "observations",
    metadata,
    sa.Column("observation_id", postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column("listing_id", postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column("raw_object_id", postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("requested_url", sa.Text(), nullable=False),
    sa.Column("final_url", sa.Text(), nullable=False),
    sa.Column("outcome", sa.String(length=32), nullable=False),
    sa.Column("page_classification", sa.String(length=64), nullable=False),
    sa.Column("capture_mode", sa.String(length=32), nullable=False),
    sa.Column("content_checksum", sa.String(length=71), nullable=False),
    sa.Column("content_size", sa.BigInteger(), nullable=False),
    sa.Column("media_type", sa.String(length=255), nullable=False),
    sa.Column("replay_eligible", sa.Boolean(), nullable=False),
    sa.Column("retention_policy_reference", sa.String(length=128), nullable=False),
    sa.Column("compliance_reference", sa.String(length=128), nullable=False),
    sa.Column("idempotency_fingerprint", sa.String(length=71), nullable=False),
    sa.CheckConstraint(
        "outcome IN ('SUCCESS', 'PARTIAL', 'FAILED')",
        name="ck_observations_outcome",
    ),
    sa.CheckConstraint(
        "page_classification = btrim(page_classification) AND length(page_classification) > 0",
        name="ck_observations_page_classification",
    ),
    sa.CheckConstraint(
        "capture_mode IN "
        "('FULL_PAYLOAD', 'SANITIZED_PAYLOAD', 'RELEVANT_FRAGMENTS', "
        "'STRUCTURED_FACTS_ONLY', 'METADATA_ONLY', 'TRANSIENT')",
        name="ck_observations_capture_mode",
    ),
    sa.CheckConstraint(
        "content_checksum ~ '^sha256:[0-9a-f]{64}$'",
        name="ck_observations_content_checksum",
    ),
    sa.CheckConstraint(
        "idempotency_fingerprint ~ '^sha256:[0-9a-f]{64}$'",
        name="ck_observations_idempotency_fingerprint",
    ),
    sa.CheckConstraint(
        "content_size > 0",
        name="ck_observations_content_size_positive",
    ),
    sa.ForeignKeyConstraint(
        ["listing_id", "source_id"],
        ["listings.listing_id", "listings.source_id"],
        name="fk_observations_listing_source_listings",
        ondelete="RESTRICT",
    ),
    sa.ForeignKeyConstraint(
        ["raw_object_id", "source_id"],
        ["raw_objects.raw_object_id", "raw_objects.source_id"],
        name="fk_observations_raw_object_source_raw_objects",
        ondelete="RESTRICT",
    ),
    sa.ForeignKeyConstraint(
        ["source_id"],
        ["sources.source_id"],
        name="fk_observations_source_id_sources",
        ondelete="RESTRICT",
    ),
    sa.PrimaryKeyConstraint("observation_id", name="pk_observations"),
    sa.UniqueConstraint(
        "observation_id",
        "source_id",
        name="uq_observations_id_source",
    ),
    sa.UniqueConstraint(
        "source_id",
        "idempotency_fingerprint",
        name="uq_observations_source_fingerprint",
    ),
    sa.Index("ix_observations_listing_observed_at", "listing_id", "observed_at"),
)

source_run_observations = sa.Table(
    "source_run_observations",
    metadata,
    sa.Column("source_run_id", postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column("observation_id", postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(
        ["source_run_id", "source_id"],
        ["source_runs.source_run_id", "source_runs.source_id"],
        name="fk_source_run_observations_run_source",
        ondelete="RESTRICT",
    ),
    sa.ForeignKeyConstraint(
        ["observation_id", "source_id"],
        ["observations.observation_id", "observations.source_id"],
        name="fk_source_run_observations_observation_source",
        ondelete="RESTRICT",
    ),
    sa.PrimaryKeyConstraint(
        "source_run_id",
        "observation_id",
        name="pk_source_run_observations",
    ),
    sa.Index(
        "ix_source_run_observations_observation_id",
        "observation_id",
    ),
)

parse_runs = sa.Table(
    "parse_runs",
    metadata,
    sa.Column("parse_run_id", postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column("observation_id", postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column("parser_name", sa.String(length=64), nullable=False),
    sa.Column("parser_version", sa.String(length=64), nullable=False),
    sa.Column("schema_version", sa.Integer(), nullable=False),
    sa.Column("input_checksum", sa.String(length=71), nullable=False),
    sa.Column("result", sa.String(length=32), nullable=False),
    sa.Column("idempotency_key", sa.String(length=71), nullable=False),
    sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("finished_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column(
        "warnings",
        postgresql.JSONB(astext_type=sa.Text()),
        nullable=False,
    ),
    sa.Column(
        "error",
        postgresql.JSONB(astext_type=sa.Text()),
        nullable=True,
    ),
    sa.CheckConstraint(
        "parser_name = btrim(parser_name) AND length(parser_name) > 0",
        name="ck_parse_runs_parser_name",
    ),
    sa.CheckConstraint(
        "parser_version = btrim(parser_version) AND length(parser_version) > 0",
        name="ck_parse_runs_parser_version",
    ),
    sa.CheckConstraint(
        "schema_version > 0",
        name="ck_parse_runs_schema_version_positive",
    ),
    sa.CheckConstraint(
        "input_checksum ~ '^sha256:[0-9a-f]{64}$'",
        name="ck_parse_runs_input_checksum",
    ),
    sa.CheckConstraint(
        "idempotency_key ~ '^sha256:[0-9a-f]{64}$'",
        name="ck_parse_runs_idempotency_key",
    ),
    sa.CheckConstraint(
        "result IN ('SUCCESS', 'PARTIAL', 'FAILED', 'NOT_REPLAYABLE')",
        name="ck_parse_runs_result",
    ),
    sa.CheckConstraint(
        "finished_at >= started_at",
        name="ck_parse_runs_finished_after_started",
    ),
    sa.CheckConstraint(
        "jsonb_typeof(warnings) = 'array'",
        name="ck_parse_runs_warnings_array",
    ),
    sa.CheckConstraint(
        "error IS NULL OR jsonb_typeof(error) = 'object'",
        name="ck_parse_runs_error_object",
    ),
    sa.ForeignKeyConstraint(
        ["observation_id"],
        ["observations.observation_id"],
        name="fk_parse_runs_observation_id_observations",
        ondelete="RESTRICT",
    ),
    sa.PrimaryKeyConstraint("parse_run_id", name="pk_parse_runs"),
    sa.UniqueConstraint(
        "observation_id",
        "parser_name",
        "parser_version",
        "input_checksum",
        name="uq_parse_runs_observation_parser_input",
    ),
    sa.UniqueConstraint(
        "parse_run_id",
        "observation_id",
        name="uq_parse_runs_id_observation",
    ),
)

source_facts = sa.Table(
    "source_facts",
    metadata,
    sa.Column("source_fact_id", postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column("parse_run_id", postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column("observation_id", postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column("fact_key", sa.String(length=128), nullable=False),
    sa.Column("fact_type", sa.String(length=64), nullable=False),
    sa.Column("field_path", sa.String(length=255), nullable=False),
    sa.Column("value_state", sa.String(length=32), nullable=False),
    sa.Column(
        "raw_value",
        postgresql.JSONB(astext_type=sa.Text(), none_as_null=True),
        nullable=True,
    ),
    sa.Column(
        "normalized_value",
        postgresql.JSONB(astext_type=sa.Text(), none_as_null=True),
        nullable=True,
    ),
    sa.Column("language", sa.String(length=16), nullable=True),
    sa.Column("unit", sa.String(length=32), nullable=True),
    sa.Column("schema_version", sa.Integer(), nullable=False),
    sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint(
        "fact_key = btrim(fact_key) AND length(fact_key) > 0",
        name="ck_source_facts_fact_key",
    ),
    sa.CheckConstraint(
        "fact_type = btrim(fact_type) AND length(fact_type) > 0",
        name="ck_source_facts_fact_type",
    ),
    sa.CheckConstraint(
        "field_path = btrim(field_path) AND length(field_path) > 0",
        name="ck_source_facts_field_path",
    ),
    sa.CheckConstraint(
        "value_state IN ('PRESENT', 'UNKNOWN', 'MALFORMED')",
        name="ck_source_facts_value_state",
    ),
    sa.CheckConstraint(
        "(value_state = 'PRESENT' AND raw_value IS NOT NULL "
        "AND normalized_value IS NOT NULL) "
        "OR (value_state = 'UNKNOWN' AND normalized_value IS NULL) "
        "OR (value_state = 'MALFORMED' AND raw_value IS NOT NULL "
        "AND normalized_value IS NULL)",
        name="ck_source_facts_value_shape",
    ),
    sa.CheckConstraint(
        "schema_version > 0",
        name="ck_source_facts_schema_version_positive",
    ),
    sa.ForeignKeyConstraint(
        ["parse_run_id", "observation_id"],
        ["parse_runs.parse_run_id", "parse_runs.observation_id"],
        name="fk_source_facts_parse_run_observation",
        ondelete="RESTRICT",
    ),
    sa.PrimaryKeyConstraint("source_fact_id", name="pk_source_facts"),
    sa.UniqueConstraint(
        "parse_run_id",
        "fact_key",
        name="uq_source_facts_parse_run_fact_key",
    ),
)
