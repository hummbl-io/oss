"""Kernel invariants (K1-K14) and panic handling.

Invariants are unbreakable rules. Violating any invariant is a Kernel panic.

K1-K8 are enforced on every receipt path. K9-K11 are enum-defined, schema-backed,
and exposed through Kernel validation methods. K12-K14 extend the invariant set
to cover safety, convergence detection, and physical-AI safety — closing the
primitive-invariant pairing gap identified in the 2026-09-02 assessment.

Each invariant carries a severity tier (CRITICAL → HIGH → MEDIUM → LOW) that
determines the response on violation:
  CRITICAL → KernelPanic, immediate halt
  HIGH     → KernelPanic, halt or quarantine
  MEDIUM   → Warning, operator review required
  LOW      → Log entry, informational
"""

from __future__ import annotations

import enum


class Severity(enum.Enum):
    """Graduated severity tiers for invariant violations.

    CRITICAL: System integrity compromised, immediate halt required.
    HIGH:     Serious violation, halt or quarantine.
    MEDIUM:   Warning, operator review required.
    LOW:      Log entry, informational.
    """

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# Default severity mapping for each invariant.
# Overrides per-call-site are allowed via KernelPanic(severity=...).
_DEFAULT_SEVERITY: dict[str, Severity] = {}


class KernelInvariant(enum.Enum):
    """The fourteen unbreakable Kernel invariants."""

    RECEIPT = "K1"
    """Every action that affects shared state produces a structured, signed receipt."""

    LAW = "K2"
    """Every receipt is evaluated against at least one scaling law."""

    IDENTITY = "K3"
    """Every agent has a single canonical identity, trust tier, and capability vector."""

    TEMPORAL = "K4"
    """Every receipt has a sequence_id for total ordering within its agent context."""

    EVIDENCE = "K5"
    """Every claim in a receipt is graded or marked speculative."""

    AUTHORITY = "K6"
    """Every authority exercise is scoped, limited, and leaves a receipt."""

    ROLE = "K7"
    """Every role is a runtime claim, not a static assignment."""

    DOCTRINE = "K8"
    """Every fleet artifact respects the doctrine invariants D1-D7."""

    REVERSIBILITY = "K9"
    """Every governed durable-state mutation or irreversible external side effect
    declares a rollback path or is explicitly marked irreversible with a recorded
    risk acceptance. Scoped: applies to governed durable-state mutations and
    irreversible external side effects only."""

    RECOVERY = "K10"
    """Re-engagement after halt, quarantine, or open breaker requires root-cause
    verification, evidence collection, and operator approval. Scoped: applies to
    re-engagement after halt/quarantine/open breaker only."""

    INTEGRITY = "K11"
    """Receipt sequences are complete and unbroken. Sequence gaps and hash-chain
    breaks trigger KernelPanic. Timestamp-only anomalies do NOT automatically
    trigger KernelPanic — they route to warning, quarantine, or operator review
    unless combined with sequence or hash compromise."""

    SAFETY = "K12"
    """Emergency halt and failure detection capabilities are always available
    and operational. Kill switch and circuit breaker must be reachable and
    responsive. Covers P1 (kill_switch) and P2 (circuit_breaker)."""

    CONVERGENCE = "K13"
    """Instrumental convergence patterns in agent behavior are detected and
    flagged. Agents that appear to optimize for unintended instrumental goals
    are identified before harm occurs. Covers P16 (convergence_guard)."""

    PHYSICAL_SAFETY = "K14"
    """Physical-AI actions respect kinematic constraints and pHRI safety modes.
    Robot actions must stay within declared speed, force, and proximity limits.
    Covers P20 (physical_governor)."""


# Populate default severity mapping
_DEFAULT_SEVERITY = {
    "K1": Severity.CRITICAL,
    "K2": Severity.HIGH,
    "K3": Severity.CRITICAL,
    "K4": Severity.MEDIUM,
    "K5": Severity.HIGH,
    "K6": Severity.CRITICAL,
    "K7": Severity.MEDIUM,
    "K8": Severity.HIGH,
    "K9": Severity.HIGH,
    "K10": Severity.HIGH,
    "K11": Severity.CRITICAL,
    "K12": Severity.MEDIUM,
    "K13": Severity.LOW,
    "K14": Severity.CRITICAL,
}


def default_severity(invariant: KernelInvariant) -> Severity:
    """Return the default severity tier for an invariant."""
    return _DEFAULT_SEVERITY.get(invariant.value, Severity.HIGH)


class KernelPanic(Exception):
    """Raised when a Kernel invariant is violated.

    A Kernel panic is not recoverable by the violating agent. The Kernel
    may halt, isolate, or quarantine depending on severity.

    The severity defaults to the invariant's default severity tier if not
    explicitly specified. Callers can override with a string ("CRITICAL",
    "HIGH", "MEDIUM", "LOW") or a Severity enum value.
    """

    def __init__(
        self,
        invariant: KernelInvariant,
        detail: str,
        agent_id: str | None = None,
        severity: str | Severity | None = None,
    ) -> None:
        self.invariant = invariant
        self.detail = detail
        self.agent_id = agent_id
        if severity is None:
            sev = default_severity(invariant)
            self.severity = sev.value.upper()
            self.severity_enum = sev
        elif isinstance(severity, Severity):
            self.severity = severity.value.upper()
            self.severity_enum = severity
        else:
            self.severity = str(severity).upper()
            try:
                self.severity_enum = Severity(str(severity).lower())
            except ValueError:
                self.severity_enum = Severity.HIGH
        super().__init__(f"KERNEL PANIC [{invariant.value}]: {detail}")
