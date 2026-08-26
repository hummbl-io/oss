# Governance Primitives Inventory

Status: canonical inventory
Last updated: 2026-08-23

This file is the authority source for implemented primitive counts.
The README table mirrors this inventory.

## Existing primitives (P1-P26)

These are the core primitives shipped with the package.

| # | Module | Description |
|---|--------|-------------|
| P1 | `kernel` | Governance operating system — receipts, identity, roles, laws, evidence, sequence, authority, schedule |
| P2 | `kill_switch` | Emergency halt system with 4 graduated modes (DISENGAGED, HALT_NONCRITICAL, HALT_ALL, EMERGENCY) |
| P3 | `circuit_breaker` | Automatic failure detection and recovery across 3 states (CLOSED, HALF_OPEN, OPEN) |
| P4 | `cost_governor` | Budget tracking with soft/hard caps and ALLOW/WARN/DENY decisions |
| P5 | `delegation` | HMAC-SHA256 signed capability tokens for agent delegation chains |
| P6 | `audit_log` | Append-only JSONL governance audit log with rotation and retention |
| P7 | `identity` | Agent registry with configurable aliases, trust tiers, and canonicalization |
| P8 | `schema_validator` | Stdlib-only JSON Schema validator (Draft 2020-12 subset) with top-level `ValidationError` export |
| P9 | `coordination_bus` | Append-only TSV message bus with flock locking and HMAC signing |
| P10 | `compliance_mapper` | Map governance traces to SOC2, GDPR, and OWASP controls |
| P11 | `health_probe` | Composable health probe framework with latency tracking |
| P12 | `output_validator` | Rule-based content validation for agent outputs (PII detection, injection detection, blocklists) |
| P13 | `capability_fence` | Soft sandbox enforcing capability boundaries per agent role |
| P14 | `stride_mapper` | Map agent interactions to STRIDE threat categories with mitigation suggestions |
| P15 | `lifecycle` | NIST AI RMF orchestrator composing kill switch, circuit breaker, cost governor, and audit log |
| P16 | `contract_net` | Market-based task allocation protocol for multi-agent systems |
| P17 | `convergence_guard` | Detect instrumental convergence patterns in agent behavior |
| P18 | `reward_monitor` | Behavioral drift and reward gaming detector |
| P19 | `lamport_clock` | Hardened logical clock for causal ordering of distributed agent events (v0.5.0) |
| P20 | `reasoning` | Structured governance reasoning engine with rule application, conflict detection, and decision tracing |
| P21 | `eal` | Execution Assurance Layer — Arbiter-verified code quality in execution receipts |
| P22 | `physical_governor` | Kinematic constraints and pHRI safety modes for physical-AI deployments |
| P23 | `errors` | `HummblError`, `FailureMode`, and `fm_to_errors()` — typed error taxonomy |
| P24 | `failure_modes` | Structured failure mode catalog with classification and error cross-reference |
| P25 | `evolution_lineage` | In-memory lineage tracking for eAI variants with drift detection |
| P26 | `ValidationError` | Top-level exception for schema validation failures (exported from `schema_validator`) |

## Implemented expansion primitives (P27-P34)

These are kernel sub-primitives added after the initial 26.

| # | Module | Invariant | Description |
|---|--------|-----------|-------------|
| P27 | `canon_registry` | — | Canonical operator approval registry for governance transitions |
| P28 | `rollback` | K9 | Rollback declaration validation with reversibility checks |
| P29 | `recovery_verifier` | K10 | Recovery verification with root-cause and operator approval validation |
| P30 | `receipt_integrity_monitor` | K11 | Sequence, hash-chain, and timestamp integrity checks for receipts |
| P31 | `contestability` | D6 | Contest status tracking with review outcome validation |
| P32 | `doctrine_amendment` | D7 | Doctrine amendment validation with operator approval and tier transitions |
| P33 | `authority_sweeper` | P34 | Authority sweep validation with revocation consistency checks |
| P34 | `trust_adjuster` | P36 | Trust tier adjustment validation with severity classification |

## Count summary

- Core primitives: 26
- Implemented expansion primitives: 8
- **Total implemented: 34**

## Verification

```bash
python -c "import pathlib,re; t=pathlib.Path('PRIMITIVES.md').read_text(); a=t.split('## Existing primitives',1)[1].split('## Implemented expansion primitives',1)[0]; b=t.split('## Implemented expansion primitives',1)[1].split('## Count',1)[0]; ids=[int(x) for x in re.findall(r'^\| P(\d+) \|', a+b, re.M)]; assert len(ids)==34, f'count={len(ids)}'; assert len(ids)==len(set(ids)), f'duplicates={ids}'; assert set(ids)==set(range(1,35)), f'missing/extra={set(range(1,35))^set(ids)}'; print('34 primitives verified: unique, complete P1-P34')"
```
