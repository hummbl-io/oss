# Copyright 2024-2026 HUMMBL, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

"""Coverage matrix evidence-cell validator.

Inspects every code-reference in matrix Evidence cells and classifies as:
  - VALID — resolves against known CLI / file system / spec-doc set
  - DRAFT — already explicitly marked [DRAFT] or "planned"
  - UNRESOLVABLE — claims a CLI flag or path that does not exist

Stdlib-only. Implements hummbl-governance#29 — validate or relabel draft cells.

The validator reads compliance_mapper.py's argparse surface to determine what
flags exist. Unresolvable cells are reported for manual relabeling.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

# Actual compliance_mapper CLI surface (parsed from main() argparse).
# These are the only flags that resolve. Anything else cited is unresolvable.
COMPLIANCE_MAPPER_FLAGS = {"--days", "--framework", "--dir", "--output"}
COMPLIANCE_MAPPER_FRAMEWORKS = {
    "soc2", "gdpr", "owasp", "nist-rmf", "eu-ai-act", "iso27001", "nist-csf"
}

# Patterns to extract code references from matrix files.
BACKTICK_RE = re.compile(r"`([^`\n]+)`")
GENERATED_MATRIX_REPORTS = {"README.md", "EVIDENCE_VALIDATION.md"}

# Patterns identifying claim types within backticks.
RE_COMPLIANCE_MAPPER = re.compile(r"^compliance_mapper\b")
RE_FILE_PATH = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_./-]*\.(py|md|json|toml|yaml|yml|tsv|jsonl)$")
RE_PYTHON_MODULE_PATH = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_/.]*\.py$")
RE_hummbl_governance_PATH = re.compile(r"^hummbl_governance/[a-zA-Z0-9_/.-]+$")
RE_DOCS_PATH = re.compile(r"^.*docs?/[a-zA-Z0-9_/.\-]+$")
RE_ENVVAR_OR_FLAG = re.compile(r"^[A-Z_]+_TOKEN$|^\[[a-z-]+\]$|^--[a-z][a-z0-9-]+$")
RE_DRAFT_MARKER = re.compile(r"\[DRAFT(?::[^\]]*)?\]|planned|not yet shipped", re.IGNORECASE)


def classify_compliance_mapper_invocation(text: str) -> tuple[str, str]:
    """Classify a compliance_mapper CLI invocation.

    Returns (status, reason). Status is one of "valid", "unresolvable".
    """
    # Extract --flag tokens from the invocation
    tokens = text.split()
    flags_in_text = {t for t in tokens if t.startswith("--")}
    # Any unknown flag → unresolvable
    unknown = flags_in_text - COMPLIANCE_MAPPER_FLAGS
    if unknown:
        return "unresolvable", f"unknown flag(s): {sorted(unknown)}"

    # If --framework is given, check the value
    fw_match = re.search(r"--framework\s+([a-z0-9-]+)", text)
    if fw_match:
        fw = fw_match.group(1)
        if fw not in COMPLIANCE_MAPPER_FRAMEWORKS and not fw.startswith("<"):
            return "unresolvable", f"unknown framework: {fw}"

    return "valid", "matches CLI surface"


REPO_ROOT = Path(__file__).resolve().parents[1]


def classify_reference(ref: str, repo_root: Path = REPO_ROOT) -> tuple[str, str]:
    """Classify a backtick-quoted reference. Returns (kind, status)."""
    # Strip wrapping whitespace
    ref = ref.strip()

    # Skip pure-prose backticks (e.g., `[DRAFT]`)
    if RE_DRAFT_MARKER.search(ref):
        return "draft-marker", "draft"

    # Compliance mapper invocations
    if RE_COMPLIANCE_MAPPER.match(ref):
        status, reason = classify_compliance_mapper_invocation(ref)
        return "compliance-mapper-cli", status

    # Python file paths
    if RE_PYTHON_MODULE_PATH.match(ref):
        if (repo_root / ref).is_file():
            return "file-path", "valid"
        return "file-path", "unresolvable"

    # hummbl-governance paths (broader)
    if RE_hummbl_governance_PATH.match(ref):
        return "hummbl-governance-path", "external-ref"

    # Docs path
    if RE_DOCS_PATH.match(ref):
        return "docs-path", "external-ref"

    # Env var or pip extra
    if RE_ENVVAR_OR_FLAG.match(ref):
        return "config-token", "valid"

    return "other", "uncategorized"


def scan_matrix(path: Path, repo_root: Path = REPO_ROOT) -> dict:
    """Scan a matrix file and return reference classification."""
    text = path.read_text(encoding="utf-8")
    refs: list[dict] = []

    for match in BACKTICK_RE.finditer(text):
        ref = match.group(1)
        kind, status = classify_reference(ref, repo_root)
        # Skip uninteresting categories
        if kind in ("draft-marker", "config-token"):
            continue
        if kind == "other" and len(ref) < 5:
            # Skip noise like `id`, `N/A`
            continue
        refs.append({
            "ref": ref,
            "kind": kind,
            "status": status,
        })

    return {
        "path": str(path),
        "refs": refs,
        "by_status": dict(Counter(r["status"] for r in refs)),
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--matrix-dir", type=Path, default=Path("docs/coverage"))
    p.add_argument("--format", choices=("human", "json"), default="human")
    p.add_argument("--strict", action="store_true",
                   help="Exit 1 if any unresolvable refs found")
    args = p.parse_args(argv)

    files = sorted(
        f for f in args.matrix_dir.glob("*.md") if f.name not in GENERATED_MATRIX_REPORTS
    )
    fleet_unresolvable = 0
    results = []
    for f in files:
        r = scan_matrix(f)
        results.append(r)
        fleet_unresolvable += r["by_status"].get("unresolvable", 0)

    if args.format == "json":
        print(json.dumps({"matrices": results, "fleet_unresolvable": fleet_unresolvable}, indent=2))
    else:
        for r in results:
            name = Path(r["path"]).name
            unresolvable = [x for x in r["refs"] if x["status"] == "unresolvable"]
            ok_count = sum(1 for x in r["refs"] if x["status"] == "valid")
            print(f"\n=== {name} (refs total={len(r['refs'])}, valid={ok_count}, unresolvable={len(unresolvable)}) ===")
            if unresolvable:
                for u in unresolvable[:30]:
                    print(f"  ✗ [{u['kind']}] {u['ref']}")
        print()
        print(f"FLEET UNRESOLVABLE: {fleet_unresolvable}")

    return 1 if (args.strict and fleet_unresolvable > 0) else 0


if __name__ == "__main__":
    sys.exit(main())
