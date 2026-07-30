"""Application-owned persistence use case for the Phase 1 foundation."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol, Self
from uuid import UUID, uuid7

from homesearch.config import LoadedConfiguration

Clock = Callable[[], datetime]
IdFactory = Callable[[], UUID]


class PersistenceConflictError(RuntimeError):
    """A durable identity conflicts with already persisted state."""


@dataclass(frozen=True, slots=True)
class ConfigurationSnapshotWrite:
    """Secret-free effective configuration ready for durable persistence."""

    configuration_snapshot_id: UUID
    config_id: str
    config_version: int
    schema_version: int
    effective_from: datetime
    recorded_at: datetime
    digest: str
    document: Mapping[str, object]


class FoundationRepository(Protocol):
    """Persistence operations required by the Phase 1 bootstrap use case."""

    def persist_configuration_snapshot(
        self,
        snapshot: ConfigurationSnapshotWrite,
    ) -> UUID:
        """Persist or return the immutable snapshot identified by its digest."""

    def ensure_user(self, user_id: UUID, created_at: datetime) -> None:
        """Ensure the configured user identity exists without rewriting it."""

    def ensure_source(
        self,
        source_id: UUID,
        source_key: str,
        created_at: datetime,
    ) -> None:
        """Ensure a source ID/key pair exists without silently remapping it."""


class FoundationUnitOfWork(Protocol):
    """Use-case-owned transaction containing the foundation repository."""

    @property
    def foundation(self) -> FoundationRepository:
        """Return the repository bound to the active transaction."""

    def __enter__(self) -> Self:
        """Open the transaction scope."""

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: object | None,
    ) -> None:
        """Rollback uncommitted work and release the connection."""

    def commit(self) -> None:
        """Commit the complete application use case atomically."""

    def rollback(self) -> None:
        """Rollback the complete application use case."""


UnitOfWorkFactory = Callable[[], FoundationUnitOfWork]


def _utc_instant(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("system clock must return a timezone-aware instant")
    return value.astimezone(UTC)


def _uuid7(identifier: UUID) -> UUID:
    if identifier.version != 7:
        raise ValueError("new durable IDs must be application-generated UUIDv7 values")
    return identifier


def _system_clock() -> datetime:
    return datetime.now(UTC)


def persist_configuration_foundation(
    configuration: LoadedConfiguration,
    unit_of_work_factory: UnitOfWorkFactory,
    *,
    clock: Clock = _system_clock,
    id_factory: IdFactory = uuid7,
) -> UUID:
    """Atomically persist a safe configuration and its configured identities."""

    recorded_at = _utc_instant(clock())
    snapshot = ConfigurationSnapshotWrite(
        configuration_snapshot_id=_uuid7(id_factory()),
        config_id=configuration.configuration.config_id,
        config_version=configuration.configuration.config_version,
        schema_version=configuration.configuration.schema_version,
        effective_from=configuration.configuration.effective_from,
        recorded_at=recorded_at,
        digest=configuration.digest,
        document=configuration.configuration.model_dump(mode="json"),
    )

    with unit_of_work_factory() as unit_of_work:
        persisted_snapshot_id = unit_of_work.foundation.persist_configuration_snapshot(snapshot)
        for user in configuration.configuration.user_scope.users:
            unit_of_work.foundation.ensure_user(user.user_id, recorded_at)
        for source in configuration.configuration.source_registry.sources:
            unit_of_work.foundation.ensure_source(
                source.source_id,
                source.source_key,
                recorded_at,
            )
        unit_of_work.commit()

    return persisted_snapshot_id
