# Roadmap: Foundation and Ingestion

Read with [Roadmap](../roadmap.md). Every phase preserves the cross-phase rules and approval gates defined there.

## Phase 0 — Durable specification and architecture

**Goal:** establish product contract and design boundaries before implementation.

**Deliverables:**

- `AGENTS.md` and `docs/README.md`;
- product, architecture, data-model, and roadmap entry points plus focused documents;
- explicit risks, uncertainties, ADR candidates, and deferred work; and
- a documentation-only [Gate A decision set](../adr/README.md) with alternatives, consequences, validation, and an explicit lifecycle status.

**Tests/review:**

- trace every originating requirement into the documentation set;
- verify no production code, credentials, live access, deployment, or external resource;
- check terminology/invariants/links and Mermaid rendering; and
- verify every Gate A ADR was reviewable as `Proposed` before approval and did not silently authorize implementation.

**Completion criteria:**

- required entry-point files exist and are consistently routed;
- property/listing/observation, retention, provenance, identity, history, security, and portability are explicit;
- unresolved decisions are labeled;
- the product owner reviewed the proposals and explicitly approved Gate A on 2026-07-30.

**Dependencies:** none.

**Intentionally deferred:** all implementation and provider/source commitments.

## Phase 1 — Project skeleton, configuration, and database foundation

**Goal:** minimal runnable/testable foundation without live property collection.

**Authorization:** Gate A passed and this phase may begin. No Phase 1 implementation is included in the Gate A acceptance change.

**Progress:** independently reviewed tasks now provide the Python 3.14/uv package and local quality commands, followed by strict layered configuration loading, the one-user/default-user UUIDv7 anchor, configuration schema version 3's empty-by-default source-policy registry, and schema version 4's empty-by-default search-policy registry. Source policies use UUIDv7 identities plus stable keys and validate lifecycle/access state, capabilities, request limits, and ADR 0008 capture/retention/storage vocabulary without authorizing access. Search policies add versioned UUIDv7 identities, source-neutral administrative areas, JPY price/negotiation criteria, property/new-used criteria, discovery intervals/result limits, and validated user/source references. The accepted synchronous SQLAlchemy 2/psycopg 3 connection boundary now resolves only a configured database secret, requires an explicit PostgreSQL driver/database, and creates a lazy engine without connecting. No search is enabled by default, and database schemas, migrations, actual connections, Compose, repositories, polling, source/provider adapters, scheduling, structured logging, and CI remain separate follow-up tasks.

**Deliverables:**

- implementation of the explicitly Accepted Gate A ADRs, with any material deviation recorded before code changes;
- modular package skeleton;
- safe configuration schema, environment overlays, and secret references;
- placeholder-only `.env.example`;
- Gate A-approved local-development and early/MVP persistence workflow;
- documented production relational target and tested migration path;
- an [ADR 0002](../adr/0002-database-strategy.md)-compliant PostgreSQL 18 local/CI foundation;
- initial migrations for the approved configuration, user/source, listing/property anchor, run-ledger, and migration metadata scope;
- developer commands/CI and structured correlation logging.

[ADR 0005](../adr/0005-scheduling-and-durable-jobs.md) proposes deferring the scheduler, worker daemon, and durable `Job` table until Phase 6.

**Tests:**

- configuration validation and invalid thresholds/intervals/missing references;
- selected-store migration from empty and upgrade smoke test;
- target-database tests that expose differences in concurrency, types, constraints, transactions, JSON/time semantics, and geospatial behavior relevant to the approved production target;
- if SQLite is used for a bounded purpose, target-compatible tests proving business/persistence logic does not depend on SQLite behavior;
- secret scan/redaction;
- module-boundary checks where supported.

**Completion criteria:**

- documented contributor setup;
- deterministic tests/lint/types;
- the selected local/MVP store migrates from empty and reports version;
- Accepted ADRs record local, early/MVP, production-target, migration-path, runtime, configuration, user-scope, and CI decisions;
- no production service/secret needed;
- Gate A ADRs are Accepted or explicitly deferred without leaving an implementation dependency unresolved.

**Dependencies:** satisfied — Phase 0 is approved and Gate A passed with ADRs 0001–0011 `Accepted`.

**Intentionally deferred:** source adapters, raw payload storage, broad schema, scheduler/worker/job engine, external calls, deployment.

## Phase 2 — Source contracts and raw observation ingestion

**Goal:** prove immutable ingestion using synthetic/manual fixtures only.

**Deliverables:**

- typed discovery/fetch/parse/status adapter interfaces;
- source/access registry and capture/retention modes;
- observations, raw-object metadata, parse runs, source facts, and source-run migrations;
- test filesystem/raw-object adapter with manifest/checksums;
- idempotent ingestion service;
- synthetic/manual adapter;
- fixture provenance/legal format;
- structured source/parser failures.

**Tests:**

- repeated ingestion causes one logical effect;
- immutable observations;
- all capture modes including transient/not replayable;
- checksum corruption/missing object;
- parser success/partial/failure/new-version replay;
- adapter failure isolation;
- no body/secret leakage in logs.

**Completion criteria:**

- synthetic listing flows to immutable observation and facts;
- reparse preserves earlier result;
- test-body expiry retains metadata/provenance;
- no live site accessed.

**Dependencies:** Phase 1.

**Intentionally deferred:** real source access, canonical matching/merge, enrichment, notifications.

## Phase 3 — First approved source

**Goal:** implement one lawful sustainable ingestion path and adapter quality bar.

**Deliverables:**

- written source assessment/approval;
- capability/configuration mapping;
- conservative rates, timeouts, jitter, retry/cooldown, pause control;
- approved discovery/detail/manual/API/feed path;
- source identity and status interpretation;
- original headline, catch copy, and selling-point facts with observation provenance;
- permitted representative fixtures;
- parser required-field health metrics;
- alternate/manual behavior when automation is unavailable.

**Tests:**

- typical, missing, malformed, ended, markup-changed, and encoding fixtures;
- ID/URL/relisting cases;
- headline/catch-copy history and marketing-claim source attribution;
- status without treating failed fetch as disappearance;
- rate/cooldown/retry classification;
- drift/required-field signal;
- recorded/synthetic end-to-end test, not uncontrolled live CI.

**Completion criteria:**

- Gate B evidence recorded;
- adapter contract met;
- approved access/retention respected;
- source failure isolated/observable;
- fixtures protect future parser changes;
- production schedule remains off unless separately approved.

**Dependencies:** Phase 2 and Gate B.

**Intentionally deferred:** additional sources, auto cross-source matching, canonical merge, high-frequency polling, any protection bypass.
