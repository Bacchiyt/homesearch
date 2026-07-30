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
AreaLabel = Annotated[str, Field(min_length=1, max_length=100)]
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


class SearchLifecycle(StrEnum):
    """Configured search availability without implementing a scheduler."""

    ENABLED = "ENABLED"
    DISABLED = "DISABLED"
    PAUSED = "PAUSED"
    RETIRED = "RETIRED"


class PropertyType(StrEnum):
    """Initial source-neutral residential property categories."""

    DETACHED_HOUSE = "DETACHED_HOUSE"
    CONDOMINIUM = "CONDOMINIUM"
    OTHER_RESIDENTIAL = "OTHER_RESIDENTIAL"


class PropertyCondition(StrEnum):
    """Source-neutral new/used search criteria."""

    NEW = "NEW"
    USED = "USED"


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


class AdministrativeAreaConfiguration(StrictConfigurationModel):
    """One configurable Japanese administrative search area."""

    area_key: StableId
    prefecture: AreaLabel
    municipality: AreaLabel
    localities: tuple[AreaLabel, ...] = ()

    @field_validator("prefecture", "municipality")
    @classmethod
    def labels_must_be_trimmed(cls, value: str) -> str:
        """Reject ambiguous blank or padded administrative labels."""

        if not value.strip() or value != value.strip():
            raise ValueError("administrative labels must be non-blank and trimmed")
        return value

    @field_validator("localities")
    @classmethod
    def localities_must_be_unique_and_trimmed(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        """Use an empty tuple for a whole municipality; otherwise reject ambiguity."""

        if any(not value.strip() or value != value.strip() for value in values):
            raise ValueError("locality labels must be non-blank and trimmed")
        if len(values) != len(set(values)):
            raise ValueError("locality labels must be unique within an area")
        return values


class PriceCriteriaConfiguration(StrictConfigurationModel):
    """JPY price bounds plus an optional amount above the preferred maximum."""

    minimum_jpy: NonNegativeInt | None = None
    maximum_jpy: PositiveInt | None = None
    negotiation_margin_jpy: PositiveInt | None = None

    @model_validator(mode="after")
    def require_coherent_price_bounds(self) -> PriceCriteriaConfiguration:
        """Reject inverted bounds and a negotiation margin without a maximum."""

        if (
            self.minimum_jpy is not None
            and self.maximum_jpy is not None
            and self.minimum_jpy > self.maximum_jpy
        ):
            raise ValueError("minimum_jpy cannot exceed maximum_jpy")
        if self.negotiation_margin_jpy is not None and self.maximum_jpy is None:
            raise ValueError("negotiation_margin_jpy requires maximum_jpy")
        return self


class SearchPolicyConfiguration(StrictConfigurationModel):
    """Versioned source-neutral criteria for one configured discovery search."""

    search_id: UUID7
    search_key: StableId
    search_version: PositiveInt
    effective_from: AwareDatetime
    user_id: UUID7
    lifecycle: SearchLifecycle
    source_ids: tuple[UUID7, ...]
    areas: tuple[AdministrativeAreaConfiguration, ...]
    price: PriceCriteriaConfiguration
    property_types: tuple[PropertyType, ...]
    property_conditions: tuple[PropertyCondition, ...]
    discovery_interval_minutes: PositiveInt
    maximum_results_per_run: PositiveInt

    @field_validator("effective_from")
    @classmethod
    def effective_from_must_be_utc(cls, value: datetime) -> datetime:
        """Keep search-policy effective instants canonical and unambiguous."""

        if value.utcoffset() != UTC.utcoffset(value):
            raise ValueError("effective_from must use UTC")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def require_unambiguous_search_criteria(self) -> SearchPolicyConfiguration:
        """Reject empty or duplicate criteria before any discovery can run."""

        if not self.source_ids:
            raise ValueError("searches must reference at least one source")
        if len(self.source_ids) != len(set(self.source_ids)):
            raise ValueError("search source references must be unique")

        if not self.areas:
            raise ValueError("searches must define at least one area")
        area_keys = [area.area_key for area in self.areas]
        if len(area_keys) != len(set(area_keys)):
            raise ValueError("search area keys must be unique")

        if not self.property_types:
            raise ValueError("searches must include at least one property type")
        if len(self.property_types) != len(set(self.property_types)):
            raise ValueError("search property types must be unique")

        if not self.property_conditions:
            raise ValueError("searches must include at least one property condition")
        if len(self.property_conditions) != len(set(self.property_conditions)):
            raise ValueError("search property conditions must be unique")
        return self


class SearchRegistryConfiguration(StrictConfigurationModel):
    """Replacement-layer registry with one policy per search identity."""

    searches: tuple[SearchPolicyConfiguration, ...] = ()

    @model_validator(mode="after")
    def search_identities_must_be_unique(self) -> SearchRegistryConfiguration:
        """Reject ambiguous policy selection for a search."""

        search_ids = [search.search_id for search in self.searches]
        if len(search_ids) != len(set(search_ids)):
            raise ValueError("search IDs must be unique")
        search_keys = [search.search_key for search in self.searches]
        if len(search_keys) != len(set(search_keys)):
            raise ValueError("search keys must be unique")
        return self


class VersionedConfiguration(StrictConfigurationModel):
    """Shared version and identity metadata for tracked configuration."""

    schema_version: Literal[4]
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
    search_registry: SearchRegistryConfiguration
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

    @model_validator(mode="after")
    def search_references_must_be_valid(self) -> SafeConfiguration:
        """Resolve configured search ownership and source capabilities."""

        user_ids = {user.user_id for user in self.user_scope.users}
        sources_by_id = {source.source_id: source for source in self.source_registry.sources}

        for search in self.search_registry.searches:
            if search.user_id not in user_ids:
                raise ValueError("search user_id must reference a configured user")

            referenced_sources = []
            for source_id in search.source_ids:
                source = sources_by_id.get(source_id)
                if source is None:
                    raise ValueError("search source_ids must reference configured sources")
                referenced_sources.append(source)

            if search.lifecycle is SearchLifecycle.ENABLED:
                if any(
                    source.lifecycle is not SourceLifecycle.ENABLED for source in referenced_sources
                ):
                    raise ValueError("enabled searches require enabled sources")
                if any(
                    source.access_status is not SourceAccessStatus.APPROVED
                    for source in referenced_sources
                ):
                    raise ValueError("enabled searches require approved source access")
                if any(
                    SourceCapability.DISCOVERY not in source.capabilities
                    for source in referenced_sources
                ):
                    raise ValueError("enabled searches require source discovery capability")

        return self


class ProfileConfiguration(VersionedConfiguration):
    """Versioned, tracked overlay selected explicitly by the operator."""

    user_scope: UserScopeConfiguration | None = None
    source_registry: SourceRegistryConfiguration | None = None
    search_registry: SearchRegistryConfiguration | None = None
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
