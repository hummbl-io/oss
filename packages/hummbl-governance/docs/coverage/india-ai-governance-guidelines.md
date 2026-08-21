# India AI Governance Guidelines Coverage Matrix — HUMMBL

**Standard**: India AI Governance Guidelines: Enabling Safe and Trusted AI Innovation (MeitY, IndiaAI Mission)
**Effective**: November 5, 2025 (published; phased implementation per Action Plan — short, medium, long-term)
**Source**: https://static.pib.gov.in/WriteReadData/specificdocs/documents/2025/nov/doc2025115685601.pdf
**Last reviewed**: 2026-06-25
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not Indian legal counsel and does not provide legal advice on the India AI Governance Guidelines. The Guidelines are a techno-legal, principle-based framework — not a standalone statute. They recommend voluntary compliance measures, graded liability, and reliance on existing Indian laws (IT Act 2000, DPDP Act 2023, Consumer Protection Act 2019, Copyright Act 1957) plus sectoral regulation (RBI, SEBI, TRAI, CCI). The Guidelines propose new institutional bodies (AIGG, TPEC, AISI) that do not yet exist as statutory entities. Statutory compliance is the customer-organization responsibility. HUMMBL maps technical primitives to the Guidelines' seven sutras, risk-mitigation, accountability, transparency, incident-reporting, and practical-industry obligations.

## Scope summary

The Guidelines apply to all entities developing or deploying AI systems in India, including developers, deployers, and users across the AI value chain. They are technology-neutral and cross-sectoral, with sectoral regulators continuing domain-specific enforcement. The framework identifies seven risk areas (malicious use, bias and discrimination, transparency failures, systemic risk, loss of control, national security threats, risk to vulnerable groups) and recommends a graded liability approach proportionate to role and risk. The Guidelines do not create new statutory penalties; existing laws and sectoral regulatory powers continue to apply. Implementation is phased: short-term (establish AIGG/TPEC, risk frameworks, voluntary commitments), medium-term (technical standards, incident database, sandboxes, law amendments), and long-term (monitoring, new laws, global standards leadership).

## Obligations + coverage

### Guiding principles — Seven Sutras (Part 1)

| Obligation | Coverage | Evidence |
|---|---|---|
| Trust is the Foundation — embed trust across the value chain (technology, stakeholders, users) | ✅ Audit-log immutability + compliance-mapper trust-artifact tuples provide verifiable chain-of-custody (cross-ref OECD AI Principles) | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| People First — human-centric design, oversight, and empowerment for accountability and safety | ✅ Human-oversight delegation token + identity registry for named human controllers (cross-ref EU AI Act Art. 14, South Korea AI Basic Act Art. 34) | `hummbl_governance/delegation.py`, `hummbl_governance/identity.py` |
| Innovation over Restraint — prioritise responsible innovation over cautionary restraint | ⚪ Boundary: innovation-prioritisation policy stance is organisational, not software-addressable | |
| Fairness and Equity — design and test AI systems for fair, non-exclusionary, unbiased, non-discriminatory outcomes including for marginalised communities | ✅ Output-validator bias-detection gate + compliance-mapper fairness-assessment tuples (cross-ref NIST AI RMF MEASURE 2.11) | `hummbl_governance/output_validator.py`, `hummbl_governance/compliance_mapper.py` |
| Accountability — clear attribution of accountability for developers and deployers based on role and risk of harm | ✅ Identity registry + audit-log attribution tuples + delegation-token chain-of-responsibility (cross-ref EU AI Act Art. 26) | `hummbl_governance/identity.py`, `hummbl_governance/audit_log.py`, `hummbl_governance/delegation.py` |
| Understandable by Design — AI systems should be explainable and interpretable to the extent feasible | ✅ Reasoning-engine explanation tuples + compliance-mapper explainability-disclosure generator (cross-ref EU AI Act Art. 13) | `hummbl_governance/reasoning.py`, `hummbl_governance/compliance_mapper.py` |
| Safety, Resilience and Sustainability — minimise risk of harm, detect anomalies, provide early warnings, environmental responsibility | ✅ Kill-switch 4-mode halt + circuit-breaker fast-fail + health-probe anomaly detection + cost-governor resource enforcement (cross-ref NIST AI RMF MAP 1.6) | `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py`, `hummbl_governance/health_probe.py`, `hummbl_governance/cost_governor.py` |

### Risk mitigation obligations (Part 2, Pillar 4 — Risk Mitigation)

| Obligation | Coverage | Evidence |
|---|---|---|
| Identify and assess seven risk areas: malicious use, bias/discrimination, transparency failures, systemic risk, loss of control, national security threats, risk to vulnerable groups | ✅ STRIDE-mapper threat taxonomy + compliance-mapper risk-assessment tuples covering all seven risk categories (cross-ref NIST AI RMF MAP) | `hummbl_governance/stride_mapper.py`, `hummbl_governance/compliance_mapper.py` |
| Adopt voluntary frameworks — principles, standards, self-certifications, and audits alongside techno-legal solutions (privacy-preserving architectures, algorithmic auditing, watermarking, consent-based data-sharing) | ✅ Compliance-mapper voluntary-commitment tuples + output-validator watermarking/provenance labels + capability-fence privacy-preserving sandbox (cross-ref ISO/IEC 42001) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/output_validator.py`, `hummbl_governance/capability_fence.py` |
| Implement human-in-the-loop and system-level safeguards (audit trails, monitoring) for high-velocity AI use cases and loss-of-control risks, particularly in critical sectors | ✅ Delegation-token human-oversight gate + audit-log immutable trail + health-probe continuous monitoring + convergence-guard for autonomous loops (cross-ref EU AI Act Art. 14) | `hummbl_governance/delegation.py`, `hummbl_governance/audit_log.py`, `hummbl_governance/health_probe.py`, `hummbl_governance/convergence_guard.py` |
| Develop and apply India-specific AI risk assessment and classification framework for systems and applications | 🟡 Partial: compliance-mapper risk-classification tuples provide the substrate; India-specific taxonomy and thresholds are org-configured | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/stride_mapper.py` |

### Accountability and transparency (Part 2, Pillar 5 — Accountability)

| Obligation | Coverage | Evidence |
|---|---|---|
| Adopt graded liability framework proportionate to each stakeholder's role and level of risk, supported by transparency reports, self-certifications, internal policies, and techno-legal measures | ✅ Audit-log role-attribution tuples + compliance-mapper graded-liability matrix mapping function × risk × due-diligence (cross-ref South Korea AI Basic Act Art. 34) | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Publish transparency reports on AI systems (may be shared confidentially with regulators if sensitive) | 🟡 Partial: compliance-report generator produces publishable transparency reports; submission and publication are org tasks | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Establish accessible, multilingual grievance-redressal mechanisms with feedback loops for product improvement | 🟡 Partial: audit-log grievance tuples + feedback-loop capture; multilingual accessibility and public-facing portal are org tasks | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Transparency across the AI value chain — voluntary disclosures on underlying technology, interplay between actors, and flow of resources (data, compute) | ✅ Audit-log value-chain provenance tuples + compliance-mapper disclosure generator capturing data/compute/actor flows | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |

### Content authentication and data governance (Part 2, Pillar 3 — Policy & Regulation)

| Obligation | Coverage | Evidence |
|---|---|---|
| Implement content authentication and provenance techniques — watermarking, unique identifiers (C2PA-aligned), forensic tools, dataset provenance, model-attribution methods | ✅ Output-validator provenance-labeling tuple type + content-authenticity watermarking gate (cross-ref EU AI Act Art. 50, South Korea AI Basic Act Art. 31) | `hummbl_governance/output_validator.py`, `hummbl_governance/audit_log.py` |
| Counter deepfakes and AI-enabled disinformation through detection tools (anomaly detection, deepfake detection) and provenance verification | ✅ Output-validator deepfake-detection gate + health-probe anomaly detection + audit-log provenance chain (cross-ref EU AI Act Art. 50(2)) | `hummbl_governance/output_validator.py`, `hummbl_governance/health_probe.py` |
| Establish expert committee for content authentication and provenance standards (industry, government, academia, standard-setting bodies) | ⚪ Boundary: government-committee formation is organisational, not software-addressable | |

### Incident reporting and safety testing (Part 2, Pillars 4 & 6)

| Obligation | Coverage | Evidence |
|---|---|---|
| Contribute to national AI incidents database — structured, interoperable, confidential reporting without threat of penalties; leverage CERT-In for AI system vulnerabilities | ✅ Audit-log incident tuples + coordination-bus structured reporting + compliance-mapper incident-export format (cross-ref NIST AI RMF MEASURE 2.7) | `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py`, `hummbl_governance/compliance_mapper.py` |
| AISI safety testing — develop test suites, benchmarks, and evaluation metrics to support oversight and risk preparation | 🟡 Partial: compliance-mapper test-suite tuples + health-probe evaluation metrics provide substrate; AISI institutional test-suite development is org/government task | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/health_probe.py` |
| Encourage voluntary incident reporting with confidentiality protections and no-penalty design to identify harms, assess impact, and mitigate | ✅ Audit-log confidential-incident tuples with identity-redaction + compliance-mapper no-penalty-reporting workflow | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |

### Practical guidelines for industry (Part 4)

| Obligation | Coverage | Evidence |
|---|---|---|
| Comply with applicable Indian laws — IT Act 2000, DPDP Act 2023, Consumer Protection Act 2019, Copyright Act 1957, and sectoral regulations | ✅ Compliance-mapper crosswalk to Indian statutes + audit-log compliance-evidence tuples (cross-ref India DPDP Act coverage matrix) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Adopt voluntary compliance measures and maintain system documentation to facilitate oversight and audits by sectoral regulators or AISI | ✅ Audit-log documentation-retention tuples + compliance-mapper voluntary-commitment registry + evidence-export for audit | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Use techno-legal tools — privacy-preserving architectures, bias-mitigation technologies, and consent-based data-sharing models (DEPA for AI Training) | ✅ Capability-fence privacy-preserving sandbox + output-validator bias-mitigation gate + identity consent-record tuples (cross-ref India DPDP Act S.6–7) | `hummbl_governance/capability_fence.py`, `hummbl_governance/output_validator.py`, `hummbl_governance/identity.py` |
| Establish internal policies, self-certifications, committee hearings, and peer monitoring for accountability culture | 🟡 Partial: compliance-mapper self-certification tuples + audit-log policy-artifact storage; committee hearings and peer monitoring are org processes | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |

### Institutional architecture and action plan (Parts 2 & 3)

| Obligation | Coverage | Evidence |
|---|---|---|
| Establish AI Governance Group (AIGG) as inter-ministerial policy body, supported by Technology & Policy Expert Committee (TPEC) and AI Safety Institute (AISI) | ⚪ Boundary: government institutional design and inter-ministerial body formation are organisational, not software-addressable | |
| Launch regulatory sandboxes for supervised innovation and testing of AI systems | ⚪ Boundary: regulator-operated sandbox infrastructure is organisational, not software-addressable | |
| Phased action plan — short-term (AIGG/TPEC, risk frameworks, voluntary commitments), medium-term (standards, incident database, sandboxes, law amendments), long-term (monitoring, new laws, global standards, horizon scanning) | ⚪ Boundary: government policy process and legislative timeline are organisational, not software-addressable | |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| Guiding principles — Seven Sutras (Part 1) | 7 | 6 | 0 | 1 |
| Risk mitigation (Part 2, Pillar 4) | 4 | 3 | 1 | 0 |
| Accountability and transparency (Part 2, Pillar 5) | 4 | 2 | 2 | 0 |
| Content authentication and data governance (Part 2, Pillar 3) | 3 | 2 | 0 | 1 |
| Incident reporting and safety testing (Part 2, Pillars 4 & 6) | 3 | 2 | 1 | 0 |
| Practical guidelines for industry (Part 4) | 4 | 3 | 1 | 0 |
| Institutional architecture and action plan (Parts 2 & 3) | 3 | 0 | 0 | 3 |
| **Totals** | **28** | **18** | **5** | **5** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated. The India AI Governance Guidelines are principle-based and voluntary — not a binding statute — so coverage mapping reflects technical substrate alignment rather than statutory compliance.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Data protection overlaps India DPDP Act 2023 — see [`india-dpdp.md`](./india-dpdp.md)
- Transparency and labeling overlaps EU AI Act Art. 50 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Risk management overlaps NIST AI RMF — see [`nist-ai-rmf.md`](./nist-ai-rmf.md)
- Human oversight overlaps EU AI Act Art. 14 and South Korea AI Basic Act Art. 34 — see [`eu-ai-act.md`](./eu-ai-act.md), [`south-korea-ai-basic-act.md`](./south-korea-ai-basic-act.md)
- Content provenance overlaps South Korea AI Basic Act Art. 31 — see [`south-korea-ai-basic-act.md`](./south-korea-ai-basic-act.md)
- Voluntary compliance frameworks overlap ISO/IEC 42001 — see [`iso-42001.md`](./iso-42001.md)
- Seven sutras adapted from RBI FREE-AI Committee Report (13 Aug 2025) — finance-sector complementary framework
