# Singapore Model AI Governance Framework Coverage Matrix — HUMMBL

**Standard**: Model AI Governance Framework, Second Edition (PDPC/IMDA)
**Effective**: 2020 (voluntary guidance; referenced as 2024 edition per latest PDPC listing)
**Source**: https://www.pdpc.gov.sg/help-and-resources/2020/01/model-ai-governance-framework
**Last reviewed**: 2026-06-25
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not Singapore legal counsel and does not provide legal advice on the Model AI Governance Framework. The Model Framework is voluntary guidance published by the Personal Data Protection Commission (PDPC) and Info-communications Media Development Authority (IMDA) — it is not legally binding statute. It translates AI ethical principles into practical, implementable measures for private-sector organisations deploying AI at scale. Statutory compliance (e.g. PDPA, sectoral law) remains a customer-organisation responsibility. HUMMBL maps technical primitives to the Model Framework's four-area structure: internal governance, human oversight, operations management, and stakeholder engagement.

## Scope summary

The Model Framework applies to private-sector organisations deploying AI at scale in Singapore. It is technology- and sector-agnostic, covering both internal-facing and customer-facing AI-augmented decision-making. The four broad areas are: (A) internal governance structures and measures, (B) determining the level of human involvement in AI-augmented decision-making, (C) operations management, and (D) stakeholder interaction and communication. The framework is principle-driven and risk-based — organisations are encouraged to adopt measures proportional to the impact of their AI systems on individuals. A companion Generative AI Framework (2024) extends the model with nine dimensions (accountability, data, trusted development, incident reporting, testing, security, content provenance, safety, R&D) but is out of scope for this matrix.

## Obligations + coverage

### Internal governance structures and measures (§3.4–3.10)

| Obligation | Coverage | Evidence |
|---|---|---|
| Allocate clear roles and responsibilities for ethical AI deployment across personnel and departments | ✅ Delegation-token issuance + identity-registry role assignment (cross-ref EU AI Act Art. 14, NIST AI RMF GOVERN) | `hummbl_governance/delegation.py`, `hummbl_governance/identity.py` |
| Establish coordinating body with cross-organisation representation and relevant expertise | ✅ Coordination-bus topic registration + multi-agent message routing | `hummbl_governance/coordination_bus.py` |
| Apply risk management framework to assess and manage AI deployment risks, including adverse impact on individuals | ✅ Risk-assessment template + risk-treatment tuples (cross-ref NIST AI RMF, EU AI Act Art. 9) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Board and senior management oversight of AI strategy, risk appetite, and corporate values | 🟡 Partial: delegation-token authority-level captures hierarchy; board-level governance is org task | `hummbl_governance/delegation.py`, `hummbl_governance/kernel/authority_engine.py` |
| Ensure staff working with AI are properly trained to interpret outputs and detect bias | 🟡 Partial: lifecycle onboarding tracks training state; curriculum delivery is org task | `hummbl_governance/lifecycle.py` |
| Implement internal checks and balances — separate teams for methodology/deployment and validation | ✅ Capability-fence isolation + audit-log independent verification | `hummbl_governance/capability_fence.py`, `hummbl_governance/audit_log.py` |
| Ensure AI deployment complies with existing laws and regulations (PDPA, Competition Act, sectoral rules) | ✅ Law-engine rule loading + compliance-mapper crosswalk | `hummbl_governance/kernel/law_engine.py`, `hummbl_governance/compliance_mapper.py` |
| Develop and maintain governance handbook documenting the entire AI deployment process | ✅ Audit-log immutable documentation + evidence-export | `hummbl_governance/audit_log.py`, `hummbl_governance/kernel/evidence_engine.py` |

### Human involvement in AI-augmented decision-making (§3.11–3.21)

| Obligation | Coverage | Evidence |
|---|---|---|
| Determine appropriate level of human involvement — human-in-the-loop, human-over-the-loop, or human-out-of-the-loop | ✅ Delegation-token oversight-mode configuration + capability-fence autonomy limits | `hummbl_governance/delegation.py`, `hummbl_governance/capability_fence.py` |
| Human-in-the-loop for high-impact decisions requiring affirmative human action before execution | ✅ Kill-switch HOLD mode + delegation-token human-approval gate | `hummbl_governance/kill_switch.py`, `hummbl_governance/delegation.py` |
| Human-over-the-loop intervention when AI encounters unexpected or undesirable events | ✅ Circuit-breaker fast-fail + kill-switch HALT mode for human takeover | `hummbl_governance/circuit_breaker.py`, `hummbl_governance/kill_switch.py` |
| Assess risk appetite and severity of harm to determine oversight level | ✅ Risk-assessment template with harm-severity scoring | `hummbl_governance/compliance_mapper.py` |
| Minimise risk of harm to individuals from AI-augmented decisions | ✅ Output-validator harm-gate + capability-fence action restriction | `hummbl_governance/output_validator.py`, `hummbl_governance/capability_fence.py` |
| Use statistical confidence levels to trigger human review of low-confidence AI outputs | ✅ Circuit-breaker confidence-threshold trigger + health-probe anomaly detection | `hummbl_governance/circuit_breaker.py`, `hummbl_governance/health_probe.py` |

### Operations management (§3.22–3.41)

| Obligation | Coverage | Evidence |
|---|---|---|
| Ensure data quality — assess representativeness, completeness, reliability, and relevance of training data | ✅ Schema-validator data-quality checks + audit-log data-lineage tuples | `hummbl_governance/schema_validator.py`, `hummbl_governance/audit_log.py` |
| Minimise bias in data and models to prevent unintended discriminatory decisions | ✅ Output-validator fairness-gate + audit-log bias-incident tuples | `hummbl_governance/output_validator.py`, `hummbl_governance/audit_log.py` |
| Justify model selection and design against intended objective and use case | ✅ Compliance-mapper objective-alignment assessment + evidence-engine documentation | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/kernel/evidence_engine.py` |
| Ensure model robustness, reproducibility, and auditability | ✅ Lamport-clock deterministic ordering + audit-log immutable trace + receipt-engine provenance | `hummbl_governance/lamport_clock.py`, `hummbl_governance/audit_log.py`, `hummbl_governance/kernel/receipt_engine.py` |
| Establish monitoring and reporting systems for deployed AI performance and issues | ✅ Health-probe continuous monitoring + audit-log performance-event tuples | `hummbl_governance/health_probe.py`, `hummbl_governance/audit_log.py` |
| Maintain, document, and review deployed AI models with remediation measures | ✅ Lifecycle phase tracking + audit-log model-version documentation | `hummbl_governance/lifecycle.py`, `hummbl_governance/audit_log.py` |
| Incorporate explainability features in model design — report confidence levels and decision rationale | ✅ Reasoning-engine explanation generation + evidence-engine rationale capture | `hummbl_governance/reasoning.py`, `hummbl_governance/kernel/evidence_engine.py` |
| Implement regular tuning and parameter adjustment based on monitoring feedback | ✅ Lifecycle phase transition + health-probe drift detection | `hummbl_governance/lifecycle.py`, `hummbl_governance/health_probe.py` |
| Monitor upstream data source changes for adverse model impact (data drift) | ✅ Schema-validator drift detection + health-probe anomaly alerting | `hummbl_governance/schema_validator.py`, `hummbl_governance/health_probe.py` |

### Stakeholder interaction and communication (§3.42–3.49)

| Obligation | Coverage | Evidence |
|---|---|---|
| Disclose AI use to stakeholders — make AI policies known to users | ✅ Transparency-notification tuple + audit-log disclosure record (cross-ref EU AI Act Art. 50) | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Provide explanations of AI-augmented decisions to individuals (how AI works, how a decision was made, reasons, impact) | ✅ Reasoning-engine explanation generation + compliance-mapper explanation-plan template | `hummbl_governance/reasoning.py`, `hummbl_governance/compliance_mapper.py` |
| Establish feedback channels for stakeholders to provide input on AI systems | ✅ Coordination-bus feedback topic + audit-log feedback-receipt tuples | `hummbl_governance/coordination_bus.py`, `hummbl_governance/audit_log.py` |
| Review communications channels and stakeholder interactions for effectiveness | 🟡 Partial: audit-log records interactions; effectiveness review is org task | `hummbl_governance/audit_log.py` |
| Make communications easy to understand and context-appropriate for different stakeholder groups | 🟡 Partial: reasoning-engine generates explanations; audience tailoring is org task | `hummbl_governance/reasoning.py` |

### Foundational principles (§2.1–2.4)

| Obligation | Coverage | Evidence |
|---|---|---|
| AI decisions should be explainable — provide understandable rationale for algorithmic decisions | ✅ Reasoning-engine explanation generation + evidence-engine rationale capture | `hummbl_governance/reasoning.py`, `hummbl_governance/kernel/evidence_engine.py` |
| AI decisions should be transparent — make AI use and decision processes visible | ✅ Audit-log immutable trace + receipt-engine provenance chain | `hummbl_governance/audit_log.py`, `hummbl_governance/kernel/receipt_engine.py` |
| AI decisions should be fair — avoid unintended discriminatory outcomes | ✅ Output-validator fairness-gate + bias-detection tuples | `hummbl_governance/output_validator.py`, `hummbl_governance/audit_log.py` |
| AI solutions should be human-centric — preserve human agency and oversight | ✅ Delegation-token human-oversight mode + kill-switch human-control gate | `hummbl_governance/delegation.py`, `hummbl_governance/kill_switch.py` |

### Voluntary nature and scope

| Obligation | Coverage | Evidence |
|---|---|---|
| The Model Framework is voluntary guidance — adoption is encouraged but not legally mandated | ⚪ Boundary: voluntary-adoption decision is organizational, not software-addressable | |
| Companion Generative AI Framework (2024, nine dimensions) extends guidance to generative AI | ⚪ Boundary: separate framework scope — see future coverage matrix when available | |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| Internal governance (§3.4–3.10) | 8 | 6 | 2 | 0 |
| Human involvement (§3.11–3.21) | 6 | 6 | 0 | 0 |
| Operations management (§3.22–3.41) | 9 | 9 | 0 | 0 |
| Stakeholder interaction (§3.42–3.49) | 5 | 3 | 2 | 0 |
| Foundational principles (§2.1–2.4) | 4 | 4 | 0 | 0 |
| Voluntary nature and scope | 2 | 0 | 0 | 2 |
| **Totals** | **34** | **28** | **4** | **2** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Human oversight overlaps EU AI Act Art. 14 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Risk management overlaps NIST AI RMF GOVERN/MEASURE — see [`nist-ai-rmf.md`](./nist-ai-rmf.md)
- Transparency and disclosure overlaps EU AI Act Art. 50 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Explainability overlaps EU AI Act Art. 13 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Internal governance overlaps ISO 42001 AI management system — see [`iso-42001.md`](./iso-42001.md)
- Agentic AI extension overlaps IMDA Model AI Governance Framework for Agentic AI — see [`imda-agentic.md`](./imda-agentic.md)
