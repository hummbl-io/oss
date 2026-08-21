# ISO/IEC 38507:2022 Coverage Matrix — HUMMBL

**Standard**: ISO/IEC 38507:2022 — Information technology — Governance of IT — Governance implications of the use of artificial intelligence by organizations
**Effective**: April 2022 (published 2022-04-08)
**Source**: https://www.iso.org/standard/56641.html
**Last reviewed**: 2026-06-25
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is **not** an ISO/IEC 38507 assessment body and does not provide governance consulting. ISO/IEC 38507 is guidance for **governing bodies** — boards, executive teams, senior leaders — not a certifiable management system standard. It addresses how organizational leadership should oversee AI use, ensure accountability, and maintain fit-for-purpose governance as AI adoption evolves. The governing body's responsibilities (strategy authorship, policy approval, committee structure, fiduciary duty) are organizational, not software-addressable. HUMMBL maps technical primitives to the governance-implication areas where runtime evidence, accountability chains, and oversight automation can support governing-body obligations.

## Scope summary

ISO/IEC 38507:2022 applies to any organization using or considering AI — public and private companies, government entities, and not-for-profits of any size. It complements the ISO/IEC 38500 IT governance series and the ISO/IEC 38505 data governance series, extending governance principles to AI-specific concerns: decision automation, data-driven problem-solving, adaptive systems, accountability structures, risk oversight, and ethical alignment. The standard is organized into Clause 4 (governance implications), Clause 5 (overview of AI and AI systems), and Clause 6 (policies to address AI use: oversight, decision-making, data, culture, compliance, risk), plus Annex A mapping to relevant governance standards.

## Obligations + coverage

### Clause 4 — Governance implications of organizational AI use (4.2–4.3)

| Obligation | Coverage | Evidence |
|---|---|---|
| 4.2 — Maintain governance when introducing AI; ensure existing governance remains fit-for-purpose as AI use changes | 🟡 Partial: lifecycle-stage tuples + per-stage governance gates provide fitness evidence; governance-structure review is org task | `hummbl_governance/lifecycle.py`, `hummbl_governance/audit_log.py` |
| 4.2 — Governing body ensures sufficient capabilities to deal with AI implications (skills, review frequency, monitoring criteria, subcommittees) | ⚪ Boundary: board capability-building and committee structure are organizational | |
| 4.2 — Increase frequency of review of organization's use of IT and AI; examine and update monitoring criteria | 🟡 Partial: continuous monitoring via governance bus + health probes supply review data; review cadence is org task | `hummbl_governance/health_probe.py`, `hummbl_governance/coordination_bus.py` |
| 4.3 — Accountability established across all aspects of AI use (impacts, strategy, lifecycle phases, environment changes, security, decommissioning) | ✅ DCT delegation chain + lifecycle accountability tuples span design → deployment → decommissioning | `hummbl_governance/delegation.py`, `hummbl_governance/lifecycle.py` |
| 4.3 — Appropriate security controls in place to protect organization, stakeholders, and data | ✅ Capability fence + output validator + kill-switch enforce security boundaries (cross-ref ISO 27001) | `hummbl_governance/capability_fence.py`, `hummbl_governance/output_validator.py`, `hummbl_governance/kill_switch.py` |
| 4.3 — Reporting to demonstrate to stakeholders that AI use is effectively governed (evaluate, direct, monitor) | 🟡 Partial: compliance-report generator + audit-log export produce governance evidence; stakeholder reporting act is org task | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |

### Clause 5 — Overview of AI and AI systems (5.2–5.5)

| Obligation | Coverage | Evidence |
|---|---|---|
| 5.2.1 — Governance of decision automation; understand implications of automated decisions | ✅ Decision-provenance tuples + human-oversight delegation tokens govern automated decision points | `hummbl_governance/audit_log.py`, `hummbl_governance/delegation.py` |
| 5.2.2 — Governance of data-driven problem-solving; ensure data quality and suitability | ✅ Data-quality tuples + schema validation + provenance chain govern data-driven processes | `hummbl_governance/schema_validator.py`, `hummbl_governance/audit_log.py` |
| 5.2.3 — Governance of adaptive/learning systems; monitor for drift and unintended adaptation | ✅ Reward monitor + convergence guard + health probe detect behavioral drift in adaptive systems | `hummbl_governance/reward_monitor.py`, `hummbl_governance/convergence_guard.py`, `hummbl_governance/health_probe.py` |
| 5.3 — Understand the AI ecosystem (developers, providers, operators, stakeholders) | 🟡 Partial: identity registry + delegation chain map ecosystem actors; ecosystem mapping is org task | `hummbl_governance/identity.py`, `hummbl_governance/delegation.py` |
| 5.4 — Govern benefits of AI use; ensure AI supports organizational goals | ⚪ Boundary: benefit realization and strategic alignment are organizational governance tasks | |
| 5.5 — Govern constraints on AI use; understand limitations and risks of AI technologies | 🟡 Partial: capability fence + cost governor enforce operational constraints; constraint identification is org task | `hummbl_governance/capability_fence.py`, `hummbl_governance/cost_governor.py` |

### Clause 6.2–6.3 — Governance oversight and decision-making

| Obligation | Coverage | Evidence |
|---|---|---|
| 6.2 — Governance oversight based on policies; identify individual and collective accountability in chain of responsibility | ✅ DCT delegation chain + identity registry enforce individual accountability with scope-bound policies | `hummbl_governance/delegation.py`, `hummbl_governance/identity.py` |
| 6.2 — Ensure sufficient human oversight; persons using AI are properly trained and know how to raise concerns | ✅ Human-oversight delegation token + concern-reporting tuple + escalation primitives (cross-ref EU AI Act Art. 14) | `hummbl_governance/delegation.py`, `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py` |
| 6.2 — Legal requirements and obligations determined for using AI technologies | 🟡 Partial: compliance mapper tracks regulatory obligations; legal determination is org task | `hummbl_governance/compliance_mapper.py` |
| 6.3 — Governance of decision-making; appropriate level of automation vs human involvement | ✅ Authority engine + doctrine engine enforce decision-automation boundaries with human-in-the-loop gates | `hummbl_governance/kernel/authority_engine.py`, `hummbl_governance/kernel/doctrine_engine.py` |
| 6.3 — Transparency of AI-assisted decisions; explainability of decision processes | ✅ Reasoning engine + evidence engine produce decision rationale + evidence chain for explainability | `hummbl_governance/reasoning.py`, `hummbl_governance/kernel/evidence_engine.py` |
| 6.3 — Accountability for AI-driven decisions; traceability from decision to responsible actor | ✅ Receipt engine + audit log produce signed decision receipts linking decisions to accountable actors | `hummbl_governance/kernel/receipt_engine.py`, `hummbl_governance/audit_log.py` |

### Clause 6.4–6.5 — Governance of data use and culture/values

| Obligation | Coverage | Evidence |
|---|---|---|
| 6.4 — Data used for correct purpose; sensitive data protected and secured | ✅ Capability fence + schema validator enforce purpose-binding + data-classification boundaries | `hummbl_governance/capability_fence.py`, `hummbl_governance/schema_validator.py` |
| 6.4 — Prior assessment of availability, quality, quantity, and suitability of data | ✅ Data-quality tuples + schema validation + provenance chain assess data suitability pre-use | `hummbl_governance/schema_validator.py`, `hummbl_governance/audit_log.py` |
| 6.4 — Examination of potential biases in data | 🟡 Partial: schema validation + audit-log bias-flag tuples detect structural bias; bias audit methodology is org task | `hummbl_governance/schema_validator.py`, `hummbl_governance/audit_log.py` |
| 6.4 — Formulate description of AI system (algorithms, data, models) for transparency and intended-use verification | ✅ Technical-doc generator + system-description tuples produce transparent AI system descriptions (cross-ref EU AI Act Art. 11) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| 6.5 — Governing body shapes organizational culture and values for ethical AI use | ⚪ Boundary: culture and values are organizational leadership responsibilities | |
| 6.5 — Ensure staff interests and concerns (workplace safety, training, quality of work) are represented | 🟡 Partial: concern-reporting tuple + escalation primitives surface staff concerns; representation structure is org task | `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py` |

### Clause 6.6 — Compliance

| Obligation | Coverage | Evidence |
|---|---|---|
| 6.6.1 — Identify and meet compliance obligations (legal, regulatory, contractual) for AI use | ✅ Compliance mapper tracks regulatory obligations across frameworks (cross-ref NIST AI RMF, EU AI Act, ISO 42001) | `hummbl_governance/compliance_mapper.py` |
| 6.6.2 — Compliance management; processes to manage and monitor ongoing compliance | ✅ Compliance mapper + audit log + stride mapper provide continuous compliance monitoring + violation detection | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py`, `hummbl_governance/stride_mapper.py` |

### Clause 6.7 — Risk

| Obligation | Coverage | Evidence |
|---|---|---|
| 6.7.1 — Define and approve risk appetite for AI; tolerance for bias, uncertainty, automation levels | 🟡 Partial: cost governor + circuit breaker encode operational risk thresholds; risk-appetite authorship is board task | `hummbl_governance/cost_governor.py`, `hummbl_governance/circuit_breaker.py` |
| 6.7.2 — Implement risk management processes throughout AI lifecycle (cross-ref ISO/IEC 23894) | ✅ Risk-identification + assessment + treatment tuples + lifecycle gates (cross-ref NIST AI RMF) | `hummbl_governance/audit_log.py`, `hummbl_governance/lifecycle.py` |
| 6.7.3 — Risk objectives aligned with organizational objectives | ⚪ Boundary: organizational objective alignment is leadership task | |
| 6.7.4 — Identify AI-specific risk sources (unwanted bias, cyber-threats, lack of AI expertise) | ✅ STRIDE mapper + reward monitor + health probe identify bias, security, and behavioral risk sources | `hummbl_governance/stride_mapper.py`, `hummbl_governance/reward_monitor.py`, `hummbl_governance/health_probe.py` |
| 6.7.5 — Implement controls to manage identified risks | ✅ Kill-switch 4-mode halt + circuit-breaker fast-fail + capability fence + cost governor enforce risk controls | `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py`, `hummbl_governance/capability_fence.py`, `hummbl_governance/cost_governor.py` |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| Clause 4 — Governance implications (4.2–4.3) | 6 | 2 | 3 | 1 |
| Clause 5 — Overview of AI and AI systems (5.2–5.5) | 6 | 3 | 2 | 1 |
| Clause 6.2–6.3 — Oversight and decision-making | 6 | 5 | 1 | 0 |
| Clause 6.4–6.5 — Data use and culture/values | 6 | 3 | 2 | 1 |
| Clause 6.6 — Compliance | 2 | 2 | 0 | 0 |
| Clause 6.7 — Risk | 5 | 3 | 1 | 1 |
| **Totals** | **31** | **18** | **9** | **4** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- ISO/IEC 38500 IT governance series — the parent standard 38507 extends
- ISO/IEC 42001 AIMS operationalizes 38507 governance principles — see [`iso-42001.md`](./iso-42001.md)
- ISO/IEC 23894 AI risk management — Clause 6.7 risk provisions reference this — see [`nist-ai-rmf.md`](./nist-ai-rmf.md)
- EU AI Act human oversight (Art. 14) and transparency (Art. 50) overlap Clauses 6.2–6.3 — see [`eu-ai-act.md`](./eu-ai-act.md)
- ISO 27001 security controls overlap Clause 4.3 security provisions — see [`iso-27001.md`](./iso-27001.md)
