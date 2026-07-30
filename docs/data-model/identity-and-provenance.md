# Identity, Provenance, and History Data Model

Read with [Conceptual data model](../data-model.md) and [Property/history requirements](../product/property-and-history.md).

## Property identity entities

### `Property`

Stable canonical anchor for a physical residence.

**Fields:** immutable `property_id`, property type, lifecycle/projection/identity state, created and first/last observed times, current projection version, and optional supersession status.

The row is not the full state. Merged IDs remain resolvable through lineage; splits may map one former property to several successors.

### `PropertyListingLink`

Versioned assertion that a listing refers to a property.

**Fields:** property/listing, validity interval, link state, identity decision, confidence, resolution method (`AUTO`, `MANUAL`), and created time.

A listing normally has at most one active link; corrected historical links remain.

### `IdentityEvidence`

Normalized evidence usable for candidate generation/comparison.

**Fields:** kind, listing/property/observation/source-fact references, raw/normalized value, quality/precision/confidence, verification, observed/effective times, normalizer version.

Kinds include 建築確認番号, 号棟, development, address, coordinates, areas, floor plan, completion/status, builder/developer/seller, station, and permitted photo fingerprint.

### `IdentityCandidate`

Considered unresolved listing/property pair.

**Fields:** left/right IDs, candidate-generation method/version, coarse reason, created time, and processing state. Candidate generation improves recall but never merges.

### `IdentityDecision` and `IdentityEvidenceLink`

Immutable algorithm/manual result plus exact evidence contributions.

**Fields:** candidate, score/confidence, resolution (`AUTO_MATCH`, `POSSIBLE_MATCH`, `MANUAL_REVIEW`, `DISTINCT`), positive/conflicting reasons, thresholds/configuration, algorithm version, time/actor, supersession; evidence link includes comparison, weight/contribution, severity, and reason code.

### `IdentityOperation` and `PropertyIdentityAlias`

Audit manual/approved `MERGE`, `SPLIT`, `REASSIGN_LISTING`, `OVERRIDE_MATCH`, and `REVERT_OVERRIDE`.

**Fields:** actor/time/rationale, review case, before/after references, affected IDs, recomputation state, alias/survivor/successor relationships, effective time, and ambiguity.

## Duplicate-resolution process

### Candidate generation

Index normalized confirmation-number variants, address/location buckets, development plus 号棟, coordinate proximity, areas/floor-plan/completion combinations, and relisting lineage.

No candidate means not found, not proven distinct, unless required searches completed successfully.

### Evidence comparison

- Matching 建築確認番号 is strong; conflicting 号棟 is a strong stop signal.
- Same development/address can contain distinct buildings.
- Area comparison requires unit normalization and tolerances.
- Approximate coordinates cannot prove an exact house.
- Japanese normalization must retain meaningful suffixes/block/lot detail.
- Photo fingerprints, if approved, remain supporting evidence.

### Decision policy

- `AUTO_MATCH`: calibrated high score, required strong evidence, no disqualifying conflict.
- `POSSIBLE_MATCH`: meaningful similarity but insufficient certainty; no automatic link.
- `MANUAL_REVIEW`: ambiguity/conflict requiring user action.
- `DISTINCT`: sufficient contradictory evidence.

False merges are costlier than delayed merges. Retain scores, thresholds, reasons, and conflicts.

### Merge/split effects

A merge selects a surviving anchor, versions listing links, records lineage, recomputes projections/enrichment/evaluation/events, and preserves prior IDs/evidence/notifications.

A split creates/identifies distinct anchors, versions listing reassignment, records lineage, invalidates affected projections, recomputes downstream results, and never rewrites identity evidence. Correction-notification policy must prevent noise.

## Canonical provenance entities

### `PropertyFieldDefinition`

Registry for field key, type/unit, multiplicity, validation schema, sensitivity, merge policy, temporal semantics, and query/index needs.

### `PropertyFieldValue`

Immutable normalized candidate.

**Fields:** property/field, typed value/versioned JSON where necessary, knowledge/verification state, confidence/precision, source authority kind, originating observation/fact/enrichment/manual assertion, observed/effective time, normalizer version, fingerprint, and retraction/supersession reason.

### `CanonicalFieldSelection`

Historical chosen result.

**Fields:** property/field, chosen candidate or explicit unknown/conflict, selected/valid/superseded times, merge-policy version, reason/conflict state, and input-set fingerprint.

### `CanonicalSelectionCandidate`

Complete relevant candidate set at selection time with rank, authority, freshness, precision, accepted/rejected state, and reason.

### `PropertyCurrent`

Optional denormalized current table/view with projection version/rebuild time. It is reproducible and never the only copy.

## Price, status, and publication

### Price

Use field candidates/selections plus a timeline projection. Retain currency, amount, kind/conditions, listing/property context, observation/effective time, source, and verification. Formatting/parser changes do not create price events.

### `ListingStatusAssertion`

One observation's source status text, normalized status/confidence, interpreter version, and effective time.

### `ListingStatusPeriod`

Derived listing timeline with `ACTIVE`, `INACTIVE`, `SOLD`, `ENDED`, `DISAPPEARED`, `UNKNOWN`, or `RELISTED`, start/end, derivation version, evidence/miss windows, and confidence.

Failed requests or one absent result cannot establish disappearance.

### `PublicationFact`

Preserves publication, information-provision, update, next-update, and validity dates separately, with raw representation, parsed precision, source fact, and parser version.

