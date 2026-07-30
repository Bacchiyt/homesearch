# Homesearch Product Specification

## Purpose

Homesearch is a long-lived personal system for discovering, normalizing, enriching, evaluating, tracking, and notifying a user about Japanese residential properties. Its first use case is detached houses (一戸建て), especially new detached houses, while the core model should allow other residential property types later.

The product should:

- discover approved-source listings through configurable searches;
- preserve what each source showed over time;
- recognize when several advertisements describe one physical property;
- merge complementary information without losing provenance or conflicts;
- enrich properties with location, transport, amenities, hazards, terrain, and layout evidence;
- apply configurable, versioned hard requirements and preferences;
- track meaningful changes without deleting disfavored or ended properties;
- provide auditable Japanese notifications and reports; and
- remain maintainable, portable, recoverable, and affordable for years.

This specification does not authorize live scraping, external API setup, production infrastructure, email delivery, deployment, or credentials.

## Core terms

- **Property:** canonical physical home with an internal immutable ID.
- **Listing:** one source's advertisement or official presentation for a property.
- **Observation:** immutable evidence of what a source showed during one fetch/ingestion.
- **Canonical value:** selected normalized property field value with provenance and selection rationale.
- **Enrichment:** information derived from external datasets or analysis.
- **Evaluation:** versioned conclusion or score based on explicit evidence and rules.
- **Tracking:** user intent to re-check a known property more frequently.

## Product principles

1. Preserve permitted raw source facts after parsing and normalization.
2. Make historical state and past knowledge reconstructible.
3. Represent unknown, unverified, missing, and conflicting information explicitly.
4. Keep physical properties separate from advertisements.
5. Never silently resolve ambiguous duplicates.
6. Retain field-level provenance and competing source values.
7. Make searches, sources, schedules, thresholds, destinations, and rules configurable/versioned.
8. Respect source terms, protections, copyrights, privacy, and law.
9. Record operational health independently of whether an email arrives.
10. Keep providers replaceable and stable enrichment cached for low cost.

## Primary workflows

### Discover

1. Select a due source/search configuration.
2. Discover listing references through an approved adapter.
3. Capture fetch metadata and the permitted raw representation.
4. Run versioned parsing and normalization.
5. Resolve the listing to a property, create one, or open manual review.
6. Select canonical field values while retaining provenance/conflicts.
7. Run only required or stale enrichment/evaluation.
8. Emit meaningful idempotent events.
9. Notify only when policy says the property is sufficiently processed and the event has not already been reported.

### Track and review

Discovery and tracking are separate workflows that share ingestion. `TRACKING` properties use a configurable interval, initially at least twice daily where source constraints allow. Manual review handles identity, address, status, and enrichment ambiguity through audited merge, split, correction, override, or deferral.

`NOT_TRACKING`, `ARCHIVED`, rejected, ended, and disappeared properties remain historically intact and can be reactivated where applicable.

## Requirement map

- [Source and ingestion](product/source-and-ingestion.md) — configurable searches, source adapters, observations, access, publication/status evidence.
- [Property and history](product/property-and-history.md) — identity, deduplication, canonical merge, property fields, claims, historical reconstruction.
- [Enrichment and evaluation](product/enrichment-and-evaluation.md) — location, transport, amenities, confirmed gym, hazards, terrain, layout, recommendations.
- [Tracking, notifications, and reporting](product/tracking-notifications-and-reporting.md) — states, meaningful changes, secure actions, deduplication, polling, reports, manual review.
- [Quality constraints and open decisions](product/quality-and-decisions.md) — non-functional requirements, testing, cost, portability, deferred capabilities, ADR candidates.

## Eventual acceptance

Homesearch succeeds when approved sources can be ingested safely; source history can be reconstructed; false property merges are prevented; canonical fields retain provenance; evaluations and events are explainable/versioned; each meaningful event is notified at most as policy permits; tracking decisions are secure; and run/health records show that the monitor is operating even when no property qualifies.

