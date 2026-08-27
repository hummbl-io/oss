"""Tests for HUMMBL Typed Tuples.

Covers all tuple domains (IDP, BaseN, Nodezero, Traces) with tests for:
- Construction and field access
- Immutability (frozen dataclass)
- Serialization to canonical envelope + tuple_data shape
- Round-trip from_dict -> to_dict fidelity
- Deterministic SHA-256 hashing
- Schema validation of Python-serialized output
"""

from __future__ import annotations

import json
from pathlib import Path

import hummbl_tuples
from hummbl_tuples import (
    AttestTuple,
    BaseProfileIssuedTuple,
    ContractTuple,
    ControlModeSetTuple,
    DCTTuple,
    DCTXTuple,
    EvidenceTuple,
    ExperimentRunAssignedTuple,
    HitlOverrideTuple,
    ModelCandidateTuple,
    ModelSelectedTuple,
    PathComparisonTuple,
    PosttrainingTrace,
    PretrainingTrace,
    PromotionReceiptTuple,
    ReasoningPathTuple,
    RegistryVersionPinnedTuple,
    RevocationTuple,
    SystemTuple,
    TraceEvidenceTuple,
    TransformationCandidateTuple,
    TransformationSelectedTuple,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMAS_DIR = REPO_ROOT / "schemas"

# Import the stdlib validator for schema checks
import sys

sys.path.insert(0, str(REPO_ROOT / "reference_impl"))
from validate_examples import ValidationError, _check_schema_features, _validate

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _validate_against_schema(instance_dict: dict, schema_name: str) -> None:
    """Validate a dict against a named schema file."""
    schema_path = SCHEMAS_DIR / schema_name
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    _validate(instance_dict, schema)


def test_additional_properties_schema_values_are_validated():
    schema = {
        "type": "object",
        "additionalProperties": {"type": "string"},
    }

    _validate({"artifact": "ok"}, schema)

    try:
        _validate({"artifact": 3}, schema)
        assert False, "schema-valued additionalProperties should validate map values"
    except ValidationError as exc:
        assert "$.artifact: expected string" in str(exc)


def test_unsupported_schema_keywords_fail_loudly():
    # Validator allowlist intentionally rejects features not yet implemented
    # (oneOf/anyOf/multipleOf/etc.) so unknown keywords cannot silently pass.
    try:
        _check_schema_features({"type": "string", "oneOf": [{"type": "string"}]})
        assert False, "unsupported schema keywords should fail before validation"
    except ValidationError as exc:
        assert "unsupported schema keyword 'oneOf'" in str(exc)


# ---------------------------------------------------------------------------
# IDP Tuple Tests
# ---------------------------------------------------------------------------


class TestContractTuple:
    def test_construction(self):
        ct = ContractTuple(
            intent_id="i-1",
            task_id="t-1",
            objective="Do the thing",
            allowed_tools=["read", "write"],
            outputs=["result"],
            risk_tier="LOW",
        )
        assert ct.tuple_type == "CONTRACT"
        assert ct.objective == "Do the thing"
        assert ct.risk_tier == "LOW"

    def test_immutability(self):
        ct = ContractTuple(
            intent_id="i-1",
            task_id="t-1",
            objective="x",
            allowed_tools=[],
            outputs=[],
            risk_tier="LOW",
        )
        try:
            ct.objective = "changed"
            assert False, "Should have raised"
        except AttributeError:
            pass

    def test_envelope_shape(self):
        ct = ContractTuple(
            intent_id="i-1",
            task_id="t-1",
            objective="x",
            allowed_tools=["a"],
            outputs=["b"],
            risk_tier="MED",
            max_subdelegation_depth=2,
        )
        d = ct.to_dict()
        assert d["tuple_type"] == "CONTRACT"
        assert "intent_id" in d
        assert "task_id" in d
        assert "time" in d
        assert d["tuple_data"]["objective"] == "x"
        assert d["tuple_data"]["max_subdelegation_depth"] == 2

    def test_round_trip(self):
        ct = ContractTuple(
            intent_id="i-1",
            task_id="t-1",
            time="2026-01-01T00:00:00Z",
            objective="obj",
            allowed_tools=["r"],
            outputs=["o"],
            risk_tier="LOW",
        )
        d = ct.to_dict()
        ct2 = ContractTuple.from_dict(d)
        assert ct2.objective == ct.objective
        assert ct2.to_json() == ct.to_json()

    def test_hash_determinism(self):
        kwargs = dict(
            id="fixed-id",
            time="2026-01-01T00:00:00Z",
            intent_id="i",
            task_id="t",
            objective="o",
            allowed_tools=[],
            outputs=[],
            risk_tier="L",
        )
        assert ContractTuple(**kwargs).hash == ContractTuple(**kwargs).hash

    def test_schema_validation(self):
        ct = ContractTuple(
            intent_id="i-1",
            task_id="t-1",
            objective="x",
            allowed_tools=["a"],
            outputs=["b"],
            risk_tier="LOW",
        )
        _validate_against_schema(ct.to_dict(), "contract.schema.json")


class TestDCTTuple:
    def test_envelope_and_schema(self):
        dct = DCTTuple(
            intent_id="i-1",
            task_id="t-1",
            issuer="gov",
            subject="agent-1",
            ops_allowed=["train"],
            event="issued",
            token_id="tok-1",
        )
        d = dct.to_dict()
        assert d["tuple_data"]["issuer"] == "gov"
        assert d["tuple_data"]["ops_allowed"] == ["train"]
        _validate_against_schema(d, "dct.schema.json")

    def test_round_trip(self):
        dct = DCTTuple(
            intent_id="i",
            task_id="t",
            time="2026-01-01T00:00:00Z",
            issuer="a",
            subject="b",
            ops_allowed=["x"],
        )
        assert DCTTuple.from_dict(dct.to_dict()).hash == dct.hash


class TestDCTXTuple:
    def test_envelope_and_schema(self):
        dx = DCTXTuple(
            intent_id="i-1",
            task_id="t-1",
            event="issued",
            status="PROPOSED",
            chain_depth=0,
        )
        d = dx.to_dict()
        assert d["tuple_data"]["event"] == "issued"
        _validate_against_schema(d, "dctx.schema.json")


class TestPromotionReceiptTuple:
    def test_envelope_and_schema(self):
        receipt = PromotionReceiptTuple(
            intent_id="i-1",
            task_id="candidate-1",
            candidate_id="candidate-1",
            rung_from="local",
            rung_to="linux-1gpu",
            decision="allow",
            decided_by="governor",
            policy_version="promo-v1",
            reason_codes=["artifact_complete"],
            artifact_manifest={"results": "r2://results.json"},
        )
        d = receipt.to_dict()
        assert d["tuple_data"]["decision"] == "allow"
        _validate_against_schema(d, "promotion_receipt.schema.json")


class TestRevocationTuple:
    def test_envelope_and_schema(self):
        revocation = RevocationTuple(
            intent_id="i-1",
            task_id="task-1",
            token_id="token-1",
            subject="agent-1",
            revoked_by="kill-switch",
            reason="manual emergency halt",
            cascade=True,
        )
        d = revocation.to_dict()
        assert d["tuple_data"]["terminal_state"] == "REVOKED"
        _validate_against_schema(d, "revocation.schema.json")


class TestEvidenceTuple:
    def test_envelope_and_schema(self):
        ev = EvidenceTuple(
            intent_id="i-1",
            task_id="t-1",
            event="task_completed",
            duration_s=12.5,
            warnings_count=0,
        )
        d = ev.to_dict()
        assert d["tuple_data"]["duration_s"] == 12.5
        _validate_against_schema(d, "evidence.schema.json")


class TestAttestTuple:
    def test_envelope_and_schema(self):
        at = AttestTuple(
            intent_id="i-1",
            task_id="t-1",
            event="verified",
            evidence_hash="abc123",
            verifier_id="v-1",
            passed=True,
            findings=["all criteria met"],
        )
        d = at.to_dict()
        assert d["tuple_data"]["passed"] is True
        _validate_against_schema(d, "attest.schema.json")


class TestSystemTuple:
    def test_envelope_and_schema(self):
        st = SystemTuple(
            intent_id="i-1",
            task_id="t-1",
            event="adapter_invoked",
            adapter="openai",
            required_capability="chat",
        )
        d = st.to_dict()
        assert d["tuple_data"]["required_capability"] == "chat"
        assert "required" not in d["tuple_data"]
        _validate_against_schema(d, "system.schema.json")


# ---------------------------------------------------------------------------
# BaseN Tuple Tests
# ---------------------------------------------------------------------------


class TestModelCandidateTuple:
    def test_envelope_and_schema(self):
        mc = ModelCandidateTuple(
            problem_id="p1",
            run_id="r1",
            control_mode="AI_AUTONOMOUS",
            transformation_id="t1",
            mental_model_id="m1",
            candidate_rank=1,
            proposed_by="agent",
        )
        d = mc.to_dict()
        assert d["control_mode"] == "AI_AUTONOMOUS"
        assert d["tuple_data"]["candidate_rank"] == 1
        _validate_against_schema(d, "model_candidate.schema.json")


class TestModelSelectedTuple:
    def test_envelope_and_schema(self):
        ms = ModelSelectedTuple(
            problem_id="p1",
            run_id="r1",
            control_mode="HITL_CONTROLLED",
            transformation_id="t1",
            mental_model_id="m1",
            selected_by="human",
            selection_rationale="best fit",
        )
        d = ms.to_dict()
        _validate_against_schema(d, "model_selected.schema.json")

    def test_round_trip(self):
        ms = ModelSelectedTuple(
            problem_id="p1",
            run_id="r1",
            control_mode="AI_AUTONOMOUS",
            transformation_id="t1",
            mental_model_id="m1",
            selected_by="agent",
            selection_rationale="r",
        )
        assert ModelSelectedTuple.from_dict(ms.to_dict()).hash == ms.hash


class TestTransformationCandidateTuple:
    def test_schema(self):
        tc = TransformationCandidateTuple(
            problem_id="p1",
            run_id="r1",
            control_mode="AI_AUTONOMOUS",
            transformation_id="t1",
            candidate_rank=1,
            proposed_by="agent",
            selection_rationale="r",
        )
        _validate_against_schema(tc.to_dict(), "transformation_candidate.schema.json")


class TestTransformationSelectedTuple:
    def test_schema(self):
        ts = TransformationSelectedTuple(
            problem_id="p1",
            run_id="r1",
            control_mode="AI_AUTONOMOUS",
            transformation_id="t1",
            selected_by="agent",
            selection_rationale="r",
        )
        _validate_against_schema(ts.to_dict(), "transformation_selected.schema.json")


class TestHitlOverrideTuple:
    def test_schema(self):
        ho = HitlOverrideTuple(
            problem_id="p1",
            run_id="r1",
            control_mode="HITL_CONTROLLED",
            overridden_tuple_id="prev-1",
            override_type="MODEL_CHANGE",
            human_actor="researcher",
            override_reason="better model available",
        )
        _validate_against_schema(ho.to_dict(), "hitl_override.schema.json")


class TestReasoningPathTuple:
    def test_schema(self):
        rp = ReasoningPathTuple(
            problem_id="p1",
            run_id="r1",
            control_mode="AI_AUTONOMOUS",
            path_id="path-1",
            constructed_by="agent",
            path_steps=[
                {"step_index": 1, "transformation_id": "t1", "mental_model_id": "m1"},
                {"step_index": 2, "transformation_id": "t2", "mental_model_id": "m2"},
            ],
            path_depth=2,
        )
        _validate_against_schema(rp.to_dict(), "reasoning_path.schema.json")


class TestPathComparisonTuple:
    def test_schema(self):
        pc = PathComparisonTuple(
            problem_id="p1",
            run_id="r1",
            control_mode="AI_AUTONOMOUS",
            path_a_id="a",
            path_b_id="b",
            comparison_basis="task_success",
            preferred_path="A",
            decided_by="agent",
        )
        _validate_against_schema(pc.to_dict(), "path_comparison.schema.json")


class TestTraceEvidenceTuple:
    def test_schema(self):
        te = TraceEvidenceTuple(
            problem_id="p1",
            run_id="r1",
            control_mode="AI_AUTONOMOUS",
            path_id="path-1",
            claim="Model improves task success",
            evidence_status="SUPPORTED",
            metric_bundle={"task_success": 0.92, "token_cost": 12000},
        )
        _validate_against_schema(te.to_dict(), "trace_evidence_tuple.schema.json")


# ---------------------------------------------------------------------------
# Nodezero Tuple Tests
# ---------------------------------------------------------------------------


class TestBaseProfileIssuedTuple:
    def test_schema(self):
        bp = BaseProfileIssuedTuple(run_id="r1", base_profile="gpt-4-base")
        d = bp.to_dict()
        assert d["tuple_data"]["issued_by"] == "nodezero"
        _validate_against_schema(d, "base_profile_issued.schema.json")


class TestControlModeSetTuple:
    def test_schema(self):
        cm = ControlModeSetTuple(
            run_id="r1",
            control_mode="AI_AUTONOMOUS",
            rationale="baseline run",
        )
        _validate_against_schema(cm.to_dict(), "control_mode_set.schema.json")


class TestExperimentRunAssignedTuple:
    def test_schema(self):
        er = ExperimentRunAssignedTuple(
            problem_id="p1",
            run_id="r1",
            assignee="agent-1",
            control_mode="AI_AUTONOMOUS",
        )
        d = er.to_dict()
        assert d["problem_id"] == "p1"
        _validate_against_schema(d, "experiment_run_assigned.schema.json")


class TestRegistryVersionPinnedTuple:
    def test_schema(self):
        rv = RegistryVersionPinnedTuple(
            run_id="r1",
            transformation_registry_version="1.0.0",
            mental_model_registry_version="1.0.0",
        )
        _validate_against_schema(rv.to_dict(), "registry_version_pinned.schema.json")


# ---------------------------------------------------------------------------
# Trace Artifact Tests
# ---------------------------------------------------------------------------


class TestPretrainingTrace:
    def test_envelope_shape(self):
        pt = PretrainingTrace(
            trace_source="human",
            trace_visibility="explicit",
            governance_status="draft",
            objective="train reasoning",
            corpus_role="training",
        )
        d = pt.to_dict()
        assert d["artifact_type"] == "reasoning_trace"
        assert d["lifecycle_stage"] == "pretraining"
        assert "tuple_type" not in d  # traces use artifact_type
        assert "id" in d  # Layer 1 universal
        assert "time" in d  # Layer 1 universal
        assert "payload" in d
        assert d["payload"]["objective"] == "train reasoning"
        _validate_against_schema(d, "pretraining_trace.schema.json")

    def test_round_trip(self):
        pt = PretrainingTrace(
            trace_source="human",
            trace_visibility="explicit",
            governance_status="draft",
            objective="o",
            corpus_role="c",
        )
        pt2 = PretrainingTrace.from_dict(pt.to_dict())
        assert pt2.corpus_role == pt.corpus_role


class TestPosttrainingTrace:
    def test_schema(self):
        pt = PosttrainingTrace(
            lifecycle_stage="sft",
            trace_source="human",
            trace_visibility="explicit",
            governance_status="trusted",
            objective="fine-tune",
            trace_role="supervision",
        )
        _validate_against_schema(pt.to_dict(), "posttraining_trace.schema.json")


# ---------------------------------------------------------------------------
# Cross-cutting tests
# ---------------------------------------------------------------------------


class TestLayer1Universal:
    """Verify Layer 1 fields (id, time) are present on ALL tuple families."""

    def test_idp_has_layer1(self):
        ct = ContractTuple(
            intent_id="i", task_id="t", objective="x", allowed_tools=[], outputs=[], risk_tier="L"
        )
        d = ct.to_dict()
        assert "id" in d and len(d["id"]) > 0
        assert "time" in d and "T" in d["time"]

    def test_basen_has_layer1(self):
        ms = ModelSelectedTuple(
            problem_id="p",
            run_id="r",
            control_mode="AI_AUTONOMOUS",
            transformation_id="t",
            mental_model_id="m",
            selected_by="agent",
            selection_rationale="r",
        )
        d = ms.to_dict()
        assert "id" in d and len(d["id"]) > 0
        assert "time" in d

    def test_nodezero_has_layer1(self):
        bp = BaseProfileIssuedTuple(run_id="r1", base_profile="gpt-4-base")
        d = bp.to_dict()
        assert "id" in d
        assert "time" in d

    def test_trace_has_layer1(self):
        pt = PretrainingTrace(
            trace_source="human",
            trace_visibility="explicit",
            governance_status="draft",
            objective="o",
            corpus_role="c",
        )
        d = pt.to_dict()
        assert "id" in d
        assert "time" in d


class TestLayer2Governance:
    """Verify Layer 2 fields are present on IDP tuples and absent on research tuples."""

    def test_idp_has_layer2(self):
        ct = ContractTuple(
            intent_id="i", task_id="t", objective="x", allowed_tools=[], outputs=[], risk_tier="L"
        )
        d = ct.to_dict()
        assert "state" in d
        assert "drift" in d
        assert "tier" in d
        assert "agent" in d
        assert "tool" in d

    def test_basen_no_layer2(self):
        ms = ModelSelectedTuple(
            problem_id="p",
            run_id="r",
            control_mode="AI_AUTONOMOUS",
            transformation_id="t",
            mental_model_id="m",
            selected_by="agent",
            selection_rationale="r",
        )
        d = ms.to_dict()
        assert "state" not in d
        assert "drift" not in d
        assert "tier" not in d

    def test_nodezero_no_layer2(self):
        bp = BaseProfileIssuedTuple(run_id="r1", base_profile="gpt-4-base")
        d = bp.to_dict()
        assert "state" not in d
        assert "drift" not in d


class TestSchemaValidationNegative:
    """Verify schemas reject invalid input."""

    def test_missing_required_field(self):
        """CONTRACT without tuple_type should fail validation."""
        bad = {
            "id": "x",
            "time": "2026-01-01T00:00:00Z",
            "intent_id": "i",
            "task_id": "t",
            "tuple_data": {},
        }
        import pytest

        with pytest.raises(Exception):
            _validate_against_schema(bad, "contract.schema.json")

    def test_invalid_state_enum(self):
        """Layer 2 state must be ok/blocked/error."""
        ct = ContractTuple(
            intent_id="i", task_id="t", objective="x", allowed_tools=[], outputs=[], risk_tier="L"
        )
        d = ct.to_dict()
        d["state"] = "invalid_state"
        import pytest

        with pytest.raises(Exception):
            _validate_against_schema(d, "contract.schema.json")

    def test_negative_drift(self):
        """Drift must be >= 0."""
        ct = ContractTuple(
            intent_id="i", task_id="t", objective="x", allowed_tools=[], outputs=[], risk_tier="L"
        )
        d = ct.to_dict()
        d["drift"] = -0.5
        import pytest

        with pytest.raises(Exception):
            _validate_against_schema(d, "contract.schema.json")

    def test_empty_id_rejected(self):
        """id must have minLength 1."""
        ct = ContractTuple(
            intent_id="i", task_id="t", objective="x", allowed_tools=[], outputs=[], risk_tier="L"
        )
        d = ct.to_dict()
        d["id"] = ""
        import pytest

        with pytest.raises(Exception):
            _validate_against_schema(d, "contract.schema.json")


class TestFromDictErrors:
    """Verify from_dict error handling."""

    def test_non_dict_input(self):
        import pytest

        with pytest.raises(ValueError, match="expected dict"):
            ContractTuple.from_dict("not a dict")

    def test_non_dict_input_list(self):
        import pytest

        with pytest.raises(ValueError, match="expected dict"):
            ContractTuple.from_dict([1, 2, 3])


class TestSchemaCoverage:
    """Verify every example has a schema and validates."""

    def test_all_examples_validate(self):
        """Replicates make validate as a pytest test."""
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "validator", str(REPO_ROOT / "reference_impl" / "validate_examples.py")
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        assert mod.main() == 0


class TestVersion:
    def test_version_accessible(self):
        assert hummbl_tuples.__version__ == "0.2.0"


class TestGovernanceChain:
    """Integration test: build a full CONTRACT -> DCT -> DCTX -> EVIDENCE -> ATTEST chain."""

    def test_chain(self):
        contract = ContractTuple(
            intent_id="intent-1",
            task_id="task-1",
            objective="Generate morning briefing",
            allowed_tools=["briefing:generate"],
            outputs=["briefing content"],
            risk_tier="LOW",
        )

        dct = DCTTuple(
            intent_id="intent-1",
            task_id="task-1",
            issuer="governor",
            subject="agent-1",
            ops_allowed=["briefing:generate"],
            event="issued",
        )

        dctx = DCTXTuple(
            intent_id="intent-1",
            task_id="task-1",
            event="issued",
            status="PROPOSED",
            chain_depth=0,
        )

        evidence = EvidenceTuple(
            intent_id="intent-1",
            task_id="task-1",
            event="task_completed",
            duration_s=3.2,
        )

        attest = AttestTuple(
            intent_id="intent-1",
            task_id="task-1",
            event="verified",
            evidence_hash=evidence.hash,
            verifier_id="governor",
            passed=True,
            findings=["all criteria met"],
        )

        # All produce valid schema output
        _validate_against_schema(contract.to_dict(), "contract.schema.json")
        _validate_against_schema(dct.to_dict(), "dct.schema.json")
        _validate_against_schema(dctx.to_dict(), "dctx.schema.json")
        _validate_against_schema(evidence.to_dict(), "evidence.schema.json")
        _validate_against_schema(attest.to_dict(), "attest.schema.json")

        # Attest references evidence hash
        assert attest.evidence_hash == evidence.hash

        # All hashes are unique
        hashes = {contract.hash, dct.hash, dctx.hash, evidence.hash, attest.hash}
        assert len(hashes) == 5


# ---------------------------------------------------------------------------
# MM_APPLIED Experimental Schema Tests
# ---------------------------------------------------------------------------


class TestMMAppliedSchema:
    """Tests for schemas/experimental/mm_applied.schema.json.

    Verifies the conditional invariants codex flagged on PR #16:
    - When operator.mutates=true: invoker.dct_id and wm_state_after are required
    - When operator.mutates=false: wm_state_after must be omitted
    - pattern, format(uuid), and maximum constraints are enforced
    """

    def _mutating_example(self) -> dict:
        return {
            "tuple_type": "MM_APPLIED",
            "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            "time": "2026-04-19T14:30:00Z",
            "tuple_data": {
                "operator": {"code": "RE.04", "family": "RE", "arity": 1, "mutates": True},
                "invoker": {"agent_id": "claude-code", "dct_id": "dct-x", "invocation_depth": 1},
                "wm_state_before": {"version": "wm-v1"},
                "wm_state_after": {"version": "wm-v2"},
                "justification": {"reason": "ten-char reason", "output_summary": "out"},
            },
        }

    def _readonly_example(self) -> dict:
        return {
            "tuple_type": "MM_APPLIED",
            "id": "b2c3d4e5-f6a7-8901-bcde-f23456789012",
            "time": "2026-04-19T15:00:00Z",
            "tuple_data": {
                "operator": {"code": "P.01", "family": "P", "arity": 1, "mutates": False},
                "invoker": {"agent_id": "codex", "invocation_depth": 0},
                "wm_state_before": {"version": "wm-v1"},
                "justification": {"reason": "ten-char reason", "output_summary": "out"},
            },
        }

    def test_mutating_example_validates(self):
        _validate_against_schema(self._mutating_example(), "experimental/mm_applied.schema.json")

    def test_readonly_example_validates(self):
        _validate_against_schema(self._readonly_example(), "experimental/mm_applied.schema.json")

    def test_mutating_without_dct_id_rejected(self):
        """Codex P1: mutates=true must require invoker.dct_id."""
        import pytest

        bad = self._mutating_example()
        del bad["tuple_data"]["invoker"]["dct_id"]
        with pytest.raises(Exception):
            _validate_against_schema(bad, "experimental/mm_applied.schema.json")

    def test_mutating_without_wm_state_after_rejected(self):
        """Codex P2: mutates=true must require tuple_data.wm_state_after."""
        import pytest

        bad = self._mutating_example()
        del bad["tuple_data"]["wm_state_after"]
        with pytest.raises(Exception):
            _validate_against_schema(bad, "experimental/mm_applied.schema.json")

    def test_readonly_with_wm_state_after_rejected(self):
        """Codex P2: mutates=false must omit wm_state_after."""
        import pytest

        bad = self._readonly_example()
        bad["tuple_data"]["wm_state_after"] = {"version": "wm-v2"}
        with pytest.raises(Exception):
            _validate_against_schema(bad, "experimental/mm_applied.schema.json")

    def test_invalid_operator_code_pattern_rejected(self):
        """Validator must enforce pattern: ^(P|IN|CO|DE|RE|SY)\\.[0-9]{2}$."""
        import pytest

        bad = self._mutating_example()
        bad["tuple_data"]["operator"]["code"] = "XX.99"
        with pytest.raises(Exception):
            _validate_against_schema(bad, "experimental/mm_applied.schema.json")

    def test_invalid_uuid_format_rejected(self):
        """Validator must enforce format: uuid on id."""
        import pytest

        bad = self._mutating_example()
        bad["id"] = "not-a-uuid"
        with pytest.raises(Exception):
            _validate_against_schema(bad, "experimental/mm_applied.schema.json")

    def test_confidence_above_maximum_rejected(self):
        """Validator must enforce maximum: 1.0 on confidence."""
        import pytest

        bad = self._mutating_example()
        bad["tuple_data"]["justification"]["confidence"] = 1.5
        with pytest.raises(Exception):
            _validate_against_schema(bad, "experimental/mm_applied.schema.json")

    def test_belonging_score_above_maximum_rejected(self):
        """Validator must enforce maximum: 1.0 on invoker.belonging_score."""
        import pytest

        bad = self._mutating_example()
        bad["tuple_data"]["invoker"]["belonging_score"] = 2.0
        with pytest.raises(Exception):
            _validate_against_schema(bad, "experimental/mm_applied.schema.json")

    def test_alternatives_considered_pattern_enforced(self):
        """Each item in alternatives_considered must match operator code pattern."""
        import pytest

        bad = self._mutating_example()
        bad["tuple_data"]["justification"]["alternatives_considered"] = ["RE.04", "BAD"]
        with pytest.raises(Exception):
            _validate_against_schema(bad, "experimental/mm_applied.schema.json")
