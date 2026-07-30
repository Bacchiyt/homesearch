# Homesearch

Homesearch is a personal system for discovering, normalizing, enriching, evaluating, tracking, and reporting Japanese residential property listings. Product and architecture documentation starts at [`docs/README.md`](docs/README.md).

## Current implementation scope

Phase 1 begins with the Python project and local quality-tool bootstrap. This first task provides only a runnable package, locked dependencies, and deterministic lint, format, type, and test commands.

Configuration, PostgreSQL, migrations, Docker Compose, CI, source adapters, external providers, credentials, and deployment remain intentionally deferred to later independently reviewed tasks.

## Local setup

Install [uv](https://docs.astral.sh/uv/getting-started/installation/). The project pins CPython 3.14.6 in `.python-version`; uv can install that interpreter when it is not already available.

```shell
uv sync --locked
```

Run the local quality checks:

```shell
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run pytest
```

The environment is project-local and disposable. Do not commit `.venv`, local configuration, secrets, generated artifacts, or runtime data.
