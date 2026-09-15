"""After Action Report format for evaluation output (canonical 7-section spec).

Implements the canonical AAR format with 7 required sections, Base120 code
mapping, evidence receipts, and bus integration footer. Used by the CLI
when ``--aar`` is passed.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from typing import Any


def add_aar_arg(parser: Any) -> None:
    """Add the --aar argument to an argparse parser."""
    parser.add_argument(
        "--aar",
        action="store_true",
        help="Format output as an After Action Report (7-section canonical format)",
    )


class AarFormatter:
    """After Action Report formatter (canonical 7-section spec)."""

    SECTION_CODES = {
        "mission": "P6",
        "chronology": "RE17",
        "outcome": "IN17",
        "root_causes": "DE1",
        "sustains": "RE16",
        "improves": "IN20",
        "recommendations": "DE7",
    }

    def __init__(self, skill_name: str, author: str = "", classification: str = "") -> None:
        self.skill_name = skill_name
        self.author = author
        self.classification = classification

        self._objective: str = ""
        self._success_criteria: str = ""
        self._constraints: str = ""

        self._chronology: list[tuple[str, str, str]] = []

        self._planned: str = ""
        self._actual: str = ""
        self._delta: str = ""

        self._root_causes: list[tuple[str, list[str]]] = []

        self._sustains: list[tuple[str, str]] = []
        self._improves: list[tuple[str, str]] = []
        self._recommendations: list[tuple[str, str, str]] = []

        self._evidence: list[str] = []
        self._bus_posted: bool = False
        self._bus_note: str = ""
        self._applied_codes: set[str] = set()

    def _now(self) -> str:
        return datetime.now(UTC).strftime("%Y%m%d-%H%MZ")

    def _print(self, text: str = "") -> None:
        print(text, file=sys.stdout)

    def _track_code(self, section: str) -> None:
        code = self.SECTION_CODES.get(section, "")
        if code:
            self._applied_codes.add(code)

    def set_mission(
        self, objective: str, success_criteria: str = "", constraints: str = ""
    ) -> None:
        """Set the mission and intent for Section 1."""
        self._objective = objective
        self._success_criteria = success_criteria
        self._constraints = constraints
        self._track_code("mission")

    def chronology_entry(self, timestamp: str, action: str, result: str = "") -> None:
        """Add a chronology entry for Section 2."""
        self._chronology.append((timestamp, action, result))
        self._track_code("chronology")

    def set_outcome(self, planned: str, actual: str, delta: str = "") -> None:
        """Set the outcome vs plan for Section 3."""
        self._planned = planned
        self._actual = actual
        self._delta = delta
        self._track_code("outcome")

    def root_cause(self, deviation: str, why_chain: list[str]) -> None:
        """Add a root cause analysis entry for Section 4."""
        self._root_causes.append((deviation, why_chain))
        self._track_code("root_causes")

    def sustain(self, what: str, evidence: str = "") -> None:
        """Add a sustain entry for Section 5."""
        self._sustains.append((what, evidence))
        self._track_code("sustains")

    def improve(self, what: str, evidence: str = "") -> None:
        """Add an improve entry for Section 6."""
        self._improves.append((what, evidence))
        self._track_code("improves")

    def recommendation(self, priority: str, action: str, addresses: str = "") -> None:
        """Add a recommendation for Section 7."""
        priority_upper = priority.upper()
        if priority_upper not in ("HIGH", "MED", "LOW"):
            priority_upper = "LOW"
        self._recommendations.append((priority_upper, action, addresses))
        self._track_code("recommendations")

    def set_evidence(self, artifacts: list[str]) -> None:
        """Set the evidence artifacts for the footer."""
        self._evidence = artifacts

    def set_bus(self, posted: bool, note: str = "") -> None:
        """Set the bus posting status for the footer."""
        self._bus_posted = posted
        self._bus_note = note

    def render(self) -> None:
        """Print the full AAR with all 7 sections and footer."""
        now = self._now()
        header_line = f"AAR: {self.skill_name}"
        if self.classification:
            header_line += f" | {self.classification}"
        header_line += f" | {now}"
        if self.author:
            header_line += f" | {self.author}"

        self._print(header_line)
        self._print("=" * 70)
        self._print()

        # Section 1: Mission & Intent
        self._print("## 1. Mission & Intent (P6: Point-of-View Anchoring)")
        self._print(f"- **Objective**: {self._objective}")
        if self._success_criteria:
            self._print(f"- **Success criteria**: {self._success_criteria}")
        if self._constraints:
            self._print(f"- **Constraints**: {self._constraints}")
        self._print()

        # Section 2: Chronology
        self._print("## 2. Chronology (RE17: Versioning & Diff)")
        if self._chronology:
            self._print("| Time/Commit | Action | Result |")
            self._print("|-------------|--------|--------|")
            for ts, action, result in self._chronology:
                self._print(f"| {ts} | {action} | {result} |")
        else:
            self._print("  (no chronology entries)")
        self._print()

        # Section 3: Outcome vs Plan
        self._print("## 3. Outcome vs Plan (IN17: Counterfactual Negation)")
        self._print(f"- **Planned**: {self._planned}")
        self._print(f"- **Actual**: {self._actual}")
        if self._delta:
            self._print(f"- **Delta**: {self._delta}")
        self._print()

        # Section 4: Root Causes
        self._print("## 4. Root Causes (DE1: Root Cause Analysis)")
        if self._root_causes:
            for deviation, why_chain in self._root_causes:
                self._print(f"- Deviation: {deviation}")
                for i, why in enumerate(why_chain, 1):
                    self._print(f"  Why {i}: {why}")
        else:
            self._print("  (no deviations -- no root causes to analyze)")
        self._print()

        # Section 5: Sustains
        self._print("## 5. Sustains (RE16: Retrospective -> Prospective Loop)")
        if self._sustains:
            for what, evidence in self._sustains:
                line = f"- {what}"
                if evidence:
                    line += f" -- evidence: {evidence}"
                self._print(line)
        else:
            self._print("  (no sustains recorded)")
        self._print()

        # Section 6: Improves
        self._print("## 6. Improves (IN20: Antigoals & Anti-Patterns Catalog)")
        if self._improves:
            for what, evidence in self._improves:
                line = f"- {what}"
                if evidence:
                    line += f" -- evidence: {evidence}"
                self._print(line)
        else:
            self._print("  (no improves recorded)")
        self._print()

        # Section 7: Recommendations
        self._print("## 7. Recommendations (DE7: Pareto Decomposition)")
        if self._recommendations:
            for i, (priority, action, addresses) in enumerate(self._recommendations, 1):
                line = f"{i}. **[{priority}]** {action}"
                if addresses:
                    line += f" -- addresses: {addresses}"
                self._print(line)
        else:
            self._print("  (no recommendations)")
        self._print()

        # Footer
        self._print("---")
        codes = sorted(self._applied_codes)
        self._print(f"Base120 Applied: {', '.join(codes) if codes else '[none]'}")
        evidence_str = ", ".join(self._evidence) if self._evidence else "[none]"
        self._print(f"Evidence: {evidence_str}")
        if self._bus_posted:
            bus_str = "Y"
            if self._bus_note:
                bus_str += f" ({self._bus_note})"
        else:
            bus_str = "N"
        self._print(f"Bus: {bus_str}")

    def to_dict(self) -> dict[str, Any]:
        """Return AAR data as a dict."""
        return {
            "skill_name": self.skill_name,
            "author": self.author,
            "classification": self.classification,
            "timestamp": self._now(),
            "mission": {
                "objective": self._objective,
                "success_criteria": self._success_criteria,
                "constraints": self._constraints,
            },
            "chronology": [
                {"timestamp": ts, "action": act, "result": res} for ts, act, res in self._chronology
            ],
            "outcome": {
                "planned": self._planned,
                "actual": self._actual,
                "delta": self._delta,
            },
            "root_causes": [
                {"deviation": dev, "why_chain": chain} for dev, chain in self._root_causes
            ],
            "sustains": [{"what": w, "evidence": e} for w, e in self._sustains],
            "improves": [{"what": w, "evidence": e} for w, e in self._improves],
            "recommendations": [
                {"priority": p, "action": a, "addresses": addr}
                for p, a, addr in self._recommendations
            ],
            "evidence": self._evidence,
            "bus_posted": self._bus_posted,
            "bus_note": self._bus_note,
            "applied_codes": sorted(self._applied_codes),
        }
