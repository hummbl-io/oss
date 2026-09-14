"""Krineia receipt rendering for evaluation output.

Provides the MTSMU receipt footer with trust-root separation, falsifiability
anchors, verify-method tags, and epistemic stance declarations. Used by the
CLI when ``--krineia`` is passed (composes with ``--base120``).

This is a RENDERING layer, not a cryptographic receipt writer. Full Krineia
v2.0.0 cryptographic receipts (with HMAC-SHA256 signatures, hash chains) are
written by the krineia-watcher daemon — a separate observer process that
satisfies Krineia Invariant 5 (trust-root separation by process boundary).
"""

from __future__ import annotations

import os
import sys
from typing import Any

VERIFY_METHODS = frozenset(
    {
        "verify-after",
        "cross-check",
        "empirical",
        "unverified",
    }
)

STANCES = frozenset(
    {
        "descriptive",
        "prescriptive",
        "strategic",
        "negotiative",
        "hybrid",
    }
)

UNCERTAINTY_LEVELS = frozenset({"low", "medium", "high", "unknown"})


class KrineiaSeparationError(ValueError):
    """Trust-root separation violated: reasoned_by == observed_agent."""


class KrineiaReceiptError(ValueError):
    """A Krineia receipt field is invalid."""


def add_krineia_arg(parser: Any) -> None:
    """Add the --krineia argument to an argparse parser."""
    parser.add_argument(
        "--krineia",
        action="store_true",
        help="Add Krineia receipt footer (trust-root separation + falsifiability)",
    )


class KrineiaReceipt:
    """Krineia MTSMU receipt footer renderer.

    Holds receipt metadata and renders the standardized footer that
    declares trust-root separation, falsifiability anchors, and epistemic
    stance. Composes with Base120Formatter — call ``render()`` after
    ``fmt.footer()``.
    """

    def __init__(
        self,
        reasoned_by: str,
        observed_agent: str,
        falsifiability_anchor: str,
        stance: str = "descriptive",
        source: str = "[UNVERIFIED — registry not looked up]",
        *,
        verify_method_default: str = "unverified",
        uncertainty_default: str = "unknown",
        session_id: str | None = None,
    ) -> None:
        if not reasoned_by or not observed_agent or not falsifiability_anchor:
            raise KrineiaReceiptError(
                "reasoned_by, observed_agent, and falsifiability_anchor are required"
            )
        if stance not in STANCES:
            raise KrineiaReceiptError(f"stance must be one of: {', '.join(sorted(STANCES))}")
        if verify_method_default not in VERIFY_METHODS:
            raise KrineiaReceiptError(
                f"verify_method_default must be one of: {', '.join(sorted(VERIFY_METHODS))}"
            )
        self.reasoned_by = reasoned_by
        self.observed_agent = observed_agent
        self.falsifiability_anchor = falsifiability_anchor
        self.stance = stance
        self.source = source
        self.verify_method_default = verify_method_default
        self.uncertainty_default = uncertainty_default
        self.session_id = session_id or os.environ.get("DEVIN_SESSION_ID", "")

    def check_separation(self) -> None:
        """Verify trust-root separation (Krineia §3.2).

        Raises:
            KrineiaSeparationError: If reasoned_by == observed_agent.
        """
        base_reasoned = self.reasoned_by.split()[0].split("(")[0].strip().lower()
        base_observed = self.observed_agent.split()[0].split("(")[0].strip().lower()
        if base_reasoned == base_observed:
            raise KrineiaSeparationError(
                f"Trust-root separation violated (Krineia §3.2): "
                f"reasoned_by ({self.reasoned_by}) == observed_agent ({self.observed_agent}). "
                f"The agent who reasons must not be the agent whose state is observed. "
                f"Refusing to emit receipt — downgrade to operator-local memory only."
            )

    def _print(self, text: str = "") -> None:
        print(text, file=sys.stdout)

    def render(self) -> None:
        """Print the Krineia receipt footer.

        Call this AFTER ``Base120Formatter.footer()``.
        Raises KrineiaSeparationError if trust-root separation is violated.
        """
        self.check_separation()

        self._print()
        self._print("---- Krineia Receipt ----")
        self._print(f"Reasoned-by: {self.reasoned_by}")
        if self.session_id:
            self._print(f"Session: {self.session_id}")
        self._print(f"Observed-agent: {self.observed_agent}")
        self._print(f"Falsifiability anchor: {self.falsifiability_anchor}")
        self._print(f"Stance: {self.stance}")
        self._print(f"Verify-method default: {self.verify_method_default}")
        self._print(f"Uncertainty default: {self.uncertainty_default}")
        self._print(f"Source: {self.source}")
        self._print("-------------------------")
        self._print()
        self._print("NOTE: This is an MTSMU receipt footer, not a cryptographic receipt.")
        self._print("Cryptographic receipts are written by krineia-watcher (separate process).")

    def to_dict(self) -> dict[str, str]:
        """Return receipt metadata as a dict (for Record envelope wrapping)."""
        return {
            "reasoned_by": self.reasoned_by,
            "observed_agent": self.observed_agent,
            "falsifiability_anchor": self.falsifiability_anchor,
            "stance": self.stance,
            "source": self.source,
            "verify_method_default": self.verify_method_default,
            "uncertainty_default": self.uncertainty_default,
            "session_id": self.session_id,
        }
