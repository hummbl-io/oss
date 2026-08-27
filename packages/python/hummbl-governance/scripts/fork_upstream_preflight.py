#!/usr/bin/env python3
"""Third-Party Fork & Upstream Contribution Protocol v0.1 — Preflight Gate.

Implements the mandatory preflight from
docs/third-party-fork-upstream-contribution-protocol-v0.1.md

Usage:
    python scripts/fork_upstream_preflight.py --repo /path/to/fork [--upstream <org/repo>]
    python scripts/fork_upstream_preflight.py --repo /path/to/fork --json

Exit codes:
    0 = preflight pass
    1 = preflight fail (do not proceed with external action)
    2 = operational error (bad path, git failure)
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROTOCOL_VERSION = "0.1"

AUTHORITY_DOCS = [
    "README.md",
    "README.rst",
    "CONTRIBUTING.md",
    "CONTRIBUTING.rst",
    "CODE_OF_CONDUCT.md",
    "SECURITY.md",
    "SUPPORT.md",
    "GOVERNANCE.md",
    "LICENSE",
    "LICENSE.md",
    "AGENTS.md",
    "CLAUDE.md",
]

TEMPLATE_DIRS = [".github/ISSUE_TEMPLATE", ".github"]
PR_TEMPLATE_NAMES = [
    "PULL_REQUEST_TEMPLATE.md",
    "pull_request_template.md",
    "PULL_REQUEST_TEMPLATE",
]


def run_git(repo: Path, *args: str) -> str:
    """Run a git command in the repo and return stdout."""
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def get_remotes(repo: Path) -> dict[str, str]:
    """Return {remote_name: url} for the repo."""
    out = run_git(repo, "remote", "-v")
    remotes: dict[str, str] = {}
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 2:
            remotes[parts[0]] = parts[1]
    return remotes


def classify_repo(remotes: dict[str, str]) -> tuple[str, str]:
    """Classify the repository relationship. Returns (classification, evidence)."""
    origin = remotes.get("origin", "")
    upstream = remotes.get("upstream", "")

    if "hummbl-io" in origin or "hummbl-dev" in origin:
        if upstream:
            return "active-third-party-fork", f"origin={origin}, upstream={upstream}"
        return "hummbl-native", f"origin={origin}, no upstream remote"

    if upstream:
        return "active-third-party-fork", f"origin={origin}, upstream={upstream}"

    return "independent-repo", f"origin={origin}, no upstream remote"


def read_authority_docs(repo: Path) -> dict[str, str | None]:
    """Read authority documents from the repo root. Returns {filename: content_or_None}."""
    docs: dict[str, str | None] = {}
    for name in AUTHORITY_DOCS:
        path = repo / name
        if path.exists():
            docs[name] = path.read_text(encoding="utf-8", errors="replace")[:5000]
        else:
            docs[name] = None
    return docs


def check_pr_templates(repo: Path) -> list[str]:
    """Check for PR template files."""
    found = []
    for d in TEMPLATE_DIRS:
        for name in PR_TEMPLATE_NAMES:
            path = repo / d / name
            if path.exists():
                found.append(str(path.relative_to(repo)))
    return found


def extract_rules(docs: dict[str, str | None]) -> dict[str, str]:
    """Extract operative rules from authority documents. Returns {rule: determination}."""
    rules: dict[str, str] = {}
    contributing = docs.get("CONTRIBUTING.md") or ""

    rules["unsolicited_prs_permitted"] = "unknown" if not contributing else "check-contributing"
    rules["issue_first_required"] = "unknown"
    rules["ai_disclosure_required"] = "unknown"
    rules["dco_signoff_required"] = "unknown"
    rules["cla_required"] = "unknown"

    lower = contributing.lower()
    if "signed-off-by" in lower or "dco" in lower:
        rules["dco_signoff_required"] = "yes"
    if "cla" in lower and "contributor license agreement" in lower:
        rules["cla_required"] = "yes"
    if "ai-generated" in lower or "ai generated" in lower:
        rules["ai_disclosure_required"] = "yes"
    if "issue first" in lower or "open an issue" in lower or "before submitting" in lower:
        rules["issue_first_required"] = "yes"

    return rules


def verify_topology(remotes: dict[str, str]) -> tuple[bool, str]:
    """Verify remote topology. Returns (ok, message)."""
    if "origin" not in remotes:
        return False, "no origin remote configured"
    if "upstream" not in remotes:
        return False, "no upstream remote configured — run: git remote add upstream <url>"
    return True, f"origin={remotes['origin']}, upstream={remotes['upstream']}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Third-Party Fork & Upstream Contribution Protocol v0.1 Preflight")
    parser.add_argument("--repo", required=True, help="Path to the fork repository")
    parser.add_argument("--upstream", help="Upstream org/repo (e.g., SakanaAI/AI-Scientist-v2)")
    parser.add_argument("--json", action="store_true", help="Output receipt as JSON")
    parser.add_argument("--agent", default=os.environ.get("USER", "unknown"))
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    if not repo.exists():
        print(f"ERROR: repo path does not exist: {repo}", file=sys.stderr)
        return 2

    if not (repo / ".git").exists():
        print(f"ERROR: not a git repository: {repo}", file=sys.stderr)
        return 2

    try:
        remotes = get_remotes(repo)
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    classification, evidence = classify_repo(remotes)
    docs = read_authority_docs(repo)
    pr_templates = check_pr_templates(repo)
    rules = extract_rules(docs)
    topology_ok, topology_msg = verify_topology(remotes)

    docs_read = [k for k, v in docs.items() if v is not None]
    docs_missing = [k for k, v in docs.items() if v is None]

    fail_closed = classification == "active-third-party-fork" and not topology_ok
    unknown_rules = [k for k, v in rules.items() if v == "unknown"]
    needs_escalation = bool(unknown_rules) or fail_closed

    receipt = {
        "protocol_version": PROTOCOL_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent": args.agent,
        "repository": str(repo),
        "upstream": remotes.get("upstream", args.upstream or "NOT_CONFIGURED"),
        "classification": classification,
        "classification_evidence": evidence,
        "authority_documents_read": docs_read,
        "authority_documents_missing": docs_missing,
        "pr_templates_found": pr_templates,
        "operative_rules": rules,
        "remote_topology_verified": topology_ok,
        "topology_message": topology_msg,
        "preflight_pass": not needs_escalation,
        "operator_escalation": needs_escalation,
        "escalation_reasons": (
            [f"unknown_rule: {r}" for r in unknown_rules] + (["topology_not_verified"] if fail_closed else [])
        ),
    }

    if args.json:
        print(json.dumps(receipt, indent=2))
    else:
        print(f"Protocol v{PROTOCOL_VERSION} Preflight")
        print(f"  Repository:      {repo}")
        print(f"  Classification:  {classification}")
        print(f"  Docs read:       {len(docs_read)}/{len(AUTHORITY_DOCS)}")
        print(f"  Docs missing:    {len(docs_missing)}")
        print(f"  PR templates:    {pr_templates or 'none'}")
        print(f"  Topology:        {'OK' if topology_ok else 'FAIL'} — {topology_msg}")
        print(f"  Unknown rules:   {unknown_rules or 'none'}")
        print(f"  Preflight:       {'PASS' if receipt['preflight_pass'] else 'FAIL'}")
        if needs_escalation:
            print(f"  Escalation:      REQUIRED — {receipt['escalation_reasons']}")

    return 0 if receipt["preflight_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
