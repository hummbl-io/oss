# Argentina AI Plan Coverage Matrix — HUMMBL

**Standard**: Argentina National AI Plan (Plan Nacional de Inteligencia Artificial)
**Effective**: 2024
**Source**: https://www.argentina.gob.ar/ciencia/tecnologia-e-innovacion/inteligencia-artificial
**Last reviewed**: 2026-06-26
**Reviewer**: devin (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not Argentine-licensed counsel and does not provide legal advice on the Argentine AI Plan. The Plan is a national policy framework. HUMMBL maps technical primitives to the Plan's AI governance and deployment objectives.

## Scope summary

Argentina's National AI Plan covers 6 strategic areas: (1) AI governance and ethics, (2) AI in public services, (3) AI talent and education, (4) AI research and innovation, (5) AI infrastructure and data, and (6) AI for social inclusion. Argentina is subject to Latin American AI frameworks and UNESCO AI Ethics (cross-ref [`docs/coverage/unesco-ai-ethics.md`](./unesco-ai-ethics.md)).

## Obligations + coverage

### AI governance and ethics (Area 1)

| Obligation | Coverage | Evidence |
|---|---|---|
| Establish AI governance framework for public-sector AI systems | ✅ Compliance-mapper encodes governance obligations + doctrine-engine enforces governance doctrine (cross-ref NIST AI RMF GOVERN) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/kernel/doctrine_engine.py` |
| Apply AI ethics principles — fairness, transparency, accountability, privacy | ✅ Output-validation gate for fairness/bias + immutable audit-log for accountability + privacy-by-design enforcement (cross-ref UNESCO Ethics of AI) | `hummbl_governance/output_validator.py`, `hummbl_governance/audit_log.py` |
| Establish AI impact assessment for government AI deployments | ✅ Impact-assessment template with risk-tier classification (cross-ref EU AI Act Art. 27, NIST AI RMF) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Develop AI legal and regulatory framework | 🟡 Partial: compliance-mapper maps legal requirements and generates framework documentation; legislative drafting is governmental | `hummbl_governance/compliance_mapper.py` |

### AI in public services (Area 2)

| Obligation | Coverage | Evidence |
|---|---|---|
| Deploy AI in public administration for citizen service improvement | ✅ Lifecycle + coordination-bus orchestrate governed AI service delivery with audit trail (cross-ref EU AI Act Art. 60) | `hummbl_governance/lifecycle.py`, `hummbl_governance/coordination_bus.py` |
| Ensure transparency and explainability of AI in government services | ✅ Transparency-notification primitive + output-validator explainability gate (cross-ref EU AI Act Art. 50, 13) | `hummbl_governance/audit_log.py`, `hummbl_governance/output_validator.py` |
| Maintain human oversight and accountability for AI in public services | ✅ Human-oversight delegation token + identity-registry role assignment (cross-ref EU AI Act Art. 14) | `hummbl_governance/delegation.py`, `hummbl_governance/identity.py` |

### AI talent, education, and research (Areas 3, 4)

| Obligation | Coverage | Evidence |
|---|---|---|
| Develop AI talent through education and training programs | 🟡 Partial: compliance-mapper generates AI literacy training materials and documentation; curriculum delivery is organizational | `hummbl_governance/compliance_mapper.py` |
| Promote AI literacy and digital skills across the population | 🟡 Partial: compliance-mapper generates AI literacy training materials and documentation; campaign delivery is organizational | `hummbl_governance/compliance_mapper.py` |
| Support AI research in universities and research institutions | ⚪ Boundary: research-institution funding and academic R&D programs are governmental | |

### AI infrastructure, data, and social inclusion (Areas 5, 6)

| Obligation | Coverage | Evidence |
|---|---|---|
| Develop AI computing infrastructure and data centres | ⚪ Boundary: national computing infrastructure provisioning is governmental | |
| Establish data governance framework for AI with quality and interoperability | ✅ Data-governance tuples + schema-validator enforce data quality and interoperability constraints | `hummbl_governance/schema_validator.py`, `hummbl_governance/compliance_mapper.py` |
| Ensure data protection and privacy in AI systems | ✅ Privacy-by-design enforcement + data-minimization tuple + immutable audit trail | `hummbl_governance/audit_log.py`, `hummbl_governance/output_validator.py` |
| Promote AI for social inclusion and reducing inequality | 🟡 Partial: compliance-mapper generates inclusive-growth AI documentation and bias-mitigation evidence; social policy is governmental | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/output_validator.py` |
| Monitor and evaluate AI plan implementation against KPIs | ✅ Compliance-mapper + audit-log + health-probe produce M&E evidence tuples and readiness signals | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py`, `hummbl_governance/health_probe.py` |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| AI governance & ethics | 4 | 3 | 1 | 0 |
| AI in public services | 3 | 3 | 0 | 0 |
| AI talent, education & research | 3 | 0 | 2 | 1 |
| AI infrastructure, data & social inclusion | 5 | 3 | 1 | 1 |
| **Totals** | **15** | **9** | **4** | **2** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- UNESCO AI Ethics: [`docs/coverage/unesco-ai-ethics.md`](./unesco-ai-ethics.md)
- NIST AI RMF: [`docs/coverage/nist-ai-rmf.md`](./nist-ai-rmf.md)
