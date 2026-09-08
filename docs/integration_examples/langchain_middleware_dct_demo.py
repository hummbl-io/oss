#!/usr/bin/env python3
# Copyright 2026 HUMMBL, LLC
# SPDX-License-Identifier: Apache-2.0
"""Public LangChain-shaped middleware demo: DCT + KillSwitch + JSONL evidence.

Minimal dependencies:
  - Required: hummbl-governance (stdlib-only Core) from this monorepo / PyPI
  - Optional: langchain (only if you want the real BaseCallbackHandler path)

Without LangChain installed, the same middleware boundary runs against a
mock runnable so the demo stays reproducible in CI and air-gapped checks.

Alpha demo / competitive posture artifact. Not production-certified.
Confers no compliance status. Credo-free.
Public C = CONTRACT (not Atlas Constitution).

Canon:
  - DOI 10.5281/zenodo.21957831
  - docs/research/2026-08-23_governance-tuple-protocol-spec.md
  - packages/python/hummbl-tuples/schemas/{contract,dct,evidence}.schema.json
  - packages/python/hummbl-governance/docs/public-claims.md
"""

from __future__ import annotations

import json
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from hummbl_governance import KillSwitch, KillSwitchMode
from hummbl_governance.delegation import DelegationTokenManager, TokenBinding

try:  # optional — keep deps minimal
    from langchain_core.callbacks.base import BaseCallbackHandler

    _HAS_LANGCHAIN = True
except ImportError:  # pragma: no cover
    BaseCallbackHandler = object  # type: ignore[misc,assignment]
    _HAS_LANGCHAIN = False


@dataclass
class MiddlewareDecision:
    allowed: bool
    reason: str
    dct_token_id: str | None
    evidence_path: str


class DctKillSwitchJsonlMiddleware(BaseCallbackHandler if _HAS_LANGCHAIN else object):
    """Pre-tool / pre-invoke gate emitting CONTRACT×DCT×EVIDENCE JSONL."""

    def __init__(
        self,
        *,
        issuer: str = "operator@langchain-demo",
        subject: str = "langchain-agent",
        contract_id: str = "contract-langchain-middleware-v0",
        task_id: str = "task-langchain-middleware-demo",
        ops_allowed: list[str] | None = None,
        jsonl_path: Path | None = None,
        signing_secret: bytes = b"langchain-demo-not-for-prod",
    ) -> None:
        if _HAS_LANGCHAIN:
            super().__init__()  # type: ignore[misc]
        self.issuer = issuer
        self.subject = subject
        self.contract_id = contract_id
        self.task_id = task_id
        self.ops_allowed = ops_allowed or ["llm:invoke", "tool:search"]
        self.jsonl_path = jsonl_path or Path(tempfile.gettempdir()) / "hummbl_langchain_demo.jsonl"
        self.mgr = DelegationTokenManager(secret=signing_secret)
        self.ks = KillSwitch()
        self._token = self.mgr.create_token(
            issuer=self.issuer,
            subject=self.subject,
            ops_allowed=self.ops_allowed,
            binding=TokenBinding(task_id=self.task_id, contract_id=self.contract_id),
            expiry_minutes=60,
        )
        self._write_contract_genesis()

    def _now(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def _append(self, record: dict[str, Any]) -> None:
        self.jsonl_path.parent.mkdir(parents=True, exist_ok=True)
        with self.jsonl_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, sort_keys=True) + "\n")

    def _write_contract_genesis(self) -> None:
        self._append(
            {
                "tuple_type": "CONTRACT",
                "id": f"ctr-{self.contract_id}",
                "time": self._now(),
                "intent_id": "intent-langchain-middleware",
                "task_id": self.task_id,
                "state": "ok",
                "drift": 0,
                "tier": 0,
                "agent": self.subject,
                "tool": "langchain.middleware",
                "previous_hash": None,
                "tuple_data": {
                    "contract_id": self.contract_id,
                    "objective": "Demo DCT+KillSwitch JSONL mediation for LangChain-shaped invoke",
                    "allowed_tools": list(self.ops_allowed),
                    "outputs": ["jsonl_evidence"],
                    "risk_tier": "low",
                },
            }
        )
        self._append(
            {
                "tuple_type": "DCT",
                "id": f"dct-{self._token.token_id}",
                "time": self._now(),
                "intent_id": "intent-langchain-middleware",
                "task_id": self.task_id,
                "state": "ok",
                "drift": 0,
                "tier": 0,
                "agent": self.subject,
                "tool": "delegation.create_token",
                "previous_hash": None,
                "tuple_data": {
                    "event": "dct_issued",
                    "token_id": self._token.token_id,
                    "issuer": self.issuer,
                    "subject": self.subject,
                    "ops_allowed": list(self.ops_allowed),
                },
            }
        )

    def gate(self, operation: str) -> MiddlewareDecision:
        ks = self.ks.check_task_allowed("langchain_invoke")
        if not ks.get("allowed"):
            decision = MiddlewareDecision(
                allowed=False,
                reason=str(ks.get("reason", "kill switch blocked")),
                dct_token_id=self._token.token_id,
                evidence_path=str(self.jsonl_path),
            )
            self._emit_evidence("blocked", operation, decision.reason)
            return decision

        ok, err = self.mgr.check_least_privilege(
            self._token,
            operation,
            allowed_tools=self.ops_allowed,
        )
        if not ok:
            decision = MiddlewareDecision(
                allowed=False,
                reason=f"DCT denied operation {operation!r}: {err}",
                dct_token_id=self._token.token_id,
                evidence_path=str(self.jsonl_path),
            )
            self._emit_evidence("blocked", operation, decision.reason)
            return decision

        decision = MiddlewareDecision(
            allowed=True,
            reason=f"DCT permitted {operation!r}",
            dct_token_id=self._token.token_id,
            evidence_path=str(self.jsonl_path),
        )
        self._emit_evidence("ok", operation, decision.reason)
        return decision

    def _emit_evidence(self, state: str, operation: str, reason: str) -> None:
        self._append(
            {
                "tuple_type": "EVIDENCE",
                "id": f"ev-{operation}-{self._now()}",
                "time": self._now(),
                "intent_id": "intent-langchain-middleware",
                "task_id": self.task_id,
                "state": state if state in {"ok", "blocked", "error"} else "error",
                "drift": 0,
                "tier": 0,
                "agent": self.subject,
                "tool": operation,
                "previous_hash": None,
                "tuple_data": {
                    "event": "langchain_middleware_gate",
                    "operation": operation,
                    "reason": reason,
                    "dct_token_id": self._token.token_id,
                    "kill_switch_mode": self.ks.mode.name,
                    "langchain_available": _HAS_LANGCHAIN,
                },
            }
        )

    # LangChain callback surface (no-op useful if handler is attached).
    def on_chain_start(self, serialized: dict[str, Any], inputs: dict[str, Any], **kwargs: Any) -> None:
        self.gate("llm:invoke")


def governed_invoke(prompt: str, middleware: DctKillSwitchJsonlMiddleware | None = None) -> dict[str, Any]:
    """Run a mock (or real) invoke behind the middleware gate."""
    mw = middleware or DctKillSwitchJsonlMiddleware()
    decision = mw.gate("llm:invoke")
    if not decision.allowed:
        return {"status": "blocked", **asdict(decision)}

    # Minimal runnable: no network. Real ChatOpenAI wiring is out of scope here.
    output = f"[governed demo] {prompt[:200]}"
    return {
        "status": "ok",
        "output": output,
        "langchain_available": _HAS_LANGCHAIN,
        "alpha": True,
        "production_certified": False,
        **asdict(decision),
    }


def main() -> None:
    mw = DctKillSwitchJsonlMiddleware()
    print("=== allow path ===")
    print(json.dumps(governed_invoke("Summarize CONTRACT×DCT×EVIDENCE in one line.", mw), indent=2))

    print("=== kill-switch block path ===")
    mw.ks.engage(
        KillSwitchMode.HALT_ALL,
        reason="Demo halt",
        triggered_by="langchain_middleware_dct_demo",
    )
    print(json.dumps(governed_invoke("This should be blocked.", mw), indent=2))

    print(f"JSONL evidence: {mw.jsonl_path}")
    print("Assessor tip: python tools/assessor-v0/verify.py", mw.jsonl_path)


if __name__ == "__main__":
    main()
