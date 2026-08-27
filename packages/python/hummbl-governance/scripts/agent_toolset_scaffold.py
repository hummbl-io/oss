#!/usr/bin/env python3
"""Helper to onboard the approved hummbl-governance agent toolset in any repository."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any, Dict
from urllib.parse import urlparse


TOOLSET_FILES: Dict[str, str] = {
    "scripts/issue_pr_draft_coverage.py": "Issue/PR draft coverage + promotion pipeline",
    "scripts/pr_census.py": "PR and branch drift snapshot",
    "scripts/claim_drift.py": "Claim/lineage drift detection",
    "scripts/check-dependencies.py": "Dependency drift and pinning checks",
    "scripts/anvil_git_signing_audit.py": "Git signing / toolchain health",
    "scripts/audit-github-actions.py": "GitHub Actions health diagnostics",
    "scripts/financial_pulse.py": "Spend/usage telemetry",
    "scripts/ops/keepalive_fleet_loop.py": "Fleet keepalive watchdog",
    "hummbl_governance/services/health.py": "Runtime health surface",
    "hummbl_governance/services/scheduler.py": "Scheduler wiring and state",
    "hummbl_governance/bus/bus_writer.py": "Canonical bus write surface",
    "hummbl_governance/bus/bus_verifier.py": "Bus integrity checks",
    "hummbl_governance/quality/monitor.py": "Quality telemetry producer",
    "hummbl_governance/quality/analyzer.py": "Quality signal generator",
    "hummbl_governance/state_authority.py": "Authority checks and guardrails",
}


REPO_MARKERS = (
    ".git",
    "hummbl.repo.yaml",
    "pyproject.toml",
)


def find_repo_root(path: Path) -> Path:
    """Return the nearest repository root at or above *path*."""
    current = path.resolve()
    if current.is_file():
        current = current.parent

    for candidate in (current, *current.parents):
        if any((candidate / marker).exists() for marker in REPO_MARKERS):
            return candidate
    return current


def repo_default_name(repo_path: Path) -> str:
    remote = (repo_path / ".git" / "config")
    if not remote.exists():
        return "<owner>/<repo>"
    text = remote.read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("url = "):
            continue
        url = line.split("=", 1)[1].strip().rstrip("/")
        if url.startswith("git" + "@" + "github.com:"):
            repo_name = url.removeprefix("git" + "@" + "github.com:")
        else:
            parsed = urlparse(url)
            if parsed.hostname != "github.com":
                continue
            repo_name = parsed.path.lstrip("/")
        if repo_name.endswith(".git"):
            repo_name = repo_name[:-4]
        if len(repo_name.split("/")) == 2 and all(repo_name.split("/")):
            return repo_name
    return "<owner>/<repo>"


def status_for_repo(repo_root: Path) -> Dict[str, Any]:
    out: Dict[str, Any] = {"present": [], "missing": []}
    for relpath, reason in TOOLSET_FILES.items():
        root_match = repo_root / relpath
        nested_match = repo_root / "hummbl-governance" / relpath
        if root_match.exists():
            out["present"].append({
                "path": relpath,
                "why": reason,
                "resolved_path": str(root_match),
            })
        elif nested_match.exists():
            out["present"].append({
                "path": relpath,
                "why": reason,
                "resolved_path": str(nested_match),
            })
        else:
            out["missing"].append({"path": relpath, "why": reason})
    out["summary"] = {
        "present_count": len(out["present"]),
        "missing_count": len(out["missing"]),
        "total": len(TOOLSET_FILES),
    }
    return out


def detect_docs_root(repo_root: Path) -> Path:
    doc_roots = [
        repo_root / "hummbl-governance" / "docs",
        repo_root / "hummbl-governance" / "DOCS",
        repo_root / "docs",
        repo_root / "DOCS",
    ]
    for doc_root in doc_roots:
        nested = doc_root / "operations"
        if nested.exists():
            return nested
    return (repo_root / "docs" / "operations")


def print_table(repo_root: Path, status: Dict[str, Any]) -> str:
    repo = repo_root
    lines = [
        f"# Toolset status for `{repo}`",
        "",
        f"- Present: {status['summary']['present_count']}/{status['summary']['total']}",
        f"- Missing: {status['summary']['missing_count']}",
        "",
        "## Present",
    ]
    if status["present"]:
        lines.extend([""] + ["- " + item["path"] for item in status["present"]])
    else:
        lines.append("")
        lines.append("- None")

    lines.extend(["", "## Missing", ""])
    if status["missing"]:
        lines.extend(["- " + item["path"] + f" — {item['why']}" for item in status["missing"]])
    else:
        lines.append("- None")
    return "\n".join(lines)


def write_template(repo_root: Path, template_path: Path, force: bool) -> str:
    target = detect_docs_root(repo_root) / "AGENT_TOOLSET_STARTER.md"
    if target.exists() and not force:
        return f"skipped: exists: {target}"

    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        shutil.copyfile(template_path, target)
    except shutil.SameFileError:
        return f"skipped: template source is target: {target}"
    return f"written: {target}"


def template_candidates(repo_root: Path, script_root: Path) -> list[Path]:
    """Return starter-doc template candidates in repo-native order."""
    script_repo_root = find_repo_root(script_root)
    bases = [
        repo_root / "hummbl-governance",
        repo_root,
        script_repo_root / "hummbl-governance",
        script_repo_root,
        script_root / "hummbl-governance",
        script_root,
    ]
    candidates: list[Path] = []
    seen: set[Path] = set()
    for base in bases:
        for docs_dir in ("docs", "DOCS"):
            candidate = base / docs_dir / "operations" / "AGENT_TOOLSET_STARTER.md"
            if candidate not in seen:
                candidates.append(candidate)
                seen.add(candidate)
    return candidates


def resolve_template_source(repo_root: Path, script_root: Path) -> Path:
    for candidate in template_candidates(repo_root, script_root):
        if candidate.exists():
            return candidate
    raise SystemExit("AGENT_TOOLSET_STARTER.md template not found")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scaffold/check agent toolset onboarding.")
    parser.add_argument("--repo", default=".", help="Repository root to evaluate")
    parser.add_argument("--format", default="table", choices=["table", "json"])
    parser.add_argument("--copy-template", action="store_true", help="Copy starter doc into repo")
    parser.add_argument("--force-template", action="store_true", help="Overwrite template if already present")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_path = Path(args.repo).resolve()
    if not repo_path.exists():
        raise SystemExit(f"repo path not found: {repo_path}")
    repo_root = find_repo_root(repo_path)

    status = status_for_repo(repo_root)
    report = {"repo": str(repo_root), "repo_name": repo_default_name(repo_root), "toolset": status}

    if args.copy_template:
        script_root = Path(__file__).resolve().parent
        template_source = resolve_template_source(repo_root, script_root)
        report["template_source"] = str(template_source)
        report["template_result"] = write_template(repo_root, template_source, args.force_template)

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(print_table(repo_root, status))
        if status["missing"]:
            print("\nNext step for this repo: add missing paths or record approved repo-native replacements.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
