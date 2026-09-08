# Sandbox Lifecycle Contract v0.1

Status: experimental Phase 0 contract.

## Purpose

The sandbox lifecycle contract defines the control-plane records needed to run
replaceable AI-agent workers under a durable supervisor. It is designed for
long-running simulations where worker processes may expire, fail, or restart
without becoming their own source of authority.

This package validates contracts and their relationships. It does not launch a
container, virtual machine, or operating-system sandbox, and validation alone
does not prove that requested controls were enforced.

## Contract Set

Five closed JSON Schemas ship in `hummbl_governance/data/`:

| Contract | Purpose |
|---|---|
| `sandbox-profile.v0.1` | Requests a digest-pinned image, filesystem boundary, network and credential posture, process restrictions, and resource limits. |
| `sandbox-lease.v0.1` | Bounds worker lifetime, renewal and restart counts, cumulative resources, and kill-switch authority. |
| `sandbox-checkpoint.v0.1` | Records verified state and artifact digests stored outside the replaceable worker. |
| `sandbox-lifecycle-receipt.v0.1` | Records requested versus effective controls, outcomes, budget use, and tamper-evident receipt linkage. |
| `sandbox-kill-switch.v0.1` | Defines a host-supervisor-controlled halt or termination state at worker, sandbox, or fleet scope. |

Unknown fields are rejected. The schemas are packaged with the wheel and load
without network access.

## Durable Simulation Pattern

```text
durable supervisor
  -> validate profile + lease + armed kill switch
  -> launch replaceable worker through a backend adapter
  -> measure effective controls and emit a lifecycle receipt
  -> checkpoint state outside the worker
  -> renew, replace, or terminate within cumulative budgets
```

For an endurance run, the supervisor—not the worker—owns lease renewal,
restart accounting, checkpoint verification, receipt persistence, and the kill
switch. A 24-hour canary can use hourly worker leases with at most 23 renewals,
a small restart allowance, no network or credentials by default, and a
cumulative 24-hour budget. Those values are a recommended canary posture, not
hard-coded policy.

## Enforced Invariants

`validate_sandbox_contract` rejects malformed or semantically inconsistent
individual records. `validate_sandbox_bundle` additionally requires:

- matching sandbox, profile, lease, worker, supervisor, and kill-switch IDs;
- the exact canonical profile digest in every dependent record;
- a receipt digest calculated without its self-referential digest field;
- host-controlled kill-switch modes that match their declared scope and target;
- mandatory controls to be requested and, for successful events, effective;
- disjoint effective and inactive control sets;
- violation codes for denied or failed events, and none for successful events;
- valid UTC timestamps, bounded lease chronology, and counter limits; and
- reported cumulative consumption no greater than the lease budget.

## API

```python
from hummbl_governance import (
    SandboxContractKind,
    sandbox_contract_digest,
    sandbox_receipt_digest,
    validate_sandbox_bundle,
    validate_sandbox_contract,
)

profile_digest = sandbox_contract_digest(profile)
receipt["receipt_digest"] = sandbox_receipt_digest(receipt)
validate_sandbox_contract(SandboxContractKind.PROFILE, profile)
validate_sandbox_bundle(
    profile=profile,
    lease=lease,
    checkpoint=checkpoint,
    receipt=receipt,
    kill_switch=kill_switch,
)
```

The digest functions use deterministic UTF-8 JSON with sorted keys and reject
non-finite numbers and other non-canonical JSON values.

## Backend Conformance Boundary

A backend adapter must still translate the validated profile into native
controls, inspect the controls actually in force, and fail closed when any
mandatory control is unavailable. A production supervisor also needs durable
receipt storage, cryptographic signing outside the worker, health monitoring,
checkpoint storage, recovery policy, and an out-of-band termination path.

The next phase is a single-worker, no-network canary on one backend. Promotion
beyond experimental status requires backend conformance tests and endurance-run
receipts; schema validation is not runtime-isolation evidence.

## Related Standard

See [Simulation-Affordance Contract Canonicalization](SIMULATION_AFFORDANCE_CONTRACTS.md)
for the separate adapter, deterministic replay, and simulation-governance
boundary. This lifecycle contract governs the execution envelope; it does not
promote simulation outputs or engine-specific behavior into governance canon.
