# Homesearch Architecture

## Target shape

Homesearch is a low-cost, auditable **modular monolith with separately runnable web, scheduler, and worker entry points**, a relational persistence strategy selected at Gate A, and optional provider-neutral object storage.

Modules share one versioned codebase but communicate through explicit application interfaces and durable jobs/events. This avoids premature distributed-system complexity while leaving clean seams for measured future extraction.

This is a target architecture, not approval to begin Phase 1.

PostgreSQL is the likely long-term production target, especially if PostGIS provides material geospatial value. Phase 0 does not decide the local-development store, early/MVP persistence, production relational target, or migration path.

## Adopted directions

- Separate physical properties, listings, and immutable observations.
- Persist permitted source evidence before or atomically with downstream scheduling.
- Make parsing, normalization, identity, merge, enrichment, evaluation, and change detection versioned/replayable.
- Use append-oriented history plus rebuildable current projections.
- Keep field candidates/provenance separate from selected canonical state.
- Use durable runs, jobs, and events for audit, retries, idempotency, and notification deduplication.
- Isolate every source and external provider behind typed interfaces.
- Preserve explicit unknown/conflict/verification states.
- Run discovery and tracking as distinct workflows sharing ingestion.
- Cache stable enrichment by input fingerprint and refresh policy.
- Bound new-property enrichment with a versioned, deadline-aware notification-readiness policy.

## Provisional choices

These require ADR approval before implementation:

- Python is the leading runtime candidate for parsing/data/geospatial work.
- Gate A selects local, early/MVP, and production persistence plus their migration path; all domain/schema design remains PostgreSQL-compatible/migration-ready.
- SQLite may support isolated tests, tools, prototypes, exports, or temporary local work, but not permanent production or the sole validation of database semantics.
- A small typed HTTP application can serve confirmations and health.
- Database-backed durable jobs are a low-cost candidate whose validity depends on the Gate A database decision; add a broker only after measurement.
- Optional large permitted payloads use checksum-addressed, replaceable blob storage referenced from the selected relational store.

See [Quality constraints and open decisions](product/quality-and-decisions.md) and [Roadmap](roadmap.md).

## System context

```mermaid
flowchart LR
    User["User / reviewer"]
    Sources["Approved property sources<br/>portals, brokers, developers,<br/>feeds or manual imports"]
    Geo["Geocoding / maps / POI providers"]
    Route["Routing / traffic providers"]
    Hazard["Official hazard datasets"]
    Mail["Email provider"]

    subgraph HS["Homesearch"]
        API["API and confirmation UI"]
        Scheduler["Scheduler"]
        Workers["Workers"]
        Domain["Domain modules"]
        DB[("Relational persistence<br/>Gate A decision")]
        Blob[("Optional portable<br/>raw-object storage")]
        Ops["Health, logs, metrics,<br/>run ledger"]
    end

    Sources --> Workers
    Geo --> Workers
    Route --> Workers
    Hazard --> Workers
    Scheduler --> Workers
    Workers --> Domain
    Domain --> DB
    Workers --> Blob
    Workers --> Ops
    Domain --> Mail
    Mail --> User
    User --> API
    API --> Domain
    API --> DB
```

A source can be an API, feed, permitted HTTP adapter, imported file, or manual input. The diagram does not authorize automated access.

## Module ownership

```text
homesearch/
  domain/
    properties/ listings/ identity/ provenance/
    evaluation/ tracking/ events/
  application/
    discovery/ observation_ingestion/ parsing/
    canonicalization/ enrichment/ notification/
    review/ reporting/
  adapters/
    sources/ database/ object_storage/
    geocoding/ amenities/ routing/ hazards/ email/
  workers/ api/ config/ observability/
```

- **Properties/listings:** domain identities, statuses, value types, and invariants.
- **Identity:** evidence comparison, conflicts, match decisions, and manual-resolution semantics.
- **Provenance:** candidate values, field-specific selection, verification, and conflicts.
- **Evaluation:** profiles, hard rules, preferences, evidence requirements, and explainable outcomes.
- **Tracking/events:** user transitions, semantic change identity, and notification eligibility.
- **Discovery/ingestion/parsing:** approved collection orchestration, immutable capture, and source facts.
- **Canonicalization:** normalization, identity coordination, candidate creation, merge, and projection.
- **Enrichment:** provider calls, cache/staleness, evidence, and versioning.
- **Notification:** versioned readiness/deadline decisions, immutable payloads, delivery attempts, and secure actions.
- **Review/reporting:** audited correction and reproducible output.
- **Adapters:** translation to sources, persistence, storage, enrichment, email, clocks, and IDs.

Domain modules do not fetch pages, call vendors, or depend on ORM models. Source parsers do not own global retries, scheduling, canonical merge, or database transactions.

## Focused architecture documents

- [Pipeline and interfaces](architecture/pipeline-and-interfaces.md) — adapter contracts, discovery/tracking/reprocessing flows, observations, and canonical projections.
- [Jobs and operations](architecture/jobs-and-operations.md) — durable scheduling, idempotency, failure handling, observability, configuration, and testing.
- [Deployment and providers](architecture/deployment-and-providers.md) — action endpoint, topology, portability, backup/recovery, provider strategy, scaling, and risks.
