# Switzerland AI Action Plan Coverage Matrix — HUMMBL

**Standard**: Swiss Federal Council AI Action Plan (Action Plan for the Swiss Federal Administration on Artificial Intelligence)
**Effective**: April 2024
**Source**: https://www.eda.admin.ch/eda/en/home/aussenpolitik/internationale-vertraege/abkommen-digitales/kuenstliche-intelligenz.html
**Last reviewed**: 2026-06-26
**Reviewer**: devin (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not Swiss-licensed counsel and does not provide legal advice on the Swiss AI Action Plan. The Plan is a federal administration policy framework. HUMMBL maps technical primitives to the Plan's AI governance, ethics, and technical-safety objectives.

## Scope summary

The Swiss AI Action Plan covers 6 action areas: (1) AI in federal administration, (2) legal framework, (3) AI ethics and human rights, (4) AI research and innovation, (5) AI talent and skills, and (6) international cooperation. Switzerland is developing a sectoral AI regulatory approach aligned with the Council of Europe AI Convention (cross-ref [`docs/coverage/council-of-europe-ai-convention.md`](./council-of-europe-ai-convention.md)).

## Obligations + coverage

### AI in federal administration (Action 1)

| Obligation | Coverage | Evidence |
|---|---|---|
| Deploy AI in federal administration with governance and oversight | ✅ Lifecycle + coordination-bus orchestrate governed AI service delivery with audit trail (cross-ref EU AI Act Art. 60) | `hummbl_governance/lifecycle.py`, `hummbl_governance/coordination_bus.py` |
| Ensure transparency and explainability of AI in government services | ✅ Transparency-notification primitive + output-validator explainability gate (cross-ref EU AI Act Art. 50, 13) | `hummbl_governance/audit_log.py`, `hummbl_governance/output_validator.py` |
| Establish AI impact assessment for federal AI deployments | ✅ Impact-assessment template with risk-tier classification (cross-ref EU AI Act Art. 27, NIST AI RMF) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Maintain human oversight and accountability for AI systems in administration | ✅ Human-oversight delegation token + identity-registry role assignment (cross-ref EU AI Act Art. 14) | `hummbl_governance/delegation.py`, `hummbl_governance/identity.py` |

### Legal framework and ethics (Actions 2, 3)

| Obligation | Coverage | Evidence |
|---|---|---|
| Develop sectoral AI legal framework aligned with Council of Europe AI Convention | 🟡 Partial: compliance-mapper maps legal requirements and generates framework documentation; legislative drafting is governmental | `hummbl_governance/compliance_mapper.py` |
| Apply ethical AI principles — human dignity, non-discrimination, transparency, accountability | ✅ Compliance-mapper encodes ethical-principle tuples + doctrine-engine enforces principle doctrine (cross-ref [`docs/coverage/council-of-europe-ai-convention.md`](./council-of-europe-ai-convention.md), [`docs/coverage/unesco-ai-ethics.md`](./unesco-ai-ethics.md)) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/kernel/doctrine_engine.py` |
| Ensure AI systems do not violate fundamental rights | ✅ Output-validation gate for fairness/bias + human-oversight delegation token + immutable audit trail | `hummbl_governance/output_validator.py`, `hummbl_governance/delegation.py`, `hummbl_governance/audit_log.py` |
| Establish AI liability and responsibility framework | 🟡 Partial: audit-log provides immutable evidence trail for liability attribution; legal liability framework enactment is governmental | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |

### Research, innovation, and talent (Actions 4, 5)

| Obligation | Coverage | Evidence |
|---|---|---|
| Support AI research and innovation in Swiss institutions | ⚪ Boundary: research-institution funding and R&D programs are governmental | |
| Develop AI talent through education and training | 🟡 Partial: compliance-mapper generates AI literacy training materials and documentation; curriculum delivery is organizational | `hummbl_governance/compliance_mapper.py` |
| Promote AI literacy and digital skills across the population | 🟡 Partial: compliance-mapper generates AI literacy training materials and documentation; campaign delivery is organizational | `hummbl_governance/compliance_mapper.py` |

### International cooperation (Action 6)

| Obligation | Coverage | Evidence |
|---|---|---|
| Participate in international AI standards and governance forums | 🟡 Partial: compliance-mapper generates standards-mapping documentation and evidence for international alignment; diplomatic participation is governmental | `hummbl_governance/compliance_mapper.py` |
| Align Swiss AI framework with EU AI Act and international standards | ✅ Compliance-mapper cross-framework mapping + evidence substrate (cross-ref [`docs/coverage/eu-ai-act.md`](./eu-ai-act.md), [`docs/coverage/nist-ai-rmf.md`](./nist-ai-rmf.md), [`docs/coverage/iso-42001.md`](./iso-42001.md)) | `hummbl_governance/compliance_mapper.py` |
| Monitor and evaluate AI action plan implementation | ✅ Compliance-mapper + audit-log + health-probe produce M&E evidence tuples and readiness signals | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py`, `hummbl_governance/health_probe.py` |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| AI in federal administration | 4 | 4 | 0 | 0 |
| Legal framework & ethics | 4 | 2 | 2 | 0 |
| Research, innovation & talent | 3 | 0 | 2 | 1 |
| International cooperation | 3 | 2 | 1 | 0 |
| **Totals** | **14** | **8** | **5** | **1** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Council of Europe AI Convention: [`docs/coverage/council-of-europe-ai-convention.md`](./council-of-europe-ai-convention.md)
- EU AI Act: [`docs/coverage/eu-ai-act.md`](./eu-ai-act.md)
- UNESCO AI Ethics: [`docs/coverage/unesco-ai-ethics.md`](./unesco-ai-ethics.md)
- NIST AI RMF: [`docs/coverage/nist-ai-rmf.md`](./nist-ai-rmf.md)
- ISO 42001: [`docs/coverage/iso-42001.md`](./iso-42001.md)
