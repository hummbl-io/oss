"""Bus message types and protocol constants for the gitops loop.

All message types are non-privileged (STATUS-class) and can be posted by any
authenticated agent. The bridge accepts arbitrary type strings, so these are
convention, not schema-enforced.

Message bodies use key=value pairs separated by spaces, matching the existing
bus lexicon convention (see hummbl-bus package).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# --- Message types ---

# Forward (local -> remote)
REVIEW_CLAIMED = "REVIEW_CLAIMED"  # agent claims a review aspect on a PR
REVIEW_COVERED = "REVIEW_COVERED"  # agent reports what aspects a review covered

# Return (remote -> local)
CI_COMPLETED = "CI_COMPLETED"      # CI watcher reports PR CI pass/fail
MAIN_MOVED = "MAIN_MOVED"          # origin/main advanced; branches may be stale
RECEIPT_VERIFIED = "RECEIPT_VERIFIED"  # CI receipt pulled and verified (or MISMATCH)
REBASE_AVAILABLE = "REBASE_AVAILABLE"  # stale branch can be cleanly rebased
REBASE_CONFLICTS = "REBASE_CONFLICTS"  # stale branch has merge conflicts
REBASE_DONE = "REBASE_DONE"        # branch rebased and force-pushed

# --- Review aspects (for coverage matrix) ---

REVIEW_ASPECTS = frozenset({
    "security",    # security implications, attack surface, secrets
    "logic",       # correctness, edge cases, algorithmic soundness
    "tests",       # test coverage, test quality, missing tests
    "docs",        # documentation accuracy, completeness
    "style",       # code style, naming, readability
    "ci",          # CI config, workflow correctness, check names
    "performance", # performance implications, resource usage
    "breaking",    # breaking changes, API/contract compatibility
})


@dataclass(frozen=True)
class ReviewClaim:
    """A claim by an agent to review a specific aspect of a PR."""

    pr_number: int
    aspect: str
    agent: str
    host: str

    def to_bus_message(self) -> str:
        return (
            f"host={self.host} pr={self.pr_number} aspect={self.aspect} "
            f"agent={self.agent} action=claimed"
        )


@dataclass(frozen=True)
class CICompletion:
    """CI completion event for a PR."""

    pr_number: int
    result: str  # "PASS" or "FAIL"
    checks_total: int
    checks_passed: int
    checks_failed: int
    host: str
    repo: Optional[str] = None

    def to_bus_message(self) -> str:
        repo_tag = f" repo={self.repo}" if self.repo else ""
        return (
            f"host={self.host} pr={self.pr_number} result={self.result} "
            f"checks={self.checks_passed}/{self.checks_total} "
            f"failed={self.checks_failed}{repo_tag}"
        )


@dataclass(frozen=True)
class MainMoved:
    """Notification that origin/main advanced relative to local."""

    local_sha: str
    remote_sha: str
    commits_behind: int
    stale_branches: tuple[str, ...]  # branches behind origin/main
    host: str
    repo: Optional[str] = None

    def to_bus_message(self) -> str:
        repo_tag = f" repo={self.repo}" if self.repo else ""
        branches = ",".join(self.stale_branches) if self.stale_branches else "none"
        return (
            f"host={self.host} behind={self.commits_behind} "
            f"stale_branches={branches}{repo_tag}"
        )


def validate_aspect(aspect: str) -> bool:
    """Check if a review aspect is in the known set."""
    return aspect in REVIEW_ASPECTS
