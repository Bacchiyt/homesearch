"""Tests for versioned layered configuration."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest
from pydantic import SecretStr

from homesearch.config import (
    ConfigurationError,
    LogFormat,
    LogLevel,
    OperationalSettings,
    load_configuration,
)

DEFAULTS = Path("config/defaults.toml")


def _write_toml(path: Path, content: str) -> Path:
    path.write_text(dedent(content).strip() + "\n", encoding="utf-8")
    return path


def _settings(config_path: Path, **values: object) -> OperationalSettings:
    return OperationalSettings.model_validate({"config_path": config_path, **values})


def test_repository_defaults_load_with_a_stable_digest() -> None:
    loaded_once = load_configuration(_settings(DEFAULTS))
    loaded_again = load_configuration(_settings(DEFAULTS))

    assert loaded_once.configuration.schema_version == 1
    assert loaded_once.configuration.config_id == "homesearch-default"
    assert loaded_once.configuration.config_version == 1
    assert loaded_once.configuration.runtime.log_level is LogLevel.INFO
    assert loaded_once.configuration.runtime.log_format is LogFormat.JSON
    assert loaded_once.digest == loaded_again.digest
    assert loaded_once.digest.startswith("sha256:")
    assert len(loaded_once.digest) == 71


@pytest.mark.parametrize("filename", ["missing.toml", "invalid.toml"])
def test_missing_or_malformed_toml_fails_before_work_starts(
    tmp_path: Path,
    filename: str,
) -> None:
    path = tmp_path / filename
    if filename == "invalid.toml":
        path.write_text("not = [valid", encoding="utf-8")

    with pytest.raises(ConfigurationError, match="Configuration file"):
        load_configuration(_settings(path))


def test_layers_apply_in_the_documented_precedence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base = _write_toml(
        tmp_path / "base.toml",
        """
        schema_version = 1
        config_id = "base"
        config_version = 1
        effective_from = 2026-07-30T00:00:00Z

        [runtime]
        log_level = "INFO"
        log_format = "json"
        """,
    )
    profile = _write_toml(
        tmp_path / "profile.toml",
        """
        schema_version = 1
        config_id = "profile"
        config_version = 2
        effective_from = 2026-07-31T00:00:00Z

        [runtime]
        log_level = "DEBUG"
        """,
    )
    local = _write_toml(
        tmp_path / "local.toml",
        """
        [runtime]
        log_format = "console"
        """,
    )

    layered = load_configuration(_settings(base, profile_path=profile, local_config_path=local))
    assert layered.configuration.config_id == "profile"
    assert layered.configuration.config_version == 2
    assert layered.configuration.runtime.log_level is LogLevel.DEBUG
    assert layered.configuration.runtime.log_format is LogFormat.CONSOLE

    monkeypatch.setenv("HOMESEARCH_LOG_LEVEL", "ERROR")
    monkeypatch.setenv("HOMESEARCH_LOG_FORMAT", "json")
    monkeypatch.chdir(tmp_path)
    overridden = load_configuration(
        OperationalSettings(
            config_path=base,
            profile_path=profile,
            local_config_path=local,
        )
    )
    assert overridden.configuration.runtime.log_level is LogLevel.ERROR
    assert overridden.configuration.runtime.log_format is LogFormat.JSON


def test_ignored_dotenv_supplies_allowlisted_settings_and_secrets(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    defaults = DEFAULTS.resolve()
    profile = _write_toml(
        tmp_path / "profile.toml",
        """
        schema_version = 1
        config_id = "dotenv-profile"
        config_version = 1
        effective_from = 2026-07-30T00:00:00Z

        [[secret_references]]
        secret_id = "database-url"
        setting = "database_url"
        required = true
        """,
    )
    secret_value = "dotenv-sensitive-value"
    (tmp_path / ".env").write_text(
        "\n".join(
            [
                f"HOMESEARCH_CONFIG_PATH={defaults}",
                f"HOMESEARCH_PROFILE_PATH={profile}",
                "HOMESEARCH_LOG_LEVEL=WARNING",
                f"HOMESEARCH_DATABASE_URL={secret_value}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    loaded = load_configuration()

    assert loaded.configuration.config_id == "dotenv-profile"
    assert loaded.configuration.runtime.log_level is LogLevel.WARNING
    assert loaded.get_secret("database-url") is not None
    assert secret_value not in repr(loaded)
    assert secret_value not in loaded.model_dump_json()


@pytest.mark.parametrize(
    ("filename", "content", "setting_values"),
    [
        (
            "base.toml",
            """
            schema_version = 1
            config_id = "base"
            config_version = 1
            effective_from = 2026-07-30T00:00:00Z
            unexpected = true

            [runtime]
            log_level = "INFO"
            log_format = "json"
            """,
            {},
        ),
        (
            "profile.toml",
            """
            schema_version = 1
            config_id = "profile"
            config_version = 1
            effective_from = 2026-07-30T00:00:00Z
            unexpected = true
            """,
            {"profile_path": "profile.toml"},
        ),
        (
            "local.toml",
            """
            config_id = "not-allowed-locally"
            """,
            {"local_config_path": "local.toml"},
        ),
    ],
)
def test_unknown_fields_are_rejected_in_every_layer(
    tmp_path: Path,
    filename: str,
    content: str,
    setting_values: dict[str, str],
) -> None:
    base = _write_toml(
        tmp_path / "base.toml",
        """
        schema_version = 1
        config_id = "base"
        config_version = 1
        effective_from = 2026-07-30T00:00:00Z

        [runtime]
        log_level = "INFO"
        log_format = "json"
        """,
    )
    target = _write_toml(tmp_path / filename, content)
    if filename == "base.toml":
        base = target

    resolved_values = {key: tmp_path / value for key, value in setting_values.items()}
    with pytest.raises(ConfigurationError, match="Invalid configuration"):
        load_configuration(_settings(base, **resolved_values))


@pytest.mark.parametrize(
    "invalid_line",
    [
        "schema_version = 2",
        'config_id = "UPPERCASE"',
        "config_version = 0",
        "effective_from = 2026-07-30T09:00:00+09:00",
    ],
)
def test_invalid_version_metadata_fails_before_work_starts(
    tmp_path: Path,
    invalid_line: str,
) -> None:
    values = {
        "schema_version": "schema_version = 1",
        "config_id": 'config_id = "base"',
        "config_version": "config_version = 1",
        "effective_from": "effective_from = 2026-07-30T00:00:00Z",
    }
    field = invalid_line.split("=", maxsplit=1)[0].strip()
    values[field] = invalid_line
    base = _write_toml(
        tmp_path / "base.toml",
        f"""
        {values["schema_version"]}
        {values["config_id"]}
        {values["config_version"]}
        {values["effective_from"]}

        [runtime]
        log_level = "INFO"
        log_format = "json"
        """,
    )

    with pytest.raises(ConfigurationError, match="Invalid configuration"):
        load_configuration(_settings(base))


def test_required_secret_reference_must_resolve(tmp_path: Path) -> None:
    profile = _write_toml(
        tmp_path / "profile.toml",
        """
        schema_version = 1
        config_id = "database-profile"
        config_version = 1
        effective_from = 2026-07-30T00:00:00Z

        [[secret_references]]
        secret_id = "database-url"
        setting = "database_url"
        required = true
        """,
    )

    with pytest.raises(
        ConfigurationError,
        match="Required secret reference is unresolved: database-url",
    ):
        load_configuration(_settings(DEFAULTS, profile_path=profile))


def test_duplicate_secret_references_are_rejected(tmp_path: Path) -> None:
    profile = _write_toml(
        tmp_path / "profile.toml",
        """
        schema_version = 1
        config_id = "database-profile"
        config_version = 1
        effective_from = 2026-07-30T00:00:00Z

        [[secret_references]]
        secret_id = "primary-database"
        setting = "database_url"

        [[secret_references]]
        secret_id = "duplicate-database"
        setting = "database_url"
        """,
    )

    with pytest.raises(
        ConfigurationError,
        match="secret settings must be referenced at most once",
    ):
        load_configuration(_settings(DEFAULTS, profile_path=profile))


def test_secret_values_are_redacted_and_excluded_from_digest(tmp_path: Path) -> None:
    profile = _write_toml(
        tmp_path / "profile.toml",
        """
        schema_version = 1
        config_id = "database-profile"
        config_version = 1
        effective_from = 2026-07-30T00:00:00Z

        [[secret_references]]
        secret_id = "database-url"
        setting = "database_url"
        required = true
        """,
    )
    first_value = "first-sensitive-value"
    second_value = "second-sensitive-value"

    first = load_configuration(
        _settings(
            DEFAULTS,
            profile_path=profile,
            database_url=SecretStr(first_value),
        )
    )
    second = load_configuration(
        _settings(
            DEFAULTS,
            profile_path=profile,
            database_url=SecretStr(second_value),
        )
    )

    assert first.digest == second.digest
    assert first.get_secret("database-url") is not None
    assert first.get_secret("missing") is None
    rendered = f"{first!r}\n{first}\n{first.model_dump_json()}"
    assert first_value not in rendered
    assert second_value not in rendered


def test_digest_is_independent_of_toml_key_order(tmp_path: Path) -> None:
    first = _write_toml(
        tmp_path / "first.toml",
        """
        schema_version = 1
        config_id = "same"
        config_version = 1
        effective_from = 2026-07-30T00:00:00Z

        [runtime]
        log_level = "INFO"
        log_format = "json"
        """,
    )
    second = _write_toml(
        tmp_path / "second.toml",
        """
        effective_from = 2026-07-30T00:00:00Z
        config_version = 1
        config_id = "same"
        schema_version = 1

        [runtime]
        log_format = "json"
        log_level = "INFO"
        """,
    )

    assert (
        load_configuration(_settings(first)).digest == load_configuration(_settings(second)).digest
    )


def test_environment_cannot_override_unlisted_policy_fields(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    defaults = DEFAULTS.resolve()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HOMESEARCH_CONFIG_VERSION", "999")

    loaded = load_configuration(OperationalSettings(config_path=defaults))

    assert loaded.configuration.config_version == 1
