# ADR 0002: Database Strategy from Local Development to Production

## Status

Proposed

## Context

Gate A must decide the local-development database, early/MVP persistence, production relational target, and tested path between them. Homesearch will preserve immutable observations, versioned projections, provenance, leases, idempotency constraints, JSON/time values, and potentially spatial data. Differences in concurrency, types, constraints, transactions, and geospatial behavior cannot be hidden by a convenient test store.

PostgreSQL/PostGIS is the desired long-term direction, but no database was selected during Phase 0. Database files, dumps, credentials, and personal data must never be committed.

## Decision

Recommend **Option B: PostgreSQL from Phase 1 for local development, early/MVP persistence, and production**, subject to Gate A approval.

- Use PostgreSQL 18.x as the Phase 1 implementation target and select the [current supported minor release](https://www.postgresql.org/support/versioning/) when implementation begins. Local, CI, and deployment configuration deliberately manage the selected version; do not intentionally remain on an older supported-major minor or float across majors implicitly.
- Use the same schema and Alembic migration history in local, CI, MVP, and production environments.
- Run PostgreSQL locally in a named Docker volume by default, with a compatible native macOS installation as an alternative.
- Require PostgreSQL integration tests from the first migration. Unit tests may use in-memory fakes where database behavior is irrelevant.
- Keep PostGIS optional and disabled until a later ADR proves material value. Spatial use is isolated in persistence/provider adapters and migrations.
- Move environments with migrations plus PostgreSQL-native logical backup/restore or controlled data copy; verify schema version, row/reference counts, and checksums before cutover.
- Keep connection strings in environment/secret storage. Keep local volumes outside Git and dumps/exports in ignored, access-controlled locations.

PostgreSQL 18 is an implementation target, not a permanent architectural constraint. A future supported PostgreSQL major can replace it after compatibility validation, migration rehearsal, backup/restore testing, and rollout/rollback or forward-repair planning. Update or supersede this ADR when a major change materially affects architecture, operations, extensions, or portability. Advancing to a current minor within the approved PostgreSQL 18 series is routine maintenance, but still requires migration/integration CI and applicable restore validation.

SQLite is permitted only for isolated, bounded uses that do not become application persistence:

- an isolated test/tool database lives in an OS temporary directory or repo-ignored `var/sqlite/`, never in a tracked path;
- test databases last one test run; temporary tool/prototype databases last only the documented task and contain no live-source history;
- exports follow their explicit retention policy and are not a running database;
- disposable uses have no backup requirement; a valuable tool artifact must be exported with a checksum to an ignored/approved location before disposal;
- no SQLite prototype may cross into Phase 2 ingestion or become an operational source of record without a new ADR; and
- every persistence behavior involving transactions, constraints, JSON/time, concurrency, leasing, migrations, or geospatial semantics is tested on PostgreSQL.

### Options compared

| Criterion | A. SQLite local/MVP, migrate later | B. PostgreSQL throughout | C. SQLite local, PostgreSQL MVP/production |
|---|---|---|---|
| Local setup | Simplest executable/file | Container or native service | Simplest until integration |
| Early operating cost | Near zero | Near zero locally | Near zero locally |
| CI | Fast SQLite plus mandatory PG compatibility suite | One authoritative PG service | Both engines or risk gaps |
| Type/constraint/transaction fidelity | Lowest | Highest | Local behavior can diverge |
| Concurrency/job leasing fidelity | Weak | Production-equivalent | Requires separate PG validation |
| JSON/time semantics | Migration/semantic risk | Consistent | Dual-engine complexity |
| Backup | File copy needs write-safe procedure | `pg_dump`/restore and host backups | Two procedures |
| PostGIS path | Later schema/data migration | Extension can be added later | Available from MVP |
| Migration risk | Highest after history accumulates | Lowest; host moves remain | Moderate before MVP |
| Ongoing complexity | One simple engine, then migration project | One engine and local service | Two supported modes |

## Alternatives considered

- **Option A:** rejected as the recommendation because it defers operational setup by creating a later data/semantic migration after valuable history may exist.
- **Option C:** rejected as the recommendation because dual-engine local/CI behavior either doubles support work or lets PostgreSQL-only failures arrive late.
- **Managed PostgreSQL from day one:** not required for local/Phase 1 work and would create an external resource and recurring commitment before Gate D.
- **SQLite prohibited everywhere:** rejected because it remains useful for truly disposable tests, tools, prototypes, and exports when no PostgreSQL behavior is being asserted.

## Consequences

- Developers incur a local PostgreSQL process/container requirement.
- The project avoids a deliberate database-engine migration between MVP and production.
- CI must run a PostgreSQL service and migrations.
- Production hosting remains a later provider/cost decision; this ADR selects engine strategy, not a vendor.
- PostgreSQL-specific optimizations are available but must remain isolated and justified.

## Risks/trade-offs

- Docker or a native database increases local setup and resource use.
- PostgreSQL 18 availability may lag on a future host; Gate D must verify host support and the current supported PostgreSQL 18 minor.
- Staying on an older minor increases exposure to fixed defects and security issues; managed version updates need an explicit maintenance cadence.
- A single-engine strategy can encourage accidental extension coupling; portability checks and explicit capability boundaries remain required.
- Logical restore/cutover still needs rehearsal even without an engine change.

## Follow-up/validation

- Gate A must explicitly select A, B, or C; this recommendation is not self-approving.
- In Phase 1, select the current supported PostgreSQL 18.x minor and prove empty-schema migration, upgrade, constraints, transaction behavior, UTC/JSON round trips, and restore into a fresh instance at that managed version.
- For a future PostgreSQL major, validate application/driver/extension compatibility and rehearse backup, restore, migration, and recovery before changing the approved target; update the ADR where the impact is material.
- Before MVP persistence becomes valuable, define local backup handling and production RPO/RTO.
- Before PostGIS, record a separate ADR with query/data portability and host implications.

## Date

2026-07-30
