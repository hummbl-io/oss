# San Francisco AI Inventory Ordinance Coverage Matrix — HUMMBL

**Standard**: San Francisco Administrative Code Chapter 22J — Artificial Intelligence Tools (Ordinance No. 288-24)
**Effective**: January 19, 2025
**Source**: https://sfgov.legistar.com/LegislationDetail.aspx?GUID=2E76BC16-98F5-4136-8A3B-7EA81D8968F4&ID=6898479
**Last reviewed**: 2026-06-25
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not San Francisco legal counsel and does not provide legal advice on Chapter 22J. The ordinance applies to City and County of San Francisco departments and their Chief Information Officer (CIO); it is a municipal-government transparency and inventory regime, not a private-sector product regulation. Statutory compliance is the customer-organization responsibility. HUMMBL maps technical primitives to the ordinance's inventory-compilation, public-disclosure, bias-review, incident-monitoring, and enforcement-support obligations.

## Scope summary

Chapter 22J requires every City department head to disclose AI technologies the department has procured, borrowed, or received as a gift to the CIO, who publishes a public Inventory on the DataSF platform. Each disclosure must include 22 data elements spanning identity, purpose, training data, optimization, bias testing, human oversight, incident monitoring, data reuse, affected communities, rights impacts, accessibility, workforce impacts, and identified risks. The CIO must complete the Inventory within one year, submit a biennial AI Technology Report to the Board of Supervisors, and the Controller conducts an annual compliance review. Enforcement is via public complaint, 30-day cure, quarterly Board reporting, and committee hearings; Sec. 22J.5 disclaims any private right of action.

## Obligations + coverage

### Inventory compilation and publication (Sec. 22J.3(a))

| Obligation | Coverage | Evidence |
|---|---|---|
| Collect required disclosure data (22J.3(b)(1)–(22)) from departments using AI technology within six months of effective date | 🟡 Partial: compliance-mapper produces inventory-record schema; cross-department collection act is org task | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/coordination_bus.py` |
| Begin publishing Inventory responses on the DataSF platform within six months | 🟡 Partial: report generator produces publishable content; DataSF publication is org task | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Complete Inventory within one year, including technologies being purchased, borrowed, or received as gift prior to acquisition/deployment | 🟡 Partial: admission-control + lifecycle track pre-acquisition state; completion act is org task | `hummbl_governance/kernel/admission_control.py`, `hummbl_governance/lifecycle.py` |
| Remove technologies never obtained or no longer used from the Inventory | ✅ Lifecycle state transitions (retired/decommissioned) drive inventory removal | `hummbl_governance/lifecycle.py`, `hummbl_governance/audit_log.py` |

### Department disclosure obligations (Sec. 22J.3(b)(1)–(22))

| Obligation | Coverage | Evidence |
|---|---|---|
| Disclose technology name, vendor, purpose, function, intended use, and context/domain (items 1–4) | ✅ Inventory-record tuple type + schema-validated disclosure fields | `hummbl_governance/schema_validator.py`, `hummbl_governance/audit_log.py` |
| Disclose training data, how the technology works, and output data (items 5–7) | ✅ System-description tuple + provenance metadata + output-validation gate | `hummbl_governance/audit_log.py`, `hummbl_governance/output_validator.py` |
| Disclose optimization goals, accuracy, optimal performance conditions, and degrading conditions (items 8–10) | ✅ Capability-description tuple + health-probe performance metadata | `hummbl_governance/schema_validator.py`, `hummbl_governance/health_probe.py` |
| Disclose whether bias testing has been performed (race, gender, etc.) and the results (item 11) | ✅ Impact-assessment template + bias-test tuple with results field | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Disclose how and where people report bias, inaccuracies, or poor performance (item 12) | 🟡 Partial: report-channel tuple records mechanism; public-facing channel setup is org task | `hummbl_governance/audit_log.py`, `hummbl_governance/identity.py` |
| Disclose testing conditions/circumstances and adverse incident monitoring and communication procedures (items 13–14) | ✅ Test-condition tuple + adverse-event tuple + incident-monitoring substrate | `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py` |
| Disclose level of human oversight and whether data can be used for training proprietary/third-party systems (items 15–16) | ✅ Human-oversight delegation token + data-use provenance labeling | `hummbl_governance/delegation.py`, `hummbl_governance/output_validator.py` |
| Disclose intended users, affected communities, rights/opportunity/access impacts, accessibility, workforce impacts, use justification, and identified risks and mitigations (items 17–22) | ✅ Stakeholder-impact + rights-impact + workforce-impact + use-justification + risk-treatment tuples | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |

### AI Technology Report and review (Sec. 22J.3(g), Controller review)

| Obligation | Coverage | Evidence |
|---|---|---|
| Submit AI Technology Report to Board of Supervisors within 12 months and every two years thereafter | 🟡 Partial: compliance-report generator produces the report; Board submission is org task | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Make AI Technology Report available on the DataSF platform | 🟡 Partial: report generator produces publishable content; DataSF publication is org task | `hummbl_governance/compliance_mapper.py` |
| Controller conducts annual review of department compliance with Sec. 22J.3 | 🟡 Partial: audit-log export + compliance evidence supports review; Controller review act is org task | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |

### Enforcement (Sec. 22J.4)

| Obligation | Coverage | Evidence |
|---|---|---|
| Accept written notice of alleged inventory violations from the public; CIO forwards to Department with 30-day cure period | 🟡 Partial: violation-tracking tuple + schedule-engine deadline tracking; public-complaint intake and cure act are org tasks | `hummbl_governance/audit_log.py`, `hummbl_governance/kernel/schedule_engine.py` |
| CIO quarterly reports valid uncured violations to Board of Supervisors | 🟡 Partial: compliance-report generator produces quarterly report; Board reporting is org task | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Board calendars hearing within 60 days; Department Head reports compliance plan at Government Audit and Oversight Committee | ⚪ Boundary: legislative calendaring and hearing testimony are organizational, not software-addressable | |

### General welfare and liability (Sec. 22J.5)

| Obligation | Coverage | Evidence |
|---|---|---|
| Ordinance promotes general welfare only; no private right of action or municipal liability for breach | ⚪ Boundary: liability-scope disclaimer is a legal determination, not software-addressable | |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| Inventory compilation and publication (Sec. 22J.3(a)) | 4 | 1 | 3 | 0 |
| Department disclosure obligations (Sec. 22J.3(b)) | 8 | 7 | 1 | 0 |
| AI Technology Report and review (Sec. 22J.3(g), Controller) | 3 | 0 | 3 | 0 |
| Enforcement (Sec. 22J.4) | 3 | 0 | 2 | 1 |
| General welfare and liability (Sec. 22J.5) | 1 | 0 | 0 | 1 |
| **Totals** | **19** | **8** | **9** | **2** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Bias testing and impact assessment overlap EU AI Act Art. 27 (FRIA) — see [`eu-ai-act.md`](./eu-ai-act.md)
- Human oversight overlaps EU AI Act Art. 14 and South Korea AI Basic Act Art. 34 — see [`eu-ai-act.md`](./eu-ai-act.md), [`south-korea-ai-basic-act.md`](./south-korea-ai-basic-act.md)
- Adverse incident monitoring overlaps NIST AI RMF MEASURE — see [`nist-ai-rmf.md`](./nist-ai-rmf.md)
- Risk identification and treatment overlap NIST AI RMF MAP and South Korea Art. 32 — see [`nist-ai-rmf.md`](./nist-ai-rmf.md), [`south-korea-ai-basic-act.md`](./south-korea-ai-basic-act.md)
