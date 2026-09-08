#!/usr/bin/env python3
# Copyright 2026 HUMMBL, LLC
# SPDX-License-Identifier: Apache-2.0
"""Cursor beforeShellExecution harness hook (CONTRACT × DCT × EVIDENCE).

Wires published hummbl-governance APIs:
  - KillSwitch (P1)
  - CapabilityFence (P4)
  - ReceiptEngine (P26 / K1)

Credo-free. Public C = CONTRACT (not Atlas Constitution).
Alpha demo / competitive posture artifact. Not production-certified.
Confers no compliance status.

Canon:
  - DOI 10.5281/zenodo.21957831
  - docs/research/2026-08-23_governance-tuple-protocol-spec.md
  - packages/python/hummbl-governance/docs/public-claims.md

Cursor passes a JSON payload on stdin (command + optional cwd). This hook
prints a JSON decision on stdout:
  {"permission": "allow"|"deny", "reason": "...", "receipt_id": "..."}

See hooks.json.example for wiring.
"""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

# Prefer published package APIs from this monorepo when importable.
try:
    from hummbl_governance import (
        CapabilityDenied,
        CapabilityFence,
        KillSwitch,
        KillSwitchMode,
        ReceiptEngine,
    )
    from hummbl_governance.delegation import DelegationTokenManager, TokenBinding
except ImportError:  # pragma: no cover - demo path when package not on PYTHONPATH
    print(
        json.dumps(
            {
                "permission": "deny",
                "reason": (
                    "hummbl_governance not importable; install packages/python/"
                    "hummbl-governance or set PYTHONPATH"
                ),
            }
        )
    )
    raise SystemExit(0)


_SHELL_CAP_MAP: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\brm\b|\bunlink\b|\brmdir\b", re.I), "shell:rm"),
    (re.compile(r"\bcurl\b|\bwget\b|\bnc\b", re.I), "shell:net"),
    (re.compile(r"\b(cat|less|head|tail|rg|grep|ls|find)\b", re.I), "shell:read"),
    (re.compile(r".", re.I), "shell:execute"),
]


def _capability_for_command(command: str) -> str:
    for pattern, cap in _SHELL_CAP_MAP:
        if pattern.search(command):
            return cap
    return "shell:execute"


def _read_input() -> dict[str, Any]:
    raw = sys.stdin.read().strip()
    if not raw:
        return {"command": ""}
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    return {"command": raw}


def decide(payload: dict[str, Any]) -> dict[str, Any]:
    command = str(payload.get("command") or payload.get("cmd") or "").strip()
    agent_id = str(payload.get("agent_id") or "cursor-shell-hook")
    task_id = str(payload.get("task_id") or "cursor-beforeShellExecution")
    contract_id = str(payload.get("contract_id") or "contract-cursor-shell-v0")

    # CONTRACT surface: allowlisted shell capabilities for this demo contract.
    allowed_caps = ["shell:read", "shell:execute", "fs:list"]
    denied_caps = ["shell:rm", "shell:net"]

    state_dir = Path(
        os.environ.get(
            "HUMMBL_HOOK_STATE_DIR",
            tempfile.mkdtemp(prefix="hummbl-cursor-hook-"),
        )
    )
    secret = os.environ.get("HUMMBL_SIGNING_SECRET", "assessor-demo-not-for-prod").encode(
        "utf-8"
    )

    ks = KillSwitch()
    # Demo default: disengaged. Operators may pre-engage via env.
    engage_mode = os.environ.get("HUMMBL_HOOK_KILL_MODE", "").strip().upper()
    if engage_mode and engage_mode != "DISENGAGED":
        ks.engage(
            mode=KillSwitchMode[engage_mode],
            reason="Harness demo kill mode from HUMMBL_HOOK_KILL_MODE",
            triggered_by="cursor_beforeShellExecution",
        )

    ks_check = ks.check_task_allowed("shell_execution")
    if not ks_check.get("allowed"):
        return {
            "permission": "deny",
            "reason": ks_check.get("reason", "kill switch blocked shell_execution"),
            "tuple": "CONTRACT×DCT×EVIDENCE",
            "component": "KillSwitch",
        }

    # DCT: issue a short-lived demo token bound to the CONTRACT id.
    mgr = DelegationTokenManager(secret=secret)
    token = mgr.create_token(
        issuer="operator@cursor-harness",
        subject=agent_id,
        ops_allowed=allowed_caps,
        binding=TokenBinding(task_id=task_id, contract_id=contract_id),
        expiry_minutes=30,
    )

    fence = CapabilityFence.from_delegation_token(
        token,
        mgr,
        expected_issuer="operator@cursor-harness",
        expected_subject=agent_id,
        expected_task_id=task_id,
        expected_contract_id=contract_id,
        denied=denied_caps,
    )

    capability = _capability_for_command(command)
    receipts = ReceiptEngine(state_dir=state_dir, signing_secret=secret)

    try:
        fence.check(capability)
        permission = "allow"
        reason = f"capability {capability!r} permitted under CONTRACT {contract_id}"
        action_type = "shell.allow"
    except CapabilityDenied as exc:
        permission = "deny"
        reason = str(exc)
        action_type = "shell.deny"

    last = receipts.last_for_agent(agent_id)
    prev_hash = last.compute_hash() if last else ""
    seq = (last.sequence_id + 1) if last else 1
    receipt = receipts.create_and_store(
        agent_id=agent_id,
        action_type=action_type,
        payload={
            "command": command[:500],
            "capability": capability,
            "permission": permission,
            "contract_id": contract_id,
            "task_id": task_id,
            "dct_token_id": token.token_id,
            "tuple": "CONTRACT×DCT×EVIDENCE",
        },
        law_checks=["K1", "K6", "K12"],
        evidence_grade="DEMO",
        prev_receipt_hash=prev_hash,
        sequence_id=seq,
    )

    return {
        "permission": permission,
        "reason": reason,
        "receipt_id": receipt.receipt_id,
        "capability": capability,
        "contract_id": contract_id,
        "dct_token_id": token.token_id,
        "tuple": "CONTRACT×DCT×EVIDENCE",
        "alpha": True,
        "production_certified": False,
    }


def main() -> int:
    decision = decide(_read_input())
    print(json.dumps(decision, sort_keys=True))
    # Cursor hooks typically treat exit 0 as "hook ran"; permission is in JSON.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
