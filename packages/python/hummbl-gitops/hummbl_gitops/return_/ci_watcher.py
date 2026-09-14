"""B1: CI watcher — poll gh pr checks and post to bus on completion.

This module watches CI status for open PRs and posts a CI_COMPLETED message
to the coordination bus when CI finishes (pass or fail). This eliminates the
need for manual `gh pr status` checks.

The watcher is designed to run as a background process (daemon, systemd timer,
or agent-invoked long poll). It polls at a configurable interval and only
posts on state transitions (not every poll), avoiding bus spam.

Requires the `gh` CLI to be authenticated.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Sequence

from hummbl_gitops.protocol import CI_COMPLETED, CICompletion


@dataclass
class PRCheckState:
    """Current CI state for a single PR."""

    pr_number: int
    checks_total: int = 0
    checks_completed: int = 0
    checks_passed: int = 0
    checks_failed: int = 0
    in_progress: bool = False
    last_result: Optional[str] = None  # "PASS", "FAIL", or None if still running


@dataclass
class WatchResult:
    """Result of a single watch poll cycle."""

    pr_number: int
    state: PRCheckState
    transitioned: bool = False  # True if state changed since last poll
    completion: Optional[CICompletion] = None  # Set if CI just completed


def get_pr_checks(pr_number: int, repo: Optional[str] = None) -> PRCheckState:
    """Query CI check status for a PR via gh CLI.

    Args:
        pr_number: PR number to check.
        repo: Full repo name (owner/repo). If None, uses current repo.

    Returns:
        PRCheckState with current check counts.
    """
    cmd = ["gh", "pr", "checks", str(pr_number), "--json", "name,state,conclusion"]
    if repo:
        cmd.extend(["--repo", repo])

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return PRCheckState(pr_number=pr_number)

    try:
        checks = json.loads(result.stdout)
    except json.JSONDecodeError:
        return PRCheckState(pr_number=pr_number)

    state = PRCheckState(pr_number=pr_number, checks_total=len(checks))

    for check in checks:
        check_state = check.get("state", "").upper()
        conclusion = check.get("conclusion", "").upper()

        if check_state in ("IN_PROGRESS", "PENDING", "QUEUED"):
            state.in_progress = True
        elif check_state in ("SUCCESS", "NEUTRAL", "SKIPPED"):
            state.checks_completed += 1
            if conclusion in ("SUCCESS", "NEUTRAL", "SKIPPED", ""):
                state.checks_passed += 1
        elif check_state in ("FAILURE", "CANCELLED", "TIMED_OUT", "ACTION_REQUIRED"):
            state.checks_completed += 1
            state.checks_failed += 1

    if not state.in_progress and state.checks_completed > 0:
        state.last_result = "FAIL" if state.checks_failed > 0 else "PASS"

    return state


def detect_transition(
    previous: Optional[PRCheckState],
    current: PRCheckState,
) -> WatchResult:
    """Detect if CI state transitioned from running to completed.

    A transition is: was in_progress, now not in_progress, and checks completed.
    Also detects: was completed with different result (e.g., re-run).
    """
    transitioned = False
    completion = None

    if previous is None:
        # First poll — only report if already complete
        if not current.in_progress and current.last_result is not None:
            transitioned = True
    else:
        was_running = previous.in_progress
        now_done = not current.in_progress and current.last_result is not None

        if was_running and now_done:
            transitioned = True
        elif (
            previous.last_result is not None
            and current.last_result is not None
            and previous.last_result != current.last_result
        ):
            # Result changed (e.g., re-run after fix)
            transitioned = True

    if transitioned and current.last_result is not None:
        completion = CICompletion(
            pr_number=current.pr_number,
            result=current.last_result,
            checks_total=current.checks_total,
            checks_passed=current.checks_passed,
            checks_failed=current.checks_failed,
            host="unknown",  # set by caller
        )

    return WatchResult(
        pr_number=current.pr_number,
        state=current,
        transitioned=transitioned,
        completion=completion,
    )


def watch_prs(
    pr_numbers: Sequence[int],
    interval_seconds: int = 60,
    max_polls: Optional[int] = None,
    repo: Optional[str] = None,
    host: str = "unknown",
    on_completion: Optional[callable] = None,
) -> list[WatchResult]:
    """Watch CI status for one or more PRs, posting on completion.

    Args:
        pr_numbers: PR numbers to watch.
        interval_seconds: Poll interval in seconds.
        max_polls: Maximum number of poll cycles. None = infinite.
        repo: Repo (owner/repo) for gh CLI.
        host: Host tag for bus messages.
        on_completion: Callback invoked with CICompletion when a PR transitions.
                       If None, completions are collected and returned.

    Returns:
        List of WatchResults that transitioned (completions only).
    """
    states: dict[int, Optional[PRCheckState]] = {n: None for n in pr_numbers}
    completions: list[WatchResult] = []
    poll_count = 0

    while True:
        poll_count += 1
        if max_polls is not None and poll_count > max_polls:
            break

        for pr_num in pr_numbers:
            current = get_pr_checks(pr_num, repo=repo)
            previous = states[pr_num]
            result = detect_transition(previous, current)
            states[pr_num] = current

            if result.transitioned and result.completion is not None:
                # Set host on the completion
                result.completion = CICompletion(
                    pr_number=result.completion.pr_number,
                    result=result.completion.result,
                    checks_total=result.completion.checks_total,
                    checks_passed=result.completion.checks_passed,
                    checks_failed=result.completion.checks_failed,
                    host=host,
                    repo=repo,
                )

                if on_completion is not None:
                    on_completion(result.completion)
                completions.append(result)

        if max_polls is None:
            time.sleep(interval_seconds)

    return completions


def get_open_pr_numbers(repo: Optional[str] = None) -> list[int]:
    """Get PR numbers for all open PRs in the repo."""
    cmd = ["gh", "pr", "list", "--state", "open", "--json", "number"]
    if repo:
        cmd.extend(["--repo", repo])

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return []

    try:
        prs = json.loads(result.stdout)
        return [pr["number"] for pr in prs]
    except json.JSONDecodeError:
        return []
