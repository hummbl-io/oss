#!/usr/bin/env python3
"""Validate GitHub Actions workflow files for SHA-pinning and hygiene.

Checks every .github/workflows/*.yml for:
  1. SHA-pinned actions (rejects @vN, @main, @stable, @latest, @master, etc.)
  2. ASCII-only content (flags non-ASCII with line number + code point)
  3. LF line endings (flags CRLF)
  4. Referenced environments exist on the repo (via gh api)
  5. Quoted "on": key (warns on unquoted on: to avoid YAML 1.1 boolean parsing)
  6. With --check-python-packages: Python CI discovery and preview coverage

Hard failures (exit 1): SHA-pin violations, non-ASCII, CRLF, and enabled
Python package-coverage checks.
Warnings (exit 0 if only these): environment-not-found, unquoted on:.

Context: hummbl-io/oss has sha_pinning_required: true. On 2026-08-21, four
consecutive runs failed with startup_failure because workflows used tag-pinned
actions (e.g. @v4) instead of 40-char commit SHAs. This validator catches those
conditions before tag push.

Known limitation -- runtime-fetch vector: SHA-pinning verifies code identity
but does NOT prevent an action from fetching external resources at runtime
(e.g. curl | python3). The tj-actions/changed-files compromise (CVE-2025-30066,
March 2025) used exactly this vector -- a pinned SHA that fetched a remote
memory-dump script. Static analysis cannot detect runtime fetch. For that
vector, use StepSecurity Harden-Runner (network egress control) as a
complementary defense. This validator addresses the tag-modification vector
only.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

SHA_PIN_RE = re.compile(r"uses:\s+[\w.-]+(?:/[\w.-]+)+@[0-9a-fA-F]{40}\s*$")
USES_RE = re.compile(r"^\s*-?\s*uses:\s+(.+)$")
ON_RE = re.compile(r"^on:(\s|$)")
ENV_RE = re.compile(r"^\s*environment:\s+[\"']?([^\"'\s#]+)")
PACKAGE_NAME_RE = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_.-]*")


def strip_comment(line: str) -> str:
    """Strip an inline YAML comment (space+# to end of line)."""
    idx = line.find(" #")
    return line[:idx] if idx != -1 else line


def get_environments(repo: str):
    """Return (env_names, error_msg). error_msg is None on success."""
    try:
        r = subprocess.run(
            ["gh", "api", f"repos/{repo}/environments", "--jq", ".environments[].name"],
            capture_output=True, text=True, timeout=15,
        )
        if r.returncode != 0:
            return [], r.stderr.strip() or "gh api failed"
        return [e for e in r.stdout.splitlines() if e.strip()], None
    except FileNotFoundError:
        return [], "gh CLI not found"
    except subprocess.TimeoutExpired:
        return [], "gh api timed out"


def validate_file(path: Path, envs):
    """Return list of (severity, message, line_no_or_None)."""
    issues = []
    raw = path.read_bytes()
    if b"\r\n" in raw:
        issues.append(("FAIL", "CRLF line ending detected (use LF)", None))
    text = raw.decode("utf-8", errors="replace")
    for i, line in enumerate(text.split("\n"), 1):
        stripped = line.rstrip("\r")
        for ch in stripped:
            if ord(ch) > 127:
                name = unicodedata.name(ch, "UNKNOWN")
                issues.append(("FAIL", f"Non-ASCII: U+{ord(ch):04X} ({name}) on line {i}", i))
                break
        clean = strip_comment(stripped).rstrip()
        m = USES_RE.match(clean)
        if m:
            value = m.group(1).strip().strip('"').strip("'")
            if not value.startswith("./"):
                if not SHA_PIN_RE.match(f"uses: {value}"):
                    issues.append(("FAIL", f"SHA-pin violation: {value} (tag refs not allowed; pin to 40-char SHA)", i))
        if ON_RE.match(stripped):
            issues.append(("WARN", "Unquoted 'on:' key (use \"on\": to avoid YAML 1.1 boolean parsing)", i))
        em = ENV_RE.match(stripped)
        if em and envs is not None:
            env_name = em.group(1)
            if env_name not in envs:
                issues.append(("WARN", f"Environment '{env_name}' referenced but does not exist on repo", i))
    return issues


def _mapping_block(text: str, keys: tuple[str, ...]) -> list[str] | None:
    """Select a block mapping using this repo's two-space YAML indentation."""
    lines = text.splitlines()
    for depth, key in enumerate(keys):
        prefix = "  " * depth
        matches = [i for i, line in enumerate(lines)
                   if strip_comment(line).rstrip() == f"{prefix}{key}:"]
        if len(matches) != 1:
            return None
        start = matches[0] + 1
        end = start
        while end < len(lines):
            line = lines[end]
            if line.strip() and not line.lstrip().startswith("#"):
                if len(line) - len(line.lstrip(" ")) <= len(prefix):
                    break
            end += 1
        lines = lines[start:end]
    return lines


def validate_python_package_matrix(workflows_dir: Path):
    """Check the package sets used by this repo's Python CI.

    The main matrix discovers immediate package directories with tests/;
    preview uses an inline package list in jobs.test-preview.strategy.matrix.
    This is a deliberately narrow layout check, not a general YAML parser.
    Unsupported preview layouts fail instead of silently skipping coverage.
    Node matrices and the main job's extra Python 3.10 entries are unrelated.
    """
    ci_path = workflows_dir / "ci.yml"
    packages_dir = workflows_dir.resolve().parent.parent / "packages" / "python"
    if not ci_path.is_file():
        return [("FAIL", f"CI workflow not found: {ci_path}", None)]
    if not packages_dir.is_dir():
        return [("FAIL", f"Python packages directory not found: {packages_dir}", None)]

    directories = [p for p in packages_dir.iterdir() if p.is_dir()]
    actual = {p.name for p in directories if (p / "pyproject.toml").is_file()}
    if not actual:
        return [("FAIL", f"No Python package manifests found in {packages_dir}", None)]
    discovered = {p.name for p in directories if (p / "tests").is_dir()}
    issues = []

    def compare(label, packages):
        details = []
        if missing := sorted(actual - packages):
            details.append("missing=" + ",".join(missing))
        if extra := sorted(packages - actual):
            details.append("extra=" + ",".join(extra))
        if details:
            issues.append(("FAIL", f"Python CI {label} drift: " + "; ".join(details), None))

    compare("tests-directory discovery", discovered)
    text = ci_path.read_text(encoding="utf-8")
    # Match only the named preview job, not the Node package matrix or a
    # package: key inside a script. This is the indentation used by ci.yml.
    matrix = _mapping_block(text, ("jobs", "test-preview", "strategy", "matrix"))
    lines = [strip_comment(line).rstrip() for line in matrix or []
             if line.strip() and not line.lstrip().startswith("#")]
    entry = re.fullmatch(r"        package: *\[([^\]\n]*)\]", lines[0]) if len(lines) == 1 else None
    if entry is None:
        issues.append(("FAIL", "Expected one inline package list in jobs.test-preview.strategy.matrix", None))
        return issues
    packages = []
    for item in entry.group(1).split(","):
        item = item.strip()
        if len(item) >= 2 and item[0] in "\"'" and item[-1] == item[0]:
            item = item[1:-1]
        if not PACKAGE_NAME_RE.fullmatch(item):
            issues.append(("FAIL", "Invalid package name in Python preview matrix", None))
            return issues
        packages.append(item)
    if len(set(packages)) != len(packages):
        issues.append(("FAIL", "Duplicate package in Python preview matrix", None))
    compare("preview matrix", set(packages))
    return issues


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate GitHub Actions workflow files.")
    ap.add_argument("--repo", default="hummbl-io/oss")
    ap.add_argument("--workflows-dir", default=".github/workflows")
    ap.add_argument("--check-python-packages", action="store_true",
                    help="Check this monorepo's Python CI package coverage")
    args = ap.parse_args()

    wdir = Path(args.workflows_dir)
    print(f"Validating {wdir}/*.yml and *.yaml")
    print("=" * 32)
    print()

    if not wdir.is_dir():
        print("No workflows found.")
        return 1 if args.check_python_packages else 0

    files = sorted(wdir.glob("*.yml")) + sorted(wdir.glob("*.yaml"))
    if not files:
        print("No workflows found.")
        return 1 if args.check_python_packages else 0

    envs, env_err = get_environments(args.repo)
    env_list = envs if env_err is None else None
    if env_err:
        print(f"[WARN] Could not fetch environments: {env_err} (skipping environment check)")
        print()

    fails = 0
    warns = 0
    for f in files:
        for sev, msg, lineno in validate_file(f, env_list):
            loc = f"{f}:{lineno}" if lineno is not None else str(f)
            print(f"[{sev}] {loc}")
            print(f"  {msg}")
            print()
            if sev == "FAIL":
                fails += 1
            else:
                warns += 1

    if args.check_python_packages:
        for sev, msg, lineno in validate_python_package_matrix(wdir):
            print(f"[{sev}] {wdir / 'ci.yml'}: {msg}")
            fails += 1

    print("=" * 32)
    print(f"Summary: {fails} FAIL, {warns} WARN")
    if fails:
        print("Exit: 1 (failures found)")
        return 1
    print("Exit: 0 (all passed)")
    print("Note: SHA-pin check covers tag-modification vector only.")
    print("      For runtime-fetch vector, use StepSecurity Harden-Runner.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
