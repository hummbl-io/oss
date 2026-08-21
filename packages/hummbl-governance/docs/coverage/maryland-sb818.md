# Maryland AI Governance Act (SB 818) Coverage Matrix — HUMMBL

**Standard**: Maryland Artificial Intelligence Governance Act of 2024, Senate Bill 818, Chapter 496 (State Finance and Procurement Article §§ 3.5-318, 3.5-303, 3.5-801–3.5-806, 13-116)
**Effective**: July 1, 2024 (staged compliance deadlines through July 1, 2027)
**Source**: https://mgaleg.maryland.gov/2024RS/chapters_noln/CH_496_sb0818e.pdf
**Last reviewed**: 2026-06-25
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not Maryland-licensed counsel and does not provide legal advice on the AI Governance Act. The Act applies exclusively to units of State government (not private-sector AI developers or deployers). It distinguishes "high-risk artificial intelligence" — including "rights-impacting AI" (affecting civil rights, civil liberties, equal opportunities, access to critical resources, or privacy) and "safety-impacting AI" (affecting human life, well-being, or critical infrastructure). Statutory compliance is the customer-organization responsibility. HUMMBL maps technical primitives to the Act's inventory, impact-assessment, guardrail, procurement-compliance, and individual-protection obligations.

## Scope summary

The Act applies to each unit of Maryland State government, with partial applicability to the Office of the Attorney General, Comptroller, State Treasurer (must adopt functionally compatible policies by June 1, 2025), and public senior higher education institutions plus Baltimore City Community College (research/academic AI exempt from subtitle but subject to separate reporting). Key deadlines: DoIT policies by December 1, 2024; annual data inventories from December 1, 2024; high-risk AI system inventories from December 1, 2025; procurement compliance ban from July 1, 2025; impact assessments for post-February 2026 systems by December 31, 2026 and for pre-February 2026 systems by July 1, 2027. No civil penalties — enforcement is internal state government administrative compliance overseen by the Governor's AI Subcabinet.

## Obligations + coverage

### Data inventory obligations (§ 3.5-318)

| Obligation | Coverage | Evidence |
|---|---|---|
| Annual data inventory identifying data meeting Chief Data Officer criteria, including when data is used in AI | ✅ Data-inventory tuple type + asset-registration primitive (cross-ref NIST AI RMF IDENTIFY) | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Data inventory in form prescribed by Chief Data Officer | ✅ Schema-validated inventory record with prescribed field structure | `hummbl_governance/schema_validator.py`, `hummbl_governance/audit_log.py` |
| DoIT develops and publishes guidance on data inventory policies and procedures | 🟡 Partial: compliance-mapper generates guidance document; publication is org task | `hummbl_governance/compliance_mapper.py` |

### AI system inventory obligations (§ 3.5-803)

| Obligation | Coverage | Evidence |
|---|---|---|
| Conduct inventory of systems employing high-risk AI by December 1, 2025, and regularly thereafter | ✅ System-inventory tuple + lifecycle registration primitive (cross-ref Texas TRAIGA § 552.103) | `hummbl_governance/audit_log.py`, `hummbl_governance/lifecycle.py` |
| Provide inventory to DoIT in required format | 🟡 Partial: compliance-report generator produces structured inventory export; submission is org task | `hummbl_governance/compliance_mapper.py` |
| Inventory includes system name, vendor, capabilities, purpose, and intended uses | ✅ System-registration tuple with vendor-identity + capability-description fields | `hummbl_governance/audit_log.py`, `hummbl_governance/identity.py` |
| Inventory records whether system underwent impact assessment prior to deployment | ✅ Assessment-status tuple + pre-deployment gate (cross-ref EU AI Act Art. 9) | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Inventory records whether system independently makes or informs high-risk decisions, with impact assessment summary | ✅ Decision-role classification tuple + assessment-result summary primitive | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| DoIT makes aggregated statewide inventory publicly available; withholds security-sensitive info | 🟡 Partial: report generator produces publishable aggregate; public website publication and security-redaction judgment are org tasks | `hummbl_governance/compliance_mapper.py` |
| DoIT provides withheld security info to Governor, General Assembly, and law enforcement on request | ⚪ Boundary: government information-sharing is organizational, not software-addressable | |

### Impact assessment obligations (§ 3.5-803(e), § 3.5-805(b))

| Obligation | Coverage | Evidence |
|---|---|---|
| Impact assessment for high-risk AI systems procured on or after February 1, 2026 (by December 31, 2026) | ✅ Impact-assessment template with risk-based evaluation (cross-ref EU AI Act Art. 27 FRIA, Colorado SB 24-205 § 6-1-1703) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Impact assessment for high-risk AI systems procured before February 1, 2026 (by July 1, 2027) | ✅ Legacy-system assessment template + retroactive-evaluation tuple | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Regular impact assessments for high-risk AI per Subcabinet determination | ✅ Scheduled-assessment primitive + health-probe monitoring cycle (cross-ref NIST AI RMF MEASURE) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/health_probe.py` |

### Policies, guardrails, and individual protection (§ 3.5-804)

| Obligation | Coverage | Evidence |
|---|---|---|
| DoIT adopts policies and procedures for high-risk AI development, procurement, deployment, use, and ongoing assessment | 🟡 Partial: policy-template generator produces framework; adoption and rulemaking are org tasks | `hummbl_governance/compliance_mapper.py` |
| Policies ensure adequate guardrails to protect individuals and communities | ✅ Kill-switch 4-mode halt + circuit-breaker fast-fail + capability-fence boundary enforcement (cross-ref NIST AI RMF GOVERN) | `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py`, `hummbl_governance/capability_fence.py` |
| Notify negatively impacted individuals and provide opt-out guidance | ✅ Adverse-impact notification tuple + opt-out-guidance primitive via coordination bus | `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py` |
| Provide procurement guidance ensuring data privacy and statutory compliance | ✅ STRIDE threat-mapping for procurement + schema-validated compliance checklist | `hummbl_governance/stride_mapper.py`, `hummbl_governance/schema_validator.py` |
| Make policies and procedures publicly available within 45 days of adoption | 🟡 Partial: report generator produces publishable policy document; website publication is org task | `hummbl_governance/compliance_mapper.py` |

### Procurement compliance and institutional obligations (§ 3.5-805, § 3.5-802)

| Obligation | Coverage | Evidence |
|---|---|---|
| Procurement ban: no new AI system procurement or deployment after July 1, 2025 unless compliant with DoIT policies | ✅ Admission-control gate + authority-engine policy enforcement at procurement boundary | `hummbl_governance/kernel/admission_control.py`, `hummbl_governance/kernel/authority_engine.py` |
| Office of the Attorney General, Comptroller, and State Treasurer: functionally compatible policies by June 1, 2025 | ⚪ Boundary: independent-entity policy adoption is organizational, not software-addressable | |
| Public senior higher education institutions and BCCC: functionally compatible policies by June 1, 2025 | ⚪ Boundary: institutional policy adoption is organizational, not software-addressable | |
| Higher ed institutions: annual report on high-risk AI procured/deployed for research or academic purposes (September 1, 2025+) | 🟡 Partial: report generator produces research-AI inventory report; submission is org task | `hummbl_governance/compliance_mapper.py` |

### AI Subcabinet, proof-of-concept, and Secretary duties (§ 3.5-806, § 13-116, § 3.5-303)

| Obligation | Coverage | Evidence |
|---|---|---|
| Subcabinet oversees AI inventory, impact assessments, monitoring of high-risk AI, and compliance with State policies | ✅ Coordination-bus oversight channel + audit-log compliance tracking + health-probe monitoring | `hummbl_governance/coordination_bus.py`, `hummbl_governance/audit_log.py`, `hummbl_governance/health_probe.py` |
| Subcabinet develops comprehensive action plan and strategy for responsible AI use across State government | ⚪ Boundary: government strategic-planning body is organizational, not software-addressable | |
| Competitive proof-of-concept procurement process with DoIT approval and MOU for status updates | ⚪ Boundary: procurement-process design and inter-agency MOU execution are organizational | |
| Secretary of IT conducts AI system inventories and annually evaluates feasibility of AI for public services | ✅ Inventory-collection primitive + annual-evaluation tuple + feasibility-assessment template | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| Data inventory (§ 3.5-318) | 3 | 2 | 1 | 0 |
| AI system inventory (§ 3.5-803) | 7 | 4 | 2 | 1 |
| Impact assessment (§ 3.5-803(e), § 3.5-805(b)) | 3 | 3 | 0 | 0 |
| Policies, guardrails, individual protection (§ 3.5-804) | 5 | 3 | 2 | 0 |
| Procurement compliance + institutional (§ 3.5-805, § 3.5-802) | 4 | 1 | 1 | 2 |
| Subcabinet, proof-of-concept, Secretary (§ 3.5-806, § 13-116, § 3.5-303) | 4 | 2 | 0 | 2 |
| **Totals** | **26** | **15** | **6** | **5** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Impact assessment overlaps EU AI Act Art. 27 (FRIA) — see [`eu-ai-act.md`](./eu-ai-act.md)
- Impact assessment overlaps Colorado SB 24-205 deployer assessment — see [`colorado-ai-act.md`](./colorado-ai-act.md)
- Guardrails and risk management overlap NIST AI RMF GOVERN/MEASURE — see [`nist-ai-rmf.md`](./nist-ai-rmf.md)
- State agency AI inventory overlaps Texas TRAIGA § 552.103 — see [`texas-traiga.md`](./texas-traiga.md)
- Procurement compliance ban overlaps California SB 942 transparency obligations — see [`california-sb-942.md`](./california-sb-942.md)
- Data privacy guidance overlaps GDPR Art. 9 (special categories) — see [`gdpr.md`](./gdpr.md)
