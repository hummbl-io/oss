"""Tuple-event constructors for the governance simulation.

These helpers emit plain dictionaries that conform to the JSON Schemas in
``schemas/`` (validated by ``reference_impl/validate_examples.py``). They are
intentionally schema-first rather than dataclass-first so that:

* a simulation trace is literally a list of schema-valid tuples,
* the same validator that guards checked-in examples also guards simulator
  output,
* migration into ``hummbl-governance`` requires no tuple-format translation.

TUPLES v2: all events include Layer 1 (id, time) and Layer 2 (state, drift,
tier, agent, tool) fields since simulation events are IDP governance tuples.
"""

from __future__ import annotations

from typing import Any, Iterable

# Counter for deterministic ID generation in simulation context.
# Reset via reset_id_counter() at simulation start.
_id_counter = 0


def _short_id() -> str:
    global _id_counter
    _id_counter += 1
    return f"sim-{_id_counter:06d}"


def reset_id_counter() -> None:
    """Reset the event ID counter for deterministic simulation runs."""
    global _id_counter
    _id_counter = 0


def _layer1_layer2(
    timestamp: str,
    agent: str = "simulation",
    tool: str = "governance.simulation",
    state: str = "ok",
    drift: float = 0.0,
    tier: int = 1,
) -> dict[str, Any]:
    """Build Layer 1 + Layer 2 envelope fields."""
    return {
        "id": _short_id(),
        "time": timestamp,
        "state": state,
        "drift": drift,
        "tier": tier,
        "agent": agent,
        "tool": tool,
    }


def contract_event(
    *,
    timestamp: str,
    intent_id: str,
    task_id: str,
    delegatee: str,
    objective: str,
    allowed_tools: Iterable[str],
    outputs: Iterable[str],
    risk_tier: str,
    evidence_requirements: Iterable[str] | None = None,
    denied_tools: Iterable[str] | None = None,
    inputs: Iterable[str] | None = None,
    max_subdelegation_depth: int = 1,
    contract_id: str | None = None,
    agent: str = "simulation",
) -> dict[str, Any]:
    """Build a CONTRACT tuple dict conforming to ``schemas/contract.schema.json``."""
    tuple_data: dict[str, Any] = {
        "contract_id": contract_id or task_id,
        "delegatee": delegatee,
        "objective": objective,
        "allowed_tools": list(allowed_tools),
        "outputs": list(outputs),
        "risk_tier": risk_tier,
        "max_subdelegation_depth": max_subdelegation_depth,
    }
    if evidence_requirements is not None:
        tuple_data["evidence_requirements"] = list(evidence_requirements)
    if denied_tools is not None:
        tuple_data["denied_tools"] = list(denied_tools)
    if inputs is not None:
        tuple_data["inputs"] = list(inputs)
    return {
        "tuple_type": "CONTRACT",
        **_layer1_layer2(timestamp, agent=agent, tier=2),
        "intent_id": intent_id,
        "task_id": task_id,
        "tuple_data": tuple_data,
    }


def dct_event(
    *,
    timestamp: str,
    intent_id: str,
    task_id: str,
    issuer: str,
    subject: str,
    ops_allowed: Iterable[str],
    token_id: str,
    event: str = "issued",
    agent: str = "simulation",
) -> dict[str, Any]:
    """Build a DCT tuple dict conforming to ``schemas/dct.schema.json``."""
    return {
        "tuple_type": "DCT",
        **_layer1_layer2(timestamp, agent=agent, tier=2),
        "intent_id": intent_id,
        "task_id": task_id,
        "tuple_data": {
            "event": event,
            "issuer": issuer,
            "subject": subject,
            "ops_allowed": list(ops_allowed),
            "token_id": token_id,
        },
    }


def dctx_event(
    *,
    timestamp: str,
    intent_id: str,
    task_id: str,
    event: str,
    status: str | None = None,
    parent_task_id: str | None = None,
    chain_depth: int | None = None,
    adapter: str | None = None,
    agent: str = "simulation",
    state: str = "ok",
) -> dict[str, Any]:
    """Build a DCTX tuple dict conforming to ``schemas/dctx.schema.json``."""
    tuple_data: dict[str, Any] = {"event": event}
    if status is not None:
        tuple_data["status"] = status
    if parent_task_id is not None:
        tuple_data["parent_task_id"] = parent_task_id
    if chain_depth is not None:
        tuple_data["chain_depth"] = chain_depth
    if adapter is not None:
        tuple_data["adapter"] = adapter
    return {
        "tuple_type": "DCTX",
        **_layer1_layer2(timestamp, agent=agent, state=state, tier=2),
        "intent_id": intent_id,
        "task_id": task_id,
        "tuple_data": tuple_data,
    }


def system_event(
    *,
    timestamp: str,
    intent_id: str,
    task_id: str,
    event: str,
    adapter: str | None = None,
    enforcement: str | None = None,
    error: str | None = None,
    required: str | None = None,
    ops_allowed: Iterable[str] | None = None,
    agent: str = "simulation",
    state: str = "ok",
) -> dict[str, Any]:
    """Build a SYSTEM tuple dict conforming to ``schemas/system.schema.json``."""
    tuple_data: dict[str, Any] = {"event": event}
    if adapter is not None:
        tuple_data["adapter"] = adapter
    if enforcement is not None:
        tuple_data["enforcement"] = enforcement
    if error is not None:
        tuple_data["error"] = error
    if required is not None:
        tuple_data["required"] = required
    if ops_allowed is not None:
        tuple_data["ops_allowed"] = list(ops_allowed)
    return {
        "tuple_type": "SYSTEM",
        **_layer1_layer2(timestamp, agent=agent, state=state, tier=1),
        "intent_id": intent_id,
        "task_id": task_id,
        "tuple_data": tuple_data,
    }


def evidence_event(
    *,
    timestamp: str,
    intent_id: str,
    task_id: str,
    event: str,
    evidence_id: str,
    duration_s: float | None = None,
    warnings_count: int | None = None,
    agents_ready: bool | None = None,
    budget_exceeded: bool | None = None,
    agent: str = "simulation",
) -> dict[str, Any]:
    """Build an EVIDENCE tuple dict conforming to ``schemas/evidence.schema.json``."""
    tuple_data: dict[str, Any] = {"event": event, "evidence_id": evidence_id}
    if duration_s is not None:
        tuple_data["duration_s"] = duration_s
    if warnings_count is not None:
        tuple_data["warnings_count"] = warnings_count
    if agents_ready is not None:
        tuple_data["agents_ready"] = agents_ready
    if budget_exceeded is not None:
        tuple_data["budget_exceeded"] = budget_exceeded
    return {
        "tuple_type": "EVIDENCE",
        **_layer1_layer2(timestamp, agent=agent, tier=1),
        "intent_id": intent_id,
        "task_id": task_id,
        "tuple_data": tuple_data,
    }
