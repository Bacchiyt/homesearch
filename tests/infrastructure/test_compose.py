"""Static contract tests for the local PostgreSQL Compose foundation."""

from __future__ import annotations

import re
from pathlib import Path

COMPOSE = Path("compose.yaml")
GITIGNORE = Path(".gitignore")


def _compose_text() -> str:
    return COMPOSE.read_text(encoding="utf-8")


def test_compose_defines_only_the_managed_postgresql_service() -> None:
    compose = _compose_text()
    services = compose.partition("services:\n")[2].partition("\nsecrets:\n")[0]

    assert re.findall(r"^  ([a-z0-9-]+):$", services, flags=re.MULTILINE) == ["postgres"]
    assert "image: postgres:18.4-bookworm" in services


def test_postgresql_is_health_checked_and_exposed_only_on_loopback() -> None:
    compose = _compose_text()

    assert "pg_isready --username=$$POSTGRES_USER --dbname=$$POSTGRES_DB" in compose
    assert '"127.0.0.1:${HOMESEARCH_POSTGRES_PORT:-5432}:5432"' in compose


def test_postgresql_18_data_uses_an_explicit_named_volume() -> None:
    compose = _compose_text()

    assert "homesearch-postgres-data:/var/lib/postgresql" in compose
    assert "name: homesearch-postgres-18-data" in compose


def test_postgresql_password_uses_an_ignored_file_secret() -> None:
    compose = _compose_text()
    gitignore = GITIGNORE.read_text(encoding="utf-8").splitlines()

    assert "POSTGRES_PASSWORD:" not in compose
    assert "POSTGRES_PASSWORD_FILE: /run/secrets/postgres-password" in compose
    assert "file: ${HOMESEARCH_POSTGRES_PASSWORD_FILE:-.secrets/postgres-password}" in compose
    assert ".secrets/" in gitignore
