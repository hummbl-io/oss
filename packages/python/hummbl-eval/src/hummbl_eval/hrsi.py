"""HRSI check-in format for evaluation output.

Provides a structured check-in format capturing the three belonging
dimensions (safety, mattering, connection), cognitive state, somatic data,
HULE, and relational notes. Used by the CLI when ``--hrsi`` is passed.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from typing import Any

COGSTATES = frozenset(
    {
        "AVAILABLE",
        "DEPLETED",
        "HYPERFOCUS",
        "RECOVERY",
        "RSD_RISK",
        "SHUTDOWN",
        "TRANSITION",
    }
)

SCALE_MIN = 1
SCALE_MAX = 5


def add_hrsi_arg(parser: Any) -> None:
    """Add the --hrsi argument to an argparse parser."""
    parser.add_argument(
        "--hrsi",
        action="store_true",
        help="Format output as an HRSI check-in (safety/mattering/connection + cogstate + HULE)",
    )


class HrsiCheckin:
    """HRSI check-in formatter."""

    def __init__(self) -> None:
        self._cogstate: str = "AVAILABLE"
        self._safety: int = 3
        self._mattering: int = 3
        self._connection: int = 3
        self._energy: int | None = None
        self._sleep_hours: float | None = None
        self._hule: str = ""
        self._relational_note: str = ""
        self._header_printed = False

    def _now(self) -> str:
        return datetime.now(UTC).strftime("%Y-%m-%d")

    def _print(self, text: str = "") -> None:
        print(text, file=sys.stdout)

    def _validate_scale(self, value: int, name: str) -> int:
        if not isinstance(value, int) or value < SCALE_MIN or value > SCALE_MAX:
            raise ValueError(
                f"{name} must be an integer between {SCALE_MIN} and {SCALE_MAX}, got {value}"
            )
        return value

    def header(self) -> None:
        """Print the HRSI check-in header."""
        if self._header_printed:
            return
        self._header_printed = True
        self._print(f"HRSI Check-In | {self._now()}")
        self._print("=" * 30)
        self._print()

    def cogstate(self, state: str) -> None:
        """Set the cognitive state."""
        state_upper = state.upper()
        if state_upper not in COGSTATES:
            raise ValueError(f"cogstate must be one of: {', '.join(sorted(COGSTATES))}")
        self._cogstate = state_upper

    def baseline(self, safety: int, mattering: int, connection: int) -> None:
        """Set the three belonging baseline dimensions (1-5 each)."""
        self._safety = self._validate_scale(safety, "safety")
        self._mattering = self._validate_scale(mattering, "mattering")
        self._connection = self._validate_scale(connection, "connection")

    def somatic(self, energy: int | None = None, sleep_hours: float | None = None) -> None:
        """Set somatic data."""
        if energy is not None:
            self._energy = self._validate_scale(energy, "energy")
        if sleep_hours is not None:
            if not isinstance(sleep_hours, (int, float)) or sleep_hours < 0 or sleep_hours > 24:
                raise ValueError(f"sleep_hours must be between 0 and 24, got {sleep_hours}")
            self._sleep_hours = float(sleep_hours)

    def hule(self, text: str) -> None:
        """Set the HULE moment."""
        self._hule = text

    def relational_note(self, text: str) -> None:
        """Set the relational connection note."""
        self._relational_note = text

    def render(
        self,
        days_logged: int | None = None,
        averages: dict[str, float] | None = None,
        trend: str = "->",
    ) -> None:
        """Print the full HRSI check-in body and footer."""
        self._print(f"Cogstate:    {self._cogstate}")
        self._print(f"Safety:      {self._safety}/5")
        self._print(f"Mattering:   {self._mattering}/5")
        self._print(f"Connection:  {self._connection}/5")
        if self._energy is not None:
            self._print(f"Energy:      {self._energy}/5  (somatic)")
        if self._sleep_hours is not None:
            self._print(f"Sleep:       {self._sleep_hours}h")
        if self._hule:
            self._print(f'HULE:        "{self._hule}"')
        if self._relational_note:
            self._print(f'Relational:  "{self._relational_note}"')

        self._print()
        if days_logged is not None:
            self._print(f"Days logged:  {days_logged} total")
        if averages:
            avg_str = "  ".join(f"{k}:{v:.1f}" for k, v in sorted(averages.items()))
            self._print(f"7-day avg:    {avg_str}")
        if trend:
            self._print(f"Trend:        {trend}")

        if self._cogstate in ("RECOVERY", "TRANSITION"):
            self._print()
            self._print("Next: [dream] (RECOVERY/TRANSITION cogstate)")
        self._print()
        self._print("=" * 30)

    def to_dict(self) -> dict[str, Any]:
        """Return check-in data as a dict."""
        return {
            "date": self._now(),
            "cogstate": self._cogstate,
            "safety": self._safety,
            "mattering": self._mattering,
            "connection": self._connection,
            "energy": self._energy,
            "sleep_hours": self._sleep_hours,
            "hule": self._hule,
            "relational_note": self._relational_note,
        }
