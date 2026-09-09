"""R6: Review coverage matrix — track what each review covered, dedup.

When multiple agents review the same PR, this module tracks which aspects
each review covered (security, logic, tests, docs, etc.) and identifies
uncovered areas. This prevents 3 agents all reviewing lint while nobody
reviews the logic.

Coverage data is stored in a JSON file per PR and can be queried via
the CLI or MCP server.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from hummbl_gitops.protocol import REVIEW_ASPECTS


@dataclass
class ReviewCoverage:
    """Coverage matrix for a single PR."""

    pr_number: int
    reviews: list[dict] = field(default_factory=list)  # [{agent, aspect, timestamp}]

    @property
    def covered_aspects(self) -> set[str]:
        return {r["aspect"] for r in self.reviews if r.get("aspect") in REVIEW_ASPECTS}

    @property
    def uncovered_aspects(self) -> set[str]:
        return REVIEW_ASPECTS - self.covered_aspects

    def add_review(self, agent: str, aspect: str, timestamp: str = "") -> None:
        self.reviews.append({
            "agent": agent,
            "aspect": aspect,
            "timestamp": timestamp,
        })

    def summary(self) -> str:
        lines = [f"Review coverage: PR #{self.pr_number}"]
        if not self.reviews:
            lines.append("  No reviews recorded.")
            return "\n".join(lines)

        # Group by aspect
        by_aspect: dict[str, list[str]] = {}
        for r in self.reviews:
            aspect = r["aspect"]
            by_aspect.setdefault(aspect, []).append(r["agent"])

        for aspect in sorted(REVIEW_ASPECTS):
            agents = by_aspect.get(aspect, [])
            if agents:
                lines.append(f"  {aspect}: {', '.join(agents)}")
            else:
                lines.append(f"  {aspect}: (uncovered)")

        uncovered = self.uncovered_aspects
        if uncovered:
            lines.append(f"\n  Uncovered: {', '.join(sorted(uncovered))}")
        else:
            lines.append("\n  All aspects covered.")

        return "\n".join(lines)

    def to_json(self) -> str:
        return json.dumps({
            "pr_number": self.pr_number,
            "reviews": self.reviews,
        }, indent=2)

    @classmethod
    def from_json(cls, data: str) -> "ReviewCoverage":
        d = json.loads(data)
        return cls(pr_number=d["pr_number"], reviews=d.get("reviews", []))


def _coverage_file(pr_number: int, base_dir: Optional[Path] = None) -> Path:
    """Get the coverage file path for a PR.

    Args:
        pr_number: PR number.
        base_dir: Base directory for coverage data. Defaults to HUMMBL_GITOPS_STATE_DIR
                  env var or ~/.local/share/hummbl-gitops/.
    """
    if base_dir is None:
        env_dir = os.environ.get("HUMMBL_GITOPS_STATE_DIR")
        if env_dir:
            base_dir = Path(env_dir)
        else:
            base_dir = Path.home() / ".local" / "share" / "hummbl-gitops"
    coverage_dir = base_dir / "review-coverage"
    coverage_dir.mkdir(parents=True, exist_ok=True)
    return coverage_dir / f"pr-{pr_number}.json"


def get_coverage(pr_number: int, base_dir: Optional[Path] = None) -> ReviewCoverage:
    """Load coverage matrix for a PR."""
    f = _coverage_file(pr_number, base_dir)
    if not f.exists():
        return ReviewCoverage(pr_number=pr_number)
    return ReviewCoverage.from_json(f.read_text())


def save_coverage(coverage: ReviewCoverage, base_dir: Optional[Path] = None) -> None:
    """Save coverage matrix for a PR."""
    f = _coverage_file(coverage.pr_number, base_dir)
    f.write_text(coverage.to_json())


def record_review(
    pr_number: int, agent: str, aspect: str, timestamp: str = "", base_dir: Optional[Path] = None
) -> ReviewCoverage:
    """Record a review claim and return updated coverage."""
    coverage = get_coverage(pr_number, base_dir)
    coverage.add_review(agent, aspect, timestamp)
    save_coverage(coverage, base_dir)
    return coverage
