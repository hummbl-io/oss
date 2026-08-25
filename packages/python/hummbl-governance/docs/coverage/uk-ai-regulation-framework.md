# UK AI Regulation Framework Coverage Matrix — HUMMBL

**Standard**: A pro-innovation approach to AI regulation (UK AI Regulation White Paper, Command Paper 815)
**Effective**: 29 March 2023 (non-statutory, principles-based; sectoral regulators implement on a voluntary/discretionary basis)
**Source**: https://www.gov.uk/government/publications/ai-regulation-a-pro-innovation-approach
**Last reviewed**: 2026-06-25
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not UK legal counsel and does not provide legal advice on the UK AI Regulation Framework. The framework is a non-statutory, principles-based white paper; the five cross-sectoral principles are not yet on a statutory footing and are implemented at the discretion of sectoral regulators (e.g. ICO, MHRA, FCA, Ofcom, HSE). Statutory compliance with underlying law (UK GDPR, Equality Act 2010, Human Rights Act 1998, sector-specific statutes) is the customer-organization responsibility. HUMMBL maps technical primitives to the five principles and the central government support functions described in the white paper.

## Scope summary

The framework applies UK-wide and is sector-led rather than centrally enforced. It defines AI by its unique characteristics (adaptivity, autonomy) and places expectations on "AI life cycle actors" — developers, deployers, and users — across the supply chain. Five cross-sectoral principles guide regulator responses: (1) safety, security and robustness; (2) appropriate transparency and explainability; (3) fairness; (4) accountability and governance; (5) contestability and redress. Government retains central functions — monitoring and evaluation, cross-sectoral risk assessment, horizon scanning, support for innovators (sandboxes/testbeds), and education/awareness — to coordinate and adapt the framework. No central AI authority is created; regulators apply principles within existing remits.

## Obligations + coverage

### Principle 1: Safety, security and robustness

| Obligation | Coverage | Evidence |
|---|---|---|
| AI systems should function in a robust, secure and safe way throughout the AI life cycle | ✅ Lifecycle-state machine + health-probe continuous monitoring + circuit-breaker fast-fail | `hummbl_governance/lifecycle.py`, `hummbl_governance/health_probe.py`, `hummbl_governance/circuit_breaker.py` |
| Risks should be continually identified, assessed and managed | ✅ Risk-identification + assessment + treatment tuple types (cross-ref NIST AI RMF, EU AI Act Art. 9) | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| AI systems should be technically secure and reliably function as intended | ✅ Capability-fence confinement + output-validator gate + schema validation | `hummbl_governance/capability_fence.py`, `hummbl_governance/output_validator.py`, `hummbl_governance/schema_validator.py` |
| System developers should embed resilience to security threats at each life-cycle stage | ✅ STRIDE threat-model mapper + capability-fence attack-surface reduction | `hummbl_governance/stride_mapper.py`, `hummbl_governance/capability_fence.py` |
| Regulators may require regular testing / due diligence on functioning, resilience and security | ✅ Health-probe periodic checks + audit-log evidence capture + compliance-report generator | `hummbl_governance/health_probe.py`, `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Kill-switch / halt capability for unsafe AI behaviour | ✅ Kill-switch 4-mode halt (HARD/SOFT/PARK/DRAIN) + circuit-breaker automatic trip | `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py` |

### Principle 2: Appropriate transparency and explainability

| Obligation | Coverage | Evidence |
|---|---|---|
| Communicate appropriate information about an AI system (when, how, for which purposes it is used) to relevant people | ✅ Transparency-notification primitive + audit-log provenance tuples (cross-ref EU AI Act Art. 50) | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Decision-making processes should be accessible, interpretable and understandable (explainability) | ✅ Reasoning-engine rationale capture + explanation-disclosure generator | `hummbl_governance/reasoning.py`, `hummbl_governance/compliance_mapper.py` |
| Transparency/explainability should be proportionate to the risk presented by the AI system | ✅ Risk-tiered disclosure via compliance-mapper risk classification + capability-fence scope | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/capability_fence.py` |
| Parties directly affected should access sufficient information to enforce their rights | 🟡 Partial: audit-log export + explanation generator produce the information; rights-enforcement is an org/legal task | `hummbl_governance/audit_log.py`, `hummbl_governance/reasoning.py` |
| Product labelling / form-and-manner disclosure as required by regulators | 🟡 Partial: output-validator can append provenance labels; regulator-specific labelling format is org task | `hummbl_governance/output_validator.py` |

### Principle 3: Fairness

| Obligation | Coverage | Evidence |
|---|---|---|
| AI systems should not undermine legal rights of individuals or organisations | 🟡 Partial: audit-log captures decision evidence for rights review; legal-rights determination is org/legal task | `hummbl_governance/audit_log.py` |
| AI systems should not discriminate unfairly against individuals | ✅ Output-validator bias/discrimination gate + reward-monitor drift detection | `hummbl_governance/output_validator.py`, `hummbl_governance/reward_monitor.py` |
| AI systems should not create unfair market outcomes | ⚪ Boundary: market-level competition analysis is regulatory/economic, not software-addressable | |
| Fairness definitions should be appropriate to a system's use, outcomes and relevant law | 🟡 Partial: compliance-mapper maps fairness controls to framework; legal fairness-definition selection is org task | `hummbl_governance/compliance_mapper.py` |
| Regulators publish descriptions/illustrations of fairness for their domain | ⚪ Boundary: regulator-published guidance is governmental, not software-addressable | |

### Principle 4: Accountability and governance

| Obligation | Coverage | Evidence |
|---|---|---|
| Governance measures should ensure effective oversight of the supply and use of AI systems | ✅ Governance-kernel authority + doctrine + law engines + lifecycle oversight | `hummbl_governance/kernel/authority_engine.py`, `hummbl_governance/kernel/doctrine_engine.py`, `hummbl_governance/kernel/law_engine.py`, `hummbl_governance/lifecycle.py` |
| Clear lines of accountability established across the AI life cycle | ✅ Identity-registry + delegation-token accountability chain + receipt-engine provenance | `hummbl_governance/identity.py`, `hummbl_governance/delegation.py`, `hummbl_governance/kernel/identity_engine.py`, `hummbl_governance/kernel/receipt_engine.py` |
| AI life cycle actors should adhere to the principles and implement measures at all stages | ✅ Lifecycle-state enforcement + admission-control + schedule-engine gating | `hummbl_governance/lifecycle.py`, `hummbl_governance/kernel/admission_control.py`, `hummbl_governance/kernel/schedule_engine.py` |
| Clear expectations for regulatory compliance placed on appropriate actors in the supply chain | ✅ Compliance-mapper obligation-to-actor mapping + delegation-token role assignment | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/delegation.py` |
| Assurance techniques (e.g. impact assessments) should identify risks early in the life cycle | ✅ Impact-assessment template + evidence-engine evidence collection (cross-ref EU AI Act Art. 27 FRIA) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/kernel/evidence_engine.py` |
| Organisations ensure proper functioning of AI systems they develop, deploy, or operate | ✅ Health-probe + output-validator + circuit-breaker runtime assurance | `hummbl_governance/health_probe.py`, `hummbl_governance/output_validator.py`, `hummbl_governance/circuit_breaker.py` |

### Principle 5: Contestability and redress

| Obligation | Coverage | Evidence |
|---|---|---|
| Users, impacted third parties and life-cycle actors should be able to contest an AI decision or outcome that is harmful | ✅ Audit-log decision-evidence capture + reasoning-engine rationale export for contest review | `hummbl_governance/audit_log.py`, `hummbl_governance/reasoning.py` |
| Regulators clarify existing routes to contestability and redress | ⚪ Boundary: regulator-published route clarification is governmental, not software-addressable | |
| Regulated entities should make contest routes (including informal channels) easily available and accessible | 🟡 Partial: audit-log + compliance-report generator produce contest evidence; channel provisioning is org task | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Appropriate transparency and explainability support contestability implementation | ✅ Reasoning rationale + audit-log provenance + output-validator labels feed contest evidence | `hummbl_governance/reasoning.py`, `hummbl_governance/audit_log.py`, `hummbl_governance/output_validator.py` |
| The non-statutory approach does not create new rights or new routes to redress at this stage | ⚪ Boundary: legal-rights creation is legislative, not software-addressable | |

### Central government support functions (Part 3.3)

| Obligation | Coverage | Evidence |
|---|---|---|
| Monitoring, assessment and feedback — central M&E framework to assess cross-economy and sector impacts | 🟡 Partial: audit-log + compliance-mapper produce monitoring evidence; central M&E aggregation is gov task | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Cross-sectoral risk assessment — identify and prioritise new and emerging AI risks | ✅ Risk-identification + assessment + treatment tuples + STRIDE threat mapping | `hummbl_governance/audit_log.py`, `hummbl_governance/stride_mapper.py`, `hummbl_governance/compliance_mapper.py` |
| Horizon scanning — identify emerging AI trends to enable coordinated adaptation | 🟡 Partial: compliance-mapper tracks framework evolution; external horizon-scanning intelligence is gov task | `hummbl_governance/compliance_mapper.py` |
| Support for innovators — testbeds and regulatory sandboxes | 🟡 Partial: capability-fence + circuit-breaker provide controlled testing environment with runtime safety boundaries for AI system testbeds; national sandbox provisioning and regulator operational management remain governmental | `hummbl_governance/capability_fence.py`, `hummbl_governance/circuit_breaker.py` |
| Education and awareness — provide guidance and awareness to support AI life-cycle actors | 🟡 Partial: compliance-mapper generates AI lifecycle guidance documentation and awareness materials for AI actors; public education campaign delivery remains governmental | `hummbl_governance/compliance_mapper.py` |
| Regulator coordination — convene regulators for joint guidance and coherent implementation | 🟡 Partial: coordination-bus provides multi-agent coordination and audit trail infrastructure for inter-regulator data sharing; inter-regulator convening and joint guidance publication remain governmental | `hummbl_governance/coordination_bus.py`, `hummbl_governance/audit_log.py` |

### Territorial application and non-statutory approach (Parts 5–6)

| Obligation | Coverage | Evidence |
|---|---|---|
| Framework applies UK-wide; sectoral regulators implement within existing territorial remits | ⚪ Boundary: jurisdictional scope is a legal determination | |
| Principles are non-statutory and applied at regulator discretion initially | ⚪ Boundary: statutory footing is a legislative decision, not software-addressable | |
| Government will evaluate whether the non-statutory framework is having the desired effect | 🟡 Partial: compliance-mapper + audit-log support evaluation evidence; evaluation act is gov task | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Global interoperability — framework aligned with OECD AI principles and international standards | ⚪ Boundary: international-treaty alignment is governmental, not software-addressable | |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| Principle 1: Safety, security and robustness | 6 | 6 | 0 | 0 |
| Principle 2: Transparency and explainability | 5 | 3 | 2 | 0 |
| Principle 3: Fairness | 5 | 2 | 2 | 1 |
| Principle 4: Accountability and governance | 6 | 6 | 0 | 0 |
| Principle 5: Contestability and redress | 5 | 2 | 1 | 2 |
| Central government support functions | 6 | 1 | 2 | 3 |
| Territorial + non-statutory approach | 4 | 0 | 1 | 3 |
| **Totals** | **37** | **20** | **8** | **9** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Transparency overlaps EU AI Act Art. 50 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Risk management overlaps NIST AI RMF — see [`nist-ai-rmf.md`](./nist-ai-rmf.md)
- Human oversight / accountability overlaps EU AI Act Art. 14 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Impact assessment overlaps EU AI Act Art. 27 (FRIA) — see [`eu-ai-act.md`](./eu-ai-act.md)
- Fairness / non-discrimination overlaps Colorado AI Act § 6-1-1701 — see [`colorado-ai-act.md`](./colorado-ai-act.md)
- Security / robustness overlaps NIST AI RMF MEASURE — see [`nist-ai-rmf.md`](./nist-ai-rmf.md)
- OECD AI Principles alignment — see [`g7-ai-code.md`](./g7-ai-code.md)
