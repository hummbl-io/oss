# Virginia HB 714 / VCDPA Coverage Matrix — HUMMBL

**Standard**: Virginia Consumer Data Protection Act (VCDPA), Va. Code Ann. §§ 59.1-575 to 59.1-585 (HB 714, 2022 Session — Chapter 451; amended 2024 cc. 840/844; amended 2026 Chapter 820)
**Effective**: January 1, 2023 (original VCDPA); 2026 amendments effective per Chapter 820
**Source**: https://law.lis.virginia.gov/vacode/title59.1/chapter53/
**Last reviewed**: 2026-06-25
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not Virginia legal counsel and does not provide legal advice on the VCDPA or HB 714. The VCDPA applies to controllers and processors conducting business in Virginia or producing products/services targeted to Virginia residents, subject to revenue and data-volume thresholds (100,000+ Virginia consumers or 25,000+ consumers with >50% gross revenue from data sale). The Act grants the Virginia Attorney General exclusive enforcement authority — there is no private right of action. Statutory compliance is the customer-organization responsibility. HUMMBL maps technical primitives to the Act's consumer-rights, data-protection-assessment, profiling-opt-out, sensitive-data, and transparency obligations.

## Scope summary

The VCDPA applies to persons that conduct business in Virginia or produce products/services targeted to Virginia residents, and that (1) control or process personal data of at least 100,000 Virginia consumers in a calendar year, or (2) control or process personal data of at least 25,000 Virginia consumers and derive over 50% of gross revenue from the sale of personal data. Nonprofit organizations (including political organizations and certain § 501(c)(4) entities per HB 714), state and local government entities, and data covered by GLBA, HIPAA, FERPA, and certain other federal laws are exempt. The Act's AI-relevant provisions center on profiling (automated processing of personal data to evaluate, analyze, or predict personal aspects), the consumer right to opt out of profiling that produces legal or similarly significant effects, mandatory data protection assessments for profiling and sensitive-data processing, and consent requirements for sensitive data including children's data.

## Obligations + coverage

### Consumer data rights (§ 59.1-577)

| Obligation | Coverage | Evidence |
|---|---|---|
| Right to confirm whether controller is processing personal data and to access such data | ✅ Audit-log processing records + compliance-mapper access-confirmation report | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Right to correct inaccuracies in personal data | 🟡 Partial: audit log records correction requests and timestamps; correction execution across downstream data stores is org task | `hummbl_governance/audit_log.py` |
| Right to delete personal data (incl. third-party-source alternative: retain deletion record or opt-out) | 🟡 Partial: lifecycle + audit log track deletion requests and minimum retention records; deletion execution across systems is org task | `hummbl_governance/lifecycle.py`, `hummbl_governance/audit_log.py` |
| Right to obtain copy of personal data in portable, readily usable format | 🟡 Partial: audit log + compliance mapper can export consumer data; portability format and transfer mechanism are org task | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Right to opt out of processing for targeted advertising, sale of personal data, or profiling with legal/significant effects | ✅ Capability fence + output validator enforce opt-out processing constraints at system boundary (cross-ref Colorado § 6-1-1305, Connecticut SB 2) | `hummbl_governance/capability_fence.py`, `hummbl_governance/output_validator.py` |

### Controller responsibilities & transparency (§ 59.1-578)

| Obligation | Coverage | Evidence |
|---|---|---|
| Data minimization — limit collection to what is adequate, relevant, and reasonably necessary | ✅ Cost governor enforces collection/processing budgets + capability fence constrains data-scope access | `hummbl_governance/cost_governor.py`, `hummbl_governance/capability_fence.py` |
| Purpose limitation — no processing incompatible with disclosed purposes without consent | ✅ Capability fence + schema validator enforce purpose-bound processing constraints | `hummbl_governance/capability_fence.py`, `hummbl_governance/schema_validator.py` |
| Establish and maintain reasonable administrative, technical, and physical data security practices | ✅ Audit-log integrity chain + identity registry + kernel evidence engine provide security evidence and access controls | `hummbl_governance/audit_log.py`, `hummbl_governance/identity.py`, `hummbl_governance/kernel/evidence_engine.py` |
| No discrimination against consumers for exercising consumer rights | 🟡 Partial: audit log records rights-exercise events for evidence; non-discrimination policy enforcement is org task | `hummbl_governance/audit_log.py` |
| Privacy notice with categories of data, purpose, rights instructions, third-party sharing categories | 🟡 Partial: compliance mapper generates notice content with required fields; publication and maintenance are org task | `hummbl_governance/compliance_mapper.py` |
| Secure, authenticated means for consumers to submit rights requests; no new account required | ✅ Identity registry authenticates requestors + kernel identity engine validates identity + audit log records requests | `hummbl_governance/identity.py`, `hummbl_governance/kernel/identity_engine.py` |

### Sensitive data, child protections & data protection assessments (§§ 59.1-578, 59.1-580)

| Obligation | Coverage | Evidence |
|---|---|---|
| Obtain consumer consent before processing sensitive data (race, religion, health, sexual orientation, genetic/biometric, child data, precise geolocation) | ✅ Identity registry + delegation token capture and verify consent state before processing | `hummbl_governance/identity.py`, `hummbl_governance/delegation.py` |
| No targeted advertising, sale, or profiling of children's data without parental consent per COPPA (§ 59.1-578.F) | ✅ Capability fence blocks child-data processing + identity registry verifies parental consent tokens | `hummbl_governance/capability_fence.py`, `hummbl_governance/identity.py` |
| No sale or offer for sale of precise geolocation data (2026 Chapter 820 amendment, § 59.1-578.A.6) | ✅ Capability fence + output validator block geolocation-data sale transactions at system boundary | `hummbl_governance/capability_fence.py`, `hummbl_governance/output_validator.py` |
| Data protection assessment for profiling with foreseeable risk of unfair/deceptive treatment, disparate impact, injury, or intrusion (§ 59.1-580.A.3) | ✅ Compliance-mapper impact-assessment template + audit-log risk tuples (cross-ref EU AI Act Art. 27 FRIA, NIST AI RMF) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Data protection assessment for sensitive data processing and heightened-risk processing activities (§ 59.1-580.A.4–5) | ✅ Compliance-mapper assessment template with sensitive-data and heightened-risk components | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Data protection assessment for online services directed to children; weigh benefits vs risks, factor de-identified data and consumer expectations (§ 59.1-580.B–C) | ✅ Compliance-mapper child-directed assessment template + risk-benefit weighing + audit-log documentation | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Disclose profiling, targeted advertising, or sale processing clearly and conspicuously; describe opt-out mechanism (§ 59.1-578.D) | 🟡 Partial: compliance mapper generates disclosure content; conspicuous publication in privacy notice is org task | `hummbl_governance/compliance_mapper.py` |

### Controller-processor relationships (§ 59.1-579)

| Obligation | Coverage | Evidence |
|---|---|---|
| Processor adheres to controller instructions and assists with consumer rights requests | ✅ Delegation token binds processor to controller instructions + coordination bus routes rights requests | `hummbl_governance/delegation.py`, `hummbl_governance/coordination_bus.py` |
| Processor assists controller with security obligations and breach notification | 🟡 Partial: audit log + health probe detect and log security events; breach notification delivery to consumers is org task | `hummbl_governance/audit_log.py`, `hummbl_governance/health_probe.py` |
| Contract must govern processing: confidentiality, deletion/return, compliance demonstration, assessment cooperation, subcontractor flow-down | 🟡 Partial: compliance mapper generates contract requirements checklist + delegation token encodes processing scope; contract execution is org task | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/delegation.py` |
| Processor provides information for DPAs and allows controller or independent assessor assessments | ✅ Audit-log export + compliance-mapper evidence report support assessment requests | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |

### Enforcement & investigation (§§ 59.1-583, 59.1-584)

| Obligation | Coverage | Evidence |
|---|---|---|
| Attorney General exclusive enforcement; 30-day cure period before action | ⚪ Boundary: regulatory enforcement process and cure-period response are organizational | |
| AG may request data protection assessments via civil investigative demand; controller must produce | 🟡 Partial: audit-log export + compliance-mapper DPA report support production; response to CID is org task | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Civil penalties up to $7,500 per violation; no private right of action | ⚪ Boundary: penalty exposure and legal-standing determinations are legal, not software-addressable | |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| Consumer data rights (§ 59.1-577) | 5 | 2 | 3 | 0 |
| Controller responsibilities & transparency (§ 59.1-578) | 6 | 4 | 2 | 0 |
| Sensitive data, child protections & DPAs (§§ 59.1-578, 59.1-580) | 7 | 6 | 1 | 0 |
| Controller-processor relationships (§ 59.1-579) | 4 | 2 | 2 | 0 |
| Enforcement & investigation (§§ 59.1-583, 59.1-584) | 3 | 0 | 1 | 2 |
| **Totals** | **25** | **14** | **9** | **2** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Profiling opt-out overlaps Colorado AI Act § 6-1-1305 — see [`colorado-ai-act.md`](./colorado-ai-act.md)
- Profiling opt-out overlaps Connecticut SB 2 — see [`connecticut-sb2-sb5.md`](./connecticut-sb2-sb5.md)
- Data protection assessments overlap EU AI Act Art. 27 (FRIA) — see [`eu-ai-act.md`](./eu-ai-act.md)
- Risk management overlaps NIST AI RMF — see [`nist-ai-rmf.md`](./nist-ai-rmf.md)
- Consumer rights overlap CCPA/CPRA — see [`ccpa-cpra.md`](./ccpa-cpra.md)
- Sensitive-data consent overlaps GDPR Art. 9 — see [`gdpr.md`](./gdpr.md)
