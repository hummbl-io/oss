# ISO/IEC 5339:2024 Coverage Matrix — HUMMBL

**Standard**: ISO/IEC 5339:2024 — Information technology — Artificial intelligence — Guidance for AI applications
**Effective**: January 2024 (published 2024-01-15)
**Source**: https://www.iso.org/standard/81120.html
**Last reviewed**: 2026-06-25
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not an ISO/IEC conformity-assessment body and does not certify compliance with ISO/IEC 5339:2024. This standard is an international guidance document (type 2 ISO deliverable), not a certifiable management-system standard; it provides macro-level guidance rather than prescriptive requirements. HUMMBL maps technical primitives to the guidance areas — stakeholder mapping, trustworthiness characteristics, risk management, ethics, and the make/use/impact perspectives — to support organizations applying the standard. Conformity assessment and organizational governance decisions remain the customer-organization responsibility.

## Scope summary

ISO/IEC 5339:2024 provides guidance for identifying the context, opportunities, and processes for developing and applying AI applications. It offers a macro-level view of the AI application context, stakeholders and their roles, relationship to the AI system life cycle (per ISO/IEC 22989:2022 and ISO/IEC 5338), and common AI application functional and non-functional characteristics. The framework incorporates three perspectives — "make", "use", and "impact" — and addresses non-functional characteristics including trustworthiness, risk management, and ethics/societal concerns. It is intended for standards developers, application developers, AI producers, AI customers, and other interested parties.

## Obligations + coverage

### AI application context and stakeholder mapping (Cl. 5.2–5.3)

| Obligation | Coverage | Evidence |
|---|---|---|
| Identify AI application context — where, why, who, when of the application (Cl. 5.2) | ✅ Context-capture tuple + compliance-mapper application-profile primitive | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Identify AI stakeholders and their roles across the AI system life cycle (Cl. 5.3.2) | ✅ Agent-identity registry + role-assignment tuples (cross-ref ISO/IEC 22989 Cl. 5) | `hummbl_governance/identity.py`, `hummbl_governance/delegation.py`, `hummbl_governance/kernel/identity_engine.py` |
| Map other stakeholders — community, regulators, AI subjects (Cl. 5.3.3) | 🟡 Partial: identity registry captures agent-level stakeholders; community/regulator/subject mapping is organizational | `hummbl_governance/identity.py` |
| Define processes for stakeholder engagement across life-cycle stages (Cl. 5.3.4) | ✅ Coordination-bus message routing + lifecycle-stage transitions (cross-ref ISO/IEC 5338) | `hummbl_governance/coordination_bus.py`, `hummbl_governance/lifecycle.py` |

### Trustworthiness characteristics (Cl. 5.5.2)

| Obligation | Coverage | Evidence |
|---|---|---|
| Validity and reliability of AI application outputs (Cl. 5.5.2.2–5.5.2.3, 5.5.2.9) | ✅ Output-validation gate + schema-validation enforcement on all agent outputs | `hummbl_governance/output_validator.py`, `hummbl_governance/schema_validator.py` |
| Safety of AI application — prevent harm to users and subjects (Cl. 5.5.2.4) | ✅ Kill-switch 4-mode halt + circuit-breaker fast-fail + capability-fence boundary enforcement | `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py`, `hummbl_governance/capability_fence.py` |
| Security and resilience of the AI application (Cl. 5.5.2.4) | ✅ Capability-fence sandboxing + STRIDE threat mapper for adversarial risk identification | `hummbl_governance/capability_fence.py`, `hummbl_governance/stride_mapper.py` |
| Accountability — trace actions to responsible parties (Cl. 5.5.2.8) | ✅ Immutable audit-log + kernel receipt-engine signed receipts + identity-engine attribution | `hummbl_governance/audit_log.py`, `hummbl_governance/kernel/receipt_engine.py`, `hummbl_governance/kernel/identity_engine.py` |
| Transparency — disclose AI use, capabilities, and limitations (Cl. 5.5.2.8) | ✅ Compliance-mapper disclosure generator + audit-log provenance tuples (cross-ref EU AI Act Art. 50) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Explainability and interpretability of AI application decisions (Cl. 5.5.2.x) | ✅ Reasoning-engine trace + audit-log decision-provenance tuples | `hummbl_governance/reasoning.py`, `hummbl_governance/audit_log.py` |
| Privacy enhancement — protect personal data in AI application (Cl. 5.5.2.x) | 🟡 Partial: identity registry manages agent identity; PII data-handling and privacy-assessment is organizational | `hummbl_governance/identity.py` |
| Fairness — address bias and discrimination in AI outputs (Cl. 5.5.2.x) | 🟡 Partial: output-validator can flag bias signals; full fairness assessment and mitigation is organizational | `hummbl_governance/output_validator.py` |

### Risks and risk management (Cl. 5.5.3)

| Obligation | Coverage | Evidence |
|---|---|---|
| Establish risk management system for the AI application (Cl. 5.5.3) | ✅ Risk-mgmt program substrate: risk-identification + assessment + treatment tuples (cross-ref NIST AI RMF, ISO/IEC 23894) | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Identify, assess, and mitigate risks across the life cycle (Cl. 5.5.3) | ✅ STRIDE threat mapper + risk-treatment tuples + circuit-breaker mitigation triggers | `hummbl_governance/stride_mapper.py`, `hummbl_governance/audit_log.py`, `hummbl_governance/circuit_breaker.py` |
| Determine risk appetite and tolerance for the organization (Cl. 5.5.3) | 🟡 Partial: cost-governor budget enforcement operationalizes tolerance; appetite-setting is organizational governance | `hummbl_governance/cost_governor.py` |

### Ethics and societal concerns (Cl. 5.5.4)

| Obligation | Coverage | Evidence |
|---|---|---|
| Address ethics and societal concerns in AI application design and deployment (Cl. 5.5.4) | 🟡 Partial: kernel doctrine-engine encodes governance principles; societal-impact assessment is organizational | `hummbl_governance/kernel/doctrine_engine.py` |
| Consider environmental and sustainability impacts of AI application (Cl. 5.5.4) | ⚪ Boundary: sustainability and environmental-impact assessment is organizational, not software-addressable | |

### Make perspective — AI producer and developer guidance (Cl. 7.1)

| Obligation | Coverage | Evidence |
|---|---|---|
| AI producer should identify customers, users, and stakeholders for the application (Cl. 7.1.2) | ✅ Identity registry + compliance-mapper stakeholder-profile primitive | `hummbl_governance/identity.py`, `hummbl_governance/compliance_mapper.py` |
| AI producer should manage data sources, quality, and provenance (Cl. 7.1.2) | ✅ Audit-log data-provenance tuples + schema-validator input validation | `hummbl_governance/audit_log.py`, `hummbl_governance/schema_validator.py` |
| AI developer should ensure qualification and skills for development (Cl. 7.1.3) | ⚪ Boundary: personnel qualification and training is organizational, not software-addressable | |
| AI application provider should define deployment mode and technical infrastructure (Cl. 7.1.5) | ✅ Lifecycle deployment-stage tracking + capability-fence deployment-boundary enforcement | `hummbl_governance/lifecycle.py`, `hummbl_governance/capability_fence.py` |
| AI producer should address trustworthiness and risk concerns in production (Cl. 7.1.2) | ✅ Kill-switch + circuit-breaker + audit-log risk-monitoring (cross-ref Cl. 5.5.2–5.5.3) | `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py`, `hummbl_governance/audit_log.py` |

### Use perspective — AI customer and user guidance (Cl. 7.2)

| Obligation | Coverage | Evidence |
|---|---|---|
| AI customer should verify AI application meets requirements (Cl. 7.2.2) | ✅ Schema-validator contract enforcement + output-validator acceptance gates | `hummbl_governance/schema_validator.py`, `hummbl_governance/output_validator.py` |
| AI user should understand AI application capabilities and limitations (Cl. 7.2.2) | ✅ Compliance-mapper capability-disclosure + reasoning-engine explanation traces | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/reasoning.py` |
| AI customer should monitor AI application performance during operation (Cl. 7.2.2) | ✅ Health-probe liveness/readiness + reward-monitor behavioral-drift detection | `hummbl_governance/health_probe.py`, `hummbl_governance/reward_monitor.py` |

### Impact perspective (Cl. 7.3)

| Obligation | Coverage | Evidence |
|---|---|---|
| Assess impact on AI subjects, community, and society (Cl. 7.3) | 🟡 Partial: compliance-mapper impact-assessment template; full societal-impact evaluation is organizational | `hummbl_governance/compliance_mapper.py` |
| Monitor evolving impacts over time due to data or legal-environment changes (Cl. 7.3) | ✅ Lifecycle re-assessment triggers + audit-log longitudinal tracking + health-probe drift detection | `hummbl_governance/lifecycle.py`, `hummbl_governance/audit_log.py`, `hummbl_governance/health_probe.py` |
| Engage relevant authorities and comply with legal requirements (Cl. 7.3) | 🟡 Partial: kernel law-engine encodes regulatory constraints; authority engagement is organizational | `hummbl_governance/kernel/law_engine.py` |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| Context + stakeholder mapping (Cl. 5.2–5.3) | 4 | 3 | 1 | 0 |
| Trustworthiness characteristics (Cl. 5.5.2) | 8 | 6 | 2 | 0 |
| Risks and risk management (Cl. 5.5.3) | 3 | 2 | 1 | 0 |
| Ethics and societal concerns (Cl. 5.5.4) | 2 | 0 | 1 | 1 |
| Make perspective (Cl. 7.1) | 5 | 4 | 0 | 1 |
| Use perspective (Cl. 7.2) | 3 | 3 | 0 | 0 |
| Impact perspective (Cl. 7.3) | 3 | 1 | 2 | 0 |
| **Totals** | **28** | **19** | **7** | **2** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- AI system life cycle overlaps ISO/IEC 22989:2022 Cl. 6 and ISO/IEC 5338 — see [`iso-iec-22989.md`](./iso-iec-22989.md), [`iso-iec-5338.md`](./iso-iec-5338.md)
- Risk management overlaps ISO/IEC 23894:2023 and NIST AI RMF — see [`iso-iec-23894.md`](./iso-iec-23894.md), [`nist-ai-rmf.md`](./nist-ai-rmf.md)
- Trustworthiness characteristics derived from ISO/IEC 24028 — see [`iso-iec-22989.md`](./iso-iec-22989.md)
- Transparency overlaps EU AI Act Art. 50 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Accountability and audit overlap SOC 2 — see [`soc2.md`](./soc2.md)
- AI management-system overlap with ISO/IEC 42001 — see [`iso-42001.md`](./iso-42001.md)
