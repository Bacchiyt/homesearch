# Ingestion Data Model

Read with [Conceptual data model](../data-model.md) and [Source requirements](../product/source-and-ingestion.md).

## `Source`

**Purpose:** stable identity for a portal, broker, developer, seller, dataset, feed, or manual origin, independent of adapter implementation.

**Important fields:** `source_id`, stable key/name, kind, homepage/base identity, lifecycle (`ENABLED`, `DISABLED`, `PAUSED`, `RETIRED`), adapter compatibility, access-assessment reference/status, policy references, and created/retired times.

Configuration is versioned separately. Retiring a source never deletes its history.

## `SourceConfigurationVersion`

**Purpose:** immutable non-secret source policy used by runs.

**Important fields:** source/version, capabilities, rate/concurrency/timeout settings, retention class, adapter configuration, effective time, checksum, and secret references—not secret values.

## `SearchConfiguration` and `SearchConfigurationVersion`

**Purpose:** stable configurable search identity plus immutable run snapshots.

**Important fields:** ID/name/state, neutral geographic criteria, price/negotiation policy, property/new-used criteria, source allow/deny list, interval/priority, versioned validated criteria, effective time, checksum, author/reason.

Areas may be administrative regions, polygons, or explicit mappings. Source-specific tokens belong in adapter mapping, not the domain search.

## `Listing`

**Purpose:** one source advertisement/presentation. One property may have many listings and a source may relist under a new ID.

**Important fields:** `listing_id`, source, source external ID/normalized form, canonical URL plus variants, ingestion method, system first/last observed, current projected status/confidence, last successful detail observation, relisting lineage hint, and created time.

**Relationships/history:** belongs to `Source`, has many `Observation`, and has zero/one active versioned link to a `Property`. External IDs may be absent/reused; URL alone is not universally unique.

## `Observation`

**Purpose:** immutable record of what was received at one source/listing observation.

**Important fields:** `observation_id`, listing/source, observed/recorded time, fetch/run IDs, requested/final URL, HTTP/status/content metadata, latency, outcome/page classification, capture mode, object reference/hash/size/media type, retention/expiry/compliance reference, replay eligibility, and correlation/idempotency fingerprint.

**History:** append-only. Later observations never update earlier ones. Body expiry updates lifecycle state or adds a retention event without deleting durable observation identity/provenance.

## `RawObject`

**Purpose:** provider-neutral catalog for permitted payloads.

**Important fields:** checksum, size, media type, compression/encryption, storage adapter/key, created/verified/expired times, retention policy, and export-manifest state.

Content-addressable deduplication is optional; independent source retention rules must remain enforceable.

## `ParseRun`

**Purpose:** one parser version's immutable attempt against an observation.

**Important fields:** observation, adapter/parser/schema versions, start/end, input checksum, result (`SUCCESS`, `PARTIAL`, `FAILED`, `NOT_REPLAYABLE`), structured error/warning/quality summary, and idempotency key.

A newer parser creates a new run rather than replacing one.

## `SourceFact`

**Purpose:** structured source claim before identity/canonical merge.

**Important fields:** parse run/observation, fact type/path, raw and parser-normalized values, language/unit, source selector/path when appropriate, source-effective date, extraction confidence/warnings, and schema version.

Examples: price, address, station text, 建築確認番号, project name, publication dates, source status, and marketing claims. A versioned parsed document plus indexed fact rows is acceptable if equivalent provenance remains.

## `MarketingClaim`

**Purpose:** queryable source selling point without treating it as verified.

**Important fields:** listing, observation/source fact, raw phrase, normalized claim kind/value, extraction method/version, and status/link to later normalized or verified evidence.

## Ingestion relationships and constraints

- Source configuration/search versions link to `PollingRun`/`SourceRun`.
- Listing identity rules are source-specific and versioned.
- One logical parse result exists per observation/parser version/input checksum.
- Facts cannot outlive their observation provenance.
- Raw-object expiry cannot cascade into facts, properties, events, or notifications.

