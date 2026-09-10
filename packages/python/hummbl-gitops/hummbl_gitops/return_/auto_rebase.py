"""B4: Auto-rebase stale branches.

Detects branches behind origin/main and either:
- Reports they can be cleanly rebased (REBASE_AVAILABLE)
- Reports they have conflicts (REBASE_CONFLICTS)
- Executes the rebase if --execute is passed (REBASE_DONE)

Day 1 posture: detect + report + execute-on-approval.
The default is dry-run. Execution requires explicit --execute flag.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class StaleBranch:
    """A branch that is behind origin/main."""

    branch: str
    behind: int  # commits behind origin/main
    ahead: int  # commits ahead of origin/main (unique work)
    can_rebase: bool  # True if rebase would be clean


def check_stale_branches(
    repo_path: Path,
    host: str = "unknown",
) -> list[StaleBranch]:
    """Find all branches behind origin/main and check if they can rebase cleanly."""
    repo_path = Path(repo_path).resolve()

    # Ensure we have latest origin/main
    subprocess.run(
        ["git", "fetch", "origin"],
        cwd=repo_path,
        capture_output=True,
        timeout=30,
    )

    # List all local branches except main
    branches_result = subprocess.run(
        ["git", "for-each-ref", "--format=%(refname:short)", "refs/heads/"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )

    stale = []
    if branches_result.returncode != 0:
        return stale

    for branch in branches_result.stdout.strip().split("\n"):
        if branch == "main" or not branch:
            continue

        # Check behind/ahead counts
        counts_result = subprocess.run(
            ["git", "rev-list", "--left-right", "--count", f"{branch}...origin/main"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )
        if counts_result.returncode != 0:
            continue

        parts = counts_result.stdout.strip().split()
        if len(parts) != 2:
            continue
        ahead, behind = int(parts[0]), int(parts[1])

        if behind == 0:
            continue  # Not stale

        # Check if rebase would be clean using merge-tree
        # merge-tree outputs conflict info if there are conflicts
        base_result = subprocess.run(
            ["git", "merge-base", branch, "origin/main"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )
        if base_result.returncode != 0:
            stale.append(StaleBranch(branch=branch, behind=behind, ahead=ahead, can_rebase=False))
            continue

        base = base_result.stdout.strip()
        tree_result = subprocess.run(
            ["git", "merge-tree", base, branch, "origin/main"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )

        # merge-tree outputs conflict info if there are conflicts
        # If the output contains "conflict" or non-zero exit with conflict markers
        has_conflicts = "conflict" in tree_result.stdout.lower() or "<<<<<<" in tree_result.stdout

        stale.append(StaleBranch(
            branch=branch,
            behind=behind,
            ahead=ahead,
            can_rebase=not has_conflicts,
        ))

    return stale


def rebase_branch(repo_path: Path, branch: str) -> bool:
    """Rebase a branch onto origin/main. Returns True on success.

    This is a destructive operation (force-push required after).
    The caller must have explicit approval before calling this.
    """
    repo_path = Path(repo_path).resolve()

    # Checkout the branch
    checkout = subprocess.run(
        ["git", "checkout", branch],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    if checkout.returncode != 0:
        return False

    # Rebase onto origin/main
    rebase = subprocess.run(
        ["git", "rebase", "origin/main"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )

    if rebase.returncode != 0:
        # Abort the failed rebase
        subprocess.run(["git", "rebase", "--abort"], cwd=repo_path, capture_output=True)
        return False

    return True
