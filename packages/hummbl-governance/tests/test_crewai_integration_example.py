from types import SimpleNamespace

from examples.crewai_integration import make_before_tool_call_guard
from hummbl_governance import CostGovernor, KillSwitch, KillSwitchMode


def test_before_tool_call_guard_reads_crewai_context():
    receipts = []
    guard = make_before_tool_call_guard(KillSwitch(), CostGovernor(":memory:"), receipts)
    context = SimpleNamespace(
        tool_name="web_search",
        tool_input={"query": "CrewAI governance"},
        agent=SimpleNamespace(role="Researcher"),
        task=SimpleNamespace(description="Research a topic"),
        crew=SimpleNamespace(id="crew-1"),
    )

    assert guard(context) is True
    receipt = receipts[-1]
    assert receipt.tool_name == "web_search"
    assert receipt.agent_id == "Researcher"
    assert receipt.decision == "ALLOW"


def test_before_tool_call_guard_blocks_when_kill_switch_blocks():
    ks = KillSwitch()
    ks.engage(KillSwitchMode.HALT_ALL, reason="operator halt", triggered_by="test")
    receipts = []
    guard = make_before_tool_call_guard(ks, CostGovernor(":memory:"), receipts)
    context = SimpleNamespace(
        tool_name="web_search",
        tool_input={"query": "CrewAI governance"},
        agent=SimpleNamespace(role="Researcher"),
        task=None,
        crew=None,
    )

    assert guard(context) is False
    assert receipts[-1].decision == "HARD_BLOCK"
    assert receipts[-1].terminal_outcome == "blocked"


def test_before_tool_call_guard_marks_budget_denial_blocked():
    gov = CostGovernor(":memory:", soft_cap=1.0, hard_cap=2.0)
    gov.record_usage("openai", "gpt-4", 100, 50, 3.0)
    receipts = []
    guard = make_before_tool_call_guard(KillSwitch(), gov, receipts)
    context = SimpleNamespace(
        tool_name="expensive_llm_tool",
        tool_input={"prompt": "continue"},
        agent=SimpleNamespace(role="Researcher"),
        task=None,
        crew=None,
    )

    assert guard(context) is False
    assert receipts[-1].decision == "HARD_BLOCK"
    assert receipts[-1].terminal_outcome == "blocked"
