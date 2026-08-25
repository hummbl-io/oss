# Deterministic Agent Runtime Event Ledger Crosswalk

**Date**: 2026-07-03
**Status**: Draft — advisory schemas, not canon until namespace review.
**Purpose**: Crosswalk between deterministic agent runtime decision boundaries and the event ledger that records their outcomes.

## Overview

This document crosswalks four advisory schemas that define how an agent
runtime makes deterministic decisions and records them in a tamper-evident
event ledger:

1. **deterministic_runtime_decision_boundary** — defines which outputs a
   model is allowed to produce within a workflow, and which authorities
   are forbidden to the model (e.g., loop control, termination, approval
   override, irreversible side-effect approval).
2. **event_ledger_entry** — a single append-only ledger record of a
   proposed effect, its validation result, approval state, applied
   effect, and projection hashes for replay verification.
3. **recovery_policy** — defines allowed and forbidden recovery actions
   for a given failure class, with bounded retry budget, verifier
   requirement, side-effect mode, and escalation path.
4. **mcp_resource_access_policy** — defines allowed and denied
   operations on a resource selector for an MCP server, with credential
   scope and approval requirements.

## Crosswalk

| Concept | Decision Boundary | Event Ledger Entry | Recovery Policy | MCP Resource Access |
|---|---|---|---|---|
| Authority | `controller` field (workflow vs model) | `actor` field | `verifier` field | `credential_scope` |
| Approval | `approval_gate.human_required_for` | `approval_state` | `escalation` | `approval_required_for` |
| Forbidden | `forbidden_model_authority` | n/a (records what happened) | `forbidden_recovery` | `denied_operations` |
| Receipt | `receipt_ref` | `receipt_ref` | `receipt_required` | `audit_receipt` |
| Boundary | `model_allowed_outputs` | `proposed_effect` + `applied_effect` | `allowed_recovery` | `allowed_operations` |

## Invariants

- **I1**: The model must not hold loop control, termination, approval
  override, or irreversible side-effect approval authority. These belong
  to the workflow controller or a human reviewer.
- **I2**: Every applied effect must have a stable projection hash so the
  ledger entry is replay-verifiable. A mutation without a stable
  projection hash is invalid.
- **I3**: Recovery from a failure must be bounded — unbounded retry
  (`retry_forever`, `max_attempts: 99`) is forbidden. The verifier must
  not be `self_check_only` for side-effect-producing recovery.
- **I4**: MCP resource access must deny `raw_shell` and
  `secret_exfiltration` regardless of resource selector. Credential
  scope `admin` with no approval requirements is invalid.

## Fixtures

See `tests/fixtures/runtime_event_ledger/runtime_event_ledger_fixtures.json`
for valid and invalid examples of each schema.

## Namespace Audit Status

Unaudited candidates only:

- `DeterministicRuntimeDecisionBoundary`
- `EventLedgerEntry`
- `RecoveryPolicy`
- `MCPResourceAccessPolicy`

Do not canonize or package until namespace review is receipted.
