# Peru Law No. 31814 + Supreme Decree 115-2025-PCM Coverage Matrix — HUMMBL

**Standard**: Law No. 31814 (Ley que promueve el uso de la inteligencia artificial en favor del desarrollo económico y social del país) + Supreme Decree No. 115-2025-PCM (Reglamento)
**Effective**: September 9, 2025 (publication); 90 business days thereafter (full force, approx. January 13, 2026)
**Source**: https://www.gob.pe/institucion/pcm/normas-legales/7133522-115-2025-pcm
**Last reviewed**: 2026-06-25
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not Peruvian legal counsel and does not provide legal advice on Law No. 31814 or Supreme Decree 115-2025-PCM. The Regulation distinguishes "uso indebido" (prohibited), "riesgo alto" (high-risk), and "riesgo aceptable" (acceptable risk) classifications, and assigns roles to developers (desarrolladores), implementers (implementadores), and users (usuarios). Statutory compliance is the customer-organization responsibility. HUMMBL maps technical primitives to the Regulation's risk-classification, transparency, privacy, security-audit, human-oversight, and incident-management obligations.

## Scope summary

The Regulation applies to public entities of the Peruvian Administration, state enterprises (FONAFE), and private organizations, civil society, citizens, and academia within the National System of Digital Transformation (SNTD). It exempts personal-use AI and defense/national-security AI (subject to principles). The SGTD (Secretariat of Government and Digital Transformation) of the PCM is the national technical-normative authority. High-risk uses cover critical infrastructure, education, employment, social programs, credit, healthcare, and emotion inference. Prohibited uses include deceptive manipulation, lethal autonomous systems, mass surveillance without legal basis, sensitive-attribute inference, real-time biometric identification (with limited exceptions), and crime-prediction profiling. Implementation is phased: 1–4 years for private sector depending on industry; 1–3 years for public entities depending on government level.

## Obligations + coverage

### Risk classification & prohibited uses (Art. 22–23)

| Obligation | Coverage | Evidence |
|---|---|---|
| Tripartite risk classification of AI systems: prohibited (uso indebido), high-risk (riesgo alto), acceptable (riesgo aceptable) | ✅ Risk-classification tuple + impact-assessment template (cross-ref EU AI Act Art. 6, NIST AI RMF MAP) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Prohibited: deceptive or manipulative influence on human decision-making using subliminal techniques or exploitation of vulnerabilities | ✅ Output-validation gate blocks manipulative outputs + capability fence restricts persuasion capabilities | `hummbl_governance/output_validator.py`, `hummbl_governance/capability_fence.py` |
| Prohibited: lethal autonomous systems that make decisions without human supervision causing physical harm | ✅ Kill-switch 4-mode halt + physical-AI safety governor enforces human-in-the-loop for physical actions | `hummbl_governance/kill_switch.py`, `hummbl_governance/physical_governor.py` |
| Prohibited: mass surveillance without legal basis or disproportionate impact on fundamental rights | ⚪ Boundary: legal-basis determination for surveillance is legal, not software-addressable | |
| Prohibited: inference of sensitive attributes (race, politics, religion, sexual orientation) from biometric data | ✅ Capability fence restricts inference scopes + output validator blocks sensitive-attribute outputs | `hummbl_governance/capability_fence.py`, `hummbl_governance/output_validator.py` |
| Prohibited: crime prediction based on personality profiling or trait assessment | ✅ Capability fence restricts profiling scopes + output validator blocks predictive-crime outputs | `hummbl_governance/capability_fence.py`, `hummbl_governance/output_validator.py` |

### High-risk uses & impact assessment (Art. 24, 30, 32)

| Obligation | Coverage | Evidence |
|---|---|---|
| High-risk classification: critical infrastructure, education, employment, social programs, credit, healthcare, emotion inference | ✅ Impact-assessment template + classification tuple for high-risk sector mapping | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Mandatory impact assessment for public-entity high-risk AI before development or implementation (Art. 30) | ✅ Impact-assessment template with risk-identification + mitigation cycle (cross-ref EU AI Act Art. 27 FRIA, NIST AI RMF MEASURE) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Voluntary impact assessment for private-sector high-risk AI (Art. 32) | ✅ Impact-assessment template available for voluntary use + recognition pathway | `hummbl_governance/compliance_mapper.py` |
| Mitigation measures when risks detected: model adjustments, data-quality improvement, human-oversight mechanisms | ✅ Risk-treatment tuples + adverse-event monitoring + iterative mitigation cycle | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py`, `hummbl_governance/coordination_bus.py` |
| Documentation retention for private impact assessments: minimum 3 years, available to judicial/administrative authorities | ✅ Immutable audit-log retention with timestamped evidence tuples | `hummbl_governance/audit_log.py` |

### Transparency & explainability (Art. 25)

| Obligation | Coverage | Evidence |
|---|---|---|
| Prior, clear, and simple notification to users of AI system purpose, functionality, and decision types | ✅ Transparency-notification primitive + compliance-report generator (cross-ref EU AI Act Art. 50, South Korea Art. 31) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Visible AI labeling of products, services, or AI-generated content, including capabilities and limitations | ✅ Provenance-labeling tuple type + output-validation gate for AI-content marking (cross-ref EU AI Act Art. 50(2)) | `hummbl_governance/output_validator.py`, `hummbl_governance/audit_log.py` |
| Explanation of automated decisions affecting human rights, in accessible language with key criteria and factors | ✅ Reasoning-engine explanation trace + explanation-disclosure generator (cross-ref EU AI Act Art. 13, Colorado deployer disclosure) | `hummbl_governance/reasoning.py`, `hummbl_governance/compliance_mapper.py` |

### Privacy, data governance & ethics (Art. 26–27)

| Obligation | Coverage | Evidence |
|---|---|---|
| Compliance with Law No. 29733 (Personal Data Protection) and ANPDP authority | 🟡 Partial: data-governance primitives support minimization and audit; statutory compliance with Law 29733 is org task | `hummbl_governance/audit_log.py`, `hummbl_governance/schema_validator.py` |
| Privacy by design: data minimization, anonymization techniques integrated into AI system development (Art. 29.b) | ✅ Capability fence enforces data-scope limits + schema validator enforces minimization constraints | `hummbl_governance/capability_fence.py`, `hummbl_governance/schema_validator.py` |
| Diverse and multidisciplinary teams for AI development and implementation | ⚪ Boundary: team composition is organizational, not software-addressable | |
| Bias identification and minimization using best practices, national/international standards | ✅ Output validator detects biased outputs + reward monitor flags disparate-impact patterns in agent behavior | `hummbl_governance/output_validator.py`, `hummbl_governance/reward_monitor.py` |

### Security, audit & incident management (Art. 29)

| Obligation | Coverage | Evidence |
|---|---|---|
| Risk management: encryption, anomaly detection, model robustness measures for AI systems | ✅ Circuit-breaker anomaly detection + cost-governor budget enforcement + capability fence robustness controls | `hummbl_governance/circuit_breaker.py`, `hummbl_governance/cost_governor.py`, `hummbl_governance/capability_fence.py` |
| Security audits: mandatory before deployment and periodic during operation, identifying vulnerabilities and biases | ✅ Audit-log evidence tuples + compliance-mapper audit template with pre-deployment and operational checkpoints | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Incident management: AI-related incidents managed as part of Information Security Management System | ✅ Circuit-breaker fast-fail + health-probe monitoring + audit-log incident tuples + coordination-bus alert propagation | `hummbl_governance/circuit_breaker.py`, `hummbl_governance/health_probe.py`, `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py` |
| Adoption of NTP-ISO/IEC 42001:2025 AI Management System (SGIA) and related standards (ISO 27002, ISO 38507, ISO 23053) | 🟡 Partial: compliance-mapper crosswalks to ISO 42001 controls; full AIMS certification is org task | `hummbl_governance/compliance_mapper.py` |

### Human oversight & accountability (Art. 7, 28, 31)

| Obligation | Coverage | Evidence |
|---|---|---|
| Human oversight of high-risk AI in public entities: health, education, justice, finance, social services (Art. 28.11) | ✅ Human-oversight delegation token + authority-engine enforcement of human-in-the-loop (cross-ref EU AI Act Art. 14, South Korea Art. 34) | `hummbl_governance/delegation.py`, `hummbl_governance/kernel/authority_engine.py` |
| Personnel trained in subject matter to avoid over-reliance on AI results (Art. 28.11.i, 31.4.i) | ⚪ Boundary: personnel training and competency development is organizational | |
| Personnel must have capacity to stop, correct, or invalidate AI decisions (Art. 28.11.ii, 31.4.ii) | ✅ Kill-switch 4-mode halt + circuit-breaker fast-fail + delegation override token | `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py`, `hummbl_governance/delegation.py` |
| Updated, accessible registry of system operation principles, data sources, algorithm logic, and social/ethical impacts (Art. 31.1) | ✅ Immutable audit-log registry + evidence tuples documenting system provenance and impact assessments | `hummbl_governance/audit_log.py`, `hummbl_governance/kernel/evidence_engine.py` |
| Policies, protocols, and procedures for security, privacy, transparency, explainability, and accountability (Art. 31.2) | ✅ Compliance-mapper policy framework + audit-log procedural evidence + law-engine rule encoding | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py`, `hummbl_governance/kernel/law_engine.py` |

### Supervision, monitoring & governance (Art. 8, 34–36)

| Obligation | Coverage | Evidence |
|---|---|---|
| SGTD monitoring of prohibited and high-risk AI uses in national territory (Art. 8.c, 35) | 🟡 Partial: audit-log export + compliance-report generator supports monitoring; SGTD surveillance act is government task | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| SGTD supervision: report noncompliance to Contraloría General de la República and sectoral authorities (Art. 34) | ⚪ Boundary: government supervisory reporting is organizational, not software-addressable | |
| Citizen alert and complaint mechanism for AI misuse via digital channel (www.gob.pe/iaperu) (Art. 36) | ⚪ Boundary: government complaint platform is organizational, not software-addressable | |
| Annual report to Congress on AI implementation, PNTD, and ENIA progress (Art. 8.h) | ⚪ Boundary: government legislative reporting is organizational | |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| Risk classification & prohibited uses (Art. 22–23) | 6 | 5 | 0 | 1 |
| High-risk uses & impact assessment (Art. 24, 30, 32) | 5 | 5 | 0 | 0 |
| Transparency & explainability (Art. 25) | 3 | 3 | 0 | 0 |
| Privacy, data governance & ethics (Art. 26–27) | 4 | 2 | 1 | 1 |
| Security, audit & incident management (Art. 29) | 4 | 3 | 1 | 0 |
| Human oversight & accountability (Art. 7, 28, 31) | 5 | 4 | 0 | 1 |
| Supervision, monitoring & governance (Art. 8, 34–36) | 4 | 0 | 1 | 3 |
| **Totals** | **31** | **22** | **3** | **6** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Risk classification overlaps EU AI Act Arts. 5–6 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Transparency overlaps EU AI Act Art. 50 and South Korea Art. 31 — see [`eu-ai-act.md`](./eu-ai-act.md), [`south-korea-ai-basic-act.md`](./south-korea-ai-basic-act.md)
- Impact assessment overlaps EU AI Act Art. 27 (FRIA) — see [`eu-ai-act.md`](./eu-ai-act.md)
- Human oversight overlaps EU AI Act Art. 14 and South Korea Art. 34 — see [`eu-ai-act.md`](./eu-ai-act.md), [`south-korea-ai-basic-act.md`](./south-korea-ai-basic-act.md)
- ISO 42001 adoption overlaps ISO 42001 coverage — see [`iso-42001.md`](./iso-42001.md)
- Security controls overlap ISO 27001 and NIST CSF — see [`iso-27001.md`](./iso-27001.md), [`nist-csf.md`](./nist-csf.md)
- Risk management overlaps NIST AI RMF MAP/MEASURE — see [`nist-ai-rmf.md`](./nist-ai-rmf.md)
