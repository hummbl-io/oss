# Kentucky AI Governance Framework Coverage Matrix — HUMMBL

**Standard**: Kentucky Revised Statutes § 42.731 — Duties of Artificial Intelligence Governance Committee; Commonwealth Office of Technology; Policies and Operating Standards on Use of Artificial Intelligence by State Agencies
**Effective**: March 24, 2025 (2025 Ky. Acts ch. 66, sec. 3)
**Source**: https://apps.legislature.ky.gov/law/statutes/statute.aspx?id=55895
**Last reviewed**: 2026-06-25
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not Kentucky legal counsel and does not provide legal advice on KRS 42.731. The statute governs state departments, agencies, and administrative bodies under the Commonwealth Office of Technology (COT). It establishes an Artificial Intelligence Governance Committee, a centralized registry, human-review requirements, transparency/disclosure duties, and a high-risk AI risk-management mandate aligned to ISO/IEC 42001. KRS 42.731(9) exempts trade secrets, confidential/proprietary information, and security-risk information from disclosure. Statutory compliance is the customer-organization responsibility. HUMMBL maps technical primitives to the statute's registry, documentation, human-oversight, privacy, transparency, and risk-management obligations.

## Scope summary

KRS 42.731 applies to all Kentucky state departments, agencies, and administrative bodies that utilize or access the Commonwealth's information technology and technology infrastructure for AI systems, generative AI, and high-risk AI. The COT's Artificial Intelligence Governance Committee sets policy and technology standards, maintains a centralized registry, and approves AI use cases. The statute distinguishes "generative artificial intelligence" and "high-risk artificial intelligence" systems, the latter carrying mandatory risk-management policies before consequential decisions may be rendered. Annual reports to the Legislative Research Commission begin December 1, 2025. Administrative regulations implementing the statute are due by December 1, 2025.

## Obligations + coverage

### AI Governance Committee & centralized registry (KRS 42.731(1))

| Obligation | Coverage | Evidence |
|---|---|---|
| Develop policy standards and guiding principles adhering to ISO/IEC 42001 | ✅ ISO 42001 crosswalk + policy-standard tuple (cross-ref ISO/IEC 42001 coverage matrix) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/kernel/law_engine.py` |
| Establish technology standards and protocols for generative AI and high-risk AI systems | ✅ Capability-fence enforcement + output-validation gate + schema-validated deployment contracts | `hummbl_governance/capability_fence.py`, `hummbl_governance/output_validator.py`, `hummbl_governance/schema_validator.py` |
| Ensure transparency in the use of AI systems | ✅ Audit-log transparency tuples + compliance-mapper disclosure records | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Maintain centralized registry with current inventory of generative AI and high-risk AI systems | ✅ Immutable audit-log inventory + identity-engine system registration (cross-ref EU AI Act Art. 49 registry) | `hummbl_governance/audit_log.py`, `hummbl_governance/kernel/identity_engine.py` |
| Develop approval process with registry of application, use case, and decision rationale | ✅ Admission-control gate + authority-engine approval workflow + receipt-engine decision records | `hummbl_governance/kernel/admission_control.py`, `hummbl_governance/kernel/authority_engine.py`, `hummbl_governance/kernel/receipt_engine.py` |

### Agency compliance & documentation (KRS 42.731(2))

| Obligation | Coverage | Evidence |
|---|---|---|
| Verify the use and development of generative AI and high-risk AI systems | ✅ Evidence-engine verification tuples + audit-log attestation records | `hummbl_governance/kernel/evidence_engine.py`, `hummbl_governance/audit_log.py` |
| Ensure AI models have comprehensive and complete documentation available for review and inspection | ✅ Documentation-retention tuples + receipt-engine artifact registry + audit-log inspection export | `hummbl_governance/audit_log.py`, `hummbl_governance/kernel/receipt_engine.py`, `hummbl_governance/compliance_mapper.py` |
| Require review and intervention by humans for all outcomes from generative and high-risk AI, scaled to use case and risk | ✅ Human-oversight delegation token + authority-engine intervention gate + kill-switch halt (cross-ref EU AI Act Art. 14) | `hummbl_governance/delegation.py`, `hummbl_governance/kernel/authority_engine.py`, `hummbl_governance/kill_switch.py` |
| Ensure use of generative and high-risk AI is resilient, accountable, and explainable | ✅ Reasoning-engine explanation records + health-probe resilience checks + audit-log accountability chain | `hummbl_governance/reasoning.py`, `hummbl_governance/health_probe.py`, `hummbl_governance/audit_log.py` |

### Privacy, data protection & system review (KRS 42.731(3)-(4))

| Obligation | Coverage | Evidence |
|---|---|---|
| Allow only necessary data in AI systems; no unrestricted access to personal data controlled by the Commonwealth | ✅ Capability-fence data-scope enforcement + identity-based access control + cost-governor data-budget limits | `hummbl_governance/capability_fence.py`, `hummbl_governance/identity.py`, `hummbl_governance/cost_governor.py` |
| Secure all data and implement a timeframe for data retention | ✅ Audit-log retention-policy tuples + receipt-engine data-lifecycle records + lifecycle retention enforcement | `hummbl_governance/audit_log.py`, `hummbl_governance/kernel/receipt_engine.py`, `hummbl_governance/lifecycle.py` |
| All departments subject to review of generative and high-risk AI systems to maintain infrastructure security | ✅ Compliance-mapper review cycle + health-probe system checks + audit-log review export (cross-ref NIST AI RMF MEASURE) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/health_probe.py`, `hummbl_governance/audit_log.py` |

### Impact assessment & risk documentation (KRS 42.731(5))

| Obligation | Coverage | Evidence |
|---|---|---|
| Document how the AI system will not result in unlawful discrimination against any individual or group | ✅ Bias-assessment tuple + compliance-mapper discrimination-impact template (cross-ref EU AI Act Art. 27 FRIA, NIST AI RMF) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Document how AI benefits citizens and serves department objectives; document extent of oversight and human interaction required | 🟡 Partial: compliance-mapper captures benefit rationale and oversight-level records; substantive benefit assessment is org task | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/delegation.py` |
| Document potential risks (cybersecurity, data protection, privacy, health/safety) with mitigation strategy; document data control and management for security and data quality | ✅ STRIDE threat-model tuples + risk-treatment tuples + evidence-engine data-quality records (cross-ref STRIDE, NIST AI RMF) | `hummbl_governance/stride_mapper.py`, `hummbl_governance/compliance_mapper.py`, `hummbl_governance/kernel/evidence_engine.py` |

### Transparency & public disclosure (KRS 42.731(6))

| Obligation | Coverage | Evidence |
|---|---|---|
| Disclose to the public through clear and conspicuous disclaimer when AI is used to render decisions, inform decisions, or produce outputs | ✅ Output-validator disclosure gate + audit-log transparency tuples (cross-ref EU AI Act Art. 50, Colorado § 6-1-1704) | `hummbl_governance/output_validator.py`, `hummbl_governance/audit_log.py` |
| Disclose how AI is used in the decision-making process for external decisions affecting citizens | ✅ Reasoning-engine explanation records + compliance-mapper decision-disclosure template | `hummbl_governance/reasoning.py`, `hummbl_governance/compliance_mapper.py` |
| Provide the extent of human involvement in validating and oversight of any decision made | ✅ Delegation-token oversight records + authority-engine intervention log + audit-chain attestation | `hummbl_governance/delegation.py`, `hummbl_governance/kernel/authority_engine.py`, `hummbl_governance/audit_log.py` |
| Make readily available options for individuals to appeal a consequential decision involving AI | 🟡 Partial: audit-log records decisions and rationale for appeal support; appeal-workflow administration is org task | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Disclaimer shall include information about third-party AI products, including system cards or developer documentation | ✅ Documentation-registry tuples + compliance-mapper third-party-asset records + receipt-engine vendor-artifact storage | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py`, `hummbl_governance/kernel/receipt_engine.py` |

### High-risk AI risk management, reporting & administration (KRS 42.731(7)-(12))

| Obligation | Coverage | Evidence |
|---|---|---|
| Establish legal and ethical framework policies aligned to existing laws, updated at least annually | ✅ Law-engine policy registry + compliance-mapper legal-alignment crosswalk + audit-log annual-review records | `hummbl_governance/kernel/law_engine.py`, `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Prohibit consequential decisions from high-risk AI without a risk management policy specifying principles, process, personnel, and bias identification/mitigation/documentation | ✅ Admission-control gate blocks high-risk AI without risk-mgmt policy + compliance-mapper bias-mitigation template + kill-switch enforcement (cross-ref NIST AI RMF, EU AI Act Art. 9) | `hummbl_governance/kernel/admission_control.py`, `hummbl_governance/compliance_mapper.py`, `hummbl_governance/kill_switch.py` |
| Risk management policy adheres to ISO/IEC 42001 or equivalent, considering deployer size, system nature/scope, and data sensitivity/volume | ✅ ISO 42001 crosswalk + compliance-mapper context-aware risk-profile tuples (cross-ref ISO/IEC 42001 coverage matrix) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/kernel/law_engine.py` |
| Provide education and training of employees about AI benefits, risks, and allowable use policies | ⚪ Boundary: employee training delivery is organizational, not software-addressable | |
| Transmit annual reports to Legislative Research Commission including AI registry, applications with decision rationale, and third-party developers; receive departmental use-case reports | 🟡 Partial: compliance-mapper generates report content from audit-log and registry data; report transmission to legislature is org task | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py`, `hummbl_governance/kernel/receipt_engine.py` |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| AI Governance Committee & centralized registry (KRS 42.731(1)) | 5 | 5 | 0 | 0 |
| Agency compliance & documentation (KRS 42.731(2)) | 4 | 4 | 0 | 0 |
| Privacy, data protection & system review (KRS 42.731(3)-(4)) | 3 | 3 | 0 | 0 |
| Impact assessment & risk documentation (KRS 42.731(5)) | 3 | 2 | 1 | 0 |
| Transparency & public disclosure (KRS 42.731(6)) | 5 | 4 | 1 | 0 |
| High-risk AI risk mgmt, reporting & administration (KRS 42.731(7)-(12)) | 5 | 3 | 1 | 1 |
| **Totals** | **25** | **21** | **3** | **1** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- ISO/IEC 42001 alignment referenced in KRS 42.731(1)(a) and (8)(b) — see [`iso-42001.md`](./iso-42001.md)
- Transparency overlaps EU AI Act Art. 50 and Colorado § 6-1-1704 — see [`eu-ai-act.md`](./eu-ai-act.md), [`colorado-ai-act.md`](./colorado-ai-act.md)
- Human oversight overlaps EU AI Act Art. 14 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Risk management overlaps NIST AI RMF and EU AI Act Art. 9 — see [`nist-ai-rmf.md`](./nist-ai-rmf.md), [`eu-ai-act.md`](./eu-ai-act.md)
- Cybersecurity risk documentation overlaps STRIDE — see [`stride.md`](./stride.md)
- Impact assessment overlaps EU AI Act Art. 27 (FRIA) — see [`eu-ai-act.md`](./eu-ai-act.md)
