# Taiwan AI Fundamental Act Coverage Matrix — HUMMBL

**Standard**: Artificial Intelligence Basic Act (人工智慧基本法), inventory ID 27
**Effective**: January 14, 2026 (promulgated; Art. 20 — takes effect on promulgation date; passed by Legislative Yuan December 23, 2025)
**Source**: https://law.nstc.gov.tw/EngLawContent.aspx?id=10099&lan=E
**Last reviewed**: 2026-06-25
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not Taiwanese legal counsel and does not provide legal advice on the AI Fundamental Act. The Act is a framework/basic law that primarily obligates the government (Executive Yuan, NSTC, MODA, industry competent authorities) to promote AI development, establish risk classification frameworks, and conduct risk assessments for government AI use. It establishes seven governing principles (Art. 4) and a risk-based management approach (Arts. 16–17) but delegates most operational obligations to future sector-specific regulations. Statutory compliance is the customer-organization responsibility. HUMMBL maps technical primitives to the Act's transparency, safety, risk-management, human-oversight, and accountability principles.

## Scope summary

The Act applies to government promotion, R&D, and application of AI in Taiwan. The central competent authority is the National Science and Technology Council (NSTC), with the Ministry of Digital Affairs (MODA) responsible for the AI risk taxonomy and assessment framework. The Act establishes seven principles (Art. 4): sustainable development and well-being, human autonomy, privacy protection and data governance, cybersecurity and safety, transparency and explainability, fairness and non-discrimination, and accountability. High-risk AI applications (identified by industry competent authorities in consultation with MODA) carry advisory-notice obligations (Art. 5) and liability/relief requirements (Art. 17). Government agencies using AI must conduct risk assessments and establish internal control mechanisms (Art. 19). Sector-specific risk-based management regulations are to be promulgated within two years of the effective date (Art. 18).

## Obligations + coverage

### Core principles (Art. 4)

| Obligation | Coverage | Evidence |
|---|---|---|
| Sustainable development and well-being — balance social equity, environmental sustainability, reduce digital gaps | ⚪ Boundary: social-policy and education obligations are governmental, not software-addressable | |
| Human autonomy — support human autonomy, respect personality rights and fundamental rights, ensure human oversight | ✅ Human-oversight delegation token + identity registration (cross-ref EU AI Act Art. 14, South Korea Art. 34) | `hummbl_governance/delegation.py`, `hummbl_governance/identity.py` |
| Privacy protection and data governance — protect personal data, respect trade secrets, data minimization, promote open reuse of non-sensitive data | ✅ Data-validation gate + access-control fence + identity-bound data handling | `hummbl_governance/schema_validator.py`, `hummbl_governance/capability_fence.py`, `hummbl_governance/identity.py` |
| Cybersecurity and safety — establish cybersecurity measures, prevent threats, ensure robustness and safety | ✅ Kill-switch 4-mode halt + circuit-breaker fast-fail + capability-fence sandbox | `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py`, `hummbl_governance/capability_fence.py` |
| Transparency and explainability — AI outputs accompanied by appropriate disclosures or labeling to facilitate risk assessment | ✅ Output-validation gate + provenance-labeling + reasoning-trace disclosure (cross-ref EU AI Act Art. 50, South Korea Art. 31) | `hummbl_governance/output_validator.py`, `hummbl_governance/audit_log.py`, `hummbl_governance/reasoning.py` |
| Fairness and non-discrimination — minimize algorithmic bias and discrimination risks, results should not discriminate against specific groups | 🟡 Partial: output-validator gates + reward-monitor detect anomalous outputs; full bias/fairness auditing is org task | `hummbl_governance/output_validator.py`, `hummbl_governance/reward_monitor.py` |
| Accountability — ensure internal governance responsibilities and external social responsibilities are assumed | ✅ Immutable audit-log + delegation-token accountability + receipt-engine provenance | `hummbl_governance/audit_log.py`, `hummbl_governance/delegation.py`, `hummbl_governance/kernel/receipt_engine.py` |

### Risk prevention and high-risk AI (Arts. 5, 16, 17)

| Obligation | Coverage | Evidence |
|---|---|---|
| Prevent AI from infringing upon people's life, body, liberty, or property (Art. 5 ¶1) | ✅ Kill-switch halt + circuit-breaker fast-fail on safety-violation tuples (cross-ref South Korea Art. 32) | `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py` |
| Prevent AI from disrupting social order, national security, or ecological environment (Art. 5 ¶1) | 🟡 Partial: safety primitives provide halt capability; determining social-order/national-security impact is org task | `hummbl_governance/kill_switch.py`, `hummbl_governance/capability_fence.py` |
| Prevent bias, discrimination, false advertising, dissemination of misleading or false information (Art. 5 ¶1) | 🟡 Partial: output-validator gates flag prohibited content; full misinformation prevention is org task | `hummbl_governance/output_validator.py`, `hummbl_governance/audit_log.py` |
| High-risk AI products must carry advisory notices or warnings (Art. 5 ¶2) | ✅ Output-labeling primitive + risk-classification tuple (cross-ref South Korea Art. 31, EU AI Act Art. 50) | `hummbl_governance/output_validator.py`, `hummbl_governance/compliance_mapper.py` |
| MODA to promote internationally interoperable AI risk taxonomy and assessment framework (Art. 16 ¶1) | ✅ Risk-classification mapping + STRIDE threat-modeling + compliance crosswalk (cross-ref NIST AI RMF, EU AI Act risk tiers) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/stride_mapper.py` |
| Competent authorities to establish risk-based management regulations; restrict or prohibit Article 5 circumstances (Art. 16 ¶2) | 🟡 Partial: kill-switch prohibit-mode + capability-fence enforce restrictions; regulatory drafting is org task | `hummbl_governance/kill_switch.py`, `hummbl_governance/capability_fence.py` |
| High-risk AI liability attribution, relief/compensation/insurance mechanisms; R&D exemption before application (Art. 17) | ⚪ Boundary: legal liability, insurance, and R&D-scope determination are organizational/legal, not software-addressable | |

### Transparency and explainability (Art. 4(5))

| Obligation | Coverage | Evidence |
|---|---|---|
| AI outputs shall be accompanied by appropriate disclosures or labeling | ✅ Provenance-labeling tuple type + output-validation gate (cross-ref EU AI Act Art. 50, South Korea Art. 31) | `hummbl_governance/output_validator.py`, `hummbl_governance/audit_log.py` |
| Disclosures shall facilitate assessment of potential risks and understanding of impact on rights and interests | ✅ Reasoning-trace disclosure + compliance-report generator + evidence-engine provenance | `hummbl_governance/reasoning.py`, `hummbl_governance/compliance_mapper.py`, `hummbl_governance/kernel/evidence_engine.py` |

### Cybersecurity and safety (Art. 4(4))

| Obligation | Coverage | Evidence |
|---|---|---|
| Establish cybersecurity measures to prevent security threats and attacks | ✅ Capability-fence sandbox + admission-control gate + authority-engine access control | `hummbl_governance/capability_fence.py`, `hummbl_governance/kernel/admission_control.py`, `hummbl_governance/kernel/authority_engine.py` |
| Ensure robustness and safety of the system | ✅ Health-probe liveness + circuit-breaker fast-fail + failure-mode taxonomy | `hummbl_governance/health_probe.py`, `hummbl_governance/circuit_breaker.py`, `hummbl_governance/failure_modes.py` |

### Privacy and data governance (Arts. 4(3), 13, 14)

| Obligation | Coverage | Evidence |
|---|---|---|
| Protect personal data privacy; respect corporate trade secrets; avoid data leakage (Art. 4(3)) | ✅ Identity-bound data handling + capability-fence access control + authority-engine authorization | `hummbl_governance/identity.py`, `hummbl_governance/capability_fence.py`, `hummbl_governance/kernel/authority_engine.py` |
| Adopt data minimization principle (Art. 4(3)) | ✅ Schema-validator input validation + cost-governor resource-budget enforcement | `hummbl_governance/schema_validator.py`, `hummbl_governance/cost_governor.py` |
| Establish open data, sharing, and reuse mechanisms; ensure data reflects national cultural values; protect IP (Art. 13) | ⚪ Boundary: data policy, cultural-value curation, and IP licensing are organizational, not software-addressable | |
| Avoid unnecessary personal data collection/processing; privacy by design and by default (Art. 14) | ✅ Default-deny capability-fence + schema-validator data-minimization gate + authority-engine least-privilege | `hummbl_governance/capability_fence.py`, `hummbl_governance/schema_validator.py`, `hummbl_governance/kernel/authority_engine.py` |

### Government AI use and human oversight (Arts. 4(2), 19)

| Obligation | Coverage | Evidence |
|---|---|---|
| Support human autonomy; ensure human oversight of AI systems (Art. 4(2)) | ✅ Human-oversight delegation token + kill-switch human-override mode + lifecycle human-in-the-loop gate | `hummbl_governance/delegation.py`, `hummbl_governance/kill_switch.py`, `hummbl_governance/lifecycle.py` |
| Government shall conduct risk assessments when using AI to perform duties or services (Art. 19 ¶1) | ✅ Risk-assessment template + STRIDE threat modeling + compliance-mapper risk classification | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/stride_mapper.py`, `hummbl_governance/audit_log.py` |
| Government shall plan risk response measures (Art. 19 ¶1) | ✅ Risk-treatment tuples + coordination-bus response orchestration + audit-log mitigation tracking | `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py` |
| Government shall establish usage guidelines or internal control management mechanisms (Art. 19 ¶2) | ✅ Doctrine-engine policy encoding + law-engine rule enforcement + schedule-engine control scheduling | `hummbl_governance/kernel/doctrine_engine.py`, `hummbl_governance/kernel/law_engine.py`, `hummbl_governance/kernel/schedule_engine.py` |

### Institutional, accountability, and regulatory obligations (Arts. 4(7), 6, 18)

| Obligation | Coverage | Evidence |
|---|---|---|
| Ensure internal governance responsibilities and external social responsibilities are assumed (Art. 4(7)) | ✅ Delegation-token responsibility assignment + audit-log accountability trail + authority-engine role enforcement | `hummbl_governance/delegation.py`, `hummbl_governance/audit_log.py`, `hummbl_governance/kernel/authority_engine.py` |
| Establish National AI Strategic Committee convened by Premier; coordinate national AI affairs (Art. 6) | ⚪ Boundary: government-committee establishment is organizational, not software-addressable | |
| Committee convenes at least annually; special meetings for sudden emergencies or major incidents (Art. 6) | ⚪ Boundary: committee operations and meeting scheduling are organizational | |
| Government shall review and adjust regulations within two years of effective date (Art. 18) | ⚪ Boundary: legislative review and regulatory drafting are organizational | |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| Core principles (Art. 4) | 7 | 5 | 1 | 1 |
| Risk prevention and high-risk AI (Arts. 5, 16, 17) | 7 | 3 | 2 | 2 |
| Transparency and explainability (Art. 4(5)) | 2 | 2 | 0 | 0 |
| Cybersecurity and safety (Art. 4(4)) | 2 | 2 | 0 | 0 |
| Privacy and data governance (Arts. 4(3), 13, 14) | 4 | 3 | 0 | 1 |
| Government AI use and human oversight (Arts. 4(2), 19) | 4 | 4 | 0 | 0 |
| Institutional, accountability, and regulatory (Arts. 4(7), 6, 18) | 4 | 1 | 0 | 3 |
| **Totals** | **30** | **20** | **3** | **7** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Transparency overlaps EU AI Act Art. 50 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Transparency overlaps South Korea AI Basic Act Art. 31 — see [`south-korea-ai-basic-act.md`](./south-korea-ai-basic-act.md)
- Risk management overlaps NIST AI RMF MEASURE — see [`nist-ai-rmf.md`](./nist-ai-rmf.md)
- Human oversight overlaps EU AI Act Art. 14 — see [`eu-ai-act.md`](./eu-ai-act.md)
- High-risk AI obligations overlap South Korea AI Basic Act Art. 34 — see [`south-korea-ai-basic-act.md`](./south-korea-ai-basic-act.md)
- Risk classification overlaps EU AI Act risk tiers — see [`eu-ai-act.md`](./eu-ai-act.md)
