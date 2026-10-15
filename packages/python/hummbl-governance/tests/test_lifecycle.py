# Copyright 2024-2026 HUMMBL, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

"""Tests for GovernanceLifecycle."""

import tempfile

from hummbl_governance.audit_log import AuditLog
from hummbl_governance.circuit_breaker import CircuitBreaker, CircuitBreakerState
from hummbl_governance.cost_governor import CostGovernor
from hummbl_governance.identity import AgentRegistry
from hummbl_governance.kill_switch import KillSwitch, KillSwitchMode
from hummbl_governance.lifecycle import GovernanceLifecycle


class TestAuthorize:
    """Authorization check sequence."""

    def setup_method(self):
        self.ks = KillSwitch()
        self.cb = CircuitBreaker(failure_threshold=5)
        self.cg = CostGovernor(db_path=":memory:", soft_cap=100.0, hard_cap=200.0)
        self.reg = AgentRegistry()
        self.reg.register_agent("worker-1", trust="medium", status="active")
        self.reg.register_agent("suspended-agent", trust="low", status="suspended")
        self.reg.register_agent("retired-agent", trust="low", status="retired")

        self.lifecycle = GovernanceLifecycle(
            kill_switch=self.ks,
            circuit_breaker=self.cb,
            cost_governor=self.cg,
            registry=self.reg,
        )

    def test_authorize_allows_normal(self):
        decision = self.lifecycle.authorize("worker-1", "database", "read")
        assert decision.allowed
        assert decision.reason == "authorized"

    def test_authorize_bool(self):
        decision = self.lifecycle.authorize("worker-1", "api", "read")
        assert bool(decision) is True

    def test_kill_switch_emergency_denies(self):
        self.ks.engage(KillSwitchMode.EMERGENCY, reason="test", triggered_by="test")
        decision = self.lifecycle.authorize("worker-1", "db", "read")
        assert not decision.allowed
        assert "EMERGENCY" in decision.reason

    def test_kill_switch_halt_all_denies(self):
        self.ks.engage(KillSwitchMode.HALT_ALL, reason="test", triggered_by="test")
        decision = self.lifecycle.authorize("worker-1", "db", "read")
        assert not decision.allowed
        assert "HALT_ALL" in decision.reason

    def test_kill_switch_halt_noncritical_allows_safety(self):
        self.ks.engage(KillSwitchMode.HALT_NONCRITICAL, reason="test", triggered_by="test")
        decision = self.lifecycle.authorize("worker-1", "db", "audit_logging")
        assert decision.allowed

    def test_kill_switch_halt_noncritical_denies_regular(self):
        self.ks.engage(KillSwitchMode.HALT_NONCRITICAL, reason="test", triggered_by="test")
        decision = self.lifecycle.authorize("worker-1", "db", "write")
        assert not decision.allowed

    def test_suspended_agent_denied(self):
        decision = self.lifecycle.authorize("suspended-agent", "db", "read")
        assert not decision.allowed
        assert decision.reason == "agent:suspended"
        assert decision.checks["agent_status"] == "suspended"
        assert decision.checks["agent_trust"] == "low"
        assert decision.checks["agent_registered"] is True

    def test_retired_agent_denied(self):
        decision = self.lifecycle.authorize("retired-agent", "db", "read")
        assert not decision.allowed
        assert decision.reason == "agent:retired"
        assert decision.checks["agent_registered"] is True

    def test_unknown_agent_denied(self):
        decision = self.lifecycle.authorize("ghost-agent", "db", "read")
        assert not decision.allowed
        assert decision.reason == "agent:unknown"
        assert decision.checks["agent_status"] == "unknown"
        assert decision.checks["agent_trust"] == "unknown"
        assert decision.checks["agent_registered"] is False

    def test_allow_unregistered_agents_opt_in(self):
        lifecycle = GovernanceLifecycle(
            registry=self.reg,
            allow_unregistered_agents=True,
        )
        decision = lifecycle.authorize("ghost-agent", "db", "read")
        assert decision.allowed
        assert decision.reason == "authorized"
        assert decision.checks["agent_registered"] is False
        assert decision.checks["agent_status"] == "unknown"

    def test_authorize_override_allows_unknown(self):
        decision = self.lifecycle.authorize(
            "ghost-agent",
            "db",
            "read",
            allow_unregistered_agents=True,
        )
        assert decision.allowed
        assert decision.checks["agent_registered"] is False

    def test_allow_unregistered_still_denies_suspended(self):
        lifecycle = GovernanceLifecycle(
            registry=self.reg,
            allow_unregistered_agents=True,
        )
        decision = lifecycle.authorize("suspended-agent", "db", "read")
        assert not decision.allowed
        assert decision.reason == "agent:suspended"

    def test_allow_unregistered_still_denies_retired(self):
        lifecycle = GovernanceLifecycle(
            registry=self.reg,
            allow_unregistered_agents=True,
        )
        decision = lifecycle.authorize("retired-agent", "db", "read")
        assert not decision.allowed
        assert decision.reason == "agent:retired"

    def test_circuit_breaker_open_denies(self):
        # Trip the circuit breaker by calling a failing function
        def fail():
            raise RuntimeError("boom")

        for _ in range(5):
            try:
                self.cb.call(fail)
            except Exception:
                pass
        assert self.cb.state == CircuitBreakerState.OPEN
        decision = self.lifecycle.authorize("worker-1", "test-service", "read")
        assert not decision.allowed
        assert "OPEN" in decision.reason

    def test_cost_governor_deny(self):
        # Exhaust the budget
        self.cg.record_usage("openai", "gpt-4", 0, 0, 250.0)
        decision = self.lifecycle.authorize(
            "worker-1",
            "api",
            "query",
            cost=10.0,
        )
        assert not decision.allowed
        assert "DENY" in decision.reason

    def test_checks_populated(self):
        decision = self.lifecycle.authorize("worker-1", "db", "read")
        assert "kill_switch" in decision.checks
        assert decision.checks["agent_status"] == "active"
        assert decision.checks["agent_trust"] == "medium"
        assert decision.checks["agent_registered"] is True
        assert "circuit_breaker" in decision.checks


class TestStatus:
    """Governance status snapshot."""

    def test_status_with_all_modules(self):
        ks = KillSwitch()
        cb = CircuitBreaker()
        cg = CostGovernor(db_path=":memory:", soft_cap=100.0, hard_cap=200.0)
        reg = AgentRegistry()
        reg.register_agent("a1", trust="high")

        lifecycle = GovernanceLifecycle(
            kill_switch=ks,
            circuit_breaker=cb,
            cost_governor=cg,
            registry=reg,
        )
        status = lifecycle.status()
        assert status.kill_switch_mode == "DISENGAGED"
        assert status.circuit_breaker_state == "CLOSED"
        assert status.budget_remaining_pct == 100.0
        assert status.health_ok is True
        assert status.agent_count == 1

    def test_status_to_dict(self):
        lifecycle = GovernanceLifecycle()
        status = lifecycle.status()
        d = status.to_dict()
        assert "govern" in d
        assert "measure" in d
        assert "manage" in d
        assert "timestamp" in d

    def test_status_with_no_modules(self):
        lifecycle = GovernanceLifecycle()
        status = lifecycle.status()
        assert status.kill_switch_mode == "DISENGAGED"
        assert status.health_ok is True


class TestLogDecision:
    """Audit log integration."""

    def test_log_decision_writes_entry(self):
        tmpdir = tempfile.mkdtemp()
        al = AuditLog(base_dir=tmpdir, require_signature=False)
        lifecycle = GovernanceLifecycle(audit_log=al)

        decision = lifecycle.authorize("agent", "db", "write")
        lifecycle.log_decision("agent", "db", "write", decision)

        entries = list(al.query_by_intent("lifecycle"))
        assert len(entries) == 1
        assert entries[0].tuple_data["event"] == "authorization_decision"
        assert entries[0].tuple_data["allowed"] is True
        al.close()

    def test_log_decision_writes_identity_checks(self):
        tmpdir = tempfile.mkdtemp()
        al = AuditLog(base_dir=tmpdir, require_signature=False)
        reg = AgentRegistry()
        reg.register_agent("worker-1", trust="high", status="active")
        lifecycle = GovernanceLifecycle(audit_log=al, registry=reg)

        decision = lifecycle.authorize("worker-1", "db", "write")
        lifecycle.log_decision("worker-1", "db", "write", decision)

        entries = list(al.query_by_intent("lifecycle"))
        assert len(entries) == 1
        checks = entries[0].tuple_data["checks"]
        assert checks["agent_status"] == "active"
        assert checks["agent_trust"] == "high"
        assert checks["agent_registered"] is True
        al.close()

    def test_log_decision_writes_unknown_denial(self):
        tmpdir = tempfile.mkdtemp()
        al = AuditLog(base_dir=tmpdir, require_signature=False)
        lifecycle = GovernanceLifecycle(audit_log=al, registry=AgentRegistry())

        decision = lifecycle.authorize("ghost", "db", "write")
        lifecycle.log_decision("ghost", "db", "write", decision)

        entries = list(al.query_by_intent("lifecycle"))
        assert len(entries) == 1
        assert entries[0].tuple_data["allowed"] is False
        assert entries[0].tuple_data["reason"] == "agent:unknown"
        checks = entries[0].tuple_data["checks"]
        assert checks["agent_status"] == "unknown"
        assert checks["agent_trust"] == "unknown"
        assert checks["agent_registered"] is False
        al.close()

    def test_log_decision_without_audit_log(self):
        """Should silently no-op when audit log is not configured."""
        lifecycle = GovernanceLifecycle()
        decision = lifecycle.authorize("agent", "db", "write")
        lifecycle.log_decision("agent", "db", "write", decision)
        # No error raised


class TestPartialConfiguration:
    """Lifecycle works with subset of modules."""

    def test_only_kill_switch(self):
        ks = KillSwitch()
        lifecycle = GovernanceLifecycle(kill_switch=ks)
        decision = lifecycle.authorize("anyone", "anything", "whatever")
        assert decision.allowed

    def test_only_registry(self):
        reg = AgentRegistry()
        reg.register_agent("ok-agent", status="active")
        lifecycle = GovernanceLifecycle(registry=reg)
        decision = lifecycle.authorize("ok-agent", "x", "read")
        assert decision.allowed

    def test_only_registry_denies_unknown(self):
        lifecycle = GovernanceLifecycle(registry=AgentRegistry())
        decision = lifecycle.authorize("anyone", "x", "read")
        assert not decision.allowed
        assert decision.reason == "agent:unknown"
