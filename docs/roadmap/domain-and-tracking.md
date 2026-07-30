# Roadmap: Domain, Tracking, and Notifications

Read with [Roadmap](../roadmap.md). Every phase preserves its cross-phase rules and gates.

## Phase 4 — Normalization, address parsing, and identity resolution

**Goal:** create explainable normalized evidence and conservative property links.

**Deliverables:**

- versioned normalization with raw provenance;
- Japanese price, area/unit, date, text, 建築確認番号, 号棟, project, and initial address normalization;
- identity evidence/candidate/decision schema;
- conservative generation/scoring and strong-conflict rules;
- `AUTO_MATCH`, `POSSIBLE_MATCH`, `MANUAL_REVIEW`, `DISTINCT`;
- minimal review workflow;
- audited reassignment/merge/split operations;
- permitted labeled identity corpus.

**Tests:**

- normalization idempotency/raw retention;
- address variants and meaningful block/lot distinctions;
- missing/variant/conflicting/reused 建築確認番号;
- same development with distinct 号棟;
- area tolerances/units;
- approximate location cannot force exact match;
- false-positive suite and repeatable explanations;
- merge/split preserves observations, IDs, lineage, historical links.

**Completion criteria:**

- every link has an explainable versioned decision;
- ambiguity/conflict remains unmerged/reviewable;
- user-approved conservative false-positive behavior;
- operations are reversible/supersedable without evidence loss.

**Dependencies:** Phase 3 for real fixtures; synthetic work may begin after Phase 2.

**Intentionally deferred:** sophisticated photo matching, machine learning, polished review UI, broad geocoding.

## Phase 5 — Cross-source merge and field-level provenance

**Goal:** canonical property views from competing candidates without overwriting evidence.

**Deliverables:**

- field registry/candidate model;
- canonical selection history/current projection;
- field-specific merge policies;
- authority/freshness/precision/verification/conflict rules;
- conflict review cases;
- price/publication/status history projections;
- second approved source or synthetic second-source proof;
- projection rebuild/replay.

**Tests:**

- processing-order independence;
- field-specific official authority only;
- newer lower-quality data does not universally win;
- conflicts remain inspectable;
- unknown does not erase known without explicit staleness;
- source correction/supersession/full replay;
- historical price/status reconstruction;
- current projection consistency.

**Completion criteria:**

- one property combines complementary listings;
- every selection identifies candidates/evidence/policy version;
- conflicts visible;
- projections rebuild from durable records.

**Dependencies:** Phase 4; second approved source only for live cross-source proof.

**Intentionally deferred:** external enrichments, advanced review UI, final recommendation.

## Phase 6 — Change events, tracking, and scheduled job reliability

**Goal:** auditable semantic changes and safe tracked-property checks.

**Deliverables:**

- property/listing events and versioned detectors;
- deterministic fingerprints;
- tracking states/transitions;
- separate discovery/tracking schedules;
- durable leases, retries/backoff/jitter/timeouts/non-overlap/dead work/pause;
- configurable twice-daily baseline;
- source-specific disappearance/relisting policy;
- auditable zero-result run reports;
- correction/reprocessing suppression hooks.

**Tests:**

- price direction versus formatting;
- ended/sold/disappeared/relisted distinctions;
- failed/partial run cannot mark disappearance;
- miss/detail-confirmation policy;
- listing addition, precision, and identity-evidence events;
- retry/lease recovery/overlap;
- unchanged input creates no duplicate event;
- `NOT_TRACKING` reactivation;
- rejected/archived data retained.

**Completion criteria:**

- historical first-seen/price/status/listing queries work;
- tracked property scheduled without duplicate overlap;
- meaningful change emits one explainable event;
- run ledger proves health independent of email.

**Dependencies:** Phase 5.

**Intentionally deferred:** outbound email/public endpoint, enrichment events, dashboard UI.

## Phase 7 — Japanese email notifications and secure tracking actions

**Goal:** deduplicated Japanese notifications and safe tracking decisions.

**Deliverables:**

- provider-neutral email interface and approved provider;
- versioned Japanese templates;
- immutable notification snapshots/delivery history;
- event/destination/policy deduplication;
- token hash/expiry/revocation/replay model;
- HTTPS landing plus confirmation POST;
- tracking audit and privacy/redaction/deliverability procedures;
- sandbox/test delivery.

**Tests:**

- same event once; distinct event allowed;
- idempotent delivery retry;
- required content, precision, verified/unknown/conflicting facts, strengths/weaknesses, links, recommendation;
- GET non-mutation;
- valid POST, expiry, tamper, mismatch, replay, revoke, concurrency;
- CSRF/referrer/log/token leakage;
- reactivation.

**Completion criteria:**

- Gate C email/action choices approved;
- reproducible correct Japanese test notification;
- scoped expiring confirmation-based action;
- observable safe provider failure;
- no recipient/credential committed.

**Dependencies:** Phase 6 and Gate C.

**Intentionally deferred:** multi-channel notification, broad UI, production delivery before deployment approval.

