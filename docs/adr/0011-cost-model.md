# ADR 0011: Architecture-Level Cost Model

## Status

Accepted

## Context

Homesearch should remain a low-cost personal system. Current vendor prices, free tiers, quotas, exchange rates, and regional availability are volatile and should not be invented in a foundation ADR. The durable decision is which architectural components create recurring cost and when a gate must measure them.

## Decision

Gate A accepts the following decision:

- optimize for local development and one modular deployment rather than multiple always-on services;
- use open-source local tooling and a local PostgreSQL container during Phase 1;
- rely on repository-included CI allowance only after checking the owner's current GitHub plan; set limits and avoid uncontrolled scheduled CI;
- expect the production relational database, backups, and storage to be the first meaningful recurring infrastructure cost;
- add no always-on web service until secure actions/operational access justify it;
- use low-volume transactional email only after Gate C provider/cost approval;
- treat geocoding, POI/business-hours, routing/traffic, and media analysis as later variable-cost capabilities with caching, quotas, and per-run budgets;
- store raw objects only when policy/value justifies retention cost; and
- do not add a broker, Kubernetes, multiple services, or high-availability topology without measured need.

Architecture-level cost expectations:

| Component | Earliest stage | Cost posture and control |
|---|---|---|
| macOS Python/uv/tools | Phase 1 | No service fee; contributor machine time/storage |
| Local PostgreSQL/Compose | Phase 1 | No hosted fee; local CPU/disk |
| GitHub Actions | Phase 1 | May fit included allowance; bound run frequency/cache size |
| Production PostgreSQL/backups | Gate D | Likely base recurring cost; compare region, storage, backup, sleep/availability, egress |
| Web/action endpoint | Phase 7/Gate D | Avoid always-on until required; compare on-demand versus small service |
| Transactional email | Phase 7/Gate C | Low volume expected; cap sends/retries and monitor rejection |
| Raw object storage | Phase 2 local, production later | Default to selective capture/TTL; monitor bytes, requests, egress |
| Geocoding/hazards | Phase 8/10 | Prefer lawful official/open data where adequate; cache by evidence/version |
| POI/routes/traffic | Phase 9/11 | Potentially largest request-based cost; batch, cache, quota, degrade to unknown |
| Image/layout analysis | Phase 12 | Opt-in/budgeted; avoid repeated analysis of unchanged hashes |
| Monitoring | Gate D | Start with run ledger/exportable logs; add paid service only for clear response value |

The near-term architecture can be close to zero incremental service cost while local and within included CI usage. That is a hypothesis, not a vendor-price commitment. Before Gates C and D, record expected monthly calls, storage growth, retention, data transfer, base fees, taxes/currency, budget ceiling, and shutdown/degradation behavior using then-current provider information.

## Alternatives considered

- **Choose free-tier vendors now:** creates premature coupling and relies on unstable terms.
- **Self-host every component:** can reduce invoices but increases operations, availability, backup, security, and electricity/time costs.
- **Managed services for every capability:** reduces some operations but creates several base fees and provider dependencies before value is proven.
- **Build a detailed multi-year forecast now:** false precision without source counts, retention volume, provider selections, or a user budget.

## Consequences

- Gate A acceptance approves the architecture without approving a vendor or spend.
- Every outbound/provider ADR must include a measured budget and failure/degradation policy.
- Caching and content hashes become cost controls as well as performance features.
- A production database may dominate early recurring cost even at low workload.

## Risks/trade-offs

- “Near zero” can hide contributor time, laptop resources, domain/sender setup, and backup responsibility.
- Free/included allowances may change or be unavailable for a private repository.
- Low-cost hosts may sleep, restrict background work/extensions, or provide weak recovery.
- Over-aggressive caching/retention limits can reduce freshness or replay evidence.

## Follow-up/validation

- Gate A accepted the cost-control principles, not a price or provider.
- Before Gate C, set a monthly variable-provider budget and call/storage estimates.
- Before Gate D, compare current Japan-region database, web, backup, storage, email, and monitoring costs and define an owner-approved monthly ceiling.
- Add per-provider usage metrics, quotas, and safe disable switches when each integration is introduced.

## Date

2026-07-30
