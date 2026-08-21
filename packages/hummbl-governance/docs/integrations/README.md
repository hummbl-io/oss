# Integrating hummbl-governance with Agent Frameworks

hummbl-governance wraps any agent framework — no framework lock-in, no dependencies.
The pattern is the same whether you're using CrewAI, LangChain, AutoGen, or raw OpenAI API calls.

## The 3-Line Pattern

```python
from hummbl_governance import KillSwitch, CircuitBreaker, CostGovernor

ks = KillSwitch()                              # 1. Emergency stop
cb = CircuitBreaker(failure_threshold=3)       # 2. Auto-fail on errors
gov = CostGovernor(":memory:", soft_cap=5.0)   # 3. Budget enforcement

# Wrap your agent call
result = ks.check_task_allowed("my_task")
if result["allowed"]:
    output = cb.call(my_agent.run)
    gov.record_usage("openai", "gpt-4", 1000, 500, 0.015)
```

That's it. Three primitives, three lines. No framework modification required.

## Runnable examples

Use these files for public, runnable patterns that mirror the snippets below:

- `python examples/crewai_integration.py`
- `python examples/openai_api_integration.py`
- `python examples/langchain_integration.py`
- `python examples/autogen_integration.py`
- `python examples/mcp_integration.py`

All examples include local fallback modes when the optional framework package
is not installed.

## CrewAI

CrewAI gives you tools to build crews. hummbl-governance gives you tools to govern them.

```python
from crewai import Agent, Crew, Task
from hummbl_governance import KillSwitch, CircuitBreaker, CostGovernor

# Your crew — unchanged
researcher = Agent(role="Researcher", goal="Find info", backstory="...")
crew = Crew(agents=[researcher], tasks=[Task(description="...", agent=researcher)])

# Governance wrap
ks = KillSwitch()
cb = CircuitBreaker(failure_threshold=3, recovery_timeout=30.0)
gov = CostGovernor("costs.db", soft_cap=5.0, hard_cap=10.0)

# Run with governance
if ks.check_task_allowed("research")["allowed"]:
    try:
        result = cb.call(crew.kickoff)
        gov.record_usage("openai", "gpt-4", 1000, 500, 0.015)
    except CircuitBreakerOpen:
        ks.engage(KillSwitchMode.HALT_NONCRITICAL,
                  reason="Circuit breaker opened",
                  triggered_by="circuit_breaker")
```

**Solves:**
- [CrewAI #6025](https://github.com/crewAIInc/crewAI/issues/6025) — Runtime release-control mediation layer
- [CrewAI #5888](https://github.com/crewAIInc/crewAI/issues/5888) — Governance middleware hook for tool call authorization

Run the full example: `python examples/crewai_integration.py`

This file provides an optional-framework-safe CrewAI wrapper and a per-tool receipt
path for hook-based mediation.

### CrewAI per-tool hook with transition receipts

Whole-crew wrapping catches run-level failures. For mid-run retry storms and
tool-call drift, attach the same primitives to a CrewAI tool hook and emit a
receipt before the tool is released:

```python
from hummbl_governance import CostGovernor, KillSwitch, build_tool_transition_receipt
from crewai.hooks import (
    register_before_tool_call_hook,
    unregister_before_tool_call_hook,
)

ks = KillSwitch()
gov = CostGovernor("costs.db", soft_cap=5.0, hard_cap=10.0)
receipts = []

def before_tool_call(context):
    tool_name = context.tool_name
    agent_id = getattr(context.agent, "role", None) or "crewai-agent"
    kill_switch_result = ks.check_task_allowed(str(tool_name))
    budget_status = gov.check_budget_status()
    budget_denied = getattr(budget_status, "decision", None) == "DENY"
    receipt = build_tool_transition_receipt(
        agent_id=str(agent_id),
        tool_name=str(tool_name),
        tool_input=context.tool_input,
        context={
            "hook": "before_tool_call",
            "task_description": getattr(context.task, "description", None),
        },
        kill_switch_result=kill_switch_result,
        budget_status=budget_status,
        terminal_outcome=(
            "blocked"
            if not kill_switch_result["allowed"] or budget_denied
            else None
        ),
    )
    receipts.append(receipt)
    return receipt.decision != "HARD_BLOCK"

register_before_tool_call_hook(before_tool_call)
try:
    # Run governed CrewAI calls under this hook.
    if not ks.check_task_allowed("research")["allowed"]:
        raise RuntimeError("Kill switch blocked")
finally:
    unregister_before_tool_call_hook(before_tool_call)
```

The receipt binds `agent_id`, `tool_name`, canonical action hash, context hash,
policy version, kill-switch state, budget state, decision, and terminal outcome
when known. That makes the hook testable: the runtime can later compare the
authorized action hash to the executed action hash instead of relying on a bare
allow/block boolean.

## LangChain

Executable version: `python examples/langchain_integration.py`

```python
from langchain.agents import AgentExecutor
from hummbl_governance import KillSwitch, CircuitBreaker, CostGovernor

executor = AgentExecutor.from_agent_and_tools(agent=agent, tools=tools)

ks = KillSwitch()
cb = CircuitBreaker(failure_threshold=3, recovery_timeout=30.0)
gov = CostGovernor("costs.db", soft_cap=5.0, hard_cap=10.0)

def governed_invoke(input_text):
    if not ks.check_task_allowed("langchain_agent")["allowed"]:
        return {"output": "Blocked by kill switch", "allowed": False}
    try:
        result = cb.call(executor.invoke, {"input": input_text})
        gov.record_usage("openai", "gpt-4", 1000, 500, 0.015)
        return result
    except CircuitBreakerOpen:
        return {"output": "Service temporarily unavailable", "error": "circuit_open"}
```

## AutoGen (Microsoft)

Executable version: `python examples/autogen_integration.py`

```python
from autogen import AssistantAgent, UserProxyAgent
from hummbl_governance import KillSwitch, CircuitBreaker, CostGovernor

assistant = AssistantAgent("assistant", llm_config=llm_config)
user_proxy = UserProxyAgent("user_proxy")

ks = KillSwitch()
cb = CircuitBreaker(failure_threshold=3, recovery_timeout=30.0)
gov = CostGovernor("costs.db", soft_cap=5.0, hard_cap=10.0)

# Wrap the chat initiation
if ks.check_task_allowed("autogen_chat")["allowed"]:
    try:
        cb.call(user_proxy.initiate_chat, assistant, message="Research AI governance")
        gov.record_usage("openai", "gpt-4", 2000, 800, 0.024)
    except CircuitBreakerOpen:
        print("Circuit breaker open — stopping chat")
```

## Raw OpenAI API

Executable version: `python examples/openai_api_integration.py`

```python
import openai
from hummbl_governance import CircuitBreaker, CostGovernor

client = openai.OpenAI()
cb = CircuitBreaker(failure_threshold=3, recovery_timeout=30.0)
gov = CostGovernor("costs.db", soft_cap=5.0, hard_cap=10.0)

def governed_completion(prompt, model="gpt-4"):
    response = cb.call(
        client.chat.completions.create,
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    gov.record_usage("openai", model,
                     response.usage.prompt_tokens,
                     response.usage.completion_tokens,
                     cost=0.015)
    return response
```

## MCP

Executable version: `python examples/mcp_integration.py`

Model Context Protocol tool calls benefit from the same policy shape as agent
framework calls:

```python
from hummbl_governance import KillSwitch, CircuitBreaker, CostGovernor

def guarded_tool(method, params, tool):
    if not KillSwitch().check_task_allowed(f"mcp:{method}")["allowed"]:
        return {"status": "blocked"}

    breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=8.0)
    governor = CostGovernor(":memory:", soft_cap=1.0, hard_cap=2.0)

    result = breaker.call(tool, params)
    governor.record_usage("mcp", method, len(method), len(str(result)), 0.0002)
    return {"status": "ok", "result": result}
```

See `examples/mcp_integration.py` for a runnable mock tool catalog with unknown
method and happy-path handling.

## What You Get

| Primitive | What it does | Why you need it |
|-----------|-------------|-----------------|
| KillSwitch | 4-mode graduated halt | Stop runaway agents without killing the process |
| CircuitBreaker | Auto-fail after N errors | Prevent retry storms burning API credits |
| CostGovernor | Soft/hard budget caps | Block spending before it exceeds your budget |
| AuditLog | Append-only JSONL log | Compliance evidence for SOC2/GDPR/NIST |
| DelegationToken | HMAC-signed scoped tokens | Multi-agent delegation with cryptographic proof |
| AgentRegistry | Identity + trust tiers | Know which agent did what |

## Zero Dependencies

hummbl-governance uses only Python stdlib. It won't conflict with your framework's dependencies. `pip audit` finds nothing because there's nothing to audit.
