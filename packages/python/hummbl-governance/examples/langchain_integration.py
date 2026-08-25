#!/usr/bin/env python3
"""Example: governed LangChain-style invocation.

The example keeps the policy boundary the same regardless of whether
`langchain` is installed:

- kill switch blocks unsafe runs
- circuit breaker wraps the model/agent invoke
- governor records token costs

Run with LangChain installed when available, otherwise the built-in mock path
exercises the same governance checks.
"""

from __future__ import annotations

from typing import Any, Dict

from hummbl_governance import CircuitBreaker, CostGovernor, KillSwitch
from hummbl_governance.circuit_breaker import CircuitBreakerOpen

try:  # pragma: no cover - optional dependency path
    from langchain_openai import ChatOpenAI

    _HAS_LANGCHAIN = True
except ImportError:  # pragma: no cover
    ChatOpenAI = None  # type: ignore[assignment]
    _HAS_LANGCHAIN = False


def _make_langchain_runnable(prompt: str):
    """Build either a real or mocked LangChain runnable."""

    if _HAS_LANGCHAIN:
        # Minimal chain: fixed-model invocation style.
        model = ChatOpenAI(model="gpt-4o-mini")

        class _SimpleAgent:
            def invoke(self, text: str) -> str:
                return model.invoke(text).content

        return _SimpleAgent()

    class _MockLangChain:
        def invoke(self, text: str) -> str:
            return f"Mocked LangChain output for: {text}"

    return _MockLangChain()


def governed_langchain_invoke(input_text: str) -> Dict[str, Any]:
    kill_switch = KillSwitch()
    breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=20.0)
    governor = CostGovernor(":memory:", soft_cap=2.0, hard_cap=5.0)

    allowed = kill_switch.check_task_allowed("langchain_agent")
    if not allowed["allowed"]:
        return {"status": "blocked", "reason": allowed["reason"]}

    runnable = _make_langchain_runnable(input_text)

    try:
        # In a real chain this would be model/agent invocation.
        output = breaker.call(runnable.invoke, input_text)
    except CircuitBreakerOpen:
        return {"status": "blocked", "reason": "circuit breaker open"}

    # LangChain examples often track approximate tokens externally; here we
    # record an estimate so the usage ledger can be verified by shape.
    prompt_tokens = max(1, len(input_text.split()))
    completion_tokens = max(1, len(str(output).split()))
    estimated_cost = 0.000004 * (prompt_tokens + completion_tokens)
    governor.record_usage("langchain", "gpt-4o-mini", prompt_tokens, completion_tokens, estimated_cost)

    return {
        "status": "ok",
        "output": output,
        "cost": estimated_cost,
        "tokens": {
            "prompt": prompt_tokens,
            "completion": completion_tokens,
        },
    }


def main() -> None:
    result = governed_langchain_invoke("Summarize the HUMMBL governance runtime boundary in one line.")
    print(f"Status: {result['status']}")
    print(f"Result: {result.get('output', result.get('reason'))}")
    if result.get("cost") is not None:
        print(f"Estimated cost: ${result['cost']:.6f}")


if __name__ == "__main__":
    main()
