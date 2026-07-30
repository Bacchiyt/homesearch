# ADR 0010: Phase 1 Continuous Integration

## Status

Accepted

## Context

Phase 1 must make the approved foundation reproducible without live sources, external APIs, production credentials, or infrastructure. Because PostgreSQL is the accepted database from the first migration, SQLite-only CI is insufficient. CI should catch formatting, typing, unit, migration, integration, and secret-safety failures while remaining low cost.

## Decision

Gate A accepts GitHub Actions for Phase 1 with:

- a pinned Ubuntu runner image and a deliberately managed exact CPython patch at the latest supported 3.14.x release selected under ADR 0001;
- uv installed through a pinned, verified mechanism;
- `uv sync --locked` against the committed lockfile;
- `ruff check` and `ruff format --check`;
- mypy for the configured source modules;
- pytest for unit, contract, and PostgreSQL integration tests;
- a PostgreSQL service container deliberately pinned to ADR 0002's current supported PostgreSQL 18 minor and aligned with the managed local/CI target;
- Alembic upgrade from an empty database to `head`, application schema-version smoke check, and `alembic check` for unrepresented model changes where reliable;
- a second migration/transaction test path when needed to expose upgrade or concurrency behavior;
- Gitleaks, pinned to a reviewed version/digest, for repository secret scanning, plus platform-native protection when available; and
- dependency caches keyed by platform, exact Python patch, and `uv.lock`, never containing secrets or database data.

CI contains no live source access, recipient, external provider call, long-lived credential, production endpoint, or deployment step. Representative source tests use permitted/synthetic fixtures only. PostgreSQL service credentials are ephemeral non-production test values.

Required checks become branch-protection candidates after the workflow exists and is stable. This ADR does not create an Actions workflow; that is Phase 1 implementation after approval.

## Alternatives considered

- **Local checks only:** no hosted usage, but insufficient protection for a long-lived repository.
- **SQLite in CI:** faster startup, but fails to validate the selected production semantics and migration path.
- **Matrix across PostgreSQL majors:** useful for a library, but unnecessary when the application pins one supported major.
- **Pyright plus mypy:** redundant and potentially conflicting for the early project.
- **Hosted database in CI:** adds secrets, network dependence, cleanup, and cost when an ephemeral service container is sufficient.
- **Platform secret scanning only:** useful when enabled, but repository/plan availability can vary; a pinned scanner makes the gate explicit.

## Consequences

- Pull requests receive deterministic quality feedback before merge.
- PostgreSQL startup increases CI duration but eliminates a separate compatibility lane.
- Tool versions and runner assumptions require periodic maintenance.
- Supported Python 3.14.x patches and PostgreSQL 18 minors must be advanced intentionally rather than drifting or remaining stale.
- Migration and secret-scan checks become part of the definition of done.

## Risks/trade-offs

- Pinned third-party actions/tools need supply-chain review and update cadence.
- Gitleaks can report false positives; suppressions must be narrow, reviewed, and never hide real secrets.
- `alembic check` does not prove hand-written data migrations or production lock behavior.
- CI concurrency tests can be flaky unless synchronization is deterministic.

## Follow-up/validation

- Gate A accepted the CI gates and PostgreSQL requirement.
- Phase 1 adds the workflow, pins external actions by full commit SHA where practical, and documents local equivalents.
- Verify a clean checkout passes with no repository secret.
- Treat Python 3.14.x patch and PostgreSQL 18 minor upgrades as managed maintenance changes that must pass the full workflow; they do not require a new ADR unless they materially change an architectural decision.
- Add migration, fixture, security, and provider-fake checks in the roadmap phase that introduces each concern.

## Date

2026-07-30
