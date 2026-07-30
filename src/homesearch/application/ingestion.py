"""Application contracts and use case for deterministic source ingestion."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Protocol, Self
from uuid import UUID, uuid7

from homesearch.config import LoadedConfiguration
from homesearch.config.models import CaptureMode, SourceCapability

Clock = Callable[[], datetime]
IdFactory = Callable[[], UUID]


class SourceTransport(StrEnum):
    """How an adapter obtains evidence for this application command."""

    FIXTURE = "FIXTURE"


class ObservationOutcome(StrEnum):
    """Normalized outcome for one received source observation."""

    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


class ParseResult(StrEnum):
    """Immutable result of one parser version against an observation."""

    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    NOT_REPLAYABLE = "NOT_REPLAYABLE"


class FactValueState(StrEnum):
    """Whether a source fact contains a usable value."""

    PRESENT = "PRESENT"
    UNKNOWN = "UNKNOWN"
    MALFORMED = "MALFORMED"


@dataclass(frozen=True, slots=True)
class SourceFactInput:
    """One normalized source claim produced by an adapter parser."""

    fact_key: str
    fact_type: str
    field_path: str
    value_state: FactValueState
    raw_value: object | None
    normalized_value: object | None
    language: str | None = None
    unit: str | None = None


@dataclass(frozen=True, slots=True)
class NormalizedIngestionResult:
    """Adapter-neutral observation, parse metadata, and source facts."""

    reference: str
    source_external_id: str
    source_listing_key: str
    canonical_url: str
    observed_at: datetime
    requested_url: str
    final_url: str
    outcome: ObservationOutcome
    page_classification: str
    capture_mode: CaptureMode
    content_checksum: str
    content_size: int
    media_type: str
    replay_eligible: bool
    storage_adapter: str
    storage_key: str
    retention_policy_reference: str
    compliance_reference: str
    parser_name: str
    parser_version: str
    parser_schema_version: int
    parse_result: ParseResult
    facts: tuple[SourceFactInput, ...]
    warnings: tuple[str, ...] = ()


class SourceIngestionAdapter(Protocol):
    """Typed source boundary consumed by the ingestion application use case."""

    @property
    def source_id(self) -> UUID:
        """Return the configured source identity implemented by this adapter."""

    @property
    def source_key(self) -> str:
        """Return the configured readable source key."""

    @property
    def transport(self) -> SourceTransport:
        """Describe how this adapter obtains evidence."""

    @property
    def adapter_name(self) -> str:
        """Return the stable adapter implementation name."""

    @property
    def adapter_version(self) -> str:
        """Return the adapter contract/implementation version."""

    def ingest(self, reference: str) -> NormalizedIngestionResult:
        """Load and normalize one source reference without persistence effects."""


@dataclass(frozen=True, slots=True)
class IngestSourceCommand:
    """Configured identity context for one manually invoked ingestion."""

    configuration_snapshot_id: UUID
    source_id: UUID
    search_id: UUID
    reference: str


@dataclass(frozen=True, slots=True)
class IngestionWrite:
    """Complete immutable write set owned by one application transaction."""

    polling_run_id: UUID
    source_run_id: UUID
    raw_object_id: UUID
    listing_id: UUID
    observation_id: UUID
    parse_run_id: UUID
    source_fact_ids: tuple[UUID, ...]
    user_id: UUID
    configuration_snapshot_id: UUID
    configuration_digest: str
    source_id: UUID
    search_id: UUID
    search_version: int
    correlation_id: UUID
    command_idempotency_key: str
    observation_fingerprint: str
    parse_idempotency_key: str
    recorded_at: datetime
    adapter_name: str
    adapter_version: str
    result: NormalizedIngestionResult


@dataclass(frozen=True, slots=True)
class IngestionReceipt:
    """Durable identities for one logical fixture-ingestion effect."""

    polling_run_id: UUID
    source_run_id: UUID
    listing_id: UUID
    observation_id: UUID
    parse_run_id: UUID
    correlation_id: UUID
    created: bool


class IngestionRepository(Protocol):
    """Persistence operation required by the first Phase 2 ingestion use case."""

    def persist_ingestion(self, write: IngestionWrite) -> IngestionReceipt:
        """Atomically persist or return one idempotent ingestion result."""


class IngestionUnitOfWork(Protocol):
    """Use-case-owned transaction containing the ingestion repository."""

    @property
    def ingestion(self) -> IngestionRepository:
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


IngestionUnitOfWorkFactory = Callable[[], IngestionUnitOfWork]


def _utc_instant(value: datetime, *, field: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware")
    return value.astimezone(UTC)


def _uuid7(identifier: UUID) -> UUID:
    if identifier.version != 7:
        raise ValueError("new durable IDs must be application-generated UUIDv7 values")
    return identifier


def _fingerprint(parts: Mapping[str, object]) -> str:
    canonical = json.dumps(
        parts,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    return f"sha256:{hashlib.sha256(canonical).hexdigest()}"


def _system_clock() -> datetime:
    return datetime.now(UTC)


def _configured_context(
    configuration: LoadedConfiguration,
    command: IngestSourceCommand,
    adapter: SourceIngestionAdapter,
) -> tuple[UUID, int, CaptureMode]:
    if adapter.transport is not SourceTransport.FIXTURE:
        raise ValueError("this Phase 2 command accepts fixture-backed adapters only")
    if adapter.source_id != command.source_id:
        raise ValueError("adapter source_id does not match the ingestion command")

    source = next(
        (
            source
            for source in configuration.configuration.source_registry.sources
            if source.source_id == command.source_id
        ),
        None,
    )
    if source is None or source.source_key != adapter.source_key:
        raise ValueError("adapter source must match configured source identity")
    if SourceCapability.MANUAL_IMPORT not in source.capabilities:
        raise ValueError("fixture ingestion requires MANUAL_IMPORT source capability")

    search = next(
        (
            search
            for search in configuration.configuration.search_registry.searches
            if search.search_id == command.search_id
        ),
        None,
    )
    if search is None or command.source_id not in search.source_ids:
        raise ValueError("search must reference the ingestion source")
    return search.user_id, search.search_version, source.capture_policy.capture_mode


def ingest_source(
    configuration: LoadedConfiguration,
    command: IngestSourceCommand,
    adapter: SourceIngestionAdapter,
    unit_of_work_factory: IngestionUnitOfWorkFactory,
    *,
    clock: Clock = _system_clock,
    id_factory: IdFactory = uuid7,
) -> IngestionReceipt:
    """Normalize and atomically persist one deterministic fixture observation."""

    user_id, search_version, configured_capture_mode = _configured_context(
        configuration,
        command,
        adapter,
    )
    if command.configuration_snapshot_id.version != 7:
        raise ValueError("configuration_snapshot_id must be a UUIDv7 value")
    if not command.reference.strip():
        raise ValueError("ingestion reference must be non-blank")

    result = adapter.ingest(command.reference)
    if result.reference != command.reference:
        raise ValueError("adapter result reference does not match the ingestion command")
    observed_at = _utc_instant(result.observed_at, field="observed_at")
    recorded_at = _utc_instant(clock(), field="system clock")
    if result.capture_mode is not configured_capture_mode:
        raise ValueError("adapter capture mode does not match configured source policy")
    if result.capture_mode is not CaptureMode.FULL_PAYLOAD:
        raise ValueError("the first fixture slice requires FULL_PAYLOAD capture")
    if not result.replay_eligible:
        raise ValueError("the first fixture slice requires replayable evidence")
    if not result.facts:
        raise ValueError("normalized ingestion must contain at least one source fact")
    fact_keys = [fact.fact_key for fact in result.facts]
    if len(fact_keys) != len(set(fact_keys)):
        raise ValueError("source fact keys must be unique within one parse result")

    observation_fingerprint = _fingerprint(
        {
            "content_checksum": result.content_checksum,
            "observed_at": observed_at.isoformat(),
            "source_id": str(command.source_id),
            "source_listing_key": result.source_listing_key,
        }
    )
    parse_idempotency_key = _fingerprint(
        {
            "input_checksum": result.content_checksum,
            "observation_fingerprint": observation_fingerprint,
            "parser_name": result.parser_name,
            "parser_schema_version": result.parser_schema_version,
            "parser_version": result.parser_version,
        }
    )
    command_idempotency_key = _fingerprint(
        {
            "adapter_name": adapter.adapter_name,
            "adapter_version": adapter.adapter_version,
            "configuration_digest": configuration.digest,
            "parse_idempotency_key": parse_idempotency_key,
            "reference": result.reference,
            "search_id": str(command.search_id),
            "search_version": search_version,
            "source_id": str(command.source_id),
        }
    )

    write = IngestionWrite(
        polling_run_id=_uuid7(id_factory()),
        source_run_id=_uuid7(id_factory()),
        raw_object_id=_uuid7(id_factory()),
        listing_id=_uuid7(id_factory()),
        observation_id=_uuid7(id_factory()),
        parse_run_id=_uuid7(id_factory()),
        source_fact_ids=tuple(_uuid7(id_factory()) for _ in result.facts),
        user_id=user_id,
        configuration_snapshot_id=command.configuration_snapshot_id,
        configuration_digest=configuration.digest,
        source_id=command.source_id,
        search_id=command.search_id,
        search_version=search_version,
        correlation_id=_uuid7(id_factory()),
        command_idempotency_key=command_idempotency_key,
        observation_fingerprint=observation_fingerprint,
        parse_idempotency_key=parse_idempotency_key,
        recorded_at=recorded_at,
        adapter_name=adapter.adapter_name,
        adapter_version=adapter.adapter_version,
        result=result,
    )

    with unit_of_work_factory() as unit_of_work:
        receipt = unit_of_work.ingestion.persist_ingestion(write)
        unit_of_work.commit()
    return receipt
