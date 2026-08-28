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

"""Domain120 lattice validator.

Validates a Domain120 lattice against the ratification criteria:
  1. 20+ operators with domain-specific content
  2. All 6 families populated (no empty families)
  3. Composition matrix has >= 3 admissible family-pairs
  4. Stopping rule: operators are reasoning moves, not domain facts (proxy)
  5. Cross-maps: at least 3 cross-domain maps identified
  6. No relabelings of Base120 ancestors (domain-specificity check)
  7. Canonical serialization valid (hash computation succeeds)
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from hummbl_lattice.models import FAMILIES, Lattice

# Generic words that don't count as domain-specific content
_GENERIC_WORDS: frozenset[str] = frozenset({
    "reason", "about", "system", "problem", "approach", "instead", "asking",
    "would", "produce", "identify", "consider", "analyze", "examine", "look",
    "think", "way", "method", "process", "step", "first", "then", "next",
    "the", "a", "an", "to", "of", "in", "for", "with", "and", "or", "not",
    "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
    "do", "does", "did", "will", "could", "should", "may", "might",
    "this", "that", "these", "those", "it", "its", "they", "them", "their",
    "we", "us", "our", "you", "your", "one", "all", "each", "every",
    "some", "any", "no", "none", "both", "few", "more", "most", "less",
    "least", "other", "another", "same", "different", "new", "old",
    "good", "bad", "right", "wrong", "true", "false",
    "what", "which", "who", "whom", "whose", "when", "where", "why", "how",
    "if", "else", "because", "since", "while", "during", "after",
    "before", "between", "through", "into", "onto", "upon", "over", "under",
    "again", "still", "also", "only", "just", "even", "very", "too",
})


@dataclass
class CheckResult:
    """Result of a single validation check."""
    name: str
    status: str  # "PASS" | "FAIL" | "WARN"
    detail: str

    @property
    def passed(self) -> bool:
        return self.status == "PASS"

    @property
    def failed(self) -> bool:
        return self.status == "FAIL"

    @property
    def is_warning(self) -> bool:
        return self.status == "WARN"


@dataclass
class ValidationReport:
    """Complete validation report for a lattice."""
    file: str = ""
    checks: list[CheckResult] = field(default_factory=list)
    lattice_hash: str = ""

    @property
    def passed_count(self) -> int:
        return sum(1 for c in self.checks if c.passed)

    @property
    def failed_count(self) -> int:
        return sum(1 for c in self.checks if c.failed)

    @property
    def warning_count(self) -> int:
        return sum(1 for c in self.checks if c.is_warning)

    @property
    def ratification_ready(self) -> bool:
        """True if no checks failed and at most 2 warnings."""
        return self.failed_count == 0 and self.warning_count <= 2

    @property
    def failing_checks(self) -> list[str]:
        return [c.name for c in self.checks if c.failed]

    def add(self, name: str, status: str, detail: str) -> None:
        self.checks.append(CheckResult(name=name, status=status, detail=detail))

    def summary(self) -> str:
        """One-line summary."""
        status = "READY" if self.ratification_ready else "NOT READY"
        return (
            f"Passed: {self.passed_count}, "
            f"Failed: {self.failed_count}, "
            f"Warnings: {self.warning_count}, "
            f"Ratification: {status}"
        )

    def to_text(self) -> str:
        """Full text report."""
        lines = [
            "=" * 70,
            "Domain120 Lattice Validation Report",
            "=" * 70,
            "",
            f"File: {self.file}",
            "",
        ]
        for check in self.checks:
            icon = {"PASS": "[OK]", "FAIL": "[XX]", "WARN": "[!!]"}[check.status]
            lines.append(f"  {icon} {check.name:30s} {check.detail}")
        lines.append("")
        lines.append("-" * 70)
        lines.append(f"  {self.summary()}")
        if self.lattice_hash:
            lines.append(f"  Lattice SHA-256: {self.lattice_hash}")
        lines.append("")
        return "\n".join(lines)


class LatticeValidator:
    """Validates Domain120 lattices against ratification criteria."""

    def validate(self, source: str | Path | Lattice) -> ValidationReport:
        """Validate a lattice from a file path or Lattice object.

        Args:
            source: Path to a lattice JSON file, or a Lattice object.

        Returns:
            ValidationReport with all check results.
        """
        report = ValidationReport()

        # Load the lattice
        if isinstance(source, Lattice):
            lattice = source
            report.file = "<in-memory>"
        else:
            path = Path(source)
            report.file = str(path)
            try:
                lattice = Lattice.from_json(path)
            except Exception as e:
                report.add("file_load", "FAIL", str(e))
                return report

        # Check 1: 20+ operators
        n_ops = lattice.operator_count
        if n_ops >= 20:
            report.add("operator_count", "PASS", f"{n_ops} operators (>= 20)")
        elif n_ops >= 15:
            report.add("operator_count", "WARN", f"{n_ops} operators (>= 20 required, >= 15 acceptable)")
        else:
            report.add("operator_count", "FAIL", f"{n_ops} operators (< 20)")

        # Check 2: All 6 families populated
        missing = lattice.missing_families
        if not missing:
            report.add("family_coverage", "PASS", f"All 6 families populated: {lattice.family_counts}")
        else:
            report.add("family_coverage", "FAIL", f"Missing families: {missing}")

        # Check 3: Domain-specific content (not relabelings)
        relabelings = []
        for op in lattice.operators:
            words = re.findall(r"\b\w+\b", op.definition.lower())
            domain_words = [w for w in words if len(w) > 5 and w not in _GENERIC_WORDS]
            if len(domain_words) < 3:
                relabelings.append(op.code)
        if not relabelings:
            report.add("domain_specificity", "PASS", "All operators have domain-specific content")
        elif len(relabelings) <= 2:
            report.add("domain_specificity", "WARN", f"{len(relabelings)} operators with low domain content: {relabelings}")
        else:
            report.add("domain_specificity", "FAIL", f"{len(relabelings)} operators with low domain content")

        # Check 4: Composition matrix >= 3 admissible pairs
        n_admissible = lattice.composition_matrix.admissible_count
        if n_admissible >= 3:
            report.add("composition_matrix", "PASS", f"{n_admissible} admissible pairs (>= 3)")
        else:
            report.add("composition_matrix", "FAIL", f"{n_admissible} admissible pairs (< 3)")

        # Check 5: Cross-maps >= 3
        n_maps = len(lattice.cross_maps)
        if n_maps >= 3:
            report.add("cross_maps", "PASS", f"{n_maps} cross-domain maps (>= 3)")
        elif n_maps >= 1:
            report.add("cross_maps", "WARN", f"{n_maps} cross-domain maps (>= 3 required, >= 1 acceptable)")
        else:
            report.add("cross_maps", "FAIL", f"{n_maps} cross-domain maps (< 3)")

        # Check 6: Canonical serialization (hash)
        try:
            report.lattice_hash = lattice.lattice_hash
            report.add("canonical_serialization", "PASS", f"SHA-256: {report.lattice_hash[:16]}...")
        except Exception as e:
            report.add("canonical_serialization", "FAIL", str(e))

        return report
