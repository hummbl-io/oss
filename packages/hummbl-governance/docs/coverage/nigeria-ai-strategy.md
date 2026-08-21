# Nigeria National AI Strategy Coverage Matrix — HUMMBL

**Standard**: National Artificial Intelligence Strategy (NAIS) — Draft, August 2024
**Effective**: August 2, 2024 (draft publication; under deliberation)
**Source**: https://ncair.nitda.gov.ng/wp-content/uploads/2024/08/National-AI-Strategy_01082024-copy.pdf
**Last reviewed**: 2026-06-25
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not Nigerian legal counsel and does not provide legal advice on the NAIS. The NAIS is a draft national strategy (policy roadmap), not an enforceable statute. It sets out five strategic pillars and proposes institutional arrangements, risk classifications, and ethical principles. Statutory compliance — including alignment with the Nigeria Data Protection Act 2023 and sectoral regulations — is the customer-organization responsibility. HUMMBL maps technical primitives to the strategy's responsible-AI, governance, risk-management, data-governance, and oversight objectives. Where objectives concern physical infrastructure, talent programs, fiscal incentives, or governmental institution-building, HUMMBL marks them as boundary (out of scope).

## Scope summary

The NAIS applies as a national policy framework for AI development, adoption, and governance in Nigeria. It was co-created through a multi-stakeholder process led by the Federal Ministry of Communications, Innovation & Digital Economy (FMCIDE) and NITDA/NCAIR. The strategy identifies five strategic pillars: (1) Building Foundational AI Infrastructure, (2) Building and Sustaining a World-class AI Ecosystem, (3) Accelerating AI Adoption and Sector Transformation, (4) Ensuring Responsible and Ethical AI Development and Deployment, and (5) Developing a Robust AI Governance Framework. It proposes a risk-based classification of AI systems with compliance tiers ranging from voluntary guidance and sandboxes to mandatory audits for high-risk systems, and identifies four AI risk categories: economic, ethical, societal, and AI model risks.

## Obligations + coverage

### Foundational AI Infrastructure (Pillar 1)

| Obligation | Coverage | Evidence |
|---|---|---|
| Deploy national HPC resources with affordable access for researchers, startups, and businesses | ⚪ Boundary: physical compute-infrastructure provisioning is organizational, not software-addressable | |
| Set up clean energy AI clusters with <50% dependence on national grid power | ⚪ Boundary: energy-infrastructure engineering is organizational | |
| Establish open data platforms for AI research with standardized data access | 🟡 Partial: schema validation enforces data-quality constraints; platform hosting and open-access provisioning are org tasks | `hummbl_governance/schema_validator.py`, `hummbl_governance/audit_log.py` |

### AI Ecosystem & Talent Development (Pillar 2)

| Obligation | Coverage | Evidence |
|---|---|---|
| Establish centres of excellence and national AI fellowship programs | ⚪ Boundary: institutional formation and talent programs are organizational | |
| National AI R&D Fund, startup incentives, and diaspora engagement | ⚪ Boundary: fiscal-incentive design and funding allocation are governmental | |

### Responsible & Ethical AI Development (Pillar 4)

| Obligation | Coverage | Evidence |
|---|---|---|
| Establish comprehensive ethical principles (fairness, transparency, accountability, privacy, human well-being) | ✅ Compliance-mapper principle-encoding with fairness, transparency, accountability, privacy, and well-being dimensions (cross-ref UNESCO AI Ethics, OECD AI Principles) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Constitute AI Ethics Expert Group (AIEEG) for independent ethical oversight | ⚪ Boundary: institutional body formation and independence guarantees are organizational | |
| Standardized assessment tool ensuring AI projects align with ethical principles | ✅ Impact-assessment template with ethical-alignment scoring (cross-ref NIST AI RMF MAP, EU AI Act Art. 27) | `hummbl_governance/compliance_mapper.py` |
| Bias mitigation across training data, algorithms, and protected characteristics | ✅ Output-validation gate + schema validation for bias detection in outputs and data schemas | `hummbl_governance/output_validator.py`, `hummbl_governance/schema_validator.py` |
| Mandatory documentation: model cards and dataset data sheets | ✅ Documentation-retention tuples + model-card and data-sheet tuple types in audit log | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Algorithmic impact assessments for high-risk AI systems | ✅ Impact-assessment template with risk-classification component (cross-ref EU AI Act Art. 27 FRIA, South Korea Art. 35) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Standards for explainability and consent in AI systems | ✅ Reasoning-engine explanation generation + identity-based consent tracking (cross-ref EU AI Act Art. 13) | `hummbl_governance/reasoning.py`, `hummbl_governance/identity.py` |
| Risk assessment across accuracy, bias, transparency, and governance factors | ✅ Risk-identification + assessment + treatment tuple types covering accuracy, bias, transparency, governance dimensions | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |

### AI Governance & Risk Management (Pillar 5)

| Obligation | Coverage | Evidence |
|---|---|---|
| Publish comprehensive National AI Principles (transparent, publicly available) | 🟡 Partial: compliance-mapper encodes and structures principles; public publication is org task | `hummbl_governance/compliance_mapper.py` |
| Establish AI Governance Regulatory Body with enforcement authority | ⚪ Boundary: regulatory-body formation and legal mandate are governmental | |
| Risk-based classification of AI systems with compliance tiers (voluntary guidance → sandboxes → mandatory audits for high-risk) | ✅ Classification-tuple type with tiered compliance levels + compliance-mapper tier assignment | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Comprehensive risk management framework minimizing negative AI impacts | ✅ Risk-mgmt program substrate: INTENT + risk-identification + risk-treatment tuples (cross-ref NIST AI RMF, EU AI Act Art. 9) | `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py` |
| Incident reporting and redress mechanisms (appeals, independent review) | ✅ Adverse-event tuples + incident-report generation + audit-log export for review (cross-ref EU AI Act Art. 73) | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Human oversight and intervention in AI systems | ✅ Human-oversight delegation token + contact-registration tuple (cross-ref EU AI Act Art. 14, South Korea Art. 34) | `hummbl_governance/delegation.py`, `hummbl_governance/identity.py` |
| Ongoing monitoring, testing, and validation of AI systems | ✅ Health-probe monitoring + lifecycle management + schema validation for continuous assurance | `hummbl_governance/health_probe.py`, `hummbl_governance/lifecycle.py`, `hummbl_governance/schema_validator.py` |

### Data Governance & Protection (Cross-cutting)

| Obligation | Coverage | Evidence |
|---|---|---|
| Data governance standards adhering to Nigeria Data Protection Act (NDPA) | ✅ Audit-log data-governance tuples + compliance-mapper NDPA-aligned controls (cross-ref NDPA 2023, GDPR) | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Privacy and data protection impact assessments for AI systems | ✅ Impact-assessment template with privacy and data-protection component (cross-ref GDPR DPIA, NDPA 2023) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Consent management for data use in AI training and deployment | ✅ Identity-based consent tracking + audit-log consent-record tuples | `hummbl_governance/identity.py`, `hummbl_governance/audit_log.py` |

### Sectoral Adoption & Enforcement (Pillars 3 & 5)

| Obligation | Coverage | Evidence |
|---|---|---|
| Sector-specific AI adoption roadmaps (healthcare, agriculture, finance, education, public services) | ⚪ Boundary: sectoral policy-roadmap development is governmental | |
| Global data quality standards for sectoral AI applications | ✅ Schema validation enforcing data-quality constraints + compliance-mapper sectoral control mapping | `hummbl_governance/schema_validator.py`, `hummbl_governance/compliance_mapper.py` |
| Suspension of service and remediation orders for non-compliant AI systems | ✅ Kill-switch 4-mode halt + circuit-breaker fast-fail for service suspension (cross-ref South Korea Art. 40 corrective orders) | `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py` |
| Administrative fines and public naming of non-compliant entities | ⚪ Boundary: penalty regime and regulatory publication are governmental | |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| Foundational AI Infrastructure (Pillar 1) | 3 | 0 | 1 | 2 |
| AI Ecosystem & Talent (Pillar 2) | 2 | 0 | 0 | 2 |
| Responsible & Ethical AI (Pillar 4) | 8 | 7 | 0 | 1 |
| AI Governance & Risk Management (Pillar 5) | 7 | 5 | 1 | 1 |
| Data Governance & Protection (Cross-cutting) | 3 | 3 | 0 | 0 |
| Sectoral Adoption & Enforcement (Pillars 3 & 5) | 4 | 2 | 0 | 2 |
| **Totals** | **27** | **17** | **3** | **7** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Ethical principles overlap UNESCO AI Ethics — see [`unesco-ai-ethics.md`](./unesco-ai-ethics.md)
- Ethical principles overlap OECD AI Principles — see [`oecd-ai-principles.md`](./oecd-ai-principles.md)
- Risk management overlaps NIST AI RMF — see [`nist-ai-rmf.md`](./nist-ai-rmf.md)
- Risk management and impact assessment overlap EU AI Act Art. 9, Art. 27 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Human oversight overlaps EU AI Act Art. 14 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Data governance overlaps Nigeria Data Protection Act / GDPR — see [`gdpr.md`](./gdpr.md)
- Corrective-order enforcement overlaps South Korea AI Basic Act Art. 40 — see [`south-korea-ai-basic-act.md`](./south-korea-ai-basic-act.md)
