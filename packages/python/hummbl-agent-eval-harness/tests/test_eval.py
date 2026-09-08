"""Tests for agent-eval-harness constraint verification."""

from agent_eval_harness import AgentEvalHarness


def test_positive_and_negative_constraints():
    harness = AgentEvalHarness()
    harness.add_regex_constraint("R1", r"\bPASS\b", "Must state PASS")
    harness.add_regex_constraint("R2", r"\bconfidential\b", "Must not leak confidential keyword", must_not_match=True)

    res_good = harness.evaluate("STATUS: PASS. All tasks complete.")
    assert res_good.score == 100.0
    assert len(res_good.violations) == 0

    res_bad = harness.evaluate("STATUS: PASS. Here is confidential data.")
    assert res_bad.score == 50.0
    assert len(res_bad.violations) == 1
    assert "confidential" in res_bad.violations[0]
