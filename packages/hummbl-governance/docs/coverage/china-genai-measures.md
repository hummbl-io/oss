# China Generative AI Interim Measures Coverage Matrix — HUMMBL

**Standard**: Interim Measures for the Administration of Generative Artificial Intelligence Services (生成式人工智能服务管理暂行办法), Order No. 15
**Effective**: August 15, 2023
**Source**: http://www.cac.gov.cn/2023-07/13/c_1690898327029107.htm
**Last reviewed**: 2026-05-14
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not Chinese legal counsel and does not provide legal advice on the Generative AI Interim Measures. The Measures are enforced by the Cyberspace Administration of China (CAC) with penalties under existing cybersecurity, data security, and PIPL laws. Statutory compliance is the customer-organization responsibility. HUMMBL maps technical primitives to the Measures' content safety, data governance, incident response, and labeling obligations.

## Scope summary

The Measures apply to generative AI service providers offering services to the public within China. They impose obligations across the full AI lifecycle: training data sourcing, data annotation, content generation, user management, personal information protection, content labeling, incident response, complaint handling, security assessment, algorithm filing, and government inspection cooperation.

## Obligations + coverage

### General service requirements (Art. 4)

| Obligation | Coverage | Evidence |
|---|---|---|
| Generate content complying with laws, regulations, and social morality | ✅ Output-validation gate + prohibited-content tuple | `hummbl_governance/output_validator.py`, `hummbl_governance/audit_log.py` |
| Prevent generation of prohibited content (national security, ethnic unity, terrorism, obscenity, false information, IP violations) | ✅ Prohibited-content-output gate + content-filtering primitive | `hummbl_governance/output_validator.py`, `hummbl_governance/kill_switch.py` |
| Generate high-quality, accurate content | ✅ Output-quality-validation tuple + accuracy-checking primitive | `hummbl_governance/output_validator.py` |
| Respect intellectual property and commercial secrets in training data and generated content | ✅ IP-respect tuple + data-classification primitive (cross-ref AB 2013) | `hummbl_governance/audit_log.py`, `hummbl_governance/schema_validator.py` |
| Protect personal information and data security | ✅ PII-protection tuple + data-classification primitive (cross-ref GDPR Art. 32) | `hummbl_governance/schema_validator.py`, `hummbl_governance/audit_log.py` |

### Training data obligations (Art. 7)

| Obligation | Coverage | Evidence |
|---|---|---|
| Use lawful data sources and foundation models for training | ✅ Data-source-lawfulness tuple + provenance-tracking primitive | `hummbl_governance/audit_log.py` |
| Do not infringe IP rights in training data | ✅ IP-compliance-verification tuple | `hummbl_governance/audit_log.py` |
| Obtain individual consent or lawful basis for personal information in training data (PIPL) | ✅ Consent-verification tuple + lawful-basis-record (cross-ref GDPR Art. 6/9) | `hummbl_governance/audit_log.py`, `hummbl_governance/delegation.py` |
| Take measures to improve training data quality (authenticity, accuracy, objectivity, diversity) | ✅ Data-quality-assessment tuple + validation primitive | `hummbl_governance/schema_validator.py`, `hummbl_governance/audit_log.py` |
| Take remedial measures against unlawful content in training data | ✅ Data-remediation tuple + corrective-action primitive | `hummbl_governance/audit_log.py` |

### Data annotation obligations (Art. 8)

| Obligation | Coverage | Evidence |
|---|---|---|
| Formulate clear, specific, operational annotation rules compliant with the Measures | ✅ Annotation-rules-documentation tuple | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Conduct data annotation quality assessment and sample-check accuracy | ✅ Annotation-quality-assessment tuple + sampling primitive | `hummbl_governance/audit_log.py` |
| Provide necessary training to annotation personnel | ⚪ Boundary: personnel training is organizational | |
| Supervise and guide annotation personnel in standardized work | ⚪ Boundary: personnel management is organizational | |

### Content producer responsibilities (Art. 9)

| Obligation | Coverage | Evidence |
|---|---|---|
| Bear network information security responsibilities as content producer | ✅ Audit-log immutability + security-responsibility tuple | `hummbl_governance/audit_log.py` |
| Bear personal information processor responsibilities under PIPL | ✅ PIPL-compliance tuple + data-controller-record (cross-ref GDPR Art. 24) | `hummbl_governance/audit_log.py`, `hummbl_governance/schema_validator.py` |
| Sign service agreements with registered users specifying rights and obligations | ⚪ Boundary: contract execution is organizational | |

### User management obligations (Art. 10)

| Obligation | Coverage | Evidence |
|---|---|---|
| Clearly specify and publicly disclose intended user groups, contexts, and purposes | ✅ Service-scope-disclosure tuple + transparency primitive | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Guide users toward scientific, rational, and lawful use of generative AI | 🟡 Partial: usage-guidance tuple; user-education implementation is org task | `hummbl_governance/compliance_mapper.py` |
| Take measures to prevent minor users from excessive dependence or addiction | ⚪ Boundary: age-verification and addiction-prevention is product-level, not platform primitive | |

### Personal information protection (Art. 11)

| Obligation | Coverage | Evidence |
|---|---|---|
| Protect users' input information and usage records | ✅ Data-protection tuple + encryption-at-rest primitive (cross-ref GDPR Art. 32) | `hummbl_governance/audit_log.py`, `hummbl_governance/schema_validator.py` |
| Do not collect non-essential personal information | ✅ Data-minimization primitive + collection-scope tuple | `hummbl_governance/delegation.py`, `hummbl_governance/schema_validator.py` |
| Do not illegally retain input information that can identify users | ✅ Retention-limit tuple + pseudonymisation primitive (cross-ref GDPR Art. 25) | `hummbl_governance/audit_log.py` |
| Do not illegally provide user input information to others | ✅ Data-sharing-prohibition tuple + access-control primitive | `hummbl_governance/delegation.py` |
| Timely accept and handle user requests for access, copy, amend, supplement, or delete personal information | ✅ Data-subject-rights tuple + request-handling primitive (cross-ref GDPR Art. 15-17) | `hummbl_governance/audit_log.py` |

### Labeling obligations (Art. 12)

| Obligation | Coverage | Evidence |
|---|---|---|
| Mark images, videos, and other generated content per Deep Synthesis Provisions (2022) | ✅ Content-labeling tuple + provenance-labeling primitive (cross-ref SB 942, Korea Art. 31) | `hummbl_governance/output_validator.py`, `hummbl_governance/audit_log.py` |
| Prominent identification for AI dialogue, synthetic voice, face generation, immersive scenes | ✅ Prominent-labeling tuple + disclosure primitive | `hummbl_governance/output_validator.py` |
| Include prominent identification function for other deep synthesis services | ✅ Identification-function tuple + labeling primitive | `hummbl_governance/output_validator.py` |

### Service stability (Art. 13)

| Obligation | Coverage | Evidence |
|---|---|---|
| Provide safe, stable, and continuous services | ✅ Circuit-breaker resilience + health-probe monitoring (cross-ref NIST CSF PR) | `hummbl_governance/circuit_breaker.py`, `hummbl_governance/health_probe.py` |

### Content safety and incident response (Art. 14)

| Obligation | Coverage | Evidence |
|---|---|---|
| Detect illegal content generated by the service | ✅ Content-detection primitive + output-validation gate | `hummbl_governance/output_validator.py` |
| Immediately cease generation and transmission when illegal content found | ✅ Kill-switch halt + output-blocking primitive | `hummbl_governance/kill_switch.py`, `hummbl_governance/output_validator.py` |
| Eliminate illegal content when detected | ✅ Content-removal tuple + remediation primitive | `hummbl_governance/audit_log.py` |
| Take model optimization training measures to rectify and prevent recurrence | 🟡 Partial: rectification-record tuple; model retraining is org task | `hummbl_governance/audit_log.py` |
| Report illegal content incidents to competent authorities | ✅ Incident-report tuple + reporting-SLA primitive | `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py` |
| Take measures against users misusing services (warnings, restrictions, suspension, termination) | ✅ User-misuse-response tuple + capability-fence primitive | `hummbl_governance/capability_fence.py`, `hummbl_governance/audit_log.py` |
| Save records of user misuse incidents | ✅ Immutable audit-log retention + misuse-record tuple | `hummbl_governance/audit_log.py` |
| Report user misuse to relevant authorities | ✅ Incident-report tuple + reporting primitive | `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py` |

### Complaint mechanism (Art. 15)

| Obligation | Coverage | Evidence |
|---|---|---|
| Establish complaint and reporting mechanisms | ✅ Complaint-intake tuple + audit-log record | `hummbl_governance/audit_log.py` |
| Set up convenient complaint/reporting entry points | 🟡 Partial: complaint-intake primitive; UI/access-points are org task | `hummbl_governance/audit_log.py` |
| Publicly disclose processing workflows and feedback timeframes | 🟡 Partial: workflow-documentation tuple; publication is org task | `hummbl_governance/compliance_mapper.py` |
| Timely accept, process, and provide feedback on complaints | ✅ Complaint-handling-SLA tuple + response-tracking primitive | `hummbl_governance/audit_log.py`, `hummbl_governance/lifecycle.py` |

### Security assessment and algorithm filing (Art. 17)

| Obligation | Coverage | Evidence |
|---|---|---|
| Conduct security assessment for services with public opinion or social mobilization attributes | ✅ Security-assessment template + risk-assessment primitive (cross-ref NIST AI RMF MAP) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Fulfill algorithm filing, alteration, and cancellation procedures | ⚪ Boundary: government-filing procedure is organizational | |

### Government inspection cooperation (Art. 19)

| Obligation | Coverage | Evidence |
|---|---|---|
| Cooperate with competent authorities' supervision and inspection | 🟡 Partial: audit-log export + compliance-report generator supports inspection; cooperation act is org task | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Provide explanations of training data sources, scale, types, annotation rules, algorithm mechanisms | ✅ Documentation-export primitive + compliance-report generator | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Provide necessary technical and data support to authorities | 🟡 Partial: data-export primitive; support provision is org task | `hummbl_governance/audit_log.py` |

### Licensing (Art. 23)

| Obligation | Coverage | Evidence |
|---|---|---|
| Obtain required permits where laws or regulations require permits for generative AI services | ⚪ Boundary: government-licensing is organizational | |

### Penalties (Art. 21)

| Obligation | Coverage | Evidence |
|---|---|---|
| Violations punished under Cybersecurity Law, Data Security Law, PIPL, Science and Technology Progress Law | ⚪ Boundary: legal-penalty framework is institutional | |
| Administrative penalties (warnings, criticism, rectification orders) where existing laws have no provisions | ⚪ Boundary: administrative-penalty exposure is legal | |
| Service suspension for refusal to rectify or serious violations | ⚪ Boundary: regulatory-ordered suspension is institutional | |
| Criminal liability for violations constituting crimes | ⚪ Boundary: criminal liability is legal | |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| General service (Art. 4) | 5 | 5 | 0 | 0 |
| Training data (Art. 7) | 5 | 5 | 0 | 0 |
| Data annotation (Art. 8) | 4 | 2 | 0 | 2 |
| Content producer (Art. 9) | 3 | 2 | 0 | 1 |
| User management (Art. 10) | 3 | 1 | 1 | 1 |
| Personal information (Art. 11) | 5 | 5 | 0 | 0 |
| Labeling (Art. 12) | 3 | 3 | 0 | 0 |
| Service stability (Art. 13) | 1 | 1 | 0 | 0 |
| Content safety + incident response (Art. 14) | 8 | 7 | 1 | 0 |
| Complaint mechanism (Art. 15) | 4 | 2 | 2 | 0 |
| Security assessment + filing (Art. 17) | 2 | 1 | 0 | 1 |
| Government cooperation (Art. 19) | 3 | 1 | 2 | 0 |
| Licensing (Art. 23) | 1 | 0 | 0 | 1 |
| Penalties (Art. 21) | 4 | 0 | 0 | 4 |
| **Totals** | **51** | **35** | **6** | **10** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Content labeling overlaps California SB 942 — see [`california-sb-942.md`](./california-sb-942.md)
- Content labeling overlaps South Korea AI Basic Act Art. 31 — see [`south-korea-ai-basic-act.md`](./south-korea-ai-basic-act.md)
- Personal information overlaps GDPR — see [`gdpr.md`](./gdpr.md)
- Incident response overlaps NIST CSF RS — see [`nist-csf.md`](./nist-csf.md)
- Kill switch for content blocking — see [`stride.md`](./stride.md) D — Denial of Service
