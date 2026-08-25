# NIST CSF 2.0 Coverage Matrix — HUMMBL

**Standard**: NIST Cybersecurity Framework 2.0 — February 2024
**Source**: https://nvlpubs.nist.gov/nistpubs/CSWP/NIST.CSWP.29.pdf
**Last reviewed**: 2026-05-14
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

NIST CSF 2.0 is **voluntary** guidance, not a regulation. No certification body. CSF 2.0 introduced a new GOVERN Function (Tier 0) and reorganized categories from CSF 1.1. This matrix maps technical primitives to the 6 Functions, 22 Categories, and 106 Subcategories of CSF 2.0.

## Structure

- 6 Functions: GOVERN (GV), IDENTIFY (ID), PROTECT (PR), DETECT (DE), RESPOND (RS), RECOVER (RC)
- 22 Categories (e.g., GV.OC = Organizational Context)
- 106 Subcategories (e.g., GV.OC-01)

## Summary

| Function | Categories | Subcategories | ✅ | 🟡 | ⚪ |
|---|---|---|---|---|---|
| GOVERN (GV) | 6 | 31 | 7 | 17 | 7 |
| IDENTIFY (ID) | 3 | 21 | 15 | 6 | 0 |
| PROTECT (PR) | 5 | 22 | 12 | 6 | 4 |
| DETECT (DE) | 2 | 11 | 8 | 3 | 0 |
| RESPOND (RS) | 4 | 13 | 11 | 2 | 0 |
| RECOVER (RC) | 2 | 8 | 3 | 4 | 1 |
| **Totals** | **22** | **106** | **56** | **38** | **12** |

**Draft coverage intent (not public claim): every subcategory has a row. Load-bearing primitives concentrate in PROTECT (PR.AA Access Control, PR.DS Data Security, PR.IR Resilience), DETECT (governance bus = monitoring substrate), and RESPOND (incident-response primitives).

---

## GOVERN (GV) — 6 Categories, 31 Subcategories

### GV.OC — Organizational Context (5)

| ID | Subcategory | Coverage | Evidence |
|---|---|---|---|
| GV.OC-01 | Organizational mission understood, informs cybersecurity risk mgmt | ⚪ Boundary: mission articulation | |
| GV.OC-02 | Internal/external stakeholders + their requirements understood | 🟡 Partial: internal stakeholder mapping via identity registry + delegation chain; external stakeholders are org | `hummbl_governance/identity.py`, `hummbl_governance/delegation.py` |
| GV.OC-03 | Legal/regulatory/contractual requirements understood + managed | 🟡 Partial: compliance registry mapping; legal interpretation is org | `hummbl_governance/compliance_mapper.py` |
| GV.OC-04 | Critical objectives, capabilities, services identified + communicated | 🟡 Partial: criticality-tag tuples; comms is org | `hummbl_governance/audit_log.py`, `hummbl_governance/schema_validator.py` |
| GV.OC-05 | Outcomes, capabilities, services that org depends on understood | 🟡 Partial: dependency-map tuples | `hummbl_governance/audit_log.py` |

### GV.RM — Risk Management Strategy (7)

| ID | Subcategory | Coverage | Evidence |
|---|---|---|---|
| GV.RM-01 | Risk management objectives established | ⚪ Boundary: risk objectives established by org | |
| GV.RM-02 | Risk appetite + tolerance defined | 🟡 Partial: cost-threshold tolerance via cost governor; full risk appetite is org | `hummbl_governance/cost_governor.py` |
| GV.RM-03 | Risk management processes + activities structured + standardized | 🟡 Partial: governance lifecycle structures RM activities; full org RM process is org | `hummbl_governance/lifecycle.py` |
| GV.RM-04 | Strategic direction + objectives inform risk management | ⚪ Boundary: strategic direction + objectives | |
| GV.RM-05 | Risk management processes communicated + roles assigned | 🟡 Partial: role assignment via DCT + comms via bus; comms cadence is org | `hummbl_governance/delegation.py`, `hummbl_governance/coordination_bus.py` |
| GV.RM-06 | Standardized method for calculating + prioritizing risks | 🟡 Partial: STRIDE threat prioritization with risk levels; full quantitative risk calculation is org | `hummbl_governance/stride_mapper.py` |
| GV.RM-07 | Strategic opportunities (positive risks) characterized | ✅ opportunity tuples | `hummbl_governance/audit_log.py` |

### GV.RR — Roles, Responsibilities, Authorities (4)

| ID | Subcategory | Coverage | Evidence |
|---|---|---|---|
| GV.RR-01 | Cybersecurity roles + responsibilities + authorities established | ✅ DCT chain: role binding (issuer/subject), responsibilities (scope, resource_selectors), authorities (ops_allowed) | `hummbl_governance/delegation.py` |
| GV.RR-02 | Cybersecurity leadership accountable for outcomes | ⚪ Boundary: leadership accountability | |
| GV.RR-03 | Workforce cybersecurity roles + responsibilities + authorities defined | 🟡 Partial: agent-role tuples with trust tiers + authority scope; HR is org | `hummbl_governance/kernel/identity_engine.py`, `hummbl_governance/kernel/authority_engine.py` |
| GV.RR-04 | Cybersecurity in HR practices | ✅ onboarding-DCT + offboarding-revocation | `hummbl_governance/delegation.py` |

### GV.PO — Policy (2)

| ID | Subcategory | Coverage | Evidence |
|---|---|---|---|
| GV.PO-01 | Cybersecurity policy established + communicated | 🟡 Partial: policy encoding via doctrine/law engine; authorship is org | `hummbl_governance/kernel/doctrine_engine.py`, `hummbl_governance/kernel/law_engine.py` |
| GV.PO-02 | Cybersecurity policy reviewed + updated | 🟡 Partial: doctrine/law engines support policy updates + law atlas reload; review cadence is org | `hummbl_governance/kernel/doctrine_engine.py`, `hummbl_governance/kernel/law_engine.py` |

### GV.OV — Oversight (3)

| ID | Subcategory | Coverage | Evidence |
|---|---|---|---|
| GV.OV-01 | Cybersecurity strategy reviewed + adjusted | ⚪ Boundary: strategy review | |
| GV.OV-02 | Cybersecurity risk management results reported + reviewed | 🟡 Partial: results reported via audit log + coordination bus; review by leadership is org | `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py` |
| GV.OV-03 | Cybersecurity risk management performance monitored + reported | 🟡 Partial: performance metrics from health probes + schedule engine; review is org | `hummbl_governance/health_probe.py`, `hummbl_governance/kernel/schedule_engine.py` |

### GV.SC — Cybersecurity Supply Chain Risk Management (10)

| ID | Subcategory | Coverage | Evidence |
|---|---|---|---|
| GV.SC-01 | C-SCRM strategy established + communicated | ⚪ Boundary: C-SCRM strategy | |
| GV.SC-02 | Suppliers identified + prioritized | ✅ Supplier-DCT identification + prioritization | `hummbl_governance/delegation.py` |
| GV.SC-03 | C-SCRM integrated into cybersecurity risk management | ⚪ Boundary: org C-SCRM integration | |
| GV.SC-04 | Suppliers known + prioritized by criticality | ✅ supplier-DCT criticality field | `hummbl_governance/delegation.py` |
| GV.SC-05 | Supplier-contract requirements established | 🟡 Partial: DCT scope binding + contract-net task requirements; legal contract terms are org | `hummbl_governance/delegation.py`, `hummbl_governance/contract_net.py` |
| GV.SC-06 | Planning + due diligence on supplier risk | 🟡 Partial: STRIDE threat analysis for supplier interactions; due diligence process is org | `hummbl_governance/stride_mapper.py` |
| GV.SC-07 | Risks from suppliers monitored | ✅ supplier-activity tuples | `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py` |
| GV.SC-08 | Suppliers integrated into incident response + BCP | 🟡 Partial: supplier IR-integration via coordination bus; BCP is org | `hummbl_governance/coordination_bus.py` |
| GV.SC-09 | Supply chain practices in lifecycle | 🟡 Partial: supplier lifecycle management; full C-SCRM practices are org | `hummbl_governance/lifecycle.py` |
| GV.SC-10 | End-of-relationship supplier management | ✅ DCT revocation for end-of-relationship supplier management | `hummbl_governance/delegation.py` |

## IDENTIFY (ID) — 3 Categories, 21 Subcategories

### ID.AM — Asset Management (8)

| ID | Subcategory | Coverage | Evidence |
|---|---|---|---|
| ID.AM-01 | Inventories of HW maintained | ✅ Asset-tuple (HW) | `hummbl_governance/audit_log.py` |
| ID.AM-02 | Inventories of SW, services, systems maintained | ✅ Asset-tuple (SW) + SBOM | `hummbl_governance/audit_log.py`, `hummbl_governance/schema_validator.py` |
| ID.AM-03 | Representations of authorized network communication + data flows | ✅ Data-flow tuples per processing activity | `hummbl_governance/audit_log.py` |
| ID.AM-04 | Inventories of services provided by suppliers maintained | ✅ Supplier-service tuple | `hummbl_governance/audit_log.py` |
| ID.AM-05 | Assets prioritized based on classification, criticality, resources, impact | ✅ Asset-priority field | `hummbl_governance/schema_validator.py` |
| ID.AM-07 | Inventories of data + corresponding metadata maintained | ✅ Data inventory tuples | `hummbl_governance/audit_log.py` |
| ID.AM-08 | Systems, HW, SW, services, data managed throughout lifecycle | ✅ Lifecycle-tuple chain | `hummbl_governance/lifecycle.py`, `hummbl_governance/audit_log.py` |

### ID.RA — Risk Assessment (10)

| ID | Subcategory | Coverage | Evidence |
|---|---|---|---|
| ID.RA-01 | Vulnerabilities in assets identified, validated, recorded | ✅ Vulnerability tuple + `pip-audit` integration | `hummbl_governance/audit_log.py`, `.github/workflows/ci.yml` |
| ID.RA-02 | Cyber threat intelligence received from info-sharing forums | 🟡 Partial: STRIDE threat mapping for ingested intel; forum participation is org | `hummbl_governance/stride_mapper.py` |
| ID.RA-03 | Internal + external threats identified + recorded | ✅ STRIDE threat identification + recording | `hummbl_governance/stride_mapper.py` |
| ID.RA-04 | Potential impacts + likelihoods of threats exploiting vulns identified + recorded | 🟡 Partial: STRIDE risk-level assignment (LOW–CRITICAL); separate likelihood analysis is org | `hummbl_governance/stride_mapper.py` |
| ID.RA-05 | Threats, vulns, likelihoods, impacts used to understand inherent risk + inform risk response | 🟡 Partial: governance lifecycle composes risk primitives; inherent risk analysis is org | `hummbl_governance/lifecycle.py` |
| ID.RA-06 | Risk responses chosen, prioritized, planned, tracked, communicated | ✅ Response-tracking tuple | `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py` |
| ID.RA-07 | Changes + exceptions managed, assessed for risk impact, recorded, tracked | ✅ Change tuple + risk-impact field | `hummbl_governance/audit_log.py` |
| ID.RA-08 | Processes for receiving, analyzing, responding to vulnerability disclosures established | 🟡 Partial: disclosure-receipt tuples via audit log; full disclosure program is org | `hummbl_governance/audit_log.py` |
| ID.RA-09 | Authenticity + integrity of HW + SW assessed prior to acquisition + use | ✅ Signed-bundle verification + integrity checks | `hummbl_governance/delegation.py`, `hummbl_governance/schema_validator.py` |
| ID.RA-10 | Critical suppliers assessed prior to acquisition | 🟡 Partial: STRIDE threat analysis for supplier interactions; acquisition process is org | `hummbl_governance/stride_mapper.py` |

### ID.IM — Improvement (3)

| ID | Subcategory | Coverage | Evidence |
|---|---|---|---|
| ID.IM-01 | Improvements identified from evaluations | ✅ Improvement tuple | `hummbl_governance/audit_log.py` |
| ID.IM-02 | Improvements identified from security tests + exercises | ✅ Test-result-improvement tuple | `hummbl_governance/audit_log.py`, `.github/workflows/ci.yml` |
| ID.IM-03 | Improvements identified from execution of operational processes, procedures, activities | ✅ Operational-improvement tuple | `hummbl_governance/audit_log.py` |
| ID.IM-04 | Incident response plans + plans-of-action established + improved | 🟡 Partial: governance lifecycle orchestrates IR execution; plan authorship is org | `hummbl_governance/lifecycle.py` |

## PROTECT (PR) — 5 Categories, 22 Subcategories

### PR.AA — Identity Management, Authentication, Access Control (6)

| ID | Subcategory | Coverage | Evidence |
|---|---|---|---|
| PR.AA-01 | Identities + credentials issued, managed, verified, revoked, audited | ✅ DCT lifecycle (issue, sign, verify, revoke, audit) | `hummbl_governance/delegation.py` |
| PR.AA-02 | Identities proofed + bound to credentials based on context | ✅ DCT issuer-binding | `hummbl_governance/delegation.py` |
| PR.AA-03 | Users + services + HW authenticated | ✅ HMAC-SHA256 token verification | `hummbl_governance/delegation.py` |
| PR.AA-04 | Identity assertions protected, conveyed, verified | ✅ Signed delegation chain | `hummbl_governance/delegation.py` |
| PR.AA-05 | Access permissions + entitlements + authorizations defined in policy, managed, enforced + reviewed | ✅ DCT ops_allowed + resource_selectors + scope-review queries | `hummbl_governance/delegation.py` |
| PR.AA-06 | Physical access to assets managed, monitored, enforced commensurate with risk | 🟡 Partial: physical governor manages proximity + safety modes for physical AI; facility access control is org | `hummbl_governance/physical_governor.py` |

### PR.AT — Awareness and Training (2)

| ID | Subcategory | Coverage | Evidence |
|---|---|---|---|
| PR.AT-01 | Personnel provided awareness + training to perform security duties | ⚪ Boundary: training program | |
| PR.AT-02 | Individuals in specialized roles provided awareness + training | ⚪ Boundary: specialized training | |

### PR.DS — Data Security (6)

| ID | Subcategory | Coverage | Evidence |
|---|---|---|---|
| PR.DS-01 | Confidentiality, integrity, availability of data-at-rest protected | ✅ Append-only + signed entries + encryption-at-rest (configurable) | `hummbl_governance/audit_log.py` |
| PR.DS-02 | Confidentiality, integrity, availability of data-in-transit protected | ✅ TLS + signed tuples | `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py` |
| PR.DS-10 | Confidentiality, integrity, availability of data-in-use protected | 🟡 Partial: signed-tuples in-memory; full DIU protection is platform | `hummbl_governance/audit_log.py` |
| PR.DS-11 | Backups created, protected, maintained, tested | 🟡 Partial: append-only log as governance-data backup; full backup infra is platform | `hummbl_governance/audit_log.py` |

### PR.PS — Platform Security (6)

| ID | Subcategory | Coverage | Evidence |
|---|---|---|---|
| PR.PS-01 | Configuration management practices established + applied | ✅ Config-tuple + change tracking | `hummbl_governance/audit_log.py` |
| PR.PS-02 | Software maintained, replaced, removed commensurate with risk | ✅ SBOM-driven dep updates + `pip-audit` | `hummbl_governance/schema_validator.py`, `.github/workflows/ci.yml` |
| PR.PS-03 | Hardware maintained, replaced, removed commensurate with risk | ⚪ Boundary: HW lifecycle | |
| PR.PS-04 | Log records generated + made available for continuous monitoring | ✅ Governance bus = continuous log | `hummbl_governance/coordination_bus.py`, `hummbl_governance/audit_log.py` |
| PR.PS-05 | Installation + execution of unauthorized software prevented | 🟡 Partial: capability fence enforces allow/deny lists at app layer; OS-level enforcement is platform | `hummbl_governance/capability_fence.py` |
| PR.PS-06 | Secure software development practices integrated, performance monitored throughout SDLC | ✅ TDD + CI gates + 17,500+ tests | `.github/workflows/ci.yml` |

### PR.IR — Technology Infrastructure Resilience (4)

| ID | Subcategory | Coverage | Evidence |
|---|---|---|---|
| PR.IR-01 | Networks + environments protected from unauthorized logical access + usage | 🟡 Partial: DCT + ops_allowed + capability fence at app layer; network layer is infra | `hummbl_governance/delegation.py`, `hummbl_governance/capability_fence.py` |
| PR.IR-02 | Org's technology assets protected from environmental threats | ⚪ Boundary: physical/environmental | |
| PR.IR-03 | Mechanisms implemented for resilience to support availability + meet RTO/RPO | ✅ Circuit-breaker + CLOSED/HALF_OPEN/OPEN state machine | `hummbl_governance/circuit_breaker.py` |
| PR.IR-04 | Adequate resource capacity to ensure availability maintained | 🟡 Partial: health probes + cost governor monitor capacity; capacity planning is org | `hummbl_governance/health_probe.py`, `hummbl_governance/cost_governor.py` |

## DETECT (DE) — 2 Categories, 11 Subcategories

### DE.CM — Continuous Monitoring (9)

| ID | Subcategory | Coverage | Evidence |
|---|---|---|---|
| DE.CM-01 | Networks + network services monitored to find potentially adverse events | 🟡 Partial: app-layer monitoring via governance bus + audit log; network-layer monitoring is infra | `hummbl_governance/coordination_bus.py`, `hummbl_governance/audit_log.py` |
| DE.CM-02 | Physical environment monitored | 🟡 Partial: physical governor monitors proximity + collision for physical AI; full facility monitoring (CCTV, sensors) is org | `hummbl_governance/physical_governor.py` |
| DE.CM-03 | Personnel activity + technology usage monitored | ✅ Activity tuples per actor (DCT subject) | `hummbl_governance/audit_log.py`, `hummbl_governance/delegation.py` |
| DE.CM-06 | External service-provider activities + services monitored | ✅ Supplier-activity tuples | `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py` |
| DE.CM-09 | Computing HW + SW, runtime envs, their data monitored | ✅ Runtime-activity tuples | `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py` |

### DE.AE — Adverse Event Analysis (8)

| ID | Subcategory | Coverage | Evidence |
|---|---|---|---|
| DE.AE-02 | Potentially adverse events analyzed to better understand activities | ✅ Event-analysis tuples | `hummbl_governance/audit_log.py` |
| DE.AE-03 | Information correlated from multiple sources | ✅ Cross-source correlation queries | `hummbl_governance/audit_log.py` |
| DE.AE-04 | Estimated impact + scope of adverse events understood | ✅ Impact-estimate tuple | `hummbl_governance/audit_log.py` |
| DE.AE-06 | Information on adverse events provided to authorized staff + tools | ✅ Authorized-disclosure tuples | `hummbl_governance/audit_log.py`, `hummbl_governance/delegation.py` |
| DE.AE-07 | Cyber threat intelligence + other contextual info integrated into analysis | 🟡 Partial: STRIDE threat integration into analysis; analyst workflow is org | `hummbl_governance/stride_mapper.py` |
| DE.AE-08 | Incidents declared when adverse events meet defined criteria | ✅ Incident-declaration tuple + threshold rules | `hummbl_governance/audit_log.py`, `hummbl_governance/schema_validator.py` |

## RESPOND (RS) — 4 Categories, 13 Subcategories

### RS.MA — Incident Management (5)

| ID | Subcategory | Coverage | Evidence |
|---|---|---|---|
| RS.MA-01 | Incident response plan executed | ✅ IR-execution tuple chain | `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py` |
| RS.MA-02 | Incident reports triaged + validated | ✅ Triage tuple + validation field | `hummbl_governance/audit_log.py` |
| RS.MA-03 | Incidents categorized + prioritized | ✅ Incident category + priority fields | `hummbl_governance/audit_log.py`, `hummbl_governance/schema_validator.py` |
| RS.MA-04 | Incidents escalated + elevated as needed | ✅ Escalation tuple | `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py` |
| RS.MA-05 | Criteria for initiating recovery applied | ✅ Recovery-initiation tuple | `hummbl_governance/audit_log.py` |

### RS.AN — Incident Analysis (4)

| ID | Subcategory | Coverage | Evidence |
|---|---|---|---|
| RS.AN-03 | Analysis performed to establish what has taken place + scope of incident | ✅ Forensic-analysis tuples; append-only bus = strong evidence | `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py` |
| RS.AN-06 | Actions performed during investigation recorded, integrity preserved | ✅ Investigation-action tuples (append-only) | `hummbl_governance/audit_log.py` |
| RS.AN-07 | Incident data + metadata collected, integrity preserved | ✅ Evidence-collection tuple | `hummbl_governance/audit_log.py` |
| RS.AN-08 | Magnitude of incident estimated + validated | ✅ Magnitude-estimate tuple | `hummbl_governance/audit_log.py` |

### RS.CO — Incident Response Reporting + Communication (2)

| ID | Subcategory | Coverage | Evidence |
|---|---|---|---|
| RS.CO-02 | Internal + external stakeholders notified per response procedures | 🟡 Partial: notification via coordination bus; comms-program is org | `hummbl_governance/coordination_bus.py` |
| RS.CO-03 | Information shared with designated stakeholders | ✅ Information-sharing via coordination bus | `hummbl_governance/coordination_bus.py` |

### RS.MI — Incident Mitigation (2)

| ID | Subcategory | Coverage | Evidence |
|---|---|---|---|
| RS.MI-01 | Incidents contained | ✅ Containment primitive: `kill_switch_core` (4 modes) | `hummbl_governance/kill_switch.py` |
| RS.MI-02 | Incidents eradicated | 🟡 Partial: kill switch halts activity; eradication remediation varies | `hummbl_governance/kill_switch.py` |

## RECOVER (RC) — 2 Categories, 8 Subcategories

### RC.RP — Incident Recovery Plan Execution (6)

| ID | Subcategory | Coverage | Evidence |
|---|---|---|---|
| RC.RP-01 | Recovery portion of IR plan executed once initiated by IR process | ✅ Recovery-plan execution tuple | `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py` |
| RC.RP-02 | Recovery actions selected, scoped, prioritized, performed | 🟡 Partial: governance lifecycle manages recovery execution; action selection is org | `hummbl_governance/lifecycle.py` |
| RC.RP-03 | Integrity of backups + other restoration assets verified before use | 🟡 Partial: integrity verification via signed entries; full backup infra is platform | `hummbl_governance/audit_log.py` |
| RC.RP-04 | Critical mission functions + cybersecurity risk mgmt considered in restoration of normal operating capabilities | 🟡 Partial: governance lifecycle tracks mission functions; consideration is org | `hummbl_governance/lifecycle.py` |
| RC.RP-05 | Integrity of restored assets verified, systems + services restored, normal status confirmed | ✅ Restoration-verification tuple | `hummbl_governance/audit_log.py` |
| RC.RP-06 | End of incident recovery declared based on criteria, incident-related documentation completed | ✅ Recovery-end-declaration tuple | `hummbl_governance/audit_log.py` |

### RC.CO — Incident Recovery Communication (2)

| ID | Subcategory | Coverage | Evidence |
|---|---|---|---|
| RC.CO-03 | Recovery activities + progress communicated to designated internal + external stakeholders | 🟡 Partial: recovery-progress comms via coordination bus; comms-program is org | `hummbl_governance/coordination_bus.py` |
| RC.CO-04 | Public updates on incident recovery shared using approved methods + messaging | ⚪ Boundary: public-comms approval is org | |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Prior partial mapping: `docs/nist-csf-mapping.md`
- ISO 27001 overlap significant in PROTECT — see [`iso-27001.md`](./iso-27001.md)
