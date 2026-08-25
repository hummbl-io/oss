# NIST CSF 2.0 Mapping — hummbl-governance v1.2.2

**Reference:** NIST Cybersecurity Framework 2.0 (2024)
**Generated:** 2026-05-14
**Coverage:** 6 Functions (GOVERN, IDENTIFY, PROTECT, DETECT, RESPOND, RECOVER), 12 dedicated tests

---

## Function Mappings

### GOVERN (GV) — Organizational Context and Risk Strategy
**Primitives:** INTENT tuples, DCTX tuples (DelegationTokenManager)
**Evidence:** Stated objectives and organizational delegation structure.
**Tests:** `test_nist_csf_intent_maps_to_govern`, `test_nist_csf_dctx_maps_to_govern`

### IDENTIFY (ID) — Asset and Risk Identification
**Primitives:** DCT tuples, ATTEST tuples (AgentRegistry, DelegationTokenManager)
**Evidence:** Resource ownership tracking, identity binding, evidence verification.
**Test:** `test_nist_csf_dct_maps_to_identify_and_protect`

### PROTECT (PR) — Safeguards and Access Controls
**Primitives:** KillSwitch, CapabilityFence, DelegationTokenManager
**Evidence:** Graduated safeguards from capability denial to emergency halt.
**Tests:** `test_nist_csf_killswitch_maps_to_protect`, `test_nist_csf_dct_maps_to_identify_and_protect`

### DETECT (DE) — Continuous Monitoring and Anomaly Detection
**Primitives:** CircuitBreaker, HealthProbe, BehaviorMonitor
**Evidence:** Failure patterns, degradation signals, behavioral drift detection.
**Test:** `test_nist_csf_circuit_breaker_maps_to_detect`

### RESPOND (RS) — Incident Response
**Primitives:** KillSwitch (HALT_ALL/EMERGENCY), CircuitBreaker (OPEN)
**Evidence:** Automated and human-initiated incident response activation.
**Tests:** `test_nist_csf_killswitch_emergency_maps_to_respond`, `test_nist_csf_circuit_breaker_open_maps_to_respond`

### RECOVER (RC) — Restoration and Improvement
**Primitives:** CircuitBreaker (HALF_OPEN), CostGovernor
**Evidence:** Recovery attempts and budget reallocation after incidents.
**Tests:** `test_nist_csf_circuit_breaker_half_open_maps_to_recover`, `test_nist_csf_cost_governor_maps_to_recover`

---

## Gaps

Per-Category and per-Subcategory mapping is not provided. NIST CSF 2.0 Categories and Subcategories require per-organization customization. The Function-level mapping provides strategic evidence; tactical mapping requires organizational context.

---

## Usage

```bash
python -m hummbl_governance.compliance_mapper --framework nist-csf --days 30
```

## Boundary

NIST CSF is a voluntary guidance framework, not a regulation. This mapping produces technical evidence aligned to NIST CSF 2.0 (2024). It does not constitute a formal CSF assessment. Organizations should customize CSF profiles to their specific environment. Not to be confused with NIST AI RMF — a separate framework with its own dedicated implementation.
