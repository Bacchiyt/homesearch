"""Layered TOML configuration loading and secret resolution."""

from __future__ import annotations

import hashlib
import json
import tomllib
from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
from typing import Any

from pydantic import BaseModel, SecretStr, ValidationError

from homesearch.config.models import (
    LoadedConfiguration,
    LocalConfiguration,
    OperationalSettings,
    ProfileConfiguration,
    ResolvedSecret,
    SafeConfiguration,
    SecretSetting,
)


class ConfigurationError(RuntimeError):
    """Safe startup failure caused by invalid or incomplete configuration."""


def load_configuration(
    settings: OperationalSettings | None = None,
) -> LoadedConfiguration:
    """Load and validate all configured layers before work starts."""

    active_settings = settings or OperationalSettings()
    base_data = _read_toml(active_settings.config_path)
    base = _validate(SafeConfiguration, base_data, active_settings.config_path)
    merged = base.model_dump(mode="python")

    if active_settings.profile_path is not None:
        profile_data = _read_toml(active_settings.profile_path)
        profile = _validate(
            ProfileConfiguration,
            profile_data,
            active_settings.profile_path,
        )
        _merge(merged, profile.model_dump(mode="python", exclude_none=True))

    if active_settings.local_config_path is not None:
        local_data = _read_toml(active_settings.local_config_path)
        local = _validate(
            LocalConfiguration,
            local_data,
            active_settings.local_config_path,
        )
        _merge(merged, local.model_dump(mode="python", exclude_none=True))

    runtime_overrides = {
        key: value
        for key, value in {
            "log_level": active_settings.log_level,
            "log_format": active_settings.log_format,
        }.items()
        if value is not None
    }
    if runtime_overrides:
        _merge(merged, {"runtime": runtime_overrides})

    effective = _validate(SafeConfiguration, merged, "effective configuration")
    resolved_secrets = _resolve_secrets(effective, active_settings)
    return LoadedConfiguration(
        configuration=effective,
        digest=_configuration_digest(effective),
        resolved_secrets=resolved_secrets,
    )


def _read_toml(path: Path) -> dict[str, Any]:
    try:
        with path.open("rb") as config_file:
            return tomllib.load(config_file)
    except FileNotFoundError as exc:
        raise ConfigurationError(f"Configuration file does not exist: {path}") from exc
    except tomllib.TOMLDecodeError as exc:
        raise ConfigurationError(f"Configuration file is not valid TOML: {path}") from exc
    except OSError as exc:
        raise ConfigurationError(f"Configuration file cannot be read: {path}") from exc


def _validate[ModelT: BaseModel](
    model: type[ModelT],
    data: Mapping[str, Any],
    source: Path | str,
) -> ModelT:
    try:
        return model.model_validate(data)
    except ValidationError as exc:
        raise ConfigurationError(f"Invalid configuration in {source}: {exc}") from exc


def _merge(target: dict[str, Any], overlay: Mapping[str, Any]) -> None:
    for key, value in overlay.items():
        existing = target.get(key)
        if isinstance(existing, dict) and isinstance(value, Mapping):
            _merge(existing, value)
        else:
            target[key] = deepcopy(value)


def _configuration_digest(configuration: SafeConfiguration) -> str:
    canonical = json.dumps(
        configuration.model_dump(mode="json"),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    return f"sha256:{hashlib.sha256(canonical).hexdigest()}"


def _resolve_secrets(
    configuration: SafeConfiguration,
    settings: OperationalSettings,
) -> tuple[ResolvedSecret, ...]:
    available: dict[SecretSetting, SecretStr | None] = {
        SecretSetting.DATABASE_URL: settings.database_url,
    }
    resolved: list[ResolvedSecret] = []

    for reference in configuration.secret_references:
        value = available[reference.setting]
        if value is None or not value.get_secret_value():
            if reference.required:
                raise ConfigurationError(
                    f"Required secret reference is unresolved: {reference.secret_id}"
                )
            continue
        resolved.append(ResolvedSecret(secret_id=reference.secret_id, value=value))

    return tuple(resolved)
