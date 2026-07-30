"""Unit tests for application-owned persistence inputs."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Never
from uuid import uuid4

import pytest

from homesearch.application import persist_configuration_foundation
from homesearch.config import OperationalSettings, load_configuration

DEFAULTS = Path("config/defaults.toml")


def _must_not_open_unit_of_work() -> Never:
    raise AssertionError("invalid application input opened a unit of work")


def test_non_uuid7_snapshot_identity_is_rejected_before_persistence() -> None:
    with pytest.raises(ValueError, match="UUIDv7"):
        persist_configuration_foundation(
            load_configuration(OperationalSettings(config_path=DEFAULTS)),
            _must_not_open_unit_of_work,
            id_factory=uuid4,
        )


def test_naive_system_clock_is_rejected_before_persistence() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        persist_configuration_foundation(
            load_configuration(OperationalSettings(config_path=DEFAULTS)),
            _must_not_open_unit_of_work,
            clock=lambda: datetime(2026, 7, 31),
        )
