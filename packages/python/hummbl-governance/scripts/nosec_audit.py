"""Audit nosec suppressions in production Python code.

Scans all .py files under the package directory (excluding tests) for
`# nosec` comments, extracts the Bandit rule code and justification,
and verifies each suppression has a documented justification.

Exit codes:
  0 — all nosec suppressions have justifications
  1 — one or more nosec suppressions lack justification
  2 — scanner error (e.g., package directory not found)

Usage:
  python scripts/nosec_audit.py [--package hummbl_governance] [--json]
  python scripts/nosec_audit.py --registry docs/nosec-registry.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


# Match: # nosec B123 — justification text
# or:    # nosec B123 - justification text
# or:    # nosec B123: justification text
# or:    # nosec (bare, no rule code)
_NOSEC_PATTERN = re.compile(
    r"#\s*nosec\s*"
    r"(?:(B\d+)\s*[—:-]\s*(.+))?"  # optional: rule code + justification
    r"\s*$",
    re.IGNORECASE,
)


@dataclass
class NosecSuppression:
    file: str
    line_no: int
    rule: str
    justification: str
    has_justification: bool
    source_line: str


def _scan_file(path: Path, repo_root: Path) -> list[NosecSuppression]:
    """Scan a single .py file for nosec comments."""
    suppressions: list[NosecSuppression] = []
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return suppressions

    # Compute relative path, falling back to absolute if not under repo_root
    try:
        rel_path = path.relative_to(repo_root).as_posix()
    except ValueError:
        rel_path = str(path)

    for line_no, line in enumerate(text.splitlines(), start=1):
        match = _NOSEC_PATTERN.search(line)
        if match:
            rule = match.group(1) or ""
            justification = (match.group(2) or "").strip()
            has_just = bool(justification)
            suppressions.append(NosecSuppression(
                file=rel_path,
                line_no=line_no,
                rule=rule,
                justification=justification,
                has_justification=has_just,
                source_line=line.strip(),
            ))
    return suppressions


def scan_package(package_dir: Path, repo_root: Path) -> list[NosecSuppression]:
    """Scan all .py files under package_dir for nosec comments.

    Excludes test files (test_*.py, *_test.py) and tests/ directories.
    """
    if not package_dir.is_dir():
        print(f"ERROR: Package directory not found: {package_dir}", file=sys.stderr)
        sys.exit(2)

    suppressions: list[NosecSuppression] = []
    for py_file in sorted(package_dir.rglob("*.py")):
        # Skip test files
        name = py_file.name
        if name.startswith("test_") or name.endswith("_test.py"):
            continue
        # Skip tests/ directories
        if "tests" in py_file.parts:
            continue
        suppressions.extend(_scan_file(py_file, repo_root))
    return suppressions


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit nosec suppressions in production code")
    parser.add_argument(
        "--package", type=str, default="hummbl_governance",
        help="Package directory to scan (default: hummbl_governance)",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output as JSON instead of human-readable",
    )
    parser.add_argument(
        "--registry", type=str, default="",
        help="Path to write a nosec registry JSON file",
    )
    parser.add_argument(
        "--strict", action="store_true",
        help="Exit 1 if any nosec lacks justification (default: warn only)",
    )
    args = parser.parse_args()

    repo_root = Path.cwd().resolve()
    package_dir = repo_root / args.package
    suppressions = scan_package(package_dir, repo_root)

    unjustified = [s for s in suppressions if not s.has_justification]

    if args.registry:
        registry = {
            "description": (
                "Registry of all nosec suppressions in production code. "
                "Review quarterly per ADR-007 and issue #137."
            ),
            "total": len(suppressions),
            "justified": len(suppressions) - len(unjustified),
            "unjustified": len(unjustified),
            "suppressions": [asdict(s) for s in suppressions],
        }
        registry_path = Path(args.registry)
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        with registry_path.open("w", encoding="utf-8") as f:
            json.dump(registry, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"WROTE {registry_path}")

    if args.json:
        print(json.dumps([asdict(s) for s in suppressions], indent=2))
    else:
        print(f"NOSEC AUDIT: {args.package}/")
        print(f"  Total suppressions: {len(suppressions)}")
        print(f"  Justified:          {len(suppressions) - len(unjustified)}")
        print(f"  Unjustified:        {len(unjustified)}")
        print()
        if suppressions:
            print(f"{'File':<55} {'Line':>5} {'Rule':<6} Justification")
            print("-" * 120)
            for s in suppressions:
                just = s.justification if s.has_justification else "*** MISSING ***"
                print(f"{s.file:<55} {s.line_no:>5} {s.rule or '?':<6} {just}")
        else:
            print("  (no nosec suppressions found)")

    if unjustified:
        if not args.json:
            print(f"\n::error::{len(unjustified)} nosec suppression(s) lack justification")
            for s in unjustified:
                print(f"::error::  {s.file}:{s.line_no} — no justification found")
        if args.strict:
            return 1
        return 0

    if suppressions and not args.json:
        print(f"\n::notice::All {len(suppressions)} nosec suppressions have justifications")
    return 0


if __name__ == "__main__":
    sys.exit(main())
