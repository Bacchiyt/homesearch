"""Checksum-verified synthetic JSON source adapter with no network behavior."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any
from uuid import UUID

from homesearch.application.ingestion import (
    FactValueState,
    NormalizedIngestionResult,
    ObservationOutcome,
    ParseResult,
    SourceFactInput,
    SourceTransport,
)
from homesearch.config.models import CaptureMode

_PRICE_PATTERN = re.compile(r"^(?P<man>[1-9][0-9]*)万円$")
_STATUS_VALUES = {"掲載中": "ACTIVE"}


class FixtureIntegrityError(RuntimeError):
    """A fixture manifest or payload failed safe deterministic validation."""


class FixtureSourceAdapter:
    """Read one synthetic fixture set and normalize its listing evidence."""

    def __init__(
        self,
        manifest_path: Path,
        *,
        source_id: UUID,
        source_key: str,
    ) -> None:
        self._manifest_path = manifest_path
        self._source_id = source_id
        self._source_key = source_key

    @property
    def source_id(self) -> UUID:
        return self._source_id

    @property
    def source_key(self) -> str:
        return self._source_key

    @property
    def transport(self) -> SourceTransport:
        return SourceTransport.FIXTURE

    @property
    def adapter_name(self) -> str:
        return "synthetic-json-fixture"

    @property
    def adapter_version(self) -> str:
        return "1"

    def ingest(self, reference: str) -> NormalizedIngestionResult:
        manifest = self._read_json(self._manifest_path, label="fixture manifest")
        if manifest.get("manifest_version") != 1:
            raise FixtureIntegrityError("fixture manifest version is unsupported")
        provenance = manifest.get("provenance")
        if (
            not isinstance(provenance, dict)
            or provenance.get("origin") != "synthetic"
            or provenance.get("live_source") is not False
        ):
            raise FixtureIntegrityError(
                "fixture provenance must identify synthetic non-live evidence"
            )
        fixtures = manifest.get("fixtures")
        if not isinstance(fixtures, dict):
            raise FixtureIntegrityError("fixture manifest has no fixture registry")
        entry = fixtures.get(reference)
        if not isinstance(entry, dict):
            raise FixtureIntegrityError(f"fixture reference is not registered: {reference}")

        relative_path = self._safe_relative_path(entry.get("payload_path"))
        payload_path = self._manifest_path.parent / relative_path
        try:
            payload_bytes = payload_path.read_bytes()
        except OSError as exc:
            raise FixtureIntegrityError(
                f"fixture payload cannot be read: {relative_path.as_posix()}"
            ) from exc

        expected_checksum = self._required_string(entry, "sha256")
        actual_checksum = hashlib.sha256(payload_bytes).hexdigest()
        if actual_checksum != expected_checksum:
            raise FixtureIntegrityError(f"fixture checksum mismatch: {relative_path.as_posix()}")

        try:
            payload = json.loads(payload_bytes)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise FixtureIntegrityError(
                f"fixture payload is not valid UTF-8 JSON: {relative_path.as_posix()}"
            ) from exc
        if not isinstance(payload, dict) or payload.get("schema_version") != 1:
            raise FixtureIntegrityError("fixture payload schema version is unsupported")

        listing = payload.get("listing")
        if not isinstance(listing, dict):
            raise FixtureIntegrityError("fixture payload has no listing object")

        source_external_id = self._required_string(payload, "source_external_id")
        canonical_url = self._required_string(payload, "canonical_url")
        observed_at = self._utc_datetime(self._required_string(payload, "observed_at"))
        headline = self._required_string(listing, "headline")
        raw_price = self._required_string(listing, "price")
        address = self._required_string(listing, "address")
        raw_status = self._required_string(listing, "status")
        price_match = _PRICE_PATTERN.fullmatch(raw_price)
        if price_match is None:
            raise FixtureIntegrityError("fixture price does not match the synthetic schema")
        normalized_status = _STATUS_VALUES.get(raw_status)
        if normalized_status is None:
            raise FixtureIntegrityError("fixture status does not match the synthetic schema")

        facts = (
            SourceFactInput(
                fact_key="headline",
                fact_type="HEADLINE",
                field_path="listing.headline",
                value_state=FactValueState.PRESENT,
                raw_value=headline,
                normalized_value=headline,
                language="ja",
            ),
            SourceFactInput(
                fact_key="price",
                fact_type="PRICE",
                field_path="listing.price",
                value_state=FactValueState.PRESENT,
                raw_value=raw_price,
                normalized_value={
                    "amount": int(price_match.group("man")) * 10_000,
                    "currency": "JPY",
                },
                language="ja",
                unit="JPY",
            ),
            SourceFactInput(
                fact_key="address",
                fact_type="ADDRESS",
                field_path="listing.address",
                value_state=FactValueState.PRESENT,
                raw_value=address,
                normalized_value={"full_text": address},
                language="ja",
            ),
            SourceFactInput(
                fact_key="source-status",
                fact_type="SOURCE_STATUS",
                field_path="listing.status",
                value_state=FactValueState.PRESENT,
                raw_value=raw_status,
                normalized_value=normalized_status,
                language="ja",
            ),
        )

        return NormalizedIngestionResult(
            reference=reference,
            source_external_id=source_external_id,
            source_listing_key=f"external-id:{source_external_id}",
            canonical_url=canonical_url,
            observed_at=observed_at,
            requested_url=canonical_url,
            final_url=canonical_url,
            outcome=ObservationOutcome.SUCCESS,
            page_classification="LISTING_DETAIL",
            capture_mode=CaptureMode.FULL_PAYLOAD,
            content_checksum=f"sha256:{actual_checksum}",
            content_size=len(payload_bytes),
            media_type=self._required_string(entry, "media_type"),
            replay_eligible=True,
            storage_adapter="FIXTURE",
            storage_key=relative_path.as_posix(),
            retention_policy_reference=self._required_string(
                entry,
                "retention_policy_reference",
            ),
            compliance_reference=self._required_string(entry, "compliance_reference"),
            parser_name="synthetic-listing-json",
            parser_version="1",
            parser_schema_version=1,
            parse_result=ParseResult.SUCCESS,
            facts=facts,
        )

    @staticmethod
    def _read_json(path: Path, *, label: str) -> dict[str, Any]:
        try:
            document = json.loads(path.read_bytes())
        except OSError as exc:
            raise FixtureIntegrityError(f"{label} cannot be read") from exc
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise FixtureIntegrityError(f"{label} is not valid UTF-8 JSON") from exc
        if not isinstance(document, dict):
            raise FixtureIntegrityError(f"{label} must contain a JSON object")
        return document

    @staticmethod
    def _safe_relative_path(value: object) -> PurePosixPath:
        if not isinstance(value, str):
            raise FixtureIntegrityError("fixture payload path is missing")
        path = PurePosixPath(value)
        if path.is_absolute() or ".." in path.parts or path.as_posix() != value:
            raise FixtureIntegrityError("fixture payload path must be a safe relative path")
        return path

    @staticmethod
    def _required_string(document: dict[str, Any], key: str) -> str:
        value = document.get(key)
        if not isinstance(value, str) or not value.strip() or value != value.strip():
            raise FixtureIntegrityError(f"fixture field is missing or invalid: {key}")
        return value

    @staticmethod
    def _utc_datetime(value: str) -> datetime:
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise FixtureIntegrityError("fixture observed_at is invalid") from exc
        if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
            raise FixtureIntegrityError("fixture observed_at must use UTC")
        return parsed.astimezone(UTC)
