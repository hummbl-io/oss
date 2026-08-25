#!/usr/bin/env python3
"""GitHub Actions workflow health and posture audit."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path


SENSITIVE_HINTS = ("token", "secret", "password", "ghp_", "aws_", "AKIA")
REQUIRED_KEYS = ("on", "jobs")


@dataclass
class WorkflowFinding:
    workflow: str
    filename: str
    message: str
    severity: str


def iter_workflow_files(root: Path) -> list[Path]:
    workflows = root / ".github" / "workflows"
    if not workflows.exists():
        return []
    return sorted([item for item in workflows.iterdir() if item.suffix in {".yml", ".yaml"}])


def parse_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines()]


def audit_text(text: str) -> list[WorkflowFinding]:
    findings: list[WorkflowFinding] = []
    lines = parse_lines(text)
    has_trigger = any(line.startswith("on:") for line in lines)
    has_jobs = any(line.startswith("jobs:") for line in lines)

    if not has_trigger:
        findings.append(WorkflowFinding("unknown", "", "workflow has no on/trigger block", "high"))
    if not has_jobs:
        findings.append(WorkflowFinding("unknown", "", "workflow has no jobs block", "high"))

    for line in lines:
        lowered = line.lower()
        if any(token in lowered for token in SENSITIVE_HINTS):
            # Skip harmless workflow syntax values like github.token
            if "github.token" in lowered:
                continue
            findings.append(WorkflowFinding("unknown", "", f"sensitive-token-like text: {line}", "medium"))

    # Simple quality checks by text heuristics
    if not any("checkout@v4" in line.lower() for line in lines):
        findings.append(WorkflowFinding("unknown", "", "checkout action not found", "low"))
    if not any("setup-python" in line for line in lines):
        findings.append(WorkflowFinding("unknown", "", "python setup action not found", "low"))
    return findings


def audit_workflow(path: Path) -> list[WorkflowFinding]:
    text = path.read_text(encoding="utf-8", errors="replace")
    findings = audit_text(text)
    workflow_name = ""
    lines = text.splitlines()
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("name:"):
            workflow_name = stripped.split(":", 1)[1].strip().strip('"')
            break
    for item in findings:
        item.workflow = workflow_name or path.name
        item.filename = path.as_posix()
    return findings


def score_findings(findings: list[WorkflowFinding]) -> tuple[str, int]:
    high = sum(1 for item in findings if item.severity == "high")
    medium = sum(1 for item in findings if item.severity == "medium")
    low = sum(1 for item in findings if item.severity == "low")
    if high:
        return "pass_with_warnings", 70 - (high * 30) - (medium * 5) - (low * 2)
    if medium:
        return "pass_with_warnings", 85 - (medium * 10) - (low * 2)
    return "pass", max(100 - low * 2, 70)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit workflows for structural and posture issues")
    parser.add_argument("--repo", default=".", help="Repository root")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    parser.add_argument("--strict", action="store_true", help="Fail if findings exist")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.repo).resolve()
    workflows = iter_workflow_files(root)
    all_findings: list[WorkflowFinding] = []
    for workflow in workflows:
        all_findings.extend(audit_workflow(workflow))

    summary = {
        "repo": str(root),
        "workflow_count": len(workflows),
        "finding_count": len(all_findings),
    }
    if all_findings:
        by_severity = {level: 0 for level in ["high", "medium", "low"]}
        for item in all_findings:
            by_severity[item.severity] = by_severity.get(item.severity, 0) + 1
        summary["by_severity"] = by_severity
        summary["status"], summary["health_score"] = score_findings(all_findings)
        summary["findings"] = [f.__dict__ for f in all_findings]
    else:
        summary["status"] = "pass"
        summary["health_score"] = 100
        summary["findings"] = []

    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print(f"Workflows: {summary['workflow_count']}")
        print(f"Status: {summary['status']}")
        print(f"Health score: {summary['health_score']}")
        for item in all_findings:
            print(f"- {item.workflow} [{item.severity}] {item.message}")

    if args.strict and all_findings:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
