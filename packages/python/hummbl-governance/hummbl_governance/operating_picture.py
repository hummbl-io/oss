"""Read-only internal operating-picture assembly.

The pilot consumes operator-provided snapshots.  It performs no network calls,
does not invoke subprocesses, and cannot authorize or execute external actions.
Source text is treated as untrusted data and is redacted or quarantined before
it reaches the generated situation or Markdown brief.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from hummbl_governance.schema_validator import SchemaValidator


SITUATION_VERSION = "situation.v0.2"
SOURCE_REGISTRY_VERSION = "source_registry.v0.1"
RETRIEVAL_RECEIPT_VERSION = "retrieval_receipt.v0.1"
TRANSFORM_VERSION = "internal-operating-picture.v0.1"
REQUIRED_SOURCE_IDS = ("coordination-bus", "github", "fleet-health")
MAX_SNAPSHOT_BYTES = 10 * 1024 * 1024
MAX_CLOCK_SKEW_SECONDS = 300

_INJECTION_PATTERNS = (
    re.compile(r"ignore\s+(?:all\s+)?previous", re.IGNORECASE),
    re.compile(r"^\s*(?:system|admin)\s*:", re.IGNORECASE | re.MULTILINE),
    re.compile(r"```\s*system", re.IGNORECASE),
    re.compile(r"\b(?:you\s+are\s+now|act\s+as|pretend\s+to\s+be)\b", re.IGNORECASE),
)
_REDACTIONS = (
    (
        re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
        "[REDACTED_EMAIL]",
        "email",
    ),
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[REDACTED_SSN]", "ssn"),
    (
        re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
        "[REDACTED_PHONE]",
        "phone",
    ),
    (
        re.compile(
            r"\b(password|passwd|api[_-]?key|access[_-]?token|token)\s*[:=]\s*[^\s,;]+",
            re.IGNORECASE,
        ),
        r"\1=[REDACTED_SECRET]",
        "secret",
    ),
)
_SAFE_IDENTIFIER = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


def _schema_path(name: str) -> Path:
    return Path(__file__).resolve().parent / "data" / name


def _load_schema(name: str) -> dict[str, Any]:
    return json.loads(_schema_path(name).read_text(encoding="utf-8"))


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _stable_id(prefix: str, value: Any) -> str:
    digest = hashlib.sha256(_canonical_json_bytes(value)).hexdigest()[:24]
    return f"{prefix}-{digest}"


def _parse_timestamp(value: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise ValueError("timestamp must be a non-empty string")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include a timezone")
    return parsed.astimezone(timezone.utc)


def _normalize_timestamp(value: str) -> str:
    return _parse_timestamp(value).isoformat(timespec="seconds").replace("+00:00", "Z")


def _freshness(observed_at: str, retrieved_at: str, threshold_seconds: int) -> str:
    age = (_parse_timestamp(retrieved_at) - _parse_timestamp(observed_at)).total_seconds()
    if age < -MAX_CLOCK_SKEW_SECONDS:
        raise ValueError("snapshot observed_at exceeds allowed future clock skew")
    return "FRESH" if age <= threshold_seconds else "STALE"


def _safe_identifier(value: Any, *, prefix: str) -> str:
    text = str(value)
    if _SAFE_IDENTIFIER.fullmatch(text):
        return text
    return _stable_id(prefix, text)


def _sanitize_text(value: Any) -> tuple[str, list[str], bool]:
    text = str(value)
    if any(pattern.search(text) for pattern in _INJECTION_PATTERNS):
        return "[QUARANTINED_UNTRUSTED_TEXT]", ["prompt_injection"], True

    redactions: list[str] = []
    for pattern, replacement, label in _REDACTIONS:
        text, count = pattern.subn(replacement, text)
        if count:
            redactions.append(label)
    return text, sorted(set(redactions)), False


def _normalize_record(raw: dict[str, Any], fallback_observed_at: str) -> dict[str, Any]:
    required = ("subject", "predicate", "value")
    missing = [field for field in required if field not in raw]
    if missing:
        raise ValueError(f"record missing required fields: {', '.join(missing)}")

    raw_record_id = raw.get("record_id") or _stable_id("record", raw)
    record_id = _safe_identifier(raw_record_id, prefix="record")
    observed_at = _normalize_timestamp(str(raw.get("observed_at", fallback_observed_at)))

    fields: dict[str, str] = {}
    redactions: set[str] = set()
    quarantined = False
    for field in ("subject", "predicate", "value", "summary"):
        default = raw["value"] if field == "summary" else ""
        sanitized, found, field_quarantined = _sanitize_text(raw.get(field, default))
        fields[field] = sanitized
        redactions.update(found)
        quarantined = quarantined or field_quarantined

    if quarantined:
        for field in fields:
            fields[field] = "[QUARANTINED_UNTRUSTED_TEXT]"

    return {
        "record_id": record_id,
        "subject": fields["subject"],
        "predicate": fields["predicate"],
        "value": fields["value"],
        "summary": fields["summary"],
        "observed_at": observed_at,
        "quarantined": quarantined,
        "redactions": sorted(redactions),
    }


def _resanitize_record(raw: dict[str, Any], fallback_observed_at: str) -> dict[str, Any]:
    """Reapply trust-boundary controls to caller-supplied observations."""
    record = _normalize_record(raw, fallback_observed_at)
    inherited = raw.get("redactions", [])
    if isinstance(inherited, list):
        record["redactions"] = sorted(
            set(record["redactions"]) | {str(item) for item in inherited}
        )
    if raw.get("quarantined") is True:
        record["quarantined"] = True
        for field in ("subject", "predicate", "value", "summary"):
            record[field] = "[QUARANTINED_UNTRUSTED_TEXT]"
    return record


def _build_receipt(
    *,
    source_id: str,
    retrieved_at: str,
    content_sha256: str | None,
    result: str,
    error: str | None,
) -> dict[str, Any]:
    body = {
        "schema_version": RETRIEVAL_RECEIPT_VERSION,
        "source_id": source_id,
        "retrieved_at": _normalize_timestamp(retrieved_at),
        "content_sha256": content_sha256,
        "transform_version": TRANSFORM_VERSION,
        "result": result,
        "error": error,
        "mutation_authority": "NONE",
    }
    return {"receipt_id": _stable_id("retrieval", body), **body}


def _failure(
    spec: dict[str, Any],
    *,
    retrieved_at: str,
    result: str,
    content_sha256: str | None,
    error: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    receipt = _build_receipt(
        source_id=spec["source_id"],
        retrieved_at=retrieved_at,
        content_sha256=content_sha256,
        result=result,
        error=error,
    )
    observation = {
        "source_id": spec["source_id"],
        "retrieved_at": _normalize_timestamp(retrieved_at),
        "observed_at": None,
        "freshness": result,
        "upstream_group": spec["upstream_group"],
        "records": [],
        "retrieval_receipt_id": receipt["receipt_id"],
        "errors": [error],
    }
    return observation, receipt


def _read_snapshot(
    path: str | Path,
    spec: dict[str, Any],
    *,
    retrieved_at: str,
    parser: Callable[[bytes], tuple[str, list[dict[str, Any]]]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    snapshot_path = Path(path)
    if not snapshot_path.is_file():
        return _failure(
            spec,
            retrieved_at=retrieved_at,
            result="MISSING",
            content_sha256=None,
            error="snapshot file is missing",
        )

    try:
        snapshot_size = snapshot_path.stat().st_size
    except OSError:
        return _failure(
            spec,
            retrieved_at=retrieved_at,
            result="ERROR",
            content_sha256=None,
            error="snapshot metadata could not be read",
        )
    if snapshot_size > MAX_SNAPSHOT_BYTES:
        return _failure(
            spec,
            retrieved_at=retrieved_at,
            result="ERROR",
            content_sha256=None,
            error=f"snapshot exceeds {MAX_SNAPSHOT_BYTES} byte safety limit",
        )

    try:
        raw_bytes = snapshot_path.read_bytes()
    except OSError:
        return _failure(
            spec,
            retrieved_at=retrieved_at,
            result="ERROR",
            content_sha256=None,
            error="snapshot content could not be read",
        )
    content_sha256 = _sha256_bytes(raw_bytes)
    try:
        observed_at, raw_records = parser(raw_bytes)
        normalized_observed_at = _normalize_timestamp(observed_at)
        records = [_normalize_record(record, normalized_observed_at) for record in raw_records]
        status = _freshness(
            normalized_observed_at,
            retrieved_at,
            int(spec["freshness_threshold_seconds"]),
        )
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        return _failure(
            spec,
            retrieved_at=retrieved_at,
            result="ERROR",
            content_sha256=content_sha256,
            error=f"snapshot parse failed: {type(exc).__name__}",
        )

    receipt = _build_receipt(
        source_id=spec["source_id"],
        retrieved_at=retrieved_at,
        content_sha256=content_sha256,
        result="SUCCESS",
        error=None,
    )
    observation = {
        "source_id": spec["source_id"],
        "retrieved_at": _normalize_timestamp(retrieved_at),
        "observed_at": normalized_observed_at,
        "freshness": status,
        "upstream_group": spec["upstream_group"],
        "records": records,
        "retrieval_receipt_id": receipt["receipt_id"],
        "errors": [],
    }
    return observation, receipt


def _parse_json_snapshot(raw_bytes: bytes) -> tuple[str, list[dict[str, Any]]]:
    payload = json.loads(raw_bytes.decode("utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("snapshot root must be an object")
    observed_at = payload.get("observed_at")
    records = payload.get("records")
    if not isinstance(observed_at, str):
        raise TypeError("snapshot observed_at must be a string")
    if not isinstance(records, list) or not all(isinstance(item, dict) for item in records):
        raise TypeError("snapshot records must be a list of objects")
    return observed_at, records


def _parse_bus_snapshot(raw_bytes: bytes) -> tuple[str, list[dict[str, Any]]]:
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(raw_bytes.decode("utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        fields = line.split("\t", 4)
        if len(fields) != 5:
            raise ValueError(f"bus line {line_number} does not have five TSV fields")
        timestamp, sender, recipient, message_type, message = fields
        records.append(
            {
                "record_id": _stable_id(
                    "bus",
                    [timestamp, sender, recipient, message_type, message],
                ),
                "subject": "pilot",
                "predicate": message_type,
                "value": message,
                "summary": f"{sender} to {recipient}: {message}",
                "observed_at": timestamp,
            }
        )
    if not records:
        raise ValueError("bus snapshot contains no records")
    observed_at = max(record["observed_at"] for record in records)
    return observed_at, records


def _validate_source_registry(registry: dict[str, Any]) -> dict[str, Any]:
    valid, errors = SchemaValidator.validate_dict(
        registry, _load_schema("source_registry_v0.1.schema.json")
    )
    if not valid:
        raise ValueError("invalid source registry: " + "; ".join(errors))
    source_ids = tuple(source["source_id"] for source in registry["sources"])
    if source_ids != REQUIRED_SOURCE_IDS:
        raise ValueError(f"source registry must contain exactly {REQUIRED_SOURCE_IDS!r} in order")
    return registry


def load_source_registry(path: str | Path) -> dict[str, Any]:
    """Load and validate the exact three-source read-only pilot registry."""
    registry = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(registry, dict):
        raise ValueError("source registry root must be an object")
    return _validate_source_registry(registry)


def read_bus_snapshot(
    path: str | Path,
    spec: dict[str, Any],
    *,
    retrieved_at: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Read a five-column coordination-bus TSV snapshot."""
    return _read_snapshot(path, spec, retrieved_at=retrieved_at, parser=_parse_bus_snapshot)


def read_github_snapshot(
    path: str | Path,
    spec: dict[str, Any],
    *,
    retrieved_at: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Read an operator-provided GitHub issue/PR/CI JSON snapshot."""
    return _read_snapshot(path, spec, retrieved_at=retrieved_at, parser=_parse_json_snapshot)


def read_fleet_health_snapshot(
    path: str | Path,
    spec: dict[str, Any],
    *,
    retrieved_at: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Read an operator-provided fleet-health JSON snapshot."""
    return _read_snapshot(path, spec, retrieved_at=retrieved_at, parser=_parse_json_snapshot)


def _source_gap(source_id: str, status: str, detail: str) -> dict[str, str]:
    return {
        "gap_id": _stable_id("gap", [source_id, status, detail]),
        "source_id": source_id,
        "kind": status,
        "detail": detail,
    }


def build_operating_picture(
    observations: list[dict[str, Any]],
    registry: dict[str, Any],
    *,
    as_of: str,
    created_by: str,
) -> dict[str, Any]:
    """Build a deterministic DRAFT situation from normalized observations."""
    registry = _validate_source_registry(registry)
    normalized_as_of = _normalize_timestamp(as_of)
    specs = {source["source_id"]: source for source in registry["sources"]}
    supplied: dict[str, dict[str, Any]] = {}
    for observation in observations:
        raw_source_id = observation.get("source_id")
        if not isinstance(raw_source_id, str) or raw_source_id not in specs:
            raise ValueError(f"observation has unregistered source_id: {raw_source_id!r}")
        source_id = raw_source_id
        if source_id in supplied:
            raise ValueError(f"duplicate observation for source_id: {source_id}")
        supplied[source_id] = observation

    sources: list[dict[str, Any]] = []
    gaps: list[dict[str, str]] = []
    evidence: list[dict[str, Any]] = []
    events: list[dict[str, str]] = []

    for source_id in REQUIRED_SOURCE_IDS:
        spec = specs[source_id]
        current_observation = supplied.get(source_id)
        if current_observation is None:
            sources.append(
                {
                    "source_id": source_id,
                    "freshness": "MISSING",
                    "observed_at": None,
                    "retrieved_at": None,
                    "upstream_group": spec["upstream_group"],
                    "retrieval_receipt_id": None,
                }
            )
            gaps.append(_source_gap(source_id, "MISSING", "No snapshot was supplied"))
            continue

        status = current_observation["freshness"]
        sources.append(
            {
                "source_id": source_id,
                "freshness": status,
                "observed_at": current_observation["observed_at"],
                "retrieved_at": current_observation["retrieved_at"],
                "upstream_group": current_observation["upstream_group"],
                "retrieval_receipt_id": current_observation["retrieval_receipt_id"],
            }
        )
        if status != "FRESH":
            detail = (
                current_observation["errors"][0]
                if current_observation["errors"]
                else f"Source is {status.lower()}"
            )
            gaps.append(_source_gap(source_id, status, detail))

        fallback_observed_at = current_observation["observed_at"] or normalized_as_of
        for raw_record in current_observation["records"]:
            record = _resanitize_record(raw_record, fallback_observed_at)
            evidence_id = _stable_id("evidence", [source_id, record["record_id"]])
            item = {
                "evidence_id": evidence_id,
                "source_id": source_id,
                "record_id": record["record_id"],
                "subject": record["subject"],
                "predicate": record["predicate"],
                "value": record["value"],
                "summary": record["summary"],
                "observed_at": record["observed_at"],
                "freshness": status,
                "upstream_group": current_observation["upstream_group"],
                "retrieval_receipt_id": current_observation["retrieval_receipt_id"],
                "quarantined": record["quarantined"],
                "redactions": record["redactions"],
            }
            evidence.append(item)
            events.append(
                {
                    "event_id": _stable_id("event", [evidence_id, record["observed_at"]]),
                    "event_type": record["predicate"],
                    "occurred_at": record["observed_at"],
                    "source_id": source_id,
                    "summary": record["summary"],
                    "evidence_ref": evidence_id,
                }
            )
            if record["quarantined"]:
                gaps.append(
                    _source_gap(
                        source_id,
                        "QUARANTINED",
                        f"Untrusted text quarantined in record {record['record_id']}",
                    )
                )

    available_sources = {
        source["source_id"] for source in sources if source["freshness"] in {"FRESH", "STALE"}
    }
    fresh_sources = {source["source_id"] for source in sources if source["freshness"] == "FRESH"}
    available_upstreams = {
        source["upstream_group"]
        for source in sources
        if source["source_id"] in available_sources
    }
    upstream_members: dict[str, list[str]] = defaultdict(list)
    for source in sources:
        if source["source_id"] in available_sources:
            upstream_members[source["upstream_group"]].append(source["source_id"])
    shared_upstreams = [
        {"upstream_group": group, "source_ids": sorted(members)}
        for group, members in sorted(upstream_members.items())
        if len(members) > 1
    ]

    evidence_groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for item in evidence:
        if not item["quarantined"]:
            evidence_groups[(item["subject"], item["predicate"])].append(item)

    claims: list[dict[str, Any]] = []
    contradictions: list[dict[str, Any]] = []
    total_sources = len(REQUIRED_SOURCE_IDS)
    coverage_ceiling = len(available_sources) / total_sources
    independence_ceiling = len(available_upstreams) / total_sources

    for (subject, predicate), items in sorted(evidence_groups.items()):
        values: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for item in items:
            values[item["value"]].append(item)
        contradicted = len(values) > 1
        if contradicted:
            contradictions.append(
                {
                    "contradiction_id": _stable_id(
                        "contradiction", [subject, predicate, sorted(values)]
                    ),
                    "subject": subject,
                    "predicate": predicate,
                    "values": sorted(values),
                    "evidence_refs": sorted(
                        item["evidence_id"] for group in values.values() for item in group
                    ),
                    "resolution_status": "UNRESOLVED",
                }
            )

        for value, supporting in sorted(values.items()):
            support_sources = {item["source_id"] for item in supporting}
            support_upstreams = {item["upstream_group"] for item in supporting}
            fresh_support = support_sources & fresh_sources
            confidence = min(
                len(support_sources) / total_sources,
                len(support_upstreams) / total_sources,
                len(fresh_support) / total_sources,
                coverage_ceiling,
                independence_ceiling,
                0.95,
            )
            if contradicted:
                confidence = min(confidence, 0.25)
            claims.append(
                {
                    "claim_id": _stable_id("claim", [subject, predicate, value]),
                    "subject": subject,
                    "predicate": predicate,
                    "value": value,
                    "confidence": round(confidence, 6),
                    "source_ids": sorted(support_sources),
                    "upstream_groups": sorted(support_upstreams),
                    "evidence_refs": sorted(item["evidence_id"] for item in supporting),
                    "contradicted": contradicted,
                }
            )

    overall_confidence = (
        sum(claim["confidence"] for claim in claims) / len(claims) if claims else 0.0
    )
    overall_confidence = min(overall_confidence, coverage_ceiling, independence_ceiling)

    recommendations: list[str] = []
    if contradictions:
        recommendations.append("Resolve contradictory claims before operational reliance.")
    if gaps:
        recommendations.append("Refresh or restore sources marked as gaps before publication.")
    if not recommendations:
        recommendations.append("Have Reuben review the draft before any publication decision.")

    body: dict[str, Any] = {
        "schema_version": SITUATION_VERSION,
        "created_at": normalized_as_of,
        "as_of": normalized_as_of,
        "created_by": created_by,
        "lifecycle": "DRAFT",
        "resolution_status": "UNRESOLVED",
        "title": "HUMMBL internal operating picture pilot",
        "governance": {
            "mutation_authority": "NONE",
            "publication_status": "DRAFT",
            "requires_human_review": True,
            "reviewer": "Reuben",
            "privacy_class": "INTERNAL",
            "prohibited_actions": [
                "account_action",
                "deployment",
                "external_message",
                "issue_or_pull_request_mutation",
                "process_restart",
            ],
        },
        "sources": sources,
        "source_independence": {
            "registered_sources": total_sources,
            "available_sources": len(available_sources),
            "independent_upstreams": len(available_upstreams),
            "shared_upstream_groups": shared_upstreams,
        },
        "claims": claims,
        "evidence": evidence,
        "events": events,
        "contradictions": contradictions,
        "gaps": gaps,
        "confidence": {
            "overall": round(overall_confidence, 6),
            "coverage_ceiling": coverage_ceiling,
            "independence_ceiling": independence_ceiling,
            "method": "minimum of claim support, freshness, coverage, and independent upstream ceilings",
        },
        "decision_layers": {
            "recommendations": recommendations,
            "authorizations": [],
            "actions": [],
            "verification": {"status": "NOT_RUN", "receipt_refs": []},
        },
    }
    return {"situation_id": _stable_id("situation", body), **body}


def render_markdown(situation: dict[str, Any]) -> str:
    """Render a review-oriented Markdown brief without raw source payloads."""
    lines = [
        "# DRAFT — HUMAN REVIEW REQUIRED",
        "",
        f"## {situation['title']}",
        "",
        f"- Situation ID: `{situation['situation_id']}`",
        f"- As of: `{situation['as_of']}`",
        f"- Overall confidence: `{situation['confidence']['overall']:.3f}`",
        "- No mutation authority; this artifact cannot authorize or execute actions.",
        "",
        "## Sources",
        "",
        "| Source | Freshness | Upstream |",
        "|---|---|---|",
    ]
    for source in situation["sources"]:
        lines.append(
            f"| {source['source_id']} | {source['freshness']} | {source['upstream_group']} |"
        )

    lines.extend(["", "## Claims", ""])
    if situation["claims"]:
        for claim in situation["claims"]:
            marker = "contradicted" if claim["contradicted"] else "uncontradicted"
            lines.append(
                f"- `{claim['subject']} / {claim['predicate']}` = `{claim['value']}` "
                f"(confidence {claim['confidence']:.3f}; {marker})"
            )
    else:
        lines.append("- No supported claims.")

    lines.extend(["", "## Contradictions", ""])
    if situation["contradictions"]:
        for item in situation["contradictions"]:
            lines.append(
                f"- `{item['subject']} / {item['predicate']}` has unresolved values: "
                + ", ".join(f"`{value}`" for value in item["values"])
            )
    else:
        lines.append("- None detected.")

    lines.extend(["", "## Gaps", ""])
    if situation["gaps"]:
        for gap in situation["gaps"]:
            lines.append(f"- `{gap['source_id']}` — {gap['kind']}: {gap['detail']}")
    else:
        lines.append("- None detected.")

    lines.extend(["", "## Recommendations", ""])
    lines.extend(f"- {item}" for item in situation["decision_layers"]["recommendations"])
    lines.extend(
        [
            "",
            "## Decision boundary",
            "",
            "Authorizations: none. Actions: none. Verification: not run.",
            "Reuben must review this draft before any publication decision.",
            "",
        ]
    )
    return "\n".join(lines)


def write_draft_outputs(
    situation: dict[str, Any],
    receipts: list[dict[str, Any]],
    output_dir: str | Path,
) -> dict[str, Path]:
    """Write the DRAFT JSON, Markdown brief, and retrieval receipt bundle."""
    valid, errors = SchemaValidator.validate_dict(
        situation, _load_schema("situation_v0.2.schema.json")
    )
    if not valid:
        raise ValueError("invalid situation: " + "; ".join(errors))
    receipt_schema = _load_schema("retrieval_receipt_v0.1.schema.json")
    for receipt in receipts:
        receipt_valid, receipt_errors = SchemaValidator.validate_dict(receipt, receipt_schema)
        if not receipt_valid:
            raise ValueError("invalid retrieval receipt: " + "; ".join(receipt_errors))

    expected_receipts = {
        source["source_id"]: source["retrieval_receipt_id"]
        for source in situation["sources"]
        if source["retrieval_receipt_id"] is not None
    }
    provided_receipts: dict[str, str] = {}
    for receipt in receipts:
        source_id = receipt["source_id"]
        if source_id in provided_receipts:
            raise ValueError(f"duplicate receipt for source: {source_id}")
        provided_receipts[source_id] = receipt["receipt_id"]
    if provided_receipts != expected_receipts:
        raise ValueError("receipt bundle does not match situation provenance")

    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    date_label = situation["as_of"][:10]
    paths = {
        "situation": target / f"situation-{date_label}.json",
        "brief": target / f"operating-picture-{date_label}.md",
        "retrieval_receipts": target / f"retrieval-receipts-{date_label}.json",
    }
    paths["situation"].write_text(
        json.dumps(situation, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    paths["brief"].write_text(render_markdown(situation), encoding="utf-8")
    paths["retrieval_receipts"].write_text(
        json.dumps(
            {
                "schema_version": "retrieval_receipt_bundle.v0.1",
                "situation_id": situation["situation_id"],
                "receipts": receipts,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return paths


__all__ = [
    "MAX_SNAPSHOT_BYTES",
    "REQUIRED_SOURCE_IDS",
    "RETRIEVAL_RECEIPT_VERSION",
    "SITUATION_VERSION",
    "SOURCE_REGISTRY_VERSION",
    "build_operating_picture",
    "load_source_registry",
    "read_bus_snapshot",
    "read_fleet_health_snapshot",
    "read_github_snapshot",
    "render_markdown",
    "write_draft_outputs",
]
