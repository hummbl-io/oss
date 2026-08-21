# ISO/IEC 23053:2022 Coverage Matrix — HUMMBL

**Standard**: ISO/IEC 23053:2022 — Framework for Artificial Intelligence (AI) Systems Using Machine Learning (ML)
**Effective**: June 2022 (published 2022-06-20)
**Source**: https://www.iso.org/standard/74438.html
**Last reviewed**: 2026-06-25
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not an ISO/IEC conformity-assessment body and does not certify framework compliance. ISO/IEC 23053:2022 is a descriptive framework standard — it establishes a common terminology and conceptual model for ML-based AI systems, not prescriptive legal obligations. The standard describes ML system components (model, data, tools), ML approaches (supervised, unsupervised, reinforcement, etc.), and an ML pipeline (data acquisition through operation). Much of the standard's content is ML-platform engineering (algorithm selection, optimisation methods, evaluation metrics, data preparation) that falls outside HUMMBL's governance-primitive scope. This matrix maps HUMMBL primitives to the framework elements where governance, safety, oversight, and lifecycle controls are relevant, and marks purely ML-technical elements as boundary.

## Scope summary

ISO/IEC 23053:2022 establishes a framework for describing AI systems that use machine learning. It defines the ML system in terms of three components — model (Clause 6.3), data (Clause 6.4), and tools (Clause 6.5) — and describes six ML approaches (Clause 7): supervised, unsupervised, semi-supervised, self-supervised, reinforcement, and transfer learning. The standard's operational core is the ML pipeline (Clause 8), which spans data acquisition (8.2), data preparation (8.3), modelling (8.4), verification and validation (8.5), model deployment (8.6), and operation (8.7). Clause 8.1 identifies four cross-cutting aspects that apply across the entire pipeline: risk management and governance; security and privacy; accountability, transparency and explainability; and safety, resilience, robustness and fairness. Annex A provides example data flow and data use statements based on ISO/IEC 19944-1. The standard is applicable to all organizations implementing or using AI systems with ML, and serves as a foundational reference for the ISO/IEC JTC 1/SC 42 standards family.

## Obligations + coverage

### ML system components (Clause 6)

| Obligation | Coverage | Evidence |
|---|---|---|
| Define the task — establish goals, requirements, input/output formats for the ML system (6.1–6.2) | ✅ Task-definition governance: contract-net task allocation, schedule-engine task ordering, sequence-engine step sequencing | `hummbl_governance/contract_net.py`, `hummbl_governance/kernel/schedule_engine.py`, `hummbl_governance/kernel/sequence_engine.py` |
| Model — trained mathematical construct generating inferences; includes retraining and continuous learning with guard-rails (6.3) | 🟡 Partial: HUMMBL governs model I/O via schema validation and output validation, and enforces guard-rails via capability fence; model internals, training, and weight optimization are out of scope | `hummbl_governance/schema_validator.py`, `hummbl_governance/output_validator.py`, `hummbl_governance/capability_fence.py` |
| Data — training, validation, test, and production datasets with disjointness requirements (6.4) | 🟡 Partial: HUMMBL captures production data as evidence tuples and audit-log artifacts; dataset partitioning, training/validation/test management are ML-platform concerns | `hummbl_governance/kernel/evidence_engine.py`, `hummbl_governance/audit_log.py` |
| Data preparation tools — formatting, cleansing, de-identification, imputation, normalisation (6.5.2) | ⚪ Boundary: data preparation is an ML-platform engineering activity, not a governance primitive | |
| ML algorithms and optimisation methods — SVM, decision trees, neural networks, gradient descent, Newton's method (6.5.3–6.5.4) | ⚪ Boundary: algorithm selection and optimisation-method configuration are ML-platform concerns, not governance primitives | |
| ML evaluation metrics — precision, recall, F1, ROC/AUC, MAE, RMSE, confusion matrix (6.5.5) | 🟡 Partial: HUMMBL monitors system health and reward signals via health-probe and reward-monitor; ML-specific metric computation (ROC, F1, etc.) is out of scope | `hummbl_governance/health_probe.py`, `hummbl_governance/reward_monitor.py` |

### ML approaches (Clause 7)

| Obligation | Coverage | Evidence |
|---|---|---|
| Supervised, unsupervised, semi-supervised, and self-supervised learning approaches (7.2–7.5) | ⚪ Boundary: ML training-paradigm selection and execution are ML-platform engineering decisions, not governance primitives | |
| Reinforcement learning — agent learns by maximizing reward through environmental interaction (7.6) | 🟡 Partial: HUMMBL's reward-monitor governs reward signals and detects reward-hacking or misalignment in RL-like agents; RL training internals are out of scope | `hummbl_governance/reward_monitor.py` |
| Transfer learning — reusing a pre-trained model for a new task (7.7) | ⚪ Boundary: model-reuse and knowledge-transfer decisions are ML-platform concerns, not governance primitives | |

### ML pipeline — data acquisition and preparation (Clause 8.2–8.3)

| Obligation | Coverage | Evidence |
|---|---|---|
| Data acquisition — identify sources, acquire representative data, ensure appropriateness to business purpose (8.2) | 🟡 Partial: HUMMBL's evidence engine captures data provenance and audit log records data lineage; data sourcing, procurement, and representativeness analysis are organizational tasks | `hummbl_governance/kernel/evidence_engine.py`, `hummbl_governance/audit_log.py` |
| Data preparation — cleansing, de-identification, wrangling, imputation, normalisation, labelling (8.3) | ⚪ Boundary: data preparation is an ML-platform engineering activity; HUMMBL does not manage data-cleansing or labelling pipelines | |
| Dataset splitting — training, validation, and test sets must be disjoint; distribution alignment with production data (8.3) | ⚪ Boundary: dataset partitioning and statistical-distribution management are ML-platform concerns, not governance primitives | |

### ML pipeline — modelling and validation (Clause 8.4–8.5)

| Obligation | Coverage | Evidence |
|---|---|---|
| Feature engineering and algorithm selection — encoding, dimensionality reduction, feature selection, algorithm choice (8.4) | ⚪ Boundary: feature engineering and algorithm selection are ML-platform engineering activities, not governance primitives | |
| Model training and hyperparameter tuning — fitting model to training data, cross-validation, model selection (8.4) | ⚪ Boundary: model training and hyperparameter optimization are ML-platform concerns, not governance primitives | |
| Model evaluation — compare predictions on test data to actual labels using evaluation metrics (8.5) | 🟡 Partial: HUMMBL's output validator validates generated outputs against expected schemas; ML-specific test-data evaluation and metric computation are out of scope | `hummbl_governance/output_validator.py`, `hummbl_governance/health_probe.py` |
| System validation — verify trained model meets stakeholder needs and initial environmental assumptions (8.5) | ✅ Compliance mapper maps controls to stakeholder expectations; schema validator validates I/O contracts against requirements | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/schema_validator.py` |

### ML pipeline — deployment and operation (Clause 8.6–8.7)

| Obligation | Coverage | Evidence |
|---|---|---|
| Model deployment — packaging, run-time environment, optimisation for target platform (8.6) | 🟡 Partial: HUMMBL's admission control gates system deployment and lifecycle manages deployment state; model packaging and runtime optimisation are ML-platform concerns | `hummbl_governance/kernel/admission_control.py`, `hummbl_governance/lifecycle.py` |
| Operation — model used in batch or continuous mode on production data; outputs sent to applications or humans (8.7) | ✅ Lifecycle operational-state management + coordination-bus execution orchestration + output validation on production outputs | `hummbl_governance/lifecycle.py`, `hummbl_governance/coordination_bus.py`, `hummbl_governance/output_validator.py` |
| Maintenance and update — retraining with current data, algorithmic changes, model updates (8.7) | 🟡 Partial: HUMMBL's lifecycle manages update transitions and kill-switch can halt for updates; retraining execution and model-update pipelines are ML-platform concerns | `hummbl_governance/lifecycle.py`, `hummbl_governance/kill_switch.py` |
| Monitoring — detect data drift, concept drift, poor generalization; continuous-learning monitoring with guard-rails (8.7) | ✅ Health-probe drift detection + reward-monitor performance tracking + convergence-guard multi-agent stability + capability-fence guard-rails | `hummbl_governance/health_probe.py`, `hummbl_governance/reward_monitor.py`, `hummbl_governance/convergence_guard.py`, `hummbl_governance/capability_fence.py` |

### Cross-cutting aspects (Clause 8.1)

| Obligation | Coverage | Evidence |
|---|---|---|
| Risk management and governance — applies across entire ML pipeline (8.1) | ✅ Compliance mapper maps controls to frameworks + STRIDE threat mapper + audit-log risk-event recording (cross-ref NIST AI RMF, ISO/IEC 23894) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/stride_mapper.py`, `hummbl_governance/audit_log.py` |
| Security and privacy — applies across entire ML pipeline (8.1) | ✅ Capability fence enforces security boundaries + identity registry authenticates agents + STRIDE mapper identifies threats (cross-ref ISO/IEC 27001) | `hummbl_governance/capability_fence.py`, `hummbl_governance/identity.py`, `hummbl_governance/stride_mapper.py` |
| Accountability, transparency, and explainability — applies across entire ML pipeline (8.1) | ✅ Immutable audit log + compliance-report generator + reasoning-engine inference traces + receipt-engine verifiable execution evidence | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py`, `hummbl_governance/reasoning.py`, `hummbl_governance/kernel/receipt_engine.py` |
| Safety, resilience, robustness, and fairness — applies across entire ML pipeline (8.1) | ✅ Kill-switch 4-mode halt + circuit-breaker fast-fail + output-validator robustness guards + convergence-guard resilience (cross-ref EU AI Act Art. 14–15) | `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py`, `hummbl_governance/output_validator.py`, `hummbl_governance/convergence_guard.py` |

### Data flow and accountability (Annex A)

| Obligation | Coverage | Evidence |
|---|---|---|
| Data flow descriptions — describe data flows through ML pipeline phases per Figure 13 (Annex A.2) | 🟡 Partial: HUMMBL's audit log records data-flow events with Lamport-clock ordering; ISO/IEC 19944-1 formatted data-flow diagrams are not generated | `hummbl_governance/audit_log.py`, `hummbl_governance/lamport_clock.py` |
| Data use statements — formulate data use statements per ISO/IEC 19944-1 format for accountability and transparency (Annex A.3) | 🟡 Partial: HUMMBL's evidence engine captures data provenance and audit log records data usage; ISO/IEC 19944-1 statement format generation is not implemented | `hummbl_governance/kernel/evidence_engine.py`, `hummbl_governance/audit_log.py` |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| ML system components (Clause 6) | 6 | 1 | 3 | 2 |
| ML approaches (Clause 7) | 3 | 0 | 1 | 2 |
| ML pipeline — data acquisition and preparation (8.2–8.3) | 3 | 0 | 1 | 2 |
| ML pipeline — modelling and validation (8.4–8.5) | 4 | 1 | 1 | 2 |
| ML pipeline — deployment and operation (8.6–8.7) | 4 | 2 | 2 | 0 |
| Cross-cutting aspects (Clause 8.1) | 4 | 4 | 0 | 0 |
| Data flow and accountability (Annex A) | 2 | 0 | 2 | 0 |
| **Totals** | **26** | **8** | **10** | **8** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Terminology baseline is ISO/IEC 22989:2022 — see [`iso-iec-22989.md`](./iso-iec-22989.md)
- Risk management cross-cutting aspect overlaps ISO/IEC 23894 and NIST AI RMF — see [`iso-iec-23894.md`](./iso-iec-23894.md), [`nist-ai-rmf.md`](./nist-ai-rmf.md)
- Safety and oversight cross-cutting aspect overlaps EU AI Act Arts. 14–15 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Security cross-cutting aspect overlaps ISO/IEC 27001 and STRIDE — see [`iso-27001.md`](./iso-27001.md), [`stride.md`](./stride.md)
- Accountability and transparency overlaps South Korea AI Basic Act Art. 31 — see [`south-korea-ai-basic-act.md`](./south-korea-ai-basic-act.md)
- AI management system context overlaps ISO/IEC 42001 AIMS — see [`iso-42001.md`](./iso-42001.md)
