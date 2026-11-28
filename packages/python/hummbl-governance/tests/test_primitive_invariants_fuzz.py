#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Deterministic stdlib-only property & boundary-mutation harness for hummbl-governance CI.

Verifies algebraic invariants across core governance primitives in <2 seconds
with zero third-party dependencies (no Hypothesis required).

Run:
    python -m unittest tests/test_primitive_invariants_fuzz.py -v
"""

from __future__ import annotations

import math
import random
import tempfile
import time
import unittest
from pathlib import Path

from hummbl_governance.attest import ALLOWLIST, CAPABILITY_FENCE, Attest
from hummbl_governance.capability_fence import CapabilityDenied, CapabilityFence
from hummbl_governance.cost_governor import CostGovernor
from hummbl_governance.delegation_context import DelegationContextManager
from hummbl_governance.kernel.receipt_engine import ReceiptEngine
from hummbl_governance.kernel.receipt_integrity_monitor import (
    check_hash_chain,
    check_sequence,
    check_timestamps,
)
from hummbl_governance.kernel.trust_adjuster import TRUST_TIER_ORDER, compute_proposed_tier
from hummbl_governance.lamport_clock import LamportClock, LamportTimestamp
from hummbl_governance.physical_governor import (
    KinematicGovernor,
    PhysicalSafetyMode,
    pHRISafetyMonitor,
)
from hummbl_governance.reward_monitor import _js_divergence, _shannon_entropy

SEED = 20261128


class TestPrimitiveAlgebraicInvariantsFuzz(unittest.TestCase):
    """Stdlib-only property-based & boundary-mutation tests (<2s total runtime)."""

    def setUp(self) -> None:
        self.rng = random.Random(SEED)

    def test_01_lamport_clock_monotonicity_and_exact_max_delta_boundary(self) -> None:
        """K4: LamportClock must be strictly monotonic and enforce exact max_delta boundary."""
        clock = LamportClock(initial=100, agent_id="node-a", max_delta=500)
        # Exact boundary: initial (100) + max_delta (500) = 600 -> must jump to 601 (kills > vs >= mutation)
        self.assertEqual(clock.receive(600), 601)
        # Off-by-one above boundary: 601 + 500 + 1 = 1102 -> must clamp to 602
        self.assertEqual(clock.receive(1102), 602)

        prev = clock.value
        for _ in range(250):
            if self.rng.random() < 0.45:
                curr = clock.tick()
                self.assertEqual(curr, prev + 1)
            else:
                remote = self.rng.randint(0, prev + 1000)
                curr = clock.receive(remote)
                if remote > prev + 500:
                    self.assertEqual(curr, prev + 1)
                else:
                    self.assertEqual(curr, max(prev, remote) + 1)
            self.assertGreater(curr, prev)
            prev = curr

        # Total ordering antisymmetry & irreflexivity
        for _ in range(100):
            t1 = LamportTimestamp(self.rng.randint(0, 50), self.rng.choice(["a", "b", "c"]))
            t2 = LamportTimestamp(self.rng.randint(0, 50), self.rng.choice(["a", "b", "c"]))
            if t1 == t2:
                self.assertIsNone(LamportClock.happened_before(t1, t2))
            else:
                hb12 = LamportClock.happened_before(t1, t2)
                hb21 = LamportClock.happened_before(t2, t1)
                self.assertIsNotNone(hb12)
                self.assertEqual(hb12, not hb21)

    def test_02_cost_governor_monotonic_spend_and_exact_thresholds(self) -> None:
        """K6/P5: CostGovernor spend is additive, rejects NaN/Inf/negative, and hits exact 80%/100% gates."""
        gov = CostGovernor(":memory:", soft_cap=50.0, hard_cap=100.0)
        for bad in (-0.001, float("nan"), float("inf"), float("-inf")):
            with self.assertRaises(ValueError):
                gov.record_usage("p", "m", 10, 10, bad)

        gov.record_usage("p", "m", 1, 1, 39.99)
        self.assertEqual(gov.check_budget_status().decision, "ALLOW")
        gov.record_usage("p", "m", 1, 1, 0.01)  # cumulative 40.00 == 80.0%
        self.assertEqual(gov.check_budget_status().decision, "WARN")
        gov.record_usage("p", "m", 1, 1, 10.00)  # cumulative 50.00 == soft_cap
        self.assertEqual(gov.check_budget_status().decision, "WARN")
        gov.record_usage("p", "m", 1, 1, 50.00)  # cumulative 100.00 == hard_cap
        self.assertEqual(gov.check_budget_status().decision, "DENY")

    def test_03_capability_fence_set_algebra_and_delegation_attenuation(self) -> None:
        """K6/P4/P48: Denied always dominates Allowed; child DelegationContext is always a subset of parent."""
        universe = [f"op:{i}" for i in range(25)]
        for _ in range(100):
            allowed = self.rng.sample(universe, k=self.rng.randint(1, 20))
            denied = self.rng.sample(universe, k=self.rng.randint(0, 12))
            fence = CapabilityFence(allowed=allowed, denied=denied, allow_all_if_empty=False)
            for cap in universe:
                if cap in denied or cap not in allowed:
                    with self.assertRaises(CapabilityDenied):
                        fence.check(cap)
                else:
                    self.assertTrue(fence.check(cap))

        dcm = DelegationContextManager(default_max_depth=5)
        root = dcm.create_trusted_context("root", operations=universe[:10], resources=("repo/*",))
        curr = root
        for depth in range(1, 6):
            sub_ops = self.rng.sample(list(curr.operations), k=max(1, len(curr.operations) - 1))
            child = dcm.delegate(curr.token_id, operations=sub_ops, resources=("repo/sub/*",))
            self.assertEqual(child.depth, depth)
            self.assertTrue(set(child.operations).issubset(set(curr.operations)))
            with self.assertRaises(PermissionError):
                dcm.delegate(child.token_id, operations=["op:999_escalated"])
            curr = child
        with self.assertRaises(PermissionError):
            dcm.delegate(curr.token_id, operations=list(curr.operations))

    def test_04_trust_adjuster_monotone_non_increasing_lattice(self) -> None:
        """K3/P36: compute_proposed_tier is monotonically non-increasing across all (tier, severity) pairs."""
        severities = ["low", "medium", "high", "critical"]
        for idx, tier in enumerate(TRUST_TIER_ORDER):
            prev_prop_idx = idx
            for sev in severities:
                prop = compute_proposed_tier(tier, sev)
                prop_idx = TRUST_TIER_ORDER.index(prop)
                self.assertGreaterEqual(prop_idx, idx)
                self.assertGreaterEqual(prop_idx, prev_prop_idx)
                prev_prop_idx = prop_idx
                if sev == "critical":
                    self.assertEqual(prop, "REVOKED")

    def test_05_reward_monitor_information_theoretic_invariants(self) -> None:
        """D4/P17: JS divergence is symmetric, bounded in [0, 1], and 0 iff P == Q; Shannon entropy >= 0."""
        keys = ["read", "write", "query", "exec", "route", "halt"]
        for _ in range(120):
            w_p = [self.rng.random() + 1e-6 for _ in keys]
            w_q = [self.rng.random() + 1e-6 for _ in keys]
            sp, sq = sum(w_p), sum(w_q)
            p = {k: v / sp for k, v in zip(keys, w_p)}
            q = {k: v / sq for k, v in zip(keys, w_q)}

            js_pq = _js_divergence(p, q)
            js_qp = _js_divergence(q, p)
            js_pp = _js_divergence(p, p)
            ent_p = _shannon_entropy(p)

            self.assertAlmostEqual(js_pq, js_qp, places=12)
            self.assertAlmostEqual(js_pp, 0.0, places=12)
            self.assertGreaterEqual(js_pq, -1e-12)
            self.assertLessEqual(js_pq, 1.0 + 1e-12)
            self.assertGreaterEqual(ent_p, 0.0)
            self.assertLessEqual(ent_p, math.log2(len(keys)) + 1e-9)

    def test_06_receipt_engine_and_integrity_monitor_tamper_detection(self) -> None:
        """K1/K4/K11/P26/P30: Hash-chained receipts pass integrity and any gap/hash mutation fails."""
        from dataclasses import asdict

        class _StubIdentityEngine:
            def resolve(self, agent_id: str) -> dict[str, str]:
                return {"agent_id": agent_id}

        with tempfile.TemporaryDirectory() as tmp:
            engine = ReceiptEngine(
                Path(tmp),
                signing_secret=b"deterministic-ci-secret",
                identity_engine=_StubIdentityEngine(),
            )
            chain = []
            prev_hash = ""
            for i in range(25):
                r = engine.create(
                    agent_id="agent-fuzz",
                    action_type=f"ACT_{i}",
                    payload={"step": i, "nonce": self.rng.randint(1, 100000)},
                    prev_receipt_hash=prev_hash,
                    sequence_id=i,
                )
                engine.store(r)
                curr_hash = r.compute_hash()
                d = asdict(r)
                d["receipt_hash"] = curr_hash
                chain.append(d)
                prev_hash = curr_hash

            seq_ok, gaps = check_sequence(chain)
            hash_ok, broken = check_hash_chain(chain)
            ts_ok, anomalies = check_timestamps(chain)
            self.assertTrue(seq_ok and not gaps)
            self.assertTrue(hash_ok and not broken)
            self.assertTrue(ts_ok and not anomalies)

            idx = self.rng.randint(0, len(chain) - 2)
            mutated = [dict(x) for x in chain]
            mutated[idx]["receipt_hash"] = "0" * 64
            hash_ok_mut, broken_mut = check_hash_chain(mutated)
            self.assertFalse(hash_ok_mut)
            self.assertGreaterEqual(len(broken_mut), 1)

            gapped = chain[:idx] + chain[idx + 1 :]
            seq_ok_gap, gaps_found = check_sequence(gapped)
            self.assertFalse(seq_ok_gap)
            self.assertEqual(gaps_found[0]["missing_count"], 1)

    def test_07_physical_governor_kinematic_and_phri_boundaries(self) -> None:
        """K14/P20: KinematicGovernor enforces exact velocity, force, and jerk limits and scaling."""
        gov = KinematicGovernor(max_velocity=2.0, max_force=40.0, max_jerk=5.0, caution_scale=0.25)
        self.assertTrue(gov.check_motion(velocity=2.0, force=40.0, jerk=5.0)["allowed"])
        self.assertFalse(gov.check_motion(velocity=2.0001)["allowed"])
        self.assertFalse(gov.check_motion(force=40.0001)["allowed"])
        self.assertFalse(gov.check_motion(jerk=5.0001)["allowed"])
        self.assertEqual(gov.get_scaled_velocity(PhysicalSafetyMode.EMERGENCY), 0.0)
        self.assertAlmostEqual(gov.get_scaled_velocity(PhysicalSafetyMode.CAUTION), 0.5)

        mon = pHRISafetyMonitor(min_distance=0.5, critical_distance=0.1)
        self.assertEqual(mon.check_safety(distance=0.1)["mode"], PhysicalSafetyMode.EMERGENCY)
        self.assertEqual(mon.check_safety(distance=0.1001)["mode"], PhysicalSafetyMode.CAUTION)
        self.assertEqual(mon.check_safety(distance=0.5)["mode"], PhysicalSafetyMode.CAUTION)
        self.assertEqual(mon.check_safety(distance=0.5001)["mode"], PhysicalSafetyMode.NORMAL)

    def test_08_attest_policy_set_invariants_and_hash_determinism(self) -> None:
        """K3/P44: Attest ALLOWLIST/CAPABILITY_FENCE set inclusion and hash sensitivity."""
        attest = Attest()
        tools = [f"t_{i}" for i in range(10)]
        for _ in range(50):
            allowed = self.rng.sample(tools, k=self.rng.randint(1, 8))
            declared = self.rng.sample(tools, k=self.rng.randint(1, 8))
            res_allow = attest.verify("srv", ALLOWLIST, allowed_tools=allowed, declared_tools=declared, nonce="n1")
            res_fence = attest.verify("srv", CAPABILITY_FENCE, allowed_tools=allowed, declared_tools=declared, nonce="n1")
            expected_ok = set(declared).issubset(set(allowed))
            self.assertEqual(res_allow.ok, expected_ok)
            self.assertEqual(res_fence.ok, expected_ok)
            res_allow_n2 = attest.verify("srv", ALLOWLIST, allowed_tools=allowed, declared_tools=declared, nonce="n2")
            self.assertNotEqual(res_allow.hash, res_allow_n2.hash)


if __name__ == "__main__":
    t0 = time.perf_counter()
    unittest.main(verbosity=2)
