# ADR 0005: Scheduling and Durable Jobs

## Status

Proposed

## Context

Homesearch eventually needs hourly discovery, roughly twice-daily tracking, retries, readiness deadlines, and reliable notification delivery. A scheduler answers when work becomes due; a durable job system records, claims, retries, and audits the work. Conflating them makes missed triggers or worker crashes difficult to reason about.

Phase 1 has no approved live source or outbound effect and therefore does not need an always-on scheduler, broker, or general job table.

## Decision

Adopt a staged design if Gate A approves:

### Phase 1

- provide synchronous, manually invoked application commands and an injectable clock;
- establish idempotency-key, timeout, error-taxonomy, correlation, and run-ledger conventions;
- do not implement a scheduler, worker daemon, broker, or durable `Job` table;
- test application use cases as repeatable commands against PostgreSQL; and
- keep source/tracking schedule values in validated configuration even though execution is disabled.

### Phase 6 and later

- use a thin platform/OS schedule (cron-compatible trigger) to invoke a due-work planner;
- use PostgreSQL-backed durable jobs with typed/versioned payloads, `due_at`, priority, attempt state, idempotency key, leases, and parent/correlation IDs;
- claim work transactionally using PostgreSQL locking semantics such as `FOR UPDATE SKIP LOCKED`, validated under concurrent integration tests;
- keep scheduling and job-store ports independent of the host and persistence adapter;
- use bounded exponential backoff with jitter, per-class timeouts, attempt ceilings, quarantine/dead state, and manual replay;
- prevent overlap with stable logical uniqueness keys and expiring leases;
- apply source/provider concurrency, cooldown, and request budgets before dispatch; and
- make notification-readiness deadline wake-ups ordinary delayed jobs. Exhausted optional work records an auditable terminal unknown/timeout rather than remaining pending forever.

Hourly discovery and twice-daily tracking are configurable starting targets, not entitlements to access a source. Gate B assessment may lower, disable, or stagger them per source. Scheduler downtime is recovered by planning missed due work within a bounded lookback, not by launching an unbounded burst.

Add Redis plus Celery/RQ, or another broker, only after measurements show PostgreSQL leasing or the selected host cannot meet throughput, latency, isolation, or operational needs.

## Alternatives considered

- **System/platform cron running whole workflows:** simple, but weak for multi-step retries, leases, audit, delayed readiness, and partial failure.
- **In-process scheduler (for example APScheduler):** easy locally, but relies on an always-on singleton and complicates failover/non-overlap.
- **Database scheduler extensions:** reduce application polling but add host/extension coupling and do not replace durable job semantics.
- **Redis with Celery or RQ from the start:** mature job ecosystems, but introduces an always-on service and recovery/observability burden before load exists.
- **Durable job table in Phase 1:** anticipates later needs but creates unused infrastructure and schema before any scheduled workflow is approved.

## Consequences

- Early phases remain command-driven and easier to test.
- Phase 6 introduces the first durable worker/scheduler machinery and its concurrency tests.
- PostgreSQL serves as both relational store and initial job coordination substrate, avoiding a broker cost.
- Scheduler triggers are replaceable because due-work calculation lives in application code.
- Phase 7 readiness deadlines can reuse `due_at` and retry semantics.

## Risks/trade-offs

- PostgreSQL job polling/locking can increase database load and contention.
- Platform cron delivery may be at-least-once or occasionally late; planner/idempotency logic must tolerate both.
- Long jobs need correctly sized leases/heartbeats or safe chunking.
- A delayed Phase 6 engine means Phases 2–5 run manually or in controlled command invocations.

## Follow-up/validation

- Gate A approves the phase split and the PostgreSQL-backed direction without authorizing implementation.
- Phase 1 tests command idempotency and run correlation only.
- Before Phase 6, prototype concurrent claims, lease recovery, fairness, cooldown, missed schedules, and dead-job replay on the production PostgreSQL major.
- Revisit a broker only with measured workload and hosting/cost evidence.

## Date

2026-07-30
