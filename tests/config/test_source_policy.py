"""Tests for the versioned non-secret source-policy boundary."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from homesearch.config import (
    CaptureMode,
    ConfigurationError,
    OperationalSettings,
    RawStorageAdapter,
    SourceAccessStatus,
    SourceCapability,
    SourceLifecycle,
    load_configuration,
)

DEFAULTS = Path("config/defaults.toml")
DEFAULT_USER_ID = "019fb31c-0022-70cf-afee-7644241d7ba8"
SOURCE_ID = "019fb335-0722-763d-a31f-7ad965f418c4"
OTHER_SOURCE_ID = "019fb335-0723-76eb-ae89-d02a2be0b2e1"


def _write_profile(tmp_path: Path, source_policy: str) -> Path:
    profile = tmp_path / "source-profile.toml"
    profile.write_text(
        dedent(
            f"""
            schema_version = 3
            config_id = "source-profile"
            config_version = 1
            effective_from = 2026-07-30T00:00:00Z

            [source_registry]
            {source_policy}
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    return profile


def _source_policy(
    *,
    source_id: str = SOURCE_ID,
    source_key: str = "synthetic-source",
    source_version: str = "1",
    effective_from: str = "2026-07-30T00:00:00Z",
    lifecycle: str = "ENABLED",
    access_status: str = "APPROVED",
    assessment: str = 'access_assessment_reference = "synthetic-access-assessment"',
    capabilities: str = '["DISCOVERY", "DETAIL_FETCH"]',
    request_policy: str = """
        [source_registry.sources.request_policy]
        timeout_seconds = 30
        minimum_interval_seconds = 2
        maximum_concurrency = 1
        maximum_requests_per_run = 50
    """,
    capture_mode: str = "METADATA_ONLY",
    storage_adapter: str = "NONE",
    raw_payload_retention_days: str = "0",
) -> str:
    return dedent(
        f"""
        [[source_registry.sources]]
        source_id = "{source_id}"
        source_key = "{source_key}"
        source_version = {source_version}
        effective_from = {effective_from}
        lifecycle = "{lifecycle}"
        access_status = "{access_status}"
        {assessment}
        capabilities = {capabilities}

        {request_policy}

        [source_registry.sources.capture_policy]
        capture_mode = "{capture_mode}"
        storage_adapter = "{storage_adapter}"
        raw_payload_retention_days = {raw_payload_retention_days}
        """
    ).strip()


def test_schema_version_three_requires_an_explicit_source_registry(tmp_path: Path) -> None:
    base = tmp_path / "missing-source-registry.toml"
    base.write_text(
        dedent(
            f"""
            schema_version = 3
            config_id = "missing-source-registry"
            config_version = 1
            effective_from = 2026-07-30T00:00:00Z

            [user_scope]
            default_user_id = "{DEFAULT_USER_ID}"

            [[user_scope.users]]
            user_id = "{DEFAULT_USER_ID}"

            [runtime]
            log_level = "INFO"
            log_format = "json"
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ConfigurationError, match="Invalid configuration"):
        load_configuration(OperationalSettings(config_path=base))


def test_versioned_profile_replaces_source_registry_and_changes_digest(
    tmp_path: Path,
) -> None:
    profile = _write_profile(tmp_path, _source_policy())

    defaults = load_configuration(OperationalSettings(config_path=DEFAULTS))
    profiled = load_configuration(OperationalSettings(config_path=DEFAULTS, profile_path=profile))

    assert defaults.configuration.source_registry.sources == ()
    assert profiled.digest != defaults.digest

    (source,) = profiled.configuration.source_registry.sources
    assert str(source.source_id) == SOURCE_ID
    assert source.source_key == "synthetic-source"
    assert source.source_version == 1
    assert source.lifecycle is SourceLifecycle.ENABLED
    assert source.access_status is SourceAccessStatus.APPROVED
    assert source.capabilities == (
        SourceCapability.DISCOVERY,
        SourceCapability.DETAIL_FETCH,
    )
    assert source.request_policy is not None
    assert source.request_policy.maximum_concurrency == 1
    assert source.capture_policy.capture_mode is CaptureMode.METADATA_ONLY
    assert source.capture_policy.storage_adapter is RawStorageAdapter.NONE
    assert source.capture_policy.raw_payload_retention_days == 0


def test_disabled_source_can_prepare_filesystem_capture_without_access(
    tmp_path: Path,
) -> None:
    source_policy = _source_policy(
        lifecycle="DISABLED",
        access_status="NOT_ASSESSED",
        assessment="",
        capabilities="[]",
        request_policy="",
        capture_mode="SANITIZED_PAYLOAD",
        storage_adapter="FILESYSTEM",
        raw_payload_retention_days="7",
    )

    loaded = load_configuration(
        OperationalSettings(
            config_path=DEFAULTS,
            profile_path=_write_profile(tmp_path, source_policy),
        )
    )

    (source,) = loaded.configuration.source_registry.sources
    assert source.lifecycle is SourceLifecycle.DISABLED
    assert source.request_policy is None
    assert source.capture_policy.storage_adapter is RawStorageAdapter.FILESYSTEM
    assert source.capture_policy.raw_payload_retention_days == 7


@pytest.mark.parametrize(
    ("source_policy", "message"),
    [
        (
            _source_policy(
                access_status="NOT_ASSESSED",
                assessment="",
            ),
            "enabled source access must be approved",
        ),
        (
            _source_policy(
                lifecycle="DISABLED",
                assessment="",
            ),
            "approved source access requires an assessment reference",
        ),
        (
            _source_policy(capabilities="[]"),
            "enabled sources must declare at least one capability",
        ),
        (
            _source_policy(request_policy=""),
            "enabled network sources require a request policy",
        ),
        (
            _source_policy(capabilities='["DISCOVERY", "DISCOVERY"]'),
            "source capabilities must be unique",
        ),
        (
            _source_policy(
                lifecycle="DISABLED",
                access_status="NOT_ASSESSED",
                assessment="",
                capabilities="[]",
                request_policy="",
                effective_from="2026-07-30T09:00:00+09:00",
            ),
            "effective_from must use UTC",
        ),
        (
            _source_policy(source_id="7b259146-cb4f-4fdf-9301-72c6eb0d16fc"),
            "Invalid configuration",
        ),
        (
            _source_policy(source_version="0"),
            "Invalid configuration",
        ),
        (
            _source_policy(
                request_policy="""
                    [source_registry.sources.request_policy]
                    timeout_seconds = 30
                    minimum_interval_seconds = 2
                    maximum_concurrency = 0
                    maximum_requests_per_run = 50
                """,
            ),
            "Invalid configuration",
        ),
        (
            _source_policy(
                lifecycle="DISABLED",
                access_status="NOT_ASSESSED",
                assessment="",
                capabilities="[]",
                request_policy="",
                capture_mode="FULL_PAYLOAD",
            ),
            "stored capture modes require a storage adapter",
        ),
        (
            _source_policy(
                lifecycle="DISABLED",
                access_status="NOT_ASSESSED",
                assessment="",
                capabilities="[]",
                request_policy="",
                storage_adapter="FILESYSTEM",
            ),
            "non-stored capture modes cannot select a storage adapter",
        ),
        (
            _source_policy(
                lifecycle="DISABLED",
                access_status="NOT_ASSESSED",
                assessment="",
                capabilities="[]",
                request_policy="",
                raw_payload_retention_days="1",
            ),
            "non-stored capture modes require zero raw-payload retention",
        ),
    ],
    ids=[
        "enabled-without-approval",
        "approval-without-assessment",
        "enabled-without-capability",
        "network-without-request-policy",
        "duplicate-capability",
        "non-utc-effective-time",
        "non-uuidv7-source-id",
        "invalid-source-version",
        "invalid-request-limit",
        "stored-without-adapter",
        "non-stored-with-adapter",
        "non-stored-with-retention",
    ],
)
def test_invalid_source_policy_fails_before_work_starts(
    tmp_path: Path,
    source_policy: str,
    message: str,
) -> None:
    profile = _write_profile(tmp_path, source_policy)

    with pytest.raises(ConfigurationError, match=message):
        load_configuration(OperationalSettings(config_path=DEFAULTS, profile_path=profile))


@pytest.mark.parametrize(
    ("second_source", "message"),
    [
        ({}, "source IDs must be unique"),
        ({"source_id": OTHER_SOURCE_ID}, "source keys must be unique"),
    ],
    ids=["duplicate-id", "duplicate-key"],
)
def test_duplicate_source_identities_are_rejected(
    tmp_path: Path,
    second_source: dict[str, str],
    message: str,
) -> None:
    first = _source_policy(
        lifecycle="DISABLED",
        access_status="NOT_ASSESSED",
        assessment="",
        capabilities="[]",
        request_policy="",
    )
    second = _source_policy(
        lifecycle="DISABLED",
        access_status="NOT_ASSESSED",
        assessment="",
        capabilities="[]",
        request_policy="",
        **second_source,
    )
    profile = _write_profile(tmp_path, f"{first}\n\n{second}")

    with pytest.raises(ConfigurationError, match=message):
        load_configuration(OperationalSettings(config_path=DEFAULTS, profile_path=profile))
