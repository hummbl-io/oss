"""Contract tests for the Phase 0 sandbox lifecycle boundary."""

from __future__ import annotations

from copy import deepcopy

import pytest

from hummbl_governance.sandbox_contracts import (
    SandboxContractError,
    SandboxContractKind,
    load_sandbox_schema,
    sandbox_contract_digest,
    sandbox_receipt_digest,
    validate_sandbox_bundle,
    validate_sandbox_contract,
)
from hummbl_governance.schema_validator import ValidationError


SHA_A = "sha256:" + "a" * 64
SHA_B = "sha256:" + "b" * 64


def _profile() -> dict:
    return {
        "schema_version": "sandbox-profile.v0.1",
        "profile_id": "sp-hermes-canary",
        "sandbox_id": "sbx-canary-001",
        "backend": "docker",
        "image_ref": f"ghcr.io/hummbl/sandbox@{SHA_A}",
        "workspace_roots": ["workspace"],
        "filesystem": {
            "root_read_only": True,
            "writable_paths": ["workspace", "tmp"],
            "blocked_paths": ["run/docker.sock", "var/run/docker.sock"],
        },
        "network": {"mode": "none", "allowed_destinations": []},
        "credentials": {"mode": "none", "audiences": []},
        "process": {
            "run_as_uid": 1000,
            "run_as_gid": 1000,
            "no_new_privileges": True,
            "capabilities": [],
        },
        "resources": {
            "cpu_cores": 2,
            "memory_mib": 2048,
            "pids": 128,
            "wall_time_seconds": 3600,
            "output_bytes": 10485760,
        },
        "mandatory_controls": [
            "network:none",
            "credentials:none",
            "rootfs:read-only",
            "no-new-privileges",
            "capabilities:none",
            "resource-limits",
        ],
        "receipt_sink": "host-bridge:receipts",
    }


def _lease() -> dict:
    return {
        "schema_version": "sandbox-lease.v0.1",
        "lease_id": "lease-canary-001",
        "sandbox_id": "sbx-canary-001",
        "profile_id": "sp-hermes-canary",
        "profile_digest": SHA_B,
        "supervisor_id": "supervisor-anvil-canary",
        "worker_id": "worker-canary-001",
        "issued_at": "2026-09-05T23:30:00Z",
        "expires_at": "2026-09-06T00:30:00Z",
        "ttl_seconds": 3600,
        "renewal_count": 0,
        "max_renewals": 23,
        "restart_count": 0,
        "max_restarts": 3,
        "cumulative_budget": {
            "wall_seconds": 86400,
            "cpu_seconds": 172800,
            "output_bytes": 251658240,
            "cost_usd": 5.0,
        },
        "status": "active",
        "kill_switch_ref": "ksw-canary-001",
    }


def _checkpoint() -> dict:
    return {
        "schema_version": "sandbox-checkpoint.v0.1",
        "checkpoint_id": "chk-canary-0001",
        "sandbox_id": "sbx-canary-001",
        "lease_id": "lease-canary-001",
        "worker_id": "worker-canary-001",
        "profile_digest": SHA_B,
        "sequence": 1,
        "created_at": "2026-09-05T23:45:00Z",
        "state_digest": SHA_A,
        "previous_checkpoint_digest": None,
        "artifact_digests": [SHA_B],
        "verified": True,
        "retention_class": "task",
        "receipt_ref": "rcpt-canary-checkpoint-0001",
    }


def _receipt() -> dict:
    controls = _profile()["mandatory_controls"]
    receipt = {
        "schema_version": "sandbox-lifecycle-receipt.v0.1",
        "receipt_id": "rcpt-canary-start-0001",
        "event": "start",
        "sandbox_id": "sbx-canary-001",
        "lease_id": "lease-canary-001",
        "worker_id": "worker-canary-001",
        "supervisor_id": "supervisor-anvil-canary",
        "profile_id": "sp-hermes-canary",
        "profile_digest": SHA_B,
        "sequence": 1,
        "timestamp": "2026-09-05T23:30:01Z",
        "outcome": "succeeded",
        "requested_controls": controls.copy(),
        "effective_controls": controls.copy(),
        "inactive_controls": [],
        "checkpoint_ref": None,
        "violation_code": None,
        "previous_receipt_digest": None,
        "receipt_digest": SHA_B,
        "signer_bridge": "host-bridge:signing",
        "budget_consumed": {
            "wall_seconds": 1,
            "cpu_seconds": 1,
            "output_bytes": 0,
            "cost_usd": 0.0,
        },
    }
    receipt["receipt_digest"] = sandbox_receipt_digest(receipt)
    return receipt


def _kill_switch() -> dict:
    return {
        "schema_version": "sandbox-kill-switch.v0.1",
        "kill_switch_id": "ksw-canary-001",
        "controller": "host_supervisor",
        "scope": "sandbox",
        "target_id": "sbx-canary-001",
        "status": "armed",
        "mode": "terminate_sandbox",
        "generation": 0,
        "changed_by": "operator",
        "changed_at": "2026-09-05T23:29:59Z",
        "reason": "initial canary guard",
        "receipt_ref": "rcpt-canary-kill-switch-0001",
    }


def _bundle() -> dict[str, dict]:
    profile = _profile()
    lease = _lease()
    lease["profile_digest"] = sandbox_contract_digest(profile)
    checkpoint = _checkpoint()
    checkpoint["profile_digest"] = lease["profile_digest"]
    receipt = _receipt()
    receipt["profile_digest"] = lease["profile_digest"]
    receipt["receipt_digest"] = sandbox_receipt_digest(receipt)
    return {
        "profile": profile,
        "lease": lease,
        "checkpoint": checkpoint,
        "receipt": receipt,
        "kill_switch": _kill_switch(),
    }


@pytest.mark.parametrize(
    ("kind", "document"),
    [
        (SandboxContractKind.PROFILE, _profile()),
        (SandboxContractKind.LEASE, _lease()),
        (SandboxContractKind.CHECKPOINT, _checkpoint()),
        (SandboxContractKind.LIFECYCLE_RECEIPT, _receipt()),
        (SandboxContractKind.KILL_SWITCH, _kill_switch()),
    ],
)
def test_valid_contracts_pass(kind: SandboxContractKind, document: dict) -> None:
    validate_sandbox_contract(kind, document)


@pytest.mark.parametrize("kind", list(SandboxContractKind))
def test_every_contract_schema_is_closed_and_versioned(kind: SandboxContractKind) -> None:
    schema = load_sandbox_schema(kind)

    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["additionalProperties"] is False
    assert schema["properties"]["schema_version"]["const"].endswith(".v0.1")


def test_unknown_contract_kind_fails_closed() -> None:
    with pytest.raises(SandboxContractError, match="unknown sandbox contract kind"):
        load_sandbox_schema("not-a-contract")


def test_sandbox_contracts_are_available_from_public_package_api() -> None:
    from hummbl_governance import (  # noqa: PLC0415
        SandboxContractKind as PublicSandboxContractKind,
    )
    from hummbl_governance import (  # noqa: PLC0415
        validate_sandbox_contract as public_validate_sandbox_contract,
    )

    assert PublicSandboxContractKind is SandboxContractKind
    assert public_validate_sandbox_contract is validate_sandbox_contract


def test_profile_requires_digest_pinned_image() -> None:
    profile = _profile()
    profile["image_ref"] = "ghcr.io/hummbl/sandbox:latest"

    with pytest.raises(ValidationError, match="image_ref"):
        validate_sandbox_contract(SandboxContractKind.PROFILE, profile)


def test_profile_rejects_ambient_network_and_credentials() -> None:
    profile = _profile()
    profile["network"] = {"mode": "host", "allowed_destinations": ["*"]}
    profile["credentials"] = {"mode": "mounted", "audiences": ["*"]}

    with pytest.raises(ValidationError):
        validate_sandbox_contract(SandboxContractKind.PROFILE, profile)


def test_profile_rejects_root_or_capability_grants() -> None:
    profile = _profile()
    profile["process"]["run_as_uid"] = 0
    profile["process"]["capabilities"] = ["SYS_ADMIN"]

    with pytest.raises(ValidationError):
        validate_sandbox_contract(SandboxContractKind.PROFILE, profile)


def test_profile_rejects_allowlist_when_network_is_none() -> None:
    profile = _profile()
    profile["network"]["allowed_destinations"] = ["pypi.org:443"]

    with pytest.raises(SandboxContractError, match="network:none"):
        validate_sandbox_contract(SandboxContractKind.PROFILE, profile)


def test_profile_rejects_audiences_when_credentials_are_none() -> None:
    profile = _profile()
    profile["credentials"]["audiences"] = ["github:repo-read"]

    with pytest.raises(SandboxContractError, match="credentials:none"):
        validate_sandbox_contract(SandboxContractKind.PROFILE, profile)


@pytest.mark.parametrize(
    ("section", "mode", "message"),
    [
        ("network", "egress_proxy", "named allowed destinations"),
        ("credentials", "broker", "at least one audience"),
    ],
)
def test_profile_scoped_bridges_require_explicit_grants(
    section: str, mode: str, message: str
) -> None:
    profile = _profile()
    profile[section]["mode"] = mode
    control = "network:none" if section == "network" else "credentials:none"
    profile["mandatory_controls"].remove(control)
    profile["mandatory_controls"].append(f"{section}:{mode.replace('_', '-')}")

    with pytest.raises(SandboxContractError, match=message):
        validate_sandbox_contract(SandboxContractKind.PROFILE, profile)


def test_profile_rejects_missing_or_duplicate_mandatory_controls() -> None:
    profile = _profile()
    profile["mandatory_controls"].remove("resource-limits")
    profile["mandatory_controls"].append("network:none")

    with pytest.raises(SandboxContractError, match="mandatory_controls"):
        validate_sandbox_contract(SandboxContractKind.PROFILE, profile)


def test_profile_rejects_missing_mandatory_control_without_duplicates() -> None:
    profile = _profile()
    profile["mandatory_controls"].remove("resource-limits")
    profile["mandatory_controls"].append("seccomp")

    with pytest.raises(SandboxContractError, match="resource-limits"):
        validate_sandbox_contract(SandboxContractKind.PROFILE, profile)


@pytest.mark.parametrize(
    "conflicting_control",
    ["network:egress-proxy", "credentials:broker"],
)
def test_profile_rejects_conflicting_mode_controls(conflicting_control: str) -> None:
    profile = _profile()
    profile["mandatory_controls"].append(conflicting_control)

    with pytest.raises(SandboxContractError, match="conflicting"):
        validate_sandbox_contract(SandboxContractKind.PROFILE, profile)


def test_lease_rejects_unbounded_lifetime_and_restart_budget() -> None:
    lease = _lease()
    lease["ttl_seconds"] = 172800
    lease["max_restarts"] = 100

    with pytest.raises(ValidationError):
        validate_sandbox_contract(SandboxContractKind.LEASE, lease)


def test_lease_wall_budget_must_cover_one_lease() -> None:
    lease = _lease()
    lease["cumulative_budget"]["wall_seconds"] = 120

    with pytest.raises(SandboxContractError, match="wall_seconds"):
        validate_sandbox_contract(SandboxContractKind.LEASE, lease)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("expires_at", "2026-09-05T23:29:59Z", "after issued_at"),
        ("expires_at", "2026-09-06T01:30:00Z", "ttl_seconds"),
        ("renewal_count", 24, "renewal_count"),
        ("restart_count", 4, "restart_count"),
    ],
)
def test_lease_rejects_temporal_or_counter_drift(
    field: str, value: object, message: str
) -> None:
    lease = _lease()
    lease[field] = value

    with pytest.raises(SandboxContractError, match=message):
        validate_sandbox_contract(SandboxContractKind.LEASE, lease)


def test_lease_rejects_calendar_invalid_timestamp() -> None:
    lease = _lease()
    lease["expires_at"] = "2026-99-99T00:30:00Z"

    with pytest.raises(SandboxContractError, match="valid UTC timestamp"):
        validate_sandbox_contract(SandboxContractKind.LEASE, lease)


def test_contract_digest_rejects_noncanonical_json() -> None:
    with pytest.raises(SandboxContractError, match="canonical JSON"):
        sandbox_contract_digest({"not_finite": float("nan")})


def test_checkpoint_requires_verified_digest_only_state() -> None:
    checkpoint = _checkpoint()
    checkpoint["verified"] = False
    checkpoint["state"] = {"secret": "must-not-be-embedded"}

    with pytest.raises(ValidationError):
        validate_sandbox_contract(SandboxContractKind.CHECKPOINT, checkpoint)


@pytest.mark.parametrize(
    ("kind", "document", "field"),
    [
        (SandboxContractKind.CHECKPOINT, _checkpoint(), "created_at"),
        (SandboxContractKind.LIFECYCLE_RECEIPT, _receipt(), "timestamp"),
        (SandboxContractKind.KILL_SWITCH, _kill_switch(), "changed_at"),
    ],
)
def test_contracts_reject_calendar_invalid_timestamps(
    kind: SandboxContractKind, document: dict, field: str
) -> None:
    document[field] = "2026-99-99T00:30:00Z"

    with pytest.raises(SandboxContractError, match="valid UTC timestamp"):
        validate_sandbox_contract(kind, document)


def test_kill_switch_must_be_host_controlled() -> None:
    kill_switch = _kill_switch()
    kill_switch["controller"] = "worker"

    with pytest.raises(ValidationError, match="controller"):
        validate_sandbox_contract(SandboxContractKind.KILL_SWITCH, kill_switch)


def test_kill_switch_mode_must_match_scope() -> None:
    kill_switch = _kill_switch()
    kill_switch["mode"] = "terminate_all"

    with pytest.raises(SandboxContractError, match="mode"):
        validate_sandbox_contract(SandboxContractKind.KILL_SWITCH, kill_switch)


def test_valid_bundle_passes_without_mutation() -> None:
    bundle = _bundle()
    original = deepcopy(bundle)

    validate_sandbox_bundle(**bundle)

    assert bundle == original


@pytest.mark.parametrize("field", ["sandbox_id", "profile_id", "worker_id", "lease_id"])
def test_bundle_rejects_cross_document_identity_drift(field: str) -> None:
    bundle = _bundle()
    target = "checkpoint" if field in {"sandbox_id", "worker_id", "lease_id"} else "receipt"
    mismatched = {
        "sandbox_id": "sbx-mismatch",
        "profile_id": "sp-mismatch",
        "worker_id": "worker-mismatch",
        "lease_id": "lease-mismatch",
    }
    bundle[target][field] = mismatched[field]
    if target == "receipt":
        bundle["receipt"]["receipt_digest"] = sandbox_receipt_digest(bundle["receipt"])

    with pytest.raises(SandboxContractError, match=field):
        validate_sandbox_bundle(**bundle)


def test_bundle_rejects_profile_digest_drift() -> None:
    bundle = _bundle()
    bundle["lease"]["profile_digest"] = SHA_A

    with pytest.raises(SandboxContractError, match="profile_digest"):
        validate_sandbox_bundle(**bundle)


def test_bundle_rejects_consumption_above_cumulative_budget() -> None:
    bundle = _bundle()
    bundle["receipt"]["budget_consumed"]["wall_seconds"] = 86401
    bundle["receipt"]["receipt_digest"] = sandbox_receipt_digest(bundle["receipt"])

    with pytest.raises(SandboxContractError, match="wall_seconds"):
        validate_sandbox_bundle(**bundle)


def test_success_receipt_fails_when_mandatory_control_is_inactive() -> None:
    bundle = _bundle()
    bundle["receipt"]["effective_controls"].remove("network:none")
    bundle["receipt"]["inactive_controls"] = ["network:none"]
    bundle["receipt"]["receipt_digest"] = sandbox_receipt_digest(bundle["receipt"])

    with pytest.raises(SandboxContractError, match="mandatory controls"):
        validate_sandbox_bundle(**bundle)


def test_denied_receipt_may_record_inactive_mandatory_control() -> None:
    bundle = _bundle()
    bundle["receipt"]["outcome"] = "denied"
    bundle["receipt"]["effective_controls"].remove("network:none")
    bundle["receipt"]["inactive_controls"] = ["network:none"]
    bundle["receipt"]["violation_code"] = "control_unavailable"
    bundle["receipt"]["receipt_digest"] = sandbox_receipt_digest(bundle["receipt"])

    validate_sandbox_bundle(**bundle)


def test_bundle_rejects_overlapping_effective_and_inactive_controls() -> None:
    bundle = _bundle()
    bundle["receipt"]["inactive_controls"] = ["network:none"]
    bundle["receipt"]["receipt_digest"] = sandbox_receipt_digest(bundle["receipt"])

    with pytest.raises(SandboxContractError, match="disjoint"):
        validate_sandbox_bundle(**bundle)


def test_bundle_rejects_receipt_that_omits_requested_control() -> None:
    bundle = _bundle()
    bundle["receipt"]["requested_controls"].remove("resource-limits")
    bundle["receipt"]["effective_controls"].remove("resource-limits")
    bundle["receipt"]["receipt_digest"] = sandbox_receipt_digest(bundle["receipt"])

    with pytest.raises(SandboxContractError, match="requested_controls"):
        validate_sandbox_bundle(**bundle)


def test_denied_receipt_requires_a_violation_code() -> None:
    bundle = _bundle()
    bundle["receipt"]["outcome"] = "denied"

    with pytest.raises(SandboxContractError, match="violation_code"):
        validate_sandbox_bundle(**bundle)


def test_failed_receipt_requires_a_violation_code() -> None:
    bundle = _bundle()
    bundle["receipt"]["outcome"] = "failed"

    with pytest.raises(SandboxContractError, match="violation_code"):
        validate_sandbox_bundle(**bundle)


def test_succeeded_receipt_rejects_a_violation_code() -> None:
    bundle = _bundle()
    bundle["receipt"]["violation_code"] = "not_applicable"

    with pytest.raises(SandboxContractError, match="violation_code"):
        validate_sandbox_bundle(**bundle)


def test_bundle_rejects_duplicate_receipt_controls() -> None:
    bundle = _bundle()
    bundle["receipt"]["requested_controls"].append("network:none")

    with pytest.raises(SandboxContractError, match="requested_controls"):
        validate_sandbox_bundle(**bundle)


def test_bundle_requires_every_requested_control_to_be_classified() -> None:
    bundle = _bundle()
    bundle["receipt"]["requested_controls"].append("seccomp")
    bundle["receipt"]["receipt_digest"] = sandbox_receipt_digest(bundle["receipt"])

    with pytest.raises(SandboxContractError, match="classify every requested control"):
        validate_sandbox_bundle(**bundle)


def test_bundle_rejects_receipt_digest_drift() -> None:
    bundle = _bundle()
    bundle["receipt"]["budget_consumed"]["cpu_seconds"] = 2

    with pytest.raises(SandboxContractError, match="receipt_digest"):
        validate_sandbox_bundle(**bundle)
