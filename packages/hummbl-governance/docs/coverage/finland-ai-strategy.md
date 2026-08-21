# Finland AI Strategy Coverage Matrix — HUMMBL

**Standard**: Finland's Age of Artificial Intelligence (AI Strategy)
**Effective**: 2019 (updated through 2025)
**Source**: https://vm.fi/en/ai
**Last reviewed**: 2026-06-26
**Reviewer**: devin (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not Finnish-licensed counsel and does not provide legal advice on the Finnish AI Strategy. The Strategy is a national policy framework. HUMMBL maps technical primitives to the Strategy's AI governance, ethics, and technical-safety objectives.

## Scope summary

Finland's AI Strategy focuses on 8 key areas: (1) AI in public services, (2) AI in healthcare, (3) AI in mobility, (4) AI in industry, (5) AI in energy, (6) data economy, (7) AI ethics and regulation, and (8) AI skills and education. Finland is subject to EU AI Act (cross-ref [`docs/coverage/eu-ai-act.md`](./eu-ai-act.md)) and GDPR (cross-ref [`docs/coverage/gdpr.md`](./gdpr.md)).

## Obligations + coverage

### Public services and governance (Measures 1–3)

| Obligation | Coverage | Evidence |
|---|---|---|
| Deploy AI in public administration for citizen service improvement | ✅ Lifecycle + coordination-bus orchestrate governed AI service delivery with audit trail (cross-ref EU AI Act Art. 60) | `hummbl_governance/lifecycle.py`, `hummbl_governance/coordination_bus.py` |
| Ensure transparency and explainability of AI in public services | ✅ Transparency-notification primitive + output-validator explainability gate (cross-ref EU AI Act Art. 50, 13) | `hummbl_governance/audit_log.py`, `hummbl_governance/output_validator.py` |
| Establish AI governance framework for public-sector AI systems | ✅ Compliance-mapper encodes governance obligations + doctrine-engine enforces governance doctrine (cross-ref NIST AI RMF GOVERN) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/kernel/doctrine_engine.py` |

### Healthcare and mobility (Measures 4–5)

| Obligation | Coverage | Evidence |
|---|---|---|
| Deploy AI in healthcare with safety, privacy, and human oversight | ✅ Kill-switch 4-mode halt + circuit-breaker fast-fail + human-oversight delegation token + privacy-by-design enforcement (cross-ref EU AI Act Art. 14, 27) | `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py`, `hummbl_governance/delegation.py` |
| Deploy AI in mobility with safety assurance and risk management | ✅ Risk-assessment + STRIDE threat mapping + capability-fence for safety-critical mobility contexts | `hummbl_governance/stride_mapper.py`, `hummbl_governance/capability_fence.py` |

### Industry and energy (Measures 6–7)

| Obligation | Coverage | Evidence |
|---|---|---|
| Promote AI adoption in Finnish industry through digital transformation | 🟡 Partial: compliance-mapper generates industry AI adoption documentation and governance templates; adoption program delivery is organizational | `hummbl_governance/compliance_mapper.py` |
| Deploy AI in energy sector for efficiency and sustainability | 🟡 Partial: compliance-mapper maps energy-sector AI requirements and generates evidence; sectoral deployment is organizational | `hummbl_governance/compliance_mapper.py` |

### Data economy (Measure 8)

| Obligation | Coverage | Evidence |
|---|---|---|
| Develop data economy infrastructure with open data and interoperability | ✅ Data-governance tuples + schema-validator enforce data quality and interoperability constraints (cross-ref GDPR, EU Data Act) | `hummbl_governance/schema_validator.py`, `hummbl_governance/compliance_mapper.py` |
| Ensure data protection and privacy in AI data processing | ✅ Privacy-by-design enforcement + data-minimization tuple + immutable audit trail (cross-ref [`docs/coverage/gdpr.md`](./gdpr.md)) | `hummbl_governance/audit_log.py`, `hummbl_governance/output_validator.py` |

### Ethics, regulation, and skills (Measures 9–11)

| Obligation | Coverage | Evidence |
|---|---|---|
| Apply ethical AI principles aligned with EU and UNESCO frameworks | ✅ Compliance-mapper encodes ethical-principle tuples + doctrine-engine enforces principle doctrine (cross-ref [`docs/coverage/unesco-ai-ethics.md`](./unesco-ai-ethics.md)) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/kernel/doctrine_engine.py` |
| Establish AI impact assessment for high-risk public-sector AI | ✅ Impact-assessment template with risk-tier classification (cross-ref EU AI Act Art. 27, NIST AI RMF) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Promote AI literacy and skills development across education system | 🟡 Partial: compliance-mapper generates AI literacy training materials and documentation; curriculum delivery is organizational | `hummbl_governance/compliance_mapper.py` |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| Public services & governance | 3 | 3 | 0 | 0 |
| Healthcare & mobility | 2 | 2 | 0 | 0 |
| Industry & energy | 2 | 0 | 2 | 0 |
| Data economy | 2 | 2 | 0 | 0 |
| Ethics, regulation & skills | 3 | 2 | 1 | 0 |
| **Totals** | **12** | **9** | **3** | **0** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- EU AI Act: [`docs/coverage/eu-ai-act.md`](./eu-ai-act.md)
- GDPR: [`docs/coverage/gdpr.md`](./gdpr.md)
- UNESCO AI Ethics: [`docs/coverage/unesco-ai-ethics.md`](./unesco-ai-ethics.md)
- NIST AI RMF: [`docs/coverage/nist-ai-rmf.md`](./nist-ai-rmf.md)
