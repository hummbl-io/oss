# Rwanda National AI Policy Coverage Matrix — HUMMBL

**Standard**: National Artificial Intelligence Policy of the Republic of Rwanda (Cabinet-approved 20 April 2023)
**Effective**: April 20, 2023
**Source**: https://www.minict.gov.rw/fileadmin/templates/Policies_and_Strategies/National_AI_Policy.pdf
**Last reviewed**: 2026-06-25
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not Rwandan legal counsel and does not provide legal advice on the National AI Policy. The Policy is a national-strategy document rather than binding legislation; it operates within Rwanda's broader legal framework including the Data Protection and Privacy Law (Law No. 058/2021 of 13/10/2021) and sector regulations enforced by RURA. Statutory compliance is the customer-organization responsibility. HUMMBL maps technical primitives to the Policy's 14 key recommendations across six priority areas (enablers, accelerators, safeguard) and to the governance/monitoring obligations of the Responsible AI Office.

## Scope summary

The Policy applies to all AI development and deployment across Rwanda's public and private sectors, with priority sectors including healthcare, agriculture, education, banking & digital payments, e-commerce & trade, and public services. It is organized around six priority areas: three enablers (21st Century Skills & AI Literacy; Reliable Infrastructure & Compute Capacity; Robust Data Strategy), two accelerators (Trustworthy AI Adoption in the Public Sector; Widely-beneficial AI Adoption in the Private Sector), and one safeguard (Practical Ethical Guidelines). Implementation is coordinated by the Responsible AI Office (RAI Office) within MINICT, with RURA as technical regulator for ethical AI guidelines and the National Cyber Security Authority (NCSA) overseeing data-protection compliance. The Policy targets USD 76.5M over 2023–2028 and a top-50 position in the Government AI Readiness Index.

## Obligations + coverage

### Enabler 1 — 21st Century Skills & AI Literacy (Recs 1–4)

| Obligation | Coverage | Evidence |
|---|---|---|
| Commit to reskilling the workforce with 21st Century AI and data skills (National Skills Building Program) | ⚪ Boundary: national workforce-reskilling programs are organizational/educational, not software-addressable | |
| Set foundations for world-class AI university education and applied research | ⚪ Boundary: academic curriculum and research-institution design is organizational | |
| Adapt education so young learners are empowered with globally competitive STEM skills | ⚪ Boundary: primary/secondary curriculum reform is organizational | |
| Streamline exchange of students and professionals between Rwanda and foreign countries | ⚪ Boundary: bilateral mobility agreements are organizational/diplomatic | |

### Enabler 2 — Reliable Infrastructure & Compute Capacity (Recs 5–6)

| Obligation | Coverage | Evidence |
|---|---|---|
| Ensure access to affordable, reliable, and secure high-performance storage and compute capacity | 🟡 Partial: cost-governor enforces compute-budget limits and health-probe monitors resource availability; physical data-center provisioning is org task | `hummbl_governance/cost_governor.py`, `hummbl_governance/health_probe.py` |
| Position Rwanda as a host for cloud infrastructure with AI-ready storage and compute serving the region | ⚪ Boundary: national cloud-infrastructure hosting strategy is organizational/commercial | |

### Enabler 3 — Robust Data Strategy (Rec 7)

| Obligation | Coverage | Evidence |
|---|---|---|
| Create pathways to greater availability and accessibility of AI-ready data (open, secure, trusted data ecosystem) | 🟡 Partial: schema-validator enforces data-contract schemas and audit-log records data-access provenance; national data-sharing policy is org task | `hummbl_governance/schema_validator.py`, `hummbl_governance/audit_log.py` |
| Ensure personal-data processing complies with Data Protection & Privacy Law (Law No. 058/2021) principles (lawfulness, fairness, transparency, purpose limitation, accuracy) | ✅ Identity-registry + audit-log + compliance-mapper encode lawful-basis, purpose-limitation, and accuracy tuples (cross-ref GDPR, Rwanda Law 058/2021) | `hummbl_governance/identity.py`, `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |

### Accelerator 1 — Trustworthy AI Adoption in the Public Sector (Recs 8, 9, 10)

| Obligation | Coverage | Evidence |
|---|---|---|
| Strengthen AI policy and regulation and ensure public trust in AI | 🟡 Partial: compliance-mapper encodes regulatory obligations and produces trust-evidence artifacts; national regulatory drafting is org task | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Collaborate in measuring international AI development and Rwanda's global competitiveness | 🟡 Partial: compliance-mapper generates metrics and evidence reports for international benchmarking submissions; index participation and diplomatic engagement remain institutional | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Improve public service delivery using AI (efficiency, performance, citizen services) | 🟡 Partial: lifecycle + coordination-bus orchestrate governed AI service delivery; sector deployment and citizen-facing integration is org task | `hummbl_governance/lifecycle.py`, `hummbl_governance/coordination_bus.py` |
| Establish a risk-sharing fund to support R&D in the public sector | ⚪ Boundary: public-sector R&D fund design is governmental/fiscal | |

### Accelerator 2 — Widely-beneficial AI Adoption in the Private Sector (Recs 11, 12)

| Obligation | Coverage | Evidence |
|---|---|---|
| Support private sector adoption and prioritization of AI to drive robust national investment | ⚪ Boundary: national investment-incentive policy is governmental/fiscal | |
| Boost Rwanda's emerging AI ecosystem (startups, incubation, seed investment fund) | ⚪ Boundary: startup-ecosystem and venture-fund design is organizational/commercial | |
| Ensure private-sector AI deployments remain safe and controllable in production | ✅ Kill-switch 4-mode halt + circuit-breaker fast-fail + capability-fence enforce safe production boundaries | `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py`, `hummbl_governance/capability_fence.py` |

### Safeguard — Practical Ethical Guidelines (Recs 13, 14)

| Obligation | Coverage | Evidence |
|---|---|---|
| Operationalize and share Rwanda's "Guidelines on the Ethical Development and Implementation of AI" (RURA) across the AI system lifecycle | ✅ Compliance-mapper encodes ethical-guideline obligations as assessable tuples + lifecycle gates enforcement at each lifecycle stage (cross-ref UNESCO Recommendation on the Ethics of AI) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/lifecycle.py` |
| Apply beneficence, non-maleficence, autonomy, justice, and explicability principles in all AI development | ✅ Reasoning-engine + output-validator enforce non-maleficence and explicability gates; doctrine-engine encodes principle doctrine (cross-ref EU AI Act Art. 13, UNESCO Ethics of AI) | `hummbl_governance/reasoning.py`, `hummbl_governance/output_validator.py`, `hummbl_governance/kernel/doctrine_engine.py` |
| Add "AI Ethics" functions to the mandates/responsibilities of regulators of AI-relevant sectors | 🟡 Partial: delegation tokens + authority-engine encode role mandates and ethics responsibilities; sectoral regulatory assignment is org task | `hummbl_governance/delegation.py`, `hummbl_governance/kernel/authority_engine.py` |
| Organize a forum of regulators of AI-relevant sectors to develop sector-specific AI ethics guidelines aligned with the general guidelines | 🟡 Partial: compliance-mapper generates sector-specific ethics guideline templates and cross-sector mapping; inter-regulator convening remains institutional | `hummbl_governance/compliance_mapper.py` |
| Actively contribute to shaping responsible AI principles & practices in international platforms (OECD, GPAI, ITU, UNESCO) | ⚪ Boundary: international-platform representation is organizational/diplomatic | |

### Governance, Institutional Framework & Monitoring (RAI Office, RURA, NCSA)

| Obligation | Coverage | Evidence |
|---|---|---|
| Establish and operationalize the Responsible AI Office (RAI Office) within MINICT to coordinate implementation across institutions | ⚪ Boundary: government-office establishment is organizational | |
| Coordinate multi-stakeholder actors (government, private sector, academia, civil society) across the AI ecosystem | 🟡 Partial: coordination-bus + contract-net enable multi-agent coordination and contracting; stakeholder convening is org task | `hummbl_governance/coordination_bus.py`, `hummbl_governance/contract_net.py` |
| Monitor and evaluate policy implementation against defined indicators and benchmarks | ✅ Compliance-mapper + audit-log + health-probe produce M&E evidence tuples and readiness signals | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py`, `hummbl_governance/health_probe.py` |
| RURA monitors compliance with ethical AI guidelines through audits and stakeholder feedback | ✅ Audit-log immutable trail + compliance-mapper audit-template + stride-mapper threat audit support regulatory audit (cross-ref NIST AI RMF, ISO 42001) | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py`, `hummbl_governance/stride_mapper.py` |
| Prepare annual progress reports for Cabinet review and public dissemination | 🟡 Partial: compliance-report generator produces the report; Cabinet submission and publication is org task | `hummbl_governance/compliance_mapper.py` |
| Hold an annual participatory consultation forum to update the Policy and guidelines | 🟡 Partial: compliance-mapper generates policy-review documentation and evidence summaries for consultation inputs; national convening remains institutional | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Enforce data-protection compliance via NCSA under Law No. 058/2021 (administrative fines, criminal liability) | 🟡 Partial: audit-log immutable evidence trail + compliance-mapper Law 058/2021 mapping produce enforcement-ready evidence artifacts; statutory penalty assessment and criminal liability are governmental/legal tasks | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Maintain human oversight and named accountability for AI systems in regulated sectors | ✅ Human-oversight delegation token + identity-registry + contact-registration tuple (cross-ref EU AI Act Art. 14, South Korea AI Basic Act Art. 34) | `hummbl_governance/delegation.py`, `hummbl_governance/identity.py` |
| Establish AI-specific liability frameworks through future legislation | ⚪ Boundary: legislative drafting is governmental | |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| Enabler 1 — Skills & AI Literacy (Recs 1–4) | 4 | 0 | 0 | 4 |
| Enabler 2 — Infrastructure & Compute (Recs 5–6) | 2 | 0 | 1 | 1 |
| Enabler 3 — Data Strategy (Rec 7) | 2 | 1 | 1 | 0 |
| Accelerator 1 — Public Sector AI (Recs 8–10) | 4 | 0 | 2 | 2 |
| Accelerator 2 — Private Sector AI (Recs 11–12) | 3 | 1 | 0 | 2 |
| Safeguard — Ethical Guidelines (Recs 13–14) | 5 | 2 | 1 | 2 |
| Governance & Monitoring (RAI Office, RURA, NCSA) | 9 | 3 | 3 | 3 |
| **Totals** | **29** | **7** | **8** | **14** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Ethical guidelines overlap UNESCO Recommendation on the Ethics of AI — see [`unesco-ethics-ai.md`](./unesco-ethics-ai.md) (if present)
- Data protection overlaps Rwanda Law No. 058/2021 and GDPR — see [`gdpr.md`](./gdpr.md)
- Human oversight overlaps EU AI Act Art. 14 and South Korea AI Basic Act Art. 34 — see [`eu-ai-act.md`](./eu-ai-act.md), [`south-korea-ai-basic-act.md`](./south-korea-ai-basic-act.md)
- Risk management and audit overlap NIST AI RMF and ISO 42001 — see [`nist-ai-rmf.md`](./nist-ai-rmf.md), [`iso-42001.md`](./iso-42001.md)
- Output validation and transparency overlap EU AI Act Art. 50 — see [`eu-ai-act.md`](./eu-ai-act.md)
