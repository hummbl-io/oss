"""Immutable Record and Relation envelopes."""

from __future__ import annotations

import json
import re
import secrets
import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from .canonical import canonicalize_json, digest_bytes


class RecordError(ValueError):
    """A Record or Relation envelope violates a structural invariant."""


RECORD_TYPE_PATTERN = re.compile(r"^[a-z][a-z0-9_.-]*:[A-Za-z][A-Za-z0-9_.-]*$")
RELATION_TYPE_PATTERN = re.compile(r"^[a-z][a-z0-9_.-]*:[a-z][a-z0-9_.-]*$")
MATURITIES = {"draft", "candidate", "canonical", "deprecated", "revoked"}
CONFIDENTIALITIES = {"public", "internal", "confidential", "restricted", "participant-sensitive"}


def new_urn_uuid7(*, timestamp_ms: int | None = None) -> str:
    """Generate an RFC 9562 UUIDv7 URN without a third-party dependency."""

    milliseconds = int(time.time() * 1000) if timestamp_ms is None else timestamp_ms
    if not 0 <= milliseconds < 2**48:
        raise RecordError("UUIDv7 timestamp is outside the 48-bit range")
    random_a = secrets.randbits(12)
    random_b = secrets.randbits(62)
    integer = (milliseconds << 80) | (0x7 << 76) | (random_a << 64) | (0b10 << 62) | random_b
    return f"urn:uuid:{uuid.UUID(int=integer)}"


def _validate_urn(value: str, field: str) -> None:
    prefix = "urn:uuid:"
    if not value.startswith(prefix):
        raise RecordError(f"{field} must be a UUID URN")
    try:
        uuid.UUID(value[len(prefix) :])
    except ValueError as exc:
        raise RecordError(f"{field} must be a UUID URN") from exc


def _validate_namespaced(value: str, field: str, pattern: re.Pattern[str]) -> None:
    if not isinstance(value, str) or not pattern.fullmatch(value):
        raise RecordError(f"{field} must be namespace-qualified")


def _validate_nonempty_string(value: str, field: str) -> None:
    if not isinstance(value, str) or not value:
        raise RecordError(f"{field} must be a non-empty string")


def _validate_nonnegative_integer(value: int, field: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise RecordError(f"{field} must be a non-negative integer")


def _validate_datetime(value: str, field: str) -> None:
    if not isinstance(value, str):
        raise RecordError(f"{field} must be an ISO-8601 date-time")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RecordError(f"{field} must be an ISO-8601 date-time") from exc
    if parsed.tzinfo is None:
        raise RecordError(f"{field} must include a timezone")


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True, slots=True)
class Record:
    record_id: str
    record_type: str
    schema_id: str
    schema_version: str
    payload_bytes: bytes
    payload_digest: str
    actor_id: str
    source_id: str
    source_sequence: int
    created_at: str
    canonicalization_profile: str = "hummbl-jcs-1"
    media_type: str = "application/json"
    maturity: str = "candidate"
    confidentiality: str = "internal"

    @property
    def payload(self) -> Any:
        """Return a fresh decoded payload so callers cannot mutate stored bytes."""

        return json.loads(self.payload_bytes)

    @classmethod
    def create(
        cls,
        record_type: str,
        schema_id: str,
        schema_version: str,
        payload: Any,
        actor_id: str,
        source_id: str,
        source_sequence: int,
        *,
        record_id: str | None = None,
        created_at: str | None = None,
        maturity: str = "candidate",
        confidentiality: str = "internal",
    ) -> Record:
        _validate_namespaced(record_type, "record_type", RECORD_TYPE_PATTERN)
        for field, value in (
            ("schema_id", schema_id),
            ("schema_version", schema_version),
            ("actor_id", actor_id),
            ("source_id", source_id),
        ):
            _validate_nonempty_string(value, field)
        _validate_nonnegative_integer(source_sequence, "source_sequence")
        if not isinstance(maturity, str) or maturity not in MATURITIES:
            raise RecordError(f"maturity must be one of: {', '.join(sorted(MATURITIES))}")
        if not isinstance(confidentiality, str) or confidentiality not in CONFIDENTIALITIES:
            raise RecordError(
                f"confidentiality must be one of: {', '.join(sorted(CONFIDENTIALITIES))}"
            )
        resolved_id = record_id or new_urn_uuid7()
        _validate_urn(resolved_id, "record_id")
        payload_bytes = canonicalize_json(payload)
        resolved_created_at = created_at or _utc_now()
        _validate_datetime(resolved_created_at, "created_at")
        return cls(
            record_id=resolved_id,
            record_type=record_type,
            schema_id=schema_id,
            schema_version=schema_version,
            payload_bytes=payload_bytes,
            payload_digest=digest_bytes(payload_bytes),
            actor_id=actor_id,
            source_id=source_id,
            source_sequence=source_sequence,
            created_at=resolved_created_at,
            maturity=maturity,
            confidentiality=confidentiality,
        )


@dataclass(frozen=True, slots=True)
class Relation:
    relation_id: str
    relation_type: str
    source_record_id: str
    target_record_id: str
    actor_id: str
    source_id: str
    source_sequence: int
    asserted_at: str

    @classmethod
    def create(
        cls,
        relation_type: str,
        source_record_id: str,
        target_record_id: str,
        actor_id: str,
        source_sequence: int,
        *,
        source_id: str = "node:local",
        relation_id: str | None = None,
        asserted_at: str | None = None,
    ) -> Relation:
        _validate_namespaced(relation_type, "relation_type", RELATION_TYPE_PATTERN)
        _validate_urn(source_record_id, "source_record_id")
        _validate_urn(target_record_id, "target_record_id")
        _validate_nonempty_string(actor_id, "actor_id")
        _validate_nonempty_string(source_id, "source_id")
        _validate_nonnegative_integer(source_sequence, "source_sequence")
        resolved_id = relation_id or new_urn_uuid7()
        _validate_urn(resolved_id, "relation_id")
        resolved_asserted_at = asserted_at or _utc_now()
        _validate_datetime(resolved_asserted_at, "asserted_at")
        return cls(
            relation_id=resolved_id,
            relation_type=relation_type,
            source_record_id=source_record_id,
            target_record_id=target_record_id,
            actor_id=actor_id,
            source_id=source_id,
            source_sequence=source_sequence,
            asserted_at=resolved_asserted_at,
        )
