# ISO 27001 Annex A Mapping — hummbl-governance v1.2.2

**Reference:** ISO/IEC 27001:2022, Annex A
**Generated:** 2026-05-14
**Coverage:** 6 control families (A.5–A.9, A.12), 10 dedicated tests

---

## Control Family Mappings

### A.5 — Information Security Policies
**Primitive:** INTENT tuples
**Evidence:** Stated objectives, purpose, and agent identity capture policy intent.
**Test:** `test_iso27001_intent_maps_to_a5`

### A.6 — Organization of Information Security
**Primitive:** DCTX tuples (DelegationTokenManager)
**Evidence:** Delegation chains prove organizational roles, separation of duties.
**Test:** `test_iso27001_dctx_maps_to_a6`

### A.7 — Human Resource Security
**Primitives:** DCT tuples, CONTRACT tuples
**Evidence:** Binding agreements between issuers and subjects with scoped operations.
**Tests:** `test_iso27001_dct_maps_to_a7`, `test_iso27001_contract_maps_to_a7`

### A.8 — Asset Management
**Primitives:** DCT tuples, ATTEST tuples
**Evidence:** Resource ownership tracking and evidence verification.
**Tests:** `test_iso27001_dct_maps_to_a8`, `test_iso27001_attest_maps_to_a8`

### A.9 — Access Control
**Primitive:** DCT tuples (DelegationTokenManager)
**Evidence:** ops_allowed field proves scoped, auditable access control.
**Test:** `test_iso27001_dct_maps_to_a9`

### A.12 — Operations Security (Logging & Monitoring)
**Primitives:** AuditLog, BusWriter
**Evidence:** Every signed governance entry provides continuous logging evidence.
**Test:** `test_iso27001_signed_maps_to_a12`

---

## Gaps

Annex A contains 93 controls. This mapping covers the 6 control families most directly addressable by code-level governance primitives for AI agent orchestration. Remaining controls (A.10–A.11 cryptography/physical, A.13–A.17 communications/acquisition/supplier/incident, A.18 compliance) require organizational process evidence beyond a software library.

---

## Usage

```bash
python -m hummbl_governance.compliance_mapper --framework iso27001 --days 30
```

## Boundary

HUMMBL is not an ISO 27001 certification body. This mapping produces technical evidence artifacts; ISO 27001 certification requires an accredited registrar.
