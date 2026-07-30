"""Static policy checks for the Phase 1 GitHub Actions workflow."""

from __future__ import annotations

import re
from pathlib import Path

WORKFLOW_PATH = Path(".github/workflows/quality.yml")


def _workflow() -> str:
    return WORKFLOW_PATH.read_text(encoding="utf-8")


def test_external_actions_are_pinned_by_full_commit_sha() -> None:
    action_references = re.findall(r"^\s*uses:\s*(\S+)", _workflow(), flags=re.MULTILINE)

    assert action_references
    assert all(re.fullmatch(r"[^@\s]+@[0-9a-f]{40}", reference) for reference in action_references)


def test_ci_uses_managed_runtime_database_and_quality_gates() -> None:
    workflow = _workflow()

    assert "runs-on: ubuntu-24.04" in workflow
    assert "image: postgres:18.4-bookworm" in workflow
    assert 'version: "0.12.0"' in workflow
    assert 'python-version: "3.14.6"' in workflow
    assert "uv sync --locked --all-groups" in workflow
    assert "uv run ruff format --check ." in workflow
    assert "uv run ruff check ." in workflow
    assert "uv run mypy" in workflow
    assert "uv run alembic upgrade head" in workflow
    assert "uv run alembic check" in workflow
    assert "HOMESEARCH_TEST_DATABASE_URL" in workflow
    assert "uv run pytest" in workflow
    assert 'GITLEAKS_VERSION: "8.30.1"' in workflow


def test_ci_has_no_privileged_pull_request_or_deployment_trigger() -> None:
    workflow = _workflow()

    assert "pull_request_target:" not in workflow
    assert "deployment:" not in workflow
    assert "id-token: write" not in workflow
