"""Tests for versioned source-neutral search-policy configuration."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent
from typing import Any

import pytest
from pydantic import ValidationError

from homesearch.config import (
    AdministrativeAreaConfiguration,
    ConfigurationError,
    OperationalSettings,
    PriceCriteriaConfiguration,
    PropertyCondition,
    PropertyType,
    SearchLifecycle,
    SearchPolicyConfiguration,
    SearchRegistryConfiguration,
    load_configuration,
)

DEFAULTS = Path("config/defaults.toml")
DEFAULT_USER_ID = "019fb31c-0022-70cf-afee-7644241d7ba8"
OTHER_USER_ID = "019fb31c-0023-7ff2-a50a-ad4abcf54ecb"
SOURCE_ID = "019fb335-0722-763d-a31f-7ad965f418c4"
OTHER_SOURCE_ID = "019fb335-0723-76eb-ae89-d02a2be0b2e1"
SEARCH_ID = "019fb342-a8f4-7224-93b7-6dbd74d2f13b"
OTHER_SEARCH_ID = "019fb342-a8f5-71bd-b8a5-32087aa4a128"


def _search_data(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "search_id": SEARCH_ID,
        "search_key": "synthetic-search",
        "search_version": 1,
        "effective_from": "2026-07-30T00:00:00Z",
        "user_id": DEFAULT_USER_ID,
        "lifecycle": "ENABLED",
        "source_ids": [SOURCE_ID],
        "areas": [
            {
                "area_key": "example-area",
                "prefecture": "Example Prefecture",
                "municipality": "Example Municipality",
                "localities": ["Example Locality"],
            }
        ],
        "price": {
            "minimum_jpy": 30_000_000,
            "maximum_jpy": 45_000_000,
            "negotiation_margin_jpy": 5_000_000,
        },
        "property_types": ["DETACHED_HOUSE"],
        "property_conditions": ["NEW"],
        "discovery_interval_minutes": 720,
        "maximum_results_per_run": 50,
    }
    data.update(overrides)
    return data


def _source_policy(
    *,
    lifecycle: str = "ENABLED",
    access_status: str = "APPROVED",
    access_assessment: str = ('access_assessment_reference = "synthetic-access-assessment"'),
    capabilities: str = '["DISCOVERY"]',
) -> str:
    return dedent(
        f"""
        [[source_registry.sources]]
        source_id = "{SOURCE_ID}"
        source_key = "synthetic-source"
        source_version = 1
        effective_from = 2026-07-30T00:00:00Z
        lifecycle = "{lifecycle}"
        access_status = "{access_status}"
        {access_assessment}
        capabilities = {capabilities}

        [source_registry.sources.request_policy]
        timeout_seconds = 30
        minimum_interval_seconds = 2
        maximum_concurrency = 1
        maximum_requests_per_run = 50

        [source_registry.sources.capture_policy]
        capture_mode = "METADATA_ONLY"
        storage_adapter = "NONE"
        raw_payload_retention_days = 0
        """
    ).strip()


def _search_policy(
    *,
    user_id: str = DEFAULT_USER_ID,
    source_id: str = SOURCE_ID,
    lifecycle: str = "ENABLED",
) -> str:
    return dedent(
        f"""
        [[search_registry.searches]]
        search_id = "{SEARCH_ID}"
        search_key = "synthetic-search"
        search_version = 1
        effective_from = 2026-07-30T00:00:00Z
        user_id = "{user_id}"
        lifecycle = "{lifecycle}"
        source_ids = ["{source_id}"]
        property_types = ["DETACHED_HOUSE"]
        property_conditions = ["NEW"]
        discovery_interval_minutes = 720
        maximum_results_per_run = 50

        [[search_registry.searches.areas]]
        area_key = "example-area"
        prefecture = "Example Prefecture"
        municipality = "Example Municipality"
        localities = ["Example Locality"]

        [search_registry.searches.price]
        minimum_jpy = 30000000
        maximum_jpy = 45000000
        negotiation_margin_jpy = 5000000
        """
    ).strip()


def _write_profile(
    tmp_path: Path,
    *,
    source_policy: str | None = None,
    search_policy: str | None = None,
) -> Path:
    profile = tmp_path / "search-profile.toml"
    profile.write_text(
        dedent(
            f"""
            schema_version = 4
            config_id = "search-profile"
            config_version = 1
            effective_from = 2026-07-30T00:00:00Z

            [source_registry]
            {source_policy if source_policy is not None else _source_policy()}

            [search_registry]
            {search_policy if search_policy is not None else _search_policy()}
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    return profile


def test_schema_version_four_requires_an_explicit_search_registry(tmp_path: Path) -> None:
    base = tmp_path / "missing-search-registry.toml"
    base.write_text(
        dedent(
            f"""
            schema_version = 4
            config_id = "missing-search-registry"
            config_version = 1
            effective_from = 2026-07-30T00:00:00Z

            [user_scope]
            default_user_id = "{DEFAULT_USER_ID}"

            [[user_scope.users]]
            user_id = "{DEFAULT_USER_ID}"

            [source_registry]
            sources = []

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


def test_versioned_profile_replaces_search_registry_and_changes_digest(
    tmp_path: Path,
) -> None:
    defaults = load_configuration(OperationalSettings(config_path=DEFAULTS))
    profiled = load_configuration(
        OperationalSettings(
            config_path=DEFAULTS,
            profile_path=_write_profile(tmp_path),
        )
    )

    assert defaults.configuration.search_registry.searches == ()
    assert profiled.digest != defaults.digest

    (search,) = profiled.configuration.search_registry.searches
    assert str(search.search_id) == SEARCH_ID
    assert search.search_id.version == 7
    assert search.search_key == "synthetic-search"
    assert search.search_version == 1
    assert search.user_id.version == 7
    assert search.lifecycle is SearchLifecycle.ENABLED
    assert tuple(str(source_id) for source_id in search.source_ids) == (SOURCE_ID,)
    assert search.areas[0].area_key == "example-area"
    assert search.areas[0].localities == ("Example Locality",)
    assert search.price.maximum_jpy == 45_000_000
    assert search.price.negotiation_margin_jpy == 5_000_000
    assert search.property_types == (PropertyType.DETACHED_HOUSE,)
    assert search.property_conditions == (PropertyCondition.NEW,)
    assert search.discovery_interval_minutes == 720
    assert search.maximum_results_per_run == 50


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"search_id": "7b259146-cb4f-4fdf-9301-72c6eb0d16fc"}, "UUID version 7"),
        ({"search_version": 0}, "greater than 0"),
        ({"effective_from": "2026-07-30T09:00:00+09:00"}, "must use UTC"),
        ({"source_ids": []}, "at least one source"),
        ({"source_ids": [SOURCE_ID, SOURCE_ID]}, "source references must be unique"),
        ({"areas": []}, "at least one area"),
        (
            {
                "areas": [
                    {
                        "area_key": "duplicate-area",
                        "prefecture": "Example Prefecture",
                        "municipality": "Example Municipality",
                    },
                    {
                        "area_key": "duplicate-area",
                        "prefecture": "Other Prefecture",
                        "municipality": "Other Municipality",
                    },
                ]
            },
            "area keys must be unique",
        ),
        ({"property_types": []}, "at least one property type"),
        (
            {"property_types": ["DETACHED_HOUSE", "DETACHED_HOUSE"]},
            "property types must be unique",
        ),
        ({"property_conditions": []}, "at least one property condition"),
        (
            {"property_conditions": ["NEW", "NEW"]},
            "property conditions must be unique",
        ),
        ({"discovery_interval_minutes": 0}, "greater than 0"),
        ({"maximum_results_per_run": 0}, "greater than 0"),
        ({"unknown_criterion": True}, "Extra inputs are not permitted"),
    ],
)
def test_invalid_search_policy_fails_validation(
    overrides: dict[str, Any],
    message: str,
) -> None:
    with pytest.raises(ValidationError, match=message):
        SearchPolicyConfiguration.model_validate(_search_data(**overrides))


@pytest.mark.parametrize(
    ("area", "message"),
    [
        (
            {
                "area_key": "example-area",
                "prefecture": " Example Prefecture",
                "municipality": "Example Municipality",
            },
            "must be non-blank and trimmed",
        ),
        (
            {
                "area_key": "example-area",
                "prefecture": "Example Prefecture",
                "municipality": "Example Municipality",
                "localities": ["Example Locality", "Example Locality"],
            },
            "locality labels must be unique",
        ),
    ],
)
def test_invalid_administrative_area_fails_validation(
    area: dict[str, Any],
    message: str,
) -> None:
    with pytest.raises(ValidationError, match=message):
        AdministrativeAreaConfiguration.model_validate(area)


@pytest.mark.parametrize(
    ("price", "message"),
    [
        (
            {"minimum_jpy": 46_000_000, "maximum_jpy": 45_000_000},
            "minimum_jpy cannot exceed maximum_jpy",
        ),
        (
            {"negotiation_margin_jpy": 5_000_000},
            "negotiation_margin_jpy requires maximum_jpy",
        ),
        ({"minimum_jpy": -1}, "greater than or equal to 0"),
        ({"maximum_jpy": 0}, "greater than 0"),
    ],
)
def test_invalid_price_criteria_fails_validation(
    price: dict[str, int],
    message: str,
) -> None:
    with pytest.raises(ValidationError, match=message):
        PriceCriteriaConfiguration.model_validate(price)


@pytest.mark.parametrize(
    ("second_overrides", "message"),
    [
        ({"search_key": "other-search"}, "search IDs must be unique"),
        ({"search_id": OTHER_SEARCH_ID}, "search keys must be unique"),
    ],
)
def test_search_registry_rejects_duplicate_identity(
    second_overrides: dict[str, Any],
    message: str,
) -> None:
    with pytest.raises(ValidationError, match=message):
        SearchRegistryConfiguration.model_validate(
            {
                "searches": [
                    _search_data(),
                    _search_data(**second_overrides),
                ]
            }
        )


@pytest.mark.parametrize(
    ("search_policy", "source_policy", "message"),
    [
        (
            _search_policy(user_id=OTHER_USER_ID),
            _source_policy(),
            "search user_id must reference a configured user",
        ),
        (
            _search_policy(source_id=OTHER_SOURCE_ID),
            _source_policy(),
            "search source_ids must reference configured sources",
        ),
        (
            _search_policy(),
            _source_policy(lifecycle="DISABLED"),
            "enabled searches require enabled sources",
        ),
        (
            _search_policy(),
            _source_policy(capabilities='["DETAIL_FETCH"]'),
            "enabled searches require source discovery capability",
        ),
    ],
)
def test_invalid_search_references_fail_before_work_starts(
    tmp_path: Path,
    search_policy: str,
    source_policy: str,
    message: str,
) -> None:
    profile = _write_profile(
        tmp_path,
        source_policy=source_policy,
        search_policy=search_policy,
    )

    with pytest.raises(ConfigurationError, match=message):
        load_configuration(OperationalSettings(config_path=DEFAULTS, profile_path=profile))


def test_disabled_search_can_reference_unassessed_disabled_source(
    tmp_path: Path,
) -> None:
    profile = _write_profile(
        tmp_path,
        source_policy=_source_policy(
            lifecycle="DISABLED",
            access_status="NOT_ASSESSED",
            access_assessment="",
            capabilities="[]",
        ),
        search_policy=_search_policy(lifecycle="DISABLED"),
    )

    loaded = load_configuration(OperationalSettings(config_path=DEFAULTS, profile_path=profile))

    (search,) = loaded.configuration.search_registry.searches
    assert search.lifecycle is SearchLifecycle.DISABLED
