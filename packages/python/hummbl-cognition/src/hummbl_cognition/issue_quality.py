"""Issue quality rubric scorer for scheduled harvests.

Scores a generated issue body against the rubric defined in
``docs/operations/ISSUE_QUALITY_RUBRIC.md``.

Criteria (total 0-17):
  - Evidence-backed (0-3)
  - Actionable (0-3)
  - Non-duplicate (0-3)
  - Acceptance criteria (0-3)
  - Test plan (0-3)
  - Severity appropriate (0-2)

Thresholds:
  - >= 14  -> auto-create
  - 10-13  -> needs-review
  - < 10   -> reject

Usage (CLI):

    python -m hummbl_cognition.issue_quality score --title "..." --body "..."
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from typing import Iterable

# ---------------------------------------------------------------------------
# Rubric constants
# ---------------------------------------------------------------------------

MAX_SCORE: int = 17
AUTO_CREATE_THRESHOLD: int = 14
NEEDS_REVIEW_THRESHOLD: int = 10

DISPOSITION_AUTO_CREATE = "auto-create"
DISPOSITION_NEEDS_REVIEW = "needs-review"
DISPOSITION_REJECT = "reject"

# Heuristic markers used to detect evidence citations in the issue body.
_EVIDENCE_MARKERS = (
    "audit",
    "finding",
    "test failure",
    "test failed",
    "log",
    "traceback",
    "error:",
    "exception",
    "stderr",
    "stdout",
    "line ",
    "py:",
    ".py",
    "stack trace",
    "assert",
    "pytest",
    "bandit",
    "semgrep",
)

# Markers that suggest the body describes concrete, agent-completable steps.
_ACTIONABLE_MARKERS = (
    "step",
    "implement",
    "add",
    "fix",
    "update",
    "refactor",
    "create",
    "replace",
    "remove",
    "migrate",
    "wire",
    "configure",
)

# Markers for acceptance-criteria sections.
_ACCEPTANCE_MARKERS = (
    "acceptance criteria",
    "acceptance",
    "done when",
    "definition of done",
    "pass when",
    "pass/fail",
    "pass condition",
    "success criteria",
)

# Markers for test-plan sections.
_TEST_PLAN_MARKERS = (
    "test plan",
    "verification",
    "verify",
    "pytest",
    "run tests",
    "test command",
    "expected output",
    "repro",
    "reproduce",
)

_SEVERITY_PATTERN = re.compile(
    r"\b(severity|priority)\b[:\s-]*\b(critical|high|medium|low|p0|p1|p2|p3|s0|s1|s2|s3)\b",
    re.IGNORECASE,
)

_SEVERITY_JUSTIFICATION_MARKERS = (
    "because",
    "due to",
    "justified",
    "reason",
    "impact",
    "affects",
    "blocks",
    "regression",
    "data loss",
    "security",
    "outage",
)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class CriterionScore:
    """Score for a single rubric criterion."""

    name: str
    score: int
    max_score: int
    notes: str = ""


@dataclass
class QualityReport:
    """Full quality report for a scored issue."""

    title: str
    total: int
    max_total: int
    disposition: str
    criteria: list[CriterionScore] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "total": self.total,
            "max_total": self.max_total,
            "disposition": self.disposition,
            "criteria": [asdict(c) for c in self.criteria],
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _normalize(text: str) -> str:
    return (text or "").strip().lower()


def _count_markers(text: str, markers: Iterable[str]) -> int:
    lowered = _normalize(text)
    return sum(1 for marker in markers if marker in lowered)


def _has_section(body: str, markers: Iterable[str]) -> bool:
    return _count_markers(body, markers) > 0


def _title_similarity(a: str, b: str) -> float:
    """Jaccard similarity over whitespace tokens of two titles."""
    a_tokens = set(_normalize(a).split())
    b_tokens = set(_normalize(b).split())
    if not a_tokens or not b_tokens:
        return 0.0
    return len(a_tokens & b_tokens) / len(a_tokens | b_tokens)


def _body_similarity(a: str, b: str) -> float:
    """Jaccard similarity over whitespace tokens of two bodies."""
    a_tokens = set(_normalize(a).split())
    b_tokens = set(_normalize(b).split())
    if not a_tokens or not b_tokens:
        return 0.0
    return len(a_tokens & b_tokens) / len(a_tokens | b_tokens)


# ---------------------------------------------------------------------------
# Per-criterion scorers
# ---------------------------------------------------------------------------


def score_evidence_backed(title: str, body: str) -> CriterionScore:
    text = f"{title}\n{body}"
    hits = _count_markers(text, _EVIDENCE_MARKERS)
    if hits >= 3:
        return CriterionScore("evidence_backed", 3, 3, "concrete citations present")
    if hits == 2:
        return CriterionScore(
            "evidence_backed", 2, 3, "specific reference but incomplete"
        )
    if hits == 1:
        return CriterionScore("evidence_backed", 1, 3, "vague reference")
    return CriterionScore("evidence_backed", 0, 3, "no evidence cited")


def score_actionable(title: str, body: str) -> CriterionScore:
    text = f"{title}\n{body}"
    hits = _count_markers(text, _ACTIONABLE_MARKERS)
    has_steps = bool(re.search(r"^\s*[-*\d]+\.?\s+\S", body, re.MULTILINE))
    if hits >= 3 and has_steps:
        return CriterionScore("actionable", 3, 3, "fully specified; agent can start")
    if hits >= 2:
        return CriterionScore("actionable", 2, 3, "clear steps but missing detail")
    if hits >= 1:
        return CriterionScore("actionable", 1, 3, "direction implied but ambiguous")
    return CriterionScore("actionable", 0, 3, "no clear next step")


def score_non_duplicate(
    title: str,
    body: str,
    existing_issues: list[dict] | None = None,
) -> CriterionScore:
    if not existing_issues:
        return CriterionScore(
            "non_duplicate",
            3,
            3,
            "no existing-issue list supplied; assumed novel (flag for review)",
        )
    best = 0.0
    for issue in existing_issues:
        ex_title = issue.get("title", "")
        ex_body = issue.get("body", "")
        sim = max(
            _title_similarity(title, ex_title),
            _body_similarity(body, ex_body),
        )
        if sim > best:
            best = sim
    if best >= 0.8:
        return CriterionScore(
            "non_duplicate", 0, 3, f"near-identical to existing (sim={best:.2f})"
        )
    if best >= 0.5:
        return CriterionScore("non_duplicate", 1, 3, f"likely overlap (sim={best:.2f})")
    if best >= 0.2:
        return CriterionScore(
            "non_duplicate", 2, 3, f"partial overlap (sim={best:.2f})"
        )
    return CriterionScore("non_duplicate", 3, 3, "no overlap with existing issues")


def score_acceptance_criteria(title: str, body: str) -> CriterionScore:
    has_section = _has_section(body, _ACCEPTANCE_MARKERS)
    has_list = bool(re.search(r"^\s*[-*\d]+\.?\s+\S", body, re.MULTILINE))
    measurable = bool(
        re.search(
            r"\b(must|should|shall|will)\b.*\b(pass|fail|return|equal|match|exit|0 errors|green)",
            body,
            re.IGNORECASE,
        )
    )
    if has_section and measurable:
        return CriterionScore("acceptance_criteria", 3, 3, "clear measurable pass/fail")
    if has_section and has_list:
        return CriterionScore("acceptance_criteria", 2, 3, "present but incomplete")
    if has_section or has_list:
        return CriterionScore("acceptance_criteria", 1, 3, "vague criteria")
    return CriterionScore("acceptance_criteria", 0, 3, "none present")


def score_test_plan(title: str, body: str) -> CriterionScore:
    has_section = _has_section(body, _TEST_PLAN_MARKERS)
    has_command = bool(re.search(r"`[^`]+`|python -m |pytest |npm |make ", body))
    has_expected = _count_markers(body, ("expected output", "expected", "verify")) > 0
    if has_section and (has_command or has_expected):
        return CriterionScore("test_plan", 3, 3, "concrete verification plan")
    if has_section:
        return CriterionScore("test_plan", 2, 3, "specified but incomplete")
    if has_command or has_expected:
        return CriterionScore("test_plan", 1, 3, "mentioned but unspecified")
    return CriterionScore("test_plan", 0, 3, "none present")


def score_severity_appropriate(title: str, body: str) -> CriterionScore:
    text = f"{title}\n{body}"
    has_severity = bool(_SEVERITY_PATTERN.search(text))
    has_justification = _count_markers(text, _SEVERITY_JUSTIFICATION_MARKERS) > 0
    if has_severity and has_justification:
        return CriterionScore(
            "severity_appropriate", 2, 2, "severity present and justified"
        )
    if has_severity:
        return CriterionScore(
            "severity_appropriate", 1, 2, "severity present but weakly justified"
        )
    return CriterionScore(
        "severity_appropriate", 0, 2, "severity missing or unjustified"
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def score_issue(
    title: str,
    body: str,
    existing_issues: list[dict] | None = None,
) -> QualityReport:
    """Score an issue against the quality rubric.

    Args:
        title: Issue title.
        body: Issue body (markdown).
        existing_issues: Optional list of dicts with ``title``/``body`` keys
            for open issues, used for the non-duplicate criterion.

    Returns:
        A :class:`QualityReport` with total, disposition, and per-criterion
        breakdown.
    """
    criteria = [
        score_evidence_backed(title, body),
        score_actionable(title, body),
        score_non_duplicate(title, body, existing_issues),
        score_acceptance_criteria(title, body),
        score_test_plan(title, body),
        score_severity_appropriate(title, body),
    ]
    total = sum(c.score for c in criteria)
    if total >= AUTO_CREATE_THRESHOLD:
        disposition = DISPOSITION_AUTO_CREATE
    elif total >= NEEDS_REVIEW_THRESHOLD:
        disposition = DISPOSITION_NEEDS_REVIEW
    else:
        disposition = DISPOSITION_REJECT
    return QualityReport(
        title=title,
        total=total,
        max_total=MAX_SCORE,
        disposition=disposition,
        criteria=criteria,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m hummbl_cognition.issue_quality",
        description="Score generated issues against the issue quality rubric.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    score_p = sub.add_parser("score", help="Score a single issue.")
    score_p.add_argument("--title", required=True, help="Issue title.")
    score_p.add_argument("--body", required=True, help="Issue body (markdown).")
    score_p.add_argument(
        "--existing-issues",
        default=None,
        help="Path to a JSON file with existing open issues (list of {title, body}).",
    )
    score_p.add_argument(
        "--json",
        action="store_true",
        help="Emit the report as JSON.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "score":
        existing = None
        if args.existing_issues:
            with open(args.existing_issues, "r", encoding="utf-8") as fh:
                existing = json.load(fh)
        report = score_issue(args.title, args.body, existing)
        if args.json:
            print(json.dumps(report.to_dict(), indent=2))
        else:
            print(f"Issue: {report.title}")
            print(f"Total: {report.total}/{report.max_total}")
            print(f"Disposition: {report.disposition}")
            print("Breakdown:")
            for c in report.criteria:
                print(f"  - {c.name}: {c.score}/{c.max_score} ({c.notes})")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
