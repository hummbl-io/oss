# South Africa AI Policy Framework Coverage Matrix — HUMMBL

**Standard**: South Africa National AI Policy Framework (Draft)
**Effective**: 2024 (draft for public consultation)
**Source**: https://www.gov.za/sites/default/files/gcis_document/202404/national-ai-policy-framework.pdf
**Last reviewed**: 2026-06-26
**Reviewer**: devin (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not South African-licensed counsel and does not provide legal advice on the South African AI Policy Framework. The Framework is a draft policy document. HUMMBL maps technical primitives to the Framework's AI governance and deployment objectives.

## Scope summary

South Africa's AI Policy Framework covers 7 pillars: (1) AI governance and regulation, (2) AI ethics and human rights, (3) AI in public services, (4) AI talent and skills, (5) AI research and innovation, (6) AI infrastructure and data, and (7) AI for inclusive growth. South Africa is also subject to POPIA (Protection of Personal Information Act).

## Obligations + coverage

### AI governance and regulation (Pillar 1)

| Obligation | Coverage | Evidence |
|---|---|---|
| Establish AI governance framework for public-sector AI systems | ✅ Compliance-mapper encodes governance obligations + doctrine-engine enforces governance doctrine (cross-ref NIST AI RMF GOVERN) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/kernel/doctrine_engine.py` |
| Develop AI legal and regulatory framework | 🟡 Partial: compliance-mapper maps legal requirements and generates framework documentation; legislative drafting is governmental | `hummbl_governance/compliance_mapper.py` |
| Establish AI impact assessment for government AI deployments | ✅ Impact-assessment template with risk-tier classification (cross-ref EU AI Act Art. 27, NIST AI RMF) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |

### AI ethics and human rights (Pillar 2)

| Obligation | Coverage | Evidence |
|---|---|---|
| Apply AI ethics principles — fairness, transparency, accountability, privacy, human oversight | ✅ Output-validation gate for fairness/bias + immutable audit-log for accountability + human-oversight delegation token (cross-ref UNESCO Ethics of AI, [`docs/coverage/african-union-ai-strategy.md`](./african-union-ai-strategy.md)) | `hummbl_governance/output_validator.py`, `hummbl_governance/audit_log.py`, `hummbl_governance/delegation.py` |
| Ensure AI systems do not violate human rights and fundamental freedoms | ✅ Output-validation gate for fairness/bias + human-oversight delegation token + immutable audit trail | `hummbl_governance/output_validator.py`, `hummbl_governance/delegation.py`, `hummbl_governance/audit_log.py` |
| Ensure data protection and privacy in AI systems (POPIA compliance) | ✅ Privacy-by-design enforcement + data-minimization tuple + immutable audit trail | `hummbl_governance/audit_log.py`, `hummbl_governance/output_validator.py` |

### AI in public services (Pillar 3)

| Obligation | Coverage | Evidence |
|---|---|---|
| Deploy AI in public administration for citizen service improvement | ✅ Lifecycle + coordination-bus orchestrate governed AI service delivery with audit trail (cross-ref EU AI Act Art. 60) | `hummbl_governance/lifecycle.py`, `hummbl_governance/coordination_bus.py` |
| Ensure transparency and explainability of AI in government services | ✅ Transparency-notification primitive + output-validator explainability gate (cross-ref EU AI Act Art. 50, 13) | `hummbl_governance/audit_log.py`, `hummbl_governance/output_validator.py` |
| Maintain human oversight and accountability for AI in public services | ✅ Human-oversight delegation token + identity-registry role assignment (cross-ref EU AI Act Art. 14) | `hummbl_governance/delegation.py`, `hummbl_governance/identity.py` |

### AI talent, skills, and research (Pillars 4, 5)

| Obligation | Coverage | Evidence |
|---|---|---|
| Develop AI talent through education and training programs | 🟡 Partial: compliance-mapper generates AI literacy training materials and documentation; curriculum delivery is organizational | `hummbl_governance/compliance_mapper.py` |
| Promote AI literacy and digital skills across the population | 🟡 Partial: compliance-mapper generates AI literacy training materials and documentation; campaign delivery is organizational | `hummbl_governance/compliance_mapper.py` |
| Support AI research in universities and research institutions | ⚪ Boundary: research-institution funding and academic R&D programs are governmental | |

### AI infrastructure, data, and inclusive growth (Pillars 6, 7)

| Obligation | Coverage | Evidence |
|---|---|---|
| Develop AI computing infrastructure and data centres | ⚪ Boundary: national computing infrastructure provisioning is governmental | |
| Establish data governance framework for AI with quality and interoperability | ✅ Data-governance tuples + schema-validator enforce data quality and interoperability constraints | `hummbl_governance/schema_validator.py`, `hummbl_governance/compliance_mapper.py` |
| Promote AI for inclusive growth and reducing inequality | 🟡 Partial: compliance-mapper generates inclusive-growth AI documentation and bias-mitigation evidence; social policy is governmental | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/output_validator.py` |
| Monitor and evaluate AI policy implementation against KPIs | ✅ Compliance-mapper + audit-log + health-probe produce M&E evidence tuples and readiness signals | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py`, `hummbl_governance/health_probe.py` |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| AI governance & regulation | 3 | 2 | 1 | 0 |
| AI ethics & human rights | 3 | 3 | 0 | 0 |
| AI in public services | 3 | 3 | 0 | 0 |
| AI talent, skills & research | 3 | 0 | 2 | 1 |
| AI infrastructure, data & inclusive growth | 4 | 2 | 1 | 1 |
| **Totals** | **16** | **10** | **4** | **2** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- African Union AI Strategy: [`docs/coverage/african-union-ai-strategy.md`](./african-union-ai-strategy.md)
- UNESCO AI Ethics: [`docs/coverage/unesco-ai-ethics.md`](./unesco-ai-ethics.md)
- NIST AI RMF: [`docs/coverage/nist-ai-rmf.md`](./nist-ai-rmf.md)
