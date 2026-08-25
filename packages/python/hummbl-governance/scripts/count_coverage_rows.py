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

"""Authoritative row-marker counter for coverage matrices.

Counts ✅/🟡/⚪/⛔ glyphs in matrix data rows ONLY (excluding header rows,
separator rows, legend tables, and prose). Source of truth for matrix totals.

Stdlib-only. Output is JSON, one line per matrix.

Implements hummbl-governance#30 — generate or remove unverified totals.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

STATES = ("✅", "🟡", "⚪", "⛔")

ROW_RE = re.compile(r"^\s*\|[^|\n]+(?:\|[^|\n]*)+\|\s*$")
SEPARATOR_RE = re.compile(r"^\s*\|(?:\s*:?-{3,}:?\s*\|)+\s*$")
LEGEND_LABELS = ("Fulfilled", "Partial", "Boundary", "Out of scope")
GENERATED_MATRIX_REPORTS = {"README.md", "EVIDENCE_VALIDATION.md"}


def count_rows(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    n = len(lines)

    counts = {s: 0 for s in STATES}
    data_row_count = 0
    unmarked_rows = 0
    multi_glyph_rows: list[int] = []  # line numbers where a row has >1 glyph

    i = 0
    while i < n:
        line = lines[i]
        if not ROW_RE.match(line):
            i += 1
            continue
        # Skip if next line is separator (this line is a header)
        if i + 1 < n and SEPARATOR_RE.match(lines[i + 1]):
            i += 2
            continue
        # Skip separator rows themselves (defensive; covered above too)
        if SEPARATOR_RE.match(line):
            i += 1
            continue
        # Skip legend table rows: any cell exactly matches a legend label
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if any(c == lbl for c in cells for lbl in LEGEND_LABELS):
            i += 1
            continue
        # Skip the vertical summary table rows (e.g., "| ✅ Fulfilled | 5 |").
        # Distinguishing feature: cell 1 has a state glyph + label like "Fulfilled".
        first_cell = cells[0] if cells else ""
        if any(
            (state in first_cell and lbl in first_cell)
            for state in STATES
            for lbl in LEGEND_LABELS
        ):
            i += 1
            continue
        # Skip summary breakdown rows: rows with 3+ integer-only cells
        # (possibly bolded). Aggregate tables either look like
        # "| Model AI Governance | 4 | 2 | 2 | 0 |" (1 label + integer
        # cells) or "| I | General provisions | Art. 1–4 | 0 | 0 | 4 | 0 |"
        # (multiple label cells + integer cells). Either way, ≥3 integer
        # cells in a row is the summary-table fingerprint.
        def _is_int_cell(c: str) -> bool:
            c = c.strip().strip("*").strip()
            return c.isdigit() or (c.startswith("-") and c[1:].isdigit())

        int_cell_count = sum(1 for c in cells if _is_int_cell(c))
        if int_cell_count >= 3:
            i += 1
            continue

        # Data-row classification:
        # - A row with no state glyph at all is an UNMARKED data row. Per
        #   issue #30 acceptance criterion 4 ("Flag unmarked rows"), these
        #   are counted but tracked separately so the deletion-as-shortcut
        #   path is visible.
        # - A row with multiple state glyphs is ambiguous (one row, one
        #   state per ADR-001 row invariant); we count it once toward the
        #   FIRST state present and record the line number for review.
        glyphs_present = [s for s in STATES if s in line]
        data_row_count += 1
        if not glyphs_present:
            unmarked_rows += 1
            i += 1
            continue
        if len(glyphs_present) > 1:
            multi_glyph_rows.append(i + 1)
        # One row, one state — fix from peer P1 (Goodhart channel). The
        # earlier `line.count(state)` form let a row with `| ✅ ✅ ✅ |` tally
        # as 3 toward ✅, gradient-tilting toward glyph addition rather than
        # coverage improvement.
        counts[glyphs_present[0]] += 1
        i += 1

    return {
        "path": str(path),
        "rows_counted": data_row_count,
        "unmarked_rows": unmarked_rows,
        "multi_glyph_rows": multi_glyph_rows,
        "counts": counts,
        "total_markers": sum(counts.values()),
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--matrix-dir", type=Path, default=Path("docs/coverage"))
    p.add_argument("--format", choices=("json", "human"), default="human")
    args = p.parse_args(argv)

    files = sorted(
        f for f in args.matrix_dir.glob("*.md") if f.name not in GENERATED_MATRIX_REPORTS
    )
    fleet = {s: 0 for s in STATES}
    fleet_rows = 0

    results = []
    for f in files:
        r = count_rows(f)
        results.append(r)
        for s in STATES:
            fleet[s] += r["counts"][s]
        fleet_rows += r["rows_counted"]

    if args.format == "json":
        print(json.dumps({"matrices": results, "fleet_totals": fleet, "fleet_rows": fleet_rows}, indent=2))
    else:
        for r in results:
            name = Path(r["path"]).name
            c = r["counts"]
            print(
                f"{name:30s} rows={r['rows_counted']:3d}  "
                f"✅={c['✅']:3d}  🟡={c['🟡']:3d}  ⚪={c['⚪']:3d}  ⛔={c['⛔']:3d}"
            )
        print()
        print(
            f"{'FLEET TOTALS':30s} rows={fleet_rows:3d}  "
            f"✅={fleet['✅']:3d}  🟡={fleet['🟡']:3d}  ⚪={fleet['⚪']:3d}  ⛔={fleet['⛔']:3d}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
