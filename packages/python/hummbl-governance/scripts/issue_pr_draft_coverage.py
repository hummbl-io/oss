#!/usr/bin/env python3
"""Issue/PR draft coverage helper.

Runs in check mode to summarize open issues/PRs and identify draft PR posture.
Designed as a lightweight, repo-local utility with optional GitHub CLI integration.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from typing import Any


def run(cmd: list[str], cwd: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )


def has_gh_cli() -> bool:
    return shutil.which("gh") is not None


def resolve_repo(explicit: str | None = None) -> tuple[str | None, bool]:
    if explicit:
        return explicit, True

    remote_proc = run(["git", "remote", "get-url", "origin"])
    if remote_proc.returncode != 0:
        return None, False

    remote_url = remote_proc.stdout.strip()
    if remote_url.startswith("git@github.com:"):
        remote_url = remote_url.split(":", 1)[1]
    if remote_url.startswith("https://github.com/"):
        remote_url = remote_url.split("https://github.com/", 1)[1]
    remote_url = remote_url.removesuffix(".git")
    if "/" in remote_url:
        return remote_url, True
    return remote_url, False


def gh_json(cmd: list[str]) -> tuple[list[dict[str, Any]] | None, str | None]:
    proc = run(["gh", *cmd], cwd=None)
    if proc.returncode != 0:
        return None, (proc.stderr or proc.stdout).strip() or "gh command failed"
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        return None, f"invalid JSON from gh: {exc}"
    if not isinstance(data, list):
        data = [data]
    return data, None


def collect_issues(repo: str, max_items: int, state: str) -> tuple[list[dict[str, Any]], list[str]]:
    if not has_gh_cli():
        return [], ["gh not installed; using local no-op mode"]
    data, err = gh_json(
        [
            "issue",
            "list",
            "--repo",
            repo,
            "--state",
            state,
            "--limit",
            str(max_items),
            "--json",
            "number,title,author,url",
        ]
    )
    if err:
        return [], [err]
    if not data:
        return [], []
    # Filter out pull-request wrappers because issue-list also returns them by default.
    filtered = [item for item in data if not item.get("pull_request")]
    return filtered, []


def collect_prs(repo: str, max_items: int, state: str) -> tuple[list[dict[str, Any]], list[str]]:
    if not has_gh_cli():
        return [], ["gh not installed; using local no-op mode"]
    data, err = gh_json(
        [
            "pr",
            "list",
            "--repo",
            repo,
            "--state",
            state,
            "--limit",
            str(max_items),
            "--json",
            "number,title,author,url,isDraft",
        ]
    )
    if err:
        return [], [err]
    return data or [], []


def summarize(
    repo: str,
    max_issues: int,
    strict_remotes: bool,
    output_json: bool,
) -> int:
    issues, warnings = collect_issues(repo, max_issues, "open")
    prs, pr_warnings = collect_prs(repo, max_issues, "open")
    warnings.extend(pr_warnings)

    drafts = [pr for pr in prs if pr.get("isDraft")]
    not_drafts = [pr for pr in prs if pr.get("isDraft") is False]
    unknown = [pr for pr in prs if pr.get("isDraft") is None]
    summary = {
        "repo": repo,
        "open_issues": len(issues),
        "open_prs": len(prs),
        "draft_prs": len(drafts),
        "ready_prs": len(not_drafts),
        "pending_state_prs": len(unknown),
        "strict_remotes": strict_remotes,
        "warnings": warnings,
        "draft_examples": [item.get("url") for item in drafts[:5]],
        "readiness_gate": "pass" if len(warnings) == 0 else "degraded",
    }

    if output_json:
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0

    print(f"Repo: {repo}")
    print(f"Open issues: {summary['open_issues']}")
    print(f"Open PRs:  {summary['open_prs']}")
    print(f"  Draft PRs: {summary['draft_prs']}")
    print(f"  Ready PRs: {summary['ready_prs']}")
    print(f"  Unknown draft state: {summary['pending_state_prs']}")
    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"  - {warning}")
    if drafts:
        print("Recent draft PR examples:")
        for url in summary["draft_examples"]:
            print(f"  - {url}")

    if strict_remotes and warnings:
        print("Strict mode failed: remote telemetry incomplete")
        return 2
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check issue and PR draft coverage")
    parser.add_argument("--repo", default=None, help="owner/repo or explicit repo path")
    parser.add_argument("--max-issues", type=int, default=100, help="max issues/PRs to pull")
    parser.add_argument("--strict-remotes", action="store_true", help="fail on gh availability failures")
    parser.add_argument("--json", action="store_true", help="emit JSON summary")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo, repo_ok = resolve_repo(args.repo)
    if not repo:
        print("No repository detected. Provide --repo.", file=sys.stderr)
        return 2
    if not repo_ok:
        print("Repository origin format is nonstandard; using provided value.", file=sys.stderr)

    return summarize(
        repo=repo,
        max_issues=args.max_issues,
        strict_remotes=args.strict_remotes,
        output_json=args.json,
    )


if __name__ == "__main__":
    raise SystemExit(main())
