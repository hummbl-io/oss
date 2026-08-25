#!/usr/bin/env python3
"""Detect duplicate or superseded PRs by branch-name pattern.

When an agent creates both a ``chore/codex/issue-N-draft-pr`` branch and
a ``feat/devin/issue-N-*`` branch for the same issue, both PRs can end
up open simultaneously with no closure signal. This script detects that
pattern and reports duplicate PRs.

Conservative v1 — detection and reporting only. Does not auto-close PRs.

Usage::

    # Scan all open PRs (requires gh CLI)
    python scripts/detect_duplicate_prs.py

    # Dry-run with explicit PR list (no gh calls)
    python scripts/detect_duplicate_prs.py --from-json prs.json

Exit codes:
    0 — no duplicates found, or duplicates found in report-only mode
    1 — duplicates found and --strict is set
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

# Pattern: any branch following <type>/<actor>/issue-<n>-... naming
_ISSUE_BRANCH_PATTERN = re.compile(r"^[^/]+/[^/]+/issue-(\d+)(?:-[^/]*)?$")
_ISSUE_SUFFIX_DRAFT_RE = re.compile(r"(^|-)draft(?:-|$)")


def parse_issue_number(branch: str) -> int | None:
    """Extract the issue number from a branch name."""
    m = _ISSUE_BRANCH_PATTERN.match(branch)
    if m:
        return int(m.group(1))
    return None


def classify_branch(branch: str) -> str:
    """Classify a branch as 'draft', 'candidate', or 'other'."""
    if not _ISSUE_BRANCH_PATTERN.match(branch):
        return "other"

    issue_tail = branch.split("issue-", 1)[1]
    if _ISSUE_SUFFIX_DRAFT_RE.search(issue_tail):
        return "draft"
    return "candidate"


def fetch_open_prs() -> list[dict]:
    """Fetch open PRs via gh CLI."""
    result = subprocess.run(
        [
            "gh", "pr", "list",
            "--state", "open",
            "--limit", "100",
            "--json", "number,title,headRefName",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def find_duplicates(prs: list[dict]) -> list[dict]:
    """Find PRs that share the same issue number across draft + candidate branches.

    Returns a list of duplicate groups, each containing:
        - issue: the issue number
        - draft_prs: list of draft PRs for that issue
        - feat_prs: list of non-draft/issue-linked PRs for that issue
    """
    by_issue: dict[int, dict[str, list[dict]]] = defaultdict(
        lambda: {"draft": [], "candidate": []}
    )

    for pr in prs:
        branch = pr.get("headRefName", "")
        issue_num = parse_issue_number(branch)
        if issue_num is None:
            continue
        kind = classify_branch(branch)
        if kind in ("draft", "candidate"):
            by_issue[issue_num][kind].append(pr)

    duplicates: list[dict] = []
    for issue, groups in sorted(by_issue.items()):
        # Duplicate if both a draft and a non-draft issue-linked branch exist
        if groups["draft"] and groups["candidate"]:
            duplicates.append({
                "issue": issue,
                "draft_prs": groups["draft"],
                "feat_prs": groups["candidate"],
            })
        # Also flag if multiple drafts exist for the same issue
        elif len(groups["draft"]) > 1:
            duplicates.append({
                "issue": issue,
                "draft_prs": groups["draft"],
                "feat_prs": [],
            })

    return duplicates


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Detect duplicate or superseded PRs by branch-name pattern."
    )
    parser.add_argument(
        "--from-json",
        type=str,
        default=None,
        help="Read PR list from a JSON file instead of calling gh.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 if duplicates are found.",
    )
    args = parser.parse_args()

    if args.from_json:
        prs = json.loads(Path(args.from_json).read_text(encoding="utf-8"))
    else:
        try:
            prs = fetch_open_prs()
        except FileNotFoundError:
            print("FAIL: gh CLI not found. Install GitHub CLI or use --from-json.")
            return 1
        except subprocess.CalledProcessError as e:
            print(f"FAIL: gh pr list failed: {e.stderr}")
            return 1

    if not prs:
        print("OK: No open PRs to check.")
        return 0

    duplicates = find_duplicates(prs)

    if not duplicates:
        print(f"OK: No duplicate PRs found among {len(prs)} open PR(s).")
        return 0

    print(f"FOUND: {len(duplicates)} duplicate PR group(s):\n")
    for group in duplicates:
        issue = group["issue"]
        draft_prs = group["draft_prs"]
        feat_prs = group["feat_prs"]

        print(f"  Issue #{issue}:")
        for pr in draft_prs:
            print(f"    [DRAFT] #{pr['number']}: {pr['title']} ({pr['headRefName']})")
        for pr in feat_prs:
            print(f"    [FEAT]  #{pr['number']}: {pr['title']} ({pr['headRefName']})")

        if draft_prs and feat_prs:
            draft_nums = ", ".join(f"#{pr['number']}" for pr in draft_prs)
            feat_nums = ", ".join(f"#{pr['number']}" for pr in feat_prs)
            print(f"    -> Close {draft_nums} with 'superseded-by: {feat_nums}'")
        elif len(draft_prs) > 1:
            nums = ", ".join(f"#{pr['number']}" for pr in draft_prs)
            print(f"    -> Multiple drafts for same issue: {nums}")
        print()

    if args.strict:
        print("FAIL: Duplicate PRs detected. Use --strict=false to report only.")
        return 1

    print("(report-only mode — no PRs were closed.)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
