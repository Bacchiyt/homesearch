"""Configuration boundary models."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Annotated, Literal

from pydantic import (
    UUID7,
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    PositiveInt,
    SecretStr,
    field_validator,
    model_validator,
)

StableId = Annotated[
    str,
    Field(
        min_length=1,
        max_length=64,
        pattern=r"^[a-z][a-z0-9-]*$",
    ),
]
ConfigurationDigest = Annotated[str, Field(pattern=r"^sha256:[0-9a-f]{64}$")]


class StrictConfigurationModel(BaseModel):
    """Immutable model that rejects undeclared configuration fields."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
    )


class LogLevel(StrEnum):
    """Supported standard-library logging levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogFormat(StrEnum):
    """Supported output contracts for the later logging adapter."""

    JSON = "json"
    CONSOLE = "console"


class SecretSetting(StrEnum):
    """Allowlisted operational secret settings."""

    DATABASE_URL = "database_url"


class RuntimeConfiguration(StrictConfigurationModel):
    """Non-secret runtime behavior stored in safe configuration."""

    log_level: LogLevel
    log_format: LogFormat


class RuntimeOverrides(StrictConfigurationModel):
    """Partial runtime values accepted from a profile or local layer."""

    log_level: LogLevel | None = None
    log_format: LogFormat | None = None


class SecretReference(StrictConfigurationModel):
    """Stable safe reference to an externally supplied value."""

    secret_id: StableId
    setting: SecretSetting
    required: bool = True


class UserConfiguration(StrictConfigurationModel):
    """Non-secret identity for the one approved logical user."""

    user_id: UUID7


class UserScopeConfiguration(StrictConfigurationModel):
    """Explicit default user without introducing authentication or tenancy."""

    default_user_id: UUID7
    users: tuple[UserConfiguration, ...]

    @model_validator(mode="after")
    def require_one_referenced_default_user(self) -> UserScopeConfiguration:
        """Enforce ADR 0007's initial one-user scope and explicit default."""

        if len(self.users) != 1:
            raise ValueError("initial user scope must define exactly one user")
        if self.users[0].user_id != self.default_user_id:
            raise ValueError("default_user_id must reference the configured user")
        return self


class VersionedConfiguration(StrictConfigurationModel):
    """Shared version and identity metadata for tracked configuration."""

    schema_version: Literal[2]
    config_id: StableId
    config_version: PositiveInt
    effective_from: AwareDatetime

    @field_validator("effective_from")
    @classmethod
    def effective_from_must_be_utc(cls, value: datetime) -> datetime:
        """Keep equivalent effective instants canonical and unambiguous."""

        if value.utcoffset() != UTC.utcoffset(value):
            raise ValueError("effective_from must use UTC")
        return value.astimezone(UTC)


class SafeConfiguration(VersionedConfiguration):
    """Effective secret-free application configuration."""

    user_scope: UserScopeConfiguration
    runtime: RuntimeConfiguration
    secret_references: tuple[SecretReference, ...] = ()

    @model_validator(mode="after")
    def secret_references_must_be_unique(self) -> SafeConfiguration:
        """Reject ambiguous aliases for the same ID or operational setting."""

        secret_ids = [reference.secret_id for reference in self.secret_references]
        if len(secret_ids) != len(set(secret_ids)):
            raise ValueError("secret reference IDs must be unique")

        settings = [reference.setting for reference in self.secret_references]
        if len(settings) != len(set(settings)):
            raise ValueError("secret settings must be referenced at most once")

        return self


class ProfileConfiguration(VersionedConfiguration):
    """Versioned, tracked overlay selected explicitly by the operator."""

    user_scope: UserScopeConfiguration | None = None
    runtime: RuntimeOverrides | None = None
    secret_references: tuple[SecretReference, ...] | None = None


class LocalConfiguration(StrictConfigurationModel):
    """Ignored non-secret overrides limited to developer runtime behavior."""

    runtime: RuntimeOverrides | None = None


class OperationalSettings(StrictConfigurationModel):
    """Complete explicit operational input, isolated from ambient settings."""

    config_path: Path = Path("config/defaults.toml")
    profile_path: Path | None = None
    local_config_path: Path | None = None
    log_level: LogLevel | None = None
    log_format: LogFormat | None = None
    database_url: SecretStr | None = Field(default=None, repr=False)


class ResolvedSecret(StrictConfigurationModel):
    """Resolved secret retained only as a redacted Pydantic value."""

    secret_id: StableId
    value: SecretStr = Field(repr=False)


class LoadedConfiguration(StrictConfigurationModel):
    """Validated effective configuration plus audit metadata."""

    configuration: SafeConfiguration
    digest: ConfigurationDigest
    resolved_secrets: tuple[ResolvedSecret, ...] = ()

    def get_secret(self, secret_id: str) -> SecretStr | None:
        """Return a resolved secret only to an adapter that names its reference."""

        for secret in self.resolved_secrets:
            if secret.secret_id == secret_id:
                return secret.value
        return None
