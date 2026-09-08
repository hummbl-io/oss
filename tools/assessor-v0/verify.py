#!/usr/bin/env python3
# Copyright 2026 HUMMBL, LLC
# SPDX-License-Identifier: Apache-2.0
"""Assessor Pack v0 — stdlib-only CONTRACT × DCT × EVIDENCE JSONL verifier.

Alpha demo. Not production-certified. Confers no compliance status.
Public C = CONTRACT (not Atlas Constitution).

Canon:
  - DOI 10.5281/zenodo.21957831 (Tuple v2.1)
  - docs/research/2026-08-23_governance-tuple-protocol-spec.md
  - packages/python/hummbl-tuples/schemas/{contract,dct,evidence}.schema.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

HEX64 = re.compile(r"^[a-f0-9]{64}$")

ENVELOPE_REQUIRED = (
    "tuple_type",
    "id",
    "time",
    "intent_id",
    "task_id",
    "tuple_data",
    "state",
    "drift",
    "tier",
    "agent",
    "tool",
)

PAYLOAD_REQUIRED: dict[str, tuple[str, ...]] = {
    "CONTRACT": ("objective", "allowed_tools", "outputs", "risk_tier"),
    "DCT": ("issuer", "subject", "ops_allowed"),
    "EVIDENCE": ("event",),
}

ALLOWED_STATES = frozenset({"ok", "blocked", "error"})


def _digest_line(obj: dict[str, Any]) -> str:
    """Assessor-local canonical digest (not a fleet ReceiptEngine signature)."""
    canonical = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _fail(errors: list[str], msg: str) -> None:
    errors.append(msg)


def assess_record(obj: Any, line_no: int, errors: list[str]) -> dict[str, Any] | None:
    if not isinstance(obj, dict):
        _fail(errors, f"L{line_no}: record must be a JSON object")
        return None

    for key in ENVELOPE_REQUIRED:
        if key not in obj:
            _fail(errors, f"L{line_no}: missing envelope field {key!r}")

    tuple_type = obj.get("tuple_type")
    if tuple_type not in PAYLOAD_REQUIRED:
        _fail(
            errors,
            f"L{line_no}: tuple_type must be one of {sorted(PAYLOAD_REQUIRED)}",
        )
        return None

    if obj.get("state") not in ALLOWED_STATES:
        _fail(errors, f"L{line_no}: state must be one of {sorted(ALLOWED_STATES)}")

    drift = obj.get("drift")
    if not isinstance(drift, (int, float)) or isinstance(drift, bool) or drift < 0:
        _fail(errors, f"L{line_no}: drift must be a number >= 0")

    tier = obj.get("tier")
    if type(tier) is not int or tier < 0:
        _fail(errors, f"L{line_no}: tier must be an integer >= 0")

    for key in ("id", "time", "intent_id", "task_id", "agent", "tool"):
        val = obj.get(key)
        if not isinstance(val, str) or not val:
            _fail(errors, f"L{line_no}: {key} must be a non-empty string")

    payload = obj.get("tuple_data")
    if not isinstance(payload, dict):
        _fail(errors, f"L{line_no}: tuple_data must be an object")
        return None

    for key in PAYLOAD_REQUIRED[tuple_type]:
        if key not in payload:
            _fail(
                errors,
                f"L{line_no}: {tuple_type} tuple_data missing required {key!r}",
            )

    if tuple_type == "CONTRACT":
        for list_key in ("allowed_tools", "outputs"):
            val = payload.get(list_key)
            if val is not None and (
                not isinstance(val, list) or not all(isinstance(x, str) for x in val)
            ):
                _fail(errors, f"L{line_no}: CONTRACT.{list_key} must be a string list")
    if tuple_type == "DCT":
        ops = payload.get("ops_allowed")
        if ops is not None and (
            not isinstance(ops, list) or not all(isinstance(x, str) for x in ops)
        ):
            _fail(errors, f"L{line_no}: DCT.ops_allowed must be a string list")

    prev = obj.get("previous_hash", None)
    if "previous_hash" in obj and prev is not None:
        if not isinstance(prev, str) or not HEX64.match(prev):
            _fail(
                errors,
                f"L{line_no}: previous_hash must be null or 64-char lowercase hex",
            )

    return obj


def assess_file(path: Path) -> list[str]:
    errors: list[str] = []
    if not path.is_file():
        return [f"fixture not found: {path}"]

    records: list[dict[str, Any]] = []
    prior_digest: str | None = None
    intent_tasks: dict[str, str] = {}
    seen_types: set[str] = set()

    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return ["fixture is empty"]

    for line_no, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            _fail(errors, f"L{line_no}: invalid JSON ({exc})")
            continue

        record = assess_record(obj, line_no, errors)
        if record is None:
            continue

        seen_types.add(record["tuple_type"])
        intent = record["intent_id"]
        task = record["task_id"]
        if intent in intent_tasks and intent_tasks[intent] != task:
            _fail(
                errors,
                f"L{line_no}: intent_id {intent!r} bound to conflicting task_ids",
            )
        intent_tasks[intent] = task

        prev = record.get("previous_hash", None)
        if prev is not None and prior_digest is not None and prev != prior_digest:
            _fail(
                errors,
                f"L{line_no}: previous_hash does not match assessor digest of prior record",
            )
        if prev is None and prior_digest is not None:
            # Allow a new genesis inside the same file, but note it.
            pass

        prior_digest = _digest_line(record)
        records.append(record)

    if not records:
        _fail(errors, "no tuple records found")

    missing = sorted(set(PAYLOAD_REQUIRED) - seen_types)
    if missing:
        _fail(
            errors,
            "fixture missing tuple types required for Assessor v0 pack: "
            + ", ".join(missing),
        )

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Assessor Pack v0: stdlib-only CONTRACT×DCT×EVIDENCE JSONL checks. "
            "Alpha demo; not production-certified."
        )
    )
    parser.add_argument(
        "fixture",
        nargs="?",
        default="fixtures/public/assessor_v0_sample.jsonl",
        help="Path to JSONL fixture (default: fixtures/public/assessor_v0_sample.jsonl)",
    )
    args = parser.parse_args(argv)

    errors = assess_file(Path(args.fixture))
    if errors:
        print("ASSESSOR v0: FAIL")
        for err in errors:
            print(f"  - {err}")
        print(
            "Boundary: structural/chain checks only. "
            "See tools/assessor-v0/WHAT_THIS_PROVES.md"
        )
        return 1

    print("ASSESSOR v0: PASS")
    print(f"  fixture: {args.fixture}")
    print("  checks: envelope, payload keys, state/drift/tier, previous_hash, intent binding")
    print("  proves: local JSONL discipline for CONTRACT×DCT×EVIDENCE (Alpha)")
    print("  does_not_prove: production use, compliance, live crypto authenticity")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
