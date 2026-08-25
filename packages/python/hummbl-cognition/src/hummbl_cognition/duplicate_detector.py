"""Duplicate detection engine for IssueOps.

Detects duplicate issue candidates before creation by comparing against
existing open AND closed issues in the target repo. Uses title similarity
scoring via difflib.SequenceMatcher plus keyword overlap analysis.

Design:
  - Pure stdlib (difflib, subprocess, json, dataclasses, re)
  - Fetches open and closed issues via `gh` CLI (subprocess)
  - Returns structured match results for receipt logging
  - Configurable similarity threshold (default 80%)
  - Keyword overlap boosts detection of reordered or reworded duplicates

Reference: IssueOps run receipt schema (skipped_duplicate_candidates field)
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Any

__all__ = [
    "DuplicateMatch",
    "DetectionResult",
    "DuplicateDetector",
    "DEFAULT_THRESHOLD",
    "detect_duplicates",
]

logger = logging.getLogger(__name__)

DEFAULT_THRESHOLD: float = 0.80

# Minimum token length to be considered a meaningful keyword
_MIN_KEYWORD_LEN = 3
# Stopwords excluded from keyword overlap scoring
_STOPWORDS = frozenset({
    "the", "and", "for", "are", "but", "not", "you", "all", "any", "can",
    "had", "her", "was", "one", "our", "out", "has", "have", "from", "this",
    "that", "with", "will", "your", "add", "new", "use", "using", "into",
    "via", "when", "where", "which", "what", "who", "how", "why", "its",
    "such", "than", "then", "them", "they", "their", "there", "been",
    "more", "most", "some", "only", "very", "also", "just", "like", "does",
    "did", "done", "each", "both", "few", "other", "own", "same", "so",
    "no", "nor", "too", "want", "needs", "need", "issue", "pr", "bug",
    "fix", "feat", "docs", "chore", "refactor", "ci", "test",
})


@dataclass
class DuplicateMatch:
    """A single duplicate match found in an existing issue."""

    issue_number: int
    issue_title: str
    similarity: float
    match_type: str  # "exact", "near", or "keyword"
    issue_state: str = "open"  # "open" or "closed"
    issue_url: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "issue_number": self.issue_number,
            "issue_title": self.issue_title,
            "similarity": round(self.similarity, 4),
            "match_type": self.match_type,
            "issue_state": self.issue_state,
            "issue_url": self.issue_url,
        }


@dataclass
class DetectionResult:
    """Result of duplicate detection for a single candidate."""

    candidate_title: str
    is_duplicate: bool
    matches: list[DuplicateMatch] = field(default_factory=list)
    best_similarity: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_title": self.candidate_title,
            "is_duplicate": self.is_duplicate,
            "matches": [m.to_dict() for m in self.matches],
            "best_similarity": round(self.best_similarity, 4),
        }


class DuplicateDetector:
    """Detects duplicate issue candidates against existing open and closed issues."""

    def __init__(
        self,
        threshold: float = DEFAULT_THRESHOLD,
        gh_runner: Any | None = None,
        keyword_threshold: float = 0.60,
    ) -> None:
        if not 0.0 < threshold <= 1.0:
            raise ValueError(f"threshold must be in (0, 1], got {threshold}")
        if not 0.0 < keyword_threshold <= 1.0:
            raise ValueError(f"keyword_threshold must be in (0, 1], got {keyword_threshold}")
        self._threshold = threshold
        self._keyword_threshold = keyword_threshold
        self._gh_runner = gh_runner or _default_gh_runner

    def fetch_open_issues(self, repo: str) -> list[dict[str, Any]]:
        """Fetch open issues from a repo via gh CLI.

        This method always fetches only OPEN issues, regardless of the
        configured gh_runner's default state. Use fetch_issues() for
        configurable state filtering.
        """
        if self._gh_runner is _default_gh_runner:
            return _default_gh_runner(repo, state="open")
        # Custom runners — try with state="open" kwarg, fall back to no-arg call
        try:
            return self._gh_runner(repo, state="open")
        except TypeError:
            return self._gh_runner(repo)

    def fetch_issues(self, repo: str, state: str = "all") -> list[dict[str, Any]]:
        """Fetch issues from a repo with configurable state filter.

        Args:
            repo: Full repo name (e.g. "hummbl-io/hummbl-cognition")
            state: "open", "closed", or "all" (default "all")

        Returns:
            List of issue dicts with number, title, state, url fields.
        """
        valid_states = {"open", "closed", "all"}
        if state not in valid_states:
            raise ValueError(
                f"state must be one of {sorted(valid_states)}, got {state!r}"
            )
        if self._gh_runner is _default_gh_runner:
            return _default_gh_runner(repo, state=state)
        # Custom runners — try with state kwarg, fall back to no-arg call
        try:
            return self._gh_runner(repo, state=state)
        except TypeError:
            return self._gh_runner(repo)

    @staticmethod
    def _tokenize(title: str) -> set[str]:
        """Extract meaningful keyword tokens from a title."""
        tokens = re.findall(r"[a-z0-9]+", title.lower())
        return {
            t for t in tokens
            if len(t) >= _MIN_KEYWORD_LEN and t not in _STOPWORDS
        }

    def _keyword_overlap(self, title_a: str, title_b: str) -> float:
        """Compute Jaccard overlap of meaningful keywords between two titles."""
        keywords_a = self._tokenize(title_a)
        keywords_b = self._tokenize(title_b)
        if not keywords_a or not keywords_b:
            return 0.0
        intersection = keywords_a & keywords_b
        union = keywords_a | keywords_b
        return len(intersection) / len(union) if union else 0.0

    def score_similarity(self, title_a: str, title_b: str) -> float:
        """Score similarity between two titles (0.0 to 1.0).

        Combines difflib.SequenceMatcher ratio with keyword overlap.
        The final score is the max of sequence ratio and a weighted
        combination that boosts when keyword overlap is high even if
        word order differs.
        """
        a = title_a.strip().lower()
        b = title_b.strip().lower()
        if not a or not b:
            return 0.0
        seq_ratio = SequenceMatcher(None, a, b).ratio()
        kw_overlap = self._keyword_overlap(a, b)
        # Weighted blend: 70% sequence ratio + 30% keyword overlap
        blended = 0.70 * seq_ratio + 0.30 * kw_overlap
        return max(seq_ratio, blended)

    def check_candidate(
        self,
        candidate_title: str,
        existing_issues: list[dict[str, Any]],
    ) -> DetectionResult:
        """Check a single candidate against existing issues."""
        matches: list[DuplicateMatch] = []
        best_sim = 0.0

        for issue in existing_issues:
            existing_title = issue.get("title", "")
            if not existing_title:
                continue
            sim = self.score_similarity(candidate_title, existing_title)
            if sim >= self._threshold:
                if sim >= 0.999:
                    match_type = "exact"
                elif self._keyword_overlap(candidate_title, existing_title) >= self._keyword_threshold:
                    match_type = "keyword"
                else:
                    match_type = "near"
                matches.append(
                    DuplicateMatch(
                        issue_number=issue.get("number", 0),
                        issue_title=existing_title,
                        similarity=sim,
                        match_type=match_type,
                        issue_state=issue.get("state", "open"),
                        issue_url=issue.get("url", ""),
                    )
                )
            if sim > best_sim:
                best_sim = sim

        matches.sort(key=lambda m: m.similarity, reverse=True)
        return DetectionResult(
            candidate_title=candidate_title,
            is_duplicate=len(matches) > 0,
            matches=matches,
            best_similarity=best_sim,
        )

    def filter_candidates(
        self,
        candidates: list[dict[str, Any]],
        repo: str,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Filter candidates into unique and duplicate lists.

        Returns:
            (unique_candidates, duplicate_candidates)
            Duplicate candidates have _duplicate_match appended.
        """
        existing = self.fetch_issues(repo, state="all")
        unique: list[dict[str, Any]] = []
        duplicates: list[dict[str, Any]] = []

        for candidate in candidates:
            title = candidate.get("title", "")
            result = self.check_candidate(title, existing)
            if result.is_duplicate:
                dup = dict(candidate)
                dup["_duplicate_match"] = result.to_dict()
                duplicates.append(dup)
            else:
                unique.append(candidate)

        return unique, duplicates


def _default_gh_runner(
    repo: str,
    state: str = "all",
) -> list[dict[str, Any]]:
    """Default gh CLI runner — fetches issues as JSON with state filter.

    Args:
        repo: Full repo name (e.g. "hummbl-io/hummbl-cognition")
        state: "open", "closed", or "all" (default "all")

    Returns:
        List of issue dicts with number, title, state, url fields.
    """
    import subprocess

    try:
        proc = subprocess.run(
            [
                "gh",
                "issue",
                "list",
                "--repo",
                repo,
                "--state",
                state,
                "--limit",
                "100",
                "--json",
                "number,title,state,url",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if proc.returncode != 0:
            logger.warning("gh issue list failed for %s: %s", repo, proc.stderr)
            return []
        return json.loads(proc.stdout)
    except Exception as e:
        logger.warning("gh issue list error for %s: %s", repo, e)
        return []


def detect_duplicates(
    candidates: list[dict[str, Any]],
    repo: str,
    threshold: float = DEFAULT_THRESHOLD,
    existing_issues: list[dict[str, Any]] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Convenience function: detect duplicates in a candidate list.

    If existing_issues is provided, uses them instead of fetching from gh.
    Returns (unique_candidates, duplicate_candidates).
    """
    if existing_issues is not None:
        detector = DuplicateDetector(threshold=threshold, gh_runner=lambda _repo: existing_issues)
    else:
        detector = DuplicateDetector(threshold=threshold)
    return detector.filter_candidates(candidates, repo)
