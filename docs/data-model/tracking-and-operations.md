# Tracking and Operations Data Model

Read with [Conceptual data model](../data-model.md) and [Tracking/notification requirements](../product/tracking-notifications-and-reporting.md).

## User and tracking

### `User` / `NotificationDestination`

Represent configured users/destinations without embedding personal values in code. A single-user implementation is acceptable, but user-scoped tracking/evaluation should not be accidentally precluded. Encrypt or secret-reference destinations as appropriate and redact exports/logs.

### `TrackingPreference`

Append-only per-user/property transitions with state (`NEW`, `TRACKING`, `NOT_TRACKING`, `ARCHIVED`), effective period, transition source, token/notification reference, reason, actor, and time. A current projection may accelerate reads.

## Events and notifications

### `PropertyEvent`

Immutable semantic change.

**Fields:** property/optional listing, kind, occurred/detected/recorded times, before/after references, evidence/change-detector version, significance/policy version, deterministic fingerprint, correction/supersession, and run/correlation IDs.

Kinds include discovery, listing added, price/status changes, ended/sold/disappeared/relisted, address/identity evidence improvement, completion/media/canonical conflict/enrichment/evaluation changes, and tracking transition.

### `Notification`

Immutable notification decision/payload snapshot.

**Fields:** property, user/destination, channel/type, events, policy/template/payload versions, reproducible rendered content, locale, created time, deduplication fingerprint, and suppression status/reason.

The snapshot preserves known, unknown, conflicting, and recommended information at creation.

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
- notification delivery state.

Partitioning observations/events is premature until measured and must preserve export/restore simplicity.

## Portability and lifecycle

Portable export includes:

- PostgreSQL schema version and logical data;
- raw-object manifest with checksums/sizes/retention/logical keys and permitted objects;
- safe configuration versions without secrets;
- parser/algorithm/rule manifest;
- migration history; and
- validation report.

Import verifies references/checksums before cutover. Backups are proven only by restore. Provider IDs may remain metadata but cannot be the sole relationship.

Raw retention, destination privacy, legal deletion, and notification-payload retention require explicit pre-production policy.

## Schema ADR questions

1. UUID/ULID/internal ID and time conventions.
2. ORM/query/transaction layer and migration tool.
3. Database enum versus checked text/reference tables.
4. Typed field tables versus typed/versioned JSON hybrid.
5. PostGIS and portable fallback.
6. Which facts need bitemporal effective time.
7. Parsed-fact physical shape/indexing.
8. External-ID reuse/relisting semantics per source.
9. User scoping from the initial schema.
10. Compliance erasure/tombstones.
11. Object encryption/key management/deduplication boundaries.
12. Destination and notification-payload privacy.
13. Confidence representation/calibration.
14. Media/floor-plan evidence representation, subject to approval.

