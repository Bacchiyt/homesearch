# Source and Ingestion Requirements

Read with [Product specification](../product-spec.md), [Pipeline and interfaces](../architecture/pipeline-and-interfaces.md), and [Ingestion data model](../data-model/ingestion.md).

## Configurable discovery

Configuration must support:

- enabled/disabled sources;
- one or more search areas independent of adapter/parser logic;
- price bands and an optional negotiation-margin policy;
- property types and new/used preference;
- source/search-specific polling and request limits;
- transport destinations, evaluation profiles, recipients, locale, feature flags, retention, and providers.

Initial examples—not business logic—are:

| Municipality | Example target areas |
|---|---|
| 藤沢市 | 石川、円行、遠藤東側 |
| 大和市 | 下鶴間、深見西 |
| 横浜市泉区 | いずみ中央南、上飯田町南部、ゆめが丘、下飯田町 |
| 横浜市旭区 | 二俣川、本村町、中沢、南本宿町 |
| 横浜市瀬谷区 | 瀬谷、橋戸 |

These labels need validation against official/source address vocabularies. Initial price interest is roughly ¥45,000,000 or less, while somewhat higher prices may be relevant for negotiation.

Initial source interest includes SUUMO, at home, LIFULL HOME'S, 朝日土地建物, local brokers, developers, and sellers. The list is configurable and does not approve automated access.

## Source adapters

Each independent adapter supports, as applicable:

- discovery;
- detail fetch or lawful alternative ingestion;
- source/listing identifiers;
- parsing and source-specific status interpretation;
- rate/timeout policy;
- parser/schema version;
- permitted fixtures/snapshots; and
- health/failure signals.

A source failure must not stop unrelated sources. Geographic, price, and property criteria are supplied as configuration, not embedded in parser logic.

Before live access, assess source terms, robots.txt, API/feed options, authentication, rate limits, anti-bot constraints, copyright, payload/fixture retention, and applicable law. Do not bypass CAPTCHAs, access controls, authentication, or technical protections. If automation is inappropriate, fail gracefully and support lawful API, feed, export, email, file, or manual ingestion.

## Discovery versus tracking

- **Discovery** searches configured source/area/filter combinations for newly appearing listings.
- **Tracking** re-checks known listings/properties for price, status, information, disappearance, relisting, and other changes.

They may reveal the same update but must use idempotent shared observation/event processing rather than separate truth paths.

## Immutable observations

Every fetch/ingestion should be capable of creating an immutable observation with:

- source, listing reference, requested/final URL, and observation time;
- request/fetch outcome, HTTP metadata, content type, latency, retry/correlation context;
- source-visible title, description, price, address, transport, attributes, dates, and status;
- ingestion method and parser/schema version;
- content hash and optional raw payload reference; and
- retention class and compliance metadata.

Capture modes are source-policy-driven:

- permitted full payload;
- sanitized/redacted payload;
- relevant fragments;
- structured source facts only;
- hash/fetch metadata only; or
- transient parsing with no retained body.

Raw bodies may expire under an approved retention policy, but durable observation metadata, permitted extracted facts, provenance, and history must remain unless a legal erasure procedure requires otherwise. The system must expose when replay is impossible.

## Parsing and data quality

- Parsing produces source facts, not canonical property truth.
- Every fact points to its observation and parser version.
- Missing or malformed fields are explicit.
- Parser changes create new derived results; they do not overwrite earlier parses.
- Parser health tracks success, required-field presence, drift, and partial/failure outcomes.
- Fixtures are representative, legally appropriate, minimized, and provenance-documented.

## Publication and availability evidence

Track independently where available:

- system first/last observed;
- source publication date;
- information provision date;
- source update and next scheduled update;
- transaction-condition validity date;
- source status;
- disappearance/reappearance;
- 掲載終了, 販売終了, 成約済み, and relisting; and
- price changes.

Normalized listing statuses initially include `ACTIVE`, `INACTIVE`, `SOLD`, `ENDED`, `DISAPPEARED`, `UNKNOWN`, and `RELISTED`.

One failed fetch or absent search result does not establish disappearance or sale. Search-engine results/cached indexes may aid discovery but are never proof of current availability. Prefer current detail-page or authoritative-source evidence.

## Source access risks

- Named sites may prohibit or technically prevent reliable collection.
- IDs and URLs can be missing, reused, or changed during relisting.
- Source markup/status language will drift.
- Twice-daily tracking may conflict with rate limits, cost, or access terms.
- Full response retention can conflict with copyright, privacy, storage, or source policy.

These are source-specific assessment gates, not problems to solve through evasion.

