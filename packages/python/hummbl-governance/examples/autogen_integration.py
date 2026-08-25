#!/usr/bin/env python3
"""Example: governed Microsoft AutoGen chat flow.

This stays runnable without `pyautogen` by using a mock chat path when the
library is not installed.
"""

from __future__ import annotations

from typing import Any, Dict

from hummbl_governance import CircuitBreaker, CostGovernor, KillSwitch
from hummbl_governance.circuit_breaker import CircuitBreakerOpen

try:  # pragma: no cover - optional dependency path
    from autogen import AssistantAgent, UserProxyAgent

    _HAS_AUTOGEN = True
except ImportError:  # pragma: no cover
    AssistantAgent = None  # type: ignore[assignment]
    UserProxyAgent = None  # type: ignore[assignment]
    _HAS_AUTOGEN = False


def _build_chat() -> tuple[Any, Any]:
    """Return `(user_proxy, assistant)` for mock or installed AutoGen."""

    if not _HAS_AUTOGEN:

        class _MockAssistant:
            def __init__(self, name: str):
                self.name = name

        class _MockUser:
            def initiate_chat(self, assistant: Any, message: str) -> Dict[str, Any]:
                return {
                    "assistant": getattr(assistant, "name", "assistant"),
                    "message": message,
                    "reply": "mock Autogen reply",
                }

        return _MockUser(), _MockAssistant("assistant")

    llm_config = {"config_list": [{"model": "gpt-4o-mini"}]}
    assistant = AssistantAgent("assistant", llm_config=llm_config)
    user_proxy = UserProxyAgent("user_proxy")
    return user_proxy, assistant


def governed_autogen_chat(message: str) -> Dict[str, Any]:
    kill_switch = KillSwitch()
    breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=20.0)
    governor = CostGovernor(":memory:", soft_cap=1.5, hard_cap=3.0)

    if not kill_switch.check_task_allowed("autogen_chat")["allowed"]:
        return {"status": "blocked", "reason": "kill switch blocked task"}

    user_proxy, assistant = _build_chat()

    try:
        result = breaker.call(user_proxy.initiate_chat, assistant, message=message)
    except CircuitBreakerOpen:
        return {"status": "blocked", "reason": "circuit breaker open"}
    except Exception as exc:  # pragma: no cover - defensive path for real AutoGen SDK behavior
        return {"status": "error", "reason": str(exc)}

    prompt_tokens = max(1, len(message.split()))
    completion_tokens = max(1, len(str(result).split()))
    cost = 0.00001 * (prompt_tokens + completion_tokens)
    governor.record_usage("autogen", "gpt-4o-mini", prompt_tokens, completion_tokens, cost)

    return {"status": "ok", "result": result, "cost": cost}


def main() -> None:
    result = governed_autogen_chat("Draft a minimal rollout safety policy for autonomous agents.")
    print(f"Status: {result['status']}")
    print(f"Result: {result.get('result', result.get('reason'))}")
    if result.get("cost") is not None:
        print(f"Estimated cost: ${result['cost']:.5f}")


if __name__ == "__main__":
    main()

