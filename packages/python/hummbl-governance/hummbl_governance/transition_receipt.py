"""Transition receipts for governed agent/tool execution.

These helpers produce a small, portable record for the boundary discussed in
CrewAI governance hooks: the authorized tool transition, the runtime support
basis, the decision, and the terminal outcome if known.

Stdlib-only. Zero third-party dependencies.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import math
import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Literal

Decision = Literal["ALLOW", "SOFT_BLOCK", "HARD_BLOCK"]
TerminalOutcome = Literal["executed", "blocked", "failed_before_execution", "failed_after_execution"]
Reversibility = Literal["reversible", "boundary", "irreversible"]
Spendability = Literal["single_use", "retryable", "non_replayable"]


def canonical_json_bytes(data: Any) -> bytes:
    """Return deterministic UTF-8 JSON bytes for hash/signature preimages."""
    return json.dumps(
        _json_safe(data),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def stable_sha256(data: Any) -> str:
    """Return a sha256: prefixed digest over canonical JSON bytes."""
    return "sha256:" + hashlib.sha256(canonical_json_bytes(data)).hexdigest()


def _json_safe(value: Any) -> Any:
    """Convert common Python objects into deterministic JSON-safe values."""
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("Non-finite floats are not valid receipt preimages")
        return value
    if isinstance(value, bytes):
        return {"__bytes_sha256__": hashlib.sha256(value).hexdigest()}
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError(f"Receipt preimage dict keys must be strings, got {type(key).__name__}")
            result[key] = _json_safe(item)
        return {k: result[k] for k in sorted(result)}
    if isinstance(value, (set, frozenset)):
        items = [_json_safe(v) for v in value]
        return sorted(items, key=lambda item: json.dumps(item, sort_keys=True, separators=(",", ":"), allow_nan=False))
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return _json_safe(value.to_dict())
    if hasattr(value, "__dict__"):
        return _json_safe(vars(value))
    raise TypeError(f"Unsupported receipt preimage type: {type(value).__name__}")


@dataclass(frozen=True, slots=True)
class ToolTransitionReceipt:
    """Receipt binding a tool authorization decision to its support basis."""

    schema_version: str
    receipt_id: str
    timestamp: str
    runtime: str
    hook: str
    agent_id: str
    actor: str | None
    actor_mode: str
    tool_name: str
    action_hash: str
    context_hash: str
    policy_version: str
    reversibility: Reversibility
    spendability: Spendability
    decision: Decision
    reason: str
    support_basis: Mapping[str, Any] = field(default_factory=dict)
    terminal_outcome: TerminalOutcome | None = None
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    decision_hash: str = ""
    signature: str | None = None

    def __post_init__(self) -> None:
        """Freeze nested mutable containers so receipts cannot drift in memory."""
        object.__setattr__(self, "support_basis", _freeze(_json_safe(self.support_basis)))
        object.__setattr__(self, "evidence_refs", tuple(self.evidence_refs))

    def to_dict(self) -> dict[str, Any]:
        """Serialize receipt to a dict with stable key names."""
        return {
            "schema_version": self.schema_version,
            "receipt_id": self.receipt_id,
            "timestamp": self.timestamp,
            "runtime": self.runtime,
            "hook": self.hook,
            "agent_id": self.agent_id,
            "actor": self.actor,
            "actor_mode": self.actor_mode,
            "tool_name": self.tool_name,
            "action_hash": self.action_hash,
            "context_hash": self.context_hash,
            "policy_version": self.policy_version,
            "reversibility": self.reversibility,
            "spendability": self.spendability,
            "decision": self.decision,
            "reason": self.reason,
            "support_basis": _thaw(self.support_basis),
            "terminal_outcome": self.terminal_outcome,
            "evidence_refs": list(self.evidence_refs),
            "decision_hash": self.decision_hash,
            "signature": self.signature,
        }

    def canonical_dict(self) -> dict[str, Any]:
        """Return the receipt body used for decision hashing and signing."""
        data = self.to_dict()
        data["decision_hash"] = ""
        data["signature"] = None
        return data


def build_tool_transition_receipt(
    *,
    agent_id: str,
    tool_name: str,
    tool_input: Any,
    context: Any | None = None,
    runtime: str = "crewai",
    hook: str = "before_tool_call",
    actor: str | None = None,
    actor_mode: str = "autonomous_no_delegating_principal",
    policy_version: str = "hummbl-governance.transition-receipt.v1",
    reversibility: Reversibility = "boundary",
    spendability: Spendability = "single_use",
    kill_switch_result: dict[str, Any] | None = None,
    budget_status: Any | None = None,
    terminal_outcome: TerminalOutcome | None = None,
    evidence_refs: list[str] | None = None,
    signing_secret: bytes | None = None,
    timestamp: datetime | None = None,
) -> ToolTransitionReceipt:
    """Build a receipt for a pre-tool authorization decision.

    The decision is intentionally conservative: kill-switch denials and hard
    budget denials become HARD_BLOCK. Budget WARN remains ALLOW but is recorded
    in the support basis so callers can escalate separately if desired.
    """
    budget = _budget_to_dict(budget_status)
    support_basis = {
        "kill_switch": kill_switch_result or {"allowed": True, "action": "allow"},
        "budget": budget,
    }
    decision, reason = _decide(support_basis)
    ts = timestamp or datetime.now(timezone.utc)

    receipt = ToolTransitionReceipt(
        schema_version="tool-transition-receipt.v1",
        receipt_id=f"ttr-{uuid.uuid4().hex[:16]}",
        timestamp=ts.isoformat().replace("+00:00", "Z"),
        runtime=runtime,
        hook=hook,
        agent_id=agent_id,
        actor=actor,
        actor_mode=actor_mode if actor is None else "delegated_principal",
        tool_name=tool_name,
        action_hash=stable_sha256({"tool_name": tool_name, "tool_input": tool_input}),
        context_hash=stable_sha256({"__context_absent__": True} if context is None else context),
        policy_version=policy_version,
        reversibility=reversibility,
        spendability=spendability,
        decision=decision,
        reason=reason,
        support_basis=support_basis,
        terminal_outcome=terminal_outcome,
        evidence_refs=evidence_refs or [],
    )
    decision_hash = stable_sha256(receipt.canonical_dict())
    signature = _sign(receipt.canonical_dict() | {"decision_hash": decision_hash}, signing_secret)
    return ToolTransitionReceipt(**(receipt.to_dict() | {"decision_hash": decision_hash, "signature": signature}))


def verify_tool_transition_receipt(
    receipt: ToolTransitionReceipt | dict[str, Any],
    signing_secret: bytes | None = None,
) -> bool:
    """Verify the decision hash and, when a secret is supplied, the HMAC.

    Without a signing secret this only verifies deterministic public fields; it
    does not authenticate the receipt signature.
    """
    data = receipt.to_dict() if isinstance(receipt, ToolTransitionReceipt) else dict(receipt)
    expected_body = dict(data)
    expected_body["decision_hash"] = ""
    expected_body["signature"] = None
    expected_hash = stable_sha256(expected_body)
    if not hmac.compare_digest(expected_hash, str(data.get("decision_hash", ""))):
        return False
    if signing_secret is None:
        return True
    signature = data.get("signature")
    if not isinstance(signature, str):
        return False
    signed_body = dict(expected_body)
    signed_body["decision_hash"] = expected_hash
    expected_signature = _sign(signed_body, signing_secret)
    return expected_signature is not None and hmac.compare_digest(expected_signature, signature)


def _budget_to_dict(budget_status: Any | None) -> dict[str, Any] | None:
    if budget_status is None:
        return None
    if hasattr(budget_status, "to_dict") and callable(budget_status.to_dict):
        return dict(budget_status.to_dict())
    if isinstance(budget_status, dict):
        return dict(budget_status)
    return {"value": _json_safe(budget_status)}


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({k: _freeze(v) for k, v in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(v) for v in value)
    return value


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {k: _thaw(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return [_thaw(v) for v in value]
    return value


def _decide(support_basis: dict[str, Any]) -> tuple[Decision, str]:
    kill_switch = support_basis.get("kill_switch") or {}
    if kill_switch.get("allowed") is False:
        return "HARD_BLOCK", str(kill_switch.get("reason") or "kill switch denied tool transition")
    budget = support_basis.get("budget") or {}
    if budget.get("decision") == "DENY":
        return "HARD_BLOCK", str(budget.get("rationale") or "budget hard cap denied tool transition")
    return "ALLOW", "transition supported by current kill switch and budget state"


def _sign(data: dict[str, Any], signing_secret: bytes | None) -> str | None:
    if signing_secret is None:
        return None
    return hmac.new(signing_secret, canonical_json_bytes(data), hashlib.sha256).hexdigest()
