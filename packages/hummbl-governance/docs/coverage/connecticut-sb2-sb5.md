# Connecticut SB 2 / SB 5 Coverage Matrix — HUMMBL

**Standard**: Connecticut SB 5 — "An Act Concerning Online Safety," Public Act No. 26-15 (39 sections); predecessor SB 2 (2025) — "An Act Concerning Artificial Intelligence" (not enacted)
**Effective**: Staggered — October 1, 2026 (Secs. 1, 2, 7–15, 26, 37–38); January 1, 2027 (Secs. 4–6, 19–22); July 1, 2027 (Secs. 3, 33, 36); October 1, 2027 (AEDT deployer disclosures, Secs. 9–11); January 1, 2028 (Sec. 39)
**Source**: https://www.cga.ct.gov/
**Last reviewed**: 2026-06-25
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not Connecticut-licensed counsel and does not provide legal advice on SB 5 (PA 26-15) or the predecessor SB 2. SB 5 is enforced primarily by the Attorney General under the Connecticut Unfair Trade Practices Act (CUTPA), with additional enforcement via the Commission on Human Rights and Opportunities (CHRO) for employment-discrimination provisions. A private right of action exists only for AI companion violations involving minors. Statutory compliance is the customer-organization responsibility. HUMMBL maps technical primitives to the Act's companion-chatbot safety, frontier-model whistleblower, AEDT transparency, antidiscrimination, provenance, subscription-disclosure, and institutional obligations.

## Scope summary

SB 5 (PA 26-15), signed May 27, 2026, is an omnibus AI statute covering AI companions (Secs. 4–6), frontier model safety (Sec. 2), automated employment-related decision technologies / AEDTs (Secs. 7–14), generative AI provenance (Sec. 15), AI subscription disclosures (Sec. 1), social media platform regulation (Sec. 39), state-agency AI governance (Secs. 16–17, 37–38), and workforce/AI-layoff reporting (Sec. 26). The predecessor SB 2 (2025) proposed a comprehensive high-risk AI framework with algorithmic-discrimination protections, consumer rights (notice, explanation, correction, appeal), and developer/deployer duty of care, but did not become law. SB 5 takes a narrower, targeted approach — transparency and disclosure obligations rather than mandatory impact assessments or bias audits — while amending Connecticut's human rights statute to clarify that AEDT use is not a defense against discrimination claims. Frontier developers are defined by a >10²⁶ FLOPs compute threshold; large frontier developers exceed $500M annual gross revenue.

## Obligations + coverage

### AI companion safety and disclosure (Secs. 4–6, effective Jan 1, 2027)

| Obligation | Coverage | Evidence |
|---|---|---|
| Implement evidence-based methods to detect user expressions of suicide, self-harm, or imminent physical violence | ✅ Output-validation gate with harm-detection tuples + kill-switch halt for harmful outputs (cross-ref Texas TRAIGA § 552.101) | `hummbl_governance/output_validator.py`, `hummbl_governance/kill_switch.py` |
| Prevent AI companion from generating output encouraging self-harm, violence, or unlawful substance consumption | ✅ Prohibited-output gate + circuit-breaker fast-fail on policy-violating content | `hummbl_governance/output_validator.py`, `hummbl_governance/circuit_breaker.py` |
| Disclose to users that they are interacting with AI (continuously visible or at start of 24-hour period + hourly for minors / every 3 hours for adults) | ✅ Transparency-notification primitive with time-bound disclosure scheduling (cross-ref EU AI Act Art. 50, South Korea AI Basic Act Art. 31) | `hummbl_governance/audit_log.py`, `hummbl_governance/lifecycle.py` |
| Prevent AI companion from claiming to be human or generating output refuting non-human identity | ✅ Output-validation gate with anthropomorphism-prevention tuple | `hummbl_governance/output_validator.py` |
| For minors: prevent manipulative techniques (emotional dependence, isolation, romantic interactions, engagement optimization) and provide parental tools for screen time and account settings | ✅ Capability-fence restricting prohibited interaction patterns + reward-monitor for engagement-optimization detection (cross-ref EU AI Act Art. 5 manipulation prohibition) | `hummbl_governance/capability_fence.py`, `hummbl_governance/reward_monitor.py` |

### Frontier model safety and whistleblower protections (Sec. 2, effective Oct 1, 2026)

| Obligation | Coverage | Evidence |
|---|---|---|
| Frontier developers (≥10²⁶ FLOPs) prohibited from retaliating against employees reporting catastrophic risks | ⚪ Boundary: employment-law whistleblower protection is organizational policy, not software-addressable | |
| Large frontier developers (>$500M revenue) must establish anonymous internal reporting process for catastrophic-risk disclosures | 🟡 Partial: audit-log provides immutable report intake and tracking; anonymous-submission infrastructure is org task | `hummbl_governance/audit_log.py` |
| Large frontier developers must investigate reports, take immediate action to eliminate danger, and provide reasonable updates to reporting employees | ✅ Adverse-event tuple + risk-treatment tuple with investigation-tracking and action-logging (cross-ref NIST AI RMF MEASURE, EU AI Act Art. 9) | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Reports and updates shared with officers and directors at least quarterly (excluding alleged wrongdoers) | 🟡 Partial: audit-log export + compliance-report generator produces quarterly summaries; distribution is org task | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Frontier developers must display clear notice of employee whistleblower rights in the workplace at all times | ⚪ Boundary: physical-workplace notice posting is organizational, not software-addressable | |

### AEDT transparency and disclosure (Secs. 7–12, effective Oct 1, 2027)

| Obligation | Coverage | Evidence |
|---|---|---|
| Developers must provide deployers all information necessary to comply with AEDT disclosure obligations (or contractually assume them) | ✅ Documentation-handoff tuple + compliance-mapper developer-deployer information flow (cross-ref Colorado AI Act § 6-1-1703, EU AI Act Art. 26) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Deployers must disclose to employees/applicants in plain language that they are interacting with an AEDT | ✅ Transparency-notification primitive with plain-language disclosure template (cross-ref EU AI Act Art. 50, Colorado § 6-1-1704) | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Deployers must provide written pre-decision notice: AEDT use, purpose, nature of decision, trade name, data categories/sources, data assessment methods, deployer contact info | ✅ Disclosure-generation primitive with structured notice tuple containing all required fields (cross-ref NYC LL 144, Colorado ADM Act) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Deployers must provide additional notice for adverse decisions (right to request human review) | ✅ Human-oversight delegation token + adverse-decision-appeal tuple (cross-ref EU AI Act Art. 14, Colorado § 6-1-1704(4)) | `hummbl_governance/delegation.py`, `hummbl_governance/audit_log.py` |
| Trade-secret exclusion: withholding party must notify individuals of withheld information and basis | 🟡 Partial: compliance-mapper can generate withholding-notice; legal determination of trade-secret status is org task | `hummbl_governance/compliance_mapper.py` |

### AEDT antidiscrimination amendments (Secs. 13–14, effective Oct 1, 2026)

| Obligation | Coverage | Evidence |
|---|---|---|
| Use of an AEDT shall not be a defense against employment-discrimination claims under Conn. Gen. Stat. § 46a-60 | ⚪ Boundary: legal-defense prohibition is statutory, not software-addressable | |
| Courts and CHRO may consider evidence of anti-bias testing and proactive efforts when adjudicating discrimination claims | ✅ Bias-testing-evidence tuple + audit-log retention of testing artifacts and results (cross-ref Colorado AI Act § 6-1-1701, NIST AI RMF MEASURE 2.11) | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Employers must not use AEDT in a manner that causes discrimination based on protected characteristics (race, color, creed, age, sex, gender identity, marital status, national origin, ancestry, disability, veteran status) | ✅ Algorithmic-discrimination-detection primitives + fairness-evaluation tuples (cross-ref Colorado SB 24-205, EU AI Act Art. 5, Texas TRAIGA § 552.101) | `hummbl_governance/audit_log.py`, `hummbl_governance/schema_validator.py` |

### Generative AI provenance (Sec. 15, effective Oct 1, 2026)

| Obligation | Coverage | Evidence |
|---|---|---|
| Covered providers (>1M monthly users, publicly accessible generative AI) must include provenance data in audio, image, or video content created or materially altered by their AI | ✅ Content-authenticity tuple + provenance-labeling primitive with C2PA-compatible metadata embedding (cross-ref EU AI Act Art. 50(2), South Korea AI Basic Act Art. 31) | `hummbl_governance/output_validator.py`, `hummbl_governance/audit_log.py` |
| Provenance data must be difficult to tamper with, remove, or disassociate using commercially and technically reasonable methods (e.g., C2PA standard) | ✅ Tamper-resistant provenance-labeling with cryptographic binding to content metadata | `hummbl_governance/output_validator.py` |
| Provenance data must allow consumers to assess whether content was created or materially altered by generative AI | ✅ Consumer-facing provenance-verification tuple + disclosure-labeling primitive | `hummbl_governance/output_validator.py`, `hummbl_governance/compliance_mapper.py` |

### Subscription disclosure, workforce, and institutional obligations (Secs. 1, 16–17, 26, 37–38)

| Obligation | Coverage | Evidence |
|---|---|---|
| AI subscription providers must disclose quantitative/qualitative limitations, usage caps, feature restrictions, and provider discretion to reduce quality/functionality (Sec. 1, effective Oct 1, 2026) | ✅ Disclosure-generation primitive with service-terms tuple + compliance-mapper template | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| AI subscription providers must disclose modifications to limitations upon renewal | ✅ Renewal-notification tuple + change-disclosure primitive | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| AI technology shall not be used to modify or impair collective bargaining agreements or reduce wages/fringe benefits/employee duties (Secs. 16–17) | ⚪ Boundary: labor-law compliance and collective-bargaining integrity is organizational, not software-addressable | |
| Employers issuing plant-closing or mass-layoff notices must disclose whether layoffs are related to AI use (Sec. 26, effective Oct 1, 2026) | 🟡 Partial: audit-log can track AI-use attribution for workforce decisions; WARN-notice filing is org task | `hummbl_governance/audit_log.py` |
| State agencies must inventory AI systems in use (Sec. 37, effective Oct 1, 2026) | ✅ System-inventory tuple + audit-log registration of deployed AI systems | `hummbl_governance/audit_log.py`, `hummbl_governance/identity.py` |
| State agencies must follow AI procurement requirements (Sec. 38, effective Oct 1, 2026) | 🟡 Partial: compliance-mapper can generate procurement-compliance documentation; procurement process is org task | `hummbl_governance/compliance_mapper.py` |

### Social media platform regulation and enforcement (Sec. 39, effective Jan 1, 2028; enforcement provisions)

| Obligation | Coverage | Evidence |
|---|---|---|
| Covered platforms must not deliver personalized algorithmic content recommendations to minors without verifiable parental consent | ✅ Age-gate + consent-verification tuple + capability-fence restricting minor-targeted recommendations (cross-ref CCPA/CPRA minor protections) | `hummbl_governance/capability_fence.py`, `hummbl_governance/delegation.py` |
| Default settings for minors: 1-hour daily algorithmic-content limit, private account mode, notification curfew (8 a.m.–9 p.m.), sensitive-content blocking | ✅ Cost-governor time-budget enforcement + capability-fence content restrictions + schedule-engine time-window enforcement | `hummbl_governance/cost_governor.py`, `hummbl_governance/capability_fence.py`, `hummbl_governance/kernel/schedule_engine.py` |
| Covered operators must display Surgeon General warning and make annual public disclosures (user counts, consent rates, default-setting usage, average usage by age/hour) | 🟡 Partial: compliance-report generator produces disclosure content; public publication is org task | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| AG enforcement under CUTPA for most provisions; private right of action for AI companion minor violations; CHRO enforcement for AEDT discrimination | ⚪ Boundary: enforcement authority and litigation is institutional/legal, not software-addressable | |
| 60-day cure period for AEDT violations before Dec 31, 2027; civil penalty up to $1,000 per frontier-model violation | ⚪ Boundary: cure-period compliance and civil-penalty exposure is legal, not software-addressable | |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| AI companion safety (Secs. 4–6) | 5 | 5 | 0 | 0 |
| Frontier model safety (Sec. 2) | 5 | 1 | 2 | 2 |
| AEDT transparency (Secs. 7–12) | 5 | 4 | 1 | 0 |
| AEDT antidiscrimination (Secs. 13–14) | 3 | 2 | 0 | 1 |
| Generative AI provenance (Sec. 15) | 3 | 3 | 0 | 0 |
| Subscription, workforce, institutional (Secs. 1, 16–17, 26, 37–38) | 6 | 3 | 2 | 1 |
| Social media + enforcement (Sec. 39) | 5 | 2 | 1 | 2 |
| **Totals** | **32** | **20** | **6** | **6** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- AEDT disclosure overlaps Colorado AI Act § 6-1-1704 — see [`colorado-ai-act.md`](./colorado-ai-act.md)
- AEDT disclosure overlaps NYC LL 144 — see [`nyc-ll144.md`](./nyc-ll144.md)
- Provenance overlaps EU AI Act Art. 50(2) — see [`eu-ai-act.md`](./eu-ai-act.md)
- Provenance overlaps South Korea AI Basic Act Art. 31 — see [`south-korea-ai-basic-act.md`](./south-korea-ai-basic-act.md)
- Antidiscrimination overlaps Colorado SB 24-205 — see [`colorado-ai-act.md`](./colorado-ai-act.md)
- Antidiscrimination overlaps Texas TRAIGA § 552.101 — see [`texas-traiga.md`](./texas-traiga.md)
- Frontier-model compute threshold (10²⁶ FLOPs) overlaps South Korea AI Basic Act Art. 32 — see [`south-korea-ai-basic-act.md`](./south-korea-ai-basic-act.md)
- Human oversight overlaps EU AI Act Art. 14 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Bias testing overlaps NIST AI RMF MEASURE 2.11 — see [`nist-ai-rmf.md`](./nist-ai-rmf.md)
- Minor protections overlap CCPA/CPRA — see [`ccpa-cpra.md`](./ccpa-cpra.md)
