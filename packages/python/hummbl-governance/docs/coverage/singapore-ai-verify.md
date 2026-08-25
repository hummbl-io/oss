# Singapore AI Verify Coverage Matrix — HUMMBL

**Standard**: AI Verify — AI Governance Testing Framework and Toolkit (Model AI Governance Framework, 2nd ed.)
**Effective**: May 25, 2022 (MVP launch); updated May 29, 2025 (Generative AI extension)
**Source**: https://aiverifyfoundation.sg/
**Last reviewed**: 2026-06-25
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not Singapore legal counsel and does not provide legal advice on AI Verify or the Model AI Governance Framework (MGF). AI Verify is a voluntary, non-binding self-assessment framework developed by IMDA and the PDPC; it does not certify systems as "safe" or "ethical," nor does it define ethical standards. It provides verifiability — allowing AI system developers and owners to demonstrate claims about their AI systems' performance against 11 internationally recognised governance principles grouped into 5 pillars. Statutory compliance and framework adoption are the customer-organisation responsibility. HUMMBL maps technical primitives to the framework's transparency, explainability, safety, fairness, accountability, and human-oversight testing requirements.

## Scope summary

AI Verify applies to AI application owners, developers, internal compliance teams, and external auditors seeking to assess the responsible implementation of AI systems — both traditional AI (since 2022) and generative AI (since the May 2025 update). The framework is technology-, industry-, scale-, and business-model agnostic, and is aligned with EU, G7, OECD, US NIST AI RMF, Hiroshima Process CoC, and ISO/IEC 42001 frameworks. Each of the 11 principles has desired outcomes assessed through a combination of technical tests and process checks (documentary evidence). The Model AI Governance Framework (2nd edition, 2020) provides the underlying implementation guidance across four key areas: internal governance structures, human involvement in AI-augmented decision-making, operations management, and stakeholder interaction and communication.

## Obligations + coverage

### Transparency on use of AI (Principle 1)

| Obligation | Coverage | Evidence |
|---|---|---|
| Provide responsible disclosure to individuals affected by AI systems so they understand the outcome | ✅ Transparency-notification primitive (cross-ref EU AI Act Art. 50, South Korea AI Basic Act Art. 31) | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Disclose use of AI in the system, its intended use, limitations, and risk assessments (process checks of documentary evidence) | ✅ Disclosure-record tuple + intended-use declaration in compliance mapper | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Use simple language appropriate to audience, purpose, and context in stakeholder communication | 🟡 Partial: report generator produces plain-language summaries; audience-tailoring is org task | `hummbl_governance/compliance_mapper.py` |

### Understanding how an AI model reaches a decision (Principles 2–3)

| Obligation | Coverage | Evidence |
|---|---|---|
| Explainability — assess factors contributing to the AI system's decision, behaviour, outcomes, and implications (technical tests + process checks) | ✅ Reasoning-engine rationale trace + decision-factor attribution | `hummbl_governance/reasoning.py`, `hummbl_governance/audit_log.py` |
| Demonstrate development preference for explainable or interpretable-by-default models (process checks) | 🟡 Partial: reasoning engine records rationale; model-selection preference is org task | `hummbl_governance/reasoning.py` |
| Repeatability / reproducibility — ensure consistency in AI output by replicating the system internally or via third party (process checks of model/data provenance, versioning) | ✅ Lamport-clock ordering + immutable audit-log provenance + schema-validated inputs | `hummbl_governance/lamport_clock.py`, `hummbl_governance/audit_log.py`, `hummbl_governance/schema_validator.py` |

### Safety, security, and robustness (Principles 4–6)

| Obligation | Coverage | Evidence |
|---|---|---|
| Safety — conduct impact/risk assessments and ensure known risks are identified and mitigated (process checks) | ✅ Risk-assessment template + risk-treatment tuples (cross-ref NIST AI RMF, EU AI Act Art. 9) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Safety — implement measures to mitigate harm, including physical harm, with kill-switch and fast-fail controls | ✅ Kill-switch 4-mode halt + circuit-breaker fast-fail + physical-governor kinematic limits | `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py`, `hummbl_governance/physical_governor.py` |
| Security — protect AI systems, data, and infrastructure from unauthorised access, disclosure, modification, or disruption (presently NA in MVP; assessed via process checks) | 🟡 Partial: capability-fence sandbox + identity registry + STRIDE threat mapper; full cybersecurity posture is org task | `hummbl_governance/capability_fence.py`, `hummbl_governance/identity.py`, `hummbl_governance/stride_mapper.py` |
| Robustness — ensure the AI system functions despite unexpected input (technical tests + process checks on adversarial resilience) | ✅ Output-validator gate + circuit-breaker on anomalous output + schema validation of inputs | `hummbl_governance/output_validator.py`, `hummbl_governance/circuit_breaker.py`, `hummbl_governance/schema_validator.py` |

### Fairness and data governance (Principles 7–8)

| Obligation | Coverage | Evidence |
|---|---|---|
| Fairness — avoid unintended bias; ensure the AI system makes the same decision even if a sensitive attribute is changed (technical tests + process checks on fairness-metric strategy) | 🟡 Partial: output-validator bias-detection rules + audit-log records; statistical fairness-test execution is org task | `hummbl_governance/output_validator.py`, `hummbl_governance/audit_log.py` |
| Fairness — define sensitive attributes consistent with legislation and corporate values; document fairness-metric selection aligned with intended outcomes (process checks) | ✅ Compliance-mapper fairness-assessment template + policy-record tuple | `hummbl_governance/compliance_mapper.py` |
| Data governance — ensure source and quality of data via good data governance practices (presently NA in MVP; assessed via process checks of data lineage and quality) | 🟡 Partial: schema-validator enforces input data quality; full data-lineage and provenance tracking is org task | `hummbl_governance/schema_validator.py`, `hummbl_governance/audit_log.py` |

### Accountability and human agency/oversight (Principles 9–10)

| Obligation | Coverage | Evidence |
|---|---|---|
| Accountability — establish clear internal governance mechanisms for proper management and oversight of AI system development and deployment (process checks) | ✅ Governance-kernel authority + role-based delegation + receipt-based accountability | `hummbl_governance/kernel/authority_engine.py`, `hummbl_governance/delegation.py`, `hummbl_governance/kernel/receipt_engine.py` |
| Accountability — assign clear roles and responsibilities for AI system operation and oversight | ✅ Identity-registry role assignment + delegation-token authority chains | `hummbl_governance/identity.py`, `hummbl_governance/delegation.py` |
| Human agency and oversight — design AI system so it does not diminish human ability to make decisions or take control (process checks) | ✅ Human-oversight delegation token + kill-switch human-in/on/out-of-loop modes (cross-ref EU AI Act Art. 14) | `hummbl_governance/kill_switch.py`, `hummbl_governance/delegation.py` |
| Human agency and oversight — define the role of humans (human-in-the-loop, human-over-the-loop, human-out-of-the-loop) for the AI system | ✅ Kill-switch 4-mode halt (RUN/HALT/PAUSE/STOP) maps to human-in/on/out-of-loop oversight tiers | `hummbl_governance/kill_switch.py` |

### Inclusive growth and Model Framework governance (Principle 11 + MGF four key areas)

| Obligation | Coverage | Evidence |
|---|---|---|
| Inclusive growth, societal and environmental well-being — ensure beneficial outcomes for people and the planet (presently NA in MVP; assessed via process checks) | ⚪ Boundary: societal/environmental impact assessment is organisational policy, not software-addressable | |
| MGF internal governance — set up corporate governance and oversight processes with internal controls, monitoring, and reporting systems | ✅ Governance-kernel law + schedule + sequence engines + audit-log monitoring | `hummbl_governance/kernel/law_engine.py`, `hummbl_governance/kernel/schedule_engine.py`, `hummbl_governance/kernel/sequence_engine.py`, `hummbl_governance/audit_log.py` |
| MGF operations management — ensure good data accountability, minimise bias, and maintain model robustness through regular tuning and reproducibility | ✅ Schema-validator data quality + output-validator bias checks + lifecycle management + lamport-clock reproducibility | `hummbl_governance/schema_validator.py`, `hummbl_governance/output_validator.py`, `hummbl_governance/lifecycle.py`, `hummbl_governance/lamport_clock.py` |
| MGF stakeholder interaction — provide general disclosure and increased transparency on how AI is used in products and services | 🟡 Partial: compliance-report generator produces stakeholder-facing summaries; publication and channel management are org tasks | `hummbl_governance/compliance_mapper.py` |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| Transparency (Principle 1) | 3 | 2 | 1 | 0 |
| Explainability & reproducibility (Principles 2–3) | 3 | 2 | 1 | 0 |
| Safety, security & robustness (Principles 4–6) | 4 | 3 | 1 | 0 |
| Fairness & data governance (Principles 7–8) | 3 | 1 | 2 | 0 |
| Accountability & human oversight (Principles 9–10) | 4 | 4 | 0 | 0 |
| Inclusive growth & MGF governance (Principle 11 + MGF) | 4 | 2 | 1 | 1 |
| **Totals** | **21** | **14** | **6** | **1** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Transparency overlaps EU AI Act Art. 50 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Transparency overlaps South Korea AI Basic Act Art. 31 — see [`south-korea-ai-basic-act.md`](./south-korea-ai-basic-act.md)
- Risk management overlaps NIST AI RMF — see [`nist-ai-rmf.md`](./nist-ai-rmf.md)
- Human oversight overlaps EU AI Act Art. 14 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Security overlaps STRIDE threat taxonomy — see [`stride.md`](./stride.md)
- Internal governance overlaps ISO/IEC 42001 — see [`iso-42001.md`](./iso-42001.md)
- AI Verify crosswalks to NIST AI RMF, Hiroshima Process CoC, and ISO/IEC 42001 are published by IMDA at https://aiverifyfoundation.sg/what-is-ai-verify/
