# Enrichment and Evaluation Data Model

Read with [Conceptual data model](../data-model.md) and [Enrichment/evaluation requirements](../product/enrichment-and-evaluation.md).

## Address and location

### `AddressEvidence`

Raw/parsed source or manual claim.

**Fields:** observation/source fact, raw address, parsed prefecture/city/ward/ōaza/chōme/block/lot, normalized form, precision, parser version, confidence, and withheld-detail indicator.

### `LocationCandidate`

Provider/evidence-derived position/address.

**Fields:** property, coordinates/CRS, normalized address/components, precision (`EXACT`, `BLOCK`, `CHO`, `APPROXIMATE`, `UNKNOWN`), provider/dataset version, input fingerprint, checked/refresh time, confidence, licensing/display constraints, supporting/conflicting evidence.

### `PropertyLocationSelection`

Versioned chosen candidate plus full candidate set, rule/version, conflict state, and rationale. Never display coordinates more precisely than evidence.

PostGIS is an ADR candidate; if adopted, isolate it from portable export.

## Transport

### `TransportAccessClaim`

Source-reported mode, station/stop/route, minutes/distance/transfers, raw text, source-effective time, normalized place references, and claim status.

### `TransportDestination`

Configurable/versioned commute or lifestyle destination with stable ID, location, and arrival/departure preferences.

### `RouteAssessment`

Property/location version plus destination/version, provider/algorithm, mode, time window, duration/distance/transfers, traffic assumptions, reliability range/confidence, checked/refresh time, input fingerprint, and evidence.

Theoretical duration and congestion/reliability remain separate.

## Amenities and business hours

### `Amenity`

Provider-neutral place/business identity.

**Fields:** internal ID, normalized name/categories/address/location, provider IDs, official identity/website when known, currentness/lifecycle, and duplicate-review state.

### `AmenityObservation`

Provider claim with external ID, name/category/address/location, hours, checked time, provider/dataset version, permitted evidence, confidence, and retention/display terms.

### `PropertyAmenity`

Versioned property/location-to-amenity relation with category, straight-line and meaningful route times/distances by mode, route/provider evidence, precision, refresh time, and input fingerprint.

### `BusinessHoursVerification`

Explicit hours verification such as `OPEN_24_HOURS`.

**Fields:** amenity, structured claim, result (`VERIFIED`, `NOT_VERIFIED`, `CONFLICTING`, `UNKNOWN`), authoritative evidence, method, checked/expiry time, and confidence.

Gym evaluation requires both route evidence and current hours verification. Failed hours lookup is not verified non-24-hour status.

## Hazard, terrain, and roads

### `HazardDatasetVersion`

Authoritative dataset/release identity with license, coverage, resolution, publication time, and import checksum.

### `HazardAssessment`

**Fields:** property/location version, hazard type, classification/value, knowledge/verification, dataset/version/feature reference, spatial method/precision/buffer, checked/evaluated time, algorithm version, and evidence.

A no-intersection result may mean unknown, outside coverage, or verified low risk depending on dataset semantics; do not conflate them.

### `TerrainRoadAssessment`

Versioned slope, gradient, road width, access difficulty, and flat/hilly evidence using the same provider/dataset/location/precision/version pattern.

## Evaluation

### `EvaluationProfile` and `EvaluationProfileVersion`

Stable profile plus immutable hard filters, preferences, thresholds, weights, destinations, evidence sufficiency, and label policy.

The initial profile includes natural light and confirmed 24-hour gym as hard requirements. All distances and preferences remain configurable.

### `PropertyEvaluation`

One evaluation against a profile/input projection.

**Fields:** property/profile version, algorithm version, input fingerprint, evaluated time, overall category (`FOCUS`, `OBSERVE`, `REJECT` or approved localized equivalent), confidence, stale/superseded state, and reason codes.

### `EvaluationCriterionResult`

Independent hard/preference result with criterion key/type, typed outcome, pass/fail/unknown, optional score, rejection flag, threshold/version, confidence, and explanation.

Examples:

- natural light: `PASS | FAIL | UNKNOWN | NEEDS_CONFIRMATION`;
- LDK openness: `STRONG | NORMAL | WEAK | UNKNOWN`;
- pantry: `YES | NO | UNKNOWN`;
- confirmed 24-hour gym: pass/fail/unknown based on hours plus walking threshold.

Multiple hard failures retain multiple rejection reasons.

### `EvaluationEvidence`

Binds a criterion to field values, observations, permitted media/floor plans, enrichments, routes, or hazards.

**Fields:** criterion result, evidence reference/type, role (`SUPPORTS`, `CONFLICTS`, `MISSING_REQUIRED`), contribution, captured version, and explanation.

Marketing copy alone cannot pass verified natural-light or gym criteria.

