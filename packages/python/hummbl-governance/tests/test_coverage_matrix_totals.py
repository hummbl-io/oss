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

"""Test that coverage matrix declared totals match counted row markers.

Implements hummbl-governance#30 enforcement: matrix totals must be mechanically
verifiable, not author-asserted.

Stdlib + pytest only.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
COVERAGE_DIR = REPO_ROOT / "docs" / "coverage"
SCRIPT = REPO_ROOT / "scripts" / "count_coverage_rows.py"
REPORT_SCRIPT = REPO_ROOT / "scripts" / "build_evidence_validation_report.py"

STATES = ("✅", "🟡", "⚪", "⛔")


def _run_counter() -> dict:
    """Invoke the count script and parse its JSON output."""
    import json as _json

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--format", "json", "--matrix-dir", str(COVERAGE_DIR)],
        capture_output=True,
        text=True,
        check=True,
    )
    return _json.loads(result.stdout)


def test_count_script_runs():
    """The counter script runs without error against current matrix dir."""
    data = _run_counter()
    assert "matrices" in data
    assert len(data["matrices"]) > 0


def test_report_builder_uses_posix_repo_relative_paths():
    """Report builder must produce stable matrix paths on Windows and POSIX."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("build_evidence_validation_report", REPORT_SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    matrix = REPO_ROOT / "docs" / "coverage" / "eu-ai-act.md"
    assert module._repo_relative_posix(matrix, REPO_ROOT) == "docs/coverage/eu-ai-act.md"


def test_no_unverified_totals_claim_in_readme():
    """README must not present aggregate counts without mechanical-verification marker.

    Specifically, the README must include the count script reference if it
    publishes any per-state count totals.
    """
    readme = (COVERAGE_DIR / "README.md").read_text(encoding="utf-8")
    # If README mentions ✅ count anywhere in a totals context, it must reference
    # the count script.
    has_total_claim = bool(re.search(r"\*\*\d+\s*✅", readme))
    if has_total_claim:
        assert "count_coverage_rows.py" in readme, (
            "README publishes aggregate count totals but does not reference "
            "scripts/count_coverage_rows.py as the source of truth"
        )


def test_fleet_total_marker_count_is_published():
    """Fleet count must be available via the count script."""
    data = _run_counter()
    fleet = data["fleet_totals"]
    assert all(s in fleet for s in STATES), f"Missing state in fleet totals: {fleet}"
    total = sum(fleet.values())
    assert total > 0, f"Fleet markers count is zero: {fleet}"


@pytest.mark.parametrize(
    "matrix_name",
    [
        "arizona-hb2394.md",
        "asean-ai-governance-guide.md",
        "australia-ai-ethics.md",
        "african-union-ai-strategy.md",
        "azerbaijan-ai-strategy.md",
        "brazil-pl2338.md",
        "california-ab-2013.md",
        "california-sb-53.md",
        "california-sb-942.md",
        "canada-aida.md",
        "ccpa-cpra.md",
        "chile-ai-bill.md",
        "china-algorithm-recommendation.md",
        "china-deep-synthesis.md",
        "china-genai-measures.md",
        "colorado-ai-act.md",
        "connecticut-sb2-sb5.md",
        "council-of-europe-ai-convention.md",
        "denmark-ai-act.md",
        "egypt-ai-strategy.md",
        "el-salvador-ai-promotion-law.md",
        "eu-ai-act.md",
        "g7-ai-code.md",
        "gdpr.md",
        "germany-mission-ki.md",
        "ieee-3119.md",
        "ieee-7001.md",
        "illinois-hb3773.md",
        "imda-agentic.md",
        "india-ai-governance-guidelines.md",
        "india-dpdp.md",
        "iowa-sf2417.md",
        "ireland-eu-ai-designation.md",
        "israel-ai-program.md",
        "iso-27001.md",
        "iso-42001.md",
        "iso-iec-22989.md",
        "iso-iec-23053.md",
        "iso-iec-23894.md",
        "iso-iec-38507.md",
        "iso-iec-42005.md",
        "iso-iec-5338.md",
        "iso-iec-5339.md",
        "italy-law-132-2025.md",
        "japan-ai-act.md",
        "kazakhstan-ai-law.md",
        "kentucky-krs42731.md",
        "latvia-ai-centre-law.md",
        "lithuania-ai-act.md",
        "maine-ai-chatbot.md",
        "malaysia-aige-guidelines.md",
        "malta-ai-regulations.md",
        "maryland-sb818.md",
        "mexico-chapultepec-principles.md",
        "netherlands-genai-vision.md",
        "new-hampshire-ch5d.md",
        "new-zealand-ai-strategy.md",
        "nigeria-ai-strategy.md",
        "nist-ai-rmf.md",
        "nist-csf.md",
        "north-carolina-eo24.md",
        "norway-ai-strategy.md",
        "nyc-ll144.md",
        "oecd-ai-principles.md",
        "owasp-llm.md",
        "peru-law-31814.md",
        "rwanda-ai-policy.md",
        "saudi-arabia-ai-strategy.md",
        "sf-ai-inventory-ordinance.md",
        "singapore-ai-verify.md",
        "singapore-model-ai-governance.md",
        "slovenia-ai-act.md",
        "soc2.md",
        "south-korea-ai-basic-act.md",
        "stride.md",
        "sweden-ai-strategy.md",
        "taiwan-ai-fundamental-act.md",
        "texas-traiga.md",
        "uk-ai-regulation-framework.md",
        "unesco-ai-ethics.md",
        "utah-ai-policy-act.md",
        "vermont-act101.md",
        "virginia-hb714.md",
        "owasp-agentic.md",
        "spain-ai-strategy.md",
        "finland-ai-strategy.md",
        "uae-ai-strategy.md",
        "switzerland-ai-strategy.md",
        "estonia-ai-strategy.md",
        "thailand-ai-strategy.md",
        "south-africa-ai-policy.md",
        "argentina-ai-plan.md",
        "hong-kong-ai-guidelines.md",
        "belgium-ai-strategy.md",
        "ophthalmic-ai.md",
    ],
)
def test_matrix_has_data_rows(matrix_name: str):
    """Every matrix must have at least one data row with a state glyph."""
    matrix = COVERAGE_DIR / matrix_name
    assert matrix.exists(), f"Matrix file missing: {matrix_name}"

    data = _run_counter()
    matching = [m for m in data["matrices"] if Path(m["path"]).name == matrix_name]
    assert len(matching) == 1, f"Counter did not produce a row for {matrix_name}"
    result = matching[0]
    assert result["rows_counted"] > 0, f"{matrix_name} has zero data rows counted"


def test_no_silent_zero_total_state():
    """Counter must report at least one ✅ across the fleet (not all-boundary)."""
    data = _run_counter()
    assert data["fleet_totals"]["✅"] > 0, (
        "Fleet has zero ✅ Fulfilled rows — either matrices are entirely "
        "boundary/draft, or the counter is broken"
    )


# ── Equality enforcement (closes the phantom-invariant gap from peer P1) ──
#
# Origin: hummbl-governance#32 Stage-3 peer review (multi-lens) flagged that
# the README claimed an equality test that did not exist — see
# `_internal/reviews/pr32-multilens/`. Each of 4 lens reviewers (measurement /
# operator / scott / popper) independently surfaced this as a P1: the
# README's "declared == counted" enforcement framing was structurally false
# because the test suite never parsed the README. This pair closes that gap.

# Matrix slug → README cell positions (column indices after stripping pipes)
# README table columns: 0=Framework, 1=Surface, 2=Rows, 3=✅, 4=🟡, 5=⚪,
# 6=Unmarked, 7=File
_README_TABLE_ROW_RE = re.compile(
    r"^\|\s*(?P<framework>[^|]+?)\s*\|[^|]+\|\s*(?P<rows>\d+)\s*\|\s*"
    r"(?P<fulfilled>\d+)\s*\|\s*(?P<partial>\d+)\s*\|\s*(?P<boundary>\d+)\s*\|\s*"
    r"(?P<unmarked>\d+)\s*\|.*?(?P<slug>[a-z0-9-]+)\.md",
    re.MULTILINE,
)


def _parse_readme_rows() -> dict:
    """Return {slug: {rows, ✅, 🟡, ⚪, unmarked}} extracted from README."""
    readme = (COVERAGE_DIR / "README.md").read_text(encoding="utf-8")
    out = {}
    for m in _README_TABLE_ROW_RE.finditer(readme):
        out[m.group("slug")] = {
            "rows": int(m.group("rows")),
            "✅": int(m.group("fulfilled")),
            "🟡": int(m.group("partial")),
            "⚪": int(m.group("boundary")),
            "unmarked": int(m.group("unmarked")),
        }
    return out


def test_readme_table_parses_all_matrices():
    """README table must list every matrix in `docs/coverage/`."""
    parsed = _parse_readme_rows()
    generated = {"README.md", "EVIDENCE_VALIDATION.md"}
    on_disk = {f.stem for f in COVERAGE_DIR.glob("*.md") if f.name not in generated}
    missing = on_disk - set(parsed)
    assert not missing, f"Matrices on disk but not in README table: {sorted(missing)}"


@pytest.mark.parametrize(
    "matrix_name",
    [
        "arizona-hb2394.md",
        "asean-ai-governance-guide.md",
        "australia-ai-ethics.md",
        "african-union-ai-strategy.md",
        "azerbaijan-ai-strategy.md",
        "brazil-pl2338.md",
        "california-ab-2013.md",
        "california-sb-53.md",
        "california-sb-942.md",
        "canada-aida.md",
        "ccpa-cpra.md",
        "chile-ai-bill.md",
        "china-algorithm-recommendation.md",
        "china-deep-synthesis.md",
        "china-genai-measures.md",
        "colorado-ai-act.md",
        "connecticut-sb2-sb5.md",
        "council-of-europe-ai-convention.md",
        "denmark-ai-act.md",
        "egypt-ai-strategy.md",
        "el-salvador-ai-promotion-law.md",
        "eu-ai-act.md",
        "g7-ai-code.md",
        "gdpr.md",
        "germany-mission-ki.md",
        "ieee-3119.md",
        "ieee-7001.md",
        "illinois-hb3773.md",
        "imda-agentic.md",
        "india-ai-governance-guidelines.md",
        "india-dpdp.md",
        "iowa-sf2417.md",
        "ireland-eu-ai-designation.md",
        "israel-ai-program.md",
        "iso-27001.md",
        "iso-42001.md",
        "iso-iec-22989.md",
        "iso-iec-23053.md",
        "iso-iec-23894.md",
        "iso-iec-38507.md",
        "iso-iec-42005.md",
        "iso-iec-5338.md",
        "iso-iec-5339.md",
        "italy-law-132-2025.md",
        "japan-ai-act.md",
        "kazakhstan-ai-law.md",
        "kentucky-krs42731.md",
        "latvia-ai-centre-law.md",
        "lithuania-ai-act.md",
        "maine-ai-chatbot.md",
        "malaysia-aige-guidelines.md",
        "malta-ai-regulations.md",
        "maryland-sb818.md",
        "mexico-chapultepec-principles.md",
        "netherlands-genai-vision.md",
        "new-hampshire-ch5d.md",
        "new-zealand-ai-strategy.md",
        "nigeria-ai-strategy.md",
        "nist-ai-rmf.md",
        "nist-csf.md",
        "north-carolina-eo24.md",
        "norway-ai-strategy.md",
        "nyc-ll144.md",
        "oecd-ai-principles.md",
        "owasp-llm.md",
        "peru-law-31814.md",
        "rwanda-ai-policy.md",
        "saudi-arabia-ai-strategy.md",
        "sf-ai-inventory-ordinance.md",
        "singapore-ai-verify.md",
        "singapore-model-ai-governance.md",
        "slovenia-ai-act.md",
        "soc2.md",
        "south-korea-ai-basic-act.md",
        "stride.md",
        "sweden-ai-strategy.md",
        "taiwan-ai-fundamental-act.md",
        "texas-traiga.md",
        "uk-ai-regulation-framework.md",
        "unesco-ai-ethics.md",
        "utah-ai-policy-act.md",
        "vermont-act101.md",
        "virginia-hb714.md",
        "owasp-agentic.md",
        "spain-ai-strategy.md",
        "finland-ai-strategy.md",
        "uae-ai-strategy.md",
        "switzerland-ai-strategy.md",
        "estonia-ai-strategy.md",
        "thailand-ai-strategy.md",
        "south-africa-ai-policy.md",
        "argentina-ai-plan.md",
        "hong-kong-ai-guidelines.md",
        "belgium-ai-strategy.md",
        "ophthalmic-ai.md",
    ],
)
def test_readme_counts_match_script_output(matrix_name: str):
    """Closes the drift bug from issue #30: README cells == counter output.

    Author edits a matrix → re-runs counter → updates README. If the chain
    is skipped (drift), this test fails and identifies the divergent cell.
    """
    parsed = _parse_readme_rows()
    slug = matrix_name.replace(".md", "")
    assert slug in parsed, f"No README row found for {slug}"

    data = _run_counter()
    matrix = next(
        m for m in data["matrices"] if Path(m["path"]).name == matrix_name
    )
    readme = parsed[slug]
    c = matrix["counts"]
    assert readme["rows"] == matrix["rows_counted"], (
        f"{matrix_name}: README Rows={readme['rows']} vs counted={matrix['rows_counted']}"
    )
    assert readme["✅"] == c["✅"], (
        f"{matrix_name}: README ✅={readme['✅']} vs counted={c['✅']}"
    )
    assert readme["🟡"] == c["🟡"], (
        f"{matrix_name}: README 🟡={readme['🟡']} vs counted={c['🟡']}"
    )
    assert readme["⚪"] == c["⚪"], (
        f"{matrix_name}: README ⚪={readme['⚪']} vs counted={c['⚪']}"
    )
    assert readme["unmarked"] == matrix["unmarked_rows"], (
        f"{matrix_name}: README Unmarked={readme['unmarked']} "
        f"vs counted={matrix['unmarked_rows']}"
    )


def test_readme_fleet_totals_match_script_output():
    """Fleet aggregate row in README must match summed counter output."""
    readme = (COVERAGE_DIR / "README.md").read_text(encoding="utf-8")
    fleet_re = re.compile(
        r"\|\s*\*\*FLEET[^|]*\*\*\s*\|[^|]+\|\s*\*\*(?P<rows>\d+)[^*]*\*\*\s*\|\s*"
        r"\*\*(?P<fulfilled>\d+)\*\*\s*\|\s*\*\*(?P<partial>\d+)\*\*\s*\|\s*"
        r"\*\*(?P<boundary>\d+)\*\*\s*\|\s*\*\*(?P<unmarked>\d+)\*\*",
    )
    m = fleet_re.search(readme)
    assert m, "Fleet aggregate row not found in README table"

    data = _run_counter()
    fleet = data["fleet_totals"]
    fleet_rows = data["fleet_rows"]
    fleet_unmarked = sum(mx.get("unmarked_rows", 0) for mx in data["matrices"])

    assert int(m.group("rows")) == fleet_rows, (
        f"README fleet Rows={m.group('rows')} vs counted={fleet_rows}"
    )
    assert int(m.group("fulfilled")) == fleet["✅"]
    assert int(m.group("partial")) == fleet["🟡"]
    assert int(m.group("boundary")) == fleet["⚪"]
    assert int(m.group("unmarked")) == fleet_unmarked, (
        f"README fleet Unmarked={m.group('unmarked')} vs counted={fleet_unmarked}"
    )


def test_readme_narrative_totals_match_script_output():
    """Narrative count sentence must not drift from generated fleet counts."""
    readme = (COVERAGE_DIR / "README.md").read_text(encoding="utf-8")
    narrative_re = re.compile(
        r"The \*\*(?P<fulfilled>\d+) ✅ Fulfilled\*\* rows.*?"
        r"The \*\*(?P<partial>\d+) 🟡 Partial\*\* rows.*?"
        r"The \*\*(?P<boundary>\d+) ⚪ Boundary\*\* rows",
    )
    match = narrative_re.search(readme)
    assert match, "README narrative count sentence not found"

    data = _run_counter()
    fleet = data["fleet_totals"]

    assert int(match.group("fulfilled")) == fleet["✅"]
    assert int(match.group("partial")) == fleet["🟡"]
    assert int(match.group("boundary")) == fleet["⚪"]
