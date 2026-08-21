# Utah AI Policy Act (SB 149) Coverage Matrix — HUMMBL

**Standard**: Utah Artificial Intelligence Policy Act, Utah Code Title 13, Chapter 72 and Utah Code Section 13-2-12
**Effective**: May 1, 2024 (sunset extended to July 1, 2027)
**Source**: https://le.utah.gov/~2024/bills/static/SB0149.html
**Last reviewed**: 2026-05-14
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not Utah-licensed counsel and does not provide legal advice on the Utah AI Policy Act. The Act is enforced by the Division of Consumer Protection with administrative fines up to $2,500 per violation. Statutory compliance is the customer-organization responsibility. HUMMBL maps technical primitives to the Act's generative AI disclosure and regulated-occupation transparency obligations.

## Scope summary

The Act applies to persons using generative AI in consumer transactions and regulated occupations in Utah. It establishes disclosure requirements for AI interactions, creates an Office of AI Policy and AI Learning Laboratory Program, and provides regulatory mitigation agreements for participants. The Act is the first US state AI law to take effect (May 1, 2024).

## Obligations + coverage

### Generative AI liability provisions (§ 13-2-12)

| Obligation | Coverage | Evidence |
|---|---|---|
| No defense for AI-caused violations — generative AI use does not shield from consumer protection liability | 🟡 Partial: audit log provides immutable HMAC-signed AI-use evidence trail supporting liability attribution; legal determination remains institutional | `hummbl_governance/audit_log.py` |
| Disclosure upon request — clearly and conspicuously disclose AI interaction when asked in consumer-protection-regulated activities | ✅ Transparency-notification primitive with on-demand disclosure trigger (cross-ref EU AI Act Art. 50) | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Regulated occupation disclosure — prominently disclose when interacting with generative AI in regulated services | ✅ Profession-context disclosure tuple + transparency primitive | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| No AI authorization for unlicensed practice — AI does not permit providing regulated occupation services without licensure | 🟡 Partial: capability fence can restrict AI from performing regulated-occupation tasks at runtime; identity registry tracks agent trust tiers and authorizations; licensure verification remains institutional | `hummbl_governance/capability_fence.py`, `hummbl_governance/identity.py` |
| Verbal disclosure timing — at start of oral exchange for regulated occupations | ✅ Time-bound disclosure-scheduling primitive | `hummbl_governance/audit_log.py`, `hummbl_governance/lifecycle.py` |
| Electronic disclosure timing — before written exchange for regulated occupations | ✅ Time-bound disclosure-scheduling primitive | `hummbl_governance/audit_log.py`, `hummbl_governance/lifecycle.py` |

### Office of AI Policy (§ 13-72-201)

| Obligation | Coverage | Evidence |
|---|---|---|
| Create Office of AI Policy within Department of Commerce | ⚪ Boundary: government-office creation is institutional | |
| Appoint Office Director | ⚪ Boundary: government-appointment is institutional | |
| Create and administer AI Learning Laboratory Program | ⚪ Boundary: government-program administration is institutional | |
| Consult with businesses and stakeholders on regulatory proposals | ⚪ Boundary: government-stakeholder consultation is institutional | |
| Make rules for learning laboratory (procedures, criteria, data limits, disclosures, reporting) | ⚪ Boundary: government-rulemaking is institutional | |
| Annual reporting to legislature on learning agenda, findings, regulatory mitigation, recommended legislation | 🟡 Partial: compliance-mapper generates structured evidence reports on AI policy findings, regulatory mitigation activity, and recommended legislative changes; legislative submission remains institutional | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Develop and publish guidance and best practices for Utah consumers about AI | 🟡 Partial: compliance-mapper documentation export produces AI governance guidance content and best-practice templates; publication and consumer-facing distribution remains institutional | `hummbl_governance/compliance_mapper.py` |

### Learning Laboratory Program (§ 13-72-301)

| Obligation | Coverage | Evidence |
|---|---|---|
| Set learning agenda for AI policy study areas | ⚪ Boundary: government-research-agenda is institutional | |
| Consult with stakeholders on learning agenda | ⚪ Boundary: government-stakeholder consultation is institutional | |

### Regulatory mitigation agreements (§ 13-72-401)

| Obligation | Coverage | Evidence |
|---|---|---|
| Application process for regulatory mitigation or joint interpretation agreements | 🟡 Partial: compliance mapper can generate application documentation and evidence packages; application submission and review process remains institutional | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Demonstrate eligibility criteria for regulatory mitigation | 🟡 Partial: compliance mapper can map controls to eligibility criteria and generate evidence; evidence engine produces structured evidence; eligibility determination remains institutional | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/kernel/evidence_engine.py` |
| Agreement specifications — scope limits, safeguards, regulatory mitigation, consumer disclosures, reporting | 🟡 Partial: compliance-report generator can document agreement terms; negotiation is org task | `hummbl_governance/compliance_mapper.py` |

### Enforcement provisions

| Obligation | Coverage | Evidence |
|---|---|---|
| Division of Consumer Protection enforcement authority | ⚪ Boundary: government-enforcement authority is institutional | |
| Administrative fine up to $2,500 per violation of § 13-2-12 | ⚪ Boundary: administrative-fine exposure is legal | |
| Court action for injunctive relief | ⚪ Boundary: judicial relief is institutional | |
| Disgorgement of money received in violation | ⚪ Boundary: judicial remedy is institutional | |
| Payment to injured persons from disgorged funds | ⚪ Boundary: judicial remedy is institutional | |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| Generative AI liability (§ 13-2-12) | 6 | 4 | 2 | 0 |
| Office of AI Policy (§ 13-72-201) | 7 | 0 | 0 | 7 |
| Learning Laboratory (§ 13-72-301) | 2 | 0 | 0 | 2 |
| Regulatory mitigation (§ 13-72-401) | 3 | 0 | 3 | 0 |
| Enforcement | 5 | 0 | 0 | 5 |
| **Totals** | **23** | **4** | **5** | **14** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Disclosure overlaps EU AI Act Art. 50 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Disclosure overlaps Colorado § 6-1-1704 — see [`colorado-ai-act.md`](./colorado-ai-act.md)
