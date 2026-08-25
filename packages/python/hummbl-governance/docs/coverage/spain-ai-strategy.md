# Spain National AI Strategy Coverage Matrix — HUMMBL

**Standard**: Estrategia Nacional de Inteligencia Artificial (Spain National AI Strategy)
**Effective**: December 2020 (updated 2021)
**Source**: https://www.lamoncloa.gob.es/presidente/actividad/Documents/PlanNacionalInteligenciaArtificial.pdf
**Last reviewed**: 2026-06-26
**Reviewer**: devin (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not Spanish-licensed counsel and does not provide legal advice on the Spanish AI Strategy. The Strategy is a national policy framework implemented through multiple ministerial actions and EU-level regulation. HUMMBL maps technical primitives to the Strategy's AI governance, ethics, and technical-safety objectives.

## Scope summary

The Spanish National AI Strategy is structured around 5 strategic axes: (1) scientific-technical capabilities, (2) talent, (3) data, (4) ethics and regulatory framework, and (5) adoption. It includes 18 measures across research infrastructure, AI talent development, data governance, ethical AI frameworks, and sectoral adoption. Spain also enacted Law 19/2023 on digital services and is subject to the EU AI Act (cross-ref [`docs/coverage/eu-ai-act.md`](./eu-ai-act.md)).

## Obligations + coverage

### Axis 1 — Scientific-technical capabilities (Measures 1–4)

| Obligation | Coverage | Evidence |
|---|---|---|
| Establish AI research excellence centres and networks | 🟡 Partial: compliance-mapper generates research-evidence documentation and capability mapping; research-centre funding and institutional establishment are governmental | `hummbl_governance/compliance_mapper.py` |
| Develop supercomputing infrastructure for AI (Barcelona Supercomputing Center, RES) | ⚪ Boundary: national HPC infrastructure provisioning is governmental | |
| Promote AI R&D in strategic sectors (health, energy, agriculture, transport) | 🟡 Partial: compliance-mapper maps sector-specific AI requirements and generates R&D evidence; sectoral R&D funding is governmental | `hummbl_governance/compliance_mapper.py` |
| Support AI technology transfer from research to industry | 🟡 Partial: compliance-mapper generates technology-transfer documentation and evidence packages; commercial transfer execution is organizational | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |

### Axis 2 — Talent (Measures 5–8)

| Obligation | Coverage | Evidence |
|---|---|---|
| Develop AI specialization programs in universities and vocational training | ⚪ Boundary: academic curriculum design is organizational | |
| Attract and retain international AI talent | ⚪ Boundary: immigration and talent-attraction policy is governmental | |
| Promote AI literacy and digital skills across the population | 🟡 Partial: compliance-mapper generates AI literacy training materials and documentation; campaign delivery is organizational | `hummbl_governance/compliance_mapper.py` |
| Create AI training programs for public-sector employees | 🟡 Partial: compliance-mapper generates public-sector AI training documentation and governance guidance; training program delivery is organizational | `hummbl_governance/compliance_mapper.py` |

### Axis 3 — Data (Measures 9–12)

| Obligation | Coverage | Evidence |
|---|---|---|
| Develop data governance framework for AI with quality and interoperability standards | ✅ Data-governance tuples + schema-validator enforce data quality and interoperability constraints (cross-ref GDPR, EU Data Act) | `hummbl_governance/schema_validator.py`, `hummbl_governance/compliance_mapper.py` |
| Create national data spaces for strategic sectors (health, mobility, energy) | 🟡 Partial: compliance-mapper generates data-space governance documentation and access-control templates; national data-space infrastructure is governmental | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/capability_fence.py` |
| Promote open data initiatives for AI training and innovation | ✅ Evidence-submission + open-data tuple with provenance tracking and licensing metadata | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Ensure data protection and privacy in AI systems (GDPR compliance) | ✅ Privacy-by-design enforcement + data-minimization tuple + immutable audit trail (cross-ref [`docs/coverage/gdpr.md`](./gdpr.md), [`docs/coverage/ccpa-cpra.md`](./ccpa-cpra.md)) | `hummbl_governance/audit_log.py`, `hummbl_governance/output_validator.py` |

### Axis 4 — Ethics and regulatory framework (Measures 13–15)

| Obligation | Coverage | Evidence |
|---|---|---|
| Develop ethical AI framework aligned with EU AI Act and UNESCO principles | ✅ Compliance-mapper encodes ethical-principle tuples + doctrine-engine enforces principle doctrine (cross-ref [`docs/coverage/eu-ai-act.md`](./eu-ai-act.md), [`docs/coverage/unesco-ai-ethics.md`](./unesco-ai-ethics.md)) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/kernel/doctrine_engine.py` |
| Establish AI impact assessment methodology for public-sector AI systems | ✅ Impact-assessment template with risk-tier classification (cross-ref EU AI Act Art. 27, NIST AI RMF) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Create AI audit and certification mechanisms | 🟡 Partial: audit-log immutable evidence trail + compliance-mapper audit-template support audit evidence; national certification body establishment is governmental | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |

### Axis 5 — Adoption (Measures 16–18)

| Obligation | Coverage | Evidence |
|---|---|---|
| Promote AI adoption in SMEs through support programs and digital transformation | 🟡 Partial: compliance-mapper generates SME AI adoption documentation and governance templates; support-program delivery is organizational | `hummbl_governance/compliance_mapper.py` |
| Deploy AI in public administration for service improvement | ✅ Lifecycle + coordination-bus orchestrate governed AI service delivery with audit trail (cross-ref EU AI Act Art. 60) | `hummbl_governance/lifecycle.py`, `hummbl_governance/coordination_bus.py` |
| Monitor and evaluate AI strategy implementation against defined KPIs | ✅ Compliance-mapper + audit-log + health-probe produce M&E evidence tuples and readiness signals | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py`, `hummbl_governance/health_probe.py` |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| Axis 1 — Scientific-technical | 4 | 0 | 3 | 1 |
| Axis 2 — Talent | 4 | 0 | 2 | 2 |
| Axis 3 — Data | 4 | 3 | 1 | 0 |
| Axis 4 — Ethics & regulatory | 3 | 2 | 1 | 0 |
| Axis 5 — Adoption | 3 | 2 | 1 | 0 |
| **Totals** | **18** | **7** | **8** | **3** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- EU AI Act: [`docs/coverage/eu-ai-act.md`](./eu-ai-act.md)
- UNESCO AI Ethics: [`docs/coverage/unesco-ai-ethics.md`](./unesco-ai-ethics.md)
- GDPR: [`docs/coverage/gdpr.md`](./gdpr.md)
- NIST AI RMF: [`docs/coverage/nist-ai-rmf.md`](./nist-ai-rmf.md)
