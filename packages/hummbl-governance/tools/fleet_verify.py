#!/usr/bin/env python3
"""
tools/fleet_verify.py — Post-Batch Verification for Fleet-Wide Operations

Verifies that batch operations (init, remediation, field backfill) actually
landed across all repos. Addresses AAR recommendation: "Add a post-batch
verification step to all fleet-wide operations."

Usage:
    python tools/fleet_verify.py --check governance-stack
    python tools/fleet_verify.py --check adr-format
    python tools/fleet_verify.py --check missing-fields
    python tools/fleet_verify.py --check all
    python tools/fleet_verify.py --check governance-stack --json

Exit codes:
    0 — all repos pass
    1 — one or more repos have issues
    2 — error (API failure, etc.)
"""

import argparse
import json
import os
import subprocess
import sys
import time
import base64
from dataclasses import dataclass, field, asdict

ORG = "hummbl-dev"

# --- Data classes ---

@dataclass
class RepoCheck:
    repo: str
    archived: bool = False
    fork: bool = False
    checks: dict = field(default_factory=dict)
    issues: list = field(default_factory=list)

@dataclass
class FleetReport:
    total: int = 0
    checked: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    repos: list = field(default_factory=list)

# --- API helpers ---

def gh_api(endpoint):
    result = subprocess.run(["gh", "api", endpoint], capture_output=True, text=True)
    if result.returncode != 0:
        return None
    return json.loads(result.stdout)

def get_all_repos(org=ORG):
    """Get all non-fork repos (including archived)."""
    # Use gh repo list which works for both orgs and user accounts
    result = subprocess.run(
        ["gh", "repo", "list", org, "--limit", "200", "--json",
         "name,isFork,isArchived,isPrivate"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return []
    repos = json.loads(result.stdout)
    # Normalize keys to match what the rest of the code expects
    for r in repos:
        r["archived"] = r.get("isArchived", False)
        r["fork"] = r.get("isFork", False)
        r["private"] = r.get("isPrivate", True)
    return repos

def get_repo_tree(repo, org=ORG):
    """Get file tree for a repo."""
    data = gh_api(f"repos/{org}/{repo}/git/trees/HEAD?recursive=1")
    if not data:
        return []
    return [item["path"] for item in data.get("tree", [])]

def get_file_content(repo, path, org=ORG):
    """Get file content via API."""
    result = subprocess.run(
        ["gh", "api", f"repos/{org}/{repo}/contents/{path}", "--jq", ".content"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return None
    return base64.b64decode(result.stdout.strip()).decode()

# --- Check functions ---

def check_governance_stack(repo, tree, archived):
    """Check that all required governance files are present."""
    issues = []
    tree_lower = {p.lower() for p in tree}

    if archived:
        # Archived repos: KRINEIA.md, hummbl.repo.yaml, _receipts/ at minimum
        required = ["KRINEIA.md", "hummbl.repo.yaml", "_receipts/krineia/primary.jsonl"]
    else:
        required = [
            "CONSTITUTION.md",
            "KRINEIA.md",
            "hummbl.repo.yaml",
            "CODEOWNERS",
            "_receipts/krineia/primary.jsonl",
        ]

    for req in required:
        if req.lower() not in tree_lower:
            issues.append(f"MISSING: {req}")

    # Check for governance baseline ADR (any number, not just ADR-001)
    has_governance_adr = any("repo-governance-baseline" in p.lower() and "docs/adr/" in p.lower()
                             for p in tree)
    if not has_governance_adr and not archived:
        issues.append("MISSING: docs/adr/ADR-NNN-repo-governance-baseline.md (any number)")

    return issues

def check_adr_format(repo, tree):
    """Check ADR filenames and basic format."""
    issues = []
    import re

    adr_files = [p for p in tree if "docs/adr/" in p and p.endswith(".md")
                 and "ADR_INDEX" not in p.upper() and "ADR_TEMPLATE" not in p.upper()
                 and not os.path.basename(p).startswith("DRAFT")]

    if not adr_files:
        return issues  # No ADRs is not an error (some repos may not have any)

    # Patterns: standard ADR-NNN-title.md or domain-prefixed ADR-DOMAIN-NNN-title.md
    standard_pat = re.compile(r'^ADR-(\d{3})-([a-z0-9-]+)\.md$')
    domain_pat = re.compile(r'^ADR-([A-Z]{2,6}(?:-[A-Z]{2,6})?)-(\d{3})-([a-z0-9-]+)\.md$')

    # Check filenames and duplicates per-directory
    by_dir = {}
    for p in adr_files:
        basename = os.path.basename(p)
        parent = os.path.dirname(p)
        if parent not in by_dir:
            by_dir[parent] = set()

        m = standard_pat.match(basename)
        dm = domain_pat.match(basename)

        if not m and not dm:
            issues.append(f"NONSTANDARD_FILENAME: {basename}")
            continue

        # Extract identifier key for duplicate check
        if m:
            key = m.group(1)
        else:
            key = f"{dm.group(1)}-{dm.group(2)}"

        if key in by_dir[parent]:
            issues.append(f"DUPLICATE_NUMBER: ADR-{key}")
        else:
            by_dir[parent].add(key)

    return issues

def check_missing_fields(repo, tree):
    """Check that baseline ADRs have all required fields."""
    issues = []

    # Find baseline ADR(s) — only in docs/adr/, not docs/handoffs/
    adr_baselines = [p for p in tree if "docs/adr/" in p
                     and "repo-governance-baseline" in p.lower()
                     and p.endswith(".md")]

    for adr_path in adr_baselines:
        content = get_file_content(repo, adr_path)
        if not content:
            issues.append(f"FETCH_FAILED: {adr_path}")
            continue

        required_fields = ["**Status:**", "**Date:**", "**Decision owner:**",
                          "**Steward:**", "**Supersedes:**", "**Superseded by:**"]

        for field_marker in required_fields:
            if field_marker not in content:
                issues.append(f"MISSING_FIELD: {field_marker} in {adr_path}")

    return issues

# --- Main verify ---

def verify_fleet(check_type="all", org=ORG, output_json=False):
    """Run verification across the fleet."""
    repos = get_all_repos(org)
    if not repos:
        print("Error: could not fetch repos")
        return None, 2

    report = FleetReport(total=len(repos))

    for repo_info in repos:
        repo = repo_info["name"]
        archived = repo_info.get("archived", False)
        fork = repo_info.get("fork", False)

        check = RepoCheck(repo=repo, archived=archived, fork=fork)
        report.checked += 1

        if fork:
            report.skipped += 1
            continue

        # Get tree
        tree = get_repo_tree(repo, org)
        if not tree:
            check.issues.append("TREE_FETCH_FAILED")
            report.failed += 1
            report.repos.append(asdict(check))
            continue

        # Run requested checks
        if check_type in ("governance-stack", "all"):
            issues = check_governance_stack(repo, tree, archived)
            check.checks["governance_stack"] = len(issues) == 0
            check.issues.extend(issues)

        if check_type in ("adr-format", "all"):
            issues = check_adr_format(repo, tree)
            check.checks["adr_format"] = len(issues) == 0
            check.issues.extend(issues)

        if check_type in ("missing-fields", "all"):
            issues = check_missing_fields(repo, tree)
            check.checks["missing_fields"] = len(issues) == 0
            check.issues.extend(issues)

        if check.issues:
            report.failed += 1
        else:
            report.passed += 1

        report.repos.append(asdict(check))

        # Progress
        status = "OK" if not check.issues else f"ISSUES ({len(check.issues)})"
        if not output_json:
            print(f"  [{report.checked}/{report.total}] {repo}: {status}")

        time.sleep(0.2)  # Rate limit

    return report, 0

# --- CLI ---

def main():
    parser = argparse.ArgumentParser(
        description="Fleet Verification Tool — post-batch verification for fleet-wide operations"
    )
    parser.add_argument("--check", choices=["governance-stack", "adr-format", "missing-fields", "all"],
                        default="all", help="Type of check to run")
    parser.add_argument("--org", default=ORG, help="GitHub org")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--fail-on-issues", action="store_true", help="Exit 1 if any issues found")

    args = parser.parse_args()

    report, exit_code = verify_fleet(args.check, args.org, args.json)

    if exit_code != 0:
        sys.exit(exit_code)

    if args.json:
        print(json.dumps(asdict(report), indent=2))
    else:
        print("\n=== Fleet Verification Report ===")
        print(f"Total repos: {report.total}")
        print(f"Checked: {report.checked}")
        print(f"Passed: {report.passed}")
        print(f"Failed: {report.failed}")
        print(f"Skipped (forks): {report.skipped}")

        if report.failed > 0:
            print("\n--- Failed repos ---")
            for r in report.repos:
                if r["issues"]:
                    print(f"  {r['repo']} ({'archived' if r['archived'] else 'active'}):")
                    for issue in r["issues"]:
                        print(f"    - {issue}")

    if args.fail_on_issues and report.failed > 0:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
