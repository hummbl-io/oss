# China Deep Synthesis Provisions Coverage Matrix — HUMMBL

**Standard**: Provisions on the Administration of Deep Synthesis of Internet Information Services (互联网信息服务深度合成管理规定), Order No. 12
**Effective**: January 10, 2023
**Source**: http://www.cac.gov.cn/2022-12/11/c_1672221949354811.htm
**Last reviewed**: 2026-06-25
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not Chinese legal counsel and does not provide legal advice on the Deep Synthesis Provisions. The Provisions are issued jointly by the Cyberspace Administration of China (CAC), the Ministry of Industry and Information Technology (MIIT), and the Ministry of Public Security (MPS), with penalties under existing cybersecurity, data security, and PIPL laws. Statutory compliance is the customer-organization responsibility. HUMMBL maps technical primitives to the Provisions' content labeling, training data governance, algorithm filing, security assessment, identity verification, and content moderation obligations.

## Scope summary

The Provisions apply to the application of deep synthesis technology to provide internet information services within China. Deep synthesis technology encompasses text, voice, music, image, video, and virtual-scene generation or editing using deep learning and virtual reality. The Provisions distinguish "deep synthesis service providers" (organizations or individuals providing the service), "technical supporters" (organizations or individuals providing technical support), and "users" (organizations or individuals using the service). Obligations span identity verification, content moderation, training data governance, algorithm review, security assessment, synthetic content labeling, algorithm filing, and government inspection cooperation.

## Obligations + coverage

### General service requirements (Arts. 4, 6)

| Obligation | Coverage | Evidence |
|---|---|---|
| Comply with laws, regulations, social morality, and correct political/opinion/value direction | ✅ Output-validation gate + prohibited-content tuple | `hummbl_governance/output_validator.py`, `hummbl_governance/audit_log.py` |
| Do not use deep synthesis to produce, reproduce, publish, or disseminate legally prohibited information | ✅ Prohibited-content-output gate + content-filtering primitive | `hummbl_governance/output_validator.py`, `hummbl_governance/kill_switch.py` |
| Do not use deep synthesis to produce, reproduce, publish, or disseminate false news information | ✅ False-information-detection tuple + output-blocking primitive (cross-ref China GenAI Art. 4) | `hummbl_governance/output_validator.py`, `hummbl_governance/audit_log.py` |

### Information security management (Arts. 7, 8)

| Obligation | Coverage | Evidence |
|---|---|---|
| Establish information security responsibility system (user registration, algorithm review, ethics review, content review, data security, PIPL, anti-fraud, emergency response) | ✅ Security-responsibility tuple + audit-log immutability (cross-ref NIST CSF PR) | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Maintain safe and controllable technical safeguards | ✅ Kill-switch 4-mode halt + circuit-breaker fast-fail + capability-fence enforcement | `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py`, `hummbl_governance/capability_fence.py` |
| Formulate and publicize management rules, platform conventions, and service agreements | 🟡 Partial: rules-documentation tuple; public publication is org task | `hummbl_governance/compliance_mapper.py` |
| Prominently notify technical supporters and users of information security obligations | 🟡 Partial: notification tuple; user-facing notification delivery is org task | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |

### Identity verification and user management (Arts. 9, 12)

| Obligation | Coverage | Evidence |
|---|---|---|
| Conduct real-name identity verification of users (mobile number, ID number, unified social credit code, or national network identity authentication) | ✅ Identity-verification tuple + authentication primitive (cross-ref GDPR Art. 6/9) | `hummbl_governance/identity.py`, `hummbl_governance/audit_log.py` |
| Do not provide information publishing services to users without real-name authentication | ✅ Access-control gate + identity-verification enforcement primitive | `hummbl_governance/identity.py`, `hummbl_governance/capability_fence.py` |
| Set up convenient user appeal and public complaint/reporting channels with published processing workflows and feedback timeframes | 🟡 Partial: complaint-intake tuple + SLA-tracking primitive; UI/access-points and publication are org task | `hummbl_governance/audit_log.py`, `hummbl_governance/lifecycle.py` |

### Content moderation and incident response (Arts. 10, 11)

| Obligation | Coverage | Evidence |
|---|---|---|
| Review input data and synthesis results using technical or manual methods | ✅ Output-validation gate + input-screening primitive | `hummbl_governance/output_validator.py`, `hummbl_governance/schema_validator.py` |
| Build and maintain feature library for identifying illegal and harmful content with entry standards, rules, and procedures | ✅ Prohibited-content-feature tuple + content-filtering primitive | `hummbl_governance/output_validator.py`, `hummbl_governance/audit_log.py` |
| Record and retain relevant network logs | ✅ Immutable audit-log retention + network-log tuple | `hummbl_governance/audit_log.py` |
| Take disposal measures upon discovering illegal/harmful content (save records, report to authorities, warn/restrict/suspend/terminate users) | ✅ Kill-switch halt + user-misuse-response tuple + incident-report primitive | `hummbl_governance/kill_switch.py`, `hummbl_governance/capability_fence.py`, `hummbl_governance/audit_log.py` |
| Establish rumor-refutation mechanism; take counter-rumor measures, save records, and report to authorities when false information detected | ✅ Rumor-refutation tuple + incident-report primitive + audit-log record | `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py` |

### Data and technical management (Arts. 14, 15)

| Obligation | Coverage | Evidence |
|---|---|---|
| Strengthen training data management and take necessary measures to ensure training data security | ✅ Data-source-lawfulness tuple + provenance-tracking primitive (cross-ref China GenAI Art. 7) | `hummbl_governance/audit_log.py`, `hummbl_governance/schema_validator.py` |
| Comply with personal information protection regulations when training data contains personal information | ✅ PII-protection tuple + consent-verification primitive (cross-ref GDPR Art. 6/9, PIPL) | `hummbl_governance/schema_validator.py`, `hummbl_governance/delegation.py` |
| For biometric (face, voice) editing features, prompt users to inform and obtain separate consent from edited individuals | ✅ Consent-verification tuple + biometric-data-consent primitive | `hummbl_governance/delegation.py`, `hummbl_governance/audit_log.py` |
| Periodically review, assess, and verify generative/synthetic algorithm mechanisms | ✅ Algorithm-review tuple + periodic-assessment primitive (cross-ref NIST AI RMF MAP) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Conduct security assessment (self or commissioned) for models/templates that generate or edit biometric info or special non-biometric info involving national security/interest | ✅ Security-assessment template + risk-assessment primitive (cross-ref NIST AI RMF MAP, China GenAI Art. 17) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |

### Synthetic content labeling (Arts. 16, 17, 18)

| Obligation | Coverage | Evidence |
|---|---|---|
| Add non-intrusive technical markers to all generated or edited content and retain logs per law | ✅ Implicit-labeling tuple + provenance-labeling primitive (cross-ref China GenAI Art. 12, SB 942) | `hummbl_governance/output_validator.py`, `hummbl_governance/audit_log.py` |
| Apply prominent labeling for deep synthesis content likely to cause public confusion (text, voice, face, immersive scenes) | ✅ Prominent-labeling tuple + disclosure primitive (cross-ref Korea Art. 31, EU AI Act Art. 50(2)) | `hummbl_governance/output_validator.py` |
| Provide prominent-labeling function and prompt users to apply it for other deep synthesis services | ✅ Identification-function tuple + labeling primitive | `hummbl_governance/output_validator.py` |
| Prohibit any organization or individual from removing, tampering with, or concealing deep synthesis labels | ✅ Label-integrity-verification tuple + tamper-detection primitive | `hummbl_governance/output_validator.py`, `hummbl_governance/audit_log.py` |
| Retain log information for labeled content per laws, regulations, and national provisions | ✅ Immutable audit-log retention + labeling-log tuple | `hummbl_governance/audit_log.py` |

### Algorithm filing, supervision, app stores, and penalties (Arts. 13, 19, 20, 21, 22)

| Obligation | Coverage | Evidence |
|---|---|---|
| Algorithm filing, alteration, cancellation, and public filing-number display for services with public opinion or social mobilization attributes per Algorithmic Recommendation Provisions | ⚪ Boundary: government-filing procedure and public-facing filing display are organizational | |
| Conduct security assessment for new products, applications, or features with public opinion or social mobilization attributes | ✅ Security-assessment template + risk-assessment primitive (cross-ref China GenAI Art. 17, NIST AI RMF MAP) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Cooperate with government supervision and inspection; provide necessary technical and data support | 🟡 Partial: audit-log export + compliance-report generator supports inspection; cooperation act is org task | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Comply with government risk-based suspension orders (pause info updates, user registration, or other services) | ✅ Kill-switch halt + circuit-breaker fast-fail + suspension-enforcement primitive | `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py` |
| App stores verify security assessment and filing status of deep synthesis apps; violations punished under Cybersecurity Law, Data Security Law, PIPL with administrative and criminal penalties | ⚪ Boundary: app-store platform governance and legal-penalty framework are institutional | |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| General service (Arts. 4, 6) | 3 | 3 | 0 | 0 |
| Information security management (Arts. 7, 8) | 4 | 2 | 2 | 0 |
| Identity verification + user mgmt (Arts. 9, 12) | 3 | 2 | 1 | 0 |
| Content moderation + incident response (Arts. 10, 11) | 5 | 5 | 0 | 0 |
| Data + technical management (Arts. 14, 15) | 5 | 5 | 0 | 0 |
| Synthetic content labeling (Arts. 16, 17, 18) | 5 | 5 | 0 | 0 |
| Filing, supervision, app stores, penalties (Arts. 13, 19, 20, 21, 22) | 5 | 2 | 1 | 2 |
| **Totals** | **30** | **24** | **4** | **2** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Content labeling overlaps China Generative AI Interim Measures Art. 12 — see [`china-genai-measures.md`](./china-genai-measures.md)
- Content labeling overlaps California SB 942 — see [`california-sb-942.md`](./california-sb-942.md)
- Content labeling overlaps South Korea AI Basic Act Art. 31 — see [`south-korea-ai-basic-act.md`](./south-korea-ai-basic-act.md)
- Prominent labeling overlaps EU AI Act Art. 50(2) — see [`eu-ai-act.md`](./eu-ai-act.md)
- Personal information overlaps GDPR — see [`gdpr.md`](./gdpr.md)
- Security assessment overlaps NIST AI RMF MAP — see [`nist-ai-rmf.md`](./nist-ai-rmf.md)
- Incident response overlaps NIST CSF RS — see [`nist-csf.md`](./nist-csf.md)
- Kill switch for content blocking — see [`stride.md`](./stride.md) D — Denial of Service
