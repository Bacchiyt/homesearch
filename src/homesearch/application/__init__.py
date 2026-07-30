"""Application use cases and persistence ports."""

from homesearch.application.ingestion import (
    FactValueState,
    IngestionReceipt,
    IngestionRepository,
    IngestionUnitOfWork,
    IngestionWrite,
    IngestSourceCommand,
    NormalizedIngestionResult,
    ObservationOutcome,
    ParseResult,
    SourceFactInput,
    SourceIngestionAdapter,
    SourceTransport,
    ingest_source,
)
from homesearch.application.persistence import (
    ConfigurationSnapshotWrite,
    FoundationRepository,
    FoundationUnitOfWork,
    PersistenceConflictError,
    persist_configuration_foundation,
)

__all__ = [
    "ConfigurationSnapshotWrite",
    "FactValueState",
    "FoundationRepository",
    "FoundationUnitOfWork",
    "IngestionReceipt",
    "IngestionRepository",
    "IngestionUnitOfWork",
    "IngestionWrite",
    "IngestSourceCommand",
    "NormalizedIngestionResult",
    "ObservationOutcome",
    "ParseResult",
    "PersistenceConflictError",
    "SourceFactInput",
    "SourceIngestionAdapter",
    "SourceTransport",
    "ingest_source",
    "persist_configuration_foundation",
]
