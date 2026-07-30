"""PostgreSQL persistence operations for the Phase 1 foundation use case."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import Connection

from homesearch.adapters.database.schema import (
    configuration_snapshots,
    sources,
    users,
)
from homesearch.application import (
    ConfigurationSnapshotWrite,
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
