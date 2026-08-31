#!/usr/bin/env python3
"""Validate a hummbl.io landing-page comprehension receipt.

Stdlib-only. Enforces the contract in
docs/research/landing-comprehension-test-protocol.md.

Usage:
    python tools/scripts/validate_landing_comprehension_receipt.py path/to/receipt.json

An UNRUN template with empty participants is valid preparation, not a
comprehension result (threshold_met is false). When five participant
records are present, every aggregate field and threshold_met is
recomputed from those records; client-supplied aggregates are not trusted.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

RECEIPT_TYPE = "landing-comprehension-test"
SCHEMA_VERSION = "1.0.0"
PROTOCOL_PATH = "docs/research/landing-comprehension-test-protocol.md"
TESTED_URL = "https://hummbl.io/"
STATUS_UNRUN = "UNRUN"

SCORE_KEYS = ("what", "why", "next", "guarantee", "evidence", "boundary")
RESPONSE_KEYS = ("q1", "q2", "q3", "q4", "q5", "q6")
AGGREGATE_KEYS = (
    "participants_total",
    "participants_scoring_at_least_9",
    "all_boundaries_at_least_1",
    "sensible_next_actions",
    "material_overclaim_detected",
    "threshold_met",
)
VIEWPORT_KEYS = ("width", "height", "first_view_seconds", "full_scan_seconds")
TOP_LEVEL_KEYS = (
    "receipt_type",
    "schema_version",
    "status",
    "protocol",
    "tested_url",
    "tested_sha",
    "tested_at",
    "viewport",
    "participants",
    "aggregate",
    "limitations",
)
EXPECTED_ROLE_COUNTS = {
    "builder": 2,
    "security-risk-compliance": 1,
    "technology-buyer": 1,
    "technical-generalist": 1,
}
ALLOWED_ROLES = frozenset(EXPECTED_ROLE_COUNTS)
PARTICIPANT_COUNT = 5
SCORE_PASS_MARK = 9
MIN_HIGH_SCORERS = 4
MIN_SENSIBLE_NEXT = 4
FIRST_VIEW_SECONDS = 20
FULL_SCAN_SECONDS = 180
SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")
ID_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


def is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def participant_score_total(scores: dict[str, Any]) -> int:
    return sum(int(scores[key]) for key in SCORE_KEYS)


def empty_aggregate() -> dict[str, Any]:
    """Aggregate for an UNRUN / empty-participant receipt.

    all_boundaries_at_least_1 is false: zero participants is not a
    comprehension result, so the vacuous all([])=True reading is rejected.
    """
    return {
        "participants_total": 0,
        "participants_scoring_at_least_9": 0,
        "all_boundaries_at_least_1": False,
        "sensible_next_actions": 0,
        "material_overclaim_detected": False,
        "threshold_met": False,
    }


def compute_aggregate(participants: list[dict[str, Any]]) -> dict[str, Any]:
    """Recompute aggregate fields from participant records."""
    if not participants:
        return empty_aggregate()

    scoring_at_least_9 = sum(
        1 for person in participants if participant_score_total(person["scores"]) >= SCORE_PASS_MARK
    )
    all_boundaries = all(person["scores"]["boundary"] >= 1 for person in participants)
    sensible = sum(1 for person in participants if person["sensible_next_action"] is True)
    any_overclaim = any(person["material_overclaim_detected"] is True for person in participants)
    threshold_met = (
        len(participants) == PARTICIPANT_COUNT
        and scoring_at_least_9 >= MIN_HIGH_SCORERS
        and all_boundaries
        and not any_overclaim
        and sensible >= MIN_SENSIBLE_NEXT
    )
    return {
        "participants_total": len(participants),
        "participants_scoring_at_least_9": scoring_at_least_9,
        "all_boundaries_at_least_1": all_boundaries,
        "sensible_next_actions": sensible,
        "material_overclaim_detected": any_overclaim,
        "threshold_met": threshold_met,
    }


def _issue(path: str, message: str) -> str:
    return f"{path}: {message}"


def _require_keys(obj: Any, keys: tuple[str, ...], path: str, issues: list[str]) -> bool:
    if not isinstance(obj, dict):
        issues.append(_issue(path, "must be an object"))
        return False
    missing = [key for key in keys if key not in obj]
    if missing:
        issues.append(_issue(path, f"missing field(s): {', '.join(missing)}"))
        return False
    return True


def _validate_viewport(viewport: Any, issues: list[str]) -> None:
    if not _require_keys(viewport, VIEWPORT_KEYS, "viewport", issues):
        return
    for key in VIEWPORT_KEYS:
        value = viewport[key]
        if not is_int(value) or value <= 0:
            issues.append(_issue(f"viewport.{key}", "must be a positive integer"))
    if is_int(viewport.get("first_view_seconds")) and viewport["first_view_seconds"] != FIRST_VIEW_SECONDS:
        issues.append(
            _issue(
                "viewport.first_view_seconds",
                f"must be {FIRST_VIEW_SECONDS} (protocol first-viewport duration)",
            )
        )
    if is_int(viewport.get("full_scan_seconds")) and viewport["full_scan_seconds"] != FULL_SCAN_SECONDS:
        issues.append(
            _issue(
                "viewport.full_scan_seconds",
                f"must be {FULL_SCAN_SECONDS} (protocol full-scan duration)",
            )
        )


def _validate_tested_fields(data: dict[str, Any], n_participants: int, issues: list[str]) -> None:
    if data.get("tested_url") != TESTED_URL:
        issues.append(_issue("tested_url", f"must be {TESTED_URL!r}"))

    sha = data.get("tested_sha")
    tested_at = data.get("tested_at")
    if n_participants == 0:
        if sha is not None:
            issues.append(_issue("tested_sha", "must be null on an UNRUN template"))
        if tested_at is not None:
            issues.append(_issue("tested_at", "must be null on an UNRUN template"))
        return

    if not isinstance(sha, str) or not SHA_RE.fullmatch(sha):
        issues.append(_issue("tested_sha", "must be a 40-character commit SHA"))
    if not isinstance(tested_at, str) or not tested_at.strip():
        issues.append(_issue("tested_at", "must be a non-empty UTC timestamp"))
        return
    try:
        datetime.fromisoformat(tested_at.replace("Z", "+00:00"))
    except ValueError:
        issues.append(_issue("tested_at", "must be an ISO-8601 timestamp"))


def _validate_scores(scores: Any, path: str, issues: list[str]) -> None:
    if not _require_keys(scores, SCORE_KEYS, path, issues):
        return
    extra = [key for key in scores if key not in SCORE_KEYS]
    if extra:
        issues.append(_issue(path, f"unexpected field(s): {', '.join(sorted(extra))}"))
    for key in SCORE_KEYS:
        value = scores[key]
        if not is_int(value) or value not in (0, 1, 2):
            issues.append(_issue(f"{path}.{key}", "must be an integer 0, 1, or 2"))


def _validate_responses(responses: Any, path: str, issues: list[str]) -> None:
    if not _require_keys(responses, RESPONSE_KEYS, path, issues):
        return
    for key in RESPONSE_KEYS:
        value = responses[key]
        if not isinstance(value, str):
            issues.append(_issue(f"{path}.{key}", "must be a string"))


def _validate_participant(person: Any, index: int, issues: list[str]) -> None:
    path = f"participants[{index}]"
    required = (
        "id",
        "role",
        "scores",
        "confidence",
        "sensible_next_action",
        "material_overclaim_detected",
        "responses",
    )
    if not _require_keys(person, required, path, issues):
        return

    ident = person["id"]
    if not isinstance(ident, str) or not ID_RE.fullmatch(ident):
        issues.append(
            _issue(
                f"{path}.id",
                "must be a 1–64 character anonymous id matching [A-Za-z0-9._-]+",
            )
        )

    role = person["role"]
    if role not in ALLOWED_ROLES:
        allowed = ", ".join(sorted(ALLOWED_ROLES))
        issues.append(_issue(f"{path}.role", f"must be one of: {allowed}"))

    _validate_scores(person["scores"], f"{path}.scores", issues)

    confidence = person["confidence"]
    if not is_int(confidence) or confidence < 1 or confidence > 5:
        issues.append(_issue(f"{path}.confidence", "must be an integer from 1 to 5"))

    if not isinstance(person["sensible_next_action"], bool):
        issues.append(_issue(f"{path}.sensible_next_action", "must be a boolean"))
    if not isinstance(person["material_overclaim_detected"], bool):
        issues.append(_issue(f"{path}.material_overclaim_detected", "must be a boolean"))

    _validate_responses(person["responses"], f"{path}.responses", issues)


def _validate_participants(participants: Any, issues: list[str]) -> list[dict[str, Any]]:
    if not isinstance(participants, list):
        issues.append(_issue("participants", "must be an array"))
        return []

    n = len(participants)
    if n not in (0, PARTICIPANT_COUNT):
        issues.append(
            _issue(
                "participants",
                f"must be empty (UNRUN preparation) or contain exactly {PARTICIPANT_COUNT} records",
            )
        )

    valid_people: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for index, person in enumerate(participants):
        before = len(issues)
        _validate_participant(person, index, issues)
        if len(issues) != before or not isinstance(person, dict):
            continue
        ident = person["id"]
        if ident in seen_ids:
            issues.append(_issue(f"participants[{index}].id", f"duplicate id {ident!r}"))
        else:
            seen_ids.add(ident)
        valid_people.append(person)

    if n == PARTICIPANT_COUNT and len(valid_people) == PARTICIPANT_COUNT:
        counts = Counter(person["role"] for person in valid_people)
        if dict(counts) != EXPECTED_ROLE_COUNTS:
            expected = ", ".join(f"{count}× {role}" for role, count in EXPECTED_ROLE_COUNTS.items())
            got = ", ".join(f"{count}× {role}" for role, count in sorted(counts.items()))
            issues.append(_issue("participants", f"expected role mix {expected}; got {got}"))

    return valid_people


def _validate_aggregate(stored: Any, computed: dict[str, Any], issues: list[str]) -> None:
    if not _require_keys(stored, AGGREGATE_KEYS, "aggregate", issues):
        return
    extra = [key for key in stored if key not in AGGREGATE_KEYS]
    if extra:
        issues.append(_issue("aggregate", f"unexpected field(s): {', '.join(sorted(extra))}"))
    for key in AGGREGATE_KEYS:
        if stored.get(key) != computed[key]:
            issues.append(
                _issue(
                    f"aggregate.{key}",
                    f"does not match recomputed value {computed[key]!r} (got {stored.get(key)!r})",
                )
            )


def _validate_limitations(limitations: Any, issues: list[str]) -> None:
    if not isinstance(limitations, list):
        issues.append(_issue("limitations", "must be an array of strings"))
        return
    if not limitations:
        issues.append(_issue("limitations", "must contain at least one string"))
        return
    for index, item in enumerate(limitations):
        if not isinstance(item, str) or not item.strip():
            issues.append(_issue(f"limitations[{index}]", "must be a non-empty string"))


def validate_receipt(data: Any) -> tuple[list[str], dict[str, Any] | None, str]:
    """Validate a loaded receipt object.

    Returns (issues, computed_aggregate_or_None, mode) where mode is
    "unrun", "complete", or "invalid".
    """
    issues: list[str] = []
    if not isinstance(data, dict):
        return [_issue("$", "receipt must be a JSON object")], None, "invalid"

    if not _require_keys(data, TOP_LEVEL_KEYS, "$", issues):
        return issues, None, "invalid"

    if data.get("receipt_type") != RECEIPT_TYPE:
        issues.append(_issue("receipt_type", f"must be {RECEIPT_TYPE!r}"))
    if data.get("schema_version") != SCHEMA_VERSION:
        issues.append(_issue("schema_version", f"must be {SCHEMA_VERSION!r}"))
    if data.get("protocol") != PROTOCOL_PATH:
        issues.append(_issue("protocol", f"must be {PROTOCOL_PATH!r}"))

    status = data.get("status")
    if not isinstance(status, str) or not status.strip():
        issues.append(_issue("status", "must be a non-empty string"))
        status = ""

    participants = data.get("participants")
    n = len(participants) if isinstance(participants, list) else -1
    if status == STATUS_UNRUN and n > 0:
        issues.append(_issue("status", "UNRUN is valid only with empty participants"))
    elif n == 0 and status and status != STATUS_UNRUN:
        issues.append(_issue("status", "an empty-participant receipt must use status UNRUN"))

    _validate_viewport(data.get("viewport"), issues)
    _validate_tested_fields(data, max(n, 0) if n != -1 else 0, issues)
    _validate_limitations(data.get("limitations"), issues)

    valid_people = _validate_participants(participants, issues)

    computed: dict[str, Any] | None
    if n == 0:
        computed = empty_aggregate()
        mode = "unrun"
    elif n == PARTICIPANT_COUNT and len(valid_people) == PARTICIPANT_COUNT:
        try:
            computed = compute_aggregate(valid_people)
        except (KeyError, TypeError, ValueError) as exc:
            issues.append(_issue("participants", f"cannot recompute aggregate: {exc}"))
            computed = None
            mode = "invalid"
        else:
            mode = "complete"
    else:
        computed = None
        mode = "invalid"

    if computed is not None:
        _validate_aggregate(data.get("aggregate"), computed, issues)

    return issues, computed, mode


def format_report(issues: list[str], computed: dict[str, Any] | None, mode: str) -> str:
    lines: list[str] = []
    if issues:
        for issue in issues:
            lines.append(f"[FAIL] {issue}")
        lines.append("")
        lines.append(f"Summary: {len(issues)} FAIL")
        lines.append("Exit: 1 (invalid receipt)")
        if computed is not None:
            lines.append("Recomputed aggregate (not trusted from the file):")
            lines.append(json.dumps(computed, indent=2))
        return "\n".join(lines)

    if mode == "unrun":
        lines.append("OK: UNRUN preparation receipt (not a comprehension result)")
    else:
        lines.append("OK: five-participant receipt")
    if computed is not None:
        lines.append(f"threshold_met: {str(computed['threshold_met']).lower()}")
        lines.append("recomputed aggregate:")
        lines.append(json.dumps(computed, indent=2))
    lines.append("Exit: 0 (valid receipt)")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate a hummbl.io landing-page comprehension receipt."
    )
    parser.add_argument("receipt", type=Path, help="Path to a receipt JSON file")
    args = parser.parse_args(argv)

    path: Path = args.receipt
    if not path.is_file():
        print(f"[FAIL] {path}: file not found", file=sys.stderr)
        return 1
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"[FAIL] {path}: invalid JSON: {exc}", file=sys.stderr)
        return 1

    issues, computed, mode = validate_receipt(data)
    print(format_report(issues, computed, mode))
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
