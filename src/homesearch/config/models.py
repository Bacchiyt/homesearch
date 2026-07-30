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
    NonNegativeInt,
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


class SourceLifecycle(StrEnum):
    """Configured source availability independent of adapter implementation."""

    ENABLED = "ENABLED"
    DISABLED = "DISABLED"
    PAUSED = "PAUSED"
    RETIRED = "RETIRED"


class SourceAccessStatus(StrEnum):
    """Recorded Gate B assessment outcome represented by safe configuration."""

    NOT_ASSESSED = "NOT_ASSESSED"
    APPROVED = "APPROVED"
    DISALLOWED = "DISALLOWED"


class SourceCapability(StrEnum):
    """Neutral capabilities that a later source adapter may implement."""

    DISCOVERY = "DISCOVERY"
    DETAIL_FETCH = "DETAIL_FETCH"
    STATUS_CHECK = "STATUS_CHECK"
    MANUAL_IMPORT = "MANUAL_IMPORT"


class CaptureMode(StrEnum):
    """Policy-controlled evidence capture vocabulary from ADR 0008."""

    FULL_PAYLOAD = "FULL_PAYLOAD"
    SANITIZED_PAYLOAD = "SANITIZED_PAYLOAD"
    RELEVANT_FRAGMENTS = "RELEVANT_FRAGMENTS"
    STRUCTURED_FACTS_ONLY = "STRUCTURED_FACTS_ONLY"
    METADATA_ONLY = "METADATA_ONLY"
    TRANSIENT = "TRANSIENT"


class RawStorageAdapter(StrEnum):
    """Phase-appropriate storage choices without selecting a hosted provider."""

    NONE = "NONE"
    FILESYSTEM = "FILESYSTEM"


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


class SourceRequestPolicyConfiguration(StrictConfigurationModel):
    """Bounded network-request settings; scheduling remains out of scope."""

    timeout_seconds: PositiveInt
    minimum_interval_seconds: NonNegativeInt
    maximum_concurrency: PositiveInt
    maximum_requests_per_run: PositiveInt


class SourceCapturePolicyConfiguration(StrictConfigurationModel):
    """Capture, raw-retention, and storage settings owned by a source version."""

    capture_mode: CaptureMode
    storage_adapter: RawStorageAdapter
    raw_payload_retention_days: NonNegativeInt

    @model_validator(mode="after")
    def require_compatible_capture_and_storage(self) -> SourceCapturePolicyConfiguration:
        """Reject storage settings that contradict the selected capture mode."""

        stored_modes = {
            CaptureMode.FULL_PAYLOAD,
            CaptureMode.SANITIZED_PAYLOAD,
            CaptureMode.RELEVANT_FRAGMENTS,
        }
        stores_raw_payload = self.capture_mode in stored_modes

        if stores_raw_payload and self.storage_adapter is RawStorageAdapter.NONE:
            raise ValueError("stored capture modes require a storage adapter")
        if not stores_raw_payload and self.storage_adapter is not RawStorageAdapter.NONE:
            raise ValueError("non-stored capture modes cannot select a storage adapter")
        if not stores_raw_payload and self.raw_payload_retention_days != 0:
            raise ValueError("non-stored capture modes require zero raw-payload retention")
        return self


class SourcePolicyConfiguration(StrictConfigurationModel):
    """Versioned non-secret policy for one source identity."""

    source_id: UUID7
    source_key: StableId
    source_version: PositiveInt
    effective_from: AwareDatetime
    lifecycle: SourceLifecycle
    access_status: SourceAccessStatus
    access_assessment_reference: StableId | None = None
    capabilities: tuple[SourceCapability, ...] = ()
    request_policy: SourceRequestPolicyConfiguration | None = None
    capture_policy: SourceCapturePolicyConfiguration

    @field_validator("effective_from")
    @classmethod
    def effective_from_must_be_utc(cls, value: datetime) -> datetime:
        """Keep source-policy effective instants canonical and unambiguous."""

        if value.utcoffset() != UTC.utcoffset(value):
            raise ValueError("effective_from must use UTC")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def require_safe_source_enablement(self) -> SourcePolicyConfiguration:
        """Require approval evidence and bounded access before enabling a source."""

        if len(self.capabilities) != len(set(self.capabilities)):
            raise ValueError("source capabilities must be unique")

        if (
            self.access_status is SourceAccessStatus.APPROVED
            and self.access_assessment_reference is None
        ):
            raise ValueError("approved source access requires an assessment reference")

        if self.lifecycle is SourceLifecycle.ENABLED:
            if self.access_status is not SourceAccessStatus.APPROVED:
                raise ValueError("enabled source access must be approved")
            if not self.capabilities:
                raise ValueError("enabled sources must declare at least one capability")

            network_capabilities = {
                SourceCapability.DISCOVERY,
                SourceCapability.DETAIL_FETCH,
                SourceCapability.STATUS_CHECK,
            }
            if network_capabilities.intersection(self.capabilities) and self.request_policy is None:
                raise ValueError("enabled network sources require a request policy")

        return self


class SourceRegistryConfiguration(StrictConfigurationModel):
    """Replacement-layer registry with one policy per source identity."""

    sources: tuple[SourcePolicyConfiguration, ...] = ()

    @model_validator(mode="after")
    def source_identities_must_be_unique(self) -> SourceRegistryConfiguration:
        """Reject ambiguous policy selection for a source."""

        source_ids = [source.source_id for source in self.sources]
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("source IDs must be unique")
        source_keys = [source.source_key for source in self.sources]
        if len(source_keys) != len(set(source_keys)):
            raise ValueError("source keys must be unique")
        return self


class VersionedConfiguration(StrictConfigurationModel):
    """Shared version and identity metadata for tracked configuration."""

    schema_version: Literal[3]
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
    source_registry: SourceRegistryConfiguration
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
    source_registry: SourceRegistryConfiguration | None = None
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
