# ADR 0006: Optional Web and API Surface

## Status

Accepted

## Context

The early system is a local, command-driven personal workflow. It does not need an always-on web process to define configuration, ingest synthetic observations, or build the domain. A later HTTPS surface is likely useful for health/status, manual review, and notification actions, but public exposure introduces authentication, token, deployment, availability, and cost obligations.

## Decision

Gate A accepts the following decision:

- do not add a web framework dependency, server entry point, always-on process, or public endpoint in Phase 1;
- keep application use cases callable through typed framework-neutral ports;
- designate [FastAPI](https://fastapi.tiangolo.com/) with Uvicorn as the default future HTTP stack, to be added only in the phase that first needs an approved HTTP surface;
- introduce the first web surface no earlier than Phase 7 unless an earlier roadmap gate explicitly approves a concrete operational need;
- keep request/response models in the API adapter and map them to application commands/results; and
- run synchronous application/database services consistently with ADRs 0001 and 0003. Async-only provider work remains behind an adapter rather than leaking through the domain.

The initial future surface is intentionally narrow:

- shallow process health;
- detailed status only with appropriate protection;
- notification action landing via non-mutating GET;
- explicit confirmation POST with scoped, expiring, replay-protected token; and
- no general public property API or account system.

Gate C must approve outbound email/action design, and Gate D must approve public hosting, secrets, monitoring, backup, and cost before deployment.

## Alternatives considered

- **FastAPI in Phase 1:** provides typed routes and generated schemas but creates an unused server/dependency and invites premature API design.
- **Starlette:** smaller and flexible, but FastAPI supplies validation and API documentation useful once a typed API is actually needed.
- **Flask:** simple and mature, but requires more choices for typed validation and OpenAPI.
- **Django:** strong integrated admin/auth/ORM, but too broad for a modular command-first system and conflicts with the selected persistence boundary.
- **Serverless function for action links:** potentially low idle cost, but host limits, database connections, token flow, and regional availability need Gate D research.
- **Email reply or no action endpoint:** lower hosting burden but weaker secure interaction and automation; it remains a fallback if hosting is not approved.

## Consequences

- Phase 1 stays local and has no web attack surface or always-on cost.
- Application ports must be usable by both CLI and a later HTTP adapter.
- FastAPI is a future default, not an installed dependency or deployed service.
- Secure actions cannot ship until the endpoint and its threat model are implemented and approved.

## Risks/trade-offs

- Deferring the API can reveal mapping gaps later; command/result contracts need clear ownership now.
- FastAPI's async capabilities could tempt an inconsistent second execution model.
- A public action endpoint adds availability and security obligations disproportionate to a personal tool.
- Health endpoints can leak operational data unless shallow and protected appropriately.

## Follow-up/validation

- Gate A accepted the deferral and designated future framework.
- At Phase 7, validate GET safety, POST confirmation, token expiry/tamper/replay, redaction, CSRF/referrer behavior, and synchronous database lifecycle.
- At Gate D, compare a small always-on host with serverless/on-demand options using current regional capability and cost.

## Date

2026-07-30
