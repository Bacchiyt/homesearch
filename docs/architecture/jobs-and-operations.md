# Jobs and Operations Architecture

Read with [Architecture](../architecture.md) and [Tracking/notification requirements](../product/tracking-notifications-and-reporting.md).

## Job classes

- source/search discovery;
- listing detail fetch;
- observation parse/reparse;
- identity/canonicalization;
- enrichment by capability;
- evaluation;
- tracking selection/fetch;
- event classification;
- notification render/delivery;
- report generation;
- retention, backup, and health maintenance.

## Durable job properties

Each job has:

- stable type, payload schema/version, and idempotency key;
- input reference/version, priority, and due time;
- state, attempt count, lease owner/expiry, and optional heartbeat;
- timeout, retry/backoff policy, and structured error;
- created/started/completed timestamps;
- parent run/job and correlation IDs; and
- optional source/provider rate bucket.

PostgreSQL row leasing/advisory coordination is the provisional starting point and requires an ADR/prototype. A queue can replace the application job adapter if measured concurrency or hosting semantics require it.

## Non-overlap and idempotency

- Unique logical keys prevent overlapping source/search windows.
- Expired leases recover safely after worker failure.
- Observation identity uses source/listing/fetch fingerprints, not timing alone.
- Derived results are unique by input fingerprint plus parser/algorithm version.
- Events fingerprint subject, change kind, before/after evidence, and policy version.
- Delivery is unique by event, destination, channel, and notification policy/template.
- Discovery cursors advance only after durable accounting for the batch.

## Rate limits and backpressure

Source/provider policy defines maximum concurrency, minimum interval, request budget, jitter, retryable categories, and cooldown. One source can pause/circuit-break without blocking others. Workers apply backpressure instead of allowing unbounded discovery output.

## Failure taxonomy

- configuration/validation;
- source access disallowed or unsupported;
- authentication/authorization;
- rate limit/cooldown/quota;
- network/timeout/transient upstream;
- content changed/parser drift;
- malformed/partial data;
- invariant/data conflict;
- persistence/concurrency;
- notification rejection/delivery; and
- internal bug.

Retry only retryable categories with bounded backoff/jitter. Quarantine exhausted work for inspection/replay. Never convert provider failure into a negative domain result, mark disappearance from a failed run, or let one provider halt unrelated work.

## Observability

Structured logs use correlation fields such as `run_id`, `job_id`, `source_id`, `search_config_id`, `listing_id`, `property_id`, `observation_id`, version, attempt, duration, and outcome. Redact credentials, action tokens, bodies, personal destinations, and unnecessary query strings.

Minimum future metrics/views:

- last attempted/successful discovery per source/search;
- last tracking selection and successful listing check;
- fetch outcomes/latency;
- parser success, required-field presence, and unknown rate by version;
- observations/listings/new properties per run;
- identity decision distribution and review backlog;
- canonical conflicts;
- enrichment success/cache hit/staleness;
- event/notification/delivery counts;
- overdue/retrying/dead jobs;
- storage/database growth; and
- backup age/latest restore-drill result.

Low-noise alerts cover overdue success, parser-field collapse, dead-job growth, notification failure, quota risk, and stale backups. Tooling/channel/cost remain open.

`PollingRun`/`SourceRun` form a durable run ledger with exact configuration versions, counts, cursor changes, errors, and timing—even when zero properties qualify.

## Configuration

Configuration layers:

1. versioned safe defaults;
2. versioned non-secret profiles;
3. deployment environment variables;
4. environment/secret-manager secrets; and
5. audited database runtime configuration where needed.

Search definitions and evaluation profiles have stable IDs/versions. Validate unknown sources, invalid areas/ranges/intervals, incompatible capabilities, and missing secret references before scheduling.

No real recipient, credential, API key, token, or private secret-bearing endpoint belongs in version control.

## Testing architecture

- pure tests for normalization, identity, merge, evaluation, events, and transitions;
- contract tests for all adapters;
- legally appropriate parser fixtures and versioned golden results;
- property-based idempotency/normalization tests;
- PostgreSQL integration tests for constraints, locking, leasing, transactions, and migrations;
- observation-to-projection replay;
- false-positive identity suites;
- provider fakes for failure/staleness/precision/quota;
- end-to-end event → notification → confirmation POST;
- action expiry/tamper/replay/GET-safety/log-redaction security tests; and
- backup/restore drills.

SQLite is not a substitute for PostgreSQL behavior involving constraints, concurrency, JSON, timestamps, locking, or migrations.

