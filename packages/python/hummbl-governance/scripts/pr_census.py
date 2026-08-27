#!/usr/bin/env python3
"""PR census report.

Collects local repository metadata and, when available, remote PR/issue
statistics from the GitHub CLI.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
import subprocess
from dataclasses import dataclass


def run(cmd: list[str], cwd: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def gh_available() -> bool:
    return shutil.which("gh") is not None


def gh_json(args: list[str]) -> tuple[list[dict[str, object]] | None, str | None]:
    proc = run(["gh", *args])
    if proc.returncode != 0:
        return None, (proc.stderr or proc.stdout).strip() or "gh call failed"
    try:
        parsed = json.loads(proc.stdout)
        if isinstance(parsed, list):
            return parsed, None
        return [parsed], None
    except json.JSONDecodeError as exc:
        return None, f"invalid JSON from gh: {exc}"


@dataclass
class Census:
    repo: str
    open_prs: int
    open_issues: int
    mergeable_true: int
    mergeable_false: int
    mergeable_unknown: int
    generated_at: str
    warnings: list[str]


def build_report(repo: str, max_items: int) -> Census | tuple[Census, int]:
    warnings: list[str] = []
    open_prs = 0
    open_issues = 0
    mergeable_true = 0
    mergeable_false = 0
    mergeable_unknown = 0

    if not gh_available():
        warnings.append("gh CLI unavailable; using local git-only census")
        try:
            proc = run(["git", "status", "--short"], cwd=None)
            if proc.returncode != 0:
                warnings.append("git status failed during local census")
        except Exception as exc:
            warnings.append(f"git status failed: {exc}")
        return Census(
            repo=repo,
            open_prs=0,
            open_issues=0,
            mergeable_true=0,
            mergeable_false=0,
            mergeable_unknown=0,
            generated_at=dt.datetime.now(dt.timezone.utc).isoformat(),
            warnings=warnings,
        )

    prs, err = gh_json(
        [
            "pr",
            "list",
            "--repo",
            repo,
            "--state",
            "open",
            "--limit",
            str(max_items),
            "--json",
            "number,title,mergeable",
        ]
    )
    if err:
        warnings.append(err)
    else:
        open_prs = len(prs)
        for item in prs:
            state = item.get("mergeable")
            if state is True:
                mergeable_true += 1
            elif state is False:
                mergeable_false += 1
            else:
                mergeable_unknown += 1

    issues, err = gh_json(
        ["issue", "list", "--repo", repo, "--state", "open", "--limit", str(max_items), "--json", "number,title"]
    )
    if err:
        warnings.append(err)
    else:
        open_issues = len([i for i in issues if not isinstance(i.get("pull_request"), dict)])

    return Census(
        repo=repo,
        open_prs=open_prs,
        open_issues=open_issues,
        mergeable_true=mergeable_true,
        mergeable_false=mergeable_false,
        mergeable_unknown=mergeable_unknown,
        generated_at=dt.datetime.now(dt.timezone.utc).isoformat(),
        warnings=warnings,
    )


def render_markdown(census: Census) -> str:
    warning_lines = [f"- {w}" for w in census.warnings] if census.warnings else ["- none"]
    return "\n".join(
        [
            "# PR Census",
            f"Repo: {census.repo}",
            f"Generated: {census.generated_at}",
            "",
            f"- Open PRs: {census.open_prs}",
            f"- Open issues: {census.open_issues}",
            f"- Mergeable PRs: {census.mergeable_true}",
            f"- Non-mergeable PRs: {census.mergeable_false}",
            f"- Unknown mergeable PRs: {census.mergeable_unknown}",
            "",
            "## Warnings",
            *warning_lines,
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a lightweight PR census")
    parser.add_argument("--repo", default=None, help="owner/repo override")
    parser.add_argument("--max-items", type=int, default=100)
    parser.add_argument("--output", help="optional markdown report path")
    parser.add_argument("--json", action="store_true", help="output JSON")
    return parser.parse_args()


def resolve_repo(explicit: str | None) -> str:
    if explicit:
        return explicit
    proc = run(["git", "remote", "get-url", "origin"])
    if proc.returncode != 0:
        return os.getcwd()
    raw = proc.stdout.strip()
    if raw.startswith("git@github.com:"):
        raw = raw.split(":", 1)[1]
    if raw.startswith("https://github.com/"):
        raw = raw.split("https://github.com/", 1)[1]
    return raw.removesuffix(".git")


def main() -> int:
    args = parse_args()
    repo = resolve_repo(args.repo)
    result = build_report(repo=repo, max_items=args.max_items)
    if args.json:
        print(json.dumps(result.__dict__, indent=2))
    else:
        md = render_markdown(result)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as fp:
                fp.write(md + "\n")
            print(f"Wrote report: {args.output}")
        else:
            print(md)
    return 2 if result.warnings else 0


if __name__ == "__main__":
    raise SystemExit(main())
