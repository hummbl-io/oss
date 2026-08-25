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

"""Auto-relabel unresolvable compliance_mapper invocations in matrices.

For each backtick-quoted compliance_mapper invocation citing a flag that does
not exist in the actual CLI (--export, --section, --control), prefix the cell
with [DRAFT — planned] to honestly signal these are spec-not-shipped.

Idempotent: skips invocations already prefixed.

Implements hummbl-governance#29 (validate or relabel) per operator framing
in b38e507 (draft scaffolds until validated).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Flags that don't exist in the real CLI as of compliance_mapper.py main()
UNREAL_FLAGS = ("--export", "--section", "--control", "--activity", "--subject")

DRAFT_PREFIX = "[DRAFT — planned per ADR-001] "
GENERATED_MATRIX_REPORTS = {"README.md", "EVIDENCE_VALIDATION.md"}

# Match a backtick-wrapped compliance_mapper invocation
INVOCATION_RE = re.compile(
    r"`(compliance_mapper\s+[^`]+)`"
)


def is_unresolvable(invocation: str) -> bool:
    """True if the invocation cites a flag not in the real CLI."""
    return any(f in invocation for f in UNREAL_FLAGS)


def already_drafted(prefix_context: str) -> bool:
    """Check if the surrounding text already marks this as draft."""
    return "[DRAFT" in prefix_context or "DRAFT —" in prefix_context


def relabel_file(path: Path, dry_run: bool = False) -> tuple[int, int]:
    """Apply relabeling. Returns (relabeled_count, skipped_count)."""
    text = path.read_text(encoding="utf-8")
    original = text
    relabeled = 0
    skipped = 0

    def replace(m: re.Match) -> str:
        nonlocal relabeled, skipped
        full = m.group(0)
        inv = m.group(1)
        if not is_unresolvable(inv):
            return full  # no change
        # Check if already drafted (look 60 chars before the match)
        start = m.start()
        prefix_window = text[max(0, start - 60):start]
        if already_drafted(prefix_window):
            skipped += 1
            return full
        relabeled += 1
        return f"`{DRAFT_PREFIX}{inv}`"

    new_text = INVOCATION_RE.sub(replace, text)
    if not dry_run and new_text != original:
        path.write_text(new_text, encoding="utf-8")
    return relabeled, skipped


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--matrix-dir", type=Path, default=Path("docs/coverage"))
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)

    files = sorted(
        f for f in args.matrix_dir.glob("*.md") if f.name not in GENERATED_MATRIX_REPORTS
    )
    total_relabeled = 0
    total_skipped = 0
    for f in files:
        n, s = relabel_file(f, dry_run=args.dry_run)
        if n or s:
            print(f"{f.name}: relabeled={n} skipped={s}")
        total_relabeled += n
        total_skipped += s

    print()
    print(f"TOTAL relabeled: {total_relabeled}")
    print(f"TOTAL skipped (already drafted): {total_skipped}")
    if args.dry_run:
        print("(dry-run; no files written)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
