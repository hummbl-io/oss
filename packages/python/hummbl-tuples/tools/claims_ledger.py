#!/usr/bin/env python3
"""Claims and evidence ledger for HUMMBL Typed Tuples.

Append-only JSONL ledger that tracks claims and their supporting/refuting
evidence across trust tiers (untrusted -> experimental -> validated ->
canonical). Each claim and evidence entry can be linked to EVIDENCE and
ATTEST tuples from the hummbl-tuples package, providing a lifecycle tracker
that sits alongside the tuple event stream.

Adapted from PSI's claims_ledger.py (commit 546188d). Key changes:
- Stages generalized to trust tiers (untrusted/experimental/validated/canonical)
- Gates generalized to review gates (propose/review/canonize)
- Added tuple cross-reference fields (evidence_tuple_ids, attest_tuple_id)
- Added to_evidence_tuple() / to_attest_tuple() conversion methods
- Removed PSI-specific path assumptions; ledger path is configurable

Schema (claim entry):
    {
        "id": "CLM-001",
        "timestamp": "2026-01-01T00:00:00Z",
        "trust_tier": "untrusted|experimental|validated|canonical",
        "claim": "assertion text",
        "claim_type": "hypothesis|observation|inference|conclusion",
        "source": "provenance reference",
        "evidence_ids": ["EV-001", ...],
        "review_gate": "none|propose|review|canonize",
        "gate_status": "n/a|candidate|approved|rejected",
        "confidence": "low|medium|high",
        "falsifier": "what would disprove this",
        "evidence_tuple_ids": ["<EVIDENCE tuple id>", ...],
        "attest_tuple_ids": ["<ATTEST tuple id>", ...],
        "tags": [...],
        "notes": "free text"
    }

Schema (evidence entry):
    {
        "id": "EV-001",
        "timestamp": "2026-01-01T00:00:00Z",
        "claim_id": "CLM-001",
        "evidence_type": "citation|test|observation|artifact|counter",
        "source": "where it came from",
        "supports": "true|false|partial",
        "grade": "A|B|C|D",
        "attest_tuple_id": "<ATTEST tuple id or null>",
        "notes": "free text"
    }
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Ledger path defaults to a file next to this tool, but can be overridden
# via --ledger-path or the CLAIMS_LEDGER_PATH environment variable.
DEFAULT_LEDGER_PATH = Path(__file__).resolve().parent / "claims_ledger.jsonl"

VALID_TRUST_TIERS = {"untrusted", "experimental", "validated", "canonical"}
VALID_CLAIM_TYPES = {"hypothesis", "observation", "inference", "conclusion"}
VALID_REVIEW_GATES = {"none", "propose", "review", "canonize"}
VALID_GATE_STATUSES = {"n/a", "candidate", "approved", "rejected"}
VALID_CONFIDENCE = {"low", "medium", "high"}
VALID_EVIDENCE_TYPES = {"citation", "test", "observation", "artifact", "counter"}
VALID_SUPPORTS = {"true", "false", "partial"}
VALID_GRADES = {"A", "B", "C", "D"}

CLAIM_PREFIX = "CLM-"
EVIDENCE_PREFIX = "EV-"

CLAIM_REQUIRED_FIELDS = {
    "id", "timestamp", "trust_tier", "claim", "claim_type", "source",
    "evidence_ids", "review_gate", "gate_status", "confidence", "tags",
}
CLAIM_OPTIONAL_FIELDS = {
    "falsifier", "evidence_tuple_ids", "attest_tuple_ids", "notes",
}
EVIDENCE_REQUIRED_FIELDS = {
    "id", "timestamp", "claim_id", "evidence_type", "source",
    "supports", "grade",
}
EVIDENCE_OPTIONAL_FIELDS = {
    "attest_tuple_id", "notes",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read_ledger(path: Path = DEFAULT_LEDGER_PATH) -> list[dict]:
    if not path.exists():
        return []
    entries: list[dict] = []
    for line_num, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), 1
    ):
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_num}: invalid JSON: {exc}") from exc
    return entries


def _next_id(entries: list[dict], prefix: str) -> str:
    max_num = 0
    for entry in entries:
        eid = entry.get("id", "")
        if eid.startswith(prefix):
            match = re.match(rf"{re.escape(prefix)}(\d+)", eid)
            if match:
                max_num = max(max_num, int(match.group(1)))
    return f"{prefix}{max_num + 1:03d}"


def _validate_claim(entry: dict) -> list[str]:
    errors: list[str] = []
    missing = CLAIM_REQUIRED_FIELDS - set(entry.keys())
    if missing:
        errors.append(
            f"claim {entry.get('id', '?')}: missing fields: {sorted(missing)}"
        )
    if entry.get("trust_tier") and entry["trust_tier"] not in VALID_TRUST_TIERS:
        errors.append(
            f"claim {entry['id']}: invalid trust_tier {entry['trust_tier']!r}"
        )
    if entry.get("claim_type") and entry["claim_type"] not in VALID_CLAIM_TYPES:
        errors.append(
            f"claim {entry['id']}: invalid claim_type {entry['claim_type']!r}"
        )
    if entry.get("review_gate") and entry["review_gate"] not in VALID_REVIEW_GATES:
        errors.append(
            f"claim {entry['id']}: invalid review_gate {entry['review_gate']!r}"
        )
    if (
        entry.get("gate_status")
        and entry["gate_status"] not in VALID_GATE_STATUSES
    ):
        errors.append(
            f"claim {entry['id']}: invalid gate_status {entry['gate_status']!r}"
        )
    if entry.get("confidence") and entry["confidence"] not in VALID_CONFIDENCE:
        errors.append(
            f"claim {entry['id']}: invalid confidence {entry['confidence']!r}"
        )
    if not entry.get("id", "").startswith(CLAIM_PREFIX):
        errors.append(
            f"claim {entry.get('id', '?')}: id must start with {CLAIM_PREFIX}"
        )
    if not entry.get("claim"):
        errors.append(f"claim {entry['id']}: claim text is empty")
    if not isinstance(entry.get("evidence_ids"), list):
        errors.append(f"claim {entry['id']}: evidence_ids must be a list")
    if not isinstance(entry.get("tags"), list):
        errors.append(f"claim {entry['id']}: tags must be a list")
    if not isinstance(entry.get("evidence_tuple_ids", []), list):
        errors.append(f"claim {entry['id']}: evidence_tuple_ids must be a list")
    if not isinstance(entry.get("attest_tuple_ids", []), list):
        errors.append(f"claim {entry['id']}: attest_tuple_ids must be a list")
    return errors


def _validate_evidence(entry: dict) -> list[str]:
    errors: list[str] = []
    missing = EVIDENCE_REQUIRED_FIELDS - set(entry.keys())
    if missing:
        errors.append(
            f"evidence {entry.get('id', '?')}: missing fields: {sorted(missing)}"
        )
    if (
        entry.get("evidence_type")
        and entry["evidence_type"] not in VALID_EVIDENCE_TYPES
    ):
        errors.append(
            f"evidence {entry['id']}: invalid evidence_type {entry['evidence_type']!r}"
        )
    if entry.get("supports") and entry["supports"] not in VALID_SUPPORTS:
        errors.append(
            f"evidence {entry['id']}: invalid supports {entry['supports']!r}"
        )
    if entry.get("grade") and entry["grade"] not in VALID_GRADES:
        errors.append(f"evidence {entry['id']}: invalid grade {entry['grade']!r}")
    if not entry.get("id", "").startswith(EVIDENCE_PREFIX):
        errors.append(
            f"evidence {entry.get('id', '?')}: id must start with {EVIDENCE_PREFIX}"
        )
    if not entry.get("claim_id"):
        errors.append(f"evidence {entry['id']}: claim_id is empty")
    return errors


def _append_entry(entry: dict, path: Path = DEFAULT_LEDGER_PATH) -> None:
    line = json.dumps(entry, ensure_ascii=False, sort_keys=False)
    with path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def _rewrite_ledger(entries: list[dict], path: Path = DEFAULT_LEDGER_PATH) -> None:
    """Rewrite the entire ledger file (used when updating backlinks)."""
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False, sort_keys=False) + "\n")
    tmp.replace(path)


def add_claim(
    claim: str,
    trust_tier: str,
    claim_type: str,
    source: str,
    confidence: str = "low",
    falsifier: str = "",
    review_gate: str = "none",
    gate_status: str = "n/a",
    evidence_tuple_ids: list[str] | None = None,
    attest_tuple_ids: list[str] | None = None,
    tags: list[str] | None = None,
    notes: str = "",
    path: Path = DEFAULT_LEDGER_PATH,
) -> dict:
    """Add a claim entry to the ledger. Returns the created entry."""
    if trust_tier not in VALID_TRUST_TIERS:
        raise ValueError(
            f"invalid trust_tier {trust_tier!r}; must be one of {sorted(VALID_TRUST_TIERS)}"
        )
    if claim_type not in VALID_CLAIM_TYPES:
        raise ValueError(f"invalid claim_type {claim_type!r}")
    if confidence not in VALID_CONFIDENCE:
        raise ValueError(f"invalid confidence {confidence!r}")
    if review_gate not in VALID_REVIEW_GATES:
        raise ValueError(f"invalid review_gate {review_gate!r}")
    if gate_status not in VALID_GATE_STATUSES:
        raise ValueError(f"invalid gate_status {gate_status!r}")

    entries = _read_ledger(path)
    claim_id = _next_id(entries, CLAIM_PREFIX)
    entry: dict[str, Any] = {
        "id": claim_id,
        "timestamp": _utc_now(),
        "trust_tier": trust_tier,
        "claim": claim,
        "claim_type": claim_type,
        "source": source,
        "evidence_ids": [],
        "review_gate": review_gate,
        "gate_status": gate_status,
        "confidence": confidence,
        "falsifier": falsifier,
        "evidence_tuple_ids": evidence_tuple_ids or [],
        "attest_tuple_ids": attest_tuple_ids or [],
        "tags": tags or [],
        "notes": notes,
    }
    errors = _validate_claim(entry)
    if errors:
        raise ValueError("; ".join(errors))
    _append_entry(entry, path)
    return entry


def add_evidence(
    claim_id: str,
    evidence_type: str,
    source: str,
    supports: str = "true",
    grade: str = "C",
    attest_tuple_id: str | None = None,
    notes: str = "",
    path: Path = DEFAULT_LEDGER_PATH,
) -> dict:
    """Add an evidence entry linked to a claim. Returns the created entry."""
    if evidence_type not in VALID_EVIDENCE_TYPES:
        raise ValueError(f"invalid evidence_type {evidence_type!r}")
    if supports not in VALID_SUPPORTS:
        raise ValueError(f"invalid supports {supports!r}")
    if grade not in VALID_GRADES:
        raise ValueError(f"invalid grade {grade!r}")

    entries = _read_ledger(path)
    claim_ids = {e["id"] for e in entries if e["id"].startswith(CLAIM_PREFIX)}
    if claim_id not in claim_ids:
        raise ValueError(f"claim {claim_id} not found in ledger")

    ev_id = _next_id(entries, EVIDENCE_PREFIX)
    entry: dict[str, Any] = {
        "id": ev_id,
        "timestamp": _utc_now(),
        "claim_id": claim_id,
        "evidence_type": evidence_type,
        "source": source,
        "supports": supports,
        "grade": grade,
        "attest_tuple_id": attest_tuple_id,
        "notes": notes,
    }
    errors = _validate_evidence(entry)
    if errors:
        raise ValueError("; ".join(errors))
    _append_entry(entry, path)

    # Backlink: update the claim's evidence_ids list
    for e in entries:
        if e["id"] == claim_id:
            e["evidence_ids"].append(ev_id)
            break
    _rewrite_ledger(entries + [entry], path)
    return entry


def link_evidence_tuple(
    claim_id: str,
    evidence_tuple_id: str,
    path: Path = DEFAULT_LEDGER_PATH,
) -> dict | None:
    """Link an EVIDENCE tuple ID to a claim. Returns the updated claim."""
    entries = _read_ledger(path)
    for e in entries:
        if e["id"] == claim_id:
            etids = e.get("evidence_tuple_ids", [])
            if evidence_tuple_id not in etids:
                etids.append(evidence_tuple_id)
                e["evidence_tuple_ids"] = etids
            _rewrite_ledger(entries, path)
            return e
    return None


def link_attest_tuple(
    claim_id: str,
    attest_tuple_id: str,
    path: Path = DEFAULT_LEDGER_PATH,
) -> dict | None:
    """Link an ATTEST tuple ID to a claim. Returns the updated claim."""
    entries = _read_ledger(path)
    for e in entries:
        if e["id"] == claim_id:
            atids = e.get("attest_tuple_ids", [])
            if attest_tuple_id not in atids:
                atids.append(attest_tuple_id)
                e["attest_tuple_ids"] = atids
            _rewrite_ledger(entries, path)
            return e
    return None


def query_claims(
    trust_tier: str | None = None,
    review_gate: str | None = None,
    gate_status: str | None = None,
    tags: list[str] | None = None,
    path: Path = DEFAULT_LEDGER_PATH,
) -> list[dict]:
    """Query claims by trust tier, review gate, gate status, or tags."""
    entries = _read_ledger(path)
    results: list[dict] = []
    for e in entries:
        if not e["id"].startswith(CLAIM_PREFIX):
            continue
        if trust_tier and e.get("trust_tier") != trust_tier:
            continue
        if review_gate and e.get("review_gate") != review_gate:
            continue
        if gate_status and e.get("gate_status") != gate_status:
            continue
        if tags:
            entry_tags = set(e.get("tags", []))
            if not set(tags).issubset(entry_tags):
                continue
        results.append(e)
    return results


def get_claim(claim_id: str, path: Path = DEFAULT_LEDGER_PATH) -> dict | None:
    """Get a single claim by ID, with its evidence attached."""
    entries = _read_ledger(path)
    claim = None
    evidence: list[dict] = []
    for e in entries:
        if e["id"] == claim_id:
            claim = e
        elif e.get("claim_id") == claim_id:
            evidence.append(e)
    if claim:
        claim = dict(claim)
        claim["_evidence"] = evidence
    return claim


def validate(path: Path = DEFAULT_LEDGER_PATH) -> list[str]:
    """Validate the ledger. Returns a list of error strings (empty = valid)."""
    if not path.exists():
        return []  # empty ledger is valid
    entries = _read_ledger(path)
    errors: list[str] = []
    seen_ids: set[str] = set()
    claim_ids: set[str] = set()
    for entry in entries:
        eid = entry.get("id", "")
        if eid in seen_ids:
            errors.append(f"duplicate id: {eid}")
            continue
        seen_ids.add(eid)
        if eid.startswith(CLAIM_PREFIX):
            claim_ids.add(eid)
            errors.extend(_validate_claim(entry))
        elif eid.startswith(EVIDENCE_PREFIX):
            errors.extend(_validate_evidence(entry))
        else:
            errors.append(f"unknown entry id prefix: {eid}")
    # Check evidence backlinks
    for entry in entries:
        if entry.get("id", "").startswith(EVIDENCE_PREFIX):
            cid = entry.get("claim_id", "")
            if cid not in claim_ids:
                errors.append(
                    f"evidence {entry['id']}: references unknown claim {cid}"
                )
    return errors


def stats(path: Path = DEFAULT_LEDGER_PATH) -> dict:
    """Return summary statistics about the ledger."""
    entries = _read_ledger(path)
    claims = [e for e in entries if e["id"].startswith(CLAIM_PREFIX)]
    evidence = [e for e in entries if e["id"].startswith(EVIDENCE_PREFIX)]
    by_tier: dict[str, int] = {}
    for c in claims:
        tier = c.get("trust_tier", "unknown")
        by_tier[tier] = by_tier.get(tier, 0) + 1
    by_gate_status: dict[str, int] = {}
    for c in claims:
        gs = c.get("gate_status", "n/a")
        by_gate_status[gs] = by_gate_status.get(gs, 0) + 1
    by_supports: dict[str, int] = {}
    for ev in evidence:
        s = ev.get("supports", "unknown")
        by_supports[s] = by_supports.get(s, 0) + 1
    linked_evidence_tuples = sum(
        1 for c in claims if c.get("evidence_tuple_ids")
    )
    linked_attest_tuples = sum(
        1 for c in claims if c.get("attest_tuple_ids")
    )
    return {
        "total_claims": len(claims),
        "total_evidence": len(evidence),
        "by_trust_tier": by_tier,
        "by_gate_status": by_gate_status,
        "by_evidence_supports": by_supports,
        "claims_with_evidence_tuples": linked_evidence_tuples,
        "claims_with_attest_tuples": linked_attest_tuples,
    }


def to_evidence_tuple(claim_id: str, path: Path = DEFAULT_LEDGER_PATH) -> dict:
    """Convert a claim to an EVIDENCE tuple dict (envelope + tuple_data).

    Returns a dict in the canonical hummbl-tuples envelope shape that can
    be passed to EvidenceTuple.from_dict(). The claim's assertion becomes
    the tuple_data.event, and the claim's metadata is mapped to the
    envelope fields.

    Raises ValueError if the claim is not found.
    """
    claim = get_claim(claim_id, path)
    if not claim:
        raise ValueError(f"claim {claim_id} not found in ledger")
    tier_map = {
        "untrusted": 0,
        "experimental": 1,
        "validated": 2,
        "canonical": 3,
    }
    return {
        "tuple_type": "EVIDENCE",
        "id": claim["id"],
        "time": claim["timestamp"],
        "state": "ok",
        "drift": 0.0,
        "tier": tier_map.get(claim.get("trust_tier", "untrusted"), 0),
        "agent": claim.get("source", ""),
        "tool": "claims_ledger",
        "intent_id": claim_id,
        "task_id": claim_id,
        "tuple_data": {
            "event": claim["claim"],
            "evidence_id": claim["id"],
        },
    }


def to_attest_tuple(
    claim_id: str,
    verifier_id: str,
    passed: bool,
    findings: list[str] | None = None,
    path: Path = DEFAULT_LEDGER_PATH,
) -> dict:
    """Convert a claim's evidence summary to an ATTEST tuple dict.

    Returns a dict in the canonical hummbl-tuples envelope shape that can
    be passed to AttestTuple.from_dict(). The evidence hash is computed
    from the claim's evidence entries (SHA-256 of their concatenated JSON).

    Raises ValueError if the claim is not found.
    """
    import hashlib

    claim = get_claim(claim_id, path)
    if not claim:
        raise ValueError(f"claim {claim_id} not found in ledger")

    evidence = claim.get("_evidence", [])
    evidence_json = json.dumps(evidence, sort_keys=True, ensure_ascii=False)
    evidence_hash = hashlib.sha256(evidence_json.encode("utf-8")).hexdigest()

    tier_map = {
        "untrusted": 0,
        "experimental": 1,
        "validated": 2,
        "canonical": 3,
    }
    return {
        "tuple_type": "ATTEST",
        "id": f"ATTEST-{claim_id}",
        "time": _utc_now(),
        "state": "ok",
        "drift": 0.0,
        "tier": tier_map.get(claim.get("trust_tier", "untrusted"), 0),
        "agent": verifier_id,
        "tool": "claims_ledger",
        "intent_id": claim_id,
        "task_id": claim_id,
        "tuple_data": {
            "event": f"attest {claim_id}",
            "evidence_hash": evidence_hash,
            "verifier_id": verifier_id,
            "passed": passed,
            "findings": findings or [],
        },
    }


def _format_claim(claim: dict, show_evidence: bool = False) -> str:
    lines = [
        f"[{claim['id']}] {claim['claim']}",
        f"  tier: {claim['trust_tier']}  type: {claim['claim_type']}  "
        f"confidence: {claim['confidence']}",
        f"  gate: {claim['review_gate']} ({claim['gate_status']})  "
        f"source: {claim['source']}",
    ]
    if claim.get("falsifier"):
        lines.append(f"  falsifier: {claim['falsifier']}")
    if claim.get("evidence_tuple_ids"):
        lines.append(
            f"  evidence_tuples: {', '.join(claim['evidence_tuple_ids'])}"
        )
    if claim.get("attest_tuple_ids"):
        lines.append(
            f"  attest_tuples: {', '.join(claim['attest_tuple_ids'])}"
        )
    if claim.get("tags"):
        lines.append(f"  tags: {', '.join(claim['tags'])}")
    if claim.get("notes"):
        lines.append(f"  notes: {claim['notes']}")
    if show_evidence and claim.get("_evidence"):
        lines.append(f"  evidence ({len(claim['_evidence'])}):")
        for ev in claim["_evidence"]:
            attest_ref = ev.get("attest_tuple_id")
            attest_str = f" attest={attest_ref}" if attest_ref else ""
            lines.append(
                f"    [{ev['id']}] {ev['evidence_type']} "
                f"supports={ev['supports']} grade={ev['grade']}{attest_str}"
                f"  {ev['source']}"
            )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Claims and evidence ledger for HUMMBL Typed Tuples"
    )
    parser.add_argument(
        "--ledger-path",
        type=Path,
        default=DEFAULT_LEDGER_PATH,
        help="Path to the JSONL ledger file",
    )
    sub = parser.add_subparsers(dest="command")

    add_c = sub.add_parser("add-claim", help="Add a claim to the ledger")
    add_c.add_argument("--claim", required=True)
    add_c.add_argument(
        "--trust-tier",
        required=True,
        choices=sorted(VALID_TRUST_TIERS),
        dest="trust_tier",
    )
    add_c.add_argument(
        "--type",
        required=True,
        choices=sorted(VALID_CLAIM_TYPES),
        dest="claim_type",
    )
    add_c.add_argument("--source", required=True)
    add_c.add_argument(
        "--confidence", default="low", choices=sorted(VALID_CONFIDENCE)
    )
    add_c.add_argument("--falsifier", default="")
    add_c.add_argument(
        "--review-gate",
        default="none",
        choices=sorted(VALID_REVIEW_GATES),
        dest="review_gate",
    )
    add_c.add_argument(
        "--gate-status",
        default="n/a",
        choices=sorted(VALID_GATE_STATUSES),
        dest="gate_status",
    )
    add_c.add_argument("--evidence-tuple-ids", nargs="*", default=[], dest="evidence_tuple_ids")
    add_c.add_argument("--attest-tuple-ids", nargs="*", default=[], dest="attest_tuple_ids")
    add_c.add_argument("--tags", nargs="*", default=[])
    add_c.add_argument("--notes", default="")

    add_e = sub.add_parser("add-evidence", help="Add evidence for a claim")
    add_e.add_argument("--claim-id", required=True, dest="claim_id")
    add_e.add_argument(
        "--type",
        required=True,
        choices=sorted(VALID_EVIDENCE_TYPES),
        dest="evidence_type",
    )
    add_e.add_argument("--source", required=True)
    add_e.add_argument(
        "--supports", default="true", choices=sorted(VALID_SUPPORTS)
    )
    add_e.add_argument("--grade", default="C", choices=sorted(VALID_GRADES))
    add_e.add_argument("--attest-tuple-id", default=None, dest="attest_tuple_id")
    add_e.add_argument("--notes", default="")

    link_et = sub.add_parser(
        "link-evidence-tuple", help="Link an EVIDENCE tuple ID to a claim"
    )
    link_et.add_argument("--claim-id", required=True, dest="claim_id")
    link_et.add_argument(
        "--evidence-tuple-id", required=True, dest="evidence_tuple_id"
    )

    link_at = sub.add_parser(
        "link-attest-tuple", help="Link an ATTEST tuple ID to a claim"
    )
    link_at.add_argument("--claim-id", required=True, dest="claim_id")
    link_at.add_argument("--attest-tuple-id", required=True, dest="attest_tuple_id")

    sub.add_parser("validate", help="Validate the ledger")
    sub.add_parser("stats", help="Show ledger statistics")

    q = sub.add_parser("query", help="Query claims")
    q.add_argument("--trust-tier", choices=sorted(VALID_TRUST_TIERS), dest="trust_tier")
    q.add_argument("--review-gate", choices=sorted(VALID_REVIEW_GATES), dest="review_gate")
    q.add_argument(
        "--gate-status", choices=sorted(VALID_GATE_STATUSES), dest="gate_status"
    )
    q.add_argument("--tags", nargs="*")

    g = sub.add_parser("get", help="Get a single claim with evidence")
    g.add_argument("claim_id")

    conv_e = sub.add_parser(
        "to-evidence-tuple", help="Convert a claim to an EVIDENCE tuple dict"
    )
    conv_e.add_argument("claim_id")

    conv_a = sub.add_parser(
        "to-attest-tuple", help="Convert a claim's evidence to an ATTEST tuple dict"
    )
    conv_a.add_argument("claim_id")
    conv_a.add_argument("--verifier-id", required=True, dest="verifier_id")
    conv_a.add_argument("--passed", action="store_true")
    conv_a.add_argument("--findings", nargs="*", default=[])

    args = parser.parse_args()
    ledger_path: Path = args.ledger_path

    if args.command == "add-claim":
        entry = add_claim(
            claim=args.claim,
            trust_tier=args.trust_tier,
            claim_type=args.claim_type,
            source=args.source,
            confidence=args.confidence,
            falsifier=args.falsifier,
            review_gate=args.review_gate,
            gate_status=args.gate_status,
            evidence_tuple_ids=args.evidence_tuple_ids,
            attest_tuple_ids=args.attest_tuple_ids,
            tags=args.tags,
            notes=args.notes,
            path=ledger_path,
        )
        print(f"Added claim {entry['id']}: {entry['claim']}")
        return 0

    if args.command == "add-evidence":
        entry = add_evidence(
            claim_id=args.claim_id,
            evidence_type=args.evidence_type,
            source=args.source,
            supports=args.supports,
            grade=args.grade,
            attest_tuple_id=args.attest_tuple_id,
            notes=args.notes,
            path=ledger_path,
        )
        print(f"Added evidence {entry['id']} for claim {entry['claim_id']}")
        return 0

    if args.command == "link-evidence-tuple":
        updated = link_evidence_tuple(
            args.claim_id, args.evidence_tuple_id, path=ledger_path
        )
        if updated:
            print(f"Linked EVIDENCE tuple {args.evidence_tuple_id} to claim {args.claim_id}")
            return 0
        print(f"Claim {args.claim_id} not found", file=sys.stderr)
        return 1

    if args.command == "link-attest-tuple":
        updated = link_attest_tuple(
            args.claim_id, args.attest_tuple_id, path=ledger_path
        )
        if updated:
            print(f"Linked ATTEST tuple {args.attest_tuple_id} to claim {args.claim_id}")
            return 0
        print(f"Claim {args.claim_id} not found", file=sys.stderr)
        return 1

    if args.command == "validate":
        errors = validate(ledger_path)
        if errors:
            for err in errors:
                print(f"FAIL {err}", file=sys.stderr)
            return 1
        print("Claims ledger validation passed")
        return 0

    if args.command == "stats":
        s = stats(ledger_path)
        print(json.dumps(s, indent=2))
        return 0

    if args.command == "query":
        results = query_claims(
            trust_tier=args.trust_tier,
            review_gate=args.review_gate,
            gate_status=args.gate_status,
            tags=args.tags,
            path=ledger_path,
        )
        for c in results:
            print(_format_claim(c))
            print()
        print(f"({len(results)} claim{'s' if len(results) != 1 else ''})")
        return 0

    if args.command == "get":
        claim = get_claim(args.claim_id, path=ledger_path)
        if not claim:
            print(f"Claim {args.claim_id} not found", file=sys.stderr)
            return 1
        print(_format_claim(claim, show_evidence=True))
        return 0

    if args.command == "to-evidence-tuple":
        tup = to_evidence_tuple(args.claim_id, path=ledger_path)
        print(json.dumps(tup, indent=2))
        return 0

    if args.command == "to-attest-tuple":
        tup = to_attest_tuple(
            args.claim_id,
            verifier_id=args.verifier_id,
            passed=args.passed,
            findings=args.findings,
            path=ledger_path,
        )
        print(json.dumps(tup, indent=2))
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
