"""Base120 cognitive structuring for evaluation output.

Provides structured report formatting with operator codes, Why/Reveals/Action
analysis, and a standardized footer. Used by the CLI when ``--base120`` is passed.

The operator catalog is loaded from the canonical Base120 registry (120 operators
across 6 families: P/IN/CO/DE/RE/SY × 20) at import time. If the registry is
unavailable, a 27-entry fallback subset is used.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime
from importlib import resources
from pathlib import Path
from typing import Any

_FALLBACK_CODES: dict[str, str] = {
    "P1": "First Principles",
    "P5": "User Journey Mapping",
    "P6": "Point-of-View Anchoring",
    "P9": "Inclusive Design",
    "P16": "Identity Mapping",
    "CO1": "Modularity",
    "CO7": "Experiment Lifecycle",
    "CO11": "Pattern Extraction",
    "CO15": "Feature Store Patterns",
    "CO19": "Multimodal Synthesis",
    "DE1": "Root Cause Analysis",
    "DE5": "Separation of Concerns",
    "DE7": "Pareto Decomposition",
    "DE17": "Orthogonal Variation",
    "IN5": "Worst-Case Analysis",
    "IN6": "Claim Verification",
    "IN8": "Proof by Contradiction",
    "IN16": "Inverse Optimization",
    "IN17": "Counterfactual Exploration",
    "IN20": "Antigoals & Anti-Patterns Catalog",
    "RE1": "Receipt-Based Trust",
    "RE4": "Nested Narrative",
    "RE13": "Velocity Tuning",
    "RE16": "Retrospective to Prospective",
    "RE17": "Versioning & Diff",
    "SY1": "Causal Loop Diagrams",
    "SY13": "Reinforcing Feedback",
}


def _load_registry() -> tuple[dict[str, str], str]:
    """Load the Base120 operator registry from the first available source.

    Resolution order:
    1. ``BASE120_REGISTRY_PATH`` env var (explicit override)
    2. Bundled package data (``hummbl_eval/data/base120_registry.json``)
    3. Fallback 27-entry subset

    Returns:
        Tuple of (code→name dict, source label).
    """
    # 1. Env var override
    env_path = os.environ.get("BASE120_REGISTRY_PATH")
    if env_path:
        p = Path(env_path)
        if p.exists() and p.suffix == ".json":
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                codes = {e["id"]: e["name"] for e in data if "id" in e and "name" in e}
                if codes:
                    return codes, "env"
            except (OSError, ValueError, json.JSONDecodeError):
                pass

    # 2. Bundled package data
    try:
        with (
            resources.files("hummbl_eval.data")
            .joinpath("base120_registry.json")
            .open(encoding="utf-8") as f
        ):
            data = json.load(f)
        if isinstance(data, list):
            codes = {e["id"]: e["name"] for e in data if "id" in e and "name" in e}
            if codes:
                return codes, "bundled"
    except (OSError, ValueError, json.JSONDecodeError, ModuleNotFoundError):
        pass

    # 3. Fallback
    return _FALLBACK_CODES.copy(), "fallback"


BASE120_CODES, REGISTRY_SOURCE = _load_registry()
REGISTRY_COUNT = len(BASE120_CODES)


def _code_name(code: str) -> str:
    """Return the human-readable name for a Base120 code."""
    return BASE120_CODES.get(code, code)


def _now_utc() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")


class Base120Formatter:
    """Cognitive structuring formatter for report output.

    Accumulates Base120 codes as sections and findings are added,
    then prints a ``Base120 Applied:`` footer at the end.
    """

    def __init__(self, skill_name: str, subtitle: str = "all") -> None:
        self.skill_name = skill_name
        self.subtitle = subtitle
        self._applied_codes: set[str] = set()
        self._header_printed = False

    def _print(self, text: str = "") -> None:
        print(text, file=sys.stdout)

    def header(self) -> None:
        """Print the Base120 report header. Call once at the start."""
        if self._header_printed:
            return
        self._header_printed = True
        now = _now_utc()
        self._print(f"{self.skill_name} (Base120 Cognitive Structuring) | {self.subtitle} | {now}")
        self._print("=" * 70)
        self._print()

    def section(self, title: str, code: str, code_full_name: str | None = None) -> None:
        """Print a section header with a Base120 code annotation."""
        name = code_full_name or _code_name(code)
        self._applied_codes.add(code)
        self._print(f"## {title} ({code}: {name})")

    def metric(self, label: str, value: Any, indent: int = 2) -> None:
        """Print a metric line within a section."""
        prefix = " " * indent
        self._print(f"{prefix}{label}: {value}")

    def raw(self, text: str, indent: int = 0) -> None:
        """Print a raw line."""
        if indent:
            self._print(" " * indent + text)
        else:
            self._print(text)

    def blank(self) -> None:
        """Print a blank line."""
        self._print()

    def finding(
        self,
        title: str,
        severity: str,
        why: str,
        reveals: str,
        action: str,
        code: str = "DE1",
        code_full_name: str | None = None,
        detail: str = "",
        verify_method: str | None = None,
        uncertainty: str | None = None,
        indent: int = 4,
    ) -> None:
        """Print a finding with cognitive analysis (Why/Reveals/Action)."""
        self._applied_codes.add(code)
        prefix = " " * indent
        line = f"{prefix}[{severity:4s}] {title}"
        if detail:
            line += f" — {detail}"
        self._print(line)
        self._print(f"{prefix}  [{code}] Why: {why}")
        self._print(f"{prefix}  Reveals: {reveals}")
        self._print(f"{prefix}  Action: {action}")
        if verify_method:
            self._print(f"{prefix}  Verify-method: {verify_method}")
        if uncertainty:
            self._print(f"{prefix}  Uncertainty: {uncertainty}")

    def analysis(
        self,
        code: str,
        why: str,
        reveals: str,
        action: str,
        code_full_name: str | None = None,
        verify_method: str | None = None,
        uncertainty: str | None = None,
        indent: int = 2,
    ) -> None:
        """Print a standalone cognitive analysis block."""
        self._applied_codes.add(code)
        prefix = " " * indent
        self._print(f"{prefix}[{code}] Why: {why}")
        self._print(f"{prefix}Reveals: {reveals}")
        self._print(f"{prefix}Action: {action}")
        if verify_method:
            self._print(f"{prefix}Verify-method: {verify_method}")
        if uncertainty:
            self._print(f"{prefix}Uncertainty: {uncertainty}")

    def footer(self) -> None:
        """Print the Base120 Applied footer. Call once at the end."""
        codes = sorted(self._applied_codes)
        self._print()
        self._print(f"Base120 Applied: {', '.join(codes)}")
        self._print(f"Registry: {REGISTRY_SOURCE} ({REGISTRY_COUNT} operators)")
        self._print("=" * 70)

    @property
    def applied_codes(self) -> set[str]:
        """Return the set of Base120 codes applied so far."""
        return self._applied_codes.copy()
