# Estonia AI Strategy (Kratt) Coverage Matrix — HUMMBL

**Standard**: Estonia's National AI Strategy (Kratt Strategy)
**Effective**: 2019–2021 (extended through 2025)
**Source**: https://www.mkm.ee/en/national-artificial-intelligence-strategy-estonia-kratt
**Last reviewed**: 2026-06-26
**Reviewer**: devin (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not Estonian-licensed counsel and does not provide legal advice on the Estonian AI Strategy. The Strategy is a national policy framework. HUMMBL maps technical primitives to the Strategy's AI governance and deployment objectives.

## Scope summary

Estonia's AI Strategy (Kratt) focuses on 8 action areas: (1) public-sector AI deployment, (2) AI in healthcare, (3) AI in agriculture, (4) AI in industry, (5) AI talent, (6) data governance, (7) AI ethics and regulation, and (8) international cooperation. Estonia is subject to EU AI Act (cross-ref [`docs/coverage/eu-ai-act.md`](./eu-ai-act.md)) and GDPR (cross-ref [`docs/coverage/gdpr.md`](./gdpr.md)).

## Obligations + coverage

### Public-sector AI deployment (Action 1)

| Obligation | Coverage | Evidence |
|---|---|---|
| Deploy AI in public administration for citizen service improvement | ✅ Lifecycle + coordination-bus orchestrate governed AI service delivery with audit trail (cross-ref EU AI Act Art. 60) | `hummbl_governance/lifecycle.py`, `hummbl_governance/coordination_bus.py` |
| Ensure transparency and explainability of AI in government services | ✅ Transparency-notification primitive + output-validator explainability gate (cross-ref EU AI Act Art. 50, 13) | `hummbl_governance/audit_log.py`, `hummbl_governance/output_validator.py` |
| Establish AI governance framework for public-sector AI systems | ✅ Compliance-mapper encodes governance obligations + doctrine-engine enforces governance doctrine (cross-ref NIST AI RMF GOVERN) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/kernel/doctrine_engine.py` |
| Maintain human oversight and accountability for AI in public services | ✅ Human-oversight delegation token + identity-registry role assignment (cross-ref EU AI Act Art. 14) | `hummbl_governance/delegation.py`, `hummbl_governance/identity.py` |

### Sectoral AI deployment (Actions 2–4)

| Obligation | Coverage | Evidence |
|---|---|---|
| Deploy AI in healthcare with safety, privacy, and human oversight | ✅ Kill-switch 4-mode halt + circuit-breaker fast-fail + human-oversight delegation token + privacy-by-design enforcement (cross-ref EU AI Act Art. 14, 27) | `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py`, `hummbl_governance/delegation.py` |
| Deploy AI in agriculture for precision farming and sustainability | 🟡 Partial: compliance-mapper maps agriculture-sector AI requirements and generates evidence; sectoral deployment is organizational | `hummbl_governance/compliance_mapper.py` |
| Promote AI adoption in Estonian industry through digital transformation | 🟡 Partial: compliance-mapper generates industry AI adoption documentation and governance templates; adoption program delivery is organizational | `hummbl_governance/compliance_mapper.py` |

### Talent, data, and ethics (Actions 5–7)

| Obligation | Coverage | Evidence |
|---|---|---|
| Develop AI talent through education and training programs | 🟡 Partial: compliance-mapper generates AI literacy training materials and documentation; curriculum delivery is organizational | `hummbl_governance/compliance_mapper.py` |
| Establish data governance framework for AI with quality and interoperability | ✅ Data-governance tuples + schema-validator enforce data quality and interoperability constraints (cross-ref GDPR) | `hummbl_governance/schema_validator.py`, `hummbl_governance/compliance_mapper.py` |
| Ensure data protection and privacy in AI systems | ✅ Privacy-by-design enforcement + data-minimization tuple + immutable audit trail (cross-ref [`docs/coverage/gdpr.md`](./gdpr.md)) | `hummbl_governance/audit_log.py`, `hummbl_governance/output_validator.py` |
| Apply ethical AI principles aligned with EU and UNESCO frameworks | ✅ Compliance-mapper encodes ethical-principle tuples + doctrine-engine enforces principle doctrine (cross-ref [`docs/coverage/unesco-ai-ethics.md`](./unesco-ai-ethics.md)) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/kernel/doctrine_engine.py` |
| Establish AI impact assessment for public-sector AI systems | ✅ Impact-assessment template with risk-tier classification (cross-ref EU AI Act Art. 27, NIST AI RMF) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |

### International cooperation (Action 8)

| Obligation | Coverage | Evidence |
|---|---|---|
| Participate in international AI cooperation and standards development | 🟡 Partial: compliance-mapper generates standards-mapping documentation and evidence for international alignment; diplomatic participation is governmental | `hummbl_governance/compliance_mapper.py` |
| Monitor and evaluate AI strategy implementation against KPIs | ✅ Compliance-mapper + audit-log + health-probe produce M&E evidence tuples and readiness signals | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py`, `hummbl_governance/health_probe.py` |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| Public-sector AI deployment | 4 | 4 | 0 | 0 |
| Sectoral AI deployment | 3 | 1 | 2 | 0 |
| Talent, data & ethics | 5 | 4 | 1 | 0 |
| International cooperation | 2 | 1 | 1 | 0 |
| **Totals** | **14** | **10** | **4** | **0** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- EU AI Act: [`docs/coverage/eu-ai-act.md`](./eu-ai-act.md)
- GDPR: [`docs/coverage/gdpr.md`](./gdpr.md)
- UNESCO AI Ethics: [`docs/coverage/unesco-ai-ethics.md`](./unesco-ai-ethics.md)
- NIST AI RMF: [`docs/coverage/nist-ai-rmf.md`](./nist-ai-rmf.md)
