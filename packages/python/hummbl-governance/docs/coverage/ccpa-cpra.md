# CCPA/CPRA Coverage Matrix — HUMMBL

**Standard**: California Consumer Privacy Act as amended by the California Privacy Rights Act, California Civil Code §§ 1798.100-1798.199 and California Code of Regulations Title 11, Division 6, Chapter 1
**Effective**: CCPA January 1, 2020; CPRA amendments January 1, 2023; ADMT regulations January 1, 2026
**Source**: https://oag.ca.gov/privacy/ccpa
**Last reviewed**: 2026-05-14
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not California-licensed counsel and does not provide legal advice on CCPA/CPRA. The Act is enforced by the California Privacy Protection Agency (CPPA) and Attorney General with civil penalties. Statutory compliance is the customer-organization responsibility. HUMMBL maps technical primitives to the Act's automated decisionmaking technology (ADMT), risk assessment, privacy notice, and consumer rights obligations as they apply to AI systems.

## Scope summary

CCPA/CPRA applies to businesses meeting revenue, data-volume, or data-selling thresholds that process California consumers' personal information. The ADMT regulations (effective January 1, 2026) impose specific obligations on businesses using AI/ADMT to make significant decisions about consumers, including pre-use notice, opt-out, access, and risk assessment requirements.

## Obligations + coverage

### ADMT definitions and scope (Reg. § 7001)

| Obligation | Coverage | Evidence |
|---|---|---|
| ADMT definition — technology that processes personal information and uses computation to replace/substantially replace human decisionmaking | ✅ ADMT-classification tuple + decision-automation-detection primitive | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Human involvement criteria — reviewer must know how to interpret output, review it, and have authority to make/change decision | ✅ Human-oversight-verification tuple + delegation-authority primitive (cross-ref EU AI Act Art. 14) | `hummbl_governance/delegation.py`, `hummbl_governance/identity.py` |
| Profiling inclusion — ADMT includes profiling that replaces/substantially replaces human decisionmaking | ✅ Profiling-detection tuple + decision-classification primitive | `hummbl_governance/audit_log.py` |

### Pre-use notice requirements (Reg. § 7220)

| Obligation | Coverage | Evidence |
|---|---|---|
| Provide Pre-use Notice before using ADMT for significant decisions | ✅ Pre-use-notification primitive + timing-gate (cross-ref EU AI Act Art. 50) | `hummbl_governance/audit_log.py`, `hummbl_governance/lifecycle.py` |
| Plain language explanation of specific purpose for ADMT use | ✅ Purpose-disclosure tuple + plain-language-validation primitive | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/output_validator.py` |
| Describe consumer's right to opt-out of ADMT and how to submit request | ✅ Opt-out-right-disclosure tuple + request-method tuple | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Inform consumer of human appeal option when opt-out exception applies | ✅ Appeal-right-disclosure tuple + human-review-delegation | `hummbl_governance/audit_log.py`, `hummbl_governance/delegation.py` |
| Identify specific exception relied upon when opt-out not required | ✅ Exception-identification tuple + compliance-record | `hummbl_governance/audit_log.py` |
| Describe consumer's right to access ADMT and how to submit request | ✅ Access-right-disclosure tuple + request-method tuple | `hummbl_governance/audit_log.py` |
| State non-retaliation prohibition for exercising CCPA rights | ✅ Non-retaliation-notice tuple | `hummbl_governance/audit_log.py` |
| Include additional information about how ADMT works for significant decisions | ✅ ADMT-explanation tuple + transparency primitive | `hummbl_governance/compliance_mapper.py` |

### Opt-out requirements (Reg. § 7221)

| Obligation | Coverage | Evidence |
|---|---|---|
| Provide ability to opt-out of ADMT for significant decisions | ✅ Opt-out-request-handling primitive + decision-exclusion tuple | `hummbl_governance/audit_log.py`, `hummbl_governance/delegation.py` |
| Provide two or more designated opt-out methods | 🟡 Partial: opt-out-request primitive supports multiple channels; channel deployment is org task | `hummbl_governance/audit_log.py` |
| Methods must be easy to use, no dark patterns | ✅ Dark-pattern-detection tuple + usability-validation primitive | `hummbl_governance/output_validator.py` |
| Collect only personal information necessary for opt-out processing | ✅ Data-minimization primitive + collection-scope tuple | `hummbl_governance/delegation.py`, `hummbl_governance/schema_validator.py` |
| Confirm receipt of opt-out request within 10 business days | ✅ 10-business-day-SLA primitive + confirmation tuple | `hummbl_governance/audit_log.py`, `hummbl_governance/lifecycle.py` |
| Honor opt-out within 15 business days | ✅ 15-business-day-SLA primitive + execution-gate | `hummbl_governance/audit_log.py`, `hummbl_governance/lifecycle.py` |
| Honor opt-out for at least 12 months | ✅ 12-month-retention tuple + opt-out-duration primitive | `hummbl_governance/lifecycle.py`, `hummbl_governance/audit_log.py` |
| Allow consumer to renew opt-out request | ✅ Renewal-request primitive + opt-out-lifecycle | `hummbl_governance/audit_log.py` |

### Access to ADMT requirements (Reg. § 7222)

| Obligation | Coverage | Evidence |
|---|---|---|
| Provide information about ADMT use when responding to access requests | ✅ Access-response tuple + ADMT-info-disclosure primitive | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Plain language explanation of specific purpose for ADMT use | ✅ Purpose-disclosure tuple (cross-ref Pre-use Notice) | `hummbl_governance/compliance_mapper.py` |
| Plain language explanation of role ADMT plays in decisionmaking process | ✅ Role-explanation tuple + transparency primitive | `hummbl_governance/compliance_mapper.py` |
| Non-retaliation notice and instructions for exercising other CCPA rights | ✅ Non-retaliation-notice tuple + rights-instruction tuple | `hummbl_governance/audit_log.py` |
| Easy-to-use request methods, no dark patterns | ✅ Dark-pattern-detection tuple + usability-validation | `hummbl_governance/output_validator.py` |
| Comply with verification requirements for access requests | ✅ Identity-verification tuple + authentication primitive | `hummbl_governance/identity.py`, `hummbl_governance/audit_log.py` |
| Inform requestor if identity cannot be verified | ✅ Verification-failure-notice tuple | `hummbl_governance/audit_log.py` |
| Explain basis for denial if request conflicts with law or CCPA exception | ✅ Denial-explanation tuple + exception-record | `hummbl_governance/audit_log.py` |
| Disclose non-denied information for partial denials | ✅ Partial-disclosure tuple + response-primitive | `hummbl_governance/audit_log.py` |
| Use reasonable security measures when transmitting requested information | ✅ Secure-transmission tuple + encryption primitive (cross-ref GDPR Art. 32) | `hummbl_governance/audit_log.py` |

### Risk assessment requirements (Reg. § 7152)

| Obligation | Coverage | Evidence |
|---|---|---|
| Conduct risk assessments for processing presenting significant privacy/security risk | ✅ Risk-assessment template + assessment-scheduling primitive (cross-ref EU AI Act Art. 9, NIST AI RMF) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Perform annual cybersecurity audits | ✅ Annual-audit-scheduling primitive + audit-evidence tuple | `hummbl_governance/lifecycle.py`, `hummbl_governance/audit_log.py` |
| Submit risk assessments to CPPA on regular basis | 🟡 Partial: risk-assessment generator produces content; submission is org task | `hummbl_governance/compliance_mapper.py` |
| Identify and document categories of sensitive personal information | ✅ Sensitive-data-classification tuple + data-classification primitive (cross-ref GDPR Art. 9) | `hummbl_governance/schema_validator.py`, `hummbl_governance/audit_log.py` |
| Weigh benefits against risks with goal of restricting processing if risks outweigh benefits | ✅ Risk-benefit-analysis tuple + risk-treatment primitive | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Create risk assessment report with specified information | ✅ Assessment-report generator + documentation tuple | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Risk assessments do not require divulging trade secrets | ⚪ Boundary: trade-secret protection is legal determination | |

### Privacy notice requirements (Civil Code § 1798.130)

| Obligation | Coverage | Evidence |
|---|---|---|
| Provide Notice at Collection for personal information collection | ✅ Notice-at-collection primitive + disclosure tuple | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Identify business purposes for collecting personal information | ✅ Purpose-disclosure tuple + purpose-limitation primitive | `hummbl_governance/audit_log.py` |
| Identify categories of personal information to be collected | ✅ Data-category-disclosure tuple + classification primitive | `hummbl_governance/schema_validator.py`, `hummbl_governance/audit_log.py` |
| Disclose consumer rights (know, delete, correct, opt-out, limit, ADMT opt-out, ADMT access) | ✅ Rights-disclosure tuple + rights-catalog primitive | `hummbl_governance/compliance_mapper.py` |
| State non-retaliation right for exercising privacy rights | ✅ Non-retaliation-notice tuple | `hummbl_governance/audit_log.py` |
| Include instructions for exercising CCPA rights and process expectations | ✅ Rights-exercise-instruction tuple + process-disclosure | `hummbl_governance/compliance_mapper.py` |

### Consumer rights applicable to AI

| Obligation | Coverage | Evidence |
|---|---|---|
| Right to know about personal information collected, including AI-generated inferences | ✅ Access-response tuple + inference-disclosure primitive | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Right to delete personal information including AI-generated inferences | ✅ Deletion-request-handling tuple + data-removal primitive (cross-ref GDPR Art. 17) | `hummbl_governance/audit_log.py` |
| Right to correct inaccurate personal information including AI-generated inferences | ✅ Rectification tuple + correction primitive (cross-ref GDPR Art. 16) | `hummbl_governance/audit_log.py` |
| Right to opt-out of sale or sharing including AI-generated profiles | ✅ Opt-out-request-handling tuple + sale/sharing-exclusion | `hummbl_governance/audit_log.py` |
| Right to limit use of sensitive personal information in AI systems | ✅ Sensitive-data-limitation tuple + use-restriction primitive | `hummbl_governance/schema_validator.py`, `hummbl_governance/audit_log.py` |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| ADMT definitions (Reg. § 7001) | 3 | 3 | 0 | 0 |
| Pre-use notice (Reg. § 7220) | 8 | 8 | 0 | 0 |
| Opt-out (Reg. § 7221) | 8 | 7 | 1 | 0 |
| Access to ADMT (Reg. § 7222) | 10 | 10 | 0 | 0 |
| Risk assessment (Reg. § 7152) | 7 | 5 | 1 | 1 |
| Privacy notice (§ 1798.130) | 6 | 6 | 0 | 0 |
| Consumer rights for AI | 5 | 5 | 0 | 0 |
| **Totals** | **47** | **44** | **2** | **1** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Consumer rights overlap GDPR Arts. 15-22 — see [`gdpr.md`](./gdpr.md)
- Risk assessment overlaps EU AI Act Art. 9 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Human oversight overlaps EU AI Act Art. 14 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Data classification overlaps ISO 27001 A.5.12-A.5.13 — see [`iso-27001.md`](./iso-27001.md)
