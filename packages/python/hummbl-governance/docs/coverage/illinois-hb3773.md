# Illinois IHRA AI Amendment (HB 3773) Coverage Matrix — HUMMBL

**Standard**: Illinois House Bill 3773 — Public Act 103-0804, amending the Illinois Human Rights Act (775 ILCS 5/2-101, 2-102), Employment Article
**Effective**: January 1, 2026
**Source**: https://reg-intel.com/us-state-ai-laws-tracker/
**Last reviewed**: 2026-06-25
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is **not** Illinois-licensed counsel and does not provide legal advice on HB 3773 or the IHRA. The amendment imposes employer liability for algorithmic discrimination **without a statutory affirmative defense** — unlike Colorado SB 24-205, which offers a safe harbor for adopting a recognized risk-management framework. Statutory compliance is the customer-organization responsibility. HUMMBL maps technical primitives to the amendment's non-discrimination, notice, and evidence-retention obligations.

## Scope summary

HB 3773 amends Article 5 (Employment) of the Illinois Human Rights Act (775 ILCS 5/2-101, 2-102). It applies to employers employing one or more employees within Illinois during 20 or more calendar weeks within the calendar year of or preceding the alleged violation. The amendment prohibits employers from using AI — including generative AI — that has the effect of subjecting employees to discrimination on the basis of protected classes under the IHRA, or from using zip codes as a proxy for protected classes, across the full employment lifecycle (recruitment, hiring, promotion, renewal, training selection, discharge, discipline, tenure, terms/privileges/conditions). Employers must also provide notice to employees that AI is being used for these purposes. The Illinois Department of Human Rights (IDHR) is authorized to adopt implementing rules. Enforcement flows through existing IHRA mechanisms: charge filing with the Human Rights Commission or private right of action in Illinois Circuit Court.

## Obligations + coverage

### Definitions and scope (§ 2-101(M)–(N))

| Obligation | Coverage | Evidence |
|---|---|---|
| "Artificial intelligence" definition — machine-based system that infers from input to generate outputs (predictions, content, recommendations, decisions); includes generative AI | ✅ AI-system type classification + validation gate (cross-ref EU AI Act Art. 3(1), Colorado § 6-1-1701) | `hummbl_governance/schema_validator.py`, `hummbl_governance/compliance_mapper.py` |
| "Generative artificial intelligence" definition — automated computing system producing outputs simulating human-produced content (text, images, multimedia, other) | ✅ Generative-AI subtype classification + content-type tagging | `hummbl_governance/schema_validator.py`, `hummbl_governance/output_validator.py` |
| Employer scope — 1+ employees within Illinois during 20+ calendar weeks within the calendar year of or preceding the alleged violation | ⚪ Boundary: legal-entity determination and employee-count threshold are organizational, not software-addressable | |
| Protected classes under IHRA — race, color, ancestry, national origin, disability, religion, sex, sexual orientation, pregnancy, military status, age (40+), marital status, citizenship, work authorization, language, conviction/arrest record, family responsibilities, reproductive health decisions | ✅ Protected-class encoding in law engine + discrimination-detection tuple types (cross-ref EU AI Act Art. 10, Colorado § 6-1-1701) | `hummbl_governance/kernel/law_engine.py`, `hummbl_governance/audit_log.py` |

### Non-discrimination — AI use prohibition (§ 2-102(L)(1))

| Obligation | Coverage | Evidence |
|---|---|---|
| Prohibition on AI use that subjects employees to discrimination — recruitment and hiring contexts | ✅ Discriminatory-output detection + fast-fail circuit breaker + kill-switch halt (cross-ref NYC LL 144 bias-audit, Colorado § 6-1-1702) | `hummbl_governance/output_validator.py`, `hummbl_governance/circuit_breaker.py`, `hummbl_governance/kill_switch.py` |
| Prohibition on AI use that subjects employees to discrimination — promotion, renewal of employment, selection for training or apprenticeship | ✅ Same detection + halt primitives applied to post-hire decision contexts | `hummbl_governance/output_validator.py`, `hummbl_governance/circuit_breaker.py` |
| Prohibition on AI use that subjects employees to discrimination — discharge, discipline, tenure, or terms/privileges/conditions of employment | ✅ Same detection + halt primitives applied to adverse-action contexts | `hummbl_governance/output_validator.py`, `hummbl_governance/circuit_breaker.py` |
| Prohibition on using zip codes as a proxy for protected classes under the Article | ✅ Proxy-feature detection schema gate + input-validation rejection of zip-code-as-race-proxy features | `hummbl_governance/schema_validator.py`, `hummbl_governance/output_validator.py` |
| Broad scope — statutory language encompasses any "use" of AI, not just fully automated decision-making | ✅ Capability-fence restricts AI capabilities across all use modes (assistive, augmented, automated) | `hummbl_governance/capability_fence.py` |
| No statutory affirmative defense — unlike Colorado SB 24-205, HB 3773 provides no safe harbor for adopting a recognized risk-management framework | ⚪ Boundary: legal determination — no software primitive can create a statutory defense the law does not provide | |
| Permitted use — nothing in the Act prevents use of AI to support inclusion of diverse candidates | ✅ Permitted-use classification tuple + inclusion-benefit tagging | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |

### Notice obligations (§ 2-102(L)(2))

| Obligation | Coverage | Evidence |
|---|---|---|
| Employer must provide notice to employees that the employer is using AI for employment decisions | ✅ Pre-use notification primitive + delivery-tracking tuple (cross-ref NYC LL 144 § 20-870(c), Colorado § 6-1-1704) | `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py` |
| Notice obligation covers all employment decision contexts — recruitment through termination | ✅ Context-tagged notification tuples spanning all 10 statutory decision categories | `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py` |
| IDHR rulemaking — circumstances and conditions that require notice | ⚪ Boundary: regulatory rulemaking is organizational, not software-addressable | |
| IDHR rulemaking — time period for providing notice | ⚪ Boundary: regulatory rulemaking is organizational | |
| IDHR rulemaking — means for providing notice | ⚪ Boundary: regulatory rulemaking is organizational | |

### Enforcement and liability

| Obligation | Coverage | Evidence |
|---|---|---|
| Charge filing with Illinois Human Rights Commission | 🟡 Partial: audit-log export + evidence bundle supports charge preparation; filing act is org task | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Private right of action — civil complaint in Illinois Circuit Court | 🟡 Partial: immutable evidence trail + decision-log export supports litigation; litigation is org task | `hummbl_governance/audit_log.py`, `hummbl_governance/kernel/evidence_engine.py` |
| IDHR authority to adopt rules necessary for implementation and enforcement | ⚪ Boundary: regulatory authority is organizational | |
| Employer liability for algorithmic discrimination — no vendor shield (agent-liability framework per Mobley v. Workday) | 🟡 Partial: immutable audit trail + decision-provenance tuples support defense; liability determination is legal | `hummbl_governance/audit_log.py`, `hummbl_governance/kernel/receipt_engine.py` |
| Remedies under IHRA — injunctive relief, reinstatement, back pay, compensatory and punitive damages | ⚪ Boundary: damages and remedies are legal, not software-addressable | |

### Adjacent Illinois AI laws

| Obligation | Coverage | Evidence |
|---|---|---|
| AIVICA (Artificial Intelligence Video Interview Act) — notice, explanation, and consent for AI analysis of video interviews (effective 2020) | ✅ Consent + notice + explanation tuples (cross-ref AIVICA coverage) | `hummbl_governance/audit_log.py`, `hummbl_governance/identity.py` |
| BIPA (Biometric Information Privacy Act) — private right of action, $1,000/$5,000 per-violation damages for biometric data misuse (effective 2008) | ⚪ Boundary: BIPA is a separate statute with private right of action; biometric-data compliance is organizational | |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| Definitions and scope (§ 2-101) | 4 | 3 | 0 | 1 |
| Non-discrimination — AI use prohibition (§ 2-102(L)(1)) | 7 | 6 | 0 | 1 |
| Notice obligations (§ 2-102(L)(2)) | 5 | 2 | 0 | 3 |
| Enforcement and liability | 5 | 0 | 3 | 2 |
| Adjacent Illinois AI laws | 2 | 1 | 0 | 1 |
| **Totals** | **23** | **12** | **3** | **8** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Algorithmic-discrimination overlaps Colorado SB 24-205 — see [`colorado-ai-act.md`](./colorado-ai-act.md)
- Employment-AI notice overlaps NYC Local Law 144 — see [`nyc-ll144.md`](./nyc-ll144.md)
- Protected-class detection overlaps EU AI Act Art. 10 (data governance) — see [`eu-ai-act.md`](./eu-ai-act.md)
- Risk-management framework contrast: Colorado offers affirmative defense (NIST AI RMF adoption); Illinois does not — see [`nist-ai-rmf.md`](./nist-ai-rmf.md)
- Inventory entry: [`docs/research/ai-governance-framework-inventory.md`](../research/ai-governance-framework-inventory.md) (ID 62)
