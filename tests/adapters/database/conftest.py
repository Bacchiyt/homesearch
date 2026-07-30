"""Shared fixtures for PostgreSQL adapter integration tests."""

from __future__ import annotations

import os

import pytest

from homesearch.config import LoadedConfiguration
from tests.adapters.database.postgresql import load_with_database_url

TEST_DATABASE_URL_ENV = "HOMESEARCH_TEST_DATABASE_URL"


@pytest.fixture(scope="module")
def server_configuration(
    tmp_path_factory: pytest.TempPathFactory,
) -> LoadedConfiguration:
    """Load the explicitly supplied PostgreSQL server connection."""

    database_url = os.environ.get(TEST_DATABASE_URL_ENV)
    if database_url is None:
        pytest.skip(f"{TEST_DATABASE_URL_ENV} is required for PostgreSQL integration tests")
    return load_with_database_url(
        tmp_path_factory.mktemp("postgresql-server-configuration"),
        database_url,
    )
