#!/usr/bin/env python3
"""5-minute enterprise agent governance demo (hummbl-governance v1.5.1).

Demonstrates the 2026 runtime agent governance lifecycle with zero third-party
dependencies:
  1. Register a non-human agent identity (AgentRegistry, K3)
  2. Enforce runtime spend budget (CostGovernor, P5)
  3. Authorize and emit a cryptographically signed transition receipt
     (ToolTransitionReceipt, K1)
  4. Verify the receipt offline (replayable proof, tamper detection)
  5. Engage the graduated KillSwitch on anomaly and prove fail-closed blocking
     (KillSwitch, P1 / K12)
  6. Generate multi-framework compliance coverage summary (ComplianceMapper,
     EU AI Act / NIST AI RMF / ISO 42001)

Run:
    python examples/enterprise_agent_governance_demo.py
"""

from __future__ import annotations

import json
import secrets
import tempfile
from pathlib import Path
from typing import Any

from hummbl_governance import (
    AgentRegistry,
    CostGovernor,
    KillSwitch,
    KillSwitchMode,
    KillSwitchReason,
    TrustTier,
    build_tool_transition_receipt,
    framework_count,
    list_frameworks,
    verify_tool_transition_receipt,
)


def run_demo(work_dir: Path | None = None) -> dict[str, Any]:
    """Execute the full end-to-end governance demo and return structured proof."""
    signing_secret = secrets.token_bytes(32)
    agent_id = "claims-triage-agent"

    with tempfile.TemporaryDirectory() as tmp:
        root = work_dir or Path(tmp)
        root.mkdir(parents=True, exist_ok=True)

        # 1. Living Agent Registry (Non-Human Identity, K3)
        registry = AgentRegistry()
        registry.register_agent(
            agent_id,
            display="Claims Triage Agent",
            trust=TrustTier.HIGH,
        )
        registry.add_alias("triage-bot", agent_id)
        canonical_agent = registry.canonicalize("triage-bot")
        assert canonical_agent == agent_id

        # 2. Runtime Budget Enforcement (CostGovernor, P5)
        cost_gov = CostGovernor(
            db_path=root / "costs.db",
            soft_cap=5.00,
            hard_cap=10.00,
        )
        cost_gov.record_usage(
            provider="openai",
            model="gpt-5-mini",
            tokens_in=2500,
            tokens_out=600,
            cost=0.42,
            meta={"agent_id": canonical_agent, "tool": "approve_refund"},
        )
        budget = cost_gov.check_budget_status()
        assert budget.decision == "ALLOW", f"unexpected budget decision: {budget}"

        # 3. Signed Runtime Transition Receipt (K1, Replayable Proof)
        kill_switch = KillSwitch(
            state_dir=root / "ks",
            require_hmac=True,
            signing_secret=signing_secret,
        )
        ks_before = kill_switch.check_task_allowed("approve_refund")
        assert ks_before["allowed"] is True

        receipt = build_tool_transition_receipt(
            agent_id=canonical_agent,
            tool_name="approve_refund",
            tool_input={"claim_id": "CLM-2026-0042", "amount_usd": 125.00},
            runtime="mcp",
            hook="before_tool_call",
            actor="operator@acme.example",
            actor_mode="delegated_human_principal",
            kill_switch_result=ks_before,
            budget_status=budget,
            terminal_outcome="allowed",
            evidence_refs=["policy:refund-auto-cap-250"],
            signing_secret=signing_secret,
        )

        # 4. Offline Cryptographic Verification + Tamper Detection
        verified_intact = verify_tool_transition_receipt(receipt, signing_secret=signing_secret)
        assert verified_intact is True

        tampered = receipt.to_dict()
        tampered["tool_name"] = "wire_transfer_unlimited"
        verified_tampered = verify_tool_transition_receipt(tampered, signing_secret=signing_secret)
        assert verified_tampered is False

        # 5. Graduated Kill Switch Containment (P1 / K12)
        ks_event = kill_switch.engage(
            mode=KillSwitchMode.HALT_ALL,
            reason="Anomalous refund burst detected by drift monitor",
            triggered_by="soc-oncall",
            affected_tasks=1,
            failure_class=KillSwitchReason.DRIFT,
        )
        ks_after = kill_switch.check_task_allowed("approve_refund")
        assert ks_after["allowed"] is False

        blocked_receipt = build_tool_transition_receipt(
            agent_id=canonical_agent,
            tool_name="approve_refund",
            tool_input={"claim_id": "CLM-2026-0043", "amount_usd": 9500.00},
            runtime="mcp",
            hook="before_tool_call",
            actor="operator@acme.example",
            actor_mode="delegated_human_principal",
            kill_switch_result=ks_after,
            budget_status=budget,
            terminal_outcome="blocked_kill_switch",
            evidence_refs=[f"kill_switch:{ks_event.mode.name}"],
            signing_secret=signing_secret,
        )
        assert verify_tool_transition_receipt(blocked_receipt, signing_secret=signing_secret) is True

        # 6. Built-in Compliance Framework Coverage
        frameworks = list_frameworks()
        target_standards = [f for f in ("eu-ai-act", "nist-rmf", "iso42001") if f in frameworks]

        return {
            "agent_id": canonical_agent,
            "trust_tier": str(registry.get_trust_tier(canonical_agent)),
            "budget_decision": budget.decision,
            "daily_spend_usd": round(cost_gov.get_daily_spend(), 4),
            "allowed_receipt_verified": verified_intact,
            "tampered_receipt_rejected": not verified_tampered,
            "kill_switch_mode": ks_event.mode.name,
            "post_halt_allowed": ks_after["allowed"],
            "blocked_receipt_verified": True,
            "compliance_frameworks_total": framework_count(),
            "key_2026_standards_present": target_standards,
        }


def main() -> int:
    summary = run_demo()
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
