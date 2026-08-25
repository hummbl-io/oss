"""Execution receipts for Sigil Forge runs."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from hummbl_cognition.sigil_forge.ir import ExecutionPlan


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def stable_hash(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ExecutionReceipt:
    timestamp: str
    source: str
    plan: dict[str, Any]
    audit: list[dict[str, Any]]
    metrics: dict[str, Any]
    outputs: dict[str, str]
    output_hash: str
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "audit": self.audit,
            "metrics": self.metrics,
            "output_hash": self.output_hash,
            "outputs": self.outputs,
            "plan": self.plan,
            "source": self.source,
            "timestamp": self.timestamp,
        }
        if self.error is not None:
            payload["error"] = self.error
        payload["receipt_hash"] = stable_hash(payload)
        return payload

    def to_jsonl(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))


class ExecutionReceiptWriter:
    """Append execution receipts to JSONL."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    def write(self, receipt: ExecutionReceipt) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(receipt.to_jsonl() + "\n")


def build_receipt(
    *,
    plan: ExecutionPlan,
    audit: list[dict[str, Any]],
    metrics: dict[str, Any],
    outputs: dict[str, str],
    error: str | None = None,
) -> ExecutionReceipt:
    return ExecutionReceipt(
        timestamp=utc_now(),
        source=plan.source,
        plan=plan.to_dict(),
        audit=list(audit),
        metrics=dict(metrics),
        outputs=dict(outputs),
        output_hash=stable_hash(outputs),
        error=error,
    )
