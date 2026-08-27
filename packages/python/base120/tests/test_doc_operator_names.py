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

"""Verify that README.md and llms.txt operator names match the canonical registry.

This test prevents documentation drift from ``operators.json`` — the canonical
source the SDK loads at runtime.  It checks:

1. Every operator code+name pair in the registry appears in both files.
2. No phantom operator codes (codes that exist in docs but not the registry).
3. The total operator count is exactly 120.
"""

from __future__ import annotations

import re
from pathlib import Path

from base120.engine import Engine

ROOT = Path(__file__).resolve().parents[1]


def _load_canonical() -> dict[str, str]:
    """Return ``{code: name}`` for all 120 operators from the live Engine."""
    engine = Engine()
    return {op.code: op.name for op in engine.list()}


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# README.md
# ---------------------------------------------------------------------------


class TestReadmeOperatorNames:
    """Every operator in the registry must appear in README.md with its canonical name."""

    def test_all_operators_present_with_correct_names(self) -> None:
        canonical = _load_canonical()
        readme = _read("README.md")
        missing: list[str] = []
        wrong: list[tuple[str, str, str]] = []
        for code, name in sorted(canonical.items()):
            expected = f"{code} {name}"
            if expected not in readme:
                # Check whether the code appears with a different name
                m = re.search(
                    rf"\b{re.escape(code)}\s+(\S+(?:\s+\S+)*?)(?:\s*[|\n]|$)",
                    readme,
                )
                if m:
                    found = m.group(1).strip().rstrip(".")
                    if found.lower() != name.lower():
                        wrong.append((code, found, name))
                missing.append(code)
        assert not missing, f"README.md is missing {len(missing)} operators: {missing[:10]}..."
        assert not wrong, f"README.md has {len(wrong)} misnamed operators: {wrong[:5]}..."

    def test_no_phantom_operators(self) -> None:
        canonical = _load_canonical()
        readme = _read("README.md")
        # Find all operator-code-like tokens in the README
        found_codes = set(re.findall(r"\b([PICDRS][A-Z]\d{1,2})\b", readme))
        # Filter to codes that look like real operator codes (not just any letter+digit)
        phantom = {c for c in found_codes if c not in canonical and c[0] in "PICDRS"}
        # Exclude false positives like "RE18" in "RE18" references that are actually
        # part of other text — only flag codes with family prefix patterns
        phantom = {c for c in phantom if re.match(r"^(P|IN|CO|DE|RE|SY)\d+$", c)}
        assert not phantom, (
            f"README.md references {len(phantom)} operator codes not in registry: {sorted(phantom)}"
        )

    def test_operator_count_is_120(self) -> None:
        canonical = _load_canonical()
        assert len(canonical) == 120, f"Expected 120 operators, got {len(canonical)}"


# ---------------------------------------------------------------------------
# llms.txt
# ---------------------------------------------------------------------------


class TestLlmsTxtOperatorNames:
    """Every operator in the registry must appear in llms.txt with its canonical name."""

    def test_all_operators_present_with_correct_names(self) -> None:
        canonical = _load_canonical()
        llms = _read("llms.txt")
        missing: list[str] = []
        wrong: list[tuple[str, str, str]] = []
        for code, name in sorted(canonical.items()):
            expected = f"- {code} {name}"
            if expected not in llms:
                # Check whether the code appears with a different name
                m = re.search(rf"^- {re.escape(code)}\s+(.+)$", llms, re.MULTILINE)
                if m:
                    found = m.group(1).strip()
                    if found.lower() != name.lower():
                        wrong.append((code, found, name))
                missing.append(code)
        assert not missing, f"llms.txt is missing {len(missing)} operators: {missing[:10]}..."
        assert not wrong, f"llms.txt has {len(wrong)} misnamed operators: {wrong[:5]}..."

    def test_no_phantom_operators(self) -> None:
        canonical = _load_canonical()
        llms = _read("llms.txt")
        found_codes = set(re.findall(r"\b([PICDRS][A-Z]\d{1,2})\b", llms))
        phantom = {c for c in found_codes if c not in canonical}
        phantom = {c for c in phantom if re.match(r"^(P|IN|CO|DE|RE|SY)\d+$", c)}
        assert not phantom, (
            f"llms.txt references {len(phantom)} operator codes not in registry: {sorted(phantom)}"
        )

    def test_family_ranges_match_registry(self) -> None:
        """The header ranges (e.g. P1–P20) must match the actual registry range."""
        engine = Engine()
        {op.code: op.name for op in engine.list()}
        llms = _read("llms.txt")
        family_order = ["P", "IN", "CO", "DE", "RE", "SY"]
        for fam in family_order:
            fam_codes = engine.family_codes(fam)
            actual_max = fam_codes[-1].replace(fam, "")
            # Look for range patterns like "P1–P20" or "P1-P20" (en dash or hyphen)
            pattern = rf"{fam}1[\u2013\-]{fam}(\d{{1,2}})"
            m = re.search(pattern, llms)
            if m:
                found_max = m.group(1)
                assert found_max == actual_max, (
                    f"llms.txt header says {fam}1\u2013{fam}{found_max} "
                    f"but registry has {fam}1\u2013{fam}{actual_max}"
                )
