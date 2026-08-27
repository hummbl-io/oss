"""Standalone regression test for the governance simulation prototype.

Matches the posture of ``test_tuples.py``: stdlib-only, runnable with a bare
``python3 test_simulation.py``. Asserts three things:

1. Every emitted event validates against the corresponding JSON Schema in
   ``schemas/``, reusing the stdlib validator from
   ``reference_impl/validate_examples.py``.
2. High-level scenario shape is correct: CONTRACT per agent, at least one
   scope-violation denial, one probation entry, one probation exit, one
   EVIDENCE per agent at the end.
3. The simulator is deterministic under a fixed seed: running it twice
   produces identical traces, and the trace-summary scalars are stable.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMAS_DIR = REPO_ROOT / "schemas"
VALIDATOR_PATH = REPO_ROOT / "reference_impl" / "validate_examples.py"


def _load_validator():
    """Import ``reference_impl/validate_examples.py`` without adding a package."""
    spec = importlib.util.spec_from_file_location(
        "hummbl_tuples_reference_validator", VALIDATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load validator from {VALIDATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_TUPLE_TYPE_TO_SCHEMA = {
    "CONTRACT": "contract.schema.json",
    "DCT": "dct.schema.json",
    "DCTX": "dctx.schema.json",
    "SYSTEM": "system.schema.json",
    "EVIDENCE": "evidence.schema.json",
}


def _load_schema(tuple_type: str) -> dict:
    schema_name = _TUPLE_TYPE_TO_SCHEMA[tuple_type]
    return json.loads((SCHEMAS_DIR / schema_name).read_text(encoding="utf-8"))


def test_governance_simulation() -> None:
    from hummbl_tuples.simulation import (
        Environment,
        gemini_probation_scenario,
        trace_summary,
    )

    validator = _load_validator()
    schemas = {t: _load_schema(t) for t in _TUPLE_TYPE_TO_SCHEMA}

    # --- 1. run + schema validation -------------------------------------
    scenario = gemini_probation_scenario()
    env = Environment(scenario, seed=0)
    trace = env.run()

    assert trace, "simulation produced no events"
    for idx, event in enumerate(trace):
        tuple_type = event.get("tuple_type")
        assert tuple_type in schemas, f"event[{idx}] has unknown tuple_type {tuple_type!r}"
        validator._validate(event, schemas[tuple_type], path=f"trace[{idx}]")
    print(f"Schema validation: OK ({len(trace)} events)")

    # --- 2. high-level scenario shape -----------------------------------
    summary = trace_summary(trace)
    assert summary["contracts"] == 3, f"expected 3 contracts, got {summary}"
    assert summary["scope_denials"] >= 2, f"expected >= 2 scope denials, got {summary}"
    assert summary["probation_entries"] == 1, f"expected 1 probation entry, got {summary}"
    assert summary["probation_exits"] == 1, f"expected 1 probation exit, got {summary}"
    assert summary["evidence_events"] == 3, f"expected 3 evidence events, got {summary}"
    print(f"Scenario shape: OK ({summary})")

    # Every agent must end with an EVIDENCE tuple keyed to its task.
    evidence_task_ids = {e["task_id"] for e in trace if e["tuple_type"] == "EVIDENCE"}
    assert evidence_task_ids == set(scenario.contracts), (
        f"evidence task ids {evidence_task_ids} != contracts {set(scenario.contracts)}"
    )
    print("Per-agent EVIDENCE coverage: OK")

    # --- 3. determinism ---------------------------------------------------
    env_b = Environment(scenario, seed=0)
    trace_b = env_b.run()
    assert trace == trace_b, "simulator is not deterministic under a fixed seed"
    assert trace_summary(trace) == trace_summary(trace_b)
    print("Determinism under seed=0: OK")

    # --- 4. probation actually restricted the executor's DCT ------------
    restricted_dcts = [
        e
        for e in trace
        if e["tuple_type"] == "DCT"
        and e["tuple_data"].get("event") == "reissued_restricted"
        and e["tuple_data"].get("subject") == "executor"
    ]
    assert len(restricted_dcts) == 1, "expected exactly one restricted DCT for executor"
    restricted_ops = restricted_dcts[0]["tuple_data"]["ops_allowed"]
    assert restricted_ops == ["read:research"], (
        f"expected restricted ops ['read:research'], got {restricted_ops}"
    )
    print("Probation DCT restriction: OK")

    # --- 5. restored DCT returns the full original scope ----------------
    restored_dcts = [
        e
        for e in trace
        if e["tuple_type"] == "DCT"
        and e["tuple_data"].get("event") == "reissued_restored"
        and e["tuple_data"].get("subject") == "executor"
    ]
    assert len(restored_dcts) == 1, "expected exactly one restored DCT for executor"
    restored_ops = restored_dcts[0]["tuple_data"]["ops_allowed"]
    assert set(restored_ops) == {
        "briefing:generate",
        "read:research",
        "publish:briefing",
    }, f"restored ops mismatch: {restored_ops}"
    print("Post-probation DCT restoration: OK")


if __name__ == "__main__":
    test_governance_simulation()
    print("\nALL SIMULATION TESTS PASSED")
