# Canada AIDA (Bill C-27) Coverage Matrix — HUMMBL

**Standard**: Artificial Intelligence and Data Act, Part 3 of the Digital Charter Implementation Act, 2022 (Bill C-27)
**Effective**: Pending (not in force; Bill C-27 died on Order Paper, Jan 2025 prorogation; not reintroduced)
**Source**: https://ised-isde.canada.ca/site/ised/en/legislation/initiatives/digital-charter-implementation-act-2023
**Last reviewed**: 2026-06-25
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not Canadian legal counsel and does not provide legal advice on AIDA. The Act distinguishes "regulated activities" (designing, developing, making available, or managing AI systems in international/interprovincial trade), "high-impact systems" (criteria to be defined in regulation), and "persons responsible" for such systems. Statutory compliance is the customer-organization responsibility. HUMMBL maps technical primitives to the Act's risk-assessment, mitigation, record-keeping, transparency, human-oversight, and incident-response obligations. Proposed November 2023 amendments (general-purpose systems, AI identity disclosure, accountability framework, incident response) are included where text was published.

## Scope summary

AIDA applies to persons carrying out regulated activities in the course of international and interprovincial trade and commerce in Canada. It does not apply to government institutions under the Privacy Act or products/services under the direction of National Defence, CSIS, CSE, or prescribed regulators. High-impact systems are defined by regulation (criteria not yet finalized); the companion document identifies sectors including healthcare, finance, employment, public services, and criminal justice. Obligations are tiered: anonymized-data measures (s. 6) apply to all regulated persons; assessment (s. 7) applies to all persons responsible for an AI system; risk mitigation, monitoring, publication, and notification (ss. 8–12) apply only to high-impact systems. Part 2 creates general offences for use of illegally obtained personal information and for making systems available that cause serious harm. Penalties reach the greater of $10M CAD and 3% of gross global revenues.

## Obligations + coverage

### Data governance — anonymized data (s. 6)

| Obligation | Coverage | Evidence |
|---|---|---|
| Establish measures with respect to the manner in which data is anonymized | ✅ Data-schema validation + anonymization-measures record (cross-ref GDPR Art. 25 data-protection-by-design) | `hummbl_governance/schema_validator.py`, `hummbl_governance/audit_log.py` |
| Establish measures with respect to the use or management of anonymized data | ✅ Anonymized-data governance record + compliance-mapping substrate | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |

### High-impact system assessment and risk management (ss. 7–9, amended)

| Obligation | Coverage | Evidence |
|---|---|---|
| Assess whether an AI system is a high-impact system (s. 7) | ✅ Impact-assessment template + classification tuple (cross-ref EU AI Act Art. 6 classification, South Korea Art. 34) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Establish measures to identify, assess and mitigate risks of harm or biased output (s. 8) | ✅ Risk-identification + assessment + treatment tuple types + biased-output detection gate (cross-ref NIST AI RMF, EU AI Act Art. 9) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/output_validator.py`, `hummbl_governance/audit_log.py` |
| Establish measures to monitor compliance with mitigation measures and their effectiveness (s. 9) | ✅ Health-probe continuous monitoring + coordination-bus event propagation | `hummbl_governance/health_probe.py`, `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py` |
| Conduct impact assessment for high-impact systems (amended — s. 10(1)(a)) | ✅ Impact-assessment template with human-rights + adverse-impact components (cross-ref EU AI Act Art. 27 FRIA, South Korea Art. 35) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Ensure reliability and robustness of the system (amended — s. 10(1)(f)) | ✅ Circuit-breaker fast-fail + convergence-guard stability check + health-probe resilience monitoring | `hummbl_governance/circuit_breaker.py`, `hummbl_governance/convergence_guard.py`, `hummbl_governance/health_probe.py` |

### Transparency and publication (ss. 11, 18, amended)

| Obligation | Coverage | Evidence |
|---|---|---|
| Publish plain-language description when making high-impact system available for use — intended use, content types, mitigation measures (s. 11(1)) | 🟡 Partial: compliance-report generator produces the plain-language description; website publication is org task | `hummbl_governance/compliance_mapper.py` |
| Publish plain-language description when managing operation of high-impact system — actual use, content types, mitigation measures (s. 11(2)) | 🟡 Partial: compliance-report generator produces the plain-language description; website publication is org task | `hummbl_governance/compliance_mapper.py` |
| Publish information on publicly available website as ordered by Minister (s. 18) | 🟡 Partial: compliance-report generator produces publishable content; website publication is org task | `hummbl_governance/compliance_mapper.py` |
| Promptly advise human user that they are communicating with an AI system where confusion is reasonably foreseeable (amended — all AI systems) | ✅ AI-identity disclosure label + output-validation gate (cross-ref EU AI Act Art. 50, South Korea Art. 31, Colorado § 6-1-1704) | `hummbl_governance/output_validator.py`, `hummbl_governance/audit_log.py` |

### Record-keeping and incident notification (ss. 10, 12, amended)

| Obligation | Coverage | Evidence |
|---|---|---|
| Keep general records describing measures established under ss. 6, 8, 9 and reasons supporting high-impact assessment (s. 10(1)) | ✅ Immutable audit-log retention + structured measures-and-assessment tuples | `hummbl_governance/audit_log.py` |
| Keep additional records in respect of requirements under ss. 6 to 9 as prescribed (s. 10(2)) | ✅ Receipt-engine structured records + audit-log extended retention | `hummbl_governance/audit_log.py`, `hummbl_governance/kernel/receipt_engine.py` |
| Notify Minister as soon as feasible if use of system results or is likely to result in material harm (s. 12) | 🟡 Partial: audit-log captures harm event with timestamp + severity; Minister notification is org task | `hummbl_governance/audit_log.py` |
| Establish incident response and reporting; assess serious harm and near-misses; cease operations until modified; report to AI and Data Commissioner (amended — s. 11(1)(g)) | ✅ Kill-switch 4-mode halt + circuit-breaker fast-fail + incident-report tuple (cross-ref EU AI Act Art. 73 serious-incident reporting) | `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py`, `hummbl_governance/audit_log.py` |

### Human oversight and accountability (amended)

| Obligation | Coverage | Evidence |
|---|---|---|
| Enable human oversight features in high-impact systems — interpretability appropriate to context (amended — ss. 10(1)(d), 11(1)(d)) | ✅ Human-oversight delegation token + reasoning-interpretability trace (cross-ref EU AI Act Art. 14, South Korea Art. 34) | `hummbl_governance/delegation.py`, `hummbl_governance/reasoning.py` |
| Establish accountability framework — roles, reporting structure, risk policies, incident procedures, data policies, training (amended) | ✅ Identity-registry roles + delegation tokens + audit-log policy-procedure records | `hummbl_governance/identity.py`, `hummbl_governance/delegation.py`, `hummbl_governance/audit_log.py` |
| Create means by which users can provide feedback on system performance (amended — s. 11(1)(e)) | 🟡 Partial: coordination-bus provides feedback-channel primitive; user-facing feedback UI is org task | `hummbl_governance/coordination_bus.py` |

### Ministerial oversight and enforcement (ss. 13–20)

| Obligation | Coverage | Evidence |
|---|---|---|
| Comply with Ministerial order to provide records (ss. 13–14) | 🟡 Partial: audit-log provides exportable structured records; compliance act is org task | `hummbl_governance/audit_log.py` |
| Comply with Ministerial audit order — conduct or engage independent auditor (s. 15) | ⚪ Boundary: external audit conduct and auditor engagement is organizational | |
| Implement measures specified by Minister to address audit-report findings (s. 16) | ⚪ Boundary: regulatory-order compliance is organizational | |
| Cease use or making available of system on Ministerial cessation order — serious risk of imminent harm (s. 17) | 🟡 Partial: kill-switch implements technical halt; order compliance is org task | `hummbl_governance/kill_switch.py` |
| Comply with Ministerial orders; Federal Court enforcement of filed orders (ss. 19–20) | ⚪ Boundary: legal-order compliance and court enforcement is organizational | |

### Confidentiality, information disclosure, offences, and penalties (ss. 22–30, Part 2 ss. 35–37)

| Obligation | Coverage | Evidence |
|---|---|---|
| Maintain confidentiality of confidential business information obtained under the Act (ss. 22–23) | ⚪ Boundary: information-handling policy and confidentiality controls are organizational | |
| Minister disclosure of information to analysts and other regulators (ss. 25–26) | ⚪ Boundary: inter-agency government disclosure is not software-addressable | |
| Minister publication of contravention or imminent-harm information on publicly available website (ss. 27–28) | ⚪ Boundary: regulatory publication is governmental | |
| Administrative monetary penalties for violations (s. 29) | ⚪ Boundary: penalty exposure is legal, not software-addressable | |
| Offence for contravention of sections 6 to 12 — fine up to greater of $10M and 3% gross global revenues (s. 30(1)) | ⚪ Boundary: criminal liability is legal, not software-addressable | |
| Part 2: Prohibition on possession or use of illegally obtained personal information for AI system design, development, or use (s. 35) | ⚪ Boundary: data-provenance legality is organizational, not software-addressable | |
| Part 2: Prohibition on knowingly or recklessly making system available that causes serious specified harm (s. 36) | ⚪ Boundary: criminal prohibition is legal; technical harm-prevention covered by ss. 8–9 | |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| Data governance — anonymized data (s. 6) | 2 | 2 | 0 | 0 |
| Assessment + risk management (ss. 7–9, amended) | 5 | 5 | 0 | 0 |
| Transparency + publication (ss. 11, 18, amended) | 4 | 1 | 3 | 0 |
| Record-keeping + incident notification (ss. 10, 12, amended) | 4 | 3 | 1 | 0 |
| Human oversight + accountability (amended) | 3 | 2 | 1 | 0 |
| Ministerial oversight + enforcement (ss. 13–20) | 5 | 0 | 2 | 3 |
| Confidentiality, offences, penalties (ss. 22–30, Part 2) | 7 | 0 | 0 | 7 |
| **Totals** | **30** | **13** | **7** | **10** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated. AIDA is pending legislation that died on the Order Paper; obligations reflect Bill C-27 as introduced (June 2022) and November 2023 amendment text published by the Minister of Innovation, Science and Industry.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Risk management overlaps EU AI Act Art. 9 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Impact assessment overlaps EU AI Act Art. 27 (FRIA) — see [`eu-ai-act.md`](./eu-ai-act.md)
- Human oversight overlaps EU AI Act Art. 14 — see [`eu-ai-act.md`](./eu-ai-act.md)
- AI identity disclosure overlaps EU AI Act Art. 50 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Transparency obligations overlap South Korea AI Basic Act Art. 31 — see [`south-korea-ai-basic-act.md`](./south-korea-ai-basic-act.md)
- Incident reporting overlaps EU AI Act Art. 73 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Risk management overlaps NIST AI RMF — see [`nist-ai-rmf.md`](./nist-ai-rmf.md)
