# Tracking and Operations Data Model

Read with [Conceptual data model](../data-model.md) and [Tracking/notification requirements](../product/tracking-notifications-and-reporting.md).

## User and tracking

### `User` / `NotificationDestination`

Represent configured users/destinations without embedding personal values in code. A single-user implementation is acceptable, but user-scoped tracking/evaluation should not be accidentally precluded. Encrypt or secret-reference destinations as appropriate and redact exports/logs.

[ADR 0007](../adr/0007-initial-user-scope.md) accepts one logical user with explicit `user_id`, secret-referenced destinations, and no early authentication.

### `TrackingPreference`

Append-only per-user/property transitions with state (`NEW`, `TRACKING`, `NOT_TRACKING`, `ARCHIVED`), effective period, transition source, token/notification reference, reason, actor, and time. A current projection may accelerate reads.

## Events and notifications

### `PropertyEvent`

Immutable semantic change.

**Fields:** property/optional listing, kind, occurred/detected/recorded times, before/after references, evidence/change-detector version, significance/policy version, deterministic fingerprint, correction/supersession, and run/correlation IDs.

Kinds include discovery, listing added, price/status changes, ended/sold/disappeared/relisted, address/identity evidence improvement, completion/media/canonical conflict/enrichment/evaluation changes, and tracking transition.

### `NotificationReadinessPolicyVersion`

Immutable definition of when a property/event is eligible for notification.

**Fields:** stable policy ID/version/effective period, applicable notification/event type, identity threshold/blocking conflicts, minimum basic facts, required source-link/provenance rules, location-precision handling, high-priority and optional enrichment requirements, accepted terminal states per requirement, maximum wait duration/deadline rule, evaluation requirement, and behavior for timeout/failure/unknown.

The policy is configuration, not hidden worker logic.

### `NotificationReadinessAssessment`

Versioned, auditable decision for a property and triggering event.

**Fields:** property/event, policy version, outcome (`NOT_READY`, `READY_COMPLETE`, `READY_WITH_UNKNOWNS`, `BLOCKED_IDENTITY_REVIEW`, or approved equivalents), trigger/first-eligible time, deadline, evaluated time, identity decision, canonical projection and evaluation references, input fingerprint, major conflicts, blocking reasons, superseded-by assessment, and resulting notification when ready.

`READY_COMPLETE` means complete relative to that policy—not that all future data is known. A passed deadline cannot override unsafe identity ambiguity.

### `NotificationReadinessRequirementResult`

Per-policy-requirement explanation.

**Fields:** assessment, requirement key/type, outcome (`SATISFIED`, `PENDING`, `UNKNOWN_ALLOWED`, `NOT_VERIFIED_ALLOWED`, `TIMED_OUT_ALLOWED`, `BLOCKED`, or approved equivalents), evidence/enrichment/job references, provider/error category, first/last attempt and terminal time, deadline contribution, and human-readable reason code.

This makes optional-provider failure terminal and visible instead of indefinitely pending.

### `Notification`

Immutable notification decision/payload snapshot.

**Fields:** property, user/destination, channel/type, events, readiness assessment, notification policy/template/payload versions, reproducible rendered content, locale, created time, deduplication fingerprint, and suppression status/reason.

The snapshot preserves verified facts, source claims, conflicts, unknown/not-yet-checked items, timeout/unavailable reasons, and recommendation at creation.

### `NotificationDelivery`

Each provider attempt with notification, attempt number, provider, destination reference, idempotency key, requested/accepted/delivered/failed times, state, provider ID, structured error, and webhook evidence.

Provider acceptance is not inbox delivery.

### `ActionToken`

One future notification action.

**Fields:** notification, user/destination, property, allowed action, token hash/non-sensitive identifier, issued/expiry/consumed/revoked times, replay policy, confirmation metadata, and resulting tracking transition.

GET validation does not consume/apply; confirmation POST consumes atomically.

## Runs, jobs, and health

### `PollingRun`

Top-level scheduled/manual discovery, tracking, enrichment, or report run with type, configuration versions, schedule/start/end, state, trigger, correlation ID, aggregate counts, and outcome.

### `SourceRun`

Source/search part of a run with exact source/config/search versions, cursor before/after, request/listing/observation/parse/property/match counts, timing/state, structured failures, and cooldown/rate data. Failure cannot imply disappearance.

### `Job`

Durable typed/versioned payload with idempotency key, due/priority/state, attempts, lease owner/expiry, timeout, structured error, parent run/job, and timestamps. Physical storage versus broker is an ADR.

[ADR 0005](../adr/0005-scheduling-and-durable-jobs.md) defers this entity and all scheduler/worker machinery until Phase 6, then selects PostgreSQL-backed leases unless measurements justify a broker.

### `SourceHealthIncident`

Access block, parser drift, repeated timeout, or field-quality collapse with source/adapter/parser, kind/severity, open/last/resolved times, metrics/evidence, action/owner, and runs.

## Manual review

### `ManualReviewCase`

Typed ambiguity: possible duplicate, confirmation-number conflict, address/location/status/area ambiguity, enrichment uncertainty, or canonical conflict.

**Fields:** kind, state (`OPEN`, `IN_REVIEW`, `RESOLVED`, `DEFERRED`), severity/priority, subjects, opening rule/version, evidence snapshot, assignee, resolution, and timestamps.

### `ManualReviewAction`

Append-only actor, action, rationale, selected evidence, time, resulting identity/field/tracking operation, and before/after references. Overrides are explicit, revocable, and never mutate source facts.

## Reports

### `ReportRun`

Compared run/window, profile/config versions, generator/template version, category counts, created time, and artifact reference.

### `ReportPropertySnapshot`

Each included property's category, all rejection reasons, key values, unknowns/conflicts, and change labels at report time. It remains reconstructible after current projections change.

## Constraints and idempotency

The physical schema should enforce where possible:

- one parse result per observation/parser/input checksum;
- one derived result per input/algorithm fingerprint;
- one normal active property link per listing;
- non-overlapping current tracking state per user/property;
- non-overlapping canonical selection periods per property/field;
- unique semantic event fingerprint;
- one readiness assessment per property/event/policy/input fingerprint;
- notification creation requires a ready assessment under its referenced policy;
- unique notification per policy/destination/fingerprint;
- unique provider delivery idempotency key;
- unique token hash and atomic single use;
- positive values where domain-valid and explicit currency/units; and
- restricted rather than cascading deletion of history.

## Index/scale considerations

Likely indexes:

- source plus external listing identity/URL fingerprint;
- observation listing/time/hash;
- run/source/time/status;
- normalized 建築確認番号;
- address components/location buckets and optional spatial proximity;
- property/field/current selection;
- current listing/tracking state;
- open review cases;
- due jobs/state/lease;
- property events/time/kind/fingerprint; and
- readiness outcome/deadline/policy/property;
- notification delivery state.

Partitioning observations/events is premature until measured and must preserve export/restore simplicity.

## Portability and lifecycle

Portable export includes:

- selected-store schema version and logical data, plus the documented migration-ready path to the likely PostgreSQL target;
- raw-object manifest with checksums/sizes/retention/logical keys and permitted objects;
- safe configuration versions without secrets;
- parser/algorithm/rule manifest;
- migration history; and
- validation report.

Import verifies references/checksums before cutover. Backups are proven only by restore. Provider IDs may remain metadata but cannot be the sole relationship.

Raw retention, destination privacy, legal deletion, and notification-payload retention require explicit pre-production policy.

## Schema decisions

Accepted Gate A decisions:

- [ADR 0002](../adr/0002-database-strategy.md): local/MVP/production database and migration/restore path;
- [ADR 0003](../adr/0003-database-access-and-migrations.md): SQLAlchemy/transactions, Alembic, UUIDv7, and time conventions;
- [ADR 0007](../adr/0007-initial-user-scope.md): one logical user with explicit user-owned state; and
- [ADR 0008](../adr/0008-raw-observation-storage.md): relational metadata and optional raw-object boundary.

Later schema questions:

1. Database enum versus checked text/reference tables.
2. Typed field tables versus typed/versioned JSON hybrid.
3. PostGIS adoption and portable fallback.
4. Which facts need bitemporal effective time.
5. Parsed-fact physical shape/indexing.
6. External-ID reuse/relisting semantics per source.
7. Compliance erasure/tombstones.
8. Object encryption/key management/deduplication boundaries.
9. Destination and notification-payload privacy.
10. Confidence representation/calibration.
11. Media/floor-plan evidence representation, subject to approval.
