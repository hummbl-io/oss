"""Evidence-governed evaluation contracts for compositional systems."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .canonical import canonicalize_json, digest_bytes, load_json
from .records import Record, Relation, new_urn_uuid7


@dataclass
class EvalResult:
    """Result of running a single test against a single output."""

    test_name: str
    passed: bool
    score: float
    details: dict[str, Any]


class EvalSuite:
    """Run evaluation suites against LLM outputs."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.tests: list[tuple[str, Callable[[str], dict[str, Any]]]] = []
        self.results: list[EvalResult] = []

    def add_test(self, name: str, check_func: Callable[[str], dict[str, Any]]) -> None:
        """Register a test function with the suite."""
        self.tests.append((name, check_func))

    def run(self, outputs: list[str]) -> list[EvalResult]:
        """Run all registered tests against all provided outputs."""
        for output in outputs:
            for name, check in self.tests:
                result = check(output)
                er = EvalResult(
                    test_name=name,
                    passed=bool(result.get("passed", False)),
                    score=float(result.get("score", 0.0)),
                    details=result,
                )
                self.results.append(er)
        return self.results

    def report(self) -> str:
        """Generate a text summary of the results."""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        percentage = passed / total * 100 if total else 0.0
        return f"Suite: {self.name}\nPassed: {passed}/{total} ({percentage:.1f}%)"


__all__ = [
    "EvalResult",
    "EvalSuite",
    "Record",
    "Relation",
    "canonicalize_json",
    "digest_bytes",
    "load_json",
    "new_urn_uuid7",
]

__version__ = "0.1.0.dev0"
