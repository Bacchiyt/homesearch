# Tracking, Notification, and Reporting Requirements

Read with [Product specification](../product-spec.md), [Jobs and operations](../architecture/jobs-and-operations.md), and [Tracking/operations data model](../data-model/tracking-and-operations.md).

## Tracking state

Initial per-user states:

- `NEW`;
- `TRACKING`;
- `NOT_TRACKING`;
- `ARCHIVED`.

State transitions are audited. `NOT_TRACKING` and `ARCHIVED` do not delete the property; a future UI/API/action can reactivate tracking.

For `TRACKING`, the initial baseline is at least two checks daily, subject to configurable intervals, source access/rate policies, last successful observations, and discovery work that already satisfies freshness.

## Meaningful changes

Versioned change policy can emit:

- price decrease/increase;
- sold, ended, disappeared, or relisted;
- new broker or official listing;
- address precision improvement;
- new 建築確認番号;
- completion/handover change;
- new photos or floor plan;
- important property field change;
- material hazard/location/amenity/evaluation change; and
- creation or resolution of an important conflict.

Formatting-only or parser-only differences are not semantic events. Failed/partial source runs do not establish disappearance. Events use deterministic fingerprints and preserve before/after evidence plus detector version.

## Notification readiness

A versioned `NotificationReadinessPolicy` decides when a newly discovered canonical property may produce its first notification. Suggested outcomes are:

- `NOT_READY` — required prerequisites are still pending before the deadline;
- `READY_COMPLETE` — every requirement in this policy reached a complete result;
- `READY_WITH_UNKNOWNS` — notification is timely and safe, but one or more allowed requirements are explicitly unknown, not verified, unavailable, or timed out;
- `BLOCKED_IDENTITY_REVIEW` — canonical identity is not safe enough to notify as one property.

Exact names remain an implementation decision, but the distinct semantics are required.

A normal new-property notification requires:

- sufficiently safe identity resolution and a canonical `Property`;
- basic facts such as price/property type and useful descriptive facts when available;
- retained source links and field-level provenance;
- the best currently obtainable address/location precision, explicitly labeled;
- configured high-priority enrichment in a policy-accepted terminal state: completed, explicitly `UNKNOWN`/`NOT_VERIFIED`, or timed out;
- evaluation based on the available evidence; and
- major conflicts surfaced rather than hidden.

The policy defines:

- applicable notification/event type;
- identity threshold and conflicts that block;
- minimum basic facts;
- high-priority versus optional enrichment;
- accepted terminal states for each requirement;
- maximum time from the triggering discovery/event to readiness;
- whether a timed-out/failed requirement permits `READY_WITH_UNKNOWNS`; and
- policy version/effective period.

Readiness is re-evaluated as complementary listings, canonical facts, enrichment, or the deadline changes. Optional map, amenity, routing, or other provider failure must not keep a property in `NOT_READY` forever. At the maximum deadline, policy either permits a timely notification with explicit 「未確認」 items or records a specific blocking reason. Identity ambiguity is not converted into readiness merely because the deadline elapsed.

Every assessment is auditable: property/event, policy version, deadline, input projection/evaluation, per-requirement outcome, provider failure/timeout, conflicts, readiness outcome, evaluated time, and supersession. Later material enrichment can produce a separate update event under notification policy.

## Japanese notifications

When a property reaches a ready state and notification policy permits, the notification contains:

- summary, price, and location precision;
- property specifications and source links;
- transport and nearby amenities;
- confirmed gym status and hazards;
- layout evaluation;
- important strengths and weaknesses;
- verified information, remaining unknowns, and conflicts; and
- recommendation whether tracking is worthwhile.

It offers 「追跡する」 and 「今は追跡しない」.

Every important item must be labeled or grouped as:

- verified;
- source claim only;
- conflicting; or
- unknown/not yet checked, including timeout/unavailable reason when known.

Notification history retains the readiness assessment, property/events, destination reference, type/channel, locale, policy/template/payload versions, historical content snapshot, provider references, attempts, delivery status, and timestamps.

## Secure action behavior

- Recipient/destination is configuration/secret-driven, never hard-coded.
- Links use high-entropy scoped signed/random expiring tokens.
- GET validates and shows a confirmation page but does not change state.
- Confirmation POST applies one atomic action.
- Tokens are scoped to user/destination, property, notification, and allowed action.
- Store token hashes where feasible; prevent tampering, replay, mismatch, and concurrent double-use.
- Expired, revoked, invalid, or consumed tokens fail safely.
- Logs, referrers, and third-party content must not leak token values.

Exact authentication and whether possession of the email link is sufficient remain security decisions.

## Notification deduplication and delivery

- Meaningful event identity is separate from notification eligibility.
- Deduplicate by event/change, destination, channel, and policy/template version.
- Provider delivery uses an idempotency key and retains each attempt.
- Provider acceptance is not proof of inbox delivery.
- Correction/reprocessing policy must avoid retroactive notification floods.

## Polling and scheduling behavior

Support configurable:

- discovery and source-specific intervals;
- tracking intervals;
- retries, timeouts, exponential backoff, jitter;
- source/provider rate limits and cooldown;
- non-overlapping leases and idempotent jobs;
- parser/source health and pause controls.

Do not poll everything every minute. Apply backpressure and isolate source failures.

## Reporting

Every comparable run produces an auditable report, even if no property qualifies:

1. 重点候補;
2. 保留観察/情報不足;
3. 除外 with every known rejection reason;
4. changes since the prior run: new, price decrease/increase, ended, disappeared, relisted, enriched, and state changed.

Reports identify stale, unknown, conflicting, and failed enrichment rather than hiding them. They retain configuration, evaluation, and template versions so the output can be reproduced.

## Manual review

Future review supports:

- possible duplicate;
- conflicting 建築確認番号 or 号棟;
- address/location ambiguity;
- conflicting property areas or status;
- canonical field conflicts; and
- enrichment uncertainty.

Review actions include merge, split, distinct, reassignment, correction, override, revert, and defer. Every action records actor, time, rationale, evidence, before/after references, and recomputation effects without modifying source facts.

## Operational questions

Run history and health views must answer:

- when each source/search last attempted and succeeded;
- when tracking last ran;
- which source/parser/provider is failing;
- observations/listings/new properties per run;
- identity decision distribution and review backlog;
- enrichment success/cache/staleness;
- notification acceptance/failure;
- overdue/retrying/dead jobs; and
- backup age/restore status when deployed.

A lack of email is never the only health indicator.
