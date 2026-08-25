#!/usr/bin/env python3
"""Claim and documentation drift checks.

The script is intentionally conservative: it only flags low-confidence, likely
high-impact wording patterns and surfaces them as review-facing signals.

It is designed to be safe under constrained automation and can run without git
remotely by using local file snapshots only.
"""

from __future__ import annotations

import argparse
import datetime as dt
import difflib
import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


HIGH_IMPACT_PATTERNS = [
    re.compile(r"\b\d{2,7}\s+(?:tests|modules|features|checks|claims|verifications)\b", re.IGNORECASE),
    re.compile(r"\bzero\s+(?:risk|vulnerability|dependency|bugs?|security|defect)s?\b", re.IGNORECASE),
    re.compile(r"\bguarantee[d]?\b|\ball ways?\b|\bnever\b|\balways\b", re.IGNORECASE),
    re.compile(r"\b(ISO|SOC|NIST|GDPR|HIPAA|EU AI Act|EU AI)\s*(?:Certified|compliant|compliance)\b", re.IGNORECASE),
]


RECEIPT_HINT_TOKENS = (
    "source-candidate",
    "verified",
    "receipt",
    "attestation",
    "evidence",
    "needs_receipt",
)


@dataclass
class ClaimFinding:
    path: str
    line: int
    text: str
    pattern: str


def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        text=True,
        capture_output=True,
        check=False,
    )


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def scan_file_for_claims(path: Path) -> list[ClaimFinding]:
    findings: list[ClaimFinding] = []
    lines = load_text(path).splitlines()
    for i, line in enumerate(lines, 1):
        for pattern in HIGH_IMPACT_PATTERNS:
            if pattern.search(line):
                low = line.lower()
                has_receipt_hint = any(token in low for token in RECEIPT_HINT_TOKENS)
                if has_receipt_hint:
                    continue
                findings.append(
                    ClaimFinding(
                        path=str(path),
                        line=i,
                        text=line.strip(),
                        pattern=pattern.pattern,
                    )
                )
    return findings


def file_paths(root: Path) -> list[Path]:
    candidate_names = [
        "README.md",
        "SECURITY.md",
        "AGENTS.md",
        "CLAUDE.md",
        os.path.join("docs", "public-claims.md"),
        os.path.join("docs", "REPO_HEALTH.md"),
        os.path.join("docs", "public-repo-promotion", "PUBLIC_COLLABORATION_KERNEL_PLAN.md"),
    ]
    out: list[Path] = []
    for name in candidate_names:
        candidate = root / name
        if candidate.exists():
            out.append(candidate)
    return out


def list_tracked_candidate_changes(root: Path) -> list[tuple[str, str, str]]:
    proc = run(["git", "diff", "--name-only", "HEAD~1", "HEAD"], cwd=root)
    if proc.returncode != 0:
        return []
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def read_previous_snapshot(path: Path, root: Path) -> list[str]:
    rel = path.relative_to(root)
    git_cmd = ["git", "show", f"HEAD~1:{rel.as_posix()}"]
    proc = run(git_cmd, cwd=root)
    if proc.returncode != 0:
        return []
    return proc.stdout.splitlines()


def drift_from_history(path: Path, root: Path) -> list[str]:
    current_lines = load_text(path).splitlines()
    previous_lines = read_previous_snapshot(path, root)
    if not previous_lines:
        return []
    diff = difflib.unified_diff(previous_lines, current_lines, lineterm="", n=0)
    drift_lines: list[str] = []
    for line in diff:
        if line.startswith("+") and not line.startswith("+++"):
            drift_lines.append(line[1:])
    return drift_lines


def compile_report(root: Path) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    drift_file_count = 0
    for path in file_paths(root):
        local_claims = scan_file_for_claims(path)
        drift_lines = drift_from_history(path, root)
        if drift_lines:
            drift_file_count += 1
        for item in local_claims:
            findings.append(
                {
                    "path": item.path,
                    "line": item.line,
                    "text": item.text,
                    "pattern": item.pattern,
                    "drift_signal": "lineage delta likely present" if drift_lines else "manual review requested",
                }
            )

    tracked_changes = list_tracked_candidate_changes(root)
    warnings: list[str] = []
    if not root.joinpath(".git").exists():
        warnings.append("repository metadata missing; history-based checks are disabled")
    if tracked_changes:
        warnings.append(f"tracked diff files: {len(tracked_changes)}")
        for changed in tracked_changes:
            candidate = (root / changed)
            if str(candidate).endswith((".md", ".txt", ".rst")) and candidate.exists():
                findings.append(
                    {
                        "path": str(candidate),
                        "line": 1,
                        "text": "file changed since HEAD~1",
                        "pattern": "git-diff",
                        "drift_signal": "verify claims/receipts before promotion",
                    }
                )

    status = "pass" if not findings else "needs_review"
    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "repo_root": str(root),
        "status": status,
        "checked_files": [str(path) for path in file_paths(root)],
        "drift_file_count": drift_file_count,
        "findings": findings,
        "warnings": warnings,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Detect potential claim/lineage drift")
    parser.add_argument(
        "--repo",
        default=".",
        help="Repository root for claim scan",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON summary",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when drift findings exist",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.repo).resolve()
    if not root.exists():
        raise SystemExit(f"repository root not found: {root}")

    report = compile_report(root)
    findings = report["findings"]
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"Repo: {report['repo_root']}")
        print(f"Status: {report['status']}")
        print(f"Checked files: {len(report['checked_files'])}")
        print(f"Findings: {len(findings)}")
        for item in findings:
            print(f"- {item['path']}:{item['line']} -> {item['text']}")
        if report["warnings"]:
            print("Warnings:")
            for warning in report["warnings"]:
                print(f"  - {warning}")

    if args.strict and findings:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
