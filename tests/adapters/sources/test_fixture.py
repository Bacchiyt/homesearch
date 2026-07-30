"""Tests for the deterministic non-live fixture source adapter."""

from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID

import pytest

from homesearch.adapters.sources import FixtureIntegrityError, FixtureSourceAdapter
from homesearch.application import FactValueState, ObservationOutcome, ParseResult

FIXTURE_DIRECTORY = Path("tests/fixtures/ingestion")
SOURCE_ID = UUID("019fb5f4-cf78-7c5f-85f5-7c8d8dfe7bb9")


def _adapter(manifest_path: Path | None = None) -> FixtureSourceAdapter:
    return FixtureSourceAdapter(
        manifest_path or FIXTURE_DIRECTORY / "manifest.json",
        source_id=SOURCE_ID,
        source_key="synthetic-fixture",
    )


def test_fixture_adapter_verifies_and_normalizes_synthetic_evidence() -> None:
    result = _adapter().ingest("listing-001")

    assert result.outcome is ObservationOutcome.SUCCESS
    assert result.parse_result is ParseResult.SUCCESS
    assert result.source_external_id == "fixture-listing-001"
    assert result.source_listing_key == "external-id:fixture-listing-001"
    assert result.content_checksum == (
        "sha256:f263ee911c8a5aeaade5a5bb58840cd7e5a4623cfac994fdacfb389bd92bac1c"
    )
    assert result.storage_key == "listing-001.json"
    assert result.replay_eligible is True
    assert [fact.fact_key for fact in result.facts] == [
        "headline",
        "price",
        "address",
        "source-status",
    ]
    assert all(fact.value_state is FactValueState.PRESENT for fact in result.facts)
    assert result.facts[1].normalized_value == {
        "amount": 42_800_000,
        "currency": "JPY",
    }
    assert result.facts[3].normalized_value == "ACTIVE"


def test_fixture_adapter_rejects_checksum_mismatch_without_exposing_body(
    tmp_path: Path,
) -> None:
    fixture_path = tmp_path / "listing-001.json"
    fixture_path.write_text('{"not": "the registered payload"}\n', encoding="utf-8")
    manifest = json.loads((FIXTURE_DIRECTORY / "manifest.json").read_text(encoding="utf-8"))
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False),
        encoding="utf-8",
    )

    with pytest.raises(FixtureIntegrityError, match="checksum mismatch") as error:
        _adapter(manifest_path).ingest("listing-001")

    assert "registered payload" not in str(error.value)


def test_fixture_adapter_rejects_manifest_that_claims_live_provenance(
    tmp_path: Path,
) -> None:
    manifest = json.loads((FIXTURE_DIRECTORY / "manifest.json").read_text(encoding="utf-8"))
    manifest["provenance"]["live_source"] = True
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False),
        encoding="utf-8",
    )

    with pytest.raises(FixtureIntegrityError, match="synthetic non-live evidence"):
        _adapter(manifest_path).ingest("listing-001")
