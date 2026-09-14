"""MTSMU rigor summary for evaluation output.

Tracks verify-methods and uncertainty levels across findings, then renders
a summary footer showing the aggregate rigor profile. Used by the CLI when
``--mtsmu`` is passed (composes with ``--base120`` and ``--krineia``).
"""

from __future__ import annotations

import sys
from collections import Counter
from typing import Any

VERIFY_METHODS = frozenset(
    {
        "verify-after",
        "cross-check",
        "empirical",
        "unverified",
    }
)

UNCERTAINTY_LEVELS = frozenset({"low", "medium", "high", "unknown"})


def add_mtsmu_arg(parser: Any) -> None:
    """Add the --mtsmu argument to an argparse parser."""
    parser.add_argument(
        "--mtsmu",
        action="store_true",
        help="Add MTSMU rigor summary footer (verify-method + uncertainty tracking)",
    )


class MtsmuSummary:
    """MTSMU rigor summary tracker and renderer."""

    def __init__(self) -> None:
        self._verify_methods: Counter[str] = Counter()
        self._uncertainties: Counter[str] = Counter()
        self._finding_count: int = 0

    def track(self, verify_method: str = "unverified", uncertainty: str = "unknown") -> None:
        """Track a finding's verify-method and uncertainty level."""
        # Strip basis suffix: "medium -- no baseline" -> "medium"
        uncertainty_level = uncertainty.split(" -- ")[0].split(" \u2014 ")[0].strip().lower()
        if uncertainty_level not in UNCERTAINTY_LEVELS:
            uncertainty_level = "unknown"
        vm = verify_method if verify_method in VERIFY_METHODS else "unverified"
        self._verify_methods[vm] += 1
        self._uncertainties[uncertainty_level] += 1
        self._finding_count += 1

    def _print(self, text: str = "") -> None:
        print(text, file=sys.stdout)

    def render(self) -> None:
        """Print the MTSMU rigor summary footer."""
        self._print()
        self._print("---- MTSMU Rigor Summary ----")
        self._print(f"Findings tracked: {self._finding_count}")

        if self._finding_count == 0:
            self._print("No findings tracked -- no rigor data to summarize.")
            self._print("-----------------------------")
            return

        self._print()
        self._print("Verify-methods:")
        for vm in sorted(VERIFY_METHODS):
            count = self._verify_methods.get(vm, 0)
            if count > 0:
                pct = count * 100 // self._finding_count
                self._print(f"  {vm:16s} {count:3d}  ({pct}%)")

        self._print()
        self._print("Uncertainty levels:")
        for level in sorted(UNCERTAINTY_LEVELS):
            count = self._uncertainties.get(level, 0)
            if count > 0:
                pct = count * 100 // self._finding_count
                self._print(f"  {level:16s} {count:3d}  ({pct}%)")

        verifiable = (
            self._verify_methods.get("verify-after", 0)
            + self._verify_methods.get("cross-check", 0)
            + self._verify_methods.get("empirical", 0)
        )
        pct_verifiable = verifiable * 100 // self._finding_count if self._finding_count else 0

        self._print()
        if pct_verifiable >= 75:
            assessment = "HIGH RIGOR"
        elif pct_verifiable >= 50:
            assessment = "MODERATE RIGOR"
        elif pct_verifiable >= 25:
            assessment = "LOW RIGOR"
        else:
            assessment = "INSUFFICIENT RIGOR"
        self._print(
            f"Verifiable: {verifiable}/{self._finding_count} ({pct_verifiable}%) -- {assessment}"
        )
        self._print("-----------------------------")

    @property
    def finding_count(self) -> int:
        return self._finding_count

    @property
    def verify_methods(self) -> Counter[str]:
        return self._verify_methods.copy()

    @property
    def uncertainties(self) -> Counter[str]:
        return self._uncertainties.copy()

    def to_dict(self) -> dict[str, Any]:
        return {
            "finding_count": self._finding_count,
            "verify_methods": dict(self._verify_methods),
            "uncertainties": dict(self._uncertainties),
        }
