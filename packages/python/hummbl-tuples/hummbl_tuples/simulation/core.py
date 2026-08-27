"""Core simulation loop for the governance MVP.

This module is the rule-based scientific instrument described in ADR-003.
Every observable in a trace is deterministic in ``(scenario, seed)``:

* timestamps come from a ``SimulationClock`` seeded by ``scenario.start_timestamp``,
* identifiers come from monotone per-scenario counters,
* iteration order over agents and scheduled actions is stable.

Any stochastic behavior must flow through ``Environment.rng`` (a
``random.Random`` seeded by the caller). Stage 1 is fully deterministic and
only plumbs the RNG so that Stage 2 sensitivity sweeps have a hook.

An ``LLMAdapter`` protocol is defined here but intentionally unused by the
default runner. The rule-based core is the validation surface; LLM-backed
agents are a *wrapper* that must not bypass the enforcement pipeline.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Protocol, runtime_checkable

from .events import (
    contract_event,
    dct_event,
    dctx_event,
    evidence_event,
    system_event,
)
from .trust import ProbationPolicy, TrustModel

# ---------------------------------------------------------------------------
# Scenario configuration types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AgentConfig:
    agent_id: str
    ops_allowed: list[str]


@dataclass(frozen=True)
class ContractConfig:
    task_id: str
    delegatee: str
    objective: str
    allowed_tools: list[str]
    outputs: list[str]
    evidence_requirements: list[str]
    risk_tier: str
    max_subdelegation_depth: int = 1


@dataclass(frozen=True)
class ScheduledAction:
    step: int
    agent_id: str
    op: str
    rationale: str = ""


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    start_timestamp: str
    dt_seconds: float
    contracts: dict[str, ContractConfig]
    actions: list[ScheduledAction]
    metadata: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Mutable per-run agent state
# ---------------------------------------------------------------------------


@dataclass
class AgentState:
    agent_id: str
    task_id: str
    ops_allowed: list[str]
    original_ops: list[str]
    on_probation: bool = False
    clean_streak: int = 0
    current_dct_token_id: str | None = None
    violation_count: int = 0


# ---------------------------------------------------------------------------
# Pluggable agent decision interface (Stage 2 hook)
# ---------------------------------------------------------------------------


@runtime_checkable
class LLMAdapter(Protocol):
    """Protocol for LLM-backed agent policies.

    The default rule-based runner does not call this; it exists so that a
    later iteration can swap a scripted scenario for a generated one without
    touching the enforcement pipeline. Any adapter implementation MUST treat
    denied ops as hard errors rather than retry loops to avoid amplifying
    hallucinated scope violations.
    """

    def propose_action(
        self, agent_state: AgentState, context: dict[str, Any]
    ) -> ScheduledAction: ...


# ---------------------------------------------------------------------------
# Deterministic clock
# ---------------------------------------------------------------------------


class SimulationClock:
    """Monotone clock with per-event microsecond sub-ticks.

    Every call to :meth:`now` returns a distinct ISO-8601 timestamp so that
    co-tick events emitted within one ``step`` are still ordered and hashable
    without collision.
    """

    def __init__(self, start_iso: str, dt_seconds: float) -> None:
        self._start = _parse_iso(start_iso)
        self._dt = timedelta(seconds=dt_seconds)
        self._ticks = 0
        self._sub_tick = 0

    def now(self) -> str:
        moment = self._start + self._ticks * self._dt + timedelta(microseconds=self._sub_tick)
        self._sub_tick += 1
        return moment.strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"

    def advance(self) -> None:
        self._ticks += 1
        self._sub_tick = 0


def _parse_iso(value: str) -> datetime:
    text = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


# ---------------------------------------------------------------------------
# Environment / run loop
# ---------------------------------------------------------------------------


class Environment:
    """Deterministic rule-based governance simulator."""

    def __init__(
        self,
        scenario: Scenario,
        *,
        seed: int = 0,
        trust_model: TrustModel | None = None,
        probation_policy: ProbationPolicy | None = None,
        adapter: LLMAdapter | None = None,
    ) -> None:
        self.scenario = scenario
        self.rng = random.Random(seed)
        self.trust = trust_model or TrustModel()
        self.policy = probation_policy or ProbationPolicy()
        self.adapter = adapter  # reserved for Stage 2
        self.clock = SimulationClock(scenario.start_timestamp, scenario.dt_seconds)
        self.trace: list[dict[str, Any]] = []
        self.agent_states: dict[str, AgentState] = {}
        self._step_index = 0
        self._token_counter = 0
        self._evidence_counter = 0
        self._intent_counter = 0

    # ----- identifier helpers -----

    def _next_token_id(self) -> str:
        self._token_counter += 1
        return f"{self.scenario.scenario_id}-tok-{self._token_counter:04d}"

    def _next_evidence_id(self) -> str:
        self._evidence_counter += 1
        return f"{self.scenario.scenario_id}-ev-{self._evidence_counter:04d}"

    def _next_intent_id(self) -> str:
        self._intent_counter += 1
        return f"{self.scenario.scenario_id}-intent-{self._intent_counter:04d}"

    # ----- lifecycle -----

    def setup(self) -> None:
        """Emit CONTRACT/DCT/DCTX tuples for every configured contract."""
        from .events import reset_id_counter

        reset_id_counter()
        for task_id in sorted(self.scenario.contracts):
            contract = self.scenario.contracts[task_id]
            self._emit_contract_bundle(task_id, contract)
        self.clock.advance()

    def _emit_contract_bundle(self, task_id: str, contract: ContractConfig) -> None:
        self.trace.append(
            contract_event(
                timestamp=self.clock.now(),
                intent_id=self._next_intent_id(),
                task_id=task_id,
                delegatee=contract.delegatee,
                objective=contract.objective,
                allowed_tools=contract.allowed_tools,
                outputs=contract.outputs,
                evidence_requirements=contract.evidence_requirements,
                risk_tier=contract.risk_tier,
                max_subdelegation_depth=contract.max_subdelegation_depth,
                contract_id=task_id,
            )
        )

        self.trust.register(contract.delegatee)
        token_id = self._next_token_id()
        self.agent_states[contract.delegatee] = AgentState(
            agent_id=contract.delegatee,
            task_id=task_id,
            ops_allowed=list(contract.allowed_tools),
            original_ops=list(contract.allowed_tools),
            current_dct_token_id=token_id,
        )

        self.trace.append(
            dct_event(
                timestamp=self.clock.now(),
                intent_id=self._next_intent_id(),
                task_id=task_id,
                issuer="governor",
                subject=contract.delegatee,
                ops_allowed=contract.allowed_tools,
                token_id=token_id,
                event="issued",
            )
        )
        self.trace.append(
            dctx_event(
                timestamp=self.clock.now(),
                intent_id=self._next_intent_id(),
                task_id=task_id,
                event="contract_bound",
                status="ISSUED",
                chain_depth=0,
                adapter="rule_based",
            )
        )

    def step(self) -> None:
        scheduled = [action for action in self.scenario.actions if action.step == self._step_index]
        for action in scheduled:
            self._process_action(action)
        self.clock.advance()
        self._step_index += 1

    def _process_action(self, action: ScheduledAction) -> None:
        agent = self.agent_states.get(action.agent_id)
        if agent is None:
            # Unknown agent: emit a SYSTEM denial rather than raising so the
            # trace remains a complete audit surface.
            self.trace.append(
                system_event(
                    timestamp=self.clock.now(),
                    intent_id=self._next_intent_id(),
                    task_id="unknown",
                    event="unknown_agent_denied",
                    adapter="rule_based",
                    enforcement="denied",
                    error=f"agent {action.agent_id!r} not bound to any contract",
                    required=action.op,
                )
            )
            return

        allowed = action.op in agent.ops_allowed
        if allowed:
            self.trace.append(
                system_event(
                    timestamp=self.clock.now(),
                    intent_id=self._next_intent_id(),
                    task_id=agent.task_id,
                    event="invocation_accepted",
                    adapter="rule_based",
                    enforcement="allowed",
                    required=action.op,
                    ops_allowed=agent.ops_allowed,
                )
            )
            self.trust.reward(agent.agent_id)
            agent.clean_streak += 1
        else:
            agent.violation_count += 1
            self.trace.append(
                system_event(
                    timestamp=self.clock.now(),
                    intent_id=self._next_intent_id(),
                    task_id=agent.task_id,
                    event="scope_violation_denied",
                    adapter="rule_based",
                    enforcement="denied",
                    error=f"op {action.op!r} not in ops_allowed",
                    required=action.op,
                    ops_allowed=agent.ops_allowed,
                )
            )
            self.trust.penalize(agent.agent_id)
            agent.clean_streak = 0

        trust = self.trust.score(agent.agent_id)

        if self.policy.should_enter(trust, agent.on_probation):
            self._enter_probation(agent)
        elif self.policy.should_exit(trust, agent.clean_streak, agent.on_probation):
            self._exit_probation(agent)

    def _enter_probation(self, agent: AgentState) -> None:
        reduced = self.policy.filtered_ops(agent.original_ops)
        agent.ops_allowed = reduced
        agent.on_probation = True
        agent.clean_streak = 0
        new_token = self._next_token_id()
        agent.current_dct_token_id = new_token
        self.trace.append(
            dctx_event(
                timestamp=self.clock.now(),
                intent_id=self._next_intent_id(),
                task_id=agent.task_id,
                event="probation_entered",
                status="PROBATION",
                adapter="rule_based",
            )
        )
        self.trace.append(
            dct_event(
                timestamp=self.clock.now(),
                intent_id=self._next_intent_id(),
                task_id=agent.task_id,
                issuer="governor",
                subject=agent.agent_id,
                ops_allowed=reduced,
                token_id=new_token,
                event="reissued_restricted",
            )
        )

    def _exit_probation(self, agent: AgentState) -> None:
        agent.ops_allowed = list(agent.original_ops)
        agent.on_probation = False
        new_token = self._next_token_id()
        agent.current_dct_token_id = new_token
        self.trace.append(
            dctx_event(
                timestamp=self.clock.now(),
                intent_id=self._next_intent_id(),
                task_id=agent.task_id,
                event="probation_exited",
                status="RESTORED",
                adapter="rule_based",
            )
        )
        self.trace.append(
            dct_event(
                timestamp=self.clock.now(),
                intent_id=self._next_intent_id(),
                task_id=agent.task_id,
                issuer="governor",
                subject=agent.agent_id,
                ops_allowed=agent.original_ops,
                token_id=new_token,
                event="reissued_restored",
            )
        )

    def finalize(self) -> None:
        for agent_id in sorted(self.agent_states):
            agent = self.agent_states[agent_id]
            self.trace.append(
                evidence_event(
                    timestamp=self.clock.now(),
                    intent_id=self._next_intent_id(),
                    task_id=agent.task_id,
                    event="scenario_completed",
                    evidence_id=self._next_evidence_id(),
                    duration_s=float(self._step_index) * self.scenario.dt_seconds,
                    warnings_count=agent.violation_count,
                    agents_ready=(not agent.on_probation),
                    budget_exceeded=False,
                )
            )

    def run(self) -> list[dict[str, Any]]:
        self.setup()
        max_step = max((a.step for a in self.scenario.actions), default=-1)
        while self._step_index <= max_step:
            self.step()
        self.finalize()
        return list(self.trace)


# ---------------------------------------------------------------------------
# Trace summary (Stage 2 sensitivity / UQ hook)
# ---------------------------------------------------------------------------


def trace_summary(trace: list[dict[str, Any]]) -> dict[str, Any]:
    """Extract scalar observables from a trace for downstream analysis.

    This is the interface point for Stage 2 sensitivity analysis and
    uncertainty quantification: any helper that sweeps seeds or perturbs
    parameters should reduce traces through this function so that the
    downstream analysis surface stays stable.
    """
    contracts = sum(1 for e in trace if e["tuple_type"] == "CONTRACT")
    denials = sum(
        1
        for e in trace
        if e["tuple_type"] == "SYSTEM" and e["tuple_data"].get("enforcement") == "denied"
    )
    probation_entries = sum(
        1
        for e in trace
        if e["tuple_type"] == "DCTX" and e["tuple_data"].get("event") == "probation_entered"
    )
    probation_exits = sum(
        1
        for e in trace
        if e["tuple_type"] == "DCTX" and e["tuple_data"].get("event") == "probation_exited"
    )
    evidence_events = [e for e in trace if e["tuple_type"] == "EVIDENCE"]
    return {
        "total_events": len(trace),
        "contracts": contracts,
        "scope_denials": denials,
        "probation_entries": probation_entries,
        "probation_exits": probation_exits,
        "evidence_events": len(evidence_events),
    }
