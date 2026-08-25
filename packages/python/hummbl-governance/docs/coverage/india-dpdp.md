# India DPDP Act 2023 Coverage Matrix — HUMMBL

**Standard**: Digital Personal Data Protection Act, 2023 (Act No. 22 of 2023)
**Effective**: Enacted 11 August 2023; commencement notified in phases (core obligations effective 2025–2026 per DPDP Rules 2025)
**Source**: https://www.meity.gov.in/writereaddata/files/Digital%20Personal%20Data%20Protection%20Act%2C%202023.pdf
**Last reviewed**: 2026-06-25
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not Indian legal counsel and does not provide legal advice on the DPDP Act 2023. The Act distinguishes "Data Fiduciaries" (controllers), "Data Processors," "Significant Data Fiduciaries" (SDFs), "Data Principals" (data subjects), and "Consent Managers." Statutory compliance is the customer-organization responsibility. HUMMBL maps technical primitives to the Act's consent, notice, security, breach-notification, data-principal-rights, and SDF obligations. Rules notified under the Act (DPDP Rules 2025) specify operational details; this matrix references the Act as enacted.

## Scope summary

The Act applies to processing of digital personal data within India, and to processing outside India that is undertaken in connection with offering goods or services to Data Principals in India. It establishes a binary consent / legitimate-use framework (no GDPR-style legitimate-interests balancing), imposes fiduciary duties on Data Fiduciaries, designates Significant Data Fiduciaries with additional obligations (DPO, independent audit, DPIA), provides special protections for children's data (under 18), adopts a negative-list approach to cross-border transfers, and establishes the Data Protection Board of India (DPB) as the adjudicatory authority. Monetary penalties range up to ₹250 crore (approx. USD 30M) per breach category.

## Obligations + coverage

### Consent and notice obligations (S.4–7)

| Obligation | Coverage | Evidence |
|---|---|---|
| Process personal data only for a lawful purpose under consent (S.6) or certain legitimate uses (S.7) | ✅ Lawful-basis tuple records consent vs. legitimate-use ground per processing activity (cross-ref GDPR Art. 6) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Provide notice to Data Principal before or with consent request — personal data, purpose, rights, complaint mechanism (S.5) | ✅ Notice-disclosure tuple captures data elements, purpose, rights summary, and complaint-path (cross-ref GDPR Art. 13) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Consent must be free, specific, informed, unconditional, unambiguous, with clear affirmative action (S.6(1)) | ✅ Consent-record tuple validates specificity + affirmative-action flag; schema validator enforces required fields | `hummbl_governance/audit_log.py`, `hummbl_governance/schema_validator.py` |
| Data Principal may withdraw consent at any time with ease comparable to giving it (S.6(4)) | ✅ Consent-withdrawal tuple links to original consent record; lifecycle primitive triggers downstream cessation | `hummbl_governance/audit_log.py`, `hummbl_governance/lifecycle.py` |
| Consent Manager — registered, interoperable platform for consent lifecycle; accountable to Data Principal (S.6(7)–(9)) | 🟡 Partial: identity registry models Consent Manager as a bus identity; registration with Board is org task | `hummbl_governance/identity.py`, `hummbl_governance/audit_log.py` |

### General obligations of Data Fiduciary (S.8)

| Obligation | Coverage | Evidence |
|---|---|---|
| Data Fiduciary is responsible for compliance regardless of agreement or Data Principal's own duties (S.8(1)) | ✅ Fiduciary-identity tuple binds accountability to the processing chain; audit log attributes every action | `hummbl_governance/identity.py`, `hummbl_governance/audit_log.py` |
| Engage Data Processor only under a valid contract for goods/services to Data Principals (S.8(2)) | ✅ Processor-delegation token + contract-net agreement tuple encode processing scope and sub-processor constraints | `hummbl_governance/delegation.py`, `hummbl_governance/contract_net.py` |
| Ensure completeness, accuracy, and consistency of personal data used for decisions or disclosures (S.8(3)) | ✅ Schema validator enforces data-quality constraints; audit log tracks correction events | `hummbl_governance/schema_validator.py`, `hummbl_governance/audit_log.py` |
| Implement appropriate technical and organisational measures for effective observance (S.8(4)) | ✅ Capability fence restricts processing scope; output validator gates disclosures; coordination bus enforces policy | `hummbl_governance/capability_fence.py`, `hummbl_governance/output_validator.py`, `hummbl_governance/coordination_bus.py` |
| Take reasonable security safeguards to prevent personal data breach (S.8(5)) | ✅ Kill-switch + circuit-breaker + capability fence provide layered breach-prevention controls | `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py`, `hummbl_governance/capability_fence.py` |
| Notify the Board and each affected Data Principal of a personal data breach (S.8(6)) | 🟡 Partial: breach-event tuple + compliance-report generator produce the notification; submission to Board and principals is org task | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Erase personal data upon consent withdrawal or when purpose is no longer served; cause Processor to erase (S.8(7)) | ✅ Lifecycle primitive enforces retention-expiry + erasure-trigger; delegation cascade propagates erasure to Processors | `hummbl_governance/lifecycle.py`, `hummbl_governance/delegation.py` |

### Children's data and Significant Data Fiduciary (S.9–10)

| Obligation | Coverage | Evidence |
|---|---|---|
| Obtain verifiable parental / lawful-guardian consent before processing a child's data (S.9(1)) | ✅ Guardian-identity tuple + verifiable-consent delegation token encode parental verification chain | `hummbl_governance/identity.py`, `hummbl_governance/delegation.py` |
| No processing likely to cause detrimental effect on well-being of a child (S.9(2)) | 🟡 Partial: impact-assessment template flags child-data risk; well-being determination requires human judgment | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| No tracking, behavioural monitoring, or targeted advertising directed at children (S.9(3)) | ✅ Capability fence blocks tracking/monitoring capabilities; output validator rejects targeted-ad outputs for child-segment | `hummbl_governance/capability_fence.py`, `hummbl_governance/output_validator.py` |
| SDF: appoint a Data Protection Officer based in India, responsible to governing body (S.10(2)(a)) | ⚪ Boundary: personnel appointment and India-residency requirement are organizational, not software-addressable | |
| SDF: appoint an independent data auditor to evaluate compliance (S.10(2)(b)) | 🟡 Partial: audit-log export + compliance-evidence pack support auditor review; auditor engagement is org task | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| SDF: conduct periodic Data Protection Impact Assessment (S.10(2)(c)(i)) | ✅ DPIA template with risk-to-rights assessment + mitigation tracking (cross-ref GDPR Art. 35, EU AI Act Art. 27) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| SDF: conduct periodic audit and other prescribed measures (S.10(2)(c)(ii)–(iii)) | 🟡 Partial: audit-log retention + compliance-report generator support periodic audit; audit execution is org task | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |

### Data Principal rights and duties (S.11–15)

| Obligation | Coverage | Evidence |
|---|---|---|
| Right to access — summary of personal data, processing activities, and identities of shared Fiduciaries/Processors (S.11) | ✅ Data-access report generator queries audit log for processing history + third-party sharing records | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Right to correction, completion, updating, and erasure of personal data (S.12) | ✅ Correction tuple + erasure-trigger via lifecycle primitive; audit log records every modification with provenance | `hummbl_governance/lifecycle.py`, `hummbl_governance/audit_log.py` |
| Right to grievance redressal — readily available means from Fiduciary or Consent Manager (S.13) | 🟡 Partial: grievance-tracking tuple + audit log record complaints; redressal mechanism and timelines are org task | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Right to nominate another individual to exercise rights in case of death/incapacity (S.14) | ⚪ Boundary: legal nomination is a personal-legal determination, not software-addressable | |
| Duties of Data Principal — comply with laws, no impersonation, no false complaints (S.15) | ⚪ Boundary: data-principal conduct obligations are legal, not Fiduciary-software-addressable | |

### Cross-border transfer and exemptions (S.16–17)

| Obligation | Coverage | Evidence |
|---|---|---|
| Government may restrict transfer of personal data to notified countries; negative-list model (S.16(1)) | 🟡 Partial: transfer-restriction tuple tracks destination jurisdiction against notified blacklist; government-notification monitoring is org task | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Higher-protection laws for cross-border transfer remain applicable (S.16(2)) | ⚪ Boundary: legal determination of conflicting higher-protection statutes is organizational | |
| Exemptions for enforcement of legal rights, research, mergers, and government processing (S.17) | ⚪ Boundary: exemption applicability is a legal determination by the customer organization | |

### Data Protection Board, enforcement, and penalties (S.18, 27–28, 33, Schedule)

| Obligation | Coverage | Evidence |
|---|---|---|
| Establishment of the Data Protection Board of India as adjudicatory authority (S.18) | ⚪ Boundary: government-body establishment is statutory, not software-addressable | |
| Board directs remedial measures, inquires into breaches, and imposes penalties (S.27) | ⚪ Boundary: regulatory inquiry and penalty imposition are government authority actions | |
| Board functions as a digital office — complaints, hearings, and decisions by digital means (S.28) | ⚪ Boundary: government digital-infrastructure design is organizational | |
| Penalty determination considers nature, gravity, duration, mitigation, and proportionality (S.33(2)) | ✅ Penalty-factor evidence pack aggregates breach severity, mitigation actions, and recurrence from audit log | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Penalties — security-safeguard breach up to ₹250 crore; breach-notification failure up to ₹200 crore; children's obligations up to ₹200 crore; SDF obligations up to ₹150 crore; other provisions up to ₹50 crore (Schedule) | ⚪ Boundary: monetary-penalty exposure is legal, not software-addressable | |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| Consent and notice (S.4–7) | 5 | 4 | 1 | 0 |
| General obligations of Data Fiduciary (S.8) | 7 | 6 | 1 | 0 |
| Children's data and SDF (S.9–10) | 7 | 3 | 3 | 1 |
| Data Principal rights and duties (S.11–15) | 5 | 2 | 1 | 2 |
| Cross-border transfer and exemptions (S.16–17) | 3 | 0 | 1 | 2 |
| Data Protection Board, enforcement, and penalties (S.18, 27–28, 33, Schedule) | 5 | 1 | 0 | 4 |
| **Totals** | **32** | **16** | **7** | **9** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Consent and lawful-basis obligations overlap GDPR Art. 6–7 — see [`gdpr.md`](./gdpr.md)
- Breach notification overlaps GDPR Art. 33–34 — see [`gdpr.md`](./gdpr.md)
- DPIA / impact assessment overlaps GDPR Art. 35, EU AI Act Art. 27 — see [`gdpr.md`](./gdpr.md), [`eu-ai-act.md`](./eu-ai-act.md)
- Children's data protections overlap GDPR Art. 8 — see [`gdpr.md`](./gdpr.md)
- Security safeguards overlap ISO 27001 Annex A — see [`iso-27001.md`](./iso-27001.md)
- Data Principal rights overlap GDPR Art. 15–17 (access, rectification, erasure) — see [`gdpr.md`](./gdpr.md)
