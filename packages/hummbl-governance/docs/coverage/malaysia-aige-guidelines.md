# Malaysia AIGE Guidelines Coverage Matrix — HUMMBL

**Standard**: National Guidelines on Artificial Intelligence Governance and Ethics (AIGE), inventory ID 46
**Effective**: September 20, 2024 (voluntary)
**Source**: https://www.malaysia.gov.my/
**Last reviewed**: 2026-06-25
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not Malaysian legal counsel and does not provide legal advice on the AIGE Guidelines. The AIGE are voluntary guidelines issued by the Ministry of Science, Technology, and Innovation (MOSTI) with no statutory force; the Minister has expressed intent that certain aspects may eventually be legislated. The guidelines address three stakeholder groups — end users, government/policymakers, and developers/technology providers — and outline seven core principles adapted from UNESCO, OECD, and the European Commission. Adoption and organizational compliance are the customer-organization responsibility. HUMMBL maps technical primitives to the seven principles' recommended practices and sub-elements.

## Scope summary

The AIGE apply voluntarily to all AI stakeholders in Malaysia: (1) AI end users (individuals and organizations using AI products), (2) government agencies, organizations, and institutions formulating AI policy, and (3) developers, designers, technology providers, and suppliers building AI systems. The guidelines cover the full AI lifecycle from data collection through ongoing monitoring. They are aligned with the National Artificial Intelligence Roadmap 2021–2025 (AI-RMAP) and are expected to inform future binding AI legislation in Malaysia. The seven core principles are: Fairness; Reliability, Safety and Control; Privacy and Security; Inclusiveness; Transparency; Accountability; and the Pursuit of Human Benefit and Happiness.

## Obligations + coverage

### Fairness (Principle 1)

| Obligation | Coverage | Evidence |
|---|---|---|
| Design AI systems to avoid bias and discrimination, including unintentional biases in data processing | ✅ Output-validation gate with bias-detection predicates + reasoning-engine fairness checks (cross-ref NIST AI RMF MAP, EU AI Act Art. 10) | `hummbl_governance/output_validator.py`, `hummbl_governance/reasoning.py` |
| Ensure benefits of AI are equally distributed across races, genders, and religions without leaving anyone behind | 🟡 Partial: convergence-guard detects disparate outcomes; equitable-distribution assurance is org policy task | `hummbl_governance/convergence_guard.py` |
| Identify potential sources of bias in training data and take steps to mitigate them (developer best practice — Data Collection) | ✅ Audit-log bias-identification tuples + compliance-mapper risk-treatment records | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |

### Reliability, Safety and Control (Principle 2)

| Obligation | Coverage | Evidence |
|---|---|---|
| AI systems should operate reliably and consistently under normal and unexpected conditions | ✅ Circuit-breaker fast-fail on anomaly + health-probe liveness/readiness checks + lifecycle state machine | `hummbl_governance/circuit_breaker.py`, `hummbl_governance/health_probe.py`, `hummbl_governance/lifecycle.py` |
| Implement fail-safe mechanisms to prevent harm in critical situations | ✅ Kill-switch 4-mode halt (pause/stop/terminate/quarantine) + capability-fence boundary enforcement | `hummbl_governance/kill_switch.py`, `hummbl_governance/capability_fence.py` |
| Resist being compromised by unauthorised parties | ✅ Capability-fence sandbox + identity-registry authentication + delegation-token authorization | `hummbl_governance/capability_fence.py`, `hummbl_governance/identity.py`, `hummbl_governance/delegation.py` |
| Conduct rigorous testing and validation to ensure AI performs as accurately as intended (developer best practice — Validation) | ✅ Schema-validator input/output contract validation + output-validator policy gates | `hummbl_governance/schema_validator.py`, `hummbl_governance/output_validator.py` |

### Privacy and Security (Principle 3)

| Obligation | Coverage | Evidence |
|---|---|---|
| Implement automatic measures to prevent data privacy breaches (rigorous testing, monitoring, fail-safe mechanisms) | ✅ Output-validator PII/sensitive-data redaction gates + circuit-breaker breach-response fast-fail | `hummbl_governance/output_validator.py`, `hummbl_governance/circuit_breaker.py` |
| Obtain informed consent and define permissible uses of personal information | 🟡 Partial: identity-registry scopes data-use permissions; consent-collection workflow is org task | `hummbl_governance/identity.py`, `hummbl_governance/kernel/identity_engine.py` |
| Ensure data security and minimise potential harm, especially in high-risk areas (military, healthcare) | ✅ Capability-fence data-access restrictions + audit-log immutable access trail + kernel/law-engine policy enforcement | `hummbl_governance/capability_fence.py`, `hummbl_governance/audit_log.py`, `hummbl_governance/kernel/law_engine.py` |
| End-user right to request personal data deletion | ⚪ Boundary: data-deletion execution across organizational data stores is organizational, not software-addressable | |

### Inclusiveness (Principle 4)

| Obligation | Coverage | Evidence |
|---|---|---|
| Provide equal access to AI that addresses national needs and mitigates social gaps | ⚪ Boundary: equitable-access policy and national-needs prioritization are organizational/governmental | |
| Incorporate user feedback to improve AI results and embed in applications (developer best practice — User Feedback) | ✅ Reward-monitor feedback-signal tracking + convergence-guard feedback-loop detection | `hummbl_governance/reward_monitor.py`, `hummbl_governance/convergence_guard.py` |
| Ensure AI systems are inclusive for all stakeholders to prevent unequal access exacerbating social divides | 🟡 Partial: contract-net multi-stakeholder participation + reasoning-engine accessibility checks; social-divide mitigation is org policy | `hummbl_governance/contract_net.py`, `hummbl_governance/reasoning.py` |

### Transparency (Principle 5)

| Obligation | Coverage | Evidence |
|---|---|---|
| (a) Full disclosure that an AI system is being used in decision-making | ✅ Audit-log AI-use disclosure tuples + output-validator provenance-labeling (cross-ref EU AI Act Art. 50, South Korea Art. 31) | `hummbl_governance/audit_log.py`, `hummbl_governance/output_validator.py` |
| (b) Disclose the intended purpose of the AI system | ✅ Compliance-mapper purpose-declaration records + kernel/doctrine-engine intent registration | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/kernel/doctrine_engine.py` |
| (c) Provide information on training data and potential historical or social biases | ✅ Audit-log training-data provenance tuples + bias-disclosure records (cross-ref EU AI Act Art. 10) | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| (d) Disclose maintenance and assessment protocols for AI systems | 🟡 Partial: lifecycle state machine tracks maintenance states; protocol publication is org task | `hummbl_governance/lifecycle.py`, `hummbl_governance/health_probe.py` |
| (e) Provide mechanisms for challenging AI decisions | ✅ Audit-log challenge/redress tuples + compliance-mapper appeal-workflow records (cross-ref Colorado § 6-1-1704) | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Provide clear explanations and justifications for AI decisions (developer best practice — Transparency) | ✅ Reasoning-engine explanation generation + audit-log decision-trace records | `hummbl_governance/reasoning.py`, `hummbl_governance/audit_log.py` |

### Accountability (Principle 6)

| Obligation | Coverage | Evidence |
|---|---|---|
| Developers, owners, and operators accountable for system performance and compliance with governance and ethical principles | ✅ Delegation-token accountability assignment + kernel/authority-engine role-based responsibility + kernel/receipt-engine immutable receipts | `hummbl_governance/delegation.py`, `hummbl_governance/kernel/authority_engine.py`, `hummbl_governance/kernel/receipt_engine.py` |
| Address system purpose to avoid consequential harm (Accountability element 1) | ✅ Kernel/doctrine-engine intent registration + kernel/evidence-engine purpose validation | `hummbl_governance/kernel/doctrine_engine.py`, `hummbl_governance/kernel/evidence_engine.py` |
| Address technology capability to avoid consequential harm (Accountability element 2) | ✅ Capability-fence scope enforcement + schema-validator capability contracts | `hummbl_governance/capability_fence.py`, `hummbl_governance/schema_validator.py` |
| Address quality and reliability to avoid consequential harm (Accountability element 3) | ✅ Health-probe reliability metrics + output-validator quality gates + audit-log performance records | `hummbl_governance/health_probe.py`, `hummbl_governance/output_validator.py`, `hummbl_governance/audit_log.py` |
| Consider sensitive users to avoid consequential harm (Accountability element 4) | 🟡 Partial: reasoning-engine sensitivity checks flag vulnerable-user scenarios; sensitive-user classification is org task | `hummbl_governance/reasoning.py` |
| Policymakers should design legal framework assigning responsibility and mechanisms to stakeholders | ⚪ Boundary: legal-framework design is governmental, not software-addressable | |

### Pursuit of Human Benefit and Happiness (Principle 7)

| Obligation | Coverage | Evidence |
|---|---|---|
| Design AI to enhance societal values and prioritize human-centred values for betterment of individuals and communities | ✅ Kernel/doctrine-engine human-benefit intent validation + reward-monitor alignment-to-human-values tracking | `hummbl_governance/kernel/doctrine_engine.py`, `hummbl_governance/reward_monitor.py` |
| (a) Human-in-the-loop (HITL) — capability for human intervention in every decision cycle | ✅ Delegation-token human-oversight tokens + kernel/sequence_engine human-approval gates per cycle | `hummbl_governance/delegation.py`, `hummbl_governance/kernel/sequence_engine.py` |
| (b) Human-on-the-loop (HOTL) — human intervention during design cycle and monitoring of system operation | ✅ Health-probe continuous monitoring + audit-log human-review checkpoints + convergence-guard drift alerts | `hummbl_governance/health_probe.py`, `hummbl_governance/audit_log.py`, `hummbl_governance/convergence_guard.py` |
| (c) Human-in-command (HIC) — oversight of overall AI activity and ability to decide when and how to use the system | ✅ Kill-switch human-command halt + kernel/authority_engine human-override authority + lifecycle human-gated state transitions | `hummbl_governance/kill_switch.py`, `hummbl_governance/kernel/authority_engine.py`, `hummbl_governance/lifecycle.py` |
| Prevent harm or misuse of AI technology | ✅ Kill-switch quarantine mode + capability-fence misuse prevention + physical-governor harm-prevention for embodied AI | `hummbl_governance/kill_switch.py`, `hummbl_governance/capability_fence.py`, `hummbl_governance/physical_governor.py` |

### Developer/provider cross-cutting best practices

| Obligation | Coverage | Evidence |
|---|---|---|
| Incorporate ethical considerations into AI design and proactively identify/address ethical challenges (Ethical Considerations) | ✅ Kernel/doctrine-engine ethical-policy enforcement + stride_mapper threat-and-ethics assessment | `hummbl_governance/kernel/doctrine_engine.py`, `hummbl_governance/stride_mapper.py` |
| Continuously monitor AI performance and impact to identify biases, risks, or unintended consequences (Ongoing Monitoring) | ✅ Reward-monitor drift detection + health-probe continuous liveness + convergence-guard unintended-consequence alerts | `hummbl_governance/reward_monitor.py`, `hummbl_governance/health_probe.py`, `hummbl_governance/convergence_guard.py` |
| End-user right to be informed about data collection | ✅ Audit-log data-collection disclosure tuples + compliance-mapper transparency records | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| End-user right to object to unconsented data usage | 🟡 Partial: identity-registry consent-scope enforcement flags unconsented use; objection workflow is org task | `hummbl_governance/identity.py`, `hummbl_governance/kernel/identity_engine.py` |
| End-user right to collective redress | ⚪ Boundary: collective-redress legal mechanism is governmental/legal, not software-addressable | |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| Fairness (Principle 1) | 3 | 2 | 1 | 0 |
| Reliability, Safety and Control (Principle 2) | 4 | 4 | 0 | 0 |
| Privacy and Security (Principle 3) | 4 | 2 | 1 | 1 |
| Inclusiveness (Principle 4) | 3 | 1 | 1 | 1 |
| Transparency (Principle 5) | 6 | 5 | 1 | 0 |
| Accountability (Principle 6) | 6 | 4 | 1 | 1 |
| Pursuit of Human Benefit and Happiness (Principle 7) | 5 | 5 | 0 | 0 |
| Developer/provider cross-cutting best practices | 5 | 3 | 1 | 1 |
| **Totals** | **36** | **26** | **6** | **4** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated. The AIGE are voluntary guidelines; mapping HUMMBL primitives to the seven principles demonstrates technical alignment, not statutory compliance.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Transparency overlaps EU AI Act Art. 50 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Transparency overlaps South Korea AI Basic Act Art. 31 — see [`south-korea-ai-basic-act.md`](./south-korea-ai-basic-act.md)
- Fairness/bias overlaps NIST AI RMF MAP — see [`nist-ai-rmf.md`](./nist-ai-rmf.md)
- Human oversight (HITL/HOTL/HIC) overlaps EU AI Act Art. 14 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Accountability overlaps ISO 42001 — see [`iso-42001.md`](./iso-42001.md)
- Privacy overlaps GDPR — see [`gdpr.md`](./gdpr.md)
- Risk management overlaps NIST AI RMF MEASURE — see [`nist-ai-rmf.md`](./nist-ai-rmf.md)
