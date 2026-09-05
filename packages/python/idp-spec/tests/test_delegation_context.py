"""Tests for delegation_context module.

Covers IDP v0.1 DCTX lifecycle:
- Chain depth tracking (I3 invariant)
- State machine transitions
- Subdelegation creation
- Budget tracking
"""

from __future__ import annotations

import os
import unittest

# Ensure ENABLE_IDP for tests
os.environ["ENABLE_IDP"] = "true"

from idp_spec.delegation_context import (
    IDP_E_CAPABILITY_ESCALATION,
    IDP_E_DEPTH_EXCEEDED,
    IDP_E_INVALID_STATE_TRANSITION,
    IDP_E_REPLAN_LIMIT,
    DelegationBudget,
    DelegationContext,
    DelegationContextManager,
    create_child_context,
    create_root_context,
)


class TestDelegationBudget(unittest.TestCase):
    """Test DelegationBudget."""

    def test_default_unlimited(self):
        """Default budget has no limits."""
        budget = DelegationBudget()
        self.assertEqual(budget.max_tokens, 0)
        self.assertEqual(budget.max_cost_usd, 0.0)
        self.assertFalse(budget.is_exceeded(tokens=1000000, cost=10000.0))

    def test_token_limit(self):
        """Token limit enforced."""
        budget = DelegationBudget(max_tokens=100)
        self.assertFalse(budget.is_exceeded(tokens=99))
        self.assertTrue(budget.is_exceeded(tokens=101))

    def test_cost_limit(self):
        """Cost limit enforced."""
        budget = DelegationBudget(max_cost_usd=50.0)
        self.assertFalse(budget.is_exceeded(cost=49.99))
        self.assertTrue(budget.is_exceeded(cost=50.01))

    def test_time_limit(self):
        """Wall time limit enforced."""
        budget = DelegationBudget(max_wall_time_seconds=60)
        self.assertFalse(budget.is_exceeded(seconds=59))
        self.assertTrue(budget.is_exceeded(seconds=61))


class TestDelegationContextCreation(unittest.TestCase):
    """Test DelegationContext creation."""

    def test_root_context(self):
        """Root context has depth 0 and no parent."""
        ctx = DelegationContext(
            intent_id="intent-1",
            task_id="task-1",
            delegator_id="agent-a",
            delegatee_id="agent-b",
            contract_id="contract-1",
            chain_depth=0,
            parent_task_id=None,
        )
        self.assertEqual(ctx.chain_depth, 0)
        self.assertIsNone(ctx.parent_task_id)
        self.assertEqual(ctx.status, "PROPOSED")

    def test_child_context(self):
        """Child context has depth > 0 and parent."""
        ctx = DelegationContext(
            intent_id="intent-1",
            task_id="task-child",
            delegator_id="agent-b",
            delegatee_id="agent-c",
            contract_id="contract-2",
            chain_depth=1,
            parent_task_id="task-parent",
        )
        self.assertEqual(ctx.chain_depth, 1)
        self.assertEqual(ctx.parent_task_id, "task-parent")

    def test_depth_exceeded_raises(self):
        """Depth > 3 raises ValueError when IDP enabled."""
        with self.assertRaises(ValueError) as ctx:
            DelegationContext(
                intent_id="intent-1",
                task_id="task-deep",
                delegator_id="a",
                delegatee_id="b",
                contract_id="c",
                chain_depth=4,  # Exceeds max of 3
            )
        self.assertIn("IDP_E_DEPTH_EXCEEDED", str(ctx.exception))

    def test_parent_depth_consistency(self):
        """Non-root task must have depth > 0."""
        with self.assertRaises(ValueError):
            DelegationContext(
                intent_id="intent-1",
                task_id="task-bad",
                delegator_id="a",
                delegatee_id="b",
                contract_id="c",
                parent_task_id="parent",  # Has parent
                chain_depth=0,  # But depth 0 - invalid
            )

    def test_root_depth_consistency(self):
        """Root task must have depth = 0."""
        with self.assertRaises(ValueError):
            DelegationContext(
                intent_id="intent-1",
                task_id="task-bad",
                delegator_id="a",
                delegatee_id="b",
                contract_id="c",
                parent_task_id=None,  # No parent
                chain_depth=1,  # But depth 1 - invalid
            )

    def test_feature_flag_disabled_allows_any_depth(self):
        """When IDP disabled, any depth allowed."""
        os.environ["ENABLE_IDP"] = "false"
        try:
            ctx = DelegationContext(
                intent_id="intent-1",
                task_id="task-deep",
                delegator_id="a",
                delegatee_id="b",
                contract_id="c",
                chain_depth=10,  # Would normally fail
            )
            self.assertEqual(ctx.chain_depth, 10)
        finally:
            os.environ["ENABLE_IDP"] = "true"


class TestStateMachineTransitions(unittest.TestCase):
    """Test DCTX state machine."""

    def setUp(self):
        self.ctx = DelegationContext(
            intent_id="i1",
            task_id="t1",
            delegator_id="a",
            delegatee_id="b",
            contract_id="c",
        )

    def test_proposed_to_issued(self):
        """PROPOSED → ISSUED is valid."""
        success, error = self.ctx.transition("ISSUED")
        self.assertTrue(success)
        self.assertEqual(self.ctx.status, "ISSUED")

    def test_issued_to_running(self):
        """ISSUED → RUNNING is valid."""
        self.ctx.transition("ISSUED")
        success, error = self.ctx.transition("RUNNING")
        self.assertTrue(success)
        self.assertEqual(self.ctx.status, "RUNNING")

    def test_running_to_evidence(self):
        """RUNNING → EVIDENCE_READY is valid."""
        self.ctx.transition("ISSUED")
        self.ctx.transition("RUNNING")
        success, error = self.ctx.transition("EVIDENCE_READY")
        self.assertTrue(success)
        self.assertEqual(self.ctx.status, "EVIDENCE_READY")

    def test_evidence_to_verified(self):
        """EVIDENCE_READY → VERIFIED is valid."""
        self.ctx.transition("ISSUED")
        self.ctx.transition("RUNNING")
        self.ctx.transition("EVIDENCE_READY")
        success, error = self.ctx.transition("VERIFIED")
        self.assertTrue(success)
        self.assertEqual(self.ctx.status, "VERIFIED")

    def test_evidence_to_replanned(self):
        """EVIDENCE_READY → REPLANNED is valid."""
        self.ctx.transition("ISSUED")
        self.ctx.transition("RUNNING")
        self.ctx.transition("EVIDENCE_READY")
        success, error = self.ctx.transition("REPLANNED")
        self.assertTrue(success)
        self.assertEqual(self.ctx.status, "REPLANNED")
        self.assertEqual(self.ctx.replan_count, 1)

    def test_replanned_to_proposed(self):
        """REPLANNED → PROPOSED is valid."""
        self.ctx.transition("ISSUED")
        self.ctx.transition("RUNNING")
        self.ctx.transition("EVIDENCE_READY")
        self.ctx.transition("REPLANNED")
        success, error = self.ctx.transition("PROPOSED")
        self.assertTrue(success)
        self.assertEqual(self.ctx.status, "PROPOSED")

    def test_replan_limit_enforced(self):
        """I5: More than 2 replans fails."""
        # First replan
        self.ctx.transition("ISSUED")
        self.ctx.transition("RUNNING")
        self.ctx.transition("EVIDENCE_READY")
        self.ctx.transition("REPLANNED")  # replan_count = 1
        self.ctx.transition("PROPOSED")
        self.ctx.transition("ISSUED")
        self.ctx.transition("RUNNING")
        self.ctx.transition("EVIDENCE_READY")
        self.ctx.transition("REPLANNED")  # replan_count = 2
        self.ctx.transition("PROPOSED")
        self.ctx.transition("ISSUED")
        self.ctx.transition("RUNNING")
        self.ctx.transition("EVIDENCE_READY")

        # Third replan should fail
        success, error = self.ctx.transition("REPLANNED")
        self.assertFalse(success)
        self.assertEqual(error, IDP_E_REPLAN_LIMIT)

    def test_invalid_transition(self):
        """Invalid transition returns error."""
        success, error = self.ctx.transition("VERIFIED")  # Can't go PROPOSED → VERIFIED
        self.assertFalse(success)
        self.assertEqual(error, IDP_E_INVALID_STATE_TRANSITION)

    def test_terminal_states(self):
        """VERIFIED and FAILED are terminal."""
        self.ctx.transition("ISSUED")
        self.ctx.transition("RUNNING")
        self.ctx.transition("EVIDENCE_READY")
        self.ctx.transition("VERIFIED")

        success, error = self.ctx.transition("ISSUED")
        self.assertFalse(success)  # Can't leave terminal state

    def test_is_terminal(self):
        """is_terminal() returns True for terminal states."""
        self.assertFalse(self.ctx.is_terminal())
        self.ctx.transition("ISSUED")
        self.ctx.transition("RUNNING")
        self.ctx.transition("EVIDENCE_READY")
        self.ctx.transition("VERIFIED")
        self.assertTrue(self.ctx.is_terminal())

    def test_is_active(self):
        """is_active() returns True for active states."""
        self.assertFalse(self.ctx.is_active())  # PROPOSED not active
        self.ctx.transition("ISSUED")
        self.assertTrue(self.ctx.is_active())


class TestSubdelegation(unittest.TestCase):
    """Test child context creation."""

    def setUp(self):
        self.parent = DelegationContext(
            intent_id="intent-1",
            task_id="task-parent",
            delegator_id="agent-a",
            delegatee_id="agent-b",
            contract_id="contract-1",
            chain_depth=0,
        )

    def test_create_child(self):
        """Child created with incremented depth."""
        child, error = self.parent.create_child(
            delegatee_id="agent-c",
            contract_id="contract-2"
        )
        self.assertIsNotNone(child)
        self.assertEqual(child.chain_depth, 1)
        self.assertEqual(child.parent_task_id, "task-parent")
        self.assertEqual(child.intent_id, "intent-1")  # Same intent
        self.assertEqual(child.delegator_id, "agent-b")  # Parent's delegatee

    def test_child_inherits_budget(self):
        """Child inherits parent budget by default."""
        self.parent.budget = DelegationBudget(max_tokens=100, max_cost_usd=50.0)
        child, _ = self.parent.create_child(
            delegatee_id="agent-c",
            contract_id="contract-2"
        )
        self.assertEqual(child.budget.max_tokens, 100)
        self.assertEqual(child.budget.max_cost_usd, 50.0)

    def test_child_inherits_risk_tier(self):
        """Child inherits parent risk tier by default."""
        self.parent.risk_tier = "HIGH"
        child, _ = self.parent.create_child(
            delegatee_id="agent-c",
            contract_id="contract-2"
        )
        self.assertEqual(child.risk_tier, "HIGH")

    def test_depth_limit_enforced(self):
        """I3: Cannot create child if depth would exceed max."""
        # Create chain at max depth
        depth3 = DelegationContext(
            intent_id="i1",
            task_id="t3",
            delegator_id="a",
            delegatee_id="b",
            contract_id="c",
            chain_depth=3,  # At max
            parent_task_id="parent-task",  # Must have parent since depth > 0
        )
        child, error = depth3.create_child(delegatee_id="d", contract_id="e")
        self.assertIsNone(child)
        self.assertEqual(error, IDP_E_DEPTH_EXCEEDED)

    def test_can_subdelegate(self):
        """can_subdelegate() checks depth limit."""
        self.assertTrue(self.parent.can_subdelegate()[0])

        depth3 = DelegationContext(
            intent_id="i1",
            task_id="t3",
            delegator_id="a",
            delegatee_id="b",
            contract_id="c",
            chain_depth=3,
            parent_task_id="parent-task",  # Must have parent since depth > 0
        )
        can_sub, error = depth3.can_subdelegate()
        self.assertFalse(can_sub)
        self.assertEqual(error, IDP_E_DEPTH_EXCEEDED)


class TestSerialization(unittest.TestCase):
    """Test to_dict/from_dict."""

    def test_round_trip(self):
        """Serialization round-trip preserves data."""
        original = DelegationContext(
            intent_id="intent-1",
            task_id="task-1",
            delegator_id="agent-a",
            delegatee_id="agent-b",
            contract_id="contract-1",
            risk_tier="HIGH",
            chain_depth=1,
            parent_task_id="parent-1",
            budget=DelegationBudget(max_tokens=100, max_cost_usd=50.0),
            status="RUNNING",
            replan_count=1,
            metadata={"key": "value"},
        )

        data = original.to_dict()
        restored = DelegationContext.from_dict(data)

        self.assertEqual(restored.intent_id, original.intent_id)
        self.assertEqual(restored.task_id, original.task_id)
        self.assertEqual(restored.chain_depth, original.chain_depth)
        self.assertEqual(restored.status, original.status)
        self.assertEqual(restored.budget.max_tokens, 100)
        self.assertEqual(restored.metadata["key"], "value")


class TestContextManager(unittest.TestCase):
    """Test DelegationContextManager."""

    def setUp(self):
        self.mgr = DelegationContextManager()

    def test_create_root(self):
        """Manager creates root context."""
        ctx = self.mgr.create_root(
            intent_id="intent-1",
            delegator_id="agent-a",
            delegatee_id="agent-b",
            contract_id="contract-1",
        )
        self.assertEqual(ctx.chain_depth, 0)
        self.assertIn(ctx.task_id, self.mgr._contexts)

    def test_get_context(self):
        """Get context by task ID."""
        ctx = self.mgr.create_root(
            intent_id="intent-1",
            delegator_id="agent-a",
            delegatee_id="agent-b",
            contract_id="contract-1",
        )
        retrieved = self.mgr.get_context(ctx.task_id)
        self.assertEqual(retrieved.task_id, ctx.task_id)

    def test_get_by_intent(self):
        """Get all contexts for intent."""
        self.mgr.create_root("intent-1", "a", "b", "c1")
        self.mgr.create_root("intent-1", "b", "c", "c2")
        self.mgr.create_root("intent-2", "x", "y", "c3")

        intent1_ctxs = self.mgr.get_by_intent("intent-1")
        self.assertEqual(len(intent1_ctxs), 2)

    def test_get_chain(self):
        """Get delegation chain."""
        root = self.mgr.create_root("intent-1", "a", "b", "c1")
        child, _ = root.create_child("c", "c2")
        self.mgr._contexts[child.task_id] = child
        grandchild, _ = child.create_child("d", "c3")
        self.mgr._contexts[grandchild.task_id] = grandchild

        chain = self.mgr.get_chain(grandchild.task_id)
        self.assertEqual(len(chain), 3)
        self.assertEqual(chain[0].task_id, root.task_id)
        self.assertEqual(chain[2].task_id, grandchild.task_id)


class TestConvenienceFunctions(unittest.TestCase):
    """Test module-level convenience functions."""

    def test_create_root_context(self):
        """create_root_context creates root."""
        ctx = create_root_context(
            intent_id="intent-1",
            delegator_id="agent-a",
            delegatee_id="agent-b",
            contract_id="contract-1",
            risk_tier="LOW",
        )
        self.assertEqual(ctx.chain_depth, 0)
        self.assertEqual(ctx.risk_tier, "LOW")

    def test_create_child_context(self):
        """create_child_context creates child."""
        parent = create_root_context("i1", "a", "b", "c1")
        child, error = create_child_context(
            parent=parent,
            delegatee_id="agent-c",
            contract_id="c2"
        )
        self.assertIsNotNone(child)
        self.assertEqual(child.chain_depth, 1)


class TestI2CapabilityAttenuation(unittest.TestCase):
    """Test I2 invariant: monotonic capability attenuation."""

    def _root(self, ops=()):
        return DelegationContext(
            intent_id="i-i2",
            task_id="root-task",
            delegator_id="alice",
            delegatee_id="bob",
            contract_id="c-1",
            chain_depth=0,
            status="RUNNING",
            ops_allowed=ops,
        )

    def test_child_same_ops_allowed(self):
        """Child with same ops as parent should succeed."""
        parent = self._root(ops=("read", "write"))
        child, error = parent.create_child("carol", "c-2", ops_allowed=("read", "write"))
        self.assertIsNotNone(child)
        self.assertIsNone(error)
        self.assertEqual(set(child.ops_allowed), {"read", "write"})

    def test_child_narrower_ops_allowed(self):
        """Child with subset of parent ops should succeed (attenuation)."""
        parent = self._root(ops=("read", "write", "execute"))
        child, error = parent.create_child("carol", "c-2", ops_allowed=("read",))
        self.assertIsNotNone(child)
        self.assertIsNone(error)
        self.assertEqual(child.ops_allowed, ("read",))

    def test_child_escalation_rejected(self):
        """Child with ops not in parent should be rejected (I2 violation)."""
        parent = self._root(ops=("read",))
        child, error = parent.create_child("carol", "c-2", ops_allowed=("read", "write"))
        self.assertIsNone(child)
        self.assertEqual(error, IDP_E_CAPABILITY_ESCALATION)

    def test_child_completely_new_op_rejected(self):
        """Child requesting an op parent doesn't have should fail."""
        parent = self._root(ops=("read", "write"))
        child, error = parent.create_child("carol", "c-2", ops_allowed=("delete",))
        self.assertIsNone(child)
        self.assertEqual(error, IDP_E_CAPABILITY_ESCALATION)

    def test_child_inherits_parent_ops_by_default(self):
        """Child without explicit ops should inherit parent's ops."""
        parent = self._root(ops=("read", "execute"))
        child, error = parent.create_child("carol", "c-2")
        self.assertIsNotNone(child)
        self.assertEqual(set(child.ops_allowed), {"read", "execute"})

    def test_unconstrained_parent_allows_any_child_ops(self):
        """Parent with empty ops (unconstrained) should allow any child ops."""
        parent = self._root(ops=())
        child, error = parent.create_child("carol", "c-2", ops_allowed=("read", "write", "delete"))
        self.assertIsNotNone(child)
        self.assertIsNone(error)

    def test_ops_in_serialization(self):
        """ops_allowed should roundtrip through to_dict/from_dict."""
        ctx = self._root(ops=("read", "write"))
        d = ctx.to_dict()
        self.assertEqual(d["ops_allowed"], ["read", "write"])
        restored = DelegationContext.from_dict(d)
        self.assertEqual(restored.ops_allowed, ("read", "write"))

    def test_backward_compat_no_ops(self):
        """Old contexts without ops_allowed should deserialize with empty tuple."""
        d = {
            "intent_id": "i-1",
            "task_id": "t-1",
            "delegator_id": "a",
            "delegatee_id": "b",
            "contract_id": "c-1",
            "chain_depth": 0,
            "status": "PROPOSED",
        }
        ctx = DelegationContext.from_dict(d)
        self.assertEqual(ctx.ops_allowed, ())


class TestSubtreeBudgetContainment(unittest.TestCase):
    """Test subtree budget attenuation, decrementation, and escalation prevention."""

    def test_child_budget_decrements_parent_remaining(self):
        """Child budget allocation decrements parent remaining capacity."""
        parent = DelegationContext(
            intent_id="i-1",
            task_id="t-1",
            delegator_id="root",
            delegatee_id="agent-a",
            contract_id="c-1",
            chain_depth=0,
            budget=DelegationBudget(max_tokens=1000, max_cost_usd=10.0),
        )
        self.assertEqual(parent.budget.remaining_tokens, 1000)
        self.assertEqual(parent.budget.remaining_cost_usd, 10.0)

        # Allocate child with 400 tokens and $4.0
        child1, error = parent.create_child(
            delegatee_id="agent-b",
            contract_id="c-2",
            budget=DelegationBudget(max_tokens=400, max_cost_usd=4.0),
        )
        self.assertIsNone(error)
        self.assertIsNotNone(child1)
        self.assertEqual(child1.budget.max_tokens, 400)
        self.assertEqual(child1.budget.max_cost_usd, 4.0)
        self.assertEqual(parent.budget.allocated_tokens, 400)
        self.assertEqual(parent.budget.allocated_cost_usd, 4.0)
        self.assertEqual(parent.budget.remaining_tokens, 600)
        self.assertEqual(parent.budget.remaining_cost_usd, 6.0)

    def test_child_budget_escalation_rejected(self):
        """Child requesting more than parent's remaining budget is rejected."""
        from idp_spec.delegation_context import IDP_E_BUDGET_ESCALATION

        parent = DelegationContext(
            intent_id="i-1",
            task_id="t-1",
            delegator_id="root",
            delegatee_id="agent-a",
            contract_id="c-1",
            chain_depth=0,
            budget=DelegationBudget(max_tokens=500, max_cost_usd=5.0),
        )
        # Attempt child with 600 tokens (> 500 remaining)
        child, error = parent.create_child(
            delegatee_id="agent-b",
            contract_id="c-2",
            budget=DelegationBudget(max_tokens=600, max_cost_usd=2.0),
        )
        self.assertIsNone(child)
        self.assertEqual(error, IDP_E_BUDGET_ESCALATION)

    def test_child_unlimited_budget_escalation_rejected(self):
        """Child requesting unlimited (0) budget when parent is bounded is rejected."""
        from idp_spec.delegation_context import IDP_E_BUDGET_ESCALATION

        parent = DelegationContext(
            intent_id="i-1",
            task_id="t-1",
            delegator_id="root",
            delegatee_id="agent-a",
            contract_id="c-1",
            chain_depth=0,
            budget=DelegationBudget(max_tokens=500, max_cost_usd=5.0),
        )
        # Attempt child with max_tokens=0 (unlimited)
        child, error = parent.create_child(
            delegatee_id="agent-b",
            contract_id="c-2",
            budget=DelegationBudget(max_tokens=0, max_cost_usd=2.0),
        )
        self.assertIsNone(child)
        self.assertEqual(error, IDP_E_BUDGET_ESCALATION)

    def test_child_inherits_remaining_budget_by_default(self):
        """Child inherits remaining budget when budget is omitted."""
        parent = DelegationContext(
            intent_id="i-1",
            task_id="t-1",
            delegator_id="root",
            delegatee_id="agent-a",
            contract_id="c-1",
            chain_depth=0,
            budget=DelegationBudget(max_tokens=1000, max_cost_usd=10.0),
        )
        # First child inherits remaining 1000
        child1, error1 = parent.create_child("agent-b", "c-2")
        self.assertIsNone(error1)
        self.assertEqual(child1.budget.max_tokens, 1000)
        self.assertEqual(parent.budget.remaining_tokens, 0)

        # Second child now finds 0 remaining tokens and receives 0 (or cannot exceed)
        child2, error2 = parent.create_child("agent-c", "c-3")
        self.assertIsNone(error2)
        self.assertEqual(child2.budget.max_tokens, 0)

    def test_budget_allocation_serialization_roundtrip(self):
        """allocated_* fields roundtrip through to_dict/from_dict."""
        ctx = DelegationContext(
            intent_id="i-1",
            task_id="t-1",
            delegator_id="a",
            delegatee_id="b",
            contract_id="c-1",
            chain_depth=0,
            budget=DelegationBudget(
                max_tokens=1000,
                max_cost_usd=10.0,
                allocated_tokens=400,
                allocated_cost_usd=4.0,
            ),
        )
        d = ctx.to_dict()
        self.assertEqual(d["budget"]["allocated_tokens"], 400)
        self.assertEqual(d["budget"]["allocated_cost_usd"], 4.0)

        restored = DelegationContext.from_dict(d)
        self.assertEqual(restored.budget.allocated_tokens, 400)
        self.assertEqual(restored.budget.allocated_cost_usd, 4.0)
        self.assertEqual(restored.budget.remaining_tokens, 600)
        self.assertEqual(restored.budget.remaining_cost_usd, 6.0)


if __name__ == "__main__":
    unittest.main()
