"""Verify command outcomes, including failures that previously exited zero."""

import pytest

from agent_eval_harness.cli import main


@pytest.mark.parametrize(
    ("text", "expected"),
    [("Status: PASS", 0), ("Status: FAIL", 1), ("PASS SECRET_KEY", 1)],
)
def test_required_and_forbidden_constraints(text, expected, capsys):
    assert main([text, "--require", r"\bPASS\b", "--forbid", r"\bSECRET_KEY\b"]) == expected
    output = capsys.readouterr().out
    assert "Eval Score:" in output
    assert ("Violations:" in output) == bool(expected)


@pytest.mark.parametrize("arguments", [["text"], ["text", "--require", "["]])
def test_missing_or_invalid_rules_are_argument_errors(arguments):
    with pytest.raises(SystemExit) as error:
        main(arguments)
    assert error.value.code == 2
