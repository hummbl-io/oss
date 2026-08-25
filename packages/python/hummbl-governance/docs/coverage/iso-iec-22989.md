# ISO/IEC 22989:2022 Coverage Matrix — HUMMBL

**Standard**: ISO/IEC 22989:2022 — Information technology — Artificial intelligence — Artificial intelligence concepts and terminology
**Effective**: July 2022 (published)
**Source**: https://www.iso.org/standard/74296.html
**Last reviewed**: 2026-06-25
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not an ISO/IEC conformity-assessment body and does not certify terminology compliance. ISO/IEC 22989:2022 is a terminology standard — it defines concepts and vocabulary, not prescriptive obligations. This matrix maps how HUMMBL's type system, governance primitives, and operational terminology align with the standard's defined concepts. Where HUMMBL implements a concept directly, the mapping is marked ✅; partial alignment is 🟡; concepts outside HUMMBL's governance scope (e.g., ML model internals, training-data pipelines) are marked ⚪.

## Scope summary

ISO/IEC 22989:2022 establishes a common vocabulary for artificial intelligence. It defines core concepts across seven term categories (§3.1 AI, §3.2 data, §3.3 machine learning, §3.4 neural networks, §3.5 trustworthiness, §3.6 NLP, §3.7 computer vision), describes AI concepts (§5) including autonomy, agents, trustworthiness characteristics, and the strong/weak-to-general/narrow distinction, specifies an AI system lifecycle model (§6) with nine stages, and provides a functional overview (§7) and ecosystem framing (§8). The standard serves as the terminology baseline for the ISO/IEC JTC 1/SC 42 family, underpinning ISO/IEC 23894 (risk management), ISO/IEC 42001 (AIMS), and ISO/IEC 24028 (trustworthiness overview).

## Concepts + coverage

### Core AI system concepts (§3.1, §5.2–5.3)

| Concept | Coverage | Evidence |
|---|---|---|
| AI system (§3.1.4) — engineered system that generates outputs for human-defined objectives | ✅ HUMMBL models AI systems as governed agents with identity, authority, and receipt-bound execution | `hummbl_governance/kernel/identity_engine.py`, `hummbl_governance/identity.py`, `hummbl_governance/kernel/authority_engine.py` |
| AI agent (§3.1.1) — entity that perceives its environment and takes action to achieve goals | ✅ Agent registry + delegation-token model + contract-net task allocation | `hummbl_governance/identity.py`, `hummbl_governance/delegation.py`, `hummbl_governance/contract_net.py` |
| AI model (§3.1.23) — representation of data, knowledge, or processes used to conduct tasks | 🟡 Partial: HUMMBL governs model I/O via schema validation and output validation but does not model or inspect model internals | `hummbl_governance/schema_validator.py`, `hummbl_governance/output_validator.py` |
| AI task (§3.1.35) — activity an AI system is designed to conduct | ✅ Task scheduling, contract-net delegation, and sequence-engine ordering | `hummbl_governance/kernel/schedule_engine.py`, `hummbl_governance/contract_net.py`, `hummbl_governance/kernel/sequence_engine.py` |
| Inference (§3.1.17) — reasoning by which conclusions are derived from known premises | ✅ Reasoning engine with premise-to-conclusion trace generation | `hummbl_governance/reasoning.py` |
| General vs. narrow AI (§5.2) — distinction between broadly capable and task-specific systems | ⚪ Boundary: capability-scope classification is an organizational design decision, not a governance primitive | |

### Data and machine learning concepts (§3.2–3.3, §5.10–5.12)

| Concept | Coverage | Evidence |
|---|---|---|
| Data (§3.2, §5.10) — information used by AI systems for training, validation, or operation | 🟡 Partial: HUMMBL captures data as evidence tuples and audit-log artifacts but does not manage training-data pipelines or datasets | `hummbl_governance/kernel/evidence_engine.py`, `hummbl_governance/audit_log.py` |
| Machine learning (§3.3.5) — process of optimizing model parameters from data | ⚪ Boundary: ML training is outside HUMMBL's governance-primitive scope; HUMMBL governs agent behavior, not model optimization | |
| Training data / trained model / validation and test data (§5.11.6–5.11.8) — data partitions and resulting model artifact | ⚪ Boundary: dataset partitioning and model artifact management are ML-platform concerns, not governance primitives | |
| Retraining (§5.11.9) — updating a trained model with new data | ⚪ Boundary: retraining triggers are an operational/ML-platform decision; HUMMBL does not manage model-update pipelines | |
| Knowledge (§3.1.21) — information organized for reasoning and inference | ✅ Evidence engine stores structured knowledge as evidence tuples; reasoning engine consumes knowledge for inference | `hummbl_governance/kernel/evidence_engine.py`, `hummbl_governance/reasoning.py` |

### Trustworthiness characteristics (§3.5, §5.15)

| Concept | Coverage | Evidence |
|---|---|---|
| Trustworthiness (§3.5.16) — ability to meet stakeholder expectations in a verifiable way | ✅ Receipt engine produces verifiable execution evidence; compliance mapper maps controls to stakeholder expectations | `hummbl_governance/kernel/receipt_engine.py`, `hummbl_governance/compliance_mapper.py` |
| AI robustness (§5.15.2) — ability to maintain performance under perturbation or unexpected input | ✅ Circuit-breaker fast-fail on anomaly + output validator guards on unexpected outputs | `hummbl_governance/circuit_breaker.py`, `hummbl_governance/output_validator.py` |
| AI reliability (§5.15.3) — performance consistency across lifecycle phases | ✅ Health-probe continuous monitoring + lifecycle state tracking | `hummbl_governance/health_probe.py`, `hummbl_governance/lifecycle.py` |
| AI resilience (§5.15.4) — recovery and continued operation under adverse conditions | ✅ Circuit-breaker recovery + convergence guard for multi-agent stability | `hummbl_governance/circuit_breaker.py`, `hummbl_governance/convergence_guard.py` |
| AI controllability (§3.5.x) — property allowing human or external agent to intervene in system functioning | ✅ Kill-switch 4-mode halt + delegation-token human-oversight model | `hummbl_governance/kill_switch.py`, `hummbl_governance/delegation.py` |
| AI explainability (§5.15.6) — degree to which an AI system's outputs can be understood | 🟡 Partial: reasoning engine produces inference traces and audit log records decisions; deep model-internal explainability is out of scope | `hummbl_governance/reasoning.py`, `hummbl_governance/audit_log.py` |
| AI predictability (§5.15.7) — expectation that AI system behavior is consistent with expectations | ✅ Output validator enforces expected output schemas + schema validator validates I/O contracts | `hummbl_governance/output_validator.py`, `hummbl_governance/schema_validator.py` |
| Transparency (§3.5.15) — communication of activities and decisions to stakeholders in an accessible manner | ✅ Immutable audit log + compliance-report generator + provenance labeling | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Safety (§5.15.x) — absence of unreasonable harm to persons or property | ✅ Kill-switch + circuit-breaker + physical-governor kinematic limits + capability fence | `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py`, `hummbl_governance/physical_governor.py`, `hummbl_governance/capability_fence.py` |
| Security (§5.15.x) — confidentiality, integrity, availability in AI contexts | ✅ Capability fence + identity registry + STRIDE threat mapper | `hummbl_governance/capability_fence.py`, `hummbl_governance/identity.py`, `hummbl_governance/stride_mapper.py` |

### AI system lifecycle (§6)

| Concept | Coverage | Evidence |
|---|---|---|
| AI system lifecycle model (§6.1) — framework of stages from inception to retirement | ✅ Lifecycle state machine with governed transitions across all stages | `hummbl_governance/lifecycle.py` |
| Inception + design and development (§6.2.2–6.2.3) — requirements, architecture, and model development | 🟡 Partial: admission control gates system entry; doctrine engine defines permissible behavior; ML development itself is out of scope | `hummbl_governance/kernel/admission_control.py`, `hummbl_governance/kernel/doctrine_engine.py` |
| Verification and validation (§6.2.4) — confirming system meets requirements and is fit for purpose | ✅ Schema validator validates I/O contracts + output validator validates generated outputs | `hummbl_governance/schema_validator.py`, `hummbl_governance/output_validator.py` |
| Deployment + operation and monitoring (§6.2.5–6.2.6) — release to production and ongoing observation | ✅ Admission control for deployment + health-probe + reward-monitor for operational monitoring | `hummbl_governance/kernel/admission_control.py`, `hummbl_governance/health_probe.py`, `hummbl_governance/reward_monitor.py` |
| Continuous validation + re-evaluation (§6.2.7–6.2.8) — ongoing assessment and periodic re-assessment | ✅ Health-probe drift detection + convergence guard + compliance-mapper periodic reassessment | `hummbl_governance/health_probe.py`, `hummbl_governance/convergence_guard.py`, `hummbl_governance/compliance_mapper.py` |
| Retirement (§6.2.9) — decommissioning and removal from service | ✅ Lifecycle retirement state + kill-switch termination mode + audit-log final-state recording | `hummbl_governance/lifecycle.py`, `hummbl_governance/kill_switch.py`, `hummbl_governance/audit_log.py` |

### Human oversight, autonomy, and automation (§5.13)

| Concept | Coverage | Evidence |
|---|---|---|
| Autonomy (§3.1.5) — system capable of modifying its domain or goal without external intervention | ✅ Authority engine defines autonomy boundaries + delegation tokens scope permitted autonomous action | `hummbl_governance/kernel/authority_engine.py`, `hummbl_governance/delegation.py` |
| Heteronomy (§3.1.6) — system operating under external intervention, control, or oversight | ✅ Kill-switch external halt + circuit-breaker external fast-fail + doctrine-engine external rule enforcement | `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py`, `hummbl_governance/kernel/doctrine_engine.py` |
| Automation (§3.1.7) — process or system functioning without human intervention | ✅ Sequence engine + coordination bus + lamport clock for automated multi-agent orchestration | `hummbl_governance/kernel/sequence_engine.py`, `hummbl_governance/coordination_bus.py`, `hummbl_governance/lamport_clock.py` |
| Human-in/on/over-the-loop (§5.13) — degrees of human involvement in AI system operation | ✅ Delegation-token model supports all three modes: in-the-loop (approval required), on-the-loop (review enabled), over-the-loop (oversight only) | `hummbl_governance/delegation.py`, `hummbl_governance/identity.py` |

## Summary

| Section | Concepts | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| Core AI system concepts (§3.1, §5.2–5.3) | 6 | 4 | 1 | 1 |
| Data and ML concepts (§3.2–3.3, §5.10–5.12) | 5 | 1 | 1 | 3 |
| Trustworthiness characteristics (§3.5, §5.15) | 10 | 9 | 1 | 0 |
| AI system lifecycle (§6) | 6 | 5 | 1 | 0 |
| Human oversight, autonomy, automation (§5.13) | 4 | 4 | 0 | 0 |
| **Totals** | **31** | **23** | **4** | **4** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Trustworthiness terminology underpins ISO/IEC 42001 AIMS — see [`iso-42001.md`](./iso-42001.md)
- Risk terminology feeds ISO/IEC 23894 and NIST AI RMF — see [`nist-ai-rmf.md`](./nist-ai-rmf.md)
- Lifecycle and human-oversight concepts overlap EU AI Act Arts. 14, 17 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Security terminology aligns with STRIDE threat modeling — see [`stride.md`](./stride.md)
- Transparency and explainability concepts overlap South Korea AI Basic Act Art. 31 — see [`south-korea-ai-basic-act.md`](./south-korea-ai-basic-act.md)
