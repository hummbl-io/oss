"""Tests for issueops_harvest module."""

import json
from pathlib import Path

import pytest

from hummbl_cognition.issueops_harvest import (
    HarvestResult,
    load_candidates,
    create_issue_via_gh,
    harvest,
)


class TestLoadCandidates:
    """Tests for load_candidates function."""

    def test_load_valid_file(self, tmp_path):
        candidates = [
            {"repo": "hummbl-io/arbiter", "title": "test issue"},
            {"repo": "hummbl-io/hummbl-governance", "title": "another issue"},
        ]
        path = tmp_path / "candidates.json"
        path.write_text(json.dumps(candidates))
        loaded = load_candidates(path)
        assert len(loaded) == 2
        assert loaded[0]["repo"] == "hummbl-io/arbiter"

    def test_load_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError, match="not found"):
            load_candidates(tmp_path / "missing.json")

    def test_load_invalid_format(self, tmp_path):
        path = tmp_path / "candidates.json"
        path.write_text(json.dumps({"not": "a list"}))
        with pytest.raises(ValueError, match="must contain a JSON array"):
            load_candidates(path)


class TestCreateIssueViaGh:
    """Tests for create_issue_via_gh function."""

    def test_dry_run(self):
        result = create_issue_via_gh(
            repo="hummbl-io/test",
            title="test issue",
            dry_run=True,
        )
        assert result["success"] is True
        assert result["dry_run"] is True
        assert result["number"] == 0


class TestHarvestDryRun:
    """Tests for harvest function in dry-run mode."""

    def test_empty_candidates(self):
        result = harvest(
            candidates=[],
            agent="devin",
            source="manual",
            dry_run=True,
        )
        assert result.total_candidates == 0
        assert result.total_created == 0
        assert len(result.errors) > 0

    def test_all_outside_boundary(self):
        candidates = [
            {"repo": "hummbl-io/unknown", "title": "test"},
        ]
        result = harvest(
            candidates=candidates,
            agent="devin",
            source="manual",
            dry_run=True,
        )
        assert result.total_created == 0
        assert len(result.issues_skipped_boundary) == 1

    def test_authorized_dry_run(self):
        candidates = [
            {"repo": "hummbl-io/arbiter", "title": "test issue"},
        ]
        result = harvest(
            candidates=candidates,
            agent="devin",
            source="manual",
            dry_run=True,
            skip_gh_fetch=True,
        )
        assert result.total_created == 1
        assert result.issues_created[0]["dry_run"] is True

    def test_duplicate_detection(self):
        candidates = [
            {"repo": "hummbl-io/arbiter", "title": "fix: existing bug"},
        ]
        existing = [{"number": 100, "title": "fix: existing bug"}]
        existing_map = {"hummbl-io/arbiter": existing}
        result = harvest(
            candidates=candidates,
            agent="devin",
            source="manual",
            dry_run=True,
            existing_issues_map=existing_map,
        )
        assert result.total_created == 0
        assert len(result.issues_skipped_duplicate) == 1

    def test_near_duplicate_detection(self):
        candidates = [
            {"repo": "hummbl-io/arbiter", "title": "security: align reporting contacts"},
        ]
        existing = [{"number": 50, "title": "security: align reporting contacts with org policy"}]
        existing_map = {"hummbl-io/arbiter": existing}
        result = harvest(
            candidates=candidates,
            agent="devin",
            source="manual",
            dry_run=True,
            duplicate_threshold=0.7,
            existing_issues_map=existing_map,
        )
        assert result.total_created == 0
        assert len(result.issues_skipped_duplicate) == 1

    def test_backpressure_limit(self):
        candidates = [
            {"repo": "hummbl-io/arbiter", "title": f"issue {i}"} for i in range(15)
        ]
        result = harvest(
            candidates=candidates,
            agent="devin",
            source="manual",
            dry_run=True,
            max_issues=5,
            skip_gh_fetch=True,
        )
        assert result.total_created == 5
        assert len(result.issues_skipped_backpressure) == 10

    def test_mixed_candidates(self):
        candidates = [
            {"repo": "hummbl-io/arbiter", "title": "unique issue"},  # created
            {"repo": "hummbl-io/arbiter", "title": "existing bug"},  # duplicate
            {"repo": "hummbl-io/unknown", "title": "unauthorized"},  # boundary skip
        ]
        existing = [{"number": 1, "title": "existing bug"}]
        existing_map = {"hummbl-io/arbiter": existing}
        result = harvest(
            candidates=candidates,
            agent="devin",
            source="manual",
            dry_run=True,
            existing_issues_map=existing_map,
        )
        assert result.total_candidates == 3
        assert result.total_created == 1
        assert len(result.issues_skipped_duplicate) == 1
        assert len(result.issues_skipped_boundary) == 1

    def test_all_duplicates(self):
        candidates = [
            {"repo": "hummbl-io/arbiter", "title": "existing issue"},
        ]
        existing = [{"number": 1, "title": "existing issue"}]
        existing_map = {"hummbl-io/arbiter": existing}
        result = harvest(
            candidates=candidates,
            agent="devin",
            source="manual",
            dry_run=True,
            existing_issues_map=existing_map,
        )
        assert result.total_created == 0
        assert len(result.issues_skipped_duplicate) == 1


class TestHarvestResult:
    """Tests for HarvestResult dataclass."""

    def test_totals(self):
        result = HarvestResult(
            total_candidates=10,
            issues_created=[{"number": 1}, {"number": 2}],
            issues_skipped_duplicate=[{"title": "dup"}],
            issues_skipped_boundary=[{"title": "boundary"}],
            issues_skipped_backpressure=[{"title": "pressure"}],
        )
        assert result.total_created == 2
        assert result.total_skipped == 3

    def test_to_dict(self):
        result = HarvestResult(
            agent="devin",
            source="manual",
            total_candidates=5,
            dry_run=True,
        )
        d = result.to_dict()
        assert d["agent"] == "devin"
        assert d["dry_run"] is True
        assert d["total_candidates"] == 5
