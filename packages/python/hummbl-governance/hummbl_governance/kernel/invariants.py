"""Kernel invariants (K1-K11) and panic handling.

Invariants are unbreakable rules. Violating any invariant is a Kernel panic.
"""

from __future__ import annotations

import enum


class KernelInvariant(enum.Enum):
    """The eleven unbreakable Kernel invariants."""

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


class KernelPanic(Exception):
    """Raised when a Kernel invariant is violated.

    A Kernel panic is not recoverable by the violating agent. The Kernel
    may halt, isolate, or quarantine depending on severity.
    """

    def __init__(
        self,
        invariant: KernelInvariant,
        detail: str,
        agent_id: str | None = None,
        severity: str = "CRITICAL",
    ) -> None:
        self.invariant = invariant
        self.detail = detail
        self.agent_id = agent_id
        self.severity = severity
        super().__init__(f"KERNEL PANIC [{invariant.value}]: {detail}")
