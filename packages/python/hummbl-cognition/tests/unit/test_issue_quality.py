"""Unit tests for hummbl_cognition.issue_quality."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Ensure repo root on path when run directly.
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from hummbl_cognition.issue_quality import (
    AUTO_CREATE_THRESHOLD,
    DISPOSITION_AUTO_CREATE,
    DISPOSITION_NEEDS_REVIEW,
    DISPOSITION_REJECT,
    MAX_SCORE,
    NEEDS_REVIEW_THRESHOLD,
    QualityReport,
    score_acceptance_criteria,
    score_actionable,
    score_evidence_backed,
    score_issue,
    score_non_duplicate,
    score_severity_appropriate,
    score_test_plan,
)
from hummbl_cognition.issue_quality import main as cli_main


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

HIGH_QUALITY_BODY = """\
## Evidence

Audit finding AUD-1234: test failure in tests/test_foo.py::test_bar

```
Traceback (most recent call last):
  File "test_foo.py", line 42
    assert result == expected
AssertionError
```

## Steps

1. Fix the assertion in test_foo.py
2. Update the helper in services/foo.py
3. Add a regression test

## Acceptance criteria

- `pytest tests/test_foo.py` must pass with 0 errors
- No new bandit HIGH findings

## Test plan

Run `python -m pytest tests/test_foo.py -v` and confirm green.

## Severity

Severity: high — because this blocks the release pipeline and is a regression.
"""

LOW_QUALITY_BODY = "Something is broken. Please fix it."


# ---------------------------------------------------------------------------
# Per-criterion tests
# ---------------------------------------------------------------------------


class TestEvidenceBacked:
    def test_no_evidence_scores_zero(self):
        result = score_evidence_backed("Fix thing", "Something is broken")
        assert result.score == 0
        assert result.max_score == 3

    def test_vague_reference_scores_one(self):
        result = score_evidence_backed("Fix thing", "A test failed somewhere")
        assert result.score == 1

    def test_specific_reference_scores_two(self):
        body = "test failure in test_foo.py"
        result = score_evidence_backed("Fix thing", body)
        assert result.score == 2

    def test_concrete_citations_score_three(self):
        body = "audit finding AUD-1: test_foo.py line 42 traceback error: AssertionError stderr"
        result = score_evidence_backed("Fix thing", body)
        assert result.score == 3


class TestActionable:
    def test_no_steps_scores_zero(self):
        result = score_actionable("Thing broken", "It is broken")
        assert result.score == 0

    def test_fully_specified_scores_three(self):
        body = "Steps:\n1. Fix the bug\n2. Add a test\n3. Update the docs"
        result = score_actionable("Implement fix", body)
        assert result.score == 3

    def test_partial_scores_one_or_two(self):
        body = "Please fix the bug"
        result = score_actionable("Fix thing", body)
        assert result.score in (1, 2)


class TestNonDuplicate:
    def test_no_existing_list_scores_three(self):
        result = score_non_duplicate("Title", "body", None)
        assert result.score == 3

    def test_near_identical_scores_zero(self):
        existing = [{"title": "Fix the foo bug", "body": "The foo is broken"}]
        result = score_non_duplicate("Fix the foo bug", "The foo is broken", existing)
        assert result.score == 0

    def test_distinct_scores_three(self):
        existing = [{"title": "Refactor bar module", "body": "Refactor bar for clarity"}]
        result = score_non_duplicate(
            "Fix the foo bug", "The foo is broken in tests", existing
        )
        assert result.score == 3


class TestAcceptanceCriteria:
    def test_none_present_scores_zero(self):
        result = score_acceptance_criteria("Fix thing", "It is broken")
        assert result.score == 0

    def test_clear_measurable_scores_three(self):
        body = "## Acceptance criteria\n- pytest must pass with 0 errors"
        result = score_acceptance_criteria("Fix thing", body)
        assert result.score == 3

    def test_vague_scores_one(self):
        body = "## Acceptance\nshould work"
        result = score_acceptance_criteria("Fix thing", body)
        assert result.score == 1


class TestTestPlan:
    def test_none_present_scores_zero(self):
        result = score_test_plan("Fix thing", "It is broken")
        assert result.score == 0

    def test_concrete_plan_scores_three(self):
        body = "## Test plan\nRun `python -m pytest tests/ -v` and verify expected output is green."
        result = score_test_plan("Fix thing", body)
        assert result.score == 3

    def test_mentioned_only_scores_one(self):
        body = "Run `make test`"
        result = score_test_plan("Thing", body)
        assert result.score == 1


class TestSeverityAppropriate:
    def test_missing_scores_zero(self):
        result = score_severity_appropriate("Fix thing", "It is broken")
        assert result.score == 0

    def test_present_but_unjustified_scores_one(self):
        body = "Severity: high"
        result = score_severity_appropriate("Fix thing", body)
        assert result.score == 1

    def test_present_and_justified_scores_two(self):
        body = "Severity: high because this blocks the release pipeline (regression)."
        result = score_severity_appropriate("Fix thing", body)
        assert result.score == 2


# ---------------------------------------------------------------------------
# Integration: score_issue
# ---------------------------------------------------------------------------


class TestScoreIssue:
    def test_high_quality_issue_auto_creates(self):
        report = score_issue("Fix foo regression", HIGH_QUALITY_BODY)
        assert isinstance(report, QualityReport)
        assert report.max_total == MAX_SCORE
        assert report.total >= AUTO_CREATE_THRESHOLD
        assert report.disposition == DISPOSITION_AUTO_CREATE
        assert len(report.criteria) == 6

    def test_low_quality_issue_rejected(self):
        report = score_issue("Fix something", LOW_QUALITY_BODY)
        assert report.total < NEEDS_REVIEW_THRESHOLD
        assert report.disposition == DISPOSITION_REJECT

    def test_medium_quality_needs_review(self):
        # Build a body that lands in the 10-13 band.
        body = (
            "## Evidence\n"
            "test failure in test_foo.py\n\n"
            "## Steps\n"
            "Fix the bug and add a test.\n\n"
            "## Acceptance\n"
            "should work\n\n"
            "## Checks\n"
            "Run `make test`\n\n"
            "Severity: medium\n"
        )
        report = score_issue("Fix foo bug", body)
        assert NEEDS_REVIEW_THRESHOLD <= report.total < AUTO_CREATE_THRESHOLD
        assert report.disposition == DISPOSITION_NEEDS_REVIEW

    def test_to_dict_roundtrip(self):
        report = score_issue("Fix foo regression", HIGH_QUALITY_BODY)
        d = report.to_dict()
        assert d["total"] == report.total
        assert d["disposition"] == report.disposition
        assert len(d["criteria"]) == 6
        # criteria entries are plain dicts
        assert {"name", "score", "max_score", "notes"} <= set(d["criteria"][0].keys())

    def test_duplicate_detection_lowers_score(self):
        existing = [{"title": "Fix foo regression", "body": HIGH_QUALITY_BODY}]
        report = score_issue("Fix foo regression", HIGH_QUALITY_BODY, existing)
        dup = next(c for c in report.criteria if c.name == "non_duplicate")
        assert dup.score == 0


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------


class TestCLI:
    def test_score_text_output(self, capsys):
        rc = cli_main(["score", "--title", "Fix foo regression", "--body", HIGH_QUALITY_BODY])
        captured = capsys.readouterr()
        assert rc == 0
        assert "Disposition:" in captured.out
        assert "Breakdown:" in captured.out

    def test_score_json_output(self, capsys):
        rc = cli_main(
            [
                "score",
                "--title",
                "Fix foo regression",
                "--body",
                HIGH_QUALITY_BODY,
                "--json",
            ]
        )
        captured = capsys.readouterr()
        assert rc == 0
        data = json.loads(captured.out)
        assert data["title"] == "Fix foo regression"
        assert "total" in data
        assert "disposition" in data
        assert len(data["criteria"]) == 6

    def test_score_with_existing_issues_file(self, tmp_path, capsys):
        existing = [{"title": "Fix foo regression", "body": HIGH_QUALITY_BODY}]
        path = tmp_path / "existing.json"
        path.write_text(json.dumps(existing), encoding="utf-8")
        rc = cli_main(
            [
                "score",
                "--title",
                "Fix foo regression",
                "--body",
                HIGH_QUALITY_BODY,
                "--existing-issues",
                str(path),
                "--json",
            ]
        )
        captured = capsys.readouterr()
        assert rc == 0
        data = json.loads(captured.out)
        dup = next(c for c in data["criteria"] if c["name"] == "non_duplicate")
        assert dup["score"] == 0

    def test_no_command_prints_help(self, capsys):
        with pytest.raises(SystemExit):
            cli_main([])


# ---------------------------------------------------------------------------
# Threshold sanity
# ---------------------------------------------------------------------------


def test_thresholds_are_consistent():
    assert NEEDS_REVIEW_THRESHOLD < AUTO_CREATE_THRESHOLD <= MAX_SCORE
    assert MAX_SCORE == 17
    assert AUTO_CREATE_THRESHOLD == 14
    assert NEEDS_REVIEW_THRESHOLD == 10
