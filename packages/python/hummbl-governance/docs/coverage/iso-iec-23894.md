# ISO/IEC 23894:2023 Coverage Matrix — HUMMBL

**Standard**: ISO/IEC 23894:2023 — Information technology — Artificial intelligence — Guidance on risk management
**Effective**: February 2023 (published)
**Source**: https://www.iso.org/standard/77304.html
**Last reviewed**: 2026-06-25
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not an ISO/IEC 23894 conformity-assessment body and does not certify AI risk management programs. ISO/IEC 23894 is a **guidance** standard (not a certifiable management-system standard like ISO/IEC 42001) that operationalises ISO 31000:2018 for AI-specific risk. It carries normative force through approximately 95 "should" obligations rather than mandatory "shall" requirements. The organizational risk-management framework, leadership commitment, stakeholder consultation, and risk-criteria definitions remain the customer organization's responsibility. HUMMBL maps technical primitives to the standard's risk-identification, assessment, treatment, monitoring, and reporting processes.

## Scope summary

ISO/IEC 23894:2023 applies to any organization that develops, produces, deploys, or uses products, systems, and services utilizing AI. It mirrors the clause structure of ISO 31000:2018 — Principles (Clause 4), Framework (Clause 5), and Processes (Clause 6) — overlaying AI-specific guidance against each sub-clause. The standard imports terminology from ISO 31000:2018, ISO Guide 73:2009, and ISO/IEC 22989:2022 rather than defining its own terms. Annex A provides 12 common AI-related objective categories, Annex B provides 8 AI risk-source categories, and Annex C maps risk-management activities against the AI system lifecycle. The standard is designed to integrate with ISO/IEC 42001 (operationalising Clauses 6.1.2 AI risk assessment and 6.1.3 AI risk treatment) and aligns with NIST AI RMF.

## Obligations + coverage

### Principles of AI risk management (Clause 4)

ISO 31000:2018 defines eight risk-management principles; ISO/IEC 23894 adds AI-specific guidance to five of them.

| Principle | Guidance | Coverage | Evidence |
|---|---|---|---|
| Inclusive (Cl. 4) — stakeholders help identify risks in data collection, define fairness criteria, identify bias, determine human-oversight needs | AI systems affect a wider stakeholder set than traditional software; structured dialog with affected parties is expected | ✅ Stakeholder-consultation tuple + impact-assessment template captures affected-party input (cross-ref EU AI Act Art. 27 FRIA) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Dynamic (Cl. 4) — risks can emerge, change, or disappear as AI systems learn, adapt, and optimize | Continuous-learning systems create moving risk targets; risk management must anticipate and detect changes | ✅ Convergence-drift detection + reward-signal monitoring + health-probe liveness checks surface behavioral change | `hummbl_governance/convergence_guard.py`, `hummbl_governance/reward_monitor.py`, `hummbl_governance/health_probe.py` |
| Best Available Information (Cl. 4) — risk decisions based on best available evidence; AI introduces uncertainty in data, models, and emergent behavior | Inputs are often incomplete; organizations should document evidence limitations | ✅ Evidence-engine requires typed evidence tuples with provenance + confidence before authority decisions | `hummbl_governance/kernel/evidence_engine.py`, `hummbl_governance/audit_log.py` |
| Human and Cultural Factors (Cl. 4) — AI risk management considers human behavior, oversight capacity, and organizational culture | Human oversight capabilities and cultural readiness affect risk outcomes | ✅ Human-oversight delegation token + capability-aware delegation with expiry (cross-ref EU AI Act Art. 14) | `hummbl_governance/delegation.py`, `hummbl_governance/identity.py` |
| Continual Improvement (Cl. 4) — risk management learns from experience and outcomes; AI systems require iterative refinement | Post-incident learning feeds back into risk criteria and controls | ✅ Lifecycle state machine + nonconformity tuples + corrective-action tracking drive iterative improvement | `hummbl_governance/lifecycle.py`, `hummbl_governance/audit_log.py` |

### Framework — leadership, integration, design (Clause 5)

| Clause | Guidance | Coverage | Evidence |
|---|---|---|---|
| 5.2 Leadership and commitment — top management should consider public statements about AI risk-management commitment | Public accountability anchor for AI trust | ⚪ Boundary: executive public statements are organizational, not software-addressable | |
| 5.4.3 Assigning organizational roles, authorities, responsibilities, and accountabilities — named individuals with authority to address AI risks | Named people (not committees) with clear authority for AI risk monitoring | ✅ Identity registry + delegation-token issuance with scoped authority + named-contact tuples | `hummbl_governance/identity.py`, `hummbl_governance/delegation.py`, `hummbl_governance/kernel/authority_engine.py` |
| 5.4.4 Allocating resources — resources for AI risk management including expertise, tools, and compute budgets | Resource allocation for risk-management activities | ✅ Cost-governor budget enforcement + admission-control resource gating | `hummbl_governance/cost_governor.py`, `hummbl_governance/kernel/admission_control.py` |
| 5.4.5 Establishing communication and consultation — mechanisms for internal and external stakeholder communication on AI risk | Two-way communication channels for risk dialog | 🟡 Partial: coordination-bus publishes risk events to subscribers; external-stakeholder consultation is org task | `hummbl_governance/coordination_bus.py` |
| 5.7 Improvement — continual improvement of the framework, incorporating lessons learned | Framework-level improvement loop | ✅ Evolution-lineage tracking + lifecycle state transitions capture framework maturation | `hummbl_governance/lifecycle.py`, `hummbl_governance/audit_log.py` |

### Risk assessment — identification, analysis, evaluation (Clause 6.4)

| Clause | Guidance | Coverage | Evidence |
|---|---|---|---|
| 6.4.2 Risk identification — identify AI-specific risk sources using Annex B catalogue (data quality/bias, model opacity, emergent behavior, adversarial attacks, misuse, sociotechnical impacts) | Structured identification of AI risk sources, events, and scenarios | ✅ STRIDE threat-modeling mapper + risk-identification tuple type with AI-specific threat categories | `hummbl_governance/stride_mapper.py`, `hummbl_governance/audit_log.py` |
| 6.4.3 Risk analysis — analyze risk sources, events, controls, and consequences; consider combinations and sequences of multiple risks | Qualitative and quantitative analysis of likelihood and impact | ✅ Reasoning engine evaluates risk scenarios with evidence-weighted analysis + convergence detection for compound risks | `hummbl_governance/reasoning.py`, `hummbl_governance/convergence_guard.py` |
| 6.4.4 Risk evaluation — compare analysis results against risk criteria to determine which risks require treatment and priority | Risk criteria thresholds drive treatment decisions | ✅ Compliance-mapper risk-criteria evaluation + schema-validated threshold tuples | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/schema_validator.py` |
| 6.3.4 Defining risk criteria — establish quantitative and qualitative criteria covering data, software, models, physical extensions, and human-in-the-loop | AI-specific criteria spanning the full system uncertainty surface | ✅ Law-engine policy-as-code encodes risk criteria + schedule-engine triggers re-evaluation on architecture/data change | `hummbl_governance/kernel/law_engine.py`, `hummbl_governance/kernel/schedule_engine.py` |

### Risk treatment (Clause 6.5)

| Clause | Guidance | Coverage | Evidence |
|---|---|---|---|
| 6.5.2 Selection of risk treatment options — avoidance, mitigation (technical + procedural controls), transfer, acceptance; human oversight as a treatment | Treatment selection informed by risk evaluation and organizational risk appetite | ✅ Risk-treatment tuple type + kill-switch 4-mode halt (avoidance) + circuit-breaker fast-fail (mitigation) | `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py`, `hummbl_governance/audit_log.py` |
| 6.5.3 Preparing and implementing risk treatment plans — documented plans specifying controls, owners, target dates, and evidence | Treatment plans with responsible owners and completion targets | ✅ Treatment-plan tuple with owner identity + schedule-engine deadline tracking + receipt-engine execution evidence | `hummbl_governance/kernel/schedule_engine.py`, `hummbl_governance/kernel/receipt_engine.py`, `hummbl_governance/identity.py` |
| Human oversight as risk treatment — particular attention to human oversight mechanisms as a treatment option | Oversight controls including halt, override, and escalation | ✅ Delegation-token scoped authority + kill-switch human-halt mode + capability-fence action restriction | `hummbl_governance/delegation.py`, `hummbl_governance/kill_switch.py`, `hummbl_governance/capability_fence.py` |

### Monitoring, review, recording, reporting (Clauses 6.2, 6.6, 6.7)

| Clause | Guidance | Coverage | Evidence |
|---|---|---|---|
| 6.2 Communication and consultation — ongoing risk communication with stakeholders throughout the process | Continuous risk dialog, not one-time notification | ✅ Coordination-bus event publishing + lamport-clock causal ordering of risk messages | `hummbl_governance/coordination_bus.py`, `hummbl_governance/lamport_clock.py` |
| 6.6 Monitoring and review — continuous monitoring of AI system behavior, risk indicators, and control effectiveness; detect drift and emergent behavior | Ongoing vigilance for dynamic AI systems rather than periodic review | ✅ Health-probe liveness + reward-monitor behavioral drift + convergence-guard anomaly detection + output-validator gate | `hummbl_governance/health_probe.py`, `hummbl_governance/reward_monitor.py`, `hummbl_governance/convergence_guard.py`, `hummbl_governance/output_validator.py` |
| 6.7 Recording and reporting — document risk-management decisions, retain evidence, report to relevant stakeholders in audience-appropriate form | Immutable records supporting audits and stakeholder reporting | ✅ Immutable append-only audit log + compliance-report generator + sequence-engine ordered event chain | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py`, `hummbl_governance/kernel/sequence_engine.py` |
| Annex C — risk-management activities mapped against AI system lifecycle stages | Lifecycle-aligned risk process as a state machine | ✅ Lifecycle state machine with risk-activity hooks per stage + doctrine-engine policy enforcement per state | `hummbl_governance/lifecycle.py`, `hummbl_governance/kernel/doctrine_engine.py` |

## Summary

| Section | Guidance items | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| Principles (Cl. 4) | 5 | 5 | 0 | 0 |
| Framework (Cl. 5) | 5 | 3 | 1 | 1 |
| Risk assessment (Cl. 6.4) | 4 | 4 | 0 | 0 |
| Risk treatment (Cl. 6.5) | 3 | 3 | 0 | 0 |
| Monitoring, review, recording, reporting (Cl. 6.2, 6.6, 6.7, Annex C) | 4 | 4 | 0 | 0 |
| **Totals** | **21** | **19** | **1** | **1** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Parent standard ISO 31000:2018 (general risk management) — not separately covered; 23894 is the AI-specific annotation layer
- Management-system companion ISO/IEC 42001:2023 — see [`iso-42001.md`](./iso-42001.md)
- Terminology source ISO/IEC 22989:2022 — see [`iso-iec-22989.md`](./iso-iec-22989.md)
- Risk-management process overlaps NIST AI RMF (IDENTIFY, MEASURE, MANAGE) — see [`nist-ai-rmf.md`](./nist-ai-rmf.md)
- Human oversight overlaps EU AI Act Art. 14 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Impact assessment overlaps EU AI Act Art. 27 (FRIA) — see [`eu-ai-act.md`](./eu-ai-act.md)
- STRIDE threat modeling for risk identification — see [`stride.md`](./stride.md)
