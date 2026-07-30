# Homesearch Implementation Roadmap

## How to use this roadmap

Implementation is approval-gated. A phase is complete only when its tests and completion criteria pass—not when files merely exist. Do not begin later phases because their interfaces can be anticipated.

Cross-phase rules:

- observations/evidence remain immutable;
- canonical state retains provenance/conflicts;
- unknown differs from verified negative;
- identity ambiguity is never silently merged;
- configuration/algorithms are versioned;
- jobs/effects are idempotent;
- secrets are not committed;
- source protections are not bypassed;
- rejected/untracked/ended properties remain; and
- durable changes update docs/ADRs.

## Approval gates

### Gate A — foundation

Gate A required the product owner to:

- approve/revise the Phase 0 documents and modular-monolith direction;
- review and explicitly accept, revise, reject, or defer each proposal in the [Gate A ADR set](adr/README.md);
- choose the runtime/toolchain, configuration model, local workflow, and CI gates;
- decide the local-development database, early/MVP persistence, production relational target, and tested migration path;
- decide database access/migrations, identifiers/time, jobs/scheduler phase boundary, initial user scope, web deferral, raw-storage boundary, and cost posture; and
- record any unresolved item with an explicit owner, validation step, and implementation-blocking effect.

**Status: Passed on 2026-07-30.** The product owner explicitly accepted ADRs 0001–0011 after review of the recommendations merged in PR #2. Phase 0 is approved and Phase 1 is authorized to begin. Gate A does not authorize later phases, live source access, outbound providers, credentials, infrastructure, or deployment.

### Gate B — source access

Before any live source:

- assess terms, robots/access, APIs/feeds, authentication, rate limits, retention/fixtures, and fallback ingestion;
- approve one source/path;
- set conservative request policy; and
- separately approve live testing.

### Gate C — outbound providers

Before external email/enrichment/action services:

- research capability, terms, privacy, cost, and quota;
- set monthly budget/approval threshold;
- decide credential handling; and
- approve outbound calls/public HTTPS endpoint.

### Gate D — production deployment

Before production:

- approve providers and expected cost;
- define recovery/retention;
- establish source/privacy compliance;
- approve production resources/credentials; and
- complete security/operations review.

## Phase map

| Phase | Goal | Detailed plan |
|---:|---|---|
| 0 | Durable specification and architecture | [Foundation and ingestion](roadmap/foundation-and-ingestion.md#phase-0--durable-specification-and-architecture) |
| 1 | Skeleton, config, persistence foundation | [Foundation and ingestion](roadmap/foundation-and-ingestion.md#phase-1--project-skeleton-configuration-and-database-foundation) |
| 2 | Source contracts and synthetic/manual raw ingestion | [Foundation and ingestion](roadmap/foundation-and-ingestion.md#phase-2--source-contracts-and-raw-observation-ingestion) |
| 3 | First approved source | [Foundation and ingestion](roadmap/foundation-and-ingestion.md#phase-3--first-approved-source) |
| 4 | Normalization and conservative identity resolution | [Domain and tracking](roadmap/domain-and-tracking.md#phase-4--normalization-address-parsing-and-identity-resolution) |
| 5 | Cross-source merge and field provenance | [Domain and tracking](roadmap/domain-and-tracking.md#phase-5--cross-source-merge-and-field-level-provenance) |
| 6 | Change events, tracking, reliable jobs | [Domain and tracking](roadmap/domain-and-tracking.md#phase-6--change-events-tracking-and-scheduled-job-reliability) |
| 7 | Japanese notifications and secure actions | [Domain and tracking](roadmap/domain-and-tracking.md#phase-7--japanese-email-notifications-and-secure-tracking-actions) |
| 8 | Location resolution | [Enrichment and operations](roadmap/enrichment-and-operations.md#phase-8--location-resolution-foundation) |
| 9 | Amenities and confirmed 24-hour gym | [Enrichment and operations](roadmap/enrichment-and-operations.md#phase-9--amenity-enrichment-and-confirmed-24-hour-gym) |
| 10 | Official hazards | [Enrichment and operations](roadmap/enrichment-and-operations.md#phase-10--official-hazard-enrichment) |
| 11 | Transport, traffic, terrain, and roads | [Enrichment and operations](roadmap/enrichment-and-operations.md#phase-11--transport-routing-traffic-and-terrainroad-enrichment) |
| 12 | Layout, natural light, recommendation | [Enrichment and operations](roadmap/enrichment-and-operations.md#phase-12--layout-natural-light-and-versioned-recommendation) |
| 13 | Manual review, reports, operational visibility | [Enrichment and operations](roadmap/enrichment-and-operations.md#phase-13--manual-review-complete-reporting-and-operational-visibility) |
| 14 | Deployment, backup, recovery, portability | [Enrichment and operations](roadmap/enrichment-and-operations.md#phase-14--deployment-backup-recovery-and-portability-hardening) |

## Cross-phase testing

| Concern | Starts | Continues through |
|---|---:|---|
| Configuration and secret safety | 1 | every phase |
| Selected-store migrations and PostgreSQL compatibility/migration path | 1 | every schema change |
| Observation immutability/replay | 2 | every parser/normalizer change |
| Parser fixtures/drift | 2–3 | every source change |
| Identity false positives | 4 | every evidence/algorithm change |
| Merge order/provenance | 5 | every field/provider addition |
| Event/notification idempotency | 6 | every new event/enrichment |
| Action-link security | 7 | every auth/deployment change |
| Provider failure/unknown handling | 8 | every enrichment |
| Algorithm/profile versioning | 4–5 | every derived-data phase |
| Run/report auditability | 6 | every workflow |
| Backup/restore | prepare before production | every production migration |

## Accepted Gate A decisions and later backlog

The [accepted Gate A decision set](adr/README.md) covers runtime/tooling, database strategy/access, configuration, jobs, web, user scope, raw storage, local development, CI, and cost. ADRs 0001–0011 are `Accepted` and are the implementation baseline for Phase 1.

Create later ADRs only when their gate/phase needs them:

1. One access/fixture assessment per materially different source.
2. Field representation/merge policy, marketing-claim aggregation, alias policy, and identity thresholds/override precedence.
3. Notification readiness/deadline policy and email/action security.
4. PostGIS adoption and portable spatial fallback if Phase 8 evidence justifies it.
5. Geocoding, POI, routing/traffic, hazard, and media evidence.
6. Hosting/provider selection, backup/recovery, monitoring, and production retention.
7. Authentication/authorization before public access or a second user.

## Current authorization

Phase 1 is authorized to begin because Gate A passed through explicit product-owner approval. This documentation-only acceptance change does not start Phase 1 implementation. Phase 2 and later work remain subject to phase dependencies, and Gates B–D still block live source access, outbound providers, production resources, credentials, and deployment.
