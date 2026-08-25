#!/usr/bin/env python3
"""Example: governed direct OpenAI call wrapper.

The script demonstrates how to run an LLM completion request through:

- Kill switch (allow / block)
- Circuit breaker (degrade on repeated upstream failures)
- Cost governor (spend tracking)

If the OpenAI SDK is not installed or no API key is present,
this example falls back to a local mock call so it remains runnable.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Mapping

from hummbl_governance import CircuitBreaker, CostGovernor, KillSwitch
from hummbl_governance.circuit_breaker import CircuitBreakerOpen

try:  # pragma: no cover - optional integration dependency
    from openai import OpenAI

    _HAS_OPENAI = True
except ImportError:  # pragma: no cover - optional path
    OpenAI = None  # type: ignore[assignment]
    _HAS_OPENAI = False


def _mock_completion(prompt: str) -> Dict[str, Any]:
    """Return a deterministic local completion shape."""

    return {
        "id": "mock-openai-response",
        "object": "chat.completion",
        "model": "mock-gpt",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": f"Mocked governance response for: {prompt}"},
            },
        ],
        "usage": {
            "prompt_tokens": max(1, len(prompt.split())),
            "completion_tokens": 12,
            "total_tokens": max(1, len(prompt.split())) + 12,
        },
    }


def _usage_tokens(response: Mapping[str, Any]) -> tuple[int, int, int]:
    usage = response.get("usage", {}) if isinstance(response, Mapping) else {}
    prompt_tokens = int(usage.get("prompt_tokens", 0) or 0)
    completion_tokens = int(usage.get("completion_tokens", 0) or 0)
    total_tokens = int(usage.get("total_tokens", prompt_tokens + completion_tokens) or 0)
    return prompt_tokens, completion_tokens, total_tokens


def _estimate_cost(prompt_tokens: int, completion_tokens: int, model: str) -> float:
    """Simple cost estimator, model-aware enough for a usage record."""

    # This is intentionally explicit and not a billing-grade price model.
    if model.startswith("gpt-4"):
        return 0.000015 * (prompt_tokens + completion_tokens)
    return 0.000003 * (prompt_tokens + completion_tokens)


def governed_completion(prompt: str, model: str = "gpt-4o-mini") -> Dict[str, Any]:
    """Run one governed completion.

    Returns a dict with either:

    - status: 'blocked'
    - status: 'mocked'
    - status: 'ok'
    """

    kill_switch = KillSwitch()
    breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=15.0)
    governor = CostGovernor(":memory:", soft_cap=5.0, hard_cap=10.0)

    allowed = kill_switch.check_task_allowed("raw_openai_completion")
    if not allowed["allowed"]:
        return {
            "status": "blocked",
            "reason": allowed.get("reason", "kill switch is active"),
        }

    def _call_openai() -> Dict[str, Any]:
        if not _HAS_OPENAI:
            return _mock_completion(prompt)

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return _mock_completion(prompt)

        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        return {
            "id": response.id,
            "object": response.object,
            "model": response.model,
            "choices": [
                {
                    "index": c.index,
                    "message": {"role": c.message.role, "content": c.message.content},
                }
                for c in getattr(response, "choices", [])
            ],
            "usage": {
                "prompt_tokens": getattr(response.usage, "prompt_tokens", 0),
                "completion_tokens": getattr(response.usage, "completion_tokens", 0),
                "total_tokens": getattr(response.usage, "total_tokens", 0),
            },
        }

    try:
        response = breaker.call(_call_openai)
    except CircuitBreakerOpen as exc:
        return {"status": "blocked", "reason": f"circuit open: {exc}"}

    prompt_tokens, completion_tokens, _ = _usage_tokens(response)
    cost = _estimate_cost(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens, model=model)
    governor.record_usage("openai", model, prompt_tokens, completion_tokens, cost)

    return {"status": "ok", "response": response, "cost": cost}


def main() -> None:
    result = governed_completion("What is governed autonomy in AI agents?")
    print(f"Status: {result['status']}")
    if result["status"] != "ok":
        print(result)
        return

    response = result["response"]
    first_choice = response["choices"][0]
    print(f"Response model: {response['model']}")
    print(f"Message: {first_choice['message']['content']}")
    print(f"Recorded cost: ${result['cost']:.4f}")


if __name__ == "__main__":
    main()

