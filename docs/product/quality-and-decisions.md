# Quality Constraints and Open Decisions

Read with [Product specification](../product-spec.md), [Architecture](../architecture.md), and [Roadmap](../roadmap.md).

## Maintainability and reliability

- Modular boundaries and typed interfaces.
- Deterministic, replayable normalization where practical.
- Source-isolated adapters and tests.
- Migration-ready schema/persistence boundaries and documented configuration.
- Idempotent writes/jobs with safe retries, backoff, jitter, timeout, and overlap prevention.
- Degraded operation when one source/provider fails.
- Parser drift/source health detection.
- No premature microservices or Kubernetes.

## Security, privacy, and compliance

- No committed secrets, personal recipient details, cookies, or private endpoints containing credentials.
- Least-privilege provider credentials via environment/secret manager.
- Expiring, replay-protected action tokens and confirmation POST.
- Redacted logs and minimized raw/fixture content.
- Source-by-source terms/robots/access/copyright/privacy assessment.
- No access-control or anti-bot circumvention.
- Configurable payload capture and retention with lawful alternate ingestion.

## Portability and recoverability

- Gate A must decide the local-development database, early/MVP persistence, production relational target, and migration path as one explicit database strategy.
- PostgreSQL is the likely/desired long-term production target, with PostGIS a possible future benefit, but this Phase 0 review does not select it.
- SQLite is not the permanent production design. It may be useful for isolated tests, local tooling, prototypes, exports, or temporary development workflows.
- Persistence/business logic must not depend on SQLite-specific behavior. SQLite-only tests must not hide differences in concurrency, types, constraints, transactions, migrations, or geospatial behavior.
- Domain/schema design remains PostgreSQL-compatible and migration-ready regardless of the early/local choice.
- Versioned migrations, logical backups, restoration drills, and portable exports.
- Provider-neutral raw object references/manifests with checksums.
- Secrets and infrastructure configuration separated from data.
- Isolate optional provider/database features.
- Define RPO/RTO, backup frequency/retention/encryption, off-failure-domain copy, and restore procedure before production reliance.

## Cost

- Target a low-cost personal deployment.
- Do not require Kubernetes, an expensive managed queue, multiple always-on servers, or repeated paid calls for unchanged data.
- Cache stable geocoding, amenity, route, hazard, and evaluation inputs/results.
- Research provider pricing and measure expected load before commitment.
- User's monthly budget ceiling and acceptable manual effort are unresolved.

## Required testing

- parser fixtures, missing/malformed fields, and drift;
- normalization and Japanese address normalization;
- identity matching and false-positive prevention;
- 号棟 and conflicting 建築確認番号;
- merge precedence, processing-order independence, conflicts, and provenance;
- price/status/change-event history;
- evaluation rules and unknown handling;
- notification/event/delivery deduplication;
- action expiry, tamper, replay, authorization, GET safety, and log redaction;
- selected-store migrations/upgrade paths plus production-target compatibility tests for transactions, concurrency, types, constraints, and geospatial behavior where relevant;
- provider failure, staleness, precision, and quota behavior;
- observation replay and projection rebuilding; and
- backup/restore verification before production.

## Explicitly deferred

- live source collection;
- production database/object storage;
- scheduled production workers and deployment;
- external map, POI, routing/traffic, hazard, image, and email calls;
- production geospatial resolution;
- full manual-review UI and dashboard;
- fully autonomous image/floor-plan judgment;
- multi-user behavior; and
- provider resources, credentials, GitHub secrets, or paid services.

## ADR and research backlog

| Decision | Current direction | What must be resolved |
|---|---|---|
| Runtime | Python is a strong provisional fit | Typing, async/browser tooling, deployment, maintainer preference |
| Web/API | Lightweight typed API | Select with runtime decision |
| Database strategy | Open until Gate A; PostgreSQL is the likely long-term target | Local development store, early/MVP persistence, production relational target, migration path, and when target-database integration tests become mandatory |
| Database access | Provider-neutral domain boundaries and explicit migration path | ORM/query builder/direct SQL, provenance ergonomics, and how early/local choices remain PostgreSQL-compatible |
| Migrations | Versioned and CI-tested | Tool and forward-repair/rollback policy |
| IDs/time | Opaque application IDs and UTC instants | UUID/ULID choice and source date precision |
| Scheduler/queue | Database-backed jobs first | Concurrency, retries, host behavior, measured load |
| PostgreSQL/PostGIS | Likely long-term option, not selected in Phase 0 | Production need, geospatial value, local/MVP timing, host support, migration and export fallback |
| PostgreSQL host | Decide only if PostgreSQL is selected | Region, cost, backup, extensions, egress, sleep behavior |
| Raw storage | DB metadata plus optional portable blobs | Source legality, capture mode, retention, encryption, lifecycle, cost |
| Geocoder | Adapter/cache, official/open preference | Japanese quality, terms, quota, cost, precision, redistribution |
| Amenity provider | Bounded cached adapter | Coverage, categories, current business hours, terms, quota |
| Routing/traffic | Independent route adapter | Walking/transit quality, historical traffic/bus reliability, cost |
| Hazard data | Prefer official Japanese datasets | Dataset/version/license, resolution, update/ingestion |
| Email | Low-volume transactional adapter | Deliverability, sender/domain, privacy, cost, webhooks |
| Action endpoint | Small HTTPS app if feasible | Hosting, token expiry, confirmation UX, authentication |
| Deployment | Single low-cost web/worker topology | Region, background/scheduler support, cost, migration path |
| Source access | Nothing approved merely by being named | Terms, robots, API/feed, rate, retention, fixture/fallback per source |
| Polling load | Unknown until measured | Search/listing/tracking counts, freshness, traffic, quotas |
| Retention | Tiered source-specific policy | Raw-body duration, metadata history, erasure, storage budget |
| Backup/monitoring | Automated backups, restore drills, structured health | RPO/RTO, frequency, alert channel, tooling, cost |
| Multi-user | Optimize for one without blocking later | User-scope tracking/evaluation from initial schema? |
| Output locale | Japanese notification required | Approve Japanese categories versus Chinese labels in source brief |
| Photo evidence | Supporting evidence only if approved | Copyright, retention, hashes/model, explainability, cost |

Do not invent provider availability or current pricing. Research these only in the roadmap phase that needs them and record approved durable choices as ADRs.
