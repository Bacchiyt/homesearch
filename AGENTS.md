# Homesearch Agent Instructions

Homesearch is a long-lived personal system for discovering, normalizing, enriching, evaluating, tracking, and reporting Japanese residential property listings.

## Before changing the project

1. Start at `docs/README.md`; read the core overview and only the task-specific documents it routes to.
2. Inspect the current implementation, migrations, tests, configuration, and decisions before changing structure.
3. Work only within the smallest approved roadmap phase. Phase 1 is not approved until the user explicitly passes Gate A.
4. Record uncertainty instead of inventing behavior, source permissions, provider capabilities, pricing, or data certainty.
5. Update the relevant docs and ADRs when a durable boundary or decision changes.

## Domain invariants

- `Property`, `Listing`, and immutable `Observation` are distinct.
- Raw source evidence is never overwritten by parsing, normalization, canonicalization, merge, or correction. Retention may vary by source and law.
- Canonical values retain field-level provenance, candidates, conflicts, and selection rationale; processing order is never authority.
- `UNKNOWN` is not `NO`, `FALSE`, `SAFE`, or `NOT_PRESENT`.
- Use an internal immutable `property_id`; 建築確認番号 is strong evidence, never the primary key or sole merge rule.
- Never silently merge ambiguity. Match decisions and manual merge/split/correction/override actions are versioned and auditable.
- Current availability requires current listing/detail evidence when possible; search-index presence is not proof.
- Derived data retains input evidence, rule/algorithm version, and evaluation time.
- Rejected, ended, archived, and `NOT_TRACKING` properties remain historically available.

## Engineering rules

- Preserve module boundaries defined in `docs/architecture.md`; keep sources and external providers behind typed adapters.
- Prefer the documented modular monolith and simple, portable, low-cost infrastructure until measured needs justify change.
- Keep persistence PostgreSQL-compatible/migration-ready; Gate A chooses local, MVP, and production database strategies. SQLite is acceptable only where target-database differences are not hidden.
- Jobs and effects are idempotent, timeout-bounded, retry-safe, rate-limited, jittered, observable, and protected from overlap.
- Search areas, sources, price/property filters, schedules, destinations, evaluation thresholds, recipients, and feature flags are configuration—not business logic.
- Cache stable enrichment by evidence/version and refresh policy.
- No destructive or irreversible migration without explicit approval and a recovery/forward-repair plan.

## Compliance and security

- Assess each source before live access. Respect terms, robots.txt, authentication, rate limits, copyright, privacy, and applicable law.
- Never bypass CAPTCHAs, access controls, authentication, anti-bot measures, or technical restrictions. Support lawful API/feed/import/manual alternatives.
- Never commit credentials, tokens, personal recipients, cookies, or private data. Use safe placeholders and secret references.
- State-changing notification links require scoped, expiring, replay-protected tokens and a confirmation POST; GET must not mutate state.
- Minimize and redact sensitive or copyrighted content in fixtures, logs, notifications, and errors.

## Tests and documentation

- Update tests with parser, normalization, identity, merge/provenance, event, evaluation, notification, migration, or security changes.
- Parser changes use permitted representative fixtures; identity tests prioritize false-merge prevention, 号棟, and conflicting 建築確認番号.
- Tests distinguish unknown, absent, verified negative, conflicting, and verified values; use deterministic clocks/IDs for historical behavior.
- Keep run history sufficient to prove discovery, tracking, parsing, enrichment, and notification health.
- Update architecture, data-model, operations, configuration, and roadmap documentation in the same change when applicable.
