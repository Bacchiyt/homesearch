# Property, Identity, Provenance, and History Requirements

Read with [Product specification](../product-spec.md) and [Identity and provenance data model](../data-model/identity-and-provenance.md).

## Property versus listing

One physical property may have portal, broker, developer, and seller listings. These remain separate `Listing` records linked to one canonical `Property` only when identity evidence supports it. Each listing has many immutable observations.

## Identity resolution

Use an internal immutable `property_id`. 建築確認番号 is strong evidence, never the database primary key and never a universal sole merge rule.

Candidate comparison may use:

- 建築確認番号 and normalized variants;
- 号棟 and project/development name;
- normalized/precise address and 番地;
- coordinates and location precision;
- land/building area;
- floor plan and floors;
- completion date and construction status;
- builder, developer, and seller;
- nearby station; and
- permitted photo or other supporting evidence.

建築確認番号 may be missing, inconsistent, wrong, development-wide, or insufficient to distinguish 号棟. Every decision retains score/confidence, positive reasons, conflicts, algorithm version, and a result such as `AUTO_MATCH`, `POSSIBLE_MATCH`, `MANUAL_REVIEW`, or `DISTINCT`.

Strong conflict or ambiguous 号棟 prevents automatic merge. False merges are more harmful than delayed matches. Thresholds require fixture-based calibration.

Manual merge, split, listing reassignment, correction, and override are audited, reversible/supersedable, and preserve property-ID lineage plus all original evidence.

## Canonical merge and provenance

For every canonical field retain:

- chosen normalized value;
- all relevant source/derived candidates;
- originating observation or enrichment result;
- observed/effective time;
- verification, confidence, and precision;
- selection policy/version and rationale; and
- conflict state.

Precedence is configurable by field. An official developer may be preferred for completion schedule, while a current portal observation is authoritative for that portal's current asking price. Freshness and source reliability matter, but there is no universal source ranking and no last-processed-wins rule.

## Property information

The canonical property supports, where known:

- current price and price history;
- raw, normalized, and precise address;
- coordinates and location precision;
- new/used and construction status;
- land/building areas;
- floor plan, floors, orientation, openings, and layout features;
- road/access, parking, zoning, structure, building/floor-area ratios;
- builder, developer, and seller;
- 建築確認番号, 号棟, and development/project name;
- completion/expected completion and handover timing;
- energy, insulation, and certification claims/evidence; and
- all source URLs.

The catalog is extensible but should not become an untyped catch-all for core queryable concepts.

## Claims and verified features

For every listing, preserve:

- original headline/title;
- catch copy and selling-point text;
- normalized marketing keywords/features;
- source/listing/observation attribution; and
- first and last observed times.

Candidate selling points include 南道路, 角地, 駅徒歩○分, LDK20帖, 吹抜け, パントリー, SIC, 駐車2台, 長期優良住宅, ZEH, 制震, and 耐震等級3.

Normalization uses a versioned concept/alias vocabulary while retaining the exact original wording. For example, `SIC` and `シューズインクローク` may map to one normalized claim concept, as may `パントリー` and `食品庫`. Alias normalization does not verify the claim.

The canonical property needs a rebuildable, historical marketing-claim aggregation that can answer:

- normalized claim/concept and observed raw variants;
- how many distinct current/relevant listings mention it;
- the denominator and versioned definition of “current/relevant listing”;
- supporting listings and sources;
- first/last seen; and
- calculation time, input fingerprint, and aggregation/alias versions.

Example output:

```text
吹抜け — 4 of 6 current/relevant listings
sources: SUUMO, broker A, broker B, developer
first seen: ...
last seen: ...

パントリー — 3 of 6 current/relevant listings
```

Count distinct listings rather than repeated observations. Historical views may include inactive listings, but must label the denominator policy.

Distinguish:

- `MARKETING_CLAIM`;
- normalized marketing claim/feature concept; and
- `VERIFIED_FEATURE` or another verified canonical fact.

Repeated broker/source emphasis is useful for summary, discovery of synonymous descriptions, and changes in marketing emphasis over time. Repetition—even across every listing—does not automatically create a `VERIFIED_FEATURE`.

Detailed NLP, synonym discovery, and extraction implementation are deferred. Phase 0 defines the domain outputs and audit requirements only.

## Knowledge states

Where appropriate retain `value`, `knowledge_state`, `verification_status`, confidence, source/evidence, observed time, and algorithm version.

- No pantry mention does not prove there is no pantry.
- No 建築確認番号 found does not prove none exists.
- No business or hazard result does not prove absence or safety.
- A verified `NO` is a known negative supported by evidence, not null/missing.

## Historical reconstruction

The system must answer, within approved retention limits:

- What was the price at a past date?
- When was a property/listing first and last seen?
- Which broker listed it first, and when did others appear?
- When did address precision improve?
- When did a listing disappear or relist?
- Which source claimed a feature?
- When did completion timing change?
- What evidence, canonical values, evaluation, and template supported a notification?

Corrections and new algorithms are additive/superseding. Current projections are rebuildable caches, never the only record.
