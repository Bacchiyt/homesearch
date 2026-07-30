# Homesearch

Homesearch is a personal system for discovering, normalizing, enriching, evaluating, tracking, and reporting Japanese residential property listings. Product and architecture documentation starts at [`docs/README.md`](docs/README.md).

## Current implementation scope

Phase 1 currently provides the Python project/toolchain bootstrap and the versioned configuration foundation. Safe TOML configuration is validated before use, layered through explicit profile/local selection, and identified by a deterministic digest that excludes resolved secret values.

PostgreSQL access, migrations, Docker Compose, CI, source adapters, external providers, real credentials, and deployment remain intentionally deferred to later independently reviewed tasks.

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

Run the local quality checks:

```shell
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run pytest
```

The environment is project-local and disposable. Do not commit `.venv`, local configuration, secrets, generated artifacts, or runtime data.
