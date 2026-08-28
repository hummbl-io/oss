"""Audit goldplate tests — error paths, boundary conditions, and security invariants.

Covers gaps identified during security audit:
- Token from_env_string error paths (empty, non-base64, bad padding)
- Token from_json with malformed JSON
- Token from_dict with missing required fields and wrong types
- depth_bound_lookup with unknown op_class and boundary trust values
- compute_dynamic_depth with out-of-range trust_score, unknown risk_tier
- DelegationBudget with negative and boundary values
- GovernanceBus write failure handling
- GovernanceEntry from_dict with missing required fields
"""

from __future__ import annotations

import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ["ENABLE_IDP"] = "true"

from idp_spec.delegation_token import (
    IDP_E_TOKEN_INVALID,
    Caveat,
    DelegationCapabilityToken,
    DelegationTokenManager,
    ResourceSelector,
    TokenBinding,
    depth_bound_lookup,
)
from idp_spec.delegation_context import (
    DelegationBudget,
    DelegationContext,
    compute_dynamic_depth,
)
from idp_spec.governance_bus import (
    IDP_E_AUDIT_IMMUTABLE,
    GovernanceBus,
    GovernanceEntry,
)


class TestFromEnvStringErrorPaths(unittest.TestCase):
    """Test DelegationCapabilityToken.from_env_string error paths."""

    def test_empty_string_raises(self):
        with self.assertRaises(ValueError) as ctx:
            DelegationCapabilityToken.from_env_string("")
        self.assertIn("Empty", str(ctx.exception))

    def test_non_string_raises(self):
        with self.assertRaises(ValueError):
            DelegationCapabilityToken.from_env_string(None)  # type: ignore[arg-type]

    def test_non_base64_chars_raise(self):
        with self.assertRaises(ValueError) as ctx:
            DelegationCapabilityToken.from_env_string("!!!!notbase64!!!")
        self.assertIn("not in URL-safe alphabet", str(ctx.exception))

    def test_bad_padding_raises(self):
        with self.assertRaises(ValueError):
            DelegationCapabilityToken.from_env_string("abc=def")

    def test_length_not_multiple_of_4_raises(self):
        with self.assertRaises(ValueError) as ctx:
            DelegationCapabilityToken.from_env_string("abc")
        self.assertIn("not a multiple of 4", str(ctx.exception))

    def test_valid_token_roundtrip(self):
        manager = DelegationTokenManager(secret=b"test-secret-32-bytes-long-ok")
        binding = TokenBinding("task-1", "contract-1")
        token = manager.create_token(
            issuer="a", subject="b", ops_allowed=["read"], binding=binding
        )
        env_str = token.to_env_string()
        restored = DelegationCapabilityToken.from_env_string(env_str)
        self.assertEqual(restored.token_id, token.token_id)
        self.assertEqual(restored.issuer, token.issuer)


class TestFromJsonErrorPaths(unittest.TestCase):
    """Test DelegationCapabilityToken.from_json error paths."""

    def test_malformed_json_raises(self):
        with self.assertRaises(ValueError) as ctx:
            DelegationCapabilityToken.from_json("{not valid json")
        self.assertIn("Malformed JSON", str(ctx.exception))

    def test_non_string_raises(self):
        with self.assertRaises(ValueError):
            DelegationCapabilityToken.from_json(123)  # type: ignore[arg-type]

    def test_missing_required_field_raises(self):
        with self.assertRaises(ValueError) as ctx:
            DelegationCapabilityToken.from_json('{"issuer": "a"}')
        self.assertIn("missing required field", str(ctx.exception))

    def test_non_dict_json_raises(self):
        with self.assertRaises(ValueError) as ctx:
            DelegationCapabilityToken.from_json('["not", "a", "dict"]')
        self.assertIn("requires dict", str(ctx.exception))


class TestFromDictErrorPaths(unittest.TestCase):
    """Test DelegationCapabilityToken.from_dict type validation."""

    def test_non_dict_raises(self):
        with self.assertRaises(ValueError) as ctx:
            DelegationCapabilityToken.from_dict("not a dict")  # type: ignore[arg-type]
        self.assertIn("requires dict", str(ctx.exception))

    def test_resource_selectors_not_list_raises(self):
        with self.assertRaises(ValueError) as ctx:
            DelegationCapabilityToken.from_dict({
                "token_id": "t1", "issuer": "a", "subject": "b",
                "resource_selectors": "not a list",
            })
        self.assertIn("resource_selectors must be a list", str(ctx.exception))

    def test_ops_allowed_not_list_raises(self):
        with self.assertRaises(ValueError) as ctx:
            DelegationCapabilityToken.from_dict({
                "token_id": "t1", "issuer": "a", "subject": "b",
                "ops_allowed": "not a list",
            })
        self.assertIn("ops_allowed must be a list", str(ctx.exception))

    def test_caveats_not_list_raises(self):
        with self.assertRaises(ValueError) as ctx:
            DelegationCapabilityToken.from_dict({
                "token_id": "t1", "issuer": "a", "subject": "b",
                "caveats": "not a list",
            })
        self.assertIn("caveats must be a list", str(ctx.exception))


class TestResourceSelectorFromDict(unittest.TestCase):
    """Test ResourceSelector.from_dict error paths."""

    def test_non_dict_raises(self):
        with self.assertRaises(ValueError) as ctx:
            ResourceSelector.from_dict("not a dict")  # type: ignore[arg-type]
        self.assertIn("requires dict", str(ctx.exception))

    def test_missing_resource_type_raises(self):
        with self.assertRaises(ValueError) as ctx:
            ResourceSelector.from_dict({"resource_id": "x"})
        self.assertIn("missing required field", str(ctx.exception))


class TestCaveatFromDict(unittest.TestCase):
    """Test Caveat.from_dict error paths."""

    def test_non_dict_raises(self):
        with self.assertRaises(ValueError) as ctx:
            Caveat.from_dict("not a dict")  # type: ignore[arg-type]
        self.assertIn("requires dict", str(ctx.exception))

    def test_missing_caveat_id_raises(self):
        with self.assertRaises(ValueError) as ctx:
            Caveat.from_dict({"type": "TIME_BOUND"})
        self.assertIn("missing required field", str(ctx.exception))

    def test_missing_type_raises(self):
        with self.assertRaises(ValueError) as ctx:
            Caveat.from_dict({"caveat_id": "c1"})
        self.assertIn("missing required field", str(ctx.exception))


class TestTokenBindingFromDict(unittest.TestCase):
    """Test TokenBinding.from_dict error paths."""

    def test_non_dict_raises(self):
        with self.assertRaises(ValueError) as ctx:
            TokenBinding.from_dict("not a dict")  # type: ignore[arg-type]
        self.assertIn("requires dict", str(ctx.exception))

    def test_missing_task_id_raises(self):
        with self.assertRaises(ValueError) as ctx:
            TokenBinding.from_dict({"contract_id": "c1"})
        self.assertIn("missing required field", str(ctx.exception))

    def test_missing_contract_id_raises(self):
        with self.assertRaises(ValueError) as ctx:
            TokenBinding.from_dict({"task_id": "t1"})
        self.assertIn("missing required field", str(ctx.exception))


class TestDepthBoundLookup(unittest.TestCase):
    """Test depth_bound_lookup boundary conditions."""

    def test_unknown_op_class_returns_zero(self):
        self.assertEqual(depth_bound_lookup("unknown_op", 0.99), 0)

    def test_trust_at_boundary_returns_zero(self):
        # code_edit T_min=0.5, trust exactly 0.5 should return 0 (not >)
        self.assertEqual(depth_bound_lookup("code_edit", 0.5), 0)

    def test_trust_just_above_boundary_returns_bound(self):
        self.assertEqual(depth_bound_lookup("code_edit", 0.51), 4)

    def test_trust_zero_returns_zero(self):
        self.assertEqual(depth_bound_lookup("routine_analysis", 0.0), 0)

    def test_trust_one_returns_bound(self):
        self.assertEqual(depth_bound_lookup("merge_kill_switch", 1.0), 1)

    def test_negative_trust_returns_zero(self):
        self.assertEqual(depth_bound_lookup("code_edit", -0.5), 0)


class TestComputeDynamicDepth(unittest.TestCase):
    """Test compute_dynamic_depth boundary conditions."""

    def test_trust_zero_returns_zero(self):
        self.assertEqual(compute_dynamic_depth(0.0, "LOW"), 0)

    def test_negative_trust_returns_zero(self):
        self.assertEqual(compute_dynamic_depth(-0.5, "LOW"), 0)

    def test_trust_above_one_returns_zero(self):
        self.assertEqual(compute_dynamic_depth(1.5, "LOW"), 0)

    def test_unknown_risk_tier_returns_zero(self):
        # Unknown tier must fail-closed (return 0) rather than defaulting
        # to LOW (most permissive). An unknown risk tier means we don't
        # know the risk level, so we must assume the worst.
        result = compute_dynamic_depth(0.9, "UNKNOWN")
        self.assertEqual(result, 0)

    def test_negative_delta_max_returns_zero(self):
        self.assertEqual(compute_dynamic_depth(1.0, "LOW", delta_max=-1), 0)

    def test_trust_one_at_critical(self):
        # CRITICAL tau=0.40, trust=1.0 → floor(1.0/0.40) = 2
        self.assertEqual(compute_dynamic_depth(1.0, "CRITICAL"), 2)

    def test_trust_just_below_tau_returns_zero(self):
        # LOW tau=0.15, trust=0.14 → floor(0.14/0.15) = 0
        self.assertEqual(compute_dynamic_depth(0.14, "LOW"), 0)


class TestDelegationBudgetBoundaries(unittest.TestCase):
    """Test DelegationBudget boundary conditions."""

    def test_exact_limit_not_exceeded(self):
        budget = DelegationBudget(max_tokens=100)
        self.assertFalse(budget.is_exceeded(tokens=100))

    def test_zero_budget_means_unlimited(self):
        budget = DelegationBudget(max_tokens=0)
        self.assertFalse(budget.is_exceeded(tokens=999999999))

    def test_negative_usage_not_exceeded(self):
        budget = DelegationBudget(max_tokens=100)
        self.assertFalse(budget.is_exceeded(tokens=-1))

    def test_exact_cost_not_exceeded(self):
        budget = DelegationBudget(max_cost_usd=50.0)
        self.assertFalse(budget.is_exceeded(cost=50.0))

    def test_all_limits_combined(self):
        budget = DelegationBudget(max_tokens=100, max_cost_usd=50.0, max_wall_time_seconds=60)
        self.assertFalse(budget.is_exceeded(tokens=50, cost=25.0, seconds=30))
        self.assertTrue(budget.is_exceeded(tokens=101, cost=25.0, seconds=30))
        self.assertTrue(budget.is_exceeded(tokens=50, cost=51.0, seconds=30))
        self.assertTrue(budget.is_exceeded(tokens=50, cost=25.0, seconds=61))


class TestGovernanceBusWriteFailure(unittest.TestCase):
    """Test GovernanceBus write failure handling."""

    def test_append_without_signature_rejected(self):
        with patch.dict(os.environ, {"ENABLE_IDP": "true"}):
            import tempfile
            with tempfile.TemporaryDirectory() as tmp:
                bus = GovernanceBus(base_dir=Path(tmp) / "gov")
                success, error = bus.append(
                    intent_id="i1",
                    task_id="t1",
                    tuple_type="DCT",
                    tuple_data={"data": 1},
                    signature=None,
                )
                self.assertFalse(success)
                self.assertEqual(error, IDP_E_AUDIT_IMMUTABLE)

    def test_append_io_error_returns_audit_incomplete(self):
        with patch.dict(os.environ, {"ENABLE_IDP": "true"}):
            import tempfile
            with tempfile.TemporaryDirectory() as tmp:
                bus = GovernanceBus(base_dir=Path(tmp) / "gov")
                # Force _open_file to raise OSError
                with patch.object(bus, "_open_file", side_effect=OSError("disk full")):
                    success, error = bus.append(
                        intent_id="i1",
                        task_id="t1",
                        tuple_type="DCT",
                        tuple_data={"data": 1},
                        signature="fake-sig",
                    )
                    self.assertFalse(success)
                    self.assertEqual(error, "IDP_E_AUDIT_INCOMPLETE")


class TestGovernanceEntryFromDictMissingFields(unittest.TestCase):
    """Test GovernanceEntry.from_dict with missing required fields."""

    def test_missing_timestamp_raises(self):
        with self.assertRaises(KeyError):
            GovernanceEntry.from_dict({
                "entry_id": "e1", "intent_id": "i1", "task_id": "t1",
                "tuple_type": "DCT", "tuple_data": {},
            })

    def test_missing_entry_id_raises(self):
        with self.assertRaises(KeyError):
            GovernanceEntry.from_dict({
                "timestamp": "2026-01-01T00:00:00Z",
                "intent_id": "i1", "task_id": "t1",
                "tuple_type": "DCT", "tuple_data": {},
            })


class TestValidateEnvTokenErrorPaths(unittest.TestCase):
    """Test DelegationTokenManager.validate_env_token error paths."""

    def setUp(self):
        self.manager = DelegationTokenManager(secret=b"test-secret-32-bytes-long-ok")
        self.binding = TokenBinding("task-1", "contract-1")

    def test_malformed_env_string_returns_invalid(self):
        is_valid, error, token = self.manager.validate_env_token("!!!notbase64!!!")
        self.assertFalse(is_valid)
        self.assertEqual(error, IDP_E_TOKEN_INVALID)
        self.assertIsNone(token)

    def test_empty_env_string_returns_invalid(self):
        is_valid, error, token = self.manager.validate_env_token("")
        self.assertFalse(is_valid)
        self.assertEqual(error, IDP_E_TOKEN_INVALID)
        self.assertIsNone(token)

    def test_valid_env_token_returns_token(self):
        token = self.manager.create_token(
            issuer="a", subject="b", ops_allowed=["read"], binding=self.binding
        )
        env_str = token.to_env_string()
        is_valid, error, parsed = self.manager.validate_env_token(env_str)
        self.assertTrue(is_valid)
        self.assertIsNone(error)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.token_id, token.token_id)


class TestDelegationContextFromDictMissingFields(unittest.TestCase):
    """Test DelegationContext.from_dict with missing required fields."""

    def test_missing_intent_id_raises(self):
        with self.assertRaises(KeyError):
            DelegationContext.from_dict({
                "task_id": "t1", "delegator_id": "a", "delegatee_id": "b",
                "contract_id": "c",
            })

    def test_missing_task_id_raises(self):
        with self.assertRaises(KeyError):
            DelegationContext.from_dict({
                "intent_id": "i1", "delegator_id": "a", "delegatee_id": "b",
                "contract_id": "c",
            })


class TestTokenSerializationRoundtrip(unittest.TestCase):
    """Test full token serialization roundtrip via env string."""

    def test_full_roundtrip_preserves_all_fields(self):
        manager = DelegationTokenManager(secret=b"test-secret-32-bytes-long-ok")
        binding = TokenBinding("task-rt", "contract-rt")
        rs = ResourceSelector("file", "/tmp/*", {"read_only": True})
        caveat = Caveat("cav-1", "TIME_BOUND", {"max_duration": 3600})
        token = manager.create_token(
            issuer="agent-a",
            subject="agent-b",
            ops_allowed=["read", "write"],
            binding=binding,
            resource_selectors=[rs],
            caveats=[caveat],
            expiry_minutes=60,
        )
        env_str = token.to_env_string()
        restored = DelegationCapabilityToken.from_env_string(env_str)
        self.assertEqual(restored.token_id, token.token_id)
        self.assertEqual(restored.issuer, token.issuer)
        self.assertEqual(restored.subject, token.subject)
        self.assertEqual(restored.ops_allowed, token.ops_allowed)
        self.assertEqual(len(restored.resource_selectors), 1)
        self.assertEqual(restored.resource_selectors[0].resource_type, "file")
        self.assertEqual(len(restored.caveats), 1)
        self.assertEqual(restored.caveats[0].caveat_id, "cav-1")
        self.assertEqual(restored.binding.task_id, "task-rt")
        self.assertEqual(restored.signature, token.signature)
        # Signature should still verify
        self.assertTrue(restored.verify_signature(b"test-secret-32-bytes-long-ok"))


if __name__ == "__main__":
    unittest.main()
