"""HUMMBL Validation Framework — external validation tests for the design system.

Addresses ARCANA peer review findings:
- C1 (4/4 lenses): No falsifiability criterion
- C4 (3/4 lenses): Verification is self-referential
- D1 (measurement, REJECT): No terminal value defined
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

__version__ = "0.1.0"

TERMINAL_VALUE = (
    "Operators can identify agent status in <2 seconds and make correct "
    "routing decisions that result in successful task completion."
)

FALSIFIABILITY_CRITERION = (
    "The HUMMBL design system is declared failed if any of the following hold:\n"
    "1. Agent recognition test: agents cannot identify their own heraldic arms "
    "with >80% accuracy in a blind test (n>=5 agents, n>=3 trials each).\n"
    "2. Operator comprehension test: operators cannot report fleet status with "
    ">70% accuracy after viewing the dashboard for 30 seconds (n>=3 operators, "
    "n>=5 trials each).\n"
    "3. API correlation test: API scores do not correlate with human judgment "
    "of task quality (correlation <0.5, n>=10 tasks).\n"
    "If any test fails, the corresponding component is reverted to its fallback."
)


class TestStatus(Enum):
    NOT_RUN = "not_run"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"

    __test__ = False


@dataclass
class ValidationResult:
    test_id: str
    test_name: str
    participant: str
    trial: int
    timestamp: str
    status: TestStatus
    score: float
    detail: str = ""


@dataclass
class ValidationTest:
    test_id: str
    test_name: str
    description: str
    arcana_finding: str
    pass_threshold: float
    min_trials: int
    unit: str
    results: list[ValidationResult] = field(default_factory=list)

    def add_result(self, participant: str, trial: int, score: float, detail: str = "") -> ValidationResult:
        status = TestStatus.PASSED if score >= self.pass_threshold else TestStatus.FAILED
        result = ValidationResult(
            test_id=self.test_id, test_name=self.test_name,
            participant=participant, trial=trial,
            timestamp=datetime.now(UTC).isoformat(),
            status=status, score=score, detail=detail,
        )
        self.results.append(result)
        return result

    @property
    def is_complete(self) -> bool:
        return len(self.results) >= self.min_trials

    @property
    def average_score(self) -> float:
        if not self.results:
            return 0.0
        return sum(r.score for r in self.results) / len(self.results)

    @property
    def pass_rate(self) -> float:
        if not self.results:
            return 0.0
        return sum(1 for r in self.results if r.status == TestStatus.PASSED) / len(self.results)

    @property
    def verdict(self) -> str:
        if not self.is_complete:
            return "incomplete"
        return "pass" if self.average_score >= self.pass_threshold else "fail"

    def to_dict(self) -> dict[str, Any]:
        return {
            "test_id": self.test_id, "test_name": self.test_name,
            "description": self.description, "arcana_finding": self.arcana_finding,
            "pass_threshold": self.pass_threshold, "min_trials": self.min_trials,
            "unit": self.unit, "n_results": len(self.results),
            "is_complete": self.is_complete, "average_score": self.average_score,
            "pass_rate": self.pass_rate, "verdict": self.verdict,
            "results": [{"participant": r.participant, "trial": r.trial, "status": r.status.value, "score": r.score, "detail": r.detail} for r in self.results],
        }


def create_heraldic_recognition_test() -> ValidationTest:
    return ValidationTest("heraldic-recognition", "Heraldic Recognition Test",
        "Show each agent 5 arms without labels. Pass if accuracy >= 80%.",
        "C4", 0.80, 15, "accuracy")

def create_operator_comprehension_test() -> ValidationTest:
    return ValidationTest("operator-comprehension", "Operator Comprehension Test",
        "Show dashboard for 30s, ask 4 questions. Pass if accuracy >= 70%.",
        "C4", 0.70, 15, "accuracy")

def create_api_correlation_test() -> ValidationTest:
    return ValidationTest("api-correlation", "API Correlation Test",
        "Score 10 tasks with API and human. Pass if correlation >= 0.50.",
        "C4", 0.50, 10, "correlation")

def create_color_identification_test() -> ValidationTest:
    return ValidationTest("color-identification", "Color Identification Test",
        "Match 11 colors to agent names. Pass if accuracy >= 60%.",
        "C1", 0.60, 9, "accuracy")

def create_trust_tier_recognition_test() -> ValidationTest:
    return ValidationTest("trust-tier-recognition", "Trust Tier Recognition Test",
        "Rank 5 trust tier colors. Pass if accuracy >= 70%.",
        "C1", 0.70, 9, "accuracy")


class ValidationSuite:
    """Runs all external validation tests and produces a report."""

    def __init__(self) -> None:
        self.tests: dict[str, ValidationTest] = {
            "heraldic-recognition": create_heraldic_recognition_test(),
            "operator-comprehension": create_operator_comprehension_test(),
            "api-correlation": create_api_correlation_test(),
            "color-identification": create_color_identification_test(),
            "trust-tier-recognition": create_trust_tier_recognition_test(),
        }

    def get_test(self, test_id: str) -> ValidationTest | None:
        return self.tests.get(test_id)

    def record_result(self, test_id: str, participant: str, trial: int, score: float, detail: str = "") -> ValidationResult | None:
        test = self.tests.get(test_id)
        if not test:
            return None
        return test.add_result(participant, trial, score, detail)

    def record_heraldic_result(self, participant: str, trial: int, score: float, detail: str = "") -> ValidationResult | None:
        return self.record_result("heraldic-recognition", participant, trial, score, detail)

    def record_operator_result(self, participant: str, trial: int, score: float, detail: str = "") -> ValidationResult | None:
        return self.record_result("operator-comprehension", participant, trial, score, detail)

    def record_api_result(self, participant: str, trial: int, score: float, detail: str = "") -> ValidationResult | None:
        return self.record_result("api-correlation", participant, trial, score, detail)

    def record_color_result(self, participant: str, trial: int, score: float, detail: str = "") -> ValidationResult | None:
        return self.record_result("color-identification", participant, trial, score, detail)

    def record_trust_result(self, participant: str, trial: int, score: float, detail: str = "") -> ValidationResult | None:
        return self.record_result("trust-tier-recognition", participant, trial, score, detail)

    @property
    def all_complete(self) -> bool:
        return all(t.is_complete for t in self.tests.values())

    @property
    def overall_verdict(self) -> str:
        verdicts = [t.verdict for t in self.tests.values()]
        if "fail" in verdicts:
            return "fail"
        if "incomplete" in verdicts:
            return "incomplete"
        return "pass"

    def report(self) -> dict[str, Any]:
        return {
            "terminal_value": TERMINAL_VALUE,
            "falsifiability_criterion": FALSIFIABILITY_CRITERION,
            "overall_verdict": self.overall_verdict,
            "all_complete": self.all_complete,
            "tests": {tid: t.to_dict() for tid, t in self.tests.items()},
            "generated_at": datetime.now(UTC).isoformat(),
        }

    def to_json(self) -> str:
        return json.dumps(self.report(), indent=2)

    def summary(self) -> str:
        lines = [
            "HUMMBL Design System — External Validation Report",
            "=" * 60,
            f"Terminal value: {TERMINAL_VALUE[:80]}...",
            f"Overall verdict: {self.overall_verdict}",
            f"All tests complete: {self.all_complete}",
            "",
            "Test Results:",
        ]
        for tid, test in self.tests.items():
            icon = {"pass": "✓", "fail": "✗", "incomplete": "○"}.get(test.verdict, "?")
            lines.append(f"  {icon} {test.test_name}: avg={test.average_score:.2f} pass_rate={test.pass_rate:.0%} trials={len(test.results)}/{test.min_trials} verdict={test.verdict}")
        return "\n".join(lines)
