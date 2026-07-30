# Homesearch

Homesearch is a personal system for discovering, normalizing, enriching, evaluating, tracking, and reporting Japanese residential property listings. Product and architecture documentation starts at [`docs/README.md`](docs/README.md).

## Current implementation scope

Phase 1 currently provides the Python project/toolchain bootstrap, the versioned configuration foundation, the synchronous PostgreSQL connection boundary, a local PostgreSQL 18.4 Docker Compose service, and a migration-backed initial persistence schema. Safe TOML configuration is validated before use, layered through explicit profile/local selection, and identified by a deterministic digest that excludes resolved secret values. The tracked defaults define one explicit non-secret UUIDv7 user plus empty source and search registries; no source or search is configured, and no source is authorized for access.

SQLAlchemy mappings, repositories/transactions, application workflows, CI, authentication, destinations, source adapters, polling/scheduler behavior, tracking schedules, external providers, real credentials, and deployment remain intentionally deferred to later independently reviewed tasks.

## Local setup

Install [uv](https://docs.astral.sh/uv/getting-started/installation/). The project pins CPython 3.14.6 in `.python-version`; uv can install that interpreter when it is not already available.

```shell
uv sync --locked
```

The tracked defaults load without secrets:

```shell
uv run python -c "from homesearch.config import load_configuration; print(load_configuration().digest)"
```

Configuration precedence is:

1. `config/defaults.toml`;
2. an optional versioned profile selected with `HOMESEARCH_PROFILE_PATH`;
3. an optional ignored `config/local.toml` selected with `HOMESEARCH_LOCAL_CONFIG_PATH`;
4. the allowlisted `HOMESEARCH_LOG_LEVEL` and `HOMESEARCH_LOG_FORMAT` overrides; and
5. external values for named secret references.

`.env.example` documents the complete current environment allowlist. Copy it to the ignored `.env` only when local overrides are needed. `config/profiles/example.toml` demonstrates a required `database-url` reference; it cannot load until `HOMESEARCH_DATABASE_URL` is supplied locally. No database connection is made by the configuration loader.

Calling `load_configuration()` with no argument reads that allowlist from the process environment and optional `.env`. Passing an `OperationalSettings` object instead treats it as the complete explicit input and does not consult ambient environment or dotenv values.

The database adapter resolves `HOMESEARCH_DATABASE_URL` only when the active versioned configuration declares the corresponding secret reference. It requires an explicit `postgresql+psycopg://.../<database>` URL and constructs a synchronous SQLAlchemy engine lazily. Engine construction does not contact PostgreSQL; connection and transaction ownership will be introduced with the migration and persistence workflows that require them.

### Local PostgreSQL

The default local database workflow requires Docker with Compose v2. `compose.yaml` runs only PostgreSQL, pinned to the current accepted PostgreSQL 18 minor. It publishes PostgreSQL on loopback only and stores its PostgreSQL 18 data root in the named `homesearch-postgres-18-data` volume.

Create an ignored, local-only password before the first start:

```shell
mkdir -p .secrets
openssl rand -hex 24 > .secrets/postgres-password
chmod 600 .secrets/postgres-password
```

Start PostgreSQL and wait for its health check:

```shell
docker compose up --detach --wait postgres
docker compose ps postgres
docker compose exec -T postgres \
  psql --username homesearch --dbname homesearch --command 'SHOW server_version;'
```

To use the existing application connection boundary, select the example profile and supply a URL containing the same local-only password. Keep the URL in the process environment or ignored `.env`; never add it to tracked TOML:

```shell
export HOMESEARCH_PROFILE_PATH=config/profiles/example.toml
export HOMESEARCH_DATABASE_URL="postgresql+psycopg://homesearch:$(tr -d '\n' < .secrets/postgres-password)@127.0.0.1:5432/homesearch"
```

Set `HOMESEARCH_POSTGRES_PORT` before Compose commands if host port `5432` is unavailable, and use the same port in `HOMESEARCH_DATABASE_URL`.

Stop the service without deleting data:

```shell
docker compose stop postgres
```

`docker compose down` removes the container and project network but retains `homesearch-postgres-18-data`; the next `up` reuses it. The named volume is local persistence, not a backup. Only when all local data is intentionally disposable, `docker compose down --volumes` removes this project’s named volume and makes the next start initialize an empty database.

### Schema migrations

`alembic.ini` contains migration-script settings only; it never contains a database URL. When a revision exists, the Alembic environment uses the same configuration loader and named database secret as the application. Offline `--sql` commands resolve the validated PostgreSQL dialect URL without connecting. Online commands create a connection only through the existing synchronous database engine boundary.

The first revision creates only the Phase 1 persistence anchors:

- immutable safe configuration snapshots identified by configuration ID/version and digest;
- explicit user and source identities;
- separate property and source-owned listing identities; and
- a user-owned top-level run ledger tied to the exact configuration snapshot and digest.

It intentionally does not seed the configured default user or add observations, raw objects, source runs, property/listing resolution links, repositories, or business workflows. Durable entity IDs use native PostgreSQL `uuid` columns without database defaults so the application remains the explicit UUIDv7 owner.

Inspect the revision history without a database:

```shell
uv run alembic heads
uv run alembic history
```

With the example database profile and secret configured, migrate the local database and report its version:

```shell
uv run alembic upgrade head
uv run alembic current
```

`uv run alembic downgrade base` removes all six Phase 1 application tables and their data. Use it only against an explicitly disposable local/test database. Alembic retains its empty version table at `base`; no pre-existing database objects are removed.

The PostgreSQL integration suite derives disposable database names from a separately supplied server URL, migrates each database from empty to `head`, downgrades to `base`, and drops only those generated databases:

```shell
export HOMESEARCH_TEST_DATABASE_URL="$HOMESEARCH_DATABASE_URL"
uv run pytest -m postgresql tests/adapters/database/test_initial_schema.py
```

The role in `HOMESEARCH_TEST_DATABASE_URL` must be allowed to create and drop databases; the existing Compose `homesearch` role has that local-only capability. The URL still passes through the application configuration and engine boundary and is never read from a tracked file. Every future schema change must add a reviewed revision with a safe, truthful downgrade or an explicit forward-repair plan.

`user_scope` is version-controlled, contains no personal profile or destination data, and currently permits exactly one user. Its explicit `default_user_id` prevents later persistence and command code from relying on a hidden process-wide singleton.

Configuration schema version 3 added the versioned `source_registry` boundary. Each source has an opaque UUIDv7 identity plus a stable readable key; its policy can record lifecycle, access-assessment status, neutral capabilities, bounded request settings, and capture/retention/storage behavior.

Schema version 4 adds the versioned `search_registry` boundary. Each search has its own UUIDv7 identity, stable key, version/effective time, configured user, source references, administrative areas, JPY price/negotiation criteria, residential property types and new/used conditions, discovery interval, and per-run result limit. Searches reference source UUIDs rather than source names. An enabled search is valid only when its user exists and every referenced source is enabled, approved, and discovery-capable.

Only a versioned profile can replace the source or search registry; ignored local TOML and environment values cannot mutate either. The repository defaults keep both registries empty. These models validate policy but never grant Gate B approval, execute an adapter, poll a source, or schedule work. Earlier schema versions are rejected until explicitly updated rather than silently migrated.

Run the local quality checks:

```shell
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run pytest
```

The environment is project-local and disposable. Do not commit `.venv`, local configuration, secrets, generated artifacts, or runtime data.
