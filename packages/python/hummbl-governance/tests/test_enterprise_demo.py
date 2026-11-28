"""Regression test verifying the 5-minute enterprise agent governance demo."""

from __future__ import annotations

import importlib.util
from pathlib import Path

DEMO_PATH = (
    Path(__file__).resolve().parent.parent
    / "examples"
    / "enterprise_agent_governance_demo.py"
)


def _load_demo():
    spec = importlib.util.spec_from_file_location("enterprise_agent_governance_demo", DEMO_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_enterprise_agent_governance_demo_end_to_end(tmp_path):
    mod = _load_demo()
    summary = mod.run_demo(work_dir=tmp_path)

    assert summary["agent_id"] == "claims-triage-agent"
    assert summary["budget_decision"] == "ALLOW"
    assert summary["allowed_receipt_verified"] is True
    assert summary["tampered_receipt_rejected"] is True
    assert summary["kill_switch_mode"] == "HALT_ALL"
    assert summary["post_halt_allowed"] is False
    assert summary["blocked_receipt_verified"] is True
    assert summary["compliance_frameworks_total"] >= 18
    assert set(summary["key_2026_standards_present"]) == {"eu-ai-act", "nist-rmf", "iso42001"}
