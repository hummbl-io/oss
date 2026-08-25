# New Hampshire Chapter 5-D Coverage Matrix — HUMMBL

**Standard**: New Hampshire Revised Statutes Annotated, Chapter 5-D — Use of Artificial Intelligence by State Agencies (RSA 5-D:1–5-D:6)
**Effective**: July 1, 2024
**Source**: https://gc.nh.gov/rsa/html/I/5-D/5-D-mrg.htm
**Last reviewed**: 2026-06-25
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not New Hampshire legal counsel and does not provide legal advice on Chapter 5-D. The chapter governs "state agencies" as defined in RSA 5-D:1, IV — any department, commission, board, institution, bureau, office, law-enforcement, or other entity of the legislative or judicial branches. Statutory compliance is the customer-organization responsibility. HUMMBL maps technical primitives to the chapter's prohibition, human-review, transparency, and compliance-reporting obligations.

## Scope summary

Chapter 5-D applies to all computer systems operated by any New Hampshire state agency. Excepted are systems used in research by state-funded institutions of higher learning and installed consumer systems in common personal use (e.g. facial recognition to unlock a smartphone). The chapter prohibits discriminatory classification, public-space biometric surveillance (absent a warrant), and deceptive deepfakes. It mandates human review of irreversible AI decisions, generative-AI content disclosure, AI-interaction notification, and a 9-month compliance review with annual DoIT reporting.

## Obligations + coverage

### Definitions & applicability (§§ 5-D:1, 5-D:2)

| Obligation | Coverage | Evidence |
|---|---|---|
| AI, generative AI, and deepfake definitions for scoping | ⚪ Boundary: statutory definitions are legal determinations, not software-addressable | |
| Chapter applies to all computer systems operated by any state agency | ⚪ Boundary: organizational scoping of "state agency" systems is a legal/procurement determination | |
| Exception for research systems at state-funded higher-education institutions | ⚪ Boundary: institutional-research exemption is an organizational classification | |
| Exception for installed consumer systems in common personal use (e.g. smartphone facial recognition) | ⚪ Boundary: consumer-use exemption is an organizational classification | |

### Prohibited uses (§ 5-D:3)

| Obligation | Coverage | Evidence |
|---|---|---|
| Prohibition on classifying persons by behavior, socio-economic status, or personal characteristics resulting in unlawful discrimination | ✅ Output-validation gate rejects discriminatory outputs + capability fence restricts classification capabilities + compliance-mapper bias-assessment template (cross-ref EU AI Act Art. 10, NIST AI RMF MEASURE-2.11) | `hummbl_governance/output_validator.py`, `hummbl_governance/capability_fence.py`, `hummbl_governance/compliance_mapper.py` |
| Prohibition on real-time/remote biometric identification for public-space surveillance, except law enforcement with a warrant | ✅ Capability fence blocks biometric-surveillance capability + compliance-mapper prohibited-use tuple with warrant-exception condition | `hummbl_governance/capability_fence.py`, `hummbl_governance/compliance_mapper.py` |
| Prohibition on deepfakes used for deceptive or malicious purposes | ✅ Output validator content-authenticity gate + capability fence restricts synthetic-media generation (cross-ref South Korea AI Basic Act Art. 31 deepfake labeling) | `hummbl_governance/output_validator.py`, `hummbl_governance/capability_fence.py` |

### Permitted uses & restrictions (§ 5-D:4)

| Obligation | Coverage | Evidence |
|---|---|---|
| Human review of irreversible AI recommendations/decisions before they take effect | ✅ Human-oversight delegation token requires named reviewer + lifecycle gate blocks execution until review-approval recorded (cross-ref EU AI Act Art. 14, South Korea Art. 34) | `hummbl_governance/delegation.py`, `hummbl_governance/lifecycle.py` |
| Human review required for irreversible decisions affecting rights/freedoms, biometric ID, critical infrastructure, law enforcement, and sentencing/ statutory interpretation | ✅ Authority-engine policy gate enforces review for high-impact domains + law-engine ties decisions to statutory authority + physical-governor for critical-infrastructure actions | `hummbl_governance/kernel/authority_engine.py`, `hummbl_governance/kernel/law_engine.py`, `hummbl_governance/physical_governor.py` |
| Disclosure that unreviewed generative-AI content was AI-generated | ✅ Provenance-labeling tuple type + output-validation gate enforces AI-generation disclosure on unreviewed gen-AI material (cross-ref South Korea Art. 31, Colorado § 6-1-1704) | `hummbl_governance/output_validator.py`, `hummbl_governance/audit_log.py` |
| Notify users they are interacting with an AI system (directly or indirectly) | ✅ Transparency-notification primitive + audit-log records interaction-disclosure event (cross-ref EU AI Act Art. 50) | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |

### Compliance (§ 5-D:5)

| Obligation | Coverage | Evidence |
|---|---|---|
| Review all AI use in agency computer systems within 9 months; remove prohibited systems | ✅ Compliance-mapper inventory + assessment template identifies prohibited uses + kill-switch removes/halts prohibited systems | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py`, `hummbl_governance/kill_switch.py` |
| Modify inconsistent AI-use procedures to align with chapter requirements | 🟡 Partial: compliance-mapper gap-analysis identifies inconsistent procedures; procedure modification is an organizational task | `hummbl_governance/compliance_mapper.py` |
| Newly deployed AI systems must comply with chapter and DoIT code of ethics | ✅ Admission-control gate blocks deployment of non-compliant systems + compliance-mapper pre-deployment assessment + schema-validator validates ethics-code attestation | `hummbl_governance/kernel/admission_control.py`, `hummbl_governance/compliance_mapper.py`, `hummbl_governance/schema_validator.py` |
| DoIT annual report to governor, House speaker, and Senate president summarizing AI systems (prohibited/removed, allowed, procurement procedures) | 🟡 Partial: compliance-mapper report generator produces the summary report; legislative submission is an organizational task | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Annual report posted on DoIT website | ⚪ Boundary: website publication is an organizational communications task, not software-addressable | |

### Severability (§ 5-D:6)

| Obligation | Coverage | Evidence |
|---|---|---|
| Severability of chapter provisions | ⚪ Boundary: legal severability doctrine is a judicial determination, not software-addressable | |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| Definitions & applicability (§§ 5-D:1–5-D:2) | 4 | 0 | 0 | 4 |
| Prohibited uses (§ 5-D:3) | 3 | 3 | 0 | 0 |
| Permitted uses & restrictions (§ 5-D:4) | 4 | 4 | 0 | 0 |
| Compliance (§ 5-D:5) | 5 | 2 | 2 | 1 |
| Severability (§ 5-D:6) | 1 | 0 | 0 | 1 |
| **Totals** | **17** | **9** | **2** | **6** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Transparency / AI-interaction disclosure overlaps EU AI Act Art. 50 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Human oversight of irreversible decisions overlaps EU AI Act Art. 14 and South Korea Art. 34 — see [`eu-ai-act.md`](./eu-ai-act.md), [`south-korea-ai-basic-act.md`](./south-korea-ai-basic-act.md)
- Bias/discrimination prohibition overlaps EU AI Act Art. 10 and NIST AI RMF MEASURE-2.11 — see [`eu-ai-act.md`](./eu-ai-act.md), [`nist-ai-rmf.md`](./nist-ai-rmf.md)
- Generative-AI content disclosure overlaps South Korea Art. 31 and Colorado § 6-1-1704 — see [`south-korea-ai-basic-act.md`](./south-korea-ai-basic-act.md), [`colorado-ai-act.md`](./colorado-ai-act.md)
- Deepfake prohibition overlaps South Korea AI Basic Act Art. 31 deepfake labeling — see [`south-korea-ai-basic-act.md`](./south-korea-ai-basic-act.md)
