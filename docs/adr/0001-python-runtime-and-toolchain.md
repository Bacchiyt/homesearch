# ADR 0001: Python Runtime and Toolchain

## Status

Proposed

## Context

Homesearch needs strong Japanese text/HTML processing, typed domain boundaries, deterministic tests, and a low-friction macOS/CI workflow. Its early workload is bounded batch processing, not a high-concurrency public server. Selecting asynchronous I/O everywhere would add transaction, test, and lifecycle complexity before measurements justify it.

[Python 3.14](https://devguide.python.org/versions/) is the current stable feature release and includes [standard-library UUIDv7 generation](https://docs.python.org/3.14/library/uuid.html). The stack must be reproducible and must not make source adapters or domain logic depend on a global event loop.

## Decision

If Gate A approves this ADR:

- use the latest supported CPython 3.14.x patch release available when Phase 1 begins, manage the selected patch through uv, and declare the approved 3.14 series in `requires-python`;
- use a single `pyproject.toml`, committed `uv.lock`, and [uv projects](https://docs.astral.sh/uv/guides/projects/) for Python installation, dependency locking, environments, and command execution;
- use a `src/homesearch/` package layout and a separate `tests/` tree;
- use Ruff for formatting, import ordering, and linting;
- use mypy as the sole static type checker, starting strict for domain/application modules and tightening adapter exceptions explicitly;
- use pytest with deterministic clocks/IDs and test doubles at provider boundaries;
- use HTTPX's synchronous `Client`, with scoped connection reuse, explicit timeouts, and adapter-owned request policy;
- use `lxml.html` as the primary permitted-HTML parser; keep fallback parsing source-specific and evidence-tested rather than globally magical;
- add no browser-automation dependency at Gate A; assess a browser adapter only for a Gate B-approved source whose lawful access path requires rendered interaction;
- use Pydantic and Pydantic Settings at external/configuration boundaries, not as core domain entities; and
- use standard-library `logging` with structured JSON output and correlation fields. Keep formatting behind the observability adapter so a logging library can be added without changing domain code.

Application services, database access, and source adapters are synchronous by default. A measured adapter may use asynchronous I/O internally later, but it must expose the same typed application port and cannot force the domain or persistence layer to become async. A future FastAPI surface may run synchronous application services through its supported execution model.

Dependency ranges belong in `pyproject.toml`; exact transitive versions belong in `uv.lock`. Phase 1 validates that selected releases support Python 3.14 before implementation proceeds.

Python 3.14 is the architecture-level runtime baseline; an early 3.14 patch is not a permanent target. Local setup, CI, and deployment configuration use deliberately managed exact patch versions where reproducibility requires them. A supported patch upgrade within the approved 3.14 series does not require a new ADR, but it must update the managed pins intentionally and pass the full CI suite before adoption. Changing the approved Python feature series requires architecture review.

## Alternatives considered

- **Python 3.13:** mature and supported, but provides a shorter support runway and lacks the standard-library UUIDv7 addition used by ADR 0003.
- **Node.js/TypeScript:** strong web/async tooling, but less aligned with the anticipated data, geospatial, and Python parsing ecosystem.
- **Async-first Python:** valuable for large concurrent network workloads, but unnecessary for the initial batch scale and more complex across database sessions, tests, and retries.
- **Pyright instead of mypy:** fast and capable, but a second checker is not justified; mypy has broad Python-library conventions and is sufficient.
- **Requests or aiohttp instead of HTTPX:** Requests is simple but lacks a paired async path; aiohttp would make async foundational. HTTPX preserves a later async option behind the adapter.
- **Beautiful Soup as the primary parser:** tolerant and approachable, but lxml provides direct tree/XPath/CSS-oriented parsing with good performance. It can be used as an explicitly tested fallback if a source needs it.
- **Browser automation in the baseline:** rejected because no live source or rendered-browser requirement is approved, and browser tooling adds significant dependency, security, and operational surface.

## Consequences

- Local and CI environments share one lockfile and command path.
- Synchronous control flow keeps transactions and retries easier to reason about at personal-project scale.
- Native dependencies used by lxml must have compatible wheels or documented macOS/CI build support.
- Async performance is not available automatically; adoption requires evidence and an adapter-scoped design.
- Python 3.14 narrows dependency choices until the ecosystem catches up, so the Phase 1 compatibility validation is blocking.
- Managed patch pins require routine updates as supported Python 3.14.x releases replace older patches.

## Risks/trade-offs

- A newly released Python line can expose package incompatibilities.
- CPU-heavy parsing must not run unbounded inside a future web request.
- A hand-rolled JSON formatter can drift; logs need contract tests for required fields and redaction.
- Sync-first can become inefficient if future lawful source/provider concurrency is much higher than expected.

## Follow-up/validation

- At Gate A, approve the runtime and sync-first boundary.
- In Phase 1, select the latest supported Python 3.14.x patch, record the managed local/CI pin, and resolve a compatible dependency set.
- Prove `uv sync --locked`, Ruff, mypy, and pytest on macOS and CI.
- Require every later 3.14.x patch upgrade to pass the same CI gates before updating local or deployment pins.
- Test HTTP timeout/connection lifecycle and structured-log redaction.
- Reconsider async only after measured concurrency, latency, or hosting constraints show a material benefit.

## Date

2026-07-30
