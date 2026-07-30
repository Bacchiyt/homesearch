# ADR 0008: Raw Observation Storage and Retention

## Status

Accepted

## Context

Replayable source evidence is valuable for parser changes and audits, but raw HTML, JSON, images, and documents can carry copyright, privacy, storage, and source-policy constraints. Phase 1 has no approved live source and should not build an unused object-storage system. Phase 2 needs synthetic/manual ingestion to prove immutable observation and retention semantics.

## Decision

Gate A accepts the following decision:

### Phase 1 preparation

- preserve the architecture boundary between relational observation metadata and optional raw-object content;
- define configuration vocabulary for capture mode, retention policy, and storage adapter;
- do not create live payloads, an object-storage service, or raw-body tables solely for future use; and
- keep source facts/provenance able to represent `TRANSIENT`, `METADATA_ONLY`, and `STORED` capture outcomes.

### Phase 2 storage

- store immutable observation/fetch metadata in PostgreSQL: source/listing/run references, requested/final URL, outcome/status, content type/size/hash, observed/recorded times, capture mode, replay eligibility, parser version/result, and retention/compliance policy reference;
- store permitted extracted source text and structured facts with observation provenance;
- store a raw payload only when the source assessment and configured policy permit it;
- keep raw bytes outside core relational rows behind a provider-neutral object-storage port, referenced by content hash, size, media type, logical key, and lifecycle state;
- use repo-ignored, checksum-addressed compressed files under `var/raw/` for local synthetic/permitted development data;
- use S3-compatible or equivalent object storage only when production retention, durability, and cost justify it; no provider is selected here;
- retain source image URLs and observation metadata by default, not downloaded image bytes. Store permitted hashes/thumbnails/originals only under a later media policy; and
- never commit raw payloads or dumps. Test fixtures must be minimal, permitted/synthetic, redacted, and separately attributable.

Retention is tiered and versioned:

- observation identity, fetch metadata, checksums, parse outcomes, extracted facts, and provenance are retained as durable history unless law/policy requires audited erasure;
- raw body/blob retention is source- and content-class-specific, can be zero, and has explicit expiry;
- expiry removes or tombstones the object through an auditable lifecycle without cascading into facts, properties, events, or notifications;
- no default means “store everything forever”; and
- policy changes affect future capture unless an explicit audited lifecycle job applies them to existing objects.

## Alternatives considered

- **Store every body forever in PostgreSQL:** simple transactions but creates database growth, backup, copyright/privacy, and retention coupling.
- **Store every body forever in object storage:** cheaper at scale but still unjustified legally and operationally.
- **Never store raw bodies:** minimizes risk but prevents permitted replay and parser debugging.
- **Build production object storage in Phase 1:** premature because no source or retention policy is approved.
- **Store downloaded listing images by default:** rejected due to copyright, volume, staleness, and limited early value.

## Consequences

- Phase 2 can demonstrate replay and expiry without committing to a cloud provider.
- Some observations will intentionally be non-replayable after transient parsing or expiry.
- Durable relational evidence remains meaningful after raw content is removed.
- Production backup/export includes a manifest and checksums for retained permitted objects.

## Risks/trade-offs

- Extracted text can itself be copyrighted or sensitive; “not raw bytes” is not an exemption.
- Content-addressed deduplication can conflict with source-specific erasure unless references and lifecycle are policy-aware.
- Local files are not production durability and must not become the only copy of valuable evidence.
- URL retention can leak tokens or personal query data; URLs require normalization/redaction policy.

## Follow-up/validation

- Gate A accepted the staged boundary, not any live capture.
- Gate B defines capture/fixture/retention permission per source before access.
- Phase 2 tests immutable metadata, checksum verification, missing/expired object behavior, replay eligibility, and non-cascading expiry with synthetic data.
- Before production raw retention, define encryption, RPO/RTO, lifecycle cost, legal deletion, and restore verification.

## Date

2026-07-30
