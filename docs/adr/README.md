# Architecture Decision Records

ADRs capture durable technical decisions without moving implementation detail into `AGENTS.md`. Read only the ADRs relevant to the task.

## Status

Gate A passed on 2026-07-30. The product owner explicitly accepted ADRs 0001–0011 after reviewing the recommendations merged in [PR #2](https://github.com/Bacchiyt/homesearch/pull/2). Phase 1 is authorized to implement these decisions within its roadmap scope.

This status change records the ADR lifecycle transition from `Proposed` to `Accepted`; it does not authorize live source access, external services, credentials, infrastructure, deployment, or later phases. Later decision changes must supersede rather than rewrite accepted history.

## Gate A accepted decision set

| ADR | Scope | Accepted decision |
|---|---|---|
| [0001](0001-python-runtime-and-toolchain.md) | Runtime, packaging, quality tools, HTTP, parsing, validation, logging | Python 3.14, uv, Ruff, mypy, pytest, HTTPX, lxml, Pydantic Settings; synchronous first |
| [0002](0002-database-strategy.md) | Local, MVP, production database, migration path | PostgreSQL 18 from Phase 1 onward; SQLite only for bounded disposable uses |
| [0003](0003-database-access-and-migrations.md) | Data access, migrations, IDs, time | SQLAlchemy 2, psycopg 3, Alembic, UUIDv7, UTC-aware instants |
| [0004](0004-configuration.md) | Safe configuration, overrides, secrets | Versioned TOML validated by Pydantic; narrow environment overrides and secret references |
| [0005](0005-scheduling-and-durable-jobs.md) | Scheduler, durable jobs, retry semantics | No Phase 1 scheduler; later platform trigger plus PostgreSQL-backed jobs |
| [0006](0006-web-and-api.md) | Optional web/API surface | No early server; FastAPI/Uvicorn when secure actions or operational API justify it |
| [0007](0007-initial-user-scope.md) | Single-user scope and future compatibility | One logical user with internal `user_id`; no early authentication |
| [0008](0008-raw-observation-storage.md) | Raw evidence, blobs, retention | Phase 1 prepares boundaries; Phase 2 stores metadata and policy-permitted portable blobs |
| [0009](0009-local-development-workflow.md) | macOS contributor workflow | uv plus Docker Compose PostgreSQL by default; native PostgreSQL supported |
| [0010](0010-continuous-integration.md) | Phase 1 quality gates | GitHub Actions with locked dependencies, PostgreSQL integration, and secret scanning |
| [0011](0011-cost-model.md) | Architecture-level cost posture | Local-first, one relational service in production, defer variable-cost providers |

## Decision dependencies

- ADR 0002 controls the target exercised by ADRs 0003, 0009, and 0010.
- ADR 0001 supplies the runtime assumed by ADRs 0003, 0004, 0006, and 0010.
- ADR 0005 deliberately defers the durable job engine until Phase 6.
- ADRs 0006, 0008, and 0011 defer provider/resource commitments to their roadmap gates.

## Lightweight ADR lifecycle

1. `Proposed` — recommendation is reviewable but not authorized.
2. `Accepted` — product owner explicitly approved it.
3. `Superseded` — a later ADR replaces it and links both directions.
4. `Rejected` — retained for historical context when useful.
