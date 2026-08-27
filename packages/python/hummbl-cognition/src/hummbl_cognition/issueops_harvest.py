"""IssueOps harvest — orchestrates automated issue creation from audit findings.

This is the capstone module that ties together all IssueOps foundation modules:
  - write_boundary: enforces authorized-repo write boundary
  - duplicate_detector: prevents duplicate issue creation
  - issueops_receipt: records structured receipts for every run
  - bus_writer: posts coordination bus messages
  - dispatcher_pod_receipt: claim/release pod lifecycle

The harvest script:
  1. Reads candidate issues from a JSON input file (audit findings)
  2. Filters candidates through the write boundary
  3. Detects duplicates against existing open issues (closed-issue
     duplicate detection is available via fetch_issues(state='all')
     but is not yet wired into the harvest flow)
  4. Creates issues in authorized repos via gh CLI
  5. Bus PROPOSAL and STATUS are posted by the GitHub Actions workflow
     (issueops-harvest.yml), not by this Python module. The workflow
     posts PROPOSAL before the harvest step and STATUS after.
  6. Appends an IssueOps run receipt with full evidence
  7. Respects backpressure (max issues per run)

CLI:
  python -m hummbl_cognition.issueops_harvest \
    --candidates /path/to/candidates.json \
    --agent devin \
    --source arbiter-audit \
    --max-issues 10

Design:
  - Pure stdlib (subprocess, json, pathlib, argparse)
  - No side effects on dry-run (--dry-run flag)
  - Structured output for CI consumption
"""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from hummbl_cognition.duplicate_detector import DuplicateDetector
from hummbl_cognition.issueops_receipt import append_receipt as append_issueops_receipt
from hummbl_cognition.issueops_receipt import create_receipt
from hummbl_cognition.write_boundary import WriteBoundaryEnforcer

__all__ = [
    "HarvestResult",
    "harvest",
    "load_candidates",
    "create_issue_via_gh",
]

logger = logging.getLogger(__name__)

DEFAULT_MAX_ISSUES = 10
DEFAULT_DUPLICATE_THRESHOLD = 0.80


@dataclass
class HarvestResult:
    """Structured result of a harvest run."""

    run_id: str = ""
    timestamp: str = ""
    agent: str = ""
    source: str = ""
    total_candidates: int = 0
    issues_created: list[dict[str, Any]] = field(default_factory=list)
    issues_skipped_duplicate: list[dict[str, Any]] = field(default_factory=list)
    issues_skipped_boundary: list[dict[str, Any]] = field(default_factory=list)
    issues_skipped_backpressure: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    dry_run: bool = False

    @property
    def total_created(self) -> int:
        return len(self.issues_created)

    @property
    def total_skipped(self) -> int:
        return (
            len(self.issues_skipped_duplicate)
            + len(self.issues_skipped_boundary)
            + len(self.issues_skipped_backpressure)
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "agent": self.agent,
            "source": self.source,
            "total_candidates": self.total_candidates,
            "total_created": self.total_created,
            "total_skipped": self.total_skipped,
            "issues_created": self.issues_created,
            "issues_skipped_duplicate": self.issues_skipped_duplicate,
            "issues_skipped_boundary": self.issues_skipped_boundary,
            "issues_skipped_backpressure": self.issues_skipped_backpressure,
            "errors": self.errors,
            "dry_run": self.dry_run,
        }


def load_candidates(candidates_path: str | Path) -> list[dict[str, Any]]:
    """Load candidate issues from a JSON file.

    Expected format: list of objects with at least:
      - repo: str (full repo name, e.g. "hummbl-io/arbiter")
      - title: str
      - body: str (optional)
      - labels: list[str] (optional)
      - category: str (optional)
      - severity: str (optional)
    """
    path = Path(candidates_path)
    if not path.exists():
        raise FileNotFoundError(f"Candidates file not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Candidates file must contain a JSON array")
    return data


def create_issue_via_gh(
    repo: str,
    title: str,
    body: str = "",
    labels: list[str] | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Create a GitHub issue via gh CLI.

    Returns dict with: success, repo, number, title, url, error
    """
    if dry_run:
        return {
            "success": True,
            "repo": repo,
            "number": 0,
            "title": title,
            "url": "",
            "error": "",
            "dry_run": True,
        }

    cmd = ["gh", "issue", "create", "--repo", repo, "--title", title]
    if body:
        cmd.extend(["--body", body])
    if labels:
        for label in labels:
            cmd.extend(["--label", label])

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if proc.returncode != 0:
            return {
                "success": False,
                "repo": repo,
                "number": 0,
                "title": title,
                "url": "",
                "error": proc.stderr.strip(),
            }
        url = proc.stdout.strip()
        # Extract issue number from URL
        number = 0
        if url:
            parts = url.rstrip("/").split("/")
            if parts:
                try:
                    number = int(parts[-1])
                except ValueError:
                    pass
        return {
            "success": True,
            "repo": repo,
            "number": number,
            "title": title,
            "url": url,
            "error": "",
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "repo": repo,
            "number": 0,
            "title": title,
            "url": "",
            "error": "gh CLI timeout (30s)",
        }
    except Exception as e:
        return {
            "success": False,
            "repo": repo,
            "number": 0,
            "title": title,
            "url": "",
            "error": str(e),
        }


def harvest(
    candidates: list[dict[str, Any]],
    agent: str,
    source: str,
    max_issues: int = DEFAULT_MAX_ISSUES,
    duplicate_threshold: float = DEFAULT_DUPLICATE_THRESHOLD,
    dry_run: bool = False,
    skip_gh_fetch: bool = False,
    existing_issues_map: dict[str, list[dict[str, Any]]] | None = None,
) -> HarvestResult:
    """Run the IssueOps harvest pipeline.

    Args:
        candidates: List of candidate issue dicts
        agent: Agent identity (e.g. "devin")
        source: Source of candidates (e.g. "arbiter-audit")
        max_issues: Maximum issues to create per run (backpressure)
        duplicate_threshold: Title similarity threshold for duplicate detection
        dry_run: If True, don't actually create issues
        skip_gh_fetch: If True, don't fetch existing issues via gh CLI
        existing_issues_map: Pre-fetched issues keyed by repo (for testing)

    Returns:
        HarvestResult with full details of the run
    """
    result = HarvestResult(
        agent=agent,
        source=source,
        total_candidates=len(candidates),
        dry_run=dry_run,
    )

    if not candidates:
        result.errors.append("No candidates provided")
        return result

    # Step 1: Write boundary enforcement
    enforcer = WriteBoundaryEnforcer()
    boundary_result = enforcer.filter_candidates(candidates)
    authorized = boundary_result.authorized
    result.issues_skipped_boundary = boundary_result.skipped

    if not authorized:
        result.errors.append("All candidates outside write boundary")
        return result

    # Step 2: Duplicate detection (per repo, open AND closed)
    detector = DuplicateDetector(threshold=duplicate_threshold)
    unique_candidates: list[dict[str, Any]] = []

    for candidate in authorized:
        repo = candidate.get("repo", "")
        if skip_gh_fetch or existing_issues_map is not None:
            existing = existing_issues_map.get(repo, []) if existing_issues_map else []
            check = detector.check_candidate(candidate.get("title", ""), existing)
        else:
            # Fetch both open and closed issues from the repo
            existing = detector.fetch_issues(repo, state="all")
            check = detector.check_candidate(candidate.get("title", ""), existing)

        if check.is_duplicate:
            dup_entry = dict(candidate)
            dup_entry["_duplicate_match"] = check.to_dict()
            result.issues_skipped_duplicate.append(dup_entry)
        else:
            unique_candidates.append(candidate)

    if not unique_candidates:
        logger.info("All candidates were duplicates or outside boundary")
        return result

    # Step 3: Backpressure — limit issues per run
    if len(unique_candidates) > max_issues:
        result.issues_skipped_backpressure = unique_candidates[max_issues:]
        unique_candidates = unique_candidates[:max_issues]

    # Step 4: Create issues
    for candidate in unique_candidates:
        repo = candidate.get("repo", "")
        title = candidate.get("title", "")
        body = candidate.get("body", "")
        labels = candidate.get("labels", [])

        issue_result = create_issue_via_gh(
            repo=repo,
            title=title,
            body=body,
            labels=labels,
            dry_run=dry_run,
        )

        if issue_result["success"]:
            result.issues_created.append(issue_result)
        else:
            result.errors.append(
                f"Failed to create issue in {repo}: {issue_result['error']}"
            )

    return result


def _cli() -> None:
    """CLI entry point for IssueOps harvest."""
    parser = argparse.ArgumentParser(
        description="IssueOps harvest — automated issue creation from audit findings"
    )
    parser.add_argument(
        "--candidates",
        required=True,
        help="Path to JSON file with candidate issues",
    )
    parser.add_argument(
        "--agent",
        required=True,
        help="Agent identity (e.g. devin)",
    )
    parser.add_argument(
        "--source",
        required=True,
        choices=[
            "chatgpt-connector",
            "arbiter-audit",
            "manual",
            "scheduled",
            "webhook",
        ],
        help="Source of candidates",
    )
    parser.add_argument(
        "--max-issues",
        type=int,
        default=DEFAULT_MAX_ISSUES,
        help=f"Maximum issues to create per run (default: {DEFAULT_MAX_ISSUES})",
    )
    parser.add_argument(
        "--duplicate-threshold",
        type=float,
        default=DEFAULT_DUPLICATE_THRESHOLD,
        help=f"Title similarity threshold (default: {DEFAULT_DUPLICATE_THRESHOLD})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't actually create issues — just report what would happen",
    )
    parser.add_argument(
        "--receipt-log",
        default=None,
        help="Custom path for IssueOps receipt log",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Write structured result to this JSON file",
    )

    args = parser.parse_args()

    # Load candidates
    try:
        candidates = load_candidates(args.candidates)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error loading candidates: {e}", file=sys.stderr)
        raise SystemExit(1)

    # Run harvest
    result = harvest(
        candidates=candidates,
        agent=args.agent,
        source=args.source,
        max_issues=args.max_issues,
        duplicate_threshold=args.duplicate_threshold,
        dry_run=args.dry_run,
    )

    # Generate receipt — include skip data so the durable record is complete
    # In dry-run mode, issues have number=0 which violates the receipt schema
    # (minimum 1). Exclude dry-run placeholders from issues_created and note
    # them in the notes field instead.
    real_issues_created = [r for r in result.issues_created if r.get("number", 0) >= 1]
    dry_run_count = len(result.issues_created) - len(real_issues_created)

    receipt = create_receipt(
        source=args.source,
        agent=args.agent,
        issues_created=[
            {
                "repo": r["repo"],
                "number": r["number"],
                "title": r["title"],
                "category": r.get("category", "auto"),
                "severity": r.get("severity", "medium"),
            }
            for r in real_issues_created
        ],
        issues_closed=[],
        issues_commented=[],
        evidence_refs=[args.candidates],
        notes=f"Harvest: {result.total_created} created, {result.total_skipped} skipped, dry_run={args.dry_run}, dry_run_placeholders={dry_run_count}",
        skipped_duplicate_candidates=[
            {
                "repo": c.get("repo", ""),
                "proposed_title": c.get("title", ""),
                "duplicate_of": c.get("_duplicate_match", {}).get("issue_url", ""),
                "match_reason": c.get("_duplicate_match", {}).get("match_type", ""),
            }
            for c in result.issues_skipped_duplicate
        ]
        or None,
        read_only_candidates=[
            {
                "repo": c.get("repo", ""),
                "proposed_title": c.get("title", ""),
                "category": c.get("category", "auto"),
                "severity": c.get("severity", "medium"),
            }
            for c in result.issues_skipped_boundary
        ]
        or None,
        backpressure_notes=(
            f"{len(result.issues_skipped_backpressure)} candidates deferred due to max-issues limit"
            if result.issues_skipped_backpressure
            else None
        ),
        run_disposition=(
            "created"
            if result.total_created > 0
            else "skipped-all"
            if result.total_skipped > 0
            else "no-op"
        ),
    )
    result.run_id = receipt["run_id"]
    result.timestamp = receipt["timestamp"]

    # Append receipt
    if args.receipt_log:
        append_issueops_receipt(receipt, args.receipt_log)
    else:
        append_issueops_receipt(receipt)

    # Output result
    output = result.to_dict()
    output["receipt"] = receipt

    if args.output:
        Path(args.output).write_text(json.dumps(output, indent=2), encoding="utf-8")
        print(f"Result written to {args.output}")
    else:
        print(json.dumps(output, indent=2))

    # Exit code: 0 if any issues created or dry run, 1 if all failed
    if not args.dry_run and result.total_created == 0 and result.total_candidates > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    _cli()
