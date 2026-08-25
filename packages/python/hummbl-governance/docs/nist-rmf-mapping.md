# NIST AI RMF Mapping — hummbl-governance v1.2.2

**Reference:** NIST AI 100-1 (2023), AI Risk Management Framework
**Generated:** 2026-05-14
**Coverage:** 8 sub-controls across 4 core functions

---

## Core Functions

### GOVERN

| Sub-Control | Primitive(s) | Test Evidence |
|---|---|---|
| GOVERN 1.1 — AI risk management policies | INTENT tuples prove stated objectives | `test_intent_maps_to_govern_1_1` |
| GOVERN 1.7 — Processes for risk identification | CircuitBreaker + KillSwitch events | `test_circuit_breaker_maps_to_govern_1_7`, `test_killswitch_maps_to_govern_1_7_and_manage_1_3` |

### MAP

| Sub-Control | Primitive(s) | Test Evidence |
|---|---|---|
| MAP 1.1 — Organizational context | CONTRACT, DCTX, DCT tuples | `test_dct_maps_to_map_1_1`, `test_dctx_maps_to_map_1_1`, `test_contract_maps_to_map_1_1` |
| MAP 2.2 — Scientific basis for risk assessment | ATTEST, EVIDENCE tuples | `test_attest_maps_to_map_2_2` |

### MEASURE

| Sub-Control | Primitive(s) | Test Evidence |
|---|---|---|
| MEASURE 2.5 — Trustworthiness evaluations | Signed governance entries | `test_signed_maps_to_measure_2_5` |
| MEASURE 2.8 — Impact metrics logged | CostGovernor events | `test_cost_governor_maps_to_measure_2_8` |

### MANAGE

| Sub-Control | Primitive(s) | Test Evidence |
|---|---|---|
| MANAGE 1.3 — Response plans executed | KillSwitch events | `test_killswitch_maps_to_govern_1_7_and_manage_1_3` |
| MANAGE 2.4 — Risk treatment applied | CircuitBreaker state transitions | `test_circuit_breaker_maps_to_manage_2_4` |

---

## Gaps

The following NIST AI RMF sub-controls are not yet explicitly mapped:

- GOVERN 1.2–1.6 (accountability structures, risk culture, organizational integration)
- MAP 2.1 (AI system context and classification granularity)
- MEASURE 2.1–2.4, 2.6, 2.7 (measurement methodology, calibration, validity, reliability)
- MANAGE 1.1, 1.2, 1.4 (risk prioritization, treatment planning, communication)
- MANAGE 2.1–2.3 (monitoring, incident response, recovery)

These gaps largely reflect organizational and process controls that a software library cannot fully address. Mapping is scoped to the sub-controls where code-level governance primitives produce direct technical evidence.

---

## Usage

```bash
python -m hummbl_governance.compliance_mapper --framework nist-rmf --dir /path/to/governance_dir
```

Generates a `ComplianceReport` with per-function JSON output.

---

## Boundary

NIST AI RMF is a **voluntary guidance framework**, not a regulation. This mapping produces technical evidence aligned to NIST AI 100-1 (2023). It does not constitute a formal RMF assessment or certification. Organizations should supplement code-level evidence with organizational process documentation for full RMF alignment.
