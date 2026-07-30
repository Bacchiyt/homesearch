"""Create the initial Phase 1 persistence foundation.

Revision ID: 20260731_0001
Revises:
Create Date: 2026-07-31
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260731_0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create only the Phase 1 identity, configuration, and run-ledger anchors."""

    op.create_table(
        "configuration_snapshots",
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

    op.create_table(
        "users",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("user_id", name="pk_users"),
    )

    op.create_table(
        "sources",
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

    op.create_table(
        "properties",
        sa.Column("property_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("property_id", name="pk_properties"),
    )

    op.create_table(
        "listings",
        sa.Column("listing_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_external_id", sa.String(length=512), nullable=True),
        sa.Column("canonical_url", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["sources.source_id"],
            name="fk_listings_source_id_sources",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("listing_id", name="pk_listings"),
    )

    op.create_table(
        "polling_runs",
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


def downgrade() -> None:
    """Return to Alembic base without deleting any pre-existing database objects."""

    op.drop_table("polling_runs")
    op.drop_table("listings")
    op.drop_table("properties")
    op.drop_table("sources")
    op.drop_table("users")
    op.drop_table("configuration_snapshots")
