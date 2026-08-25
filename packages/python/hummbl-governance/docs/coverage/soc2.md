# SOC 2 Coverage Matrix — HUMMBL

**Standard**: SOC 2 — AICPA Trust Services Criteria (2017, updated 2022). Used by service organizations to report on internal controls relevant to security, availability, processing integrity, confidentiality, privacy.
**Source**: https://www.aicpa-cima.com/topic/audit-assurance/audit-and-assurance-greater-than-soc-2
**Last reviewed**: 2026-05-14
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v1.2.2

## Boundary disclaimer

HUMMBL is **not** a SOC 2 attestation. SOC 2 reports are issued only by licensed CPA firms (e.g., A-LIGN, Deloitte, EY) following an examination per AICPA Statements on Standards for Attestation Engagements (SSAE) No. 21. A SOC 2 report covers a specific service organization, a specific service, a specific time period (Type 1: point-in-time; Type 2: 6-12 months operating effectiveness), and a specific subset of Trust Services Criteria (Common Criteria + optionally Availability/Processing Integrity/Confidentiality/Privacy).

This matrix maps HUMMBL technical primitives to the SOC 2 criteria. **The matrix does not constitute a SOC 2 report.** A customer organization seeking SOC 2 attestation must engage a CPA firm separately; HUMMBL provides evidence artifacts that support such an engagement.

## Structure

SOC 2 Trust Services Criteria (TSC):
- **Common Criteria (CC)** — required for every SOC 2 engagement, ~33 criteria across 9 sections (CC1–CC9)
- **Availability (A)** — optional, 3 criteria
- **Processing Integrity (PI)** — optional, 5 criteria
- **Confidentiality (C)** — optional, 2 criteria
- **Privacy (P)** — optional, 8 sections × multiple criteria (~18 total)

Total addressed in this matrix: 51 criteria (CC + A + PI + C + P core).

## Summary

| TSC | Criteria | ✅ | 🟡 | ⚪ |
|---|---|---|---|---|
| CC1 — Control Environment | 5 | 0 | 3 | 2 |
| CC2 — Communication + Information | 3 | 1 | 1 | 1 |
| CC3 — Risk Assessment | 4 | 2 | 2 | 0 |
| CC4 — Monitoring Activities | 2 | 2 | 0 | 0 |
| CC5 — Control Activities | 3 | 2 | 1 | 0 |
| CC6 — Logical + Physical Access Controls | 8 | 6 | 1 | 1 |
| CC7 — System Operations | 5 | 4 | 1 | 0 |
| CC8 — Change Management | 1 | 1 | 0 | 0 |
| CC9 — Risk Mitigation | 2 | 1 | 1 | 0 |
| A — Availability | 3 | 2 | 1 | 0 |
| PI — Processing Integrity | 5 | 4 | 1 | 0 |
| C — Confidentiality | 2 | 2 | 0 | 0 |
| P — Privacy (8 sections) | 8 | 6 | 2 | 0 |
| **Totals** | **51** | **33** | **14** | **4** |

**Draft coverage intent (not public claim): every Common Criterion + core TSC criterion has a row. Concentration of ✅ in CC6 (Access Control), CC7 (Operations), Availability, Processing Integrity, Confidentiality — the technically-implementable criteria.

---

## CC1 — Control Environment (5)

| ID | Description | Coverage | Evidence |
|---|---|---|---|
| CC1.1 | COSO Integrity + ethical values — leadership | ⚪ Boundary | |
| CC1.2 | Board oversight | ⚪ Boundary | |
| CC1.3 | Org structure + reporting via DCTX; structure design is org | 🟡 Partial | `hummbl_governance/delegation.py` |
| CC1.4 | Commitment to competence — HR + DCT-based role binding | 🟡 Partial | `hummbl_governance/delegation.py` |
| CC1.5 | Accountability assignment — DCT-based role binding + scope accountability; full COSO accountability framework is org | 🟡 Partial | `hummbl_governance/delegation.py` |

## CC2 — Communication and Information (3)

| ID | Description | Coverage | Evidence |
|---|---|---|---|
| CC2.1 | Information requirements + sources | ✅ tuple-schema enforced data quality | `hummbl_governance/schema_validator.py`, `hummbl_governance/audit_log.py` |
| CC2.2 | Internal communication — bus = comms substrate; comms practice is org | 🟡 Partial | `hummbl_governance/coordination_bus.py`, `hummbl_governance/audit_log.py` |
| CC2.3 | External communication | ⚪ Boundary | |

## CC3 — Risk Assessment (4)

| ID | Description | Coverage | Evidence |
|---|---|---|---|
| CC3.1 | Risk objectives + categories — `INTENT` + adverse-event tuples (risk-register integration per Krineia connector spec) | 🟡 Partial | `hummbl_governance/audit_log.py` |
| CC3.2 | Identify + analyze risks | ✅ risk-identification tuples + analysis primitives | `hummbl_governance/audit_log.py` |
| CC3.3 | Fraud risk — fraud-flag tuples; assessment is org | 🟡 Partial | `hummbl_governance/audit_log.py` |
| CC3.4 | Significant change in risk profile — change-event triggers | ✅ change-event triggers via health-state transitions + audit-log change records | `hummbl_governance/health_probe.py`, `hummbl_governance/audit_log.py` |

## CC4 — Monitoring Activities (2)

| ID | Description | Coverage | Evidence |
|---|---|---|---|
| CC4.1 | Ongoing + separate evaluations | ✅ governance bus + audit-log queries | `hummbl_governance/coordination_bus.py`, `hummbl_governance/audit_log.py` |
| CC4.2 | Evaluate + communicate deficiencies | ✅ deficiency tuples + escalation | `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py` |

## CC5 — Control Activities (3)

| ID | Description | Coverage | Evidence |
|---|---|---|---|
| CC5.1 | Selection + development of controls | ✅ control-catalog tuples | `hummbl_governance/audit_log.py`, `hummbl_governance/schema_validator.py` |
| CC5.2 | Selection + development of technology controls | ✅ primitives shipped + tested | `.github/workflows/ci.yml` |
| CC5.3 | Deployment through policies + procedures — policy authorship is org | 🟡 Partial | `hummbl_governance/audit_log.py`, `hummbl_governance/schema_validator.py` |

## CC6 — Logical and Physical Access Controls (8) — **load-bearing**

| ID | Description | Coverage | Evidence |
|---|---|---|---|
| CC6.1 | Logical access security | ✅ DCT delegation + ops_allowed | `hummbl_governance/delegation.py` |
| CC6.2 | Authorization + registration of users | ✅ DCT issuance | `hummbl_governance/delegation.py` |
| CC6.3 | Authentication credentials | ✅ HMAC-SHA256 signed tokens | `hummbl_governance/delegation.py` |
| CC6.4 | Physical access — facility security | ⚪ Boundary | |
| CC6.5 | Logical access prevented when no longer required | ✅ DCT revocation | `hummbl_governance/delegation.py` |
| CC6.6 | Logical access restricted via boundary protections | ✅ DCT scope binding | `hummbl_governance/delegation.py` |
| CC6.7 | Transmission + movement of information | ✅ TLS + signed tuples | `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py` |
| CC6.8 | Prevention/detection of unauthorized software — stdlib-only at app layer; OS layer is platform | 🟡 Partial | `hummbl_governance/capability_fence.py` |

## CC7 — System Operations (5)

| ID | Description | Coverage | Evidence |
|---|---|---|---|
| CC7.1 | Detection of new vulnerabilities | ✅ `pip-audit` blocking + Bandit + Semgrep | `.github/workflows/ci.yml`, `hummbl_governance/audit_log.py` |
| CC7.2 | Monitoring + analysis of security events | ✅ governance bus monitoring | `hummbl_governance/coordination_bus.py`, `hummbl_governance/audit_log.py` |
| CC7.3 | Incident management procedures | ✅ IR tuple chain | `hummbl_governance/audit_log.py`, `hummbl_governance/kill_switch.py` |
| CC7.4 | Incident communications | ✅ incident-comm tuple + escalation | `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py` |
| CC7.5 | Recovery — backup integrity is infra; service-level recovery covered | 🟡 Partial | `hummbl_governance/circuit_breaker.py`, `hummbl_governance/audit_log.py` |

## CC8 — Change Management (1)

| ID | Description | Coverage | Evidence |
|---|---|---|---|
| CC8.1 | Change management process | ✅ change tuples + signed audit trail + Conventional Commits + PR review | `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py` |

## CC9 — Risk Mitigation (2)

| ID | Description | Coverage | Evidence |
|---|---|---|---|
| CC9.1 | Risk mitigation activities | ✅ risk-treatment tuple + circuit-breaker primitives | `hummbl_governance/audit_log.py`, `hummbl_governance/circuit_breaker.py` |
| CC9.2 | Vendor + business partner risk — supplier-DCT + SBOM; due-diligence program is org | 🟡 Partial | `hummbl_governance/delegation.py` |

## Availability (A) — 3 criteria

| ID | Description | Coverage | Evidence |
|---|---|---|---|
| A1.1 | Capacity demand + management | ✅ capacity-monitoring tuples + circuit-breaker overload handling | `hummbl_governance/circuit_breaker.py`, `hummbl_governance/audit_log.py` |
| A1.2 | Environmental protection + recovery — backup infra is platform | 🟡 Partial | `hummbl_governance/circuit_breaker.py`, `hummbl_governance/health_probe.py` |
| A1.3 | Recovery + business continuity | ✅ circuit-breaker state machine + IR recovery tuples | `hummbl_governance/circuit_breaker.py`, `hummbl_governance/audit_log.py` |

## Processing Integrity (PI) — 5 criteria

| ID | Description | Coverage | Evidence |
|---|---|---|---|
| PI1.1 | Procedures to ensure complete, valid, accurate inputs | ✅ tuple-schema validation at ingress | `hummbl_governance/schema_validator.py` |
| PI1.2 | Procedures to detect + correct errors during processing | ✅ error tuples + correction primitives | `hummbl_governance/audit_log.py` |
| PI1.3 | Procedures to ensure complete, valid, accurate processing | ✅ append-only + signed processing tuples | `hummbl_governance/audit_log.py` |
| PI1.4 | Outputs delivered timely, complete, accurate — delivery-confirmation tuples; SLA tracking is config | 🟡 Partial | `hummbl_governance/output_validator.py`, `hummbl_governance/audit_log.py` |
| PI1.5 | Procedures protect data inputs, processing, outputs through retention | ✅ Append-only governance bus + signed entries + retention policy | `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py` |

## Confidentiality (C) — 2 criteria

| ID | Description | Coverage | Evidence |
|---|---|---|---|
| C1.1 | Confidential information identified + protected | ✅ classification tag + restricted access via DCT | `hummbl_governance/schema_validator.py`, `hummbl_governance/delegation.py` |
| C1.2 | Confidential information retained, transferred, destroyed per agreements + retention policies | ✅ retention/erasure tuples | `hummbl_governance/audit_log.py` |

## Privacy (P) — 8 sections, ~18 criteria

The Privacy TSC overlaps heavily with GDPR; rows summarized here, with detail in [`gdpr.md`](./gdpr.md).

| Section | Topic | Coverage | Evidence |
|---|---|---|---|
| P1 — Privacy notice | Provide notice + obtain consent | ✅ (cross-ref GDPR Art. 13/14, Art. 7) | `hummbl_governance/audit_log.py`, `hummbl_governance/schema_validator.py` |
| P2 — Choice + consent | Obtain consent, communicate purposes, document refusal | ✅ Consent-record tuples | `hummbl_governance/audit_log.py` |
| P3 — Collection | Limit collection to identified purposes | ✅ Tuple-schema enforces declared-field-only | `hummbl_governance/schema_validator.py` |
| P4 — Use, retention, disposal | Use only for stated purposes, retain only as needed, dispose securely | ✅ Purpose-tag + retention + erasure tuples | `hummbl_governance/audit_log.py` |
| P5 — Access | Provide individuals access to their info | ✅ DSAR export (GDPR Art. 15) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| P6 — Disclosure to third parties | Disclose only per purposes + consent | 🟡 Partial: disclosure tuples + downstream DCT propagation | `hummbl_governance/delegation.py`, `hummbl_governance/audit_log.py` |
| P7 — Quality | Maintain accuracy + completeness | ✅ Rectification tuple | `hummbl_governance/audit_log.py` |
| P8 — Monitoring + enforcement | Monitor compliance, address complaints + violations | 🟡 Partial: monitoring tuples + complaint-intake; resolution is org | `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py` |

Per the GDPR matrix, the technical privacy criteria are ✅ Fulfilled. The boundary rows in P6-P8 reflect customer-org policies and program execution.

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Prior partial mapping: `docs/soc2-mapping.md`
- Privacy criteria detail in [`gdpr.md`](./gdpr.md)
- Security overlap with [`iso-27001.md`](./iso-27001.md) Annex A
