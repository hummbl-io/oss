#!/usr/bin/env python3
"""Example: governed MCP-style tool-call adapter.

This keeps no hard dependency on the MCP SDK. It demonstrates the core
policy shape: evaluate the tool call before execution, then record/consume
governance decisions from kill switch, circuit breaker, and cost governor.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict

from hummbl_governance import CircuitBreaker, CostGovernor, KillSwitch
from hummbl_governance.circuit_breaker import CircuitBreakerOpen


Decision = Dict[str, Any]


@dataclass(frozen=True)
class MockMCPRequest:
    method: str
    params: Dict[str, Any]


def guarded_tool_dispatch(
    request: MockMCPRequest,
    tools: Dict[str, Callable[[Dict[str, Any]], Any]],
    *,
    kill_switch: KillSwitch,
    breaker: CircuitBreaker,
    governor: CostGovernor,
) -> Decision:
    """Run a governed MCP tool call if policy allows it."""

    if request.method not in tools:
        return {"status": "error", "reason": f"unknown method: {request.method}"}

    ks_allowed = kill_switch.check_task_allowed(f"mcp:{request.method}")
    if not ks_allowed["allowed"]:
        return {"status": "blocked", "reason": ks_allowed.get("reason", "kill switch active")}

    tool = tools[request.method]

    def _invoke() -> Any:
        return tool(request.params)

    try:
        result = breaker.call(_invoke)
    except CircuitBreakerOpen:
        return {"status": "blocked", "reason": "circuit breaker open"}
    except Exception as exc:
        return {"status": "error", "reason": str(exc)}

    prompt_tokens = max(1, len(request.method) + len(str(request.params)))
    completion_tokens = max(1, len(str(result)))
    estimated_cost = 0.000002 * (prompt_tokens + completion_tokens)
    governor.record_usage("mcp", "local", prompt_tokens, completion_tokens, estimated_cost)

    return {
        "status": "ok",
        "result": result,
        "cost": estimated_cost,
        "method": request.method,
    }


def make_toolset() -> Dict[str, Callable[[Dict[str, Any]], Any]]:
    """Small mock MCP tool catalog."""

    def get_weather(params: Dict[str, Any]) -> Dict[str, Any]:
        city = params.get("city", "unknown")
        return {"city": city, "forecast": "sunny", "temp_c": 22}

    def compute_total(params: Dict[str, Any]) -> Dict[str, Any]:
        left = float(params.get("left", 0))
        right = float(params.get("right", 0))
        return {"total": left + right}

    return {
        "weather.get": get_weather,
        "math.add": compute_total,
    }


def main() -> None:
    kill_switch = KillSwitch()
    breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=8.0)
    governor = CostGovernor(":memory:", soft_cap=1.0, hard_cap=2.0)

    tools = make_toolset()

    good = guarded_tool_dispatch(
        MockMCPRequest("weather.get", {"city": "Seattle"}),
        tools,
        kill_switch=kill_switch,
        breaker=breaker,
        governor=governor,
    )
    bad = guarded_tool_dispatch(
        MockMCPRequest("math.multiply", {"left": 2, "right": 3}),
        tools,
        kill_switch=kill_switch,
        breaker=breaker,
        governor=governor,
    )

    print(f"good: {good}")
    print(f"bad:  {bad}")


if __name__ == "__main__":
    main()

