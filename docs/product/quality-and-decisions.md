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
- [ADR 0002](../adr/0002-database-strategy.md) recommends PostgreSQL 18 from local development onward, with PostGIS deferred, but its status is `Proposed` and Gate A has not selected it.
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

## Gate A proposals

The detailed context, alternatives, consequences, and validation live in focused ADRs rather than this product constraint file. Every row remains open until explicit product-owner approval.

| Decision | Proposed recommendation | ADR |
|---|---|---|
| Runtime/toolchain | Python 3.14, uv, Ruff, mypy, pytest, HTTPX, lxml, Pydantic Settings, structured standard logging; synchronous first | [0001](../adr/0001-python-runtime-and-toolchain.md) |
| Database strategy | PostgreSQL 18 for local, MVP, and production; SQLite only for bounded disposable uses; PostGIS later if justified | [0002](../adr/0002-database-strategy.md) |
| Database access/migrations/IDs/time | SQLAlchemy 2 + psycopg 3, Alembic, repository/unit-of-work boundary, UUIDv7, UTC-aware instants and retained source precision | [0003](../adr/0003-database-access-and-migrations.md) |
| Configuration/secrets | Versioned TOML, Pydantic validation, narrow environment overrides, external secret values | [0004](../adr/0004-configuration.md) |
| Scheduler/jobs | Phase 1 commands only; Phase 6 platform trigger plus PostgreSQL-backed durable jobs; broker only after evidence | [0005](../adr/0005-scheduling-and-durable-jobs.md) |
| Web/API | No Phase 1 server; FastAPI/Uvicorn only when an approved HTTP surface is needed | [0006](../adr/0006-web-and-api.md) |
| Initial user scope | One logical user and explicit `user_id`; recipient by secret reference; no early authentication | [0007](../adr/0007-initial-user-scope.md) |
| Raw observation storage | Prepare boundaries in Phase 1; Phase 2 relational metadata plus optional policy-permitted portable blobs | [0008](../adr/0008-raw-observation-storage.md) |
| Local development | macOS host Python/uv plus Compose PostgreSQL by default; native PostgreSQL supported | [0009](../adr/0009-local-development-workflow.md) |
| CI | GitHub Actions with locked dependencies, Ruff, mypy, pytest, PostgreSQL migrations/integration, and secret scanning | [0010](../adr/0010-continuous-integration.md) |
| Cost posture | Local-first, one production relational service, defer and budget variable-cost providers | [0011](../adr/0011-cost-model.md) |

Approval must address each proposal. An accepted database decision must name local development, early/MVP persistence, production target, migration/restore path, and mandatory target-database testing. Approval of a database engine does not approve a host, production resource, or PostGIS.

## Later research and decisions

| Decision | Current direction | What must be resolved |
|---|---|---|
| PostgreSQL host | Decide only after the engine strategy is accepted and Gate D approaches | Region, supported major/minor, cost, backup, extensions, egress, sleep behavior |
| PostGIS | Isolated optional capability, not a Gate A dependency | Measured spatial need, host support, migrations, indexes, export/non-spatial fallback |
| Geocoder | Adapter/cache, official/open preference | Japanese quality, terms, quota, cost, precision, redistribution |
| Amenity provider | Bounded cached adapter | Coverage, categories, current business hours, terms, quota |
| Routing/traffic | Independent route adapter | Walking/transit quality, historical traffic/bus reliability, cost |
| Hazard data | Prefer official Japanese datasets | Dataset/version/license, resolution, update/ingestion |
| Email | Low-volume transactional adapter | Deliverability, sender/domain, privacy, cost, webhooks |
| Action endpoint hosting | Narrow HTTPS app if Gate C/D approve it | Hosting, token expiry, confirmation UX, protection, cost |
| Deployment | Single low-cost web/worker topology | Region, background/scheduler support, cost, migration path |
| Source access | Nothing approved merely by being named | Terms, robots, API/feed, rate, retention, fixture/fallback per source |
| Polling load | Unknown until measured | Search/listing/tracking counts, freshness, traffic, quotas |
| Retention | Tiered source-specific policy | Raw-body duration, metadata history, erasure, storage budget |
| Backup/monitoring | Automated backups, restore drills, structured health | RPO/RTO, frequency, alert channel, tooling, cost |
| Multi-user/authentication | Initial shape avoids a forced singleton but implements no auth | Trigger, identity provider, authorization, privacy, isolation, deletion |
| Output locale | Japanese notification required | Approve Japanese categories versus Chinese labels in source brief |
| Photo evidence | Supporting evidence only if approved | Copyright, retention, hashes/model, explainability, cost |

Do not invent provider availability or current pricing. Research these only in the roadmap phase that needs them and record approved durable choices as ADRs.
