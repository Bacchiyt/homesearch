# ADR 0007: Initial Single-User Scope

## Status

Proposed

## Context

Homesearch is initially a personal system for one operator and one logical recipient. Hard-coding a singleton into tracking, evaluation, and notification records would make later household or multi-user support a costly data migration. Full authentication, tenancy, roles, and account administration would be premature and would create a security surface before any public UI is approved.

## Decision

If Gate A approves:

- model one logical `User` with an opaque application-generated `user_id`;
- carry `user_id` on user-owned durable concepts when they are introduced, including tracking preferences, evaluation/profile selection, notification destinations, notifications, action tokens, and reports;
- use one configured default user in early command workflows rather than a globally implied singleton;
- keep non-secret user/profile metadata in versioned configuration or relational records as the phase requires;
- represent an email recipient as a stable `destination_id` plus a secret reference; never commit the address;
- resolve and validate the destination only when an approved outbound adapter runs, and redact it everywhere else; and
- do not implement login, password storage, sessions, OAuth, roles, tenancy administration, or public user endpoints until a public/multi-user use case is separately approved.

The early trust boundary is the local operator and deployment environment. Future action tokens are scoped to user/destination, property, action, and notification, but they are not a substitute for full authentication if a broader interface becomes public.

Shared source observations and canonical property facts remain global evidence. User preference, tracking, evaluation, recommendation, and delivery state remain user-scoped.

## Alternatives considered

- **No `User` entity or `user_id`:** simplest initially, but embeds singleton assumptions into durable rows and event/deduplication keys.
- **Full multi-user/auth from Phase 1:** future-proof in theory, but expands schema, threat model, UI, operations, and testing without an approved need.
- **Recipient email as user identity:** leaks personal data into relationships and cannot represent address changes or multiple destinations safely.
- **Tenant ID on every table:** excessive; raw observations and canonical facts are shared system evidence, not user-owned records.

## Consequences

- Some future tables carry a user foreign key even while only one user exists.
- Tests can prove that user-scoped state does not collide without implementing multi-user product behavior.
- Personal values remain outside tracked configuration and logs.
- A later authentication ADR can attach credentials/identities to the existing user without redefining evidence ownership.

## Risks/trade-offs

- A default-user shortcut could leak into code paths; application commands should receive resolved user context explicitly.
- UUIDs are identifiers, not authorization.
- Secret-provider availability and destination recovery remain deployment decisions.
- Multi-user policy, data isolation, deletion, and sharing are still undefined.

## Follow-up/validation

- Gate A approves the single logical user and initial ownership boundaries.
- Phase 1 defines only the user/config anchors needed by its approved schema; do not create auth.
- When tracking/evaluation/notification tables arrive, test user-scoped uniqueness and destination redaction.
- Before public access or a second user, write an authentication/authorization/privacy ADR and threat model.

## Date

2026-07-30
