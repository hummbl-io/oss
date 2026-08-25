# North Carolina Executive Order 24 Coverage Matrix — HUMMBL

**Standard**: Executive Order No. 24 — Advancing Trustworthy Artificial Intelligence That Benefits All North Carolinians
**Effective**: September 2, 2025 (sunset December 31, 2028)
**Source**: https://governor.nc.gov/executive-order-no-24-advancing-trustworthy-artificial-intelligence-benefits-all-north-carolinians
**Last reviewed**: 2026-06-25
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not North Carolina legal counsel and does not provide legal advice on Executive Order 24. The Order establishes governance bodies (AI Leadership Council, AI Accelerator within NCDIT, Agency AI Oversight Teams), mandates use-case proposals, and incorporates by reference the August 2024 NCDIT *North Carolina State Government Responsible Use of Artificial Intelligence Framework* (which requires AI system inventory and NIST AI RMF-based risk assessment). Statutory compliance is the customer-organization responsibility. HUMMBL maps technical primitives to the Order's inventory, risk-assessment, transparency, accountability, training, and data-protection obligations.

## Scope summary

EO 24 applies to North Carolina state agencies, with binding obligations on Cabinet agencies and encouraged (non-binding) participation by non-Cabinet agencies. It covers all AI systems designed, developed, acquired, or used by state agencies that have the potential to impact North Carolinians' exercise of rights, opportunities, or access to critical resources or services. The Order establishes the AI Leadership Council (25 members, advisory), the AI Accelerator (NCDIT-hosted centralized governance hub), and Agency AI Oversight Teams (min. 4 members each). The incorporated NCDIT Framework requires agencies to maintain an AI tool inventory and use the NIST AI RMF for risk assessment. The Order sunsets December 31, 2028 (Accelerator may continue).

## Obligations + coverage

### Governance structure and accountability (Sec. 1, Sec. 3)

| Obligation | Coverage | Evidence |
|---|---|---|
| Establish Agency AI Oversight Teams with min. 4 members possessing business, policy, and technical expertise | ✅ Identity-registry + role-assignment tokens with capability attributes (cross-ref EU AI Act Art. 14 human oversight) | `hummbl_governance/identity.py`, `hummbl_governance/delegation.py` |
| AI Leadership Council advises on AI strategy, policy, governance, and ethics frameworks promoting safety, transparency, fairness, privacy | ⚪ Boundary: multi-stakeholder advisory council is organizational, not software-addressable | |
| Council submits annual AI Strategic Recommendation to Governor by June 30 with public listening-session input | 🟡 Partial: compliance-report generator produces the report; public engagement and submission are org tasks | `hummbl_governance/compliance_mapper.py` |
| Cabinet agencies submit at least 3 AI use-case proposals to Accelerator within 180 days for review and piloting | 🟡 Partial: use-case intake tuples + risk-assessment template support proposal structuring; submission is org task | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Accelerator assesses use cases for strategic alignment, potential impact, and risk | ✅ Impact-assessment template + risk-classification tuple (cross-ref NIST AI RMF GOVERN, EU AI Act Art. 9) | `hummbl_governance/compliance_mapper.py` |

### AI system inventory and risk assessment (Sec. 2, NCDIT Framework)

| Obligation | Coverage | Evidence |
|---|---|---|
| Agencies must maintain inventory of AI tools/applications (types of AI, users, purposes) | ✅ System-inventory tuple type with asset-registration + capability-classification fields | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Accelerator collects high-risk AI use cases and publishes inventory on its website for public review | 🟡 Partial: inventory tuples + compliance-report generator produce publishable content; website publication is org task | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Accelerator defines what constitutes a high-risk AI use case (sensitive data, critical sectors, interconnected systems) | ✅ Risk-classification tuple with sector + data-sensitivity + interconnection attributes (cross-ref EU AI Act Annex III) | `hummbl_governance/compliance_mapper.py` |
| Agencies must use the NIST AI RMF for risk assessment of AI use cases | ✅ NIST AI RMF crosswalk in compliance mapper (GOVERN/MAP/MEASURE/MANAGE) (cross-ref NIST AI RMF) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/stride_mapper.py` |
| Accelerator develops a risk-assessment framework for AI use cases that agencies use when submitting proposals | ✅ Risk-assessment template with identify + assess + treat tuple types (cross-ref NIST AI RMF MAP, ISO 23894) | `hummbl_governance/compliance_mapper.py` |
| Monitor AI activities across state agencies to track AI-related risks across the use-case inventory | ✅ Audit-log event stream + health-probe monitoring + coordination-bus risk broadcast | `hummbl_governance/audit_log.py`, `hummbl_governance/health_probe.py`, `hummbl_governance/coordination_bus.py` |

### Transparency and public reporting (Sec. 2.D)

| Obligation | Coverage | Evidence |
|---|---|---|
| Accelerator submits annual public report to Governor by June 30 detailing AI initiatives and use-case results | 🟡 Partial: compliance-report generator produces the report; public publication is org task | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Annual report includes training-program participation and outcomes for the state workforce | 🟡 Partial: audit-log training-event tuples support data collection; report assembly is org task | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Develop AI Governance Framework with principles: fairness, accountability, transparency, security, privacy, civil liberties | ✅ Doctrine-engine law tuples encode governance principles as enforceable policy rules | `hummbl_governance/kernel/doctrine_engine.py`, `hummbl_governance/kernel/law_engine.py` |
| Identify and standardize state-wide definitions for AI and Generative AI | ✅ Schema-validator + classification tuples enforce consistent AI-type definitions across inventory | `hummbl_governance/schema_validator.py`, `hummbl_governance/compliance_mapper.py` |

### Training and AI literacy (Sec. 4)

| Obligation | Coverage | Evidence |
|---|---|---|
| Develop and disseminate AI literacy training for state employees and the general public (foundational concepts, fraud, ethics, safety) | ⚪ Boundary: curriculum development and public dissemination are organizational, not software-addressable | |
| Track training-program participation and outcomes for the state workforce | ✅ Audit-log training-event tuples with participant identity + completion receipts | `hummbl_governance/audit_log.py`, `hummbl_governance/kernel/receipt_engine.py` |
| AI literacy strategy must enhance public understanding, skill development, and effective utilization of AI | ⚪ Boundary: public-education strategy is organizational policy, not software-addressable | |

### Data protection, security, and safety (Sec. 2.B, NCDIT Framework)

| Obligation | Coverage | Evidence |
|---|---|---|
| Develop and enforce IP and data-protection frameworks to safeguard sensitive information and define ownership of AI-generated outputs | ✅ Capability-fence data-classification enforcement + output-validator provenance labels | `hummbl_governance/capability_fence.py`, `hummbl_governance/output_validator.py` |
| Protect sensitive data provided to the state by North Carolinians (privacy, data-protection risks) | ✅ Capability-fence data-classification gate + identity-based access control (cross-ref GDPR Art. 32) | `hummbl_governance/capability_fence.py`, `hummbl_governance/identity.py` |
| Provide guidance on safeguarding public safety and critical infrastructure from AI-related risks, including misuse or failure in high-impact systems | ✅ Kill-switch 4-mode halt + circuit-breaker fast-fail + physical-governor safety envelope | `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py`, `hummbl_governance/physical_governor.py` |
| Ensure transparency, accountability, and security in state AI initiatives and partnerships | ✅ Immutable audit-log + receipt-engine evidence tuples + authority-engine authorization records | `hummbl_governance/audit_log.py`, `hummbl_governance/kernel/receipt_engine.py`, `hummbl_governance/kernel/authority_engine.py` |
| Assess energy and water consumption and environmental impacts of increased AI use and infrastructure (Council input to Energy Policy Task Force) | ⚪ Boundary: environmental-impact assessment for physical infrastructure is organizational, not software-addressable | |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| Governance structure & accountability (Sec. 1, 3) | 5 | 2 | 2 | 1 |
| AI system inventory & risk assessment (Sec. 2, Framework) | 6 | 5 | 1 | 0 |
| Transparency & public reporting (Sec. 2.D) | 4 | 2 | 2 | 0 |
| Training & AI literacy (Sec. 4) | 3 | 1 | 0 | 2 |
| Data protection, security & safety (Sec. 2.B, Framework) | 5 | 4 | 0 | 1 |
| **Totals** | **23** | **14** | **5** | **4** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Risk assessment incorporates NIST AI RMF — see [`nist-ai-rmf.md`](./nist-ai-rmf.md)
- Human oversight overlaps EU AI Act Art. 14 — see [`eu-ai-act.md`](./eu-ai-act.md)
- High-risk classification overlaps EU AI Act Annex III — see [`eu-ai-act.md`](./eu-ai-act.md)
- Data protection overlaps GDPR Art. 32 — see [`gdpr.md`](./gdpr.md)
- Risk-assessment framework overlaps ISO/IEC 23894 — see [`iso-iec-23894.md`](./iso-iec-23894.md)
- State-agency AI governance parallels Texas TRAIGA — see [`texas-traiga.md`](./texas-traiga.md)
