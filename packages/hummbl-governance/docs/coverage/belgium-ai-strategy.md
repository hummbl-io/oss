# Belgium AI Strategy Coverage Matrix — HUMMBL

**Standard**: Belgium AI Strategy (Stratégie nationale en matière d'IA)
**Effective**: 2024
**Source**: https://www.digitalwallonia.be/en/ai-strategy
**Last reviewed**: 2026-06-26
**Reviewer**: devin (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not Belgian-licensed counsel and does not provide legal advice on the Belgian AI Strategy. The Strategy is a national policy framework. HUMMBL maps technical primitives to the Strategy's AI governance and deployment objectives.

## Scope summary

Belgium's AI Strategy covers 6 strategic areas: (1) AI governance and ethics, (2) AI in public services, (3) AI talent and education, (4) AI research and innovation, (5) AI infrastructure and data, and (6) AI adoption in industry. Belgium is subject to EU AI Act (cross-ref [`docs/coverage/eu-ai-act.md`](./eu-ai-act.md)) and GDPR (cross-ref [`docs/coverage/gdpr.md`](./gdpr.md)).

## Obligations + coverage

### AI governance and ethics (Area 1)

| Obligation | Coverage | Evidence |
|---|---|---|
| Establish AI governance framework for public-sector AI systems | ✅ Compliance-mapper encodes governance obligations + doctrine-engine enforces governance doctrine (cross-ref NIST AI RMF GOVERN) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/kernel/doctrine_engine.py` |
| Apply AI ethics principles aligned with EU AI Act and UNESCO | ✅ Compliance-mapper encodes ethical-principle tuples + doctrine-engine enforces principle doctrine (cross-ref [`docs/coverage/eu-ai-act.md`](./eu-ai-act.md), [`docs/coverage/unesco-ai-ethics.md`](./unesco-ai-ethics.md)) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/kernel/doctrine_engine.py` |
| Establish AI impact assessment for high-risk AI systems | ✅ Impact-assessment template with risk-tier classification (cross-ref EU AI Act Art. 27, NIST AI RMF) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Ensure AI systems do not violate fundamental rights | ✅ Output-validation gate for fairness/bias + human-oversight delegation token + immutable audit trail | `hummbl_governance/output_validator.py`, `hummbl_governance/delegation.py`, `hummbl_governance/audit_log.py` |

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

### AI infrastructure, data, and adoption (Areas 5, 6)

| Obligation | Coverage | Evidence |
|---|---|---|
| Develop AI computing infrastructure and data centres | ⚪ Boundary: national computing infrastructure provisioning is governmental | |
| Establish data governance framework for AI with quality and interoperability | ✅ Data-governance tuples + schema-validator enforce data quality and interoperability constraints (cross-ref GDPR) | `hummbl_governance/schema_validator.py`, `hummbl_governance/compliance_mapper.py` |
| Ensure data protection and privacy in AI systems | ✅ Privacy-by-design enforcement + data-minimization tuple + immutable audit trail (cross-ref [`docs/coverage/gdpr.md`](./gdpr.md)) | `hummbl_governance/audit_log.py`, `hummbl_governance/output_validator.py` |
| Promote AI adoption in Belgian industry through digital transformation | 🟡 Partial: compliance-mapper generates industry AI adoption documentation and governance templates; adoption program delivery is organizational | `hummbl_governance/compliance_mapper.py` |
| Monitor and evaluate AI strategy implementation against KPIs | ✅ Compliance-mapper + audit-log + health-probe produce M&E evidence tuples and readiness signals | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py`, `hummbl_governance/health_probe.py` |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| AI governance & ethics | 4 | 4 | 0 | 0 |
| AI in public services | 3 | 3 | 0 | 0 |
| AI talent, education & research | 3 | 0 | 2 | 1 |
| AI infrastructure, data & adoption | 5 | 3 | 1 | 1 |
| **Totals** | **15** | **10** | **3** | **2** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- EU AI Act: [`docs/coverage/eu-ai-act.md`](./eu-ai-act.md)
- GDPR: [`docs/coverage/gdpr.md`](./gdpr.md)
- UNESCO AI Ethics: [`docs/coverage/unesco-ai-ethics.md`](./unesco-ai-ethics.md)
- NIST AI RMF: [`docs/coverage/nist-ai-rmf.md`](./nist-ai-rmf.md)
