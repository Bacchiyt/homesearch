# ADR 0004: Versioned Configuration and Secret Boundaries

## Status

Proposed

## Context

Search areas, source policies, schedules, evaluation thresholds, recipients, and feature flags must be configuration rather than business logic. Safe configuration needs reviewable diffs and stable versions, while secrets and personal destinations must never enter Git. Arbitrary environment-variable overlays make a nested personal configuration difficult to audit and reproduce.

## Decision

If Gate A approves this ADR:

- use TOML for version-controlled, non-secret configuration and profiles;
- parse TOML with Python's [`tomllib`](https://docs.python.org/3.14/library/tomllib.html) and validate the resulting data with Pydantic models;
- use [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) for a narrow operational settings layer and secret references;
- require a top-level configuration `schema_version`, stable IDs for independently versioned objects, and explicit effective/version metadata;
- compute and persist a canonical configuration digest plus the relevant object versions on every run;
- fail before work starts on unknown fields, invalid ranges/intervals, missing references, unsupported capabilities, or unresolved required secret references;
- provide safe example files containing placeholders only; and
- redact secret values and personal destinations from logs, errors, snapshots, and exports.

Precedence is explicit:

1. versioned safe defaults;
2. an explicitly selected versioned TOML profile;
3. an optional ignored local TOML file for non-secret developer settings;
4. a small allowlist of environment overrides; and
5. secrets resolved from environment variables or an approved secret provider.

Environment overrides are limited to deployment concerns such as configuration path/profile, database URL, log level/format, and named secret references. They do not provide an unbounded mechanism to mutate search rules or evaluation policy. `.env` may be used locally only as an ignored convenience; it is never authoritative or committed.

TOML documents non-secret identity and policy. A recipient is represented by destination ID plus secret reference, not an email address in tracked TOML. Configuration migrations are explicit transforms or operator edits; the application never silently guesses a new schema.

## Alternatives considered

- **YAML:** expressive and common, but implicit typing, tags, and parser variation add risk for configuration that should be small and strict.
- **JSON:** unambiguous and ubiquitous, but less friendly for comments and sustained hand editing.
- **Environment variables for everything:** deployment-friendly but poor for nested/versioned search and policy definitions, audit, and reproducibility.
- **Database-only configuration:** enables runtime editing but creates bootstrapping, review, and recovery complexity. Audited runtime records may be added later for approved mutable controls.
- **Pydantic models for domain entities:** rejected; validation at an input boundary must not couple the core domain to a serialization framework.

## Consequences

- Safe configuration changes are reviewable and reproducible.
- Operators must manage an explicit profile and separate secret values.
- TOML writing/upgrading needs an explicit library or controlled transform if automated rewriting is later required; `tomllib` only reads.
- A restricted override list is less flexible than arbitrary environment nesting but substantially easier to audit.

## Risks/trade-offs

- Configuration object versions and the top-level schema version can be confused; naming and validation must distinguish them.
- A digest is useful only if canonicalization excludes secrets and is deterministic.
- Local ignored files can become undocumented dependencies unless setup checks report their effective source.
- Secret references can still leak metadata; destination IDs and error messages require redaction review.

## Follow-up/validation

- Gate A approves TOML, validation, precedence, and the environment allowlist principle.
- Phase 1 defines the first schema and tests valid/invalid configurations, unknown fields, override precedence, digest stability, missing secrets, and redaction.
- Before runtime editing, decide authorization, audit history, and reconciliation with version-controlled policy.
- Before production, select a secret provider and recovery procedure under Gate D.

## Date

2026-07-30
