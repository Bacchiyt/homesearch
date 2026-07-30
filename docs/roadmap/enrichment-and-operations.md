# Roadmap: Enrichment and Operations

Read with [Roadmap](../roadmap.md). Every phase preserves its cross-phase rules and gates.

## Phase 8 — Location resolution foundation

**Goal:** select the best-supported property location without overstating precision.

**Deliverables:** address evidence/location candidates/selections; approved provider; input/version cache; `EXACT`/`BLOCK`/`CHO`/`APPROXIMATE`/`UNKNOWN`; conflict review; precision-improvement events; license/display metadata.

**Tests:** every precision level; partial stays partial; conflicting address/coordinates; cache/version behavior; failure → `UNKNOWN`; display precision; one improvement event.

**Completion criteria:** chosen location has evidence/provider/version/time/precision/confidence/rule; ambiguity reviewable; unchanged inputs cached; notifications label approximation.

**Dependencies:** Phases 5–6 and Gate C.

**Intentionally deferred:** amenities, routes, hazards, terrain, unsupported parcel certainty.

## Phase 9 — Amenity enrichment and confirmed 24-hour gym

**Goal:** bounded useful amenities and evidence-based gym hard filter.

**Deliverables:** amenity identity/observations/relations; approved POI provider; categories/bounded search; meaningful mode distances; hours verification; refresh cache; configurable preferred/required gym thresholds; configurable shopping-drive preference.

**Tests:** provider duplicates/categories; bounded results; route/location invalidation; gym without hours unknown; verified non-24-hour; confirmed option inside/on/outside threshold; stale/conflicting hours; failure does not prove absence; cache/change events.

**Completion criteria:** gym uses current hours plus walking access; unknown does not false-pass/fail; calls cached; cost/quota measurable.

**Dependencies:** Phase 8, Phase 5 evaluation foundation, Gate C.

**Intentionally deferred:** exhaustive POIs, hours inference, traffic-aware driving.

## Phase 10 — Official hazard enrichment

**Goal:** location-specific hazards from approved versioned datasets.

**Deliverables:** dataset/version adapter; flood/inland flood/landslide/approved hazards; license/coverage/resolution; precision-aware spatial classification; no-result distinctions; location/dataset refresh; report evidence.

**Tests:** risk classes/boundaries; outside coverage versus no intersection; approximate location; dataset re-evaluation; failure unknown; caching; one material event.

**Completion criteria:** every assessment cites dataset/version/location/method/time; missing never “safe”; licensing/update process documented; old versions reconstructible.

**Dependencies:** Phase 8 and Gate C.

**Intentionally deferred:** unsupported parcel certainty, insurance/legal advice, terrain.

## Phase 11 — Transport, routing, traffic, and terrain/road enrichment

**Goal:** compare source claims with practical destination-specific access and road environment.

**Deliverables:** versioned destinations; source claims versus routes; approved mode provider; time-window/transfers/reliability; bus congestion evidence where available; terrain/road experiment; input cache.

**Tests:** destination invalidation; source claim not auto-verified; time/no-route cases; theory versus reliability; missing traffic unknown; approximate origin precision; cache/cost; missing terrain coverage not flat/easy.

**Completion criteria:** routes state destination/mode/assumptions/provider/version/window/confidence; unsupported congestion explicit; cost/refresh measured; terrain evidence-based or unknown.

**Dependencies:** Phase 8 and Gate C; may reuse Phase 9 routing.

**Intentionally deferred:** unsupported commute guarantees, real-time navigation, hard-coded destinations.

## Phase 12 — Layout, natural light, and versioned recommendation

**Goal:** explainable house-quality criteria and overall category without manufactured certainty.

**Deliverables:** profiles/criteria/evidence; hard versus preference engine; natural-light rubric; independent LDK/kitchen/storage/SIC/circulation; claim/normalized/verified features; all rejection reasons; approved Japanese wording; re-evaluation/version comparison.

**Tests:** marketing copy cannot pass light; obstruction can fail with reasons; unfinished/insufficient unknown; independent preferences; multiple failures retained; new version preserves old; rejected remains searchable/re-categorizable; deterministic fixed inputs.

**Completion criteria:** every result cites evidence/version; hard/preferences separate; approved category policy; automated media inference is not overstated.

**Dependencies:** Phase 5; Phase 9 for gym; Phases 8–11 as available.

**Intentionally deferred:** unvalidated autonomous visual judgment, unapproved model cost, daylight simulation without geometry.

## Phase 13 — Manual review, complete reporting, and operational visibility

**Goal:** make ambiguity, history, and health usable.

**Deliverables:** review for identity/address/location/status/enrichment conflict; audited operations UI/API; complete categories/reasons/deltas; operational status for source/parser/jobs/notifications/backups; low-noise alerts; versioned report artifacts.

**Tests:** concurrent/stale review protection; merge/split recomputation/lineage; zero-result report; all reasons/unknowns/conflicts; prior-run comparison; alert noise; redaction/authorization.

**Completion criteria:** user can answer “is it running?”; ambiguity resolvable/deferable; reports reproducible with no matches; corrections preserve observations/notifications.

**Dependencies:** Phases 6 and 12; review foundation begins in Phase 4.

**Intentionally deferred:** elaborate analytics, public/team dashboards, unnecessary administration.

## Phase 14 — Deployment, backup, recovery, and portability hardening

**Goal:** continuous operation at known cost with tested recovery/provider exit.

**Deliverables:** approved low-cost web/scheduler/worker topology; production providers; secret setup; safe migration rollout; encrypted backups/off-domain copy; restore drill; relational/object export/import; pause/circuit breakers/runbooks; cost/quota views; retention/compliance; application recovery.

**Tests:** production-like smoke; scheduler/worker restart/lease recovery; isolated database restore; object checksum import; migration on restored copy; credential rotation; provider outage degradation; HTTPS action security; cost/quota alerts.

**Completion criteria:** Gate D approved; actual restore meets RPO/RTO; migration procedure dry-run where practical; unattended health visible; cost within budget; no committed secrets.

**Dependencies:** only approved initial-production features, generally Phases 1–7 and 13 plus selected enrichment; Gate D mandatory.

**Intentionally deferred:** Kubernetes, unnecessary microservices, active-active, expensive queues, unmeasured scaling.

