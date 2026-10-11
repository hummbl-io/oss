# Copyright 2026 HUMMBL, LLC
# SPDX-License-Identifier: Apache-2.0
"""Behavioral checks for the public budget-stop example."""

import subprocess
import sys
from pathlib import Path

from examples.budget_stop_demo import run_demo


def test_denied_task_never_reaches_the_executor():
    calls = []
    result = run_demo(calls.append)
    assert calls == [1, 2, 3, 4]
    assert result["blocked_task"] == 5
    assert result["events"][-1] == {
        "task": 5, "decision": "DENY", "spend_before": 1.0, "executed": False,
    }
    assert result["recorded_spend"] == 1.0
    assert [event["decision"] for event in result["events"]] == [
        "ALLOW", "ALLOW", "WARN", "WARN", "DENY",
    ]


def test_cli_does_not_overwrite_an_existing_summary(tmp_path):
    target = tmp_path / "result.json"
    target.write_text("keep this evidence", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-m", "examples.budget_stop_demo", "--output", str(target)],
        cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True,
    )
    assert result.returncode != 0
    assert target.read_text(encoding="utf-8") == "keep this evidence"
