#!/usr/bin/env python3
"""Integration example: wrapping CrewAI with hummbl-governance.

CrewAI gives you tools to BUILD agents. hummbl-governance gives you tools
to GOVERN them. This example shows the 3-line integration pattern that
adds kill switch, circuit breaker, and cost governance to any CrewAI crew.

Related CrewAI issues this solves:
- https://github.com/crewAIInc/crewAI/issues/6025 (runtime control)
- https://github.com/crewAIInc/crewAI/issues/5888 (governance middleware)

Usage:
    # With CrewAI installed:
    pip install crewai hummbl-governance
    python examples/crewai_integration.py

    # Without CrewAI (demo mode uses a mock):
    python examples/crewai_integration.py
"""

import tempfile
from pathlib import Path
from typing import Any

from hummbl_governance import (
    CircuitBreaker,
    CostGovernor,
    KillSwitch,
    KillSwitchMode,
    AuditLog,
    ToolCallAuditor,
    build_tool_transition_receipt,
)
from hummbl_governance.capability_fence import CapabilityFence
from hummbl_governance.circuit_breaker import CircuitBreakerOpen


def run_with_crewai():
    """Real CrewAI integration — requires `pip install crewai`."""
    from crewai import Agent, Crew, Task
    from crewai.hooks import register_before_tool_call_hook, unregister_before_tool_call_hook

    # 1. Define your crew as usual
    researcher = Agent(
        role="Researcher",
        goal="Find information",
        backstory="A diligent researcher",
        tools=[],  # add your tools here
    )

    task = Task(
        description="Research a topic",
        expected_output="A summary",
        agent=researcher,
    )

    crew = Crew(agents=[researcher], tasks=[task])

    # 2. Wrap with hummbl-governance (3 lines)
    ks = KillSwitch()
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=30.0)
    gov = CostGovernor(str(Path(tempfile.mkdtemp()) / "costs.db"),
                       soft_cap=5.0, hard_cap=10.0)
    receipts = []
    hook = make_before_tool_call_guard(ks, gov, receipts)
    register_before_tool_call_hook(hook)

    # 3. Run with governance
    try:
        result = ks.check_task_allowed("research")
        if not result["allowed"]:
            print(f"Blocked by kill switch: {ks.mode.name}")
            return

        try:
            output = cb.call(crew.kickoff)
            gov.record_usage("openai", "gpt-4", 1000, 500, 0.015)
            print(f"Result: {output}")
        except CircuitBreakerOpen:
            print("Circuit breaker open — too many failures, fast-failing")
            ks.engage(KillSwitchMode.HALT_NONCRITICAL,
                      reason="Circuit breaker opened",
                      triggered_by="circuit_breaker")
        except Exception as e:
            print(f"Error: {e}")
    finally:
        unregister_before_tool_call_hook(hook)


def make_before_tool_call_guard(ks, gov, receipts):
    """Build a CrewAI ToolCallHookContext guard.

    The returned function is suitable for register_before_tool_call_hook().
    It records a transition receipt before the tool is released. Return False
    when CrewAI should block the tool call. The caller-owned receipts list is
    for short-lived examples; production agents should rotate or persist it.
    """

    def before_tool_call(context: Any):
        tool_name = getattr(context, "tool_name", None) or str(getattr(context, "tool", "unknown_tool"))
        agent = getattr(context, "agent", None)
        task = getattr(context, "task", None)
        crew = getattr(context, "crew", None)
        agent_id = getattr(agent, "role", None) or getattr(agent, "id", None) or "crewai-agent"
        payload = getattr(context, "tool_input", None)
        if payload is None:
            payload = {}
        kill_switch_result = ks.check_task_allowed(str(tool_name))
        budget_status = gov.check_budget_status()
        terminal_outcome = "blocked" if (
            not kill_switch_result["allowed"] or _budget_denied(budget_status)
        ) else None
        receipt = build_tool_transition_receipt(
            agent_id=str(agent_id),
            tool_name=str(tool_name),
            tool_input=payload,
            context={
                "agent_role": getattr(agent, "role", None),
                "task_description": getattr(task, "description", None),
                "crew_id": getattr(crew, "id", None),
            },
            kill_switch_result=kill_switch_result,
            budget_status=budget_status,
            terminal_outcome=terminal_outcome,
        )
        receipts.append(receipt)
        return receipt.decision != "HARD_BLOCK"

    return before_tool_call


def _budget_denied(budget_status: Any) -> bool:
    if isinstance(budget_status, dict):
        return budget_status.get("decision") == "DENY"
    return getattr(budget_status, "decision", None) == "DENY"


def run_demo_mode():
    """Demo without CrewAI — shows the same pattern with a mock."""
    print("Running in demo mode (CrewAI not installed)")
    print("Install with: pip install crewai\n")

    # Mock crew.kickoff()
    def mock_kickoff():
        print("  Crew: executing tasks...")
        return "Research complete: AI governance is important"

    # Same 3-line governance wrap
    ks = KillSwitch()
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=30.0)
    gov = CostGovernor(":memory:", soft_cap=5.0, hard_cap=10.0)
    audit = AuditLog(
        str(Path(tempfile.mkdtemp()) / "audit"),
        require_signature=False,
    )
    tool_audit = ToolCallAuditor(
        audit_log=audit,
        intent_id="crewai-demo-intent",
        task_id="research-task",
        capability_fence=CapabilityFence(allowed=["tool:search"]),
    )

    # Simulate a successful run
    print("=== Run 1: Normal operation ===")
    result = ks.check_task_allowed("research")
    print(f"  Kill switch: {result['allowed']} ({ks.mode.name})")

    def mock_search(query):
        return {"query": query, "rows": 3}

    safe_search = tool_audit.wrap("search", mock_search)
    print(f"  Audited tool call: {safe_search('agent governance audit')}")

    def blocked_tool():
        raise RuntimeError("This tool must never be reachable")

    try:
        blocked = tool_audit.wrap("secret", blocked_tool, capability="tool:blocked")
        blocked()
    except Exception:
        print("  Expected block: tool capability denied")

    output = cb.call(mock_kickoff)
    gov.record_usage("openai", "gpt-4", 1000, 500, 0.015)
    status = gov.check_budget_status()
    print(f"  Cost: ${status.current_spend:.3f} / ${status.hard_cap} (decision: {status.decision})")
    print(f"  Result: {output}")

    # Simulate failures triggering circuit breaker
    print("\n=== Run 2: Cascading failures ===")
    def failing_kickoff():
        raise ConnectionError("LLM API unavailable")

    for i in range(4):
        try:
            cb.call(failing_kickoff)
        except ConnectionError:
            print(f"  Attempt {i+1}: ConnectionError (breaker: {cb.state.name})")
        except CircuitBreakerOpen:
            print(f"  Attempt {i+1}: CircuitBreakerOpen — fast-fail (breaker: {cb.state.name})")
            break

    # Kill switch engages automatically
    ks.engage(KillSwitchMode.HALT_NONCRITICAL,
              reason="Circuit breaker opened",
              triggered_by="circuit_breaker")
    print(f"\n  Kill switch engaged: {ks.mode.name}")

    # Subsequent runs are blocked
    print("\n=== Run 3: Blocked by kill switch ===")
    result = ks.check_task_allowed("research")
    print(f"  Kill switch: allowed={result['allowed']} ({ks.mode.name})")
    if not result["allowed"]:
        print(f"  Blocked: {result['reason']}")

    # Audit trail
    print("\n=== Audit trail ===")
    audit_entries = list(audit.query_by_intent("crewai-demo-intent", tuple_type="SYSTEM"))
    print(f"  Tool-call audit entries: {len(audit_entries)}")
    if audit_entries:
        print(f"  Last tool event: {audit_entries[0].tuple_data}")
    print(f"  Kill switch mode: {ks.mode.name}")
    print(f"  Circuit breaker state: {cb.state.name}")
    status = gov.check_budget_status()
    print(f"  Cost: ${status.current_spend:.3f} (decision: {status.decision})")
    print(f"  Total failures: {cb.failure_count}, successes: {cb.success_count}")

    # Simulate CrewAI per-tool hook governance without requiring CrewAI.
    print("\n=== Per-tool transition receipt ===")
    receipts = []
    class DemoToolContext:
        tool_name = "web_search"
        tool_input = {"query": "CrewAI governance"}
        agent = None
        task = None
        crew = None

    guard = make_before_tool_call_guard(ks, gov, receipts)
    allowed = guard(DemoToolContext())
    receipt = receipts[-1]
    print(f"  Tool allowed: {allowed}")
    print(f"  Receipt decision: {receipt.decision}")
    print(f"  Action hash: {receipt.action_hash}")


if __name__ == "__main__":
    try:
        import crewai  # noqa: F401
        run_with_crewai()
    except ImportError:
        run_demo_mode()
