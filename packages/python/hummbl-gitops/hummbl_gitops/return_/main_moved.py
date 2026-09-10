"""B2: Detect when origin/main has advanced relative to local main.

Posts MAIN_MOVED to the bus with the list of stale branches.
This is awareness-only — no action taken, just notification.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Optional

from hummbl_gitops.protocol import MainMoved


def check_main_moved(
    repo_path: Path,
    host: str = "unknown",
) -> Optional[MainMoved]:
    """Check if origin/main is ahead of local main.

    Returns MainMoved if origin/main has advanced, None if no remote tracking.
    Also detects stale feature branches that are behind origin/main.
    """
    repo_path = Path(repo_path).resolve()

    # Fetch origin to get latest remote state
    subprocess.run(
        ["git", "fetch", "origin"],
        cwd=repo_path,
        capture_output=True,
        timeout=30,
    )

    # Get local and remote main SHAs
    local_result = subprocess.run(
        ["git", "rev-parse", "main"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    if local_result.returncode != 0:
        return None

    remote_result = subprocess.run(
        ["git", "rev-parse", "origin/main"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    if remote_result.returncode != 0:
        return None

    local_sha = local_result.stdout.strip()
    remote_sha = remote_result.stdout.strip()

    if local_sha == remote_sha:
        return MainMoved(
            local_sha=local_sha,
            remote_sha=remote_sha,
            commits_behind=0,
            stale_branches=(),
            host=host,
        )

    # Count commits behind
    count_result = subprocess.run(
        ["git", "rev-list", "--count", "main..origin/main"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    commits_behind = int(count_result.stdout.strip()) if count_result.returncode == 0 else 0

    # Find stale feature branches
    branches_result = subprocess.run(
        ["git", "for-each-ref", "--format=%(refname:short) %(upstream:short)", "refs/heads/"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )

    stale_branches = []
    if branches_result.returncode == 0:
        for line in branches_result.stdout.strip().split("\n"):
            parts = line.split()
            if len(parts) < 2:
                continue
            branch = parts[0]
            if branch == "main":
                continue
            # Check if branch is behind origin/main
            behind_result = subprocess.run(
                ["git", "rev-list", "--count", f"{branch}..origin/main"],
                cwd=repo_path,
                capture_output=True,
                text=True,
            )
            if behind_result.returncode == 0:
                behind = int(behind_result.stdout.strip())
                if behind > 0:
                    stale_branches.append(branch)

    return MainMoved(
        local_sha=local_sha,
        remote_sha=remote_sha,
        commits_behind=commits_behind,
        stale_branches=tuple(stale_branches),
        host=host,
    )
