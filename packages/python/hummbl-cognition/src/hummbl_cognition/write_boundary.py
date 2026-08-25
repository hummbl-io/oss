"""Write boundary enforcer for IssueOps.

Enforces the authorized-repo write boundary for automated issue creation.
Only repos in the authorized list may receive issues from IssueOps runs.

The boundary list is loaded from the IssueOps controller configuration
or falls back to the canonical default defined in the agentic vocabulary
doctrine (GITHUB_ACTIONS_AGENTIC_VOCABULARY.md §5.3).

Design:
  - Pure stdlib (json, pathlib, dataclasses)
  - No side effects — pure check/filter functions
  - Returns structured results for receipt logging

Reference: GITHUB_ACTIONS_AGENTIC_VOCABULARY.md §5.3 (Write Boundary)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

__all__ = [
    "WriteBoundaryError",
    "BoundaryResult",
    "WriteBoundaryEnforcer",
    "DEFAULT_AUTHORIZED_REPOS",
]

# Canonical default from GITHUB_ACTIONS_AGENTIC_VOCABULARY.md §5.3
DEFAULT_AUTHORIZED_REPOS: list[str] = [
    "hummbl-io/arbiter",
    "hummbl-io/hummbl-cognition",
    "hummbl-io/hummbl-agent",
    "hummbl-io/hummbl-governance",
    "hummbl-io/hummbl-production",
]


class WriteBoundaryError(Exception):
    """Raised when write boundary configuration is invalid."""


@dataclass
class BoundaryResult:
    """Result of a write boundary check."""

    repo: str
    authorized: bool
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"repo": self.repo, "authorized": self.authorized, "reason": self.reason}


@dataclass
class FilterResult:
    """Result of filtering a batch of candidates."""

    authorized: list[dict[str, Any]] = field(default_factory=list)
    skipped: list[dict[str, Any]] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.authorized) + len(self.skipped)


class WriteBoundaryEnforcer:
    """Enforces the authorized-repo write boundary."""

    def __init__(self, authorized_repos: list[str] | None = None) -> None:
        if authorized_repos is None:
            authorized_repos = list(DEFAULT_AUTHORIZED_REPOS)
        if not authorized_repos:
            raise WriteBoundaryError("authorized_repos must not be empty")
        self._authorized = set(authorized_repos)

    @classmethod
    def from_config(cls, config_path: str | Path) -> "WriteBoundaryEnforcer":
        """Load authorized repos from a JSON config file."""
        path = Path(config_path)
        if not path.exists():
            raise WriteBoundaryError(f"Config file not found: {path}")
        data = json.loads(path.read_text(encoding="utf-8"))
        repos = data.get("authorized_repos")
        if not repos or not isinstance(repos, list):
            raise WriteBoundaryError("Config must contain 'authorized_repos' list")
        return cls(authorized_repos=repos)

    def check_repo(self, repo_full_name: str) -> BoundaryResult:
        """Check if a repo is in the authorized write boundary."""
        if not repo_full_name or not isinstance(repo_full_name, str):
            return BoundaryResult(repo=str(repo_full_name), authorized=False, reason="invalid repo name")
        normalized = repo_full_name.strip()
        if normalized in self._authorized:
            return BoundaryResult(repo=normalized, authorized=True)
        return BoundaryResult(
            repo=normalized,
            authorized=False,
            reason=f"repo not in authorized write boundary: {sorted(self._authorized)}",
        )

    def filter_candidates(
        self, candidates: list[dict[str, Any]]
    ) -> FilterResult:
        """Filter a batch of issue candidates into authorized and skipped."""
        result = FilterResult()
        for candidate in candidates:
            repo = candidate.get("repo", "")
            check = self.check_repo(repo)
            if check.authorized:
                result.authorized.append(candidate)
            else:
                candidate_copy = dict(candidate)
                candidate_copy["_skip_reason"] = check.reason
                result.skipped.append(candidate_copy)
        return result
