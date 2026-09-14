"""Evaluation Harness for Rule Adherence and Constraint Verification."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class EvalRule:
    rule_id: str
    description: str
    validator: Callable[[str], bool]
    negative_rule: bool = False  # If true, match is a violation


@dataclass
class EvalResult:
    total_rules: int = 0
    passed_rules: int = 0
    failed_rules: int = 0
    score: float = 100.0
    violations: List[str] = field(default_factory=list)


class AgentEvalHarness:
    """Deterministic evaluation harness benchmarking agent outputs against rigid constraints."""

    def __init__(self) -> None:
        self.rules: List[EvalRule] = []

    def add_regex_constraint(self, rule_id: str, pattern: str, description: str, must_not_match: bool = False) -> None:
        """Add a strict regex-based rule constraint."""
        regex = re.compile(pattern)
        if must_not_match:
            self.rules.append(EvalRule(
                rule_id=rule_id,
                description=description,
                validator=lambda text: regex.search(text) is None,
                negative_rule=True,
            ))
        else:
            self.rules.append(EvalRule(
                rule_id=rule_id,
                description=description,
                validator=lambda text: regex.search(text) is not None,
                negative_rule=False,
            ))

    def evaluate(self, agent_output: str) -> EvalResult:
        """Run all registered rule constraints against an agent output."""
        result = EvalResult(total_rules=len(self.rules))
        for rule in self.rules:
            passed = rule.validator(agent_output)
            if passed:
                result.passed_rules += 1
            else:
                result.failed_rules += 1
                result.violations.append(f"[{rule.rule_id}] Failed: {rule.description}")

        if result.total_rules > 0:
            result.score = round((result.passed_rules / result.total_rules) * 100.0, 1)
        else:
            result.score = 100.0

        return result
