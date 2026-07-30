# Enrichment and Evaluation Requirements

Read with [Product specification](../product-spec.md), [Enrichment architecture](../architecture/deployment-and-providers.md), and [Enrichment/evaluation data model](../data-model/enrichment-and-evaluation.md).

## General enrichment rules

- Portal data is input evidence, not automatically verified truth.
- Provider/dataset, version, checked time, input evidence, precision/confidence, and retention/display constraints accompany results.
- Provider failure or missing coverage yields `UNKNOWN`, not a negative conclusion.
- High-priority enrichment reports explicit completed, unknown/not-verified, failed, or timed-out outcomes so a versioned notification-readiness policy can make a bounded decision.
- Stable results are cached and refreshed on staleness, dataset change, or material input change—not every poll.
- External providers remain replaceable and require terms, quality, quota, privacy, and cost review.

## Location resolution

Combine exact/partial address, 番地, map pins, coordinates, stations, bus stops, and permitted evidence. Store normalized address, coordinates, geocoder/dataset, checked time, and precision/confidence:

- `EXACT`;
- `BLOCK`;
- `CHO`;
- `APPROXIMATE`; or
- `UNKNOWN`.

Never display 町-level evidence as an exact house location. Conflicting evidence enters review.

## Transportation

Store source-reported station/bus information separately from independently calculated routes:

- station and walking time;
- bus stop/route, scheduled travel time, and transfers;
- configurable commuting/lifestyle destinations;
- departure/arrival windows;
- practical time-dependent routes; and
- reliability/congestion evidence where available.

A theoretical ten-minute bus route is not equivalent to one that regularly takes 25–30 minutes. If typical traffic/reliability data is unavailable, retain `UNKNOWN`; do not hard-code one office destination.

## Amenities and lifestyle

Find a bounded, useful set rather than an exhaustive POI dump:

- discount/affordable, normal, and premium/quality supermarkets;
- convenience stores, drugstores, and 100-yen shops;
- home centers and electronics/household-goods stores;
- restaurants, banks, post offices, and gyms;
- internal medicine, dentistry, dermatology, and gynecology;
- general and emergency-capable hospitals; and
- major shopping malls/commercial complexes.

Use meaningful walking, cycling, and driving time/distance. Major useful shopping access is a configurable preference, initially around 20 minutes by car.

## Confirmed 24-hour gym

The current profile:

- prefers a confirmed 24-hour gym within about five minutes' walk;
- generally requires one within a configurable ten-minute walking threshold; and
- retains but rejects the property under this hard filter if the nearest confirmed option exceeds the threshold.

“Gym” text/category alone does not verify 24-hour availability. Use reliable business/official evidence with verification and expiry times. Missing or stale evidence is `UNKNOWN`/`NOT_VERIFIED`, not pass or fail.

## Natural light and layout

Sufficient natural light is a hard requirement. Marketing text such as 陽当たり良好 is only a claim.

Evidence can include:

- photos and floor plans;
- primary opening orientation;
- LDK window number and size;
- south-facing openings;
- neighboring-building obstruction/distance;
- daylight direction, lot shape, atrium/吹抜け;
- high windows/skylights; and
- construction status.

Results:

- `PASS` when adequate evidence supports sufficient light;
- `FAIL` when evidence clearly shows poor daylight/severe obstruction;
- `UNKNOWN`/`NEEDS_CONFIRMATION` when unfinished or insufficiently evidenced.

Independent preferences:

- `ldk_openness`: `STRONG | NORMAL | WEAK | UNKNOWN`;
- `kitchen_size`: `LARGE | NORMAL | SMALL | UNKNOWN`;
- `pantry_kitchen_storage`: `YES | NO | UNKNOWN`;
- `overall_storage`: `HIGH | NORMAL | LOW | UNKNOWN`;
- `sic_doma_storage`: `YES | NO | UNKNOWN`;
- `circulation`: `GOOD | NORMAL | PROBLEM | UNKNOWN`.

Every conclusion retains evidence and rule/algorithm version.

## Hazards, terrain, and roads

Prefer reliable official, versioned data for:

- flood/洪水;
- inland flooding/内水;
- landslide/土砂; and
- other material hazards.

Store dataset/version, checked time, selected-location precision, spatial method, risk classification, and uncertainty. Missing/failed checks never imply safety.

Future terrain/road assessment supports steep slopes, road gradients, narrow/difficult roads, awkward driving access, and flat/hilly character. Conclusions require evidence and provider/dataset coverage.

## Evaluation and recommendation

Profiles are configurable/versioned and separate:

- **Hard requirements:** currently sufficient natural light and confirmed 24-hour gym access within threshold.
- **Preferences:** LDK openness, storage, pantry, kitchen practicality, SIC/doma, circulation, transport, shopping convenience, and future configured factors.

Potential Japanese-facing categories:

- `重点候補`;
- `保留観察`/情報不足;
- `除外`.

The originating brief also uses Chinese labels 重点候选/保留观察/筛除; final Japanese wording needs approval.

A property may retain multiple rejection reasons. Rejected properties remain for history, deduplication, changed rules, and market analysis. Evaluation records include profile/rule version, evaluated time, input fingerprint, evidence, confidence, and all criterion results.

## Known difficulty

- Exact location may remain impossible with partial source addresses.
- Current gym hours and business status may be stale or unavailable.
- Typical bus congestion may require costly or unavailable data.
- Hazard confidence is bounded by both dataset and location precision.
- Natural-light/layout inference from listing material is technically difficult, copyright-sensitive, and often under-evidenced.
- Low cost may constrain map/routing/image providers; cached or manual evidence may be necessary.
