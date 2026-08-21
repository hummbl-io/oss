# ISO/IEC 5338:2023 Coverage Matrix — HUMMBL

**Standard**: ISO/IEC 5338:2023 — Information technology — Artificial intelligence — AI system life cycle processes
**Effective**: 2023-12-20 (published)
**Source**: https://www.iso.org/standard/81118.html
**Last reviewed**: 2026-06-25
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is **not** an ISO 5338 conformity assessment body. ISO/IEC 5338:2023 is a **process standard** — it defines 33 life cycle processes (in 4 groups) for AI systems based on machine learning and heuristic systems, extending ISO/IEC/IEEE 15288 and ISO/IEC/IEEE 12207 with AI-specific additions. The standard is descriptive, not certifiable; an organization tailors and declares conformance to selected processes. HUMMBL contributes the technical primitives that implement or evidence individual process activities; the life cycle model, tailoring, and organizational process adoption remain the customer organization's responsibility.

## Scope summary

ISO/IEC 5338:2023 applies to AI systems based on machine learning and heuristic systems, agnostic to industry, product, service, or organization size. It defines 33 processes across four groups: Agreement (2), Organizational project-enabling (6), Technical management (8), and Technical (17). Processes are classified into three types: **Generic** (7, identical to 15288/12207), **Modified** (23, adapted with AI-specific particularities), and **AI-specific** (3 — knowledge acquisition, AI data engineering, continuous validation). The standard references ISO/IEC 22989 (AI concepts and terminology) and ISO/IEC 23053 (AI framework using ML). It complements ISO/IEC 42001 (AIMS) by providing the technical lifecycle process detail that 42001 leaves at the management level.

## Obligations + coverage

### Agreement processes (Clause 6.1)

| Process | Coverage | Evidence |
|---|---|---|
| 6.1.1 Acquisition process — acquiring an AI system from external suppliers | ⚪ Boundary: procurement and supplier contracting are organizational, not software-addressable | |
| 6.1.2 Supply process — supplying an AI system to acquirers | ⚪ Boundary: supply-chain contracting and delivery are organizational | |

### Organizational project-enabling processes (Clause 6.2)

| Process | Coverage | Evidence |
|---|---|---|
| 6.2.1 Life cycle model management — defining and maintaining the AI life cycle model | 🟡 Partial: `GovernanceLifecycle` provides a composed lifecycle orchestrator (Govern/Map/Measure/Manage); org tailoring and model selection are organizational | `hummbl_governance/lifecycle.py`, `hummbl_governance/compliance_mapper.py` |
| 6.2.2–6.2.3 Infrastructure + portfolio management — provisioning compute, tooling, and project portfolio | 🟡 Partial: cost-governor enforces compute budgets; infrastructure and portfolio decisions are organizational | `hummbl_governance/cost_governor.py` |
| 6.2.4 Human resource management — roles, competence, staffing for AI projects | ⚪ Boundary: HR management is organizational | |
| 6.2.5–6.2.6 Quality + knowledge management — quality policies and institutional knowledge for AI | ✅ Audit-log + coordination-bus provide institutional memory and quality-evidence substrate (cross-ref ISO 42001 A.4.7) | `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py` |

### Technical management processes (Clause 6.3)

| Process | Coverage | Evidence |
|---|---|---|
| 6.3.1–6.3.2 Project planning + assessment/control — planning and oversight of AI projects | 🟡 Partial: lifecycle status snapshot + health-probe monitoring; project planning is organizational | `hummbl_governance/lifecycle.py`, `hummbl_governance/health_probe.py` |
| 6.3.3–6.3.4 Decision + risk management — structured decisions and AI risk treatment | ✅ Reasoning engine + authority engine for decisions; STRIDE mapper + audit-log for risk identification and treatment (cross-ref NIST AI RMF MAP/MEASURE) | `hummbl_governance/reasoning.py`, `hummbl_governance/kernel/authority_engine.py`, `hummbl_governance/stride_mapper.py`, `hummbl_governance/audit_log.py` |
| 6.3.5–6.3.6 Configuration + information management — version control and information assets | ✅ Audit-log append-only trail + schema-validator for configuration integrity; coordination-bus for information dissemination | `hummbl_governance/audit_log.py`, `hummbl_governance/schema_validator.py`, `hummbl_governance/coordination_bus.py` |
| 6.3.7–6.3.8 Measurement + quality assurance — quantitative metrics and QA for AI systems | ✅ Cost-governor + health-probe for measurement; output-validator + compliance-mapper for QA gates (cross-ref ISO 42001 Clause 9) | `hummbl_governance/cost_governor.py`, `hummbl_governance/health_probe.py`, `hummbl_governance/output_validator.py`, `hummbl_governance/compliance_mapper.py` |

### Technical processes (Clause 6.4)

| Process | Coverage | Evidence |
|---|---|---|
| 6.4.1 Business or mission analysis — identifying AI system need and objectives | 🟡 Partial: INTENT tuple chain captures objectives; business analysis authorship is organizational | `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py` |
| 6.4.2–6.4.3 Stakeholder needs + system requirements definition — eliciting and specifying requirements | ✅ Requirements tuple + INTENT chain + schema-validator for specification conformance (cross-ref ISO 42001 A.6.2.2) | `hummbl_governance/audit_log.py`, `hummbl_governance/schema_validator.py` |
| 6.4.4–6.4.6 Architecture, design, and system analysis — defining structure and evaluating trade-offs | 🟡 Partial: design-doc tuple + signed audit trail; architecture authorship is engineering | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| 6.4.7 Knowledge acquisition process (AI-specific) — acquiring and curating knowledge for heuristic/ML systems | 🟡 Partial: knowledge-base + audit-log for knowledge provenance; knowledge elicitation methodology is organizational | `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py` |
| 6.4.8 AI data engineering process (AI-specific) — data acquisition, preparation, bias reduction, provenance | ✅ Dataset tuple + provenance chain + schema-validator for data quality (cross-ref ISO 42001 A.7, EU AI Act Art. 10) | `hummbl_governance/audit_log.py`, `hummbl_governance/schema_validator.py` |
| 6.4.9 Implementation process (modified) — model training, algorithm selection, knowledge programming | ✅ Lifecycle-stage tuples + per-stage gates + audit trail for implementation activities (cross-ref ISO 42001 A.6.1.3) | `hummbl_governance/lifecycle.py`, `hummbl_governance/audit_log.py` |
| 6.4.10 Integration process — assembling AI system components | ✅ Coordination-bus + convergence-guard for multi-agent integration and consistency | `hummbl_governance/coordination_bus.py`, `hummbl_governance/convergence_guard.py` |
| 6.4.11 Verification process — confirming the AI system meets specified requirements | ✅ Output-validator + schema-validator for verification gates; 1168-test CI suite as evidence (cross-ref ISO 42001 A.6.2.4) | `hummbl_governance/output_validator.py`, `hummbl_governance/schema_validator.py` |
| 6.4.12 Transition process — deploying the AI system to the operational environment | ✅ Deployment tuple + change-management primitives + kill-switch for safe rollout (cross-ref ISO 42001 A.6.2.5) | `hummbl_governance/audit_log.py`, `hummbl_governance/kill_switch.py`, `hummbl_governance/coordination_bus.py` |
| 6.4.13 Validation process — confirming the AI system meets stakeholder needs in intended context | ✅ Output-validator + compliance-mapper for validation against intended-use tuples (cross-ref ISO 42001 A.6.2.4) | `hummbl_governance/output_validator.py`, `hummbl_governance/compliance_mapper.py` |
| 6.4.14 Continuous validation process (AI-specific) — ongoing validation of deployed models for drift | ✅ Health-probe + reward-monitor for drift detection and continuous performance monitoring (cross-ref NIST AI RMF MEASURE) | `hummbl_governance/health_probe.py`, `hummbl_governance/reward_monitor.py` |
| 6.4.15 Operation process — running the AI system in production | ✅ Lifecycle operation-mode + coordination-bus for runtime governance + circuit-breaker for fast-fail (cross-ref ISO 42001 A.6.2.6) | `hummbl_governance/lifecycle.py`, `hummbl_governance/coordination_bus.py`, `hummbl_governance/circuit_breaker.py` |
| 6.4.16 Maintenance process (modified) — updates, retraining, corrective action for AI systems | ✅ Audit-log change trail + lifecycle re-entry gates + capability-fence for controlled updates | `hummbl_governance/audit_log.py`, `hummbl_governance/lifecycle.py`, `hummbl_governance/capability_fence.py` |
| 6.4.17 Disposal process — decommissioning and retirement of the AI system | ✅ Kill-switch full-halt + audit-log retirement record + data-disposal tuples (cross-ref ISO 42001 A.6.2.5) | `hummbl_governance/kill_switch.py`, `hummbl_governance/audit_log.py` |

## Summary

| Section | Processes | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| Agreement (6.1) | 2 | 0 | 0 | 2 |
| Organizational project-enabling (6.2) | 4 | 1 | 2 | 1 |
| Technical management (6.3) | 4 | 3 | 1 | 0 |
| Technical (6.4) | 13 | 10 | 3 | 0 |
| **Totals** | **23** | **14** | **6** | **3** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- ISO/IEC 42001 AIMS lifecycle controls overlap — see [`iso-42001.md`](./iso-42001.md) Annex A.6
- NIST AI RMF MAP/MEASURE/MANAGE functions map to lifecycle stages — see [`nist-ai-rmf.md`](./nist-ai-rmf.md)
- EU AI Act Art. 10 (data governance) overlaps AI data engineering process — see [`eu-ai-act.md`](./eu-ai-act.md)
- ISO/IEC 22989 (AI concepts) and ISO/IEC 23053 (AI framework) are normative references
