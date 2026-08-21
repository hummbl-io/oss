# Kazakhstan AI Law Coverage Matrix — HUMMBL

**Standard**: Law of the Republic of Kazakhstan "On Artificial Intelligence", No. 230-VIII ЗРК
**Effective**: January 18, 2026 (60 days after first official publication; signed November 17, 2025)
**Source**: https://so-ipr.com/news-events/publications/kazakhstan-enacts-first-ai-law-central-asia (legal text: https://adilet.zan.kz/eng/docs/Z2500000230)
**Last reviewed**: 2026-06-25
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not Kazakh legal counsel and does not provide legal advice on the Law "On Artificial Intelligence." The Law establishes principles of legality, justice, transparency, accountability, data protection, human welfare, and safety. It classifies AI systems by risk (minimal/medium/high) and autonomy (low/medium/high), prohibits seven categories of AI functionality, and introduces copyright rules for AI-generated works and prompts. Statutory compliance is the customer-organization responsibility. HUMMBL maps technical primitives to the Law's transparency, safety, risk-management, data-protection, and human-oversight obligations.

## Scope summary

The Law applies to all subjects of relations in the field of AI in Kazakhstan — owners, holders, users, data-library producers, and the national AI platform operator. It covers the full AI system lifecycle from creation through operation. AI systems are classified by risk level (minimal, medium, high) and autonomy degree (low, medium, high), with high-risk systems subject to additional documentation, audit, and trusted-list requirements. Seven categories of AI functionality are prohibited outright, including manipulative techniques, vulnerability exploitation, social scoring, unlawful biometric classification, and non-consensual emotion detection. The Law also addresses copyright for AI-assisted works and prompts, data-library provenance, and a national AI platform for development and testing.

## Obligations + coverage

### Principles & general obligations (Arts. 4–9)

| Obligation | Coverage | Evidence |
|---|---|---|
| Art. 6: AI systems must ensure fairness and equality, excluding discrimination (origin, gender, race, nationality, language, religion, etc.) | ✅ Output-validation gate with bias/discrimination checks + compliance mapping (cross-ref EU AI Act Art. 10, NIST AI RMF MEASURE) | `hummbl_governance/output_validator.py`, `hummbl_governance/compliance_mapper.py` |
| Art. 7: Provide users complete information about AI system characteristics and limitations; right to be informed about automated processing and right to object | ✅ Transparency-disclosure generator + automated-processing notification tuple (cross-ref EU AI Act Art. 50, Korea AI Basic Act Art. 31) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Art. 8(1): Owner/possessor/user must ensure continuous control over the AI system at all lifecycle stages | ✅ Lifecycle-stage governance + continuous-control enforcement (cross-ref EU AI Act Art. 14) | `hummbl_governance/lifecycle.py`, `hummbl_governance/kill_switch.py` |
| Art. 8(3): AI creation and operation must account for energy efficiency and reducing negative environmental impact | 🟡 Partial: cost-governor tracks resource consumption and enforces budgets; environmental-impact modeling is org task | `hummbl_governance/cost_governor.py` |
| Art. 9: Preserve human autonomy and free will in decision-making when operating AI systems | ✅ Human-oversight delegation token + reasoning-chain audit preserving human decision authority (cross-ref EU AI Act Art. 14) | `hummbl_governance/delegation.py`, `hummbl_governance/reasoning.py` |

### Data protection, privacy & safety (Arts. 10–11)

| Obligation | Coverage | Evidence |
|---|---|---|
| Art. 10(1)–(2): AI use subject to data-protection requirements; no unauthorized collection/storage/dissemination of personal data; prevent unauthorized third-party access; use high-quality representative data sets | ✅ Capability-fence restricting data access + identity-based authorization + schema validation for data-set quality (cross-ref GDPR Art. 5, EU AI Act Art. 10) | `hummbl_governance/capability_fence.py`, `hummbl_governance/identity.py`, `hummbl_governance/schema_validator.py` |
| Art. 11(1): AI systems must meet safety and reliability requirements that exclude unforeseen consequences or abuse | ✅ Kill-switch 4-mode halt + circuit-breaker fast-fail + output-validation gate (cross-ref Korea AI Basic Act Art. 32) | `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py`, `hummbl_governance/output_validator.py` |
| Art. 11(2): Results of AI system activities must comply with the legislation of the Republic of Kazakhstan | ✅ Compliance-mapper with legislative-conformance check + output-validation gate | `hummbl_governance/output_validator.py`, `hummbl_governance/compliance_mapper.py` |

### Risk management & owner/holder obligations (Arts. 11(3), 15, 18)

| Obligation | Coverage | Evidence |
|---|---|---|
| Art. 15(2)(1) + Art. 11(3): Owners/holders must implement risk management of AI systems | ✅ Risk-management program substrate: INTENT + risk-treatment tuples (cross-ref NIST AI RMF, EU AI Act Art. 9, Korea Art. 32) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Art. 18(1): Continuous risk management — identify, assess, mitigate risks; update at least annually | ✅ Risk-identification + assessment + treatment tuple types with annual-review schedule enforcement | `hummbl_governance/audit_log.py`, `hummbl_governance/kernel/schedule_engine.py`, `hummbl_governance/compliance_mapper.py` |
| Art. 18(2): If prohibited capabilities (Art. 17(3)) are identified, take immediate measures including suspend or terminate operation | ✅ Kill-switch immediate halt + circuit-breaker emergency trip on prohibited-capability detection | `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py` |
| Art. 15(2)(2)–(3): Ensure security and reliability including protection from unauthorized access and failures; maintain documentation based on impact degree | ✅ Capability-fence access control + health-probe failure detection + immutable audit-log documentation retention | `hummbl_governance/capability_fence.py`, `hummbl_governance/health_probe.py`, `hummbl_governance/audit_log.py` |

### User rights & obligations (Art. 16)

| Obligation | Coverage | Evidence |
|---|---|---|
| Art. 16(1)(4): Right to receive explanations about AI results affecting rights, freedoms, and legitimate interests | ✅ Explanation-disclosure generator + reasoning-chain audit for decision provenance (cross-ref EU AI Act Art. 13, Korea Art. 34) | `hummbl_governance/reasoning.py`, `hummbl_governance/compliance_mapper.py` |
| Art. 16(1)(5): Right to request information about the data on which AI decisions were based | ✅ Audit-log data-lineage query + evidence-export tuple | `hummbl_governance/audit_log.py`, `hummbl_governance/kernel/evidence_engine.py` |
| Art. 16(1)(6): Right to refuse interaction with AI systems (unless required by law) | 🟡 Partial: kill-switch supports system-level opt-out/halt; user-level refusal workflow is org policy task | `hummbl_governance/kill_switch.py` |
| Art. 16(2)(1)–(2): Users must use AI only within granted access rights and comply with safety rules | ✅ Identity-based access enforcement + capability-fence scope restriction + safety-rule compliance gate | `hummbl_governance/identity.py`, `hummbl_governance/capability_fence.py` |

### Classification & prohibited practices (Art. 17)

| Obligation | Coverage | Evidence |
|---|---|---|
| Art. 17(1): Classify AI systems by risk level (minimal, medium, high) based on impact on users, society, and state | ✅ Risk-classification tuple + impact-assessment template (cross-ref EU AI Act Art. 6, Korea Art. 34) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Art. 17(2): Classify AI systems by autonomy degree (low, medium, high) based on independence in decision-making | ✅ Autonomy-classification tuple + human-oversight delegation level mapping | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/delegation.py` |
| Art. 17(3)(1)–(2): Prohibited — subconscious/manipulative techniques distorting behavior; exploitation of vulnerabilities (age, disability, social status) | ✅ Output-validation gate rejecting manipulative/harmful outputs + capability-fence blocking vulnerability-targeting (cross-ref EU AI Act Art. 5) | `hummbl_governance/output_validator.py`, `hummbl_governance/capability_fence.py` |
| Art. 17(3)(3): Prohibited — social scoring: assessment/classification of individuals based on social behavior or personal characteristics | ✅ Output-validation gate rejecting social-scoring outputs + capability-fence blocking scoring functionality (cross-ref EU AI Act Art. 5(1)(c)) | `hummbl_governance/output_validator.py` |
| Art. 17(3)(4)–(5): Prohibited — unlawful personal-data collection/processing; biometric classification for discrimination (race, political views, religion) | ✅ Capability-fence data-access restriction + identity authorization + output-validation rejecting discriminatory biometric outputs | `hummbl_governance/capability_fence.py`, `hummbl_governance/identity.py`, `hummbl_governance/output_validator.py` |
| Art. 17(3)(6)–(7): Prohibited — emotion determination without consent; creation/distribution of legally prohibited AI results | ✅ Capability-fence blocking non-consensual emotion detection + output-validation gate for prohibited-content filtering | `hummbl_governance/capability_fence.py`, `hummbl_governance/output_validator.py` |

### Transparency, audit & machine-readable forms (Arts. 19–22)

| Obligation | Coverage | Evidence |
|---|---|---|
| Art. 19(2) + Art. 20(2): Audit of AI systems for trusted-list inclusion — assess data-library quality/legitimacy and presence of prohibited capabilities | ✅ Audit-log evidence export + compliance-mapper audit template + schema validation for data-library quality | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py`, `hummbl_governance/schema_validator.py` |
| Art. 21(1): Users must be informed that goods, works, and services are produced or provided using AI systems | ✅ Transparency-notification primitive + AI-use disclosure tuple (cross-ref EU AI Act Art. 50, Korea Art. 31) | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Art. 21(2)–(3): Synthetic AI results (deepfakes) must be marked in machine-readable form with visual/audio warning; owner/holder responsible | ✅ Content-authenticity tuple + provenance-labeling + output-validation marking gate (cross-ref EU AI Act Art. 50(2), Korea Art. 31) | `hummbl_governance/output_validator.py`, `hummbl_governance/audit_log.py` |
| Art. 22(1)–(2): Machine-readable forms must be used for transparency and accountability, enabling automated recognition of conditions by AI systems | ✅ Schema-validator enforcing machine-readable metadata + audit-log structured-record format | `hummbl_governance/schema_validator.py`, `hummbl_governance/audit_log.py` |

### Copyright, IP, data libraries & national platform (Arts. 23–27)

| Obligation | Coverage | Evidence |
|---|---|---|
| Art. 23(1)–(2): AI-assisted works protected by copyright only with human creative contribution; creative prompts recognized as copyright objects | ⚪ Boundary: copyright-eligibility determination is a legal judgment, not software-addressable | |
| Art. 23(3)–(4): Use of works for AI training is not "free use" for educational/scientific purposes; does not constitute exercise of author's exclusive rights | ⚪ Boundary: copyright-law interpretation and licensing analysis is legal, not software-addressable | |
| Art. 23(5): AI training permitted only in absence of a machine-readable opt-out prohibition from the author/copyright holder | 🟡 Partial: schema-validator can verify presence/absence of machine-readable opt-out metadata; rights-clearance workflow is org task | `hummbl_governance/schema_validator.py`, `hummbl_governance/audit_log.py` |
| Art. 27(2)(5) + Art. 27(2): Data-library producer info must be in machine-readable form at creation and transfer; ensure data quality and compliance | ✅ Schema-validator enforcing producer-provenance metadata + audit-log data-library lineage + quality-validation gate | `hummbl_governance/schema_validator.py`, `hummbl_governance/audit_log.py` |
| Art. 25: National AI Platform provides a controlled environment for development, training, and trial operation of AI models | 🟡 Partial: kernel admission-control + capability-fence provide controlled-environment sandboxing; national-platform operation is org/government task | `hummbl_governance/kernel/admission_control.py`, `hummbl_governance/capability_fence.py` |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| Principles & general obligations (Arts. 4–9) | 5 | 4 | 1 | 0 |
| Data protection, privacy & safety (Arts. 10–11) | 3 | 3 | 0 | 0 |
| Risk management & owner/holder obligations (Arts. 11(3), 15, 18) | 4 | 4 | 0 | 0 |
| User rights & obligations (Art. 16) | 4 | 3 | 1 | 0 |
| Classification & prohibited practices (Art. 17) | 6 | 6 | 0 | 0 |
| Transparency, audit & machine-readable forms (Arts. 19–22) | 4 | 4 | 0 | 0 |
| Copyright, IP, data libraries & national platform (Arts. 23–27) | 5 | 1 | 2 | 2 |
| **Totals** | **31** | **25** | **4** | **2** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Prohibited practices overlap EU AI Act Art. 5 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Transparency and AI-use notification overlap EU AI Act Art. 50 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Risk management overlaps NIST AI RMF MEASURE — see [`nist-ai-rmf.md`](./nist-ai-rmf.md)
- Risk classification overlaps EU AI Act Art. 6 and Korea AI Basic Act Art. 34 — see [`eu-ai-act.md`](./eu-ai-act.md), [`south-korea-ai-basic-act.md`](./south-korea-ai-basic-act.md)
- Human oversight overlaps EU AI Act Art. 14 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Data protection overlaps GDPR Art. 5 — see [`gdpr.md`](./gdpr.md)
- Synthetic-content labeling overlaps Korea AI Basic Act Art. 31 — see [`south-korea-ai-basic-act.md`](./south-korea-ai-basic-act.md)
