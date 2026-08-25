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

"""Tests for the coverage-matrix evidence validator.

Covers:
- `_parse_matrix_rows`: data-row extraction, legend/summary skip
- `_extract_refs`: file-ref filter (no tuple-type false positives)
- `_resolve_evidence`: alias map, package layout, missing-file behavior
- `_validate_matrix`: end-to-end pass/fail counts on tiny fixtures
"""
from __future__ import annotations

import json
import sys
from io import StringIO
from pathlib import Path

from hummbl_governance.compliance_mapper import (
    _MODULE_ALIASES,
    _STATE_BOUNDARY,
    _STATE_FULFILLED,
    _STATE_OUT_OF_SCOPE,
    _STATE_PARTIAL,
    _extract_refs,
    _parse_matrix_rows,
    _resolve_evidence,
    _validate_matrix,
)


# ---------- _parse_matrix_rows ----------


def test_parse_matrix_rows_extracts_state_and_cells():
    text = (
        "| Article | Requirement | HUMMBL coverage | Evidence |\n"
        "|---|---|---|---|\n"
        "| Art. 8 | Compliance | ✅ Done | `hummbl_governance/kill_switch.py` |\n"
        "| Art. 9 | Risk mgmt  | \U0001f7e1 Partial | partial-doc |\n"
        "| Art. 10 | Out | ⛔ N/A | n/a |\n"
    )
    rows = _parse_matrix_rows(text)
    assert len(rows) == 3
    assert rows[0]["state"] == _STATE_FULFILLED
    assert rows[0]["control_id"] == "Art. 8"
    assert "kill_switch.py" in rows[0]["evidence"]
    assert rows[1]["state"] == _STATE_PARTIAL
    assert rows[2]["state"] == _STATE_OUT_OF_SCOPE


def test_parse_matrix_rows_skips_legend_table():
    text = (
        "| Glyph | State | Meaning |\n"
        "|---|---|---|\n"
        "| ✅ | Fulfilled | HUMMBL primitive |\n"
        "| \U0001f7e1 | Partial | both halves named |\n"
        "\n"
        "| Article | Requirement | HUMMBL coverage | Evidence |\n"
        "|---|---|---|---|\n"
        "| Art. 8 | Compliance | ✅ Done | `hummbl_governance/kill_switch.py` |\n"
    )
    rows = _parse_matrix_rows(text)
    assert len(rows) == 1
    assert rows[0]["control_id"] == "Art. 8"


def test_parse_matrix_rows_skips_chapter_summary():
    text = (
        "| Chapter | Title | Article range | ✅ | \U0001f7e1 |\n"
        "|---|---|---|---|---|\n"
        "| III | High-risk | Art. 6–49 | 18 | 7 |\n"
        "\n"
        "| Article | Requirement | HUMMBL coverage | Evidence |\n"
        "|---|---|---|---|\n"
        "| Art. 8 | Compliance | ✅ Done | `hummbl_governance/kill_switch.py` |\n"
    )
    rows = _parse_matrix_rows(text)
    # The "III" row in the summary has glyphs in cells; verify it's skipped
    assert all(r["control_id"] != "III" for r in rows), "summary row leaked"
    assert any(r["control_id"] == "Art. 8" for r in rows)


def test_parse_matrix_rows_skips_state_count_summary_tables():
    text = (
        "| Section | Obligations | ✅ | \U0001f7e1 | ⚪ |\n"
        "|---|---|---:|---:|---:|\n"
        "| Access | Identity controls | 3 | 1 | 0 |\n"
        "\n"
        "| Function | Validated | ✅ | \U0001f7e1 |\n"
        "|---|---:|---:|---:|\n"
        "| GOVERN | 2 | 4 | 1 |\n"
        "\n"
        "| Article | Requirement | HUMMBL coverage | Evidence |\n"
        "|---|---|---|---|\n"
        "| Art. 8 | Compliance | ✅ Done | `hummbl_governance/kill_switch.py` |\n"
    )
    rows = _parse_matrix_rows(text)
    assert [r["control_id"] for r in rows] == ["Art. 8"]


def test_parse_matrix_rows_skips_summary_without_evidence_column():
    text = (
        "| TSC | Description | Coverage |\n"
        "|---|---|---|\n"
        "| CC6 | Access controls | ✅ Fulfilled |\n"
        "\n"
        "| Component | Coverage |\n"
        "|---|---|\n"
        "| Agent registry | ✅ Fulfilled |\n"
        "\n"
        "| Control | Requirement | Coverage | Evidence |\n"
        "|---|---|---|---|\n"
        "| C1 | Compliance | ✅ Done | `hummbl_governance/kill_switch.py` |\n"
    )
    rows = _parse_matrix_rows(text)
    assert [r["control_id"] for r in rows] == ["C1"]


def test_parse_matrix_rows_boundary_state():
    text = (
        "| Article | Requirement | HUMMBL coverage | Evidence |\n"
        "|---|---|---|---|\n"
        "| Art. 22 | Authorized rep | ⚪ Boundary: corporate-legal | n/a |\n"
    )
    rows = _parse_matrix_rows(text)
    assert len(rows) == 1
    assert rows[0]["state"] == _STATE_BOUNDARY


# ---------- _extract_refs ----------


def test_extract_refs_picks_file_paths_skips_tuple_types():
    cell = (
        "Governance bus tuples include `INTENT` (stated objectives), `DCT` "
        "(delegation chain). See `hummbl_governance/coordination_bus.py` and "
        "`services/kill_switch_core.py`."
    )
    refs = _extract_refs(cell)
    # tuple-type identifiers without "/" or extension should NOT be picked up
    assert "INTENT" not in refs
    assert "DCT" not in refs
    assert "hummbl_governance/coordination_bus.py" in refs
    assert "services/kill_switch_core.py" in refs


def test_extract_refs_keeps_extension_only_tokens():
    cell = "See `pyproject.toml` and `Makefile.md`."
    refs = _extract_refs(cell)
    # `pyproject.toml` has .toml ext, qualifies; `Makefile.md` has .md ext
    assert "pyproject.toml" in refs
    assert "Makefile.md" in refs


def test_extract_refs_drops_urls_and_oversize():
    cell = "Doc at `http://example.com/spec` and `" + "x" * 250 + "`"
    refs = _extract_refs(cell)
    assert refs == []


def test_extract_refs_returns_empty_on_no_backticks():
    assert _extract_refs("plain prose with no code") == []


# ---------- _resolve_evidence ----------


def test_resolve_evidence_alias_to_existing_package_file():
    root = Path(__file__).resolve().parent.parent  # repo root
    res = _resolve_evidence("services/kill_switch_core.py", root)
    assert res["status"] == "pass"
    # alias resolves to hummbl_governance/kill_switch.py which exists
    assert "kill_switch.py" in res["path"]
    assert "alias" in res["detail"].lower()


def test_resolve_evidence_external_marker():
    root = Path(__file__).resolve().parent.parent
    res = _resolve_evidence("_state/coordination/messages.tsv", root)
    assert res["status"] == "external"
    assert res["path"].startswith("EXTERNAL:")


def test_resolve_evidence_tier2_marker():
    root = Path(__file__).resolve().parent.parent
    res = _resolve_evidence("services/c2pa_mcp", root)
    assert res["status"] == "tier2"
    assert "Tier-2" in res["detail"]


def test_resolve_evidence_missing_file():
    root = Path(__file__).resolve().parent.parent
    res = _resolve_evidence("services/nonexistent_phantom.py", root)
    assert res["status"] == "fail"
    assert "not found" in res["detail"]


def test_resolve_evidence_direct_existing_path():
    root = Path(__file__).resolve().parent.parent
    res = _resolve_evidence("hummbl_governance/kill_switch.py", root)
    assert res["status"] == "pass"
    assert res["path"] == "hummbl_governance/kill_switch.py"
    assert not Path(res["path"]).is_absolute()


# ---------- _validate_matrix end-to-end ----------


def test_validate_matrix_returns_zero_on_clean_matrix(tmp_path):
    matrix = tmp_path / "tiny.md"
    matrix.write_text(
        "| Control | Requirement | Coverage | Evidence |\n"
        "|---|---|---|---|\n"
        "| C1 | Compliance | ✅ Done | `hummbl_governance/kill_switch.py` |\n"
        "| C2 | Partial | \U0001f7e1 partial | doc |\n"
        "| C3 | Boundary | ⚪ boundary | n/a |\n",
        encoding="utf-8",
    )
    root = Path(__file__).resolve().parent.parent
    buf = StringIO()
    old_stdout = sys.stdout
    sys.stdout = buf
    try:
        ret = _validate_matrix(str(matrix), repo_root=str(root), json_output=True)
    finally:
        sys.stdout = old_stdout
    assert ret == 0
    data = json.loads(buf.getvalue())
    assert data["fulfilled_validation"]["rows_passed"] == 1
    assert data["fulfilled_validation"]["rows_failed"] == 0
    assert data["totals"]["fulfilled"] == 1
    assert data["totals"]["partial"] == 1
    assert data["totals"]["boundary"] == 1


def test_validate_matrix_json_uses_posix_repo_relative_matrix_path():
    root = Path(__file__).resolve().parent.parent
    matrix = root / "docs" / "coverage" / "eu-ai-act.md"
    buf = StringIO()
    old_stdout = sys.stdout
    sys.stdout = buf
    try:
        _validate_matrix(str(matrix), repo_root=str(root), json_output=True)
    finally:
        sys.stdout = old_stdout
    data = json.loads(buf.getvalue())
    assert data["matrix"] == "docs/coverage/eu-ai-act.md"


def test_validate_matrix_returns_one_on_unresolved_refs(tmp_path):
    matrix = tmp_path / "tiny.md"
    matrix.write_text(
        "| Control | Requirement | Coverage | Evidence |\n"
        "|---|---|---|---|\n"
        "| C1 | Compliance | ✅ Done | `services/phantom_nonexistent.py` |\n",
        encoding="utf-8",
    )
    root = Path(__file__).resolve().parent.parent
    buf = StringIO()
    old_stdout = sys.stdout
    sys.stdout = buf
    try:
        ret = _validate_matrix(str(matrix), repo_root=str(root), json_output=True)
    finally:
        sys.stdout = old_stdout
    assert ret == 1
    data = json.loads(buf.getvalue())
    assert data["fulfilled_validation"]["rows_failed"] == 1
    assert data["fulfilled_validation"]["rows_passed"] == 0


def test_validate_matrix_flags_rows_without_refs(tmp_path):
    matrix = tmp_path / "tiny.md"
    matrix.write_text(
        "| Control | Requirement | Coverage | Evidence |\n"
        "|---|---|---|---|\n"
        "| C1 | Compliance | ✅ Done | narrative text, no backticks |\n",
        encoding="utf-8",
    )
    root = Path(__file__).resolve().parent.parent
    buf = StringIO()
    old_stdout = sys.stdout
    sys.stdout = buf
    try:
        ret = _validate_matrix(str(matrix), repo_root=str(root), json_output=True)
    finally:
        sys.stdout = old_stdout
    assert ret == 1
    data = json.loads(buf.getvalue())
    assert data["fulfilled_validation"]["rows_without_refs"] == 1


def test_validate_matrix_returns_two_on_missing_file():
    root = Path(__file__).resolve().parent.parent
    buf = StringIO()
    old_stderr = sys.stderr
    sys.stderr = buf
    try:
        ret = _validate_matrix("/path/does/not/exist.md", repo_root=str(root))
    finally:
        sys.stderr = old_stderr
    assert ret == 2


# ---------- _MODULE_ALIASES sanity ----------


def test_module_aliases_canonical_targets_resolve_in_package():
    """Every non-marker alias should point at a file that exists in the package."""
    root = Path(__file__).resolve().parent.parent
    for legacy, canonical in _MODULE_ALIASES.items():
        if canonical.startswith(("TIER2_ADMITTED:", "EXTERNAL:")):
            continue
        target = root / canonical
        assert target.exists(), (
            f"alias '{legacy}' -> '{canonical}' but target file does not exist "
            f"in {root}; update _MODULE_ALIASES in compliance_mapper.py"
        )
