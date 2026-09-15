"""Validate intel_type metadata at research and coordination boundaries."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

TERMS = {
    "HUMINT",
    "OSINT",
    "SIGINT",
    "TECHINT",
    "MASINT",
    "IMINT",
    "GEOINT",
    "CYBINT",
    "GITINT",
    "BUSINT",
    "OPSINT",
    "CODEINT",
    "LOGINT",
    "REGINT",
    "FININT",
    "TOPOINT",
}
INTEL_TYPE = re.compile(r"(?im)^\s*(?:intel_type|intel-type)\s*:\s*([^#\s,]+)")
TOPOLOGY = re.compile(r"(?i)(?:topology|filesystem|file system|repository layout|repo layout)")


def files_from(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_dir():
            for pattern in ("*.md", "*.yaml", "*.yml", "*.json"):
                files.extend(path.rglob(pattern))
        elif path.is_file():
            files.append(path)
    return sorted(set(files))


def validate(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    match = INTEL_TYPE.search(text)
    if not match:
        return ["missing intel_type"]

    values = [item.strip().upper() for item in match.group(1).split("|")]
    errors: list[str] = []
    unknown = sorted(set(values) - TERMS)
    if unknown:
        errors.append(f"unknown intel_type: {', '.join(unknown)}")
    if "GEOINT" in values and TOPOLOGY.search(text):
        errors.append("GEOINT cannot classify repository/filesystem topology; use TOPOINT")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()
    failures = 0
    checked = 0
    for path in files_from(args.paths):
        checked += 1
        for error in validate(path):
            failures += 1
            print(f"FAIL\t{path}\t{error}")
    print(f"CHECKED={checked} FAILURES={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
