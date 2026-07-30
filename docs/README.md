# Homesearch Documentation Index

This index is the required starting point for project work. Read the core overview, then only the documents relevant to the task. `AGENTS.md` contains the non-negotiable repository rules.

## Current status

- Phase 0 design is complete and Gate A passed on 2026-07-30 after explicit product-owner approval.
- [Gate A ADRs 0001–0011](adr/README.md) are `Accepted`, and Phase 1 is in progress within its documented scope.
- Phase 1 now includes the Python 3.14/uv bootstrap, strict versioned configuration, explicit user/source/search identities, a secret-safe synchronous SQLAlchemy 2/psycopg 3 boundary, local PostgreSQL 18.4 Compose, the first Alembic schema, matching Core metadata, a per-use-case connection/transaction unit of work, and atomic idempotent persistence of safe configuration snapshots plus configured user/source anchors. Property/listing/run repositories and workflows, structured logging, and CI remain unimplemented.
- Search policies can validate source-neutral areas, price/property criteria, intervals/limits, and user/source references, but no search is configured by default and no polling, source adapter, or scheduler is implemented.
- Live source access, external API setup, email delivery, infrastructure creation, credentials, and deployment remain unauthorized by Gate A.

## Core overview

Read these short entry points for any major task:

- [Product specification](product-spec.md) — product goal, scope, principles, workflows, and requirement map.
- [Architecture](architecture.md) — system shape, modules, boundaries, and architecture reading map.
- [Data model](data-model.md) — modeling invariants, relationship overview, and entity reading map.
- [Roadmap](roadmap.md) — gates, phase overview, cross-phase obligations, and current stop point.

## Task-oriented reading

| Task | Read |
|---|---|
| Source discovery, access assessment, parsing, or raw capture | [Source and ingestion requirements](product/source-and-ingestion.md), [Pipeline and interfaces](architecture/pipeline-and-interfaces.md), [Ingestion model](data-model/ingestion.md), [Roadmap: foundation and ingestion](roadmap/foundation-and-ingestion.md) |
| Property identity, deduplication, normalization, canonical merge, or provenance | [Property and history requirements](product/property-and-history.md), [Pipeline and interfaces](architecture/pipeline-and-interfaces.md), [Identity and provenance model](data-model/identity-and-provenance.md), [Roadmap: domain and tracking](roadmap/domain-and-tracking.md) |
| Marketing headlines, selling-point claims, aliases, or property-level claim aggregation | [Property and history requirements](product/property-and-history.md), [Ingestion model](data-model/ingestion.md), [Identity and provenance model](data-model/identity-and-provenance.md), [Roadmap: domain and tracking](roadmap/domain-and-tracking.md) |
| Location, amenities, gym, hazards, transport, terrain, or layout evaluation | [Enrichment and evaluation requirements](product/enrichment-and-evaluation.md), [Provider and deployment architecture](architecture/deployment-and-providers.md), [Enrichment and evaluation model](data-model/enrichment-and-evaluation.md), [Roadmap: enrichment and operations](roadmap/enrichment-and-operations.md) |
| Notification readiness, deadlines, events, delivery, secure actions, tracking, reporting, or manual review | [Tracking and reporting requirements](product/tracking-notifications-and-reporting.md), [Pipeline and interfaces](architecture/pipeline-and-interfaces.md), [Jobs and operations](architecture/jobs-and-operations.md), [Tracking and operations model](data-model/tracking-and-operations.md), [Roadmap: domain and tracking](roadmap/domain-and-tracking.md) |
| Scheduler, jobs, observability, failure handling, testing, backup, deployment, portability, or cost | [Quality and open decisions](product/quality-and-decisions.md), [Jobs and operations](architecture/jobs-and-operations.md), [Provider and deployment architecture](architecture/deployment-and-providers.md), [Roadmap](roadmap.md), [Roadmap: enrichment and operations](roadmap/enrichment-and-operations.md) |
| Database strategy, schema, persistence, or migrations | [Database strategy ADR](adr/0002-database-strategy.md), [Database access ADR](adr/0003-database-access-and-migrations.md), [Data model](data-model.md), and [Roadmap: foundation and ingestion](roadmap/foundation-and-ingestion.md) |
| Gate A runtime, configuration, local workflow, CI, user scope, web, storage, jobs, or cost implementation | [ADR index](adr/README.md), then only the ADRs it routes to |
| Later durable technology/provider decision | [Quality and open decisions](product/quality-and-decisions.md), [Provider and deployment architecture](architecture/deployment-and-providers.md), and the later backlog in [Roadmap](roadmap.md) |

## Document tree

```text
docs/
  README.md
  product-spec.md
  product/
    source-and-ingestion.md
    property-and-history.md
    enrichment-and-evaluation.md
    tracking-notifications-and-reporting.md
    quality-and-decisions.md
  architecture.md
  architecture/
    pipeline-and-interfaces.md
    jobs-and-operations.md
    deployment-and-providers.md
  data-model.md
  data-model/
    ingestion.md
    identity-and-provenance.md
    enrichment-and-evaluation.md
    tracking-and-operations.md
  roadmap.md
  roadmap/
    foundation-and-ingestion.md
    domain-and-tracking.md
    enrichment-and-operations.md
  adr/
    README.md
    0001-... through 0011-...
```

## Documentation ownership

- Product files define required behavior and uncertainty; they do not select implementation details.
- Architecture files define component responsibilities and provider-independent boundaries.
- Data-model files define conceptual entities, relationships, history, and constraints; they are not final SQL.
- Roadmap files define authorization gates, implementation order, tests, and completion criteria.
- ADRs record proposed, accepted, superseded, or rejected durable choices without rewriting accepted history.
