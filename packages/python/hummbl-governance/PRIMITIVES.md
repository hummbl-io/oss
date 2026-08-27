# Governance Primitives Inventory

Status: canonical inventory
Last updated: 2026-08-26

This file is the authority source for implemented primitive counts.
The README table mirrors this inventory.

## Admission criterion

A **HUMMBL governance primitive** is a minimal, independently specifiable
governance operation or state-bearing mechanism that:

1. Exposes stable input/output semantics (callable interface or schema)
2. Preserves named invariants under its declared preconditions
3. Cannot be decomposed into existing governance primitives without
   changing its externally relevant semantics

Items that fail this criterion are classified as **support artifacts**
(error types, catalogs, schemas) and tracked separately, not counted
as primitives.

## Identifier namespaces

To prevent collisions, identifiers are namespaced:

- `P<n>` — primitive ID (this registry, P1-P34)
- `K<n>` — kernel invariant (K1-K11, defined in `kernel/invariants.py`)
- `D<n>` — doctrine invariant (D1-D7, defined in `kernel/invariants.py`)
- Base120 model codes (e.g. `CO12`, `DE6`) are never used as invariant
  references in this registry

The `InvariantRefs` column uses `K`/`D` namespace only.

## Primitive kinds

| Kind | Definition |
|------|------------|
| `module` | Executable governance operation with callable interface |
| `orchestrator` | Composes multiple primitives into a higher-level flow |
| `monitor` | Observes state and emits alerts; does not mutate governance state |
| `error_type` | Exception or error taxonomy (support artifact, not a primitive) |
| `catalog` | Structured reference data (support artifact, not a primitive) |

## Core primitives (P1-P26)

| # | Kind | Module | Description |
|---|------|--------|-------------|
| P1 | module | `kernel` | Governance operating system — receipts, identity, roles, laws, evidence, sequence, authority, schedule |
| P2 | module | `kill_switch` | Emergency halt system with 4 graduated modes (DISENGAGED, HALT_NONCRITICAL, HALT_ALL, EMERGENCY) |
| P3 | module | `circuit_breaker` | Automatic failure detection and recovery across 3 states (CLOSED, HALF_OPEN, OPEN) |
| P4 | module | `cost_governor` | Budget tracking with soft/hard caps and ALLOW/WARN/DENY decisions |
| P5 | module | `delegation` | HMAC-SHA256 signed capability tokens for agent delegation chains |
| P6 | module | `audit_log` | Append-only JSONL governance audit log with rotation and retention |
| P7 | module | `identity` | Agent registry with configurable aliases, trust tiers, and canonicalization |
| P8 | module | `schema_validator` | Stdlib-only JSON Schema validator (Draft 2020-12 subset) with top-level `ValidationError` export |
| P9 | module | `coordination_bus` | Append-only TSV message bus with flock locking and HMAC signing |
| P10 | module | `compliance_mapper` | Map governance traces to SOC2, GDPR, and OWASP controls |
| P11 | module | `health_probe` | Composable health probe framework with latency tracking |
| P12 | module | `output_validator` | Rule-based content validation for agent outputs (PII detection, injection detection, blocklists) |
| P13 | module | `capability_fence` | Soft sandbox enforcing capability boundaries per agent role |
| P14 | module | `stride_mapper` | Map agent interactions to STRIDE threat categories with mitigation suggestions |
| P15 | orchestrator | `lifecycle` | NIST AI RMF orchestrator composing kill switch, circuit breaker, cost governor, and audit log |
| P16 | module | `contract_net` | Market-based task allocation protocol for multi-agent systems |
| P17 | module | `convergence_guard` | Detect instrumental convergence patterns in agent behavior |
| P18 | monitor | `reward_monitor` | Behavioral drift and reward gaming detector |
| P19 | module | `lamport_clock` | Hardened logical clock for causal ordering of distributed agent events (v0.5.0) |
| P20 | module | `reasoning` | Structured governance reasoning engine with rule application, conflict detection, and decision tracing |
| P21 | module | `eal` | Execution Assurance Layer — Arbiter-verified code quality in execution receipts |
| P22 | module | `physical_governor` | Kinematic constraints and pHRI safety modes for physical-AI deployments |
| P23 | error_type | `errors` | `HummblError`, `FailureMode`, and `fm_to_errors()` — typed error taxonomy (support artifact) |
| P24 | catalog | `failure_modes` | Structured failure mode catalog with classification and error cross-reference (support artifact) |
| P25 | module | `evolution_lineage` | In-memory lineage tracking for eAI variants with drift detection |
| P26 | error_type | `ValidationError` | Top-level exception for schema validation failures, exported from `schema_validator` (support artifact) |

**Note:** P23, P24, and P26 are support artifacts, not primitives under the
admission criterion. They are retained in this registry for historical
continuity (P1-P26 numbering is frozen) but are marked `error_type`/`catalog`.
**Irreducible primitive count: 23 of 26.**

## Expansion primitives (P27-P34)

Kernel sub-primitives added after the initial 26. All enforce specific
kernel (K) or doctrine (D) invariants.

| # | Kind | Module | InvariantRefs | Description |
|---|------|--------|---------------|-------------|
| P27 | module | `canon_registry` | D5 | Canonical operator approval registry for governance transitions (NO_AUTO_PROMOTION) |
| P28 | module | `rollback` | K9 | Rollback declaration validation with reversibility checks (REVERSIBILITY) |
| P29 | module | `recovery_verifier` | K10 | Recovery verification with root-cause and operator approval validation (RECOVERY) |
| P30 | monitor | `receipt_integrity_monitor` | K11, K4, K1 | Sequence, hash-chain, and timestamp integrity checks for receipts (INTEGRITY) |
| P31 | module | `contestability` | D6 | Contest status tracking with review outcome validation (CONTESTABILITY) |
| P32 | module | `doctrine_amendment` | D7 | Doctrine amendment validation with operator approval and tier transitions (DOCTRINE_AMENDMENT) |
| P33 | module | `authority_sweeper` | K6, K3 | Authority sweep validation with revocation consistency checks (AUTHORITY, IDENTITY) |
| P34 | module | `trust_adjuster` | K3 | Trust tier adjustment validation with severity classification (IDENTITY) |

## Count summary

- Core entries (P1-P26): 26 (23 primitives + 3 support artifacts)
- Expansion primitives (P27-P34): 8
- **Total entries: 34**
- **Irreducible primitives: 31** (excluding P23, P24, P26 support artifacts)

## Verification

```bash
python -c "
import pathlib, re
t = pathlib.Path('PRIMITIVES.md').read_text()
a = t.split('## Core primitives', 1)[1].split('## Expansion primitives', 1)[0]
b = t.split('## Expansion primitives', 1)[1].split('## Count', 1)[0]
ids = [int(m) for m in re.findall(r'^\| P(\d+) \|', a + b, re.M)]
assert len(ids) == 34, f'expected 34, got {len(ids)}'
assert len(ids) == len(set(ids)), f'duplicates: {ids}'
assert set(ids) == set(range(1, 35)), f'incomplete: missing {set(range(1,35)) - set(ids)}'
print(f'OK: {len(ids)} unique primitives P1-P34')
"
```
