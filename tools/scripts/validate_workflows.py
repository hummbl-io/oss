#!/usr/bin/env python3
"""Validate GitHub Actions workflow files for SHA-pinning and hygiene.

Checks every .github/workflows/*.yml for:
  1. SHA-pinned actions (rejects @vN, @main, @stable, @latest, @master, etc.)
  2. ASCII-only content (flags non-ASCII with line number + code point)
  3. LF line endings (flags CRLF)
  4. Referenced environments exist on the repo (via gh api)
  5. Quoted "on": key (warns on unquoted on: to avoid YAML 1.1 boolean parsing)

Hard failures (exit 1): SHA-pin violations, non-ASCII, CRLF.
Warnings (exit 0 if only these): environment-not-found, unquoted on:.

Context: hummbl-io/oss has sha_pinning_required: true. On 2026-08-21, four
consecutive runs failed with startup_failure because workflows used tag-pinned
actions (e.g. @v4) instead of 40-char commit SHAs. This validator catches those
conditions before tag push.
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


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate GitHub Actions workflow files.")
    ap.add_argument("--repo", default="hummbl-io/oss")
    ap.add_argument("--workflows-dir", default=".github/workflows")
    args = ap.parse_args()

    wdir = Path(args.workflows_dir)
    print(f"Validating {wdir}/*.yml and *.yaml")
    print("=" * 32)
    print()

    if not wdir.is_dir():
        print("No workflows found.")
        return 0

    files = sorted(wdir.glob("*.yml")) + sorted(wdir.glob("*.yaml"))
    if not files:
        print("No workflows found.")
        return 0

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

    print("=" * 32)
    print(f"Summary: {fails} FAIL, {warns} WARN")
    if fails:
        print("Exit: 1 (failures found)")
        return 1
    print("Exit: 0 (all passed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
