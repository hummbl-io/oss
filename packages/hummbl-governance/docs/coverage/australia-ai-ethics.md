# Australia AI Ethics Principles Coverage Matrix — HUMMBL

**Standard**: Australia's Artificial Intelligence Ethics Principles (AI Ethics Framework)
**Effective**: November 2019 (voluntary); updated 2024
**Source**: https://www.industry.gov.au/publications/australias-ai-ethics-principles
**Last reviewed**: 2026-06-25
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not Australian legal counsel and does not provide legal advice on the AI Ethics Principles. The Principles are a voluntary framework developed by CSIRO's Data61 and the Department of Industry, Science and Resources (DISR), first published in 2019 and updated in 2024. They carry no statutory force; adoption is organizational. On 21 October 2025, DISR published the Guidance for AI Adoption (6 essential practices), which evolves the Voluntary AI Safety Standard (10 guardrails) and these 8 AI Ethics Principles. Statutory compliance with any binding Australian law is the customer-organization responsibility. HUMMBL maps technical primitives to the 8 principles' recommended practices.

## Scope summary

The AI Ethics Principles apply voluntarily to businesses and governments designing, developing, and implementing AI in Australia. They aim to achieve safer, more reliable, and fairer outcomes; reduce the risk of negative impact on those affected by AI; and ensure the highest ethical standards across the AI lifecycle. The 8 principles are: (1) Human, societal and environmental wellbeing; (2) Human-centred values; (3) Fairness; (4) Privacy protection and security; (5) Reliability and safety; (6) Transparency and explainability; (7) Contestability; (8) Accountability. The framework is intended to inform future binding AI regulation in Australia and aligns with the National Framework for the Assurance of AI in Government.

## Obligations + coverage

### Human, societal and environmental wellbeing + Human-centred values (Principles 1–2)

| Obligation | Coverage | Evidence |
|---|---|---|
| AI systems should benefit individuals, society, and the environment (Principle 1) | ✅ Kernel/doctrine-engine human-benefit intent validation + reward-monitor alignment-to-human-values tracking | `hummbl_governance/kernel/doctrine_engine.py`, `hummbl_governance/reward_monitor.py` |
| AI systems should respect human rights, diversity, and the autonomy of individuals (Principle 2) | ✅ Kernel/law-engine rights-policy enforcement + reasoning-engine autonomy-preservation checks | `hummbl_governance/kernel/law_engine.py`, `hummbl_governance/reasoning.py` |
| Minimize risk of negative impact on those affected by AI applications | ✅ Compliance-mapper impact-assessment records + stride_mapper threat-and-ethics assessment (cross-ref NIST AI RMF MAP) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/stride_mapper.py` |
| Enable human oversight of AI systems so individuals retain meaningful control | ✅ Delegation-token human-oversight tokens + kernel/sequence_engine human-approval gates per cycle (cross-ref EU AI Act Art. 14) | `hummbl_governance/delegation.py`, `hummbl_governance/kernel/sequence_engine.py` |
| Ensure AI does not diminish human autonomy or override human decision-making authority | ✅ Kill-switch human-command halt + kernel/authority_engine human-override authority + lifecycle human-gated state transitions | `hummbl_governance/kill_switch.py`, `hummbl_governance/kernel/authority_engine.py`, `hummbl_governance/lifecycle.py` |

### Fairness (Principle 3)

| Obligation | Coverage | Evidence |
|---|---|---|
| AI systems should be inclusive and accessible | 🟡 Partial: contract-net multi-stakeholder participation + reasoning-engine accessibility checks; inclusive-access assurance is org policy | `hummbl_governance/contract_net.py`, `hummbl_governance/reasoning.py` |
| AI systems should not involve or result in unfair discrimination against individuals, communities, or groups | ✅ Output-validation gate with bias-detection predicates + reasoning-engine fairness checks (cross-ref NIST AI RMF MAP, EU AI Act Art. 10) | `hummbl_governance/output_validator.py`, `hummbl_governance/reasoning.py` |
| Identify potential sources of bias in training data and take steps to mitigate them | ✅ Audit-log bias-identification tuples + compliance-mapper risk-treatment records | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |

### Privacy protection and security (Principle 4)

| Obligation | Coverage | Evidence |
|---|---|---|
| AI systems should respect and uphold privacy rights and data protection | ✅ Output-validator PII/sensitive-data redaction gates + identity-registry data-use scope enforcement (cross-ref GDPR) | `hummbl_governance/output_validator.py`, `hummbl_governance/identity.py` |
| Ensure the security of data throughout the AI lifecycle | ✅ Capability-fence data-access restrictions + audit-log immutable access trail + kernel/law_engine policy enforcement | `hummbl_governance/capability_fence.py`, `hummbl_governance/audit_log.py`, `hummbl_governance/kernel/law_engine.py` |
| Implement measures to prevent data privacy breaches (monitoring, fail-safe mechanisms) | ✅ Circuit-breaker breach-response fast-fail + health-probe continuous monitoring | `hummbl_governance/circuit_breaker.py`, `hummbl_governance/health_probe.py` |
| Resist compromise by unauthorised parties accessing AI systems or data | ✅ Capability-fence sandbox + identity-registry authentication + delegation-token authorization | `hummbl_governance/capability_fence.py`, `hummbl_governance/identity.py`, `hummbl_governance/delegation.py` |

### Reliability and safety (Principle 5)

| Obligation | Coverage | Evidence |
|---|---|---|
| AI systems should reliably operate in accordance with their intended purpose | ✅ Schema-validator input/output contract validation + kernel/doctrine-engine intent registration + output-validator policy gates | `hummbl_governance/schema_validator.py`, `hummbl_governance/kernel/doctrine_engine.py`, `hummbl_governance/output_validator.py` |
| Implement fail-safe mechanisms to prevent harm in critical situations | ✅ Kill-switch 4-mode halt (pause/stop/terminate/quarantine) + capability-fence boundary enforcement | `hummbl_governance/kill_switch.py`, `hummbl_governance/capability_fence.py` |
| Conduct rigorous testing and validation to ensure AI performs as accurately as intended | ✅ Schema-validator input/output contract validation + output-validator quality gates + health-probe reliability metrics | `hummbl_governance/schema_validator.py`, `hummbl_governance/output_validator.py`, `hummbl_governance/health_probe.py` |
| Monitor AI systems in operation to detect anomalies and unintended behaviour | ✅ Circuit-breaker anomaly fast-fail + health-probe liveness/readiness checks + convergence-guard drift alerts | `hummbl_governance/circuit_breaker.py`, `hummbl_governance/health_probe.py`, `hummbl_governance/convergence_guard.py` |

### Transparency and explainability (Principle 6)

| Obligation | Coverage | Evidence |
|---|---|---|
| Transparency and responsible disclosure so people understand when they are being significantly impacted by AI | ✅ Audit-log AI-use disclosure tuples + output-validator provenance-labeling (cross-ref EU AI Act Art. 50, South Korea Art. 31) | `hummbl_governance/audit_log.py`, `hummbl_governance/output_validator.py` |
| People can find out when an AI system is engaging with them | ✅ Output-validator AI-engagement indicator + compliance-mapper disclosure records | `hummbl_governance/output_validator.py`, `hummbl_governance/compliance_mapper.py` |
| Disclose the intended purpose of the AI system | ✅ Compliance-mapper purpose-declaration records + kernel/doctrine-engine intent registration | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/kernel/doctrine_engine.py` |
| Provide information on training data and potential historical or social biases | ✅ Audit-log training-data provenance tuples + bias-disclosure records (cross-ref EU AI Act Art. 10) | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Provide clear explanations and justifications for AI decisions | ✅ Reasoning-engine explanation generation + audit-log decision-trace records | `hummbl_governance/reasoning.py`, `hummbl_governance/audit_log.py` |

### Contestability (Principle 7)

| Obligation | Coverage | Evidence |
|---|---|---|
| When an AI system significantly impacts a person, community, group, or environment, there should be a timely process to challenge the use or outcomes | ✅ Audit-log challenge/redress tuples + compliance-mapper appeal-workflow records (cross-ref Colorado § 6-1-1704) | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Provide mechanisms for people to contest AI decisions that affect them | ✅ Delegation-token appeal-authorization + kernel/authority_engine challenge-routing | `hummbl_governance/delegation.py`, `hummbl_governance/kernel/authority_engine.py` |
| Enable timely human review of contested AI outcomes | ✅ Kernel/sequence_engine human-review gates + lifecycle contestation-state transitions | `hummbl_governance/kernel/sequence_engine.py`, `hummbl_governance/lifecycle.py` |
| Suspend or halt AI operation pending contestation outcome | ✅ Kill-switch pause mode + circuit-breaker contestation-triggered fast-fail | `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py` |

### Accountability (Principle 8)

| Obligation | Coverage | Evidence |
|---|---|---|
| People responsible for the different phases of the AI system lifecycle should be identifiable and accountable for outcomes | ✅ Delegation-token accountability assignment + kernel/authority-engine role-based responsibility + kernel/receipt-engine immutable receipts | `hummbl_governance/delegation.py`, `hummbl_governance/kernel/authority_engine.py`, `hummbl_governance/kernel/receipt_engine.py` |
| Human oversight of AI systems should be enabled | ✅ Health-probe continuous monitoring + audit-log human-review checkpoints + convergence-guard drift alerts (cross-ref EU AI Act Art. 14) | `hummbl_governance/health_probe.py`, `hummbl_governance/audit_log.py`, `hummbl_governance/convergence_guard.py` |
| Maintain auditable records of AI system decisions and actions for accountability | ✅ Immutable audit-log retention + kernel/receipt-engine tamper-evident receipts + lamport_clock causal ordering | `hummbl_governance/audit_log.py`, `hummbl_governance/kernel/receipt_engine.py`, `hummbl_governance/lamport_clock.py` |
| Address system purpose to avoid consequential harm | ✅ Kernel/doctrine-engine intent registration + kernel/evidence-engine purpose validation | `hummbl_governance/kernel/doctrine_engine.py`, `hummbl_governance/kernel/evidence_engine.py` |
| Address technology capability to avoid consequential harm | ✅ Capability-fence scope enforcement + schema-validator capability contracts | `hummbl_governance/capability_fence.py`, `hummbl_governance/schema_validator.py` |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| Wellbeing + Human-centred values (Principles 1–2) | 5 | 5 | 0 | 0 |
| Fairness (Principle 3) | 3 | 2 | 1 | 0 |
| Privacy protection and security (Principle 4) | 4 | 4 | 0 | 0 |
| Reliability and safety (Principle 5) | 4 | 4 | 0 | 0 |
| Transparency and explainability (Principle 6) | 5 | 5 | 0 | 0 |
| Contestability (Principle 7) | 4 | 4 | 0 | 0 |
| Accountability (Principle 8) | 5 | 5 | 0 | 0 |
| **Totals** | **30** | **29** | **1** | **0** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated. The Australia AI Ethics Principles are voluntary; mapping HUMMBL primitives to the 8 principles demonstrates technical alignment, not statutory compliance.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Transparency overlaps EU AI Act Art. 50 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Transparency overlaps South Korea AI Basic Act Art. 31 — see [`south-korea-ai-basic-act.md`](./south-korea-ai-basic-act.md)
- Fairness/bias overlaps NIST AI RMF MAP — see [`nist-ai-rmf.md`](./nist-ai-rmf.md)
- Human oversight overlaps EU AI Act Art. 14 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Accountability overlaps ISO 42001 — see [`iso-42001.md`](./iso-42001.md)
- Privacy overlaps GDPR — see [`gdpr.md`](./gdpr.md)
- Risk management overlaps NIST AI RMF MEASURE — see [`nist-ai-rmf.md`](./nist-ai-rmf.md)
- Contestability overlaps Colorado § 6-1-1704 — see [`colorado-ai-act.md`](./colorado-ai-act.md)
