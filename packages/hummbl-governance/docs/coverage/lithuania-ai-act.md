# Lithuania AI Act Implementation Amendments Coverage Matrix — HUMMBL

**Standard**: Law on Technology and Innovation Amendment (Act No. XV-105) and Law on Information Society Services Amendment (Act No. XV-106) implementing Regulation (EU) 2024/1689 (EU AI Act)
**Effective**: April 1, 2025 (enacted Jan 14, 2025; published TAR Jan 22, 2025; certain provisions phased in Aug 2, 2025)
**Source**: https://www.e-tar.lt/portal/it/legalAct/9c30a402d88811efa5ddd96c482819f5
**Last reviewed**: 2026-06-25
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not Lithuanian legal counsel and does not provide legal advice on the XV-105/106 amendments or the EU AI Act. The amendments function as national implementing measures for Regulation (EU) 2024/1689 — they designate national authorities (Innovation Agency as notifying authority, Communications Regulatory Authority/RRT as market surveillance authority), establish an AI regulatory sandbox, and assign procedural roles rather than recreate a standalone domestic AI Act. Substantive obligations (banned practices, high-risk requirements, transparency, FRIA, penalties) arise directly at EU level. Statutory compliance is the customer-organization responsibility. HUMMBL maps technical primitives to the institutional, conformity-assessment, market-surveillance, and oversight obligations the amendments operationalize.

## Scope summary

The amendments apply to organizations developing, placing on the market, or deploying AI systems in Lithuania, including high-risk AI systems listed in Annex III of the EU AI Act. The package designates the Innovation Agency (Inovacijų agentūra) as the national notifying authority for conformity assessment bodies and the Communications Regulatory Authority (RRT) as the national market surveillance authority and single contact point to the European AI Office. The State Data Protection Inspectorate and Consumer Rights Protection Service retain sectoral oversight roles. An AI regulatory sandbox (DI smėliadėžė) is mandated within the Innovation Agency, targeted operational by Jan 1, 2026. Enforcement and penalties for substantive breaches remain primarily established at EU level in Regulation (EU) 2024/1689.

## Obligations + coverage

### National authority designation & institutional framework (XV-105, XV-106)

| Obligation | Coverage | Evidence |
|---|---|---|
| Designate Innovation Agency as national notifying authority for conformity assessment bodies | ⚪ Boundary: government-authority designation is institutional, not software-addressable | |
| Designate Communications Regulatory Authority (RRT) as national market surveillance authority and single contact point | ⚪ Boundary: government-authority designation is institutional, not software-addressable | |
| Maintain single contact point for liaison with European AI Office and other Member State authorities | 🟡 Partial: identity registry + coordination bus support contact-point routing; governmental liaison is org task | `hummbl_governance/identity.py`, `hummbl_governance/coordination_bus.py` |
| Clarify roles of State Data Protection Inspectorate and Consumer Rights Protection Service for AI-related oversight | ⚪ Boundary: inter-agency role assignment is institutional, not software-addressable | |
| Align Information Society Services Act definitions with Regulation (EU) 2024/1689 and Regulation (EU) 2022/2065 (DSA) | ⚪ Boundary: statutory definition alignment is legal, not software-addressable | |

### Conformity assessment & notified bodies (XV-105)

| Obligation | Coverage | Evidence |
|---|---|---|
| Assess competence of domestic conformity assessment bodies for high-risk AI systems | ⚪ Boundary: body-accreditation competence assessment is institutional, not software-addressable | |
| Support notification procedures for conformity assessment bodies to the European AI Office | 🟡 Partial: compliance-mapper produces notification evidence packages; submission is org task | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Maintain technical documentation for high-risk AI systems to support conformity assessment | ✅ Immutable audit-log retention + documentation-retention tuple (cross-ref EU AI Act Art. 11) | `hummbl_governance/audit_log.py` |
| Implement risk management system for high-risk AI systems (EU AI Act Art. 9 via national operationalization) | ✅ Risk-mgmt program substrate: INTENT + adverse-event tuples + risk-treatment tuples (cross-ref NIST AI RMF, EU AI Act Art. 9) | `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py` |
| Implement human oversight for high-risk AI systems (EU AI Act Art. 14 via national operationalization) | ✅ Human-oversight delegation token + contact-registration tuple (cross-ref EU AI Act Art. 14) | `hummbl_governance/delegation.py`, `hummbl_governance/identity.py` |
| Implement quality management system for high-risk AI providers | 🟡 Partial: lifecycle + audit-log support QMS evidence; full QMS certification is org task | `hummbl_governance/lifecycle.py`, `hummbl_governance/audit_log.py` |

### AI regulatory sandbox (XV-105)

| Obligation | Coverage | Evidence |
|---|---|---|
| Establish and operate AI regulatory sandbox within Innovation Agency (target operational by Jan 1, 2026) | ⚪ Boundary: government sandbox infrastructure is institutional, not software-addressable | |
| Provide controlled testing environment for AI systems under regulatory supervision | ✅ Capability-fence sandboxing + output-validator sandbox mode for controlled testing | `hummbl_governance/capability_fence.py`, `hummbl_governance/output_validator.py` |
| Offer technical and compliance advisory services to sandbox participants | 🟡 Partial: compliance-mapper generates advisory evidence; advisory delivery is org task | `hummbl_governance/compliance_mapper.py` |
| Monitor sandbox participants for adverse events and safety incidents | ✅ Adverse-event tuple + health-probe monitoring + audit-log incident capture | `hummbl_governance/audit_log.py`, `hummbl_governance/health_probe.py` |
| Enforce sandbox exit/halt conditions when testing reveals unacceptable risk | ✅ Kill-switch 4-mode halt + circuit-breaker fast-fail for sandbox termination | `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py` |

### Market surveillance & enforcement (XV-106)

| Obligation | Coverage | Evidence |
|---|---|---|
| Conduct market surveillance inspections and investigations of AI systems on the Lithuanian market | 🟡 Partial: audit-log export + compliance-report generator supports inspection response; inspection conduct is org/regulatory task | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Handle incident reporting and serious-incident notification to RRT and EU authorities | ✅ Adverse-event tuple + incident-report generator + audit-log immutable capture (cross-ref EU AI Act Art. 73) | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Issue corrective orders and remedial measures for non-compliant AI systems | ⚪ Boundary: regulatory-order issuance is governmental, not software-addressable | |
| Cooperate with cross-border market surveillance and EU AI Office information exchange | 🟡 Partial: coordination-bus + lamport-clock support ordered information exchange; governmental cooperation is org task | `hummbl_governance/coordination_bus.py`, `hummbl_governance/lamport_clock.py` |
| Maintain records and documentation for market surveillance inquiries | ✅ Immutable audit-log retention + documentation-retention tuple with tamper-evident receipts | `hummbl_governance/audit_log.py`, `hummbl_governance/kernel/receipt_engine.py` |
| Coordinate oversight between RRT, Data Protection Inspectorate, and Consumer Rights Protection Service | 🟡 Partial: coordination-bus + identity registry support multi-party coordination; inter-agency governance is org task | `hummbl_governance/coordination_bus.py`, `hummbl_governance/identity.py` |

### Transparency & fundamental rights obligations (via EU AI Act cross-ref)

| Obligation | Coverage | Evidence |
|---|---|---|
| Provide transparency notification to users interacting with AI systems (EU AI Act Art. 50 via national operationalization) | ✅ Transparency-notification primitive + audit-log capture (cross-ref EU AI Act Art. 50, South Korea Art. 31) | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Label AI-generated synthetic content and deepfakes (EU AI Act Art. 50(2)/(4) via national operationalization) | ✅ Content-authenticity tuple + output-validation gate + provenance-labeling | `hummbl_governance/output_validator.py`, `hummbl_governance/audit_log.py` |
| Conduct fundamental rights impact assessment for high-risk AI deployers (EU AI Act Art. 27 via national operationalization) | ✅ Impact-assessment template with fundamental-rights component (cross-ref EU AI Act Art. 27, South Korea Art. 35) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Ensure transparency of high-risk AI system operation to deployers (EU AI Act Art. 13 via national operationalization) | ✅ Explanation-disclosure generator + documentation-retention tuple | `hummbl_governance/compliance_mapper.py` |

### Penalties, sanctions & appeals (EU-level via national enforcement structure)

| Obligation | Coverage | Evidence |
|---|---|---|
| Apply EU-level administrative fines for banned-practice violations (up to €35M or 7% global turnover) | ⚪ Boundary: administrative-fine exposure is legal, not software-addressable | |
| Apply EU-level administrative fines for high-risk system obligation violations (up to €15M or 3% global turnover) | ⚪ Boundary: administrative-fine exposure is legal, not software-addressable | |
| Apply EU-level administrative fines for incorrect/supply of information (up to €7.5M or 1% global turnover) | ⚪ Boundary: administrative-fine exposure is legal, not software-addressable | |
| Provide national budgeting and resourcing for RRT and oversight bodies to exercise enforcement powers | ⚪ Boundary: government budgeting is institutional, not software-addressable | |
| Operate appeal routes within national administrative law and EU enforcement architecture | ⚪ Boundary: legal-appeal procedures are legal, not software-addressable | |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| National authority designation (XV-105, XV-106) | 5 | 0 | 1 | 4 |
| Conformity assessment & notified bodies (XV-105) | 6 | 3 | 2 | 1 |
| AI regulatory sandbox (XV-105) | 5 | 3 | 1 | 1 |
| Market surveillance & enforcement (XV-106) | 6 | 2 | 3 | 1 |
| Transparency & fundamental rights (EU AI Act cross-ref) | 4 | 4 | 0 | 0 |
| Penalties, sanctions & appeals (EU-level) | 5 | 0 | 0 | 5 |
| **Totals** | **31** | **12** | **7** | **12** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Substantive obligations arise from EU AI Act — see [`eu-ai-act.md`](./eu-ai-act.md)
- Risk management overlaps NIST AI RMF MEASURE — see [`nist-ai-rmf.md`](./nist-ai-rmf.md)
- Human oversight overlaps EU AI Act Art. 14 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Fundamental rights impact assessment overlaps EU AI Act Art. 27 (FRIA) — see [`eu-ai-act.md`](./eu-ai-act.md)
- Transparency overlaps EU AI Act Art. 50 and South Korea AI Basic Act Art. 31 — see [`eu-ai-act.md`](./eu-ai-act.md), [`south-korea-ai-basic-act.md`](./south-korea-ai-basic-act.md)
- Sandbox testing overlaps Council of Europe AI Convention — see [`council-of-europe-ai-convention.md`](./council-of-europe-ai-convention.md)
