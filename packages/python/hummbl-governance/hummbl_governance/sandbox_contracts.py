# Copyright 2024-2026 HUMMBL, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

"""Fail-closed contracts for sandbox workers and their host supervisor.

These contracts define the durable control plane for replaceable workers. They
do not launch a sandbox; an executor must enforce the validated profile and
record the effective controls in a lifecycle receipt.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from enum import Enum
from importlib.resources import files
from typing import Any

from hummbl_governance.schema_validator import SchemaValidator, ValidationError


class SandboxContractError(ValueError):
    """Raised when sandbox contracts disagree or violate semantic invariants."""


class SandboxContractKind(str, Enum):
    """Versioned sandbox contract document kinds."""

    PROFILE = "profile"
    LEASE = "lease"
    CHECKPOINT = "checkpoint"
    LIFECYCLE_RECEIPT = "lifecycle_receipt"
    KILL_SWITCH = "kill_switch"


_SCHEMA_FILES = {
    SandboxContractKind.PROFILE: "sandbox_profile_v0.1.schema.json",
    SandboxContractKind.LEASE: "sandbox_lease_v0.1.schema.json",
    SandboxContractKind.CHECKPOINT: "sandbox_checkpoint_v0.1.schema.json",
    SandboxContractKind.LIFECYCLE_RECEIPT: "sandbox_lifecycle_receipt_v0.1.schema.json",
    SandboxContractKind.KILL_SWITCH: "sandbox_kill_switch_v0.1.schema.json",
}

_CORE_CONTROLS = {
    "rootfs:read-only",
    "no-new-privileges",
    "capabilities:none",
    "resource-limits",
}


def _coerce_kind(kind: SandboxContractKind | str) -> SandboxContractKind:
    try:
        return SandboxContractKind(kind)
    except (TypeError, ValueError) as exc:
        raise SandboxContractError(f"unknown sandbox contract kind: {kind!r}") from exc


def load_sandbox_schema(kind: SandboxContractKind | str) -> dict[str, Any]:
    """Load a packaged sandbox schema without performing network access."""
    contract_kind = _coerce_kind(kind)
    resource = files("hummbl_governance").joinpath("data", _SCHEMA_FILES[contract_kind])
    try:
        return json.loads(resource.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SandboxContractError(
            f"cannot load schema for sandbox contract kind {contract_kind.value!r}"
        ) from exc


def sandbox_contract_digest(document: dict[str, Any]) -> str:
    """Return a deterministic SHA-256 digest for a JSON-compatible contract."""
    try:
        payload = json.dumps(
            document,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise SandboxContractError("sandbox contract is not canonical JSON") from exc
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def sandbox_receipt_digest(receipt: dict[str, Any]) -> str:
    """Digest a receipt envelope without its self-referential digest field."""
    return sandbox_contract_digest(
        {key: value for key, value in receipt.items() if key != "receipt_digest"}
    )


def validate_sandbox_contract(
    kind: SandboxContractKind | str,
    document: dict[str, Any],
) -> None:
    """Validate one contract against its closed schema and semantic rules."""
    contract_kind = _coerce_kind(kind)
    schema = load_sandbox_schema(contract_kind)
    errors = SchemaValidator.validate(document, schema)
    if errors:
        raise ValidationError("; ".join(errors))

    if contract_kind is SandboxContractKind.PROFILE:
        _validate_profile_semantics(document)
    elif contract_kind is SandboxContractKind.LEASE:
        _validate_lease_semantics(document)
    elif contract_kind is SandboxContractKind.CHECKPOINT:
        _validate_utc_timestamp("created_at", document["created_at"])
    elif contract_kind is SandboxContractKind.LIFECYCLE_RECEIPT:
        _validate_receipt_semantics(document)
    elif contract_kind is SandboxContractKind.KILL_SWITCH:
        _validate_kill_switch_semantics(document)


def _validate_utc_timestamp(field: str, value: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise SandboxContractError(f"{field} must be a valid UTC timestamp") from exc


def _validate_profile_semantics(profile: dict[str, Any]) -> None:
    network = profile["network"]
    destinations = network["allowed_destinations"]
    if network["mode"] == "none" and destinations:
        raise SandboxContractError("network:none requires an empty allowed_destinations list")
    if network["mode"] == "egress_proxy" and not destinations:
        raise SandboxContractError("network:egress_proxy requires named allowed destinations")

    credentials = profile["credentials"]
    audiences = credentials["audiences"]
    if credentials["mode"] == "none" and audiences:
        raise SandboxContractError("credentials:none requires an empty audiences list")
    if credentials["mode"] == "broker" and not audiences:
        raise SandboxContractError("credentials:broker requires at least one audience")

    mandatory_controls = profile["mandatory_controls"]
    if len(mandatory_controls) != len(set(mandatory_controls)):
        raise SandboxContractError("mandatory_controls must not contain duplicates")

    required_controls = set(_CORE_CONTROLS)
    network_control = f"network:{network['mode'].replace('_', '-')}"
    credential_control = f"credentials:{credentials['mode']}"
    conflicting_controls = (
        {"network:none", "network:egress-proxy", "credentials:none", "credentials:broker"}
        & set(mandatory_controls)
    ) - {network_control, credential_control}
    if conflicting_controls:
        raise SandboxContractError(
            "mandatory_controls contain conflicting mode controls: "
            + ", ".join(sorted(conflicting_controls))
        )

    required_controls.add(network_control)
    required_controls.add(credential_control)
    missing = required_controls - set(mandatory_controls)
    if missing:
        raise SandboxContractError(
            "mandatory_controls omit required controls: " + ", ".join(sorted(missing))
        )


def _validate_lease_semantics(lease: dict[str, Any]) -> None:
    issued_at = _validate_utc_timestamp("issued_at", lease["issued_at"])
    expires_at = _validate_utc_timestamp("expires_at", lease["expires_at"])

    if expires_at <= issued_at:
        raise SandboxContractError("expires_at must be after issued_at")
    actual_ttl = int((expires_at - issued_at).total_seconds())
    if actual_ttl != lease["ttl_seconds"]:
        raise SandboxContractError("ttl_seconds must equal expires_at minus issued_at")
    if lease["renewal_count"] > lease["max_renewals"]:
        raise SandboxContractError("renewal_count must not exceed max_renewals")
    if lease["restart_count"] > lease["max_restarts"]:
        raise SandboxContractError("restart_count must not exceed max_restarts")

    wall_budget = lease["cumulative_budget"]["wall_seconds"]
    if wall_budget < lease["ttl_seconds"]:
        raise SandboxContractError("cumulative_budget.wall_seconds must cover ttl_seconds")


def _validate_kill_switch_semantics(kill_switch: dict[str, Any]) -> None:
    _validate_utc_timestamp("changed_at", kill_switch["changed_at"])
    required_scope = {
        "terminate_worker": "worker",
        "terminate_sandbox": "sandbox",
        "terminate_all": "fleet",
    }.get(kill_switch["mode"])
    if required_scope is not None and kill_switch["scope"] != required_scope:
        raise SandboxContractError(
            f"kill-switch mode {kill_switch['mode']!r} requires {required_scope!r} scope"
        )


def _validate_receipt_semantics(receipt: dict[str, Any]) -> None:
    _validate_utc_timestamp("timestamp", receipt["timestamp"])
    for field in ("requested_controls", "effective_controls", "inactive_controls"):
        values = receipt[field]
        if len(values) != len(set(values)):
            raise SandboxContractError(f"{field} must not contain duplicates")

    outcome = receipt["outcome"]
    violation_code = receipt["violation_code"]
    if outcome == "succeeded" and violation_code is not None:
        raise SandboxContractError("succeeded receipt must not include a violation_code")
    if outcome in {"denied", "failed"} and violation_code is None:
        raise SandboxContractError("denied or failed receipt requires violation_code")

    expected_digest = sandbox_receipt_digest(receipt)
    if receipt["receipt_digest"] != expected_digest:
        raise SandboxContractError("receipt_digest does not match receipt contents")


def _require_equal(field: str, expected: Any, actual: Any, location: str) -> None:
    if actual != expected:
        raise SandboxContractError(
            f"{field} mismatch at {location}: expected {expected!r}, got {actual!r}"
        )


def validate_sandbox_bundle(
    *,
    profile: dict[str, Any],
    lease: dict[str, Any],
    checkpoint: dict[str, Any],
    receipt: dict[str, Any],
    kill_switch: dict[str, Any],
) -> None:
    """Validate a coherent worker lease, checkpoint, receipt, and kill switch."""
    contracts = {
        SandboxContractKind.PROFILE: profile,
        SandboxContractKind.LEASE: lease,
        SandboxContractKind.CHECKPOINT: checkpoint,
        SandboxContractKind.LIFECYCLE_RECEIPT: receipt,
        SandboxContractKind.KILL_SWITCH: kill_switch,
    }
    for kind, document in contracts.items():
        validate_sandbox_contract(kind, document)

    sandbox_id = profile["sandbox_id"]
    for location, document in (
        ("lease", lease),
        ("checkpoint", checkpoint),
        ("receipt", receipt),
    ):
        _require_equal("sandbox_id", sandbox_id, document["sandbox_id"], location)

    _require_equal("profile_id", profile["profile_id"], lease["profile_id"], "lease")
    _require_equal("profile_id", profile["profile_id"], receipt["profile_id"], "receipt")
    _require_equal("lease_id", lease["lease_id"], checkpoint["lease_id"], "checkpoint")
    _require_equal("lease_id", lease["lease_id"], receipt["lease_id"], "receipt")
    _require_equal("worker_id", lease["worker_id"], checkpoint["worker_id"], "checkpoint")
    _require_equal("worker_id", lease["worker_id"], receipt["worker_id"], "receipt")
    _require_equal(
        "supervisor_id", lease["supervisor_id"], receipt["supervisor_id"], "receipt"
    )
    _require_equal(
        "kill_switch_ref",
        lease["kill_switch_ref"],
        kill_switch["kill_switch_id"],
        "kill_switch",
    )

    profile_digest = sandbox_contract_digest(profile)
    _require_equal("profile_digest", profile_digest, lease["profile_digest"], "lease")
    _require_equal(
        "profile_digest", profile_digest, checkpoint["profile_digest"], "checkpoint"
    )
    _require_equal("profile_digest", profile_digest, receipt["profile_digest"], "receipt")

    scope_target = {
        "sandbox": sandbox_id,
        "worker": lease["worker_id"],
        "fleet": None,
    }[kill_switch["scope"]]
    _require_equal("target_id", scope_target, kill_switch["target_id"], "kill_switch")

    effective = set(receipt["effective_controls"])
    inactive = set(receipt["inactive_controls"])
    if effective & inactive:
        raise SandboxContractError("effective_controls and inactive_controls must be disjoint")

    mandatory = set(profile["mandatory_controls"])
    requested = set(receipt["requested_controls"])
    if effective | inactive != requested:
        raise SandboxContractError(
            "receipt controls must classify every requested control; "
            "effective_controls and inactive_controls must equal requested_controls"
        )
    if not mandatory <= requested:
        raise SandboxContractError("requested_controls omit mandatory controls")
    if receipt["outcome"] == "succeeded" and (
        not mandatory <= effective or mandatory & inactive
    ):
        raise SandboxContractError("succeeded receipt is missing mandatory controls")
    consumed = receipt["budget_consumed"]
    budget = lease["cumulative_budget"]
    for field in ("wall_seconds", "cpu_seconds", "output_bytes", "cost_usd"):
        if consumed[field] > budget[field]:
            raise SandboxContractError(
                f"budget_consumed.{field} exceeds cumulative_budget.{field}"
            )


__all__ = [
    "SandboxContractError",
    "SandboxContractKind",
    "load_sandbox_schema",
    "sandbox_contract_digest",
    "sandbox_receipt_digest",
    "validate_sandbox_bundle",
    "validate_sandbox_contract",
]
