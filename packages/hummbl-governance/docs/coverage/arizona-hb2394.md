# Arizona AI Laws Coverage Matrix — HUMMBL

**Standard**: Arizona AI Laws — HB 2394 (A.R.S. § 16-1023), SB 1295, HB 2678, HB 2175
**Effective**: HB 2394 May 21, 2024 · SB 1295 2024 · HB 2678 2025 · HB 2175 July 1, 2026
**Source**: https://www.recordinglaw.com/us-laws/ai-laws/arizona-ai-laws/
**Last reviewed**: 2026-06-25
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not Arizona legal counsel and does not provide legal advice on HB 2394, SB 1295, HB 2678, or HB 2175. Arizona regulates AI through targeted, sector-specific statutes rather than a comprehensive framework. The four enacted bills address election deepfakes, AI voice fraud, AI-generated child exploitation material, and healthcare AI claim denials. Statutory compliance is the customer-organization responsibility. HUMMBL maps technical primitives to the detection, labeling, human-oversight, and audit-retention obligations that are software-addressable; criminal penalties, civil liability, and regulatory enforcement actions are organizational and legal matters outside HUMMBL's scope.

## Scope summary

Arizona's enacted AI laws apply to distinct actor categories per bill: HB 2394 (A.R.S. § 16-1023) governs publishers of deepfake media depicting political candidates (during the 180-day pre-election window) and private citizens; SB 1295 criminalizes AI-generated voice, image, or video impersonation used for fraud or harassment as a Class 5 felony; HB 2678 extends child exploitation statutes to AI-generated or digitally manipulated imagery indistinguishable from real minors (dangerous crime against children when the depicted victim appears under age 15); HB 2175 (effective July 1, 2026) prohibits health insurers from using AI as the sole basis for medical claim denials, requiring a licensed medical director to exercise independent judgment on denials involving medical necessity. The Arizona Department of Administration's Generative AI Policy (P2000) separately governs state agency AI use but is administrative, not statutory.

## Obligations + coverage

### HB 2394 — Election deepfake protection (A.R.S. § 16-1023)

| Obligation | Coverage | Evidence |
|---|---|---|
| Prohibit publication of deepfake media depicting candidates or citizens nude, in sexual acts, committing crimes, or suffering financial/reputational harm | ✅ Output-validation gate with content-classification tuples + capability-fence content blocking (cross-ref EU AI Act Art. 50(2), South Korea Art. 31) | `hummbl_governance/output_validator.py`, `hummbl_governance/capability_fence.py` |
| Apply candidate protections during the 180-day period before a scheduled election | ✅ Temporal-scope enforcement via schedule-engine election-window gating + compliance-mapper rule activation | `hummbl_governance/kernel/schedule_engine.py`, `hummbl_governance/compliance_mapper.py` |
| Establish "actual knowledge" standard — liability attaches when publisher knows content is a digital impersonation | ✅ Audit-log knowledge-attestation tuple + receipt-engine signed-knowledge record | `hummbl_governance/audit_log.py`, `hummbl_governance/kernel/receipt_engine.py` |
| Provide 21-day corrective-action safe harbor after gaining actual knowledge | 🟡 Partial: lifecycle remediation tracking records corrective action and timestamps; legal safe-harbor determination is org task | `hummbl_governance/lifecycle.py`, `hummbl_governance/audit_log.py` |
| Enable victims to seek civil injunctive relief and monetary damages through state courts | ⚪ Boundary: civil-litigation remedy is legal, not software-addressable | |

### SB 1295 — AI voice fraud (Class 5 felony)

| Obligation | Coverage | Evidence |
|---|---|---|
| Detect and block AI-generated voice recordings, images, or videos used for fraud or harassment | ✅ Output-validator impersonation-detection gate + capability-fence synthesis restriction (cross-ref EU AI Act Art. 50(4)) | `hummbl_governance/output_validator.py`, `hummbl_governance/capability_fence.py` |
| Classify AI-based impersonation offenses at Class 5 felony severity (above standard Class 6) | ⚪ Boundary: criminal classification and sentencing is legal, not software-addressable | |
| Preserve protected-speech exemptions for comedy, parody, art, criticism, and obviously edited media | ✅ Output-validator exemption-classification tuple + reasoning-engine context evaluation for satire/parody detection | `hummbl_governance/output_validator.py`, `hummbl_governance/reasoning.py` |
| Maintain identity-provenance chain to distinguish authorized voice/image use from fraudulent impersonation | ✅ Identity-registry agent binding + delegation-token authorization chain + audit-log provenance record | `hummbl_governance/identity.py`, `hummbl_governance/delegation.py`, `hummbl_governance/audit_log.py` |

### HB 2678 — AI-generated child exploitation material

| Obligation | Coverage | Evidence |
|---|---|---|
| Detect and block AI-generated or digitally manipulated images depicting minors indistinguishable from real children | ✅ Output-validator content-classification gate with minor-depiction blocking + capability-fence generation prohibition (cross-ref EU AI Act Art. 5 prohibited practices) | `hummbl_governance/output_validator.py`, `hummbl_governance/capability_fence.py` |
| Apply indistinguishability standard — computer-generated images indistinguishable from actual children trigger exploitation statutes | ✅ Output-validator confidence-threshold gate + reasoning-engine indistinguishability assessment | `hummbl_governance/output_validator.py`, `hummbl_governance/reasoning.py` |
| Escalate content depicting victims appearing under age 15 to dangerous-crime-against-children severity | ✅ Kill-switch immediate-halt mode + circuit-breaker fast-fail on detected minor-exploitation content | `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py` |
| Apply existing child exploitation criminal penalties to AI-generated content | ⚪ Boundary: criminal prosecution and penalty assessment is legal, not software-addressable | |

### HB 2175 — Healthcare AI claim denial prohibition (effective July 1, 2026)

| Obligation | Coverage | Evidence |
|---|---|---|
| Require medical director to individually review claim denials and prior-authorization denials involving medical necessity | ✅ Human-oversight delegation token with mandatory-review gate + authority-engine human-approval requirement before denial issuance (cross-ref EU AI Act Art. 14, South Korea Art. 34) | `hummbl_governance/delegation.py`, `hummbl_governance/kernel/authority_engine.py` |
| Medical director must exercise independent medical judgment — cannot rely solely on AI-generated recommendations | ✅ Reasoning-engine independent-judgment attestation + convergence-guard human-override verification | `hummbl_governance/reasoning.py`, `hummbl_governance/convergence_guard.py` |
| Medical director must hold active, unrestricted Arizona medical license | ✅ Identity-registry credential-verification tuple + delegation-token license-attestation binding | `hummbl_governance/identity.py`, `hummbl_governance/delegation.py` |
| Written denials must include explanation of why treatment was denied | ✅ Audit-log denial-explanation tuple + compliance-mapper explanation-disclosure generator (cross-ref South Korea Art. 34 explanation plan) | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Prevent AI from serving as the sole/final decision-maker on medical necessity denials | ✅ Kill-switch halt-before-final-denial mode + circuit-breaker human-in-the-loop enforcement gate | `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py` |

### Enforcement, penalties & federal interaction

| Obligation | Coverage | Evidence |
|---|---|---|
| Support Arizona Attorney General investigations with audit-trail export and evidence production (e.g., Grok investigation) | 🟡 Partial: audit-log export + compliance-report generator supports investigation; cooperation act is org task | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Criminal penalties for AI voice fraud (Class 5 felony) and AI-generated child exploitation (dangerous crime against children) | ⚪ Boundary: criminal liability and prosecution is legal, not software-addressable | |
| Navigate federal preemption tension under Executive Order 14365 — child-safety and election laws preserved, healthcare AI may face scrutiny | ⚪ Boundary: federal-state preemption analysis is legal determination, not software-addressable | |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| HB 2394 — Election deepfakes (A.R.S. § 16-1023) | 5 | 3 | 1 | 1 |
| SB 1295 — AI voice fraud (Class 5 felony) | 4 | 3 | 0 | 1 |
| HB 2678 — AI child exploitation material | 4 | 3 | 0 | 1 |
| HB 2175 — Healthcare AI claim denial | 5 | 5 | 0 | 0 |
| Enforcement, penalties & federal interaction | 3 | 0 | 1 | 2 |
| **Totals** | **21** | **14** | **2** | **5** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Deepfake labeling overlaps EU AI Act Art. 50(2) — see [`eu-ai-act.md`](./eu-ai-act.md)
- Deepfake labeling overlaps South Korea AI Basic Act Art. 31 — see [`south-korea-ai-basic-act.md`](./south-korea-ai-basic-act.md)
- Human oversight overlaps EU AI Act Art. 14 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Human oversight overlaps South Korea AI Basic Act Art. 34 — see [`south-korea-ai-basic-act.md`](./south-korea-ai-basic-act.md)
- Prohibited-practice blocking overlaps EU AI Act Art. 5 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Healthcare AI human-in-the-loop overlaps Colorado AI Act deployer disclosure — see [`colorado-ai-act.md`](./colorado-ai-act.md)
- Risk management overlaps NIST AI RMF — see [`nist-ai-rmf.md`](./nist-ai-rmf.md)
