# Hong Kong AI Guidelines Coverage Matrix — HUMMBL

**Standard**: Hong Kong AI Governance Framework (Ethical AI Framework)
**Effective**: 2021 (updated 2024)
**Source**: https://www.pcpd.org.hk/english/resources_privacy/publications_and_reports/files/guidance_on_ai_eng.pdf
**Last reviewed**: 2026-06-26
**Reviewer**: devin (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not Hong Kong-licensed counsel and does not provide legal advice on the Hong Kong AI Guidelines. The Guidelines are a policy framework issued by the Office of the Privacy Commissioner for Personal Data (PCPD). HUMMBL maps technical primitives to the Guidelines' AI governance and data-protection objectives.

## Scope summary

Hong Kong's Ethical AI Framework covers 7 principles: (1) accountability, (2) transparency, (3) fairness, (4) privacy, (5) human oversight, (6) data governance, and (7) risk management. The framework applies to organizations using AI in Hong Kong and aligns with the Personal Data (Privacy) Ordinance (PDPO).

## Obligations + coverage

### Accountability and transparency (Principles 1, 2)

| Obligation | Coverage | Evidence |
|---|---|---|
| Establish accountability for AI system outcomes with named responsible persons | ✅ Human-oversight delegation token + identity-registry role assignment + immutable audit trail (cross-ref EU AI Act Art. 14) | `hummbl_governance/delegation.py`, `hummbl_governance/identity.py`, `hummbl_governance/audit_log.py` |
| Ensure transparency of AI use and disclose AI interaction to users | ✅ Transparency-notification primitive + on-demand disclosure trigger (cross-ref EU AI Act Art. 50) | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Provide explainability of AI decisions and outputs | ✅ Output-validator explainability gate + decision-rationale tuple (cross-ref EU AI Act Art. 13) | `hummbl_governance/output_validator.py`, `hummbl_governance/audit_log.py` |

### Fairness and privacy (Principles 3, 4)

| Obligation | Coverage | Evidence |
|---|---|---|
| Ensure AI systems are fair and do not discriminate | ✅ Output-validation gate for fairness/bias + impact-assessment template with fairness component | `hummbl_governance/output_validator.py`, `hummbl_governance/compliance_mapper.py` |
| Ensure data protection and privacy in AI systems (PDPO compliance) | ✅ Privacy-by-design enforcement + data-minimization tuple + immutable audit trail | `hummbl_governance/audit_log.py`, `hummbl_governance/output_validator.py` |
| Obtain meaningful consent for AI use of personal data | ✅ Consent-management tuple + consent-revocation support + audit trail | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |

### Human oversight and data governance (Principles 5, 6)

| Obligation | Coverage | Evidence |
|---|---|---|
| Maintain human oversight and accountability for AI systems | ✅ Human-oversight delegation token + identity-registry role assignment (cross-ref EU AI Act Art. 14) | `hummbl_governance/delegation.py`, `hummbl_governance/identity.py` |
| Establish data governance framework for AI with quality and lineage tracking | ✅ Data-governance tuples + schema-validator enforce data quality and interoperability constraints | `hummbl_governance/schema_validator.py`, `hummbl_governance/compliance_mapper.py` |
| Ensure data quality, accuracy, and representativeness for AI training | ✅ Schema-validator + data-quality tuple + provenance tracking | `hummbl_governance/schema_validator.py`, `hummbl_governance/audit_log.py` |

### Risk management (Principle 7)

| Obligation | Coverage | Evidence |
|---|---|---|
| Establish AI risk management framework with assessment and mitigation | ✅ Risk-assessment + STRIDE threat mapping + risk-treatment tuples (cross-ref NIST AI RMF, ISO/IEC 23894) | `hummbl_governance/stride_mapper.py`, `hummbl_governance/compliance_mapper.py` |
| Conduct AI impact assessment before deployment | ✅ Impact-assessment template with risk-tier classification (cross-ref EU AI Act Art. 27, NIST AI RMF) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Implement kill-switch and circuit-breaker for AI safety | ✅ Kill-switch 4-mode halt + circuit-breaker fast-fail for adversarial-trigger containment | `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py` |
| Monitor and evaluate AI systems for ongoing compliance and safety | ✅ Compliance-mapper + audit-log + health-probe produce M&E evidence tuples and readiness signals | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py`, `hummbl_governance/health_probe.py` |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| Accountability & transparency | 3 | 3 | 0 | 0 |
| Fairness & privacy | 3 | 3 | 0 | 0 |
| Human oversight & data governance | 3 | 3 | 0 | 0 |
| Risk management | 4 | 4 | 0 | 0 |
| **Totals** | **13** | **13** | **0** | **0** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- EU AI Act: [`docs/coverage/eu-ai-act.md`](./eu-ai-act.md)
- NIST AI RMF: [`docs/coverage/nist-ai-rmf.md`](./nist-ai-rmf.md)
- ISO/IEC 23894: [`docs/coverage/iso-iec-23894.md`](./iso-iec-23894.md)
- CCPA/CPRA: [`docs/coverage/ccpa-cpra.md`](./ccpa-cpra.md)
