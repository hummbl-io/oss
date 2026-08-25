from datetime import datetime, timezone

import pytest

from hummbl_governance import (
    CostGovernor,
    build_tool_transition_receipt,
    verify_tool_transition_receipt,
)
from hummbl_governance.transition_receipt import stable_sha256


def test_stable_sha256_is_order_independent():
    left = {"b": 2, "a": {"z": 3, "y": 4}}
    right = {"a": {"y": 4, "z": 3}, "b": 2}
    assert stable_sha256(left) == stable_sha256(right)


def test_stable_sha256_sorts_sets():
    left = {"tools": {"search", "write", "read"}}
    right = {"tools": {"read", "search", "write"}}
    assert stable_sha256(left) == stable_sha256(right)


def test_stable_sha256_rejects_non_string_dict_keys():
    with pytest.raises(TypeError, match="dict keys must be strings"):
        stable_sha256({1: "numeric", "1": "string"})


def test_stable_sha256_rejects_non_finite_float():
    with pytest.raises(ValueError, match="Non-finite floats"):
        stable_sha256({"cost": float("nan")})


def test_stable_sha256_rejects_unsupported_objects():
    with pytest.raises(TypeError, match="Unsupported receipt preimage type"):
        stable_sha256(object())


def test_context_hash_preserves_falsey_values():
    false_receipt = build_tool_transition_receipt(
        agent_id="researcher",
        tool_name="search_docs",
        tool_input={"query": "x"},
        context=False,
    )
    empty_receipt = build_tool_transition_receipt(
        agent_id="researcher",
        tool_name="search_docs",
        tool_input={"query": "x"},
        context={},
    )
    assert false_receipt.context_hash != empty_receipt.context_hash


def test_context_hash_distinguishes_absent_from_empty_context():
    absent_receipt = build_tool_transition_receipt(
        agent_id="researcher",
        tool_name="search_docs",
        tool_input={"query": "x"},
    )
    empty_receipt = build_tool_transition_receipt(
        agent_id="researcher",
        tool_name="search_docs",
        tool_input={"query": "x"},
        context={},
    )
    assert absent_receipt.context_hash != empty_receipt.context_hash


def test_to_dict_does_not_expose_live_mutable_support_basis():
    receipt = build_tool_transition_receipt(
        agent_id="researcher",
        tool_name="search_docs",
        tool_input={"query": "x"},
        budget_status={"decision": "ALLOW", "rationale": "ok"},
    )
    data = receipt.to_dict()
    data["support_basis"]["budget"]["decision"] = "DENY"
    assert receipt.to_dict()["support_basis"]["budget"]["decision"] == "ALLOW"


def test_build_allow_receipt_with_signature():
    receipt = build_tool_transition_receipt(
        agent_id="researcher",
        tool_name="search_docs",
        tool_input={"query": "CrewAI governance"},
        context={"task": "research"},
        signing_secret=b"secret",
        timestamp=datetime(2026, 7, 2, tzinfo=timezone.utc),
    )

    assert receipt.decision == "ALLOW"
    assert receipt.action_hash.startswith("sha256:")
    assert receipt.context_hash.startswith("sha256:")
    assert receipt.decision_hash.startswith("sha256:")
    assert receipt.signature is not None
    assert verify_tool_transition_receipt(receipt, signing_secret=b"secret") is True


def test_kill_switch_denial_becomes_hard_block():
    receipt = build_tool_transition_receipt(
        agent_id="researcher",
        tool_name="delete_record",
        tool_input={"record_id": "cust-123"},
        kill_switch_result={
            "allowed": False,
            "action": "block",
            "reason": "Kill switch engaged (HALT_ALL): delete_record blocked",
        },
    )

    assert receipt.decision == "HARD_BLOCK"
    assert "Kill switch engaged" in receipt.reason
    assert verify_tool_transition_receipt(receipt) is True


def test_budget_deny_becomes_hard_block():
    gov = CostGovernor(":memory:", soft_cap=1.0, hard_cap=2.0)
    gov.record_usage("openai", "gpt-4", 100, 50, 3.0)

    receipt = build_tool_transition_receipt(
        agent_id="researcher",
        tool_name="expensive_llm_tool",
        tool_input={"prompt": "continue"},
        budget_status=gov.check_budget_status(),
    )

    assert receipt.decision == "HARD_BLOCK"
    assert "hard cap" in receipt.reason


def test_budget_warn_remains_allow_with_support_basis():
    receipt = build_tool_transition_receipt(
        agent_id="researcher",
        tool_name="moderate_llm_tool",
        tool_input={"prompt": "continue"},
        budget_status={"decision": "WARN", "rationale": "soft cap exceeded"},
    )

    assert receipt.decision == "ALLOW"
    assert receipt.support_basis["budget"]["decision"] == "WARN"
    assert receipt.support_basis["budget"]["rationale"] == "soft cap exceeded"


def test_non_mapping_budget_status_is_preserved_without_decision_crash():
    receipt = build_tool_transition_receipt(
        agent_id="researcher",
        tool_name="custom_budget_tool",
        tool_input={"prompt": "continue"},
        budget_status=["WARN", "soft cap exceeded"],
    )

    assert receipt.decision == "ALLOW"
    assert receipt.support_basis["budget"]["value"] == ("WARN", "soft cap exceeded")


def test_tampering_breaks_verification():
    receipt = build_tool_transition_receipt(
        agent_id="researcher",
        tool_name="search_docs",
        tool_input={"query": "x"},
        signing_secret=b"secret",
    )
    data = receipt.to_dict()
    data["decision"] = "HARD_BLOCK"

    assert verify_tool_transition_receipt(data, signing_secret=b"secret") is False


def test_signature_verification_fails_with_wrong_secret():
    receipt = build_tool_transition_receipt(
        agent_id="researcher",
        tool_name="search_docs",
        tool_input={"query": "x"},
        signing_secret=b"secret",
    )

    assert verify_tool_transition_receipt(receipt, signing_secret=b"wrong-secret") is False
