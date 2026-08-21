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

"""Governance Lifecycle -- NIST AI RMF orchestrator composing existing modules.

Thin orchestration layer that wires KillSwitch, CircuitBreaker, CostGovernor,
DelegationTokenManager, AuditLog, AgentRegistry, and HealthCollector into
the four NIST AI Risk Management Framework functions:

- **Govern**: KillSwitch + AgentRegistry (authority, identity, trust)
- **Map**: AgentRegistry + StrideMapper (risk identification, threat surface)
- **Measure**: CostGovernor + HealthCollector (quantitative risk metrics)
- **Manage**: CircuitBreaker + DelegationTokenManager + AuditLog (response, delegation, audit)

This is the GaaS headline integration -- it shows how standalone primitives
compose into a complete governance lifecycle.

Usage::

    from hummbl_governance.lifecycle import GovernanceLifecycle

    lifecycle = GovernanceLifecycle(
        kill_switch=ks,
        circuit_breaker=cb,
        cost_governor=cg,
        delegation_manager=dm,
        audit_log=al,
        registry=reg,
        health_collector=hc,
    )

    # Check if an agent action is permitted
    decision = lifecycle.authorize("worker-1", "database", "write")

    # Get a full governance status snapshot
    status = lifecycle.status()

Stdlib-only.

Reference:
    Tabassi, E. (2023). AI Risk Management Framework (AI RMF 1.0).
    NIST AI 100-1. DOI: 10.6028/NIST.AI.100-1
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from hummbl_governance.audit_log import AuditLog
from hummbl_governance.circuit_breaker import CircuitBreaker, CircuitBreakerState
from hummbl_governance.cost_governor import CostGovernor
from hummbl_governance.delegation import DelegationTokenManager
from hummbl_governance.health_probe import HealthCollector
from hummbl_governance.identity import AgentRegistry
from hummbl_governance.kill_switch import KillSwitch, KillSwitchMode


class AuthorizationDecision:
    """Result of a governance authorization check."""

    __slots__ = ("allowed", "reason", "checks")

    def __init__(
        self,
        allowed: bool,
        reason: str,
        checks: dict[str, Any] | None = None,
    ) -> None:
        self.allowed = allowed
        self.reason = reason
        self.checks = checks or {}

    def __bool__(self) -> bool:
        return self.allowed

    def __repr__(self) -> str:
        return f"AuthorizationDecision(allowed={self.allowed}, reason={self.reason!r})"


@dataclass
class GovernanceStatus:
    """Snapshot of the full governance lifecycle state."""

    timestamp: str
    kill_switch_mode: str
    circuit_breaker_state: str
    budget_remaining_pct: float
    health_ok: bool
    agent_count: int
    checks: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "timestamp": self.timestamp,
            "govern": {
                "kill_switch_mode": self.kill_switch_mode,
                "agent_count": self.agent_count,
            },
            "measure": {
                "budget_remaining_pct": self.budget_remaining_pct,
                "health_ok": self.health_ok,
            },
            "manage": {
                "circuit_breaker_state": self.circuit_breaker_state,
            },
            "checks": self.checks,
        }


class GovernanceLifecycle:
    """Orchestrates governance primitives into the NIST AI RMF lifecycle.

    Composes existing hummbl-governance modules into a single authorization
    and status interface. Each method maps to one or more NIST functions
    (Govern, Map, Measure, Manage).

    All parameters are optional. Provide only the modules you have wired up.
    Missing modules are gracefully skipped in authorization checks and status.
    """

    def __init__(
        self,
        kill_switch: KillSwitch | None = None,
        circuit_breaker: CircuitBreaker | None = None,
        cost_governor: CostGovernor | None = None,
        delegation_manager: DelegationTokenManager | None = None,
        audit_log: AuditLog | None = None,
        registry: AgentRegistry | None = None,
        health_collector: HealthCollector | None = None,
    ) -> None:
        self._ks = kill_switch
        self._cb = circuit_breaker
        self._cg = cost_governor
        self._dm = delegation_manager
        self._al = audit_log
        self._reg = registry
        self._hc = health_collector

    def _check_kill_switch(self, action, checks):
        """Check kill switch mode. Returns denial or None."""
        if self._ks is None:
            return None
        mode = self._ks.mode
        checks["kill_switch"] = mode.name
        if mode == KillSwitchMode.EMERGENCY:
            return AuthorizationDecision(False, "kill_switch:EMERGENCY", checks)
        if mode == KillSwitchMode.HALT_ALL:
            return AuthorizationDecision(False, "kill_switch:HALT_ALL", checks)
        _CRITICAL_ACTIONS = (
            "safety_monitoring", "data_persistence", "audit_logging",
            "cost_tracking", "kill_switch_itself",
        )
        if mode == KillSwitchMode.HALT_NONCRITICAL and action not in _CRITICAL_ACTIONS:
            return AuthorizationDecision(False, "kill_switch:HALT_NONCRITICAL", checks)
        return None

    def _check_agent_identity(self, agent, checks):
        """Check agent identity. Returns denial or None."""
        if self._reg is None:
            return None
        status = self._reg.get_status(agent)
        trust = self._reg.get_trust_tier(agent)
        checks["agent_status"] = status
        checks["agent_trust"] = trust
        if status in ("suspended", "retired"):
            return AuthorizationDecision(False, f"agent:{status}", checks)
        return None

    def _check_circuit_breaker(self, checks):
        """Check circuit breaker state. Returns denial or None."""
        if self._cb is None:
            return None
        cb_state = self._cb.state
        checks["circuit_breaker"] = cb_state.name
        if cb_state == CircuitBreakerState.OPEN:
            return AuthorizationDecision(False, "circuit_breaker:OPEN", checks)
        return None

    def _check_cost_governor(self, cost, checks):
        """Check cost governor budget. Returns denial or None."""
        if self._cg is None or cost <= 0:
            return None
        budget = self._cg.check_budget_status()
        checks["budget_decision"] = budget.decision
        checks["budget_spent"] = budget.current_spend
        if budget.decision == "DENY":
            return AuthorizationDecision(False, "cost_governor:DENY", checks)
        return None

    def authorize(
        self,
        agent: str,
        target: str,
        action: str,
        *,
        cost: float = 0.0,
        provider: str = "",
        model: str = "",
    ) -> AuthorizationDecision:
        """Run the full governance check sequence for an agent action.

        Checks (in order, short-circuits on first denial):
        1. **Govern**: Kill switch mode (is the system halted?)
        2. **Govern**: Agent identity (is the agent known and active?)
        3. **Manage**: Circuit breaker (is the target service healthy?)
        4. **Measure**: Cost governor (is there budget remaining?)

        Args:
            agent: The agent requesting authorization.
            target: The resource or service being accessed.
            action: The action being performed (read, write, execute, etc.).
            cost: Estimated cost of the action (for budget check).
            provider: API provider name (for cost tracking).
            model: Model name (for cost tracking).

        Returns:
            AuthorizationDecision with allowed/denied and reason.
        """
        checks: dict[str, Any] = {}

        for check_fn in [
            lambda: self._check_kill_switch(action, checks),
            lambda: self._check_agent_identity(agent, checks),
            lambda: self._check_circuit_breaker(checks),
            lambda: self._check_cost_governor(cost, checks),
        ]:
            denial = check_fn()
            if denial is not None:
                return denial

        return AuthorizationDecision(True, "authorized", checks)

    def status(self) -> GovernanceStatus:
        """Get a full governance lifecycle status snapshot.

        Maps to all four NIST functions:
        - Govern: kill switch mode, agent count
        - Map: (call stride_mapper separately for threat analysis)
        - Measure: budget remaining, health status
        - Manage: circuit breaker state
        """
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        checks: dict[str, Any] = {}

        # Govern
        ks_mode = "DISENGAGED"
        if self._ks is not None:
            ks_mode = self._ks.mode.name
            checks["kill_switch_history_len"] = len(self._ks.get_history())

        agent_count = 0
        if self._reg is not None:
            agents = self._reg.get_agents()
            agent_count = len(agents)
            active = sum(1 for a in agents.values() if a.get("status") == "active")
            checks["agents_active"] = active

        # Measure
        budget_pct = 100.0
        if self._cg is not None:
            budget = self._cg.check_budget_status()
            if budget.hard_cap and budget.hard_cap > 0:
                remaining = budget.hard_cap - budget.current_spend
                budget_pct = round((remaining / budget.hard_cap) * 100, 1)
            elif budget.soft_cap > 0:
                remaining = budget.soft_cap - budget.current_spend
                budget_pct = round((remaining / budget.soft_cap) * 100, 1)
            checks["budget_decision"] = budget.decision
            checks["budget_spent"] = budget.current_spend

        health_ok = True
        if self._hc is not None:
            report = self._hc.check_all()
            health_ok = report.overall_healthy
            checks["health_probes"] = len(report.probes)
            checks["health_duration_ms"] = report.duration_ms

        # Manage
        cb_state = "CLOSED"
        if self._cb is not None:
            cb_state = self._cb.state.name
            checks["circuit_breaker_failure_count"] = self._cb.failure_count

        return GovernanceStatus(
            timestamp=now,
            kill_switch_mode=ks_mode,
            circuit_breaker_state=cb_state,
            budget_remaining_pct=budget_pct,
            health_ok=health_ok,
            agent_count=agent_count,
            checks=checks,
        )

    def log_decision(
        self,
        agent: str,
        target: str,
        action: str,
        decision: AuthorizationDecision,
        intent_id: str = "",
        task_id: str = "",
    ) -> None:
        """Record an authorization decision in the audit log.

        Args:
            agent: The agent that was checked.
            target: The resource/service targeted.
            action: The action attempted.
            decision: The authorization decision.
            intent_id: Root intent identifier.
            task_id: Task identifier.
        """
        if self._al is None:
            return

        self._al.append(
            intent_id=intent_id or "lifecycle",
            task_id=task_id or "authorization",
            tuple_type="SYSTEM",
            tuple_data={
                "event": "authorization_decision",
                "agent": agent,
                "target": target,
                "action": action,
                "allowed": decision.allowed,
                "reason": decision.reason,
                "checks": decision.checks,
            },
            require_signature=False,
        )
