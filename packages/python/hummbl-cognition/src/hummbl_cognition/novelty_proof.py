"""NOVELTY_PROOF receipts -- bounded novelty claims as durable records.

A novelty claim is a negative existential ("nothing like this exists").
It cannot be proven absolutely -- only bounded: novel within corpus C
under metric M at distance D as of time T. This module assembles the
receipt from internal evidence (a novelty-check report) and caller-
attested external evidence (literature / market adversarial search),
grades it by corpus coverage, and can append it to the ledger as an
immutable record.

Semantics:

- Receipts are immutable once posted. A claim that later collapses is
  NOT edited; a `correction` ledger entry supersedes it, preserving the
  append-only audit trail.
- Grades reflect corpus coverage, not truth: A = internal + literature +
  market all searched; B = internal + literature; C = internal only.
  A C-grade receipt is honest about being a C-grade receipt.
- External evidence is caller-attested. This module does not run external
  searches; it records what was searched so coverage is auditable.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from hummbl_cognition.novelty_check import NoveltyReport
from hummbl_cognition.verified_writer import post_verified_entry

SCHEMA_VERSION = "novelty-proof.v0.1"

VALID_SCOPES = ("internal", "literature", "market")

_CAVEATS = {
    "internal_only": (
        "internal-only proof: no external adversarial search recorded -- "
        "the claim is unverified against literature and market prior art."
    ),
    "external_attested": (
        "external evidence is caller-attested: this receipt records the "
        "searches reported to it but does not independently re-run them."
    ),
    "decay": (
        "receipts decay: re-run the recorded falsification attempts before "
        "external reliance or after recheck_due."
    ),
    "collapse_path": (
        "if this claim collapses, post a correction entry superseding it -- "
        "do not edit or delete the original receipt."
    ),
}


def grade_for_scopes(scopes: Iterable[str]) -> str:
    """Coverage grade for a set of searched scopes.

    A = internal + literature + market; B = internal + literature;
    C = internal only; "ungraded" = anything else (e.g., no internal
    coverage, or market-only).
    """
    s = set(scopes)
    if {"internal", "literature", "market"} <= s:
        return "A"
    if {"internal", "literature"} <= s:
        return "B"
    if "internal" in s and s <= {"internal"}:
        return "C"
    return "ungraded"


def _normalize_evidence(item: dict[str, Any]) -> dict[str, Any]:
    """Normalize one external-evidence record to a stable shape."""
    return {
        "scope": str(item.get("scope", "unknown")),
        "source": str(item.get("source", "")),
        "query": str(item.get("query", "")),
        "nearest_ref": str(item.get("nearest_ref", "")),
        "note": str(item.get("note", "")),
    }


def build_novelty_proof(
    claim: str,
    *,
    falsifier: str,
    internal_report: NoveltyReport | dict[str, Any] | None = None,
    external_evidence: Iterable[dict[str, Any]] = (),
    falsification_attempts: Iterable[str] = (),
    recheck_due: str | None = None,
    checked_at: str | None = None,
    status: str = "standing",
) -> dict[str, Any]:
    """Assemble a NOVELTY_PROOF receipt.

    Parameters
    ----------
    claim : str
        The bounded novelty claim.
    falsifier : str
        What finding would kill this claim. Required -- a claim without a
        falsifier is not a receipt, it is an opinion.
    internal_report : NoveltyReport | dict | None
        A novelty-check report (object or its to_dict form) covering the
        internal corpus. None = internal scope not searched.
    external_evidence : iterable of dict
        Caller-attested external searches. Each item should carry scope
        ("literature" | "market"), source, query, nearest_ref, note.
    falsification_attempts : iterable of str
        The queries actually run against each scope -- recorded so the
        proof's coverage is replayable and auditable.
    recheck_due : str | None
        ISO date when this receipt should be re-verified (novelty decays).
    checked_at : str | None
        ISO timestamp (defaults to now, UTC Z).
    status : str
        "standing" for a live claim; "collapsed" is recorded only when
        transcribing an already-collapsed claim for audit.

    Returns
    -------
    dict
        The receipt, serializable to JSON.
    """
    if not falsifier or not falsifier.strip():
        raise ValueError("falsifier is required -- a novelty claim without "
                         "a falsifier is not a receipt")

    # Internal report may arrive as a NoveltyReport or a dict
    internal_dict: dict[str, Any] | None
    if internal_report is None:
        internal_dict = None
    elif isinstance(internal_report, NoveltyReport):
        internal_dict = internal_report.to_dict()
    else:
        internal_dict = dict(internal_report)

    evidence = [_normalize_evidence(e) for e in external_evidence]

    scopes: set[str] = set()
    if internal_dict is not None:
        scopes.add("internal")
    for e in evidence:
        if e["scope"] in VALID_SCOPES:
            scopes.add(e["scope"])

    grade = grade_for_scopes(scopes)

    caveats: list[str] = [_CAVEATS["decay"], _CAVEATS["collapse_path"]]
    if grade == "C" or grade == "ungraded":
        caveats.insert(0, _CAVEATS["internal_only"])
    if evidence:
        caveats.insert(0, _CAVEATS["external_attested"])
    if internal_dict is not None:
        caveats.extend(internal_dict.get("caveats", ()))

    attempts = [str(a) for a in falsification_attempts]

    return {
        "schema": SCHEMA_VERSION,
        "claim": claim,
        "corpus_scope": sorted(scopes),
        "grade": grade,
        "status": status,
        "falsifier": falsifier,
        "falsification_attempts": attempts,
        "internal": internal_dict,
        "external_evidence": evidence,
        "checked_at": checked_at
        or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "recheck_due": recheck_due,
        "caveats": caveats,
    }


def post_novelty_proof(
    receipt: dict[str, Any],
    *,
    agent: str,
    vendor: str,
    model: str,
    confidence: float = 0.5,
    ledger_path: str | Path | None = None,
):
    """Append a NOVELTY_PROOF receipt to the cognitive ledger.

    Posted as type=discovery / scope=project with a `novelty-proof` tag --
    the canonical type set is closed, and the schema field inside the
    content carries the receipt type. The receipt JSON is the entry
    content; the schema+grade is the evidence reference.

    confidence defaults to 0.5 and reflects coverage, not truth: raise it
    only when the grade and falsification coverage justify it.
    """
    if receipt.get("schema") != SCHEMA_VERSION:
        raise ValueError(f"receipt schema must be {SCHEMA_VERSION}")

    grade = receipt.get("grade", "ungraded")
    content = json.dumps(receipt, separators=(",", ":"), sort_keys=True)

    return post_verified_entry(
        agent=agent,
        vendor=vendor,
        model=model,
        entry_type="discovery",
        scope="project",
        content=content,
        evidence=f"{SCHEMA_VERSION} grade={grade}",
        confidence=confidence,
        tags=("novelty-proof", f"grade-{grade}"),
        ledger_path=ledger_path,
    )


def format_proof_text(receipt: dict[str, Any]) -> str:
    """Human-readable rendering for CLI output."""
    lines = [
        f"NOVELTY_PROOF | grade={receipt['grade']} | status={receipt['status']}"
        f" | checked_at={receipt['checked_at']}",
        f"Claim: {receipt['claim']}",
        f"Corpus scope: {', '.join(receipt['corpus_scope']) or 'none'}",
        f"Falsifier: {receipt['falsifier']}",
    ]
    if receipt.get("recheck_due"):
        lines.append(f"Recheck due: {receipt['recheck_due']}")

    internal = receipt.get("internal")
    if internal:
        top = internal.get("top_score")
        lines.append(
            f"Internal: top_score={top} "
            f"neighbors={len(internal.get('nearest_neighbors', []))} "
            f"unseen_terms={len(internal.get('unseen_terms', []))}"
        )
    else:
        lines.append("Internal: not searched")

    ext = receipt.get("external_evidence", [])
    if ext:
        lines.append(f"External evidence ({len(ext)}):")
        for e in ext:
            lines.append(f"  [{e['scope']}] {e['source']} :: {e['query']}")

    if receipt.get("falsification_attempts"):
        lines.append(f"Falsification attempts ({len(receipt['falsification_attempts'])}):")
        for a in receipt["falsification_attempts"]:
            lines.append(f"  - {a}")

    lines.append("Caveats:")
    for c in receipt.get("caveats", []):
        lines.append(f"  - {c}")
    return "\n".join(lines)
