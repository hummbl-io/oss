# Germany MISSION KI Quality Standard Coverage Matrix — HUMMBL

**Standard**: MISSION KI Quality Standard for Low-Risk AI (November 2025)
**Effective**: November 2025 (voluntary; no statutory effective date)
**Source**: https://mission-ki.de/en/quality-standards
**Last reviewed**: 2026-06-25
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not German legal counsel and does not provide legal advice on the MISSION KI Quality Standard. The standard is a voluntary, self-assessment framework developed by MISSION KI (acatech) with PwC Germany, TÜV AI.Lab, VDE, the AI Quality & Testing Hub, and Fraunhofer IAIS, funded by Germany's Federal Ministry for Digital Transformation and Government Modernisation. It targets AI systems that fall below the EU AI Act's high-risk threshold. Statutory compliance and assessment completion are the customer-organization responsibility. HUMMBL maps technical primitives to the standard's six quality dimensions and eight-step assessment process.

## Scope summary

The MISSION KI Quality Standard applies to AI providers — particularly start-ups and SMEs — deployers, and procurement authorities seeking voluntary, evidence-based verification of AI system quality for low-risk systems. It structures assessment around six quality dimensions derived from the EU HLEG Ethics Guidelines for Trustworthy AI and harmonized with EU AI Act high-risk requirements: (1) Reliability, (2) AI-specific cybersecurity, (3) Data quality/protection/governance, (4) Non-discrimination, (5) Transparency, (6) Human oversight and control. Each dimension decomposes into criteria, indicators, and observables (VCIO model from VDE SPEC 90012), graded A–D. Protection needs analysis (low/moderate/high) determines the minimum required grade per criterion. Existing certifications (ISO 27001, GDPR, BSI IT-Grundschutz) are recognized as evidence.

## Obligations + coverage

### Reliability — performance & robustness, fallback plans (§3.3 VE)

| Obligation | Coverage | Evidence |
|---|---|---|
| Conduct risk analysis for performance and robustness, prioritising hazards with designated responsibilities | ✅ Risk-identification + risk-treatment tuple types (cross-ref NIST AI RMF IDENTIFY, EU AI Act Art. 9) | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Test and document robustness against non-malicious adverse, disruptive, or faulty inputs | ✅ Output-validation gate + circuit-breaker fast-fail on anomalous inputs | `hummbl_governance/output_validator.py`, `hummbl_governance/circuit_breaker.py` |
| Implement fallback plans and general safety measures for system degradation | ✅ Kill-switch 4-mode halt + circuit-breaker fallback + lifecycle state transitions | `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py`, `hummbl_governance/lifecycle.py` |
| Monitor for concept drift and data drift that may invalidate performance assumptions | ✅ Health-probe anomaly detection + lifecycle validity tracking | `hummbl_governance/health_probe.py`, `hummbl_governance/lifecycle.py` |

### AI-specific cybersecurity — resistance to AI-specific attacks (§3.3 CY)

| Obligation | Coverage | Evidence |
|---|---|---|
| Implement resistance to AI-specific attacks (adversarial inputs, model poisoning, prompt injection) | ✅ Capability-fence sandbox + output-validation gate for adversarial-pattern rejection | `hummbl_governance/capability_fence.py`, `hummbl_governance/output_validator.py` |
| Document security measures and maintain audit trail for security-relevant events | ✅ Immutable audit-log with tamper-evident append + receipt-engine sequence | `hummbl_governance/audit_log.py`, `hummbl_governance/kernel/receipt_engine.py` |
| Integrate existing security certifications (ISO 27001, BSI IT-Grundschutz) as evidence | 🟡 Partial: compliance-mapper ingests external certification evidence; certification acquisition is org task | `hummbl_governance/compliance_mapper.py` |

### Data quality, protection & governance (§3.3 DA)

| Obligation | Coverage | Evidence |
|---|---|---|
| Document characteristics of each dataset used, including processing steps, labelling, and cleaning | ✅ Audit-log dataset-lineage tuples + schema-validated metadata records | `hummbl_governance/audit_log.py`, `hummbl_governance/schema_validator.py` |
| Perform systematic data quality checks (completeness, consistency, plausibility) | ✅ Schema-validator validation rules + output-validator plausibility gates | `hummbl_governance/schema_validator.py`, `hummbl_governance/output_validator.py` |
| Protect personal data in accordance with GDPR | ✅ Compliance-mapper GDPR crosswalk + identity-based access control (cross-ref GDPR Art. 5, 25) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/identity.py` |
| Enforce data access controls and protect proprietary data from unauthorised access | ✅ Identity registry + delegation-token scoped access + capability-fence boundary | `hummbl_governance/identity.py`, `hummbl_governance/delegation.py`, `hummbl_governance/capability_fence.py` |

### Non-discrimination (§3.3 ND)

| Obligation | Coverage | Evidence |
|---|---|---|
| Detect and mitigate unjustified distortions and bias in AI outputs | ✅ Output-validator bias-detection gates + reward-monitor distribution-drift detection | `hummbl_governance/output_validator.py`, `hummbl_governance/reward_monitor.py` |
| Ensure accessibility and universal design considerations are documented | 🟡 Partial: compliance-mapper assessment template captures accessibility criteria; design implementation is org task | `hummbl_governance/compliance_mapper.py` |
| Facilitate stakeholder participation in quality assessment | ⚪ Boundary: stakeholder engagement is an organizational process, not software-addressable | |

### Transparency — traceability, explainability, external communication (§3.3 TR)

| Obligation | Coverage | Evidence |
|---|---|---|
| Maintain traceability and documentation of system properties, decisions, and data lineage | ✅ Immutable audit-log + Lamport-clock causal ordering + receipt-engine sequence tracking | `hummbl_governance/audit_log.py`, `hummbl_governance/lamport_clock.py`, `hummbl_governance/kernel/receipt_engine.py` |
| Provide explainability and interpretability of AI system behaviour and outputs | ✅ Reasoning-engine rationale traces + compliance-mapper explanation-disclosure generator (cross-ref EU AI Act Art. 13) | `hummbl_governance/reasoning.py`, `hummbl_governance/compliance_mapper.py` |
| Communicate externally to users and stakeholders about AI use and system limitations | ✅ Output-validator provenance-labeling + compliance-mapper transparency-notification (cross-ref EU AI Act Art. 50) | `hummbl_governance/output_validator.py`, `hummbl_governance/compliance_mapper.py` |

### Human oversight & control (§3.3 HO)

| Obligation | Coverage | Evidence |
|---|---|---|
| Ensure human capacity to act — ability to observe, modify, and terminate the AI system | ✅ Kill-switch 4-mode halt + delegation-token human-oversight authority (cross-ref EU AI Act Art. 14) | `hummbl_governance/kill_switch.py`, `hummbl_governance/delegation.py` |
| Maintain human supervision during ongoing operation with appropriate professional competence | ✅ Health-probe monitoring + circuit-breaker escalation to human review + delegation named-contact | `hummbl_governance/health_probe.py`, `hummbl_governance/circuit_breaker.py`, `hummbl_governance/delegation.py` |

### Assessment process — use case through validity monitoring (§3.1–3.2, §4)

| Obligation | Coverage | Evidence |
|---|---|---|
| Describe the use case: intended purpose, context, components, limits of application domain | ✅ Compliance-mapper system-description template + audit-log system-registration tuple | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Conduct protection needs analysis classifying each criterion as low, moderate, high, or not applicable | ✅ Compliance-mapper impact-assessment template with protection-need classification tuples | `hummbl_governance/compliance_mapper.py` |
| Classify indicators via VCIO model and assign A–D observable levels with evidence | ✅ Compliance-mapper VCIO rating records + audit-log evidence-linking tuples | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Provide reproducible evidence: test reports, audit trails, full traceability for high protection need | ✅ Evidence-engine evidence collection + receipt-engine reproducibility + audit-log immutable trail | `hummbl_governance/kernel/evidence_engine.py`, `hummbl_governance/kernel/receipt_engine.py`, `hummbl_governance/audit_log.py` |
| Validate evidence per protection-need level (self-validation / internal experts / four-eyes principle) | 🟡 Partial: delegation-token supports reviewer assignment and independence; validation act is org task | `hummbl_governance/delegation.py`, `hummbl_governance/identity.py` |
| Produce overall assessment statement (pass/fail) comparing achieved vs. required levels per criterion | ✅ Compliance-mapper assessment-report generator with pass/fail logic per criterion | `hummbl_governance/compliance_mapper.py` |
| Generate signed assessment report with system info, protection needs, quality levels, and validation statement | ✅ Compliance-mapper report template + audit-log signed-declaration tuple + identity attestation | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py`, `hummbl_governance/identity.py` |
| Monitor validity: trigger reassessment on purpose change, significant technical change, or concept/data drift | ✅ Lifecycle validity tracking + health-probe drift detection + audit-log change-event tuples | `hummbl_governance/lifecycle.py`, `hummbl_governance/health_probe.py`, `hummbl_governance/audit_log.py` |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| Reliability (§3.3 VE) | 4 | 4 | 0 | 0 |
| AI-specific cybersecurity (§3.3 CY) | 3 | 2 | 1 | 0 |
| Data quality, protection & governance (§3.3 DA) | 4 | 4 | 0 | 0 |
| Non-discrimination (§3.3 ND) | 3 | 1 | 1 | 1 |
| Transparency (§3.3 TR) | 3 | 3 | 0 | 0 |
| Human oversight & control (§3.3 HO) | 2 | 2 | 0 | 0 |
| Assessment process (§3.1–3.2, §4) | 8 | 6 | 1 | 0 |
| **Totals** | **27** | **22** | **3** | **2** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Reliability and risk management overlap NIST AI RMF MEASURE — see [`nist-ai-rmf.md`](./nist-ai-rmf.md)
- Transparency and explainability overlap EU AI Act Art. 13, 50 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Human oversight overlaps EU AI Act Art. 14 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Data protection overlaps GDPR — see [`gdpr.md`](./gdpr.md)
- Cybersecurity evidence overlaps ISO 27001 — see [`iso-27001.md`](./iso-27001.md)
- Assessment process harmonized with VDE SPEC 90012 and Fraunhofer IAIS Assessment Catalogue
