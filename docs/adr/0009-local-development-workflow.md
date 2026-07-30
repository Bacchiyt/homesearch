# ADR 0009: Local macOS Development Workflow

## Status

Proposed

## Context

The primary contributor environment is macOS. The workflow should be reproducible, close to production database semantics, and understandable without an early hosted service. Docker Compose is useful only if it materially reduces PostgreSQL version/setup drift; the Python toolchain does not need to run inside a container.

## Decision

If Gate A approves ADRs 0001 and 0002:

- install/select ADR 0001's latest supported Python 3.14.x patch and manage the selected patch with uv;
- run Python commands from the host through `uv run`;
- use Docker Compose for a local PostgreSQL 18 service at ADR 0002's current supported minor by default, with the image version deliberately managed because it isolates dependencies and matches CI/production semantics;
- store PostgreSQL data in a named container volume outside the repository;
- support a native macOS installation at a compatible supported PostgreSQL 18 minor as an equivalent alternative through the same `DATABASE_URL`;
- do not require a local object-store emulator in Phase 1; later synthetic raw objects use the ignored filesystem adapter;
- keep all credentials, database URLs containing passwords, raw objects, exports, and dumps outside Git; and
- keep setup/start/stop/migrate/test commands behind documented project tasks once Phase 1 is authorized.

The conceptual setup flow is:

1. clone and select the approved branch/revision;
2. install uv and sync the committed lockfile;
3. copy only placeholder examples into ignored local configuration, then supply local secret values;
4. start PostgreSQL through Compose or a compatible native service;
5. apply Alembic migrations to an empty development database;
6. run Ruff, mypy, and pytest, including PostgreSQL integration tests; and
7. stop services without deleting the named data volume.

Developers may create a manual `pg_dump` in an ignored, access-controlled location before a risky local experiment. Once local data becomes valuable, document automated backup/restore or move it to an approved durable environment; the named volume alone is not a backup.

This ADR is conceptual. It does not authorize or add a Compose file, project skeleton, database, credentials, or infrastructure.

## Alternatives considered

- **Native PostgreSQL only:** integrates naturally with macOS but makes versioning, cleanup, and contributor parity less deterministic.
- **Dockerize the entire development environment:** maximizes parity but slows inner-loop Python tooling and adds container complexity without demonstrated benefit.
- **SQLite local development:** simpler startup but conflicts with the recommended one-engine strategy and can hide database semantics.
- **Hosted development database:** avoids a local service but creates network, secret, cost, availability, and privacy dependencies before Gate D.
- **No Compose support:** leaves the main source of local setup drift unresolved despite PostgreSQL being the proposed foundation.

## Consequences

- Docker Desktop or another Compose-compatible runtime is the default additional prerequisite.
- Native PostgreSQL remains available for contributors who prefer it.
- Python editing/tests stay fast on the host while database behavior stays representative.
- Exact commands and files are a Phase 1 deliverable after approval.

## Risks/trade-offs

- Container runtimes consume disk/memory and licensing/installation constraints can change.
- Native and Compose networking defaults can differ; `DATABASE_URL` and setup tests must make the distinction explicit.
- Named volumes can outlive schema experiments and cause confusing state; reset procedures must identify the exact project volume and be opt-in.
- Apple Silicon wheel/container compatibility needs Phase 1 validation.

## Follow-up/validation

- Gate A approves the default and native fallback.
- In Phase 1, verify a clean macOS setup with the managed Python 3.14.x patch and current supported PostgreSQL 18 minor, empty migration, test run, and non-destructive stop/restart.
- Document a precise, recoverable local reset and restore check without broad deletion commands.
- Reassess Docker only if contributor burden outweighs database parity.

## Date

2026-07-30
