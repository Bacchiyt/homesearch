# Deployment and Provider Architecture

Read with [Architecture](../architecture.md), [Quality/open decisions](../product/quality-and-decisions.md), and [Roadmap](../roadmap.md).

## Secure action endpoint

Potential web endpoints:

- shallow health/readiness;
- detailed authenticated operational status;
- notification action landing;
- action confirmation POST;
- later property/review/tracking/report APIs.

Action flow:

1. Email contains a high-entropy opaque HTTPS token.
2. GET validates without mutating and shows property/action/expiry.
3. POST confirms with token-bound/CSRF-safe semantics.
4. Server atomically consumes token and records tracking transition.
5. Invalid, expired, mismatched, revoked, or replayed tokens fail safely.

Store a token hash where practical. Scope it to destination/user, property, action, and notification. Log only a non-sensitive identifier. Avoid token leakage through referrers or third-party landing-page content.

## Minimal topology

When approved:

- one web process for confirmations/health;
- one or more instances of the same worker process;
- one scheduler process or platform schedule invoking scheduler logic;
- the Gate A-selected production relational store;
- optional object storage; and
- approved email/enrichment providers.

Processes may share one image/platform. A dedicated broker is intentionally absent initially.

## Portability

- Use standard migrations, retain a documented path to the likely PostgreSQL target, and isolate optional extensions.
- Keep durable state in the selected relational store/object storage, never ephemeral local disk.
- Retain object checksum/logical metadata, not only provider URLs.
- Use provider ports and neutral domain result types.
- Separate infrastructure and secrets.
- Support logical relational exports and raw-object manifests/copies.
- Record runtime/schema/parser/rule versions.
- Keep scheduling semantics outside domain code.

## Backup and recovery

Before data becomes valuable:

- define RPO/RTO;
- automate encrypted backups appropriate to the selected production relational store;
- keep an affordable recoverable copy outside the primary failure domain;
- export object manifests and verify checksums;
- document configuration/secret reconstruction;
- perform and record restoration drills; and
- test risky migrations against restored copies.

Frequency, retention, encryption/key custody, provider, and recovery environment remain unresolved.

## Provider strategy

No provider or price is selected.

| Capability | Architectural rule | Research needed |
|---|---|---|
| Database | Gate A selects local/MVP/production/migration strategy; PostgreSQL is the likely production target | Japan region, backup, cost, egress, extensions/PostGIS, scaling/sleep, migration timing |
| Email | Transactional adapter with idempotency/webhook option | Japanese delivery, sender requirements, privacy, cost |
| Geocoding | Cached inputs/results with precision/terms | Japanese quality, official/open options, quota, redistribution |
| POI/business | Bounded categories and area/input cache | Coverage, categories, current hours, terms, cost |
| Routing | Separate walking/cycling/driving/transit evidence | Time-dependent routes, bus/traffic quality, quota |
| Hazard | Prefer official versioned Japanese data | Authority, license, update cycle, coordinate resolution |
| Terrain/roads | Evidence-based dataset/provider adapter | Width/gradient coverage, license, resolution |
| Object storage | Replaceable checksum-addressed lifecycle | Cost, egress, encryption, retention constraints |
| Monitoring | Exportable logs/metrics plus run ledger | Hosted cost versus operational burden |

Official/open data may suffice for some addresses/hazards but must be verified. Current business hours, quality routing/traffic, or geocoding may require paid APIs; caching controls cost.

## Scaling

Scale vertically and with stateless worker replicas first. Potential extraction points only after measurement:

- source fetch workers with distinct browser/network requirements;
- expensive image/layout enrichment;
- notification delivery; and
- analytical/reporting read models.

Extraction preserves stable job/event contracts and transactional handoff. Microservices are not a roadmap goal.

## Architecture risks

- Named sources may disallow or block automated access.
- Japanese addresses and 号棟 may remain ambiguous.
- Reliable bus congestion data may be unavailable/expensive.
- Current 24-hour gym evidence needs trustworthy refreshable hours.
- Natural-light evaluation is technically and evidentially difficult.
- Raw payload retention creates copyright, storage, privacy, and replay tradeoffs.
- False merges are more harmful than delayed review.
- Twice-daily tracking may conflict with source terms, limits, or cost.
- Delivery acceptance does not prove inbox receipt.
- Low-cost platforms may sleep or restrict reliable background scheduling.
- Provider-derived data may become stale or have display/redistribution restrictions.

Treat these as source assessments, experiments, ADRs, and roadmap gates—not hidden assumptions.
