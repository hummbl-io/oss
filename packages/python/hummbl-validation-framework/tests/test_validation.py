"""Tests for hummbl-validation-framework."""

import pytest

from hummbl_validation_framework import (
    ValidationSuite, ValidationTest,
    TERMINAL_VALUE, FALSIFIABILITY_CRITERION,
    create_heraldic_recognition_test,
    create_operator_comprehension_test,
    create_api_correlation_test,
    create_color_identification_test,
    create_trust_tier_recognition_test,
)
from hummbl_validation_framework import TestStatus as TestStatusEnum


class TestTerminalValue:
    def test_terminal_value_defined(self):
        assert "Operators" in TERMINAL_VALUE
        assert "routing decisions" in TERMINAL_VALUE
        assert "task completion" in TERMINAL_VALUE

    def test_terminal_value_is_measurable(self):
        assert "2 seconds" in TERMINAL_VALUE

    def test_falsifiability_criterion_defined(self):
        assert "declared failed" in FALSIFIABILITY_CRITERION

    def test_falsifiability_has_thresholds(self):
        assert "80%" in FALSIFIABILITY_CRITERION
        assert "70%" in FALSIFIABILITY_CRITERION
        assert "0.5" in FALSIFIABILITY_CRITERION

    def test_falsifiability_has_rollback(self):
        assert "reverted" in FALSIFIABILITY_CRITERION
        assert "fallback" in FALSIFIABILITY_CRITERION


class TestValidationTest:
    def test_add_result_pass(self):
        test = ValidationTest("t", "T", "d", "C4", 0.8, 3, "acc")
        result = test.add_result("devin", 1, 0.9)
        assert result.status == TestStatusEnum.PASSED

    def test_add_result_fail(self):
        test = ValidationTest("t", "T", "d", "C4", 0.8, 3, "acc")
        result = test.add_result("devin", 1, 0.5)
        assert result.status == TestStatusEnum.FAILED

    def test_is_complete(self):
        test = ValidationTest("t", "T", "d", "C4", 0.8, 3, "acc")
        assert not test.is_complete
        for i in range(3):
            test.add_result("a", i, 1.0)
        assert test.is_complete

    def test_average_score(self):
        test = ValidationTest("t", "T", "d", "C4", 0.8, 2, "acc")
        test.add_result("a", 1, 0.8)
        test.add_result("b", 2, 0.6)
        assert test.average_score == 0.7

    def test_pass_rate(self):
        test = ValidationTest("t", "T", "d", "C4", 0.8, 4, "acc")
        test.add_result("a", 1, 0.9)
        test.add_result("b", 2, 0.7)
        test.add_result("c", 3, 0.9)
        test.add_result("d", 4, 0.7)
        assert test.pass_rate == 0.5

    def test_verdict_incomplete(self):
        test = ValidationTest("t", "T", "d", "C4", 0.8, 5, "acc")
        test.add_result("a", 1, 1.0)
        assert test.verdict == "incomplete"

    def test_verdict_pass(self):
        test = ValidationTest("t", "T", "d", "C4", 0.8, 3, "acc")
        for i in range(3):
            test.add_result("a", i, 0.9)
        assert test.verdict == "pass"

    def test_verdict_fail(self):
        test = ValidationTest("t", "T", "d", "C4", 0.8, 3, "acc")
        for i in range(3):
            test.add_result("a", i, 0.5)
        assert test.verdict == "fail"

    def test_to_dict(self):
        test = ValidationTest("t", "T", "d", "C4", 0.8, 1, "acc")
        test.add_result("a", 1, 0.9)
        d = test.to_dict()
        assert d["test_id"] == "t"
        assert d["verdict"] == "pass"


class TestCanonicalTests:
    def test_heraldic(self):
        t = create_heraldic_recognition_test()
        assert t.test_id == "heraldic-recognition"
        assert t.pass_threshold == 0.80
        assert t.min_trials == 15

    def test_operator(self):
        t = create_operator_comprehension_test()
        assert t.pass_threshold == 0.70

    def test_api(self):
        t = create_api_correlation_test()
        assert t.pass_threshold == 0.50
        assert t.min_trials == 10

    def test_color(self):
        t = create_color_identification_test()
        assert t.pass_threshold == 0.60

    def test_trust(self):
        t = create_trust_tier_recognition_test()
        assert t.pass_threshold == 0.70


class TestValidationSuite:
    def test_creates_all_tests(self):
        suite = ValidationSuite()
        assert len(suite.tests) == 5

    def test_get_test(self):
        suite = ValidationSuite()
        assert suite.get_test("heraldic-recognition") is not None
        assert suite.get_test("nonexistent") is None

    def test_record_result(self):
        suite = ValidationSuite()
        result = suite.record_result("heraldic-recognition", "devin", 1, 1.0)
        assert result is not None
        assert result.status == TestStatusEnum.PASSED

    def test_record_unknown(self):
        suite = ValidationSuite()
        assert suite.record_result("nonexistent", "devin", 1, 1.0) is None

    def test_convenience_methods(self):
        suite = ValidationSuite()
        assert suite.record_heraldic_result("devin", 1, 1.0) is not None
        assert suite.record_operator_result("op1", 1, 0.75) is not None
        assert suite.record_api_result("devin", 1, 0.6) is not None
        assert suite.record_color_result("op1", 1, 0.8) is not None
        assert suite.record_trust_result("op1", 1, 0.9) is not None

    def test_all_complete_false(self):
        assert not ValidationSuite().all_complete

    def test_overall_verdict_incomplete(self):
        assert ValidationSuite().overall_verdict == "incomplete"

    def test_overall_verdict_fail(self):
        suite = ValidationSuite()
        test = suite.tests["heraldic-recognition"]
        for i in range(15):
            test.add_result("a", i, 0.3)
        assert suite.overall_verdict == "fail"

    def test_report(self):
        suite = ValidationSuite()
        report = suite.report()
        assert "terminal_value" in report
        assert "tests" in report
        assert len(report["tests"]) == 5

    def test_to_json(self):
        import json
        suite = ValidationSuite()
        data = json.loads(suite.to_json())
        assert "terminal_value" in data

    def test_summary(self):
        suite = ValidationSuite()
        s = suite.summary()
        assert "Validation Report" in s
