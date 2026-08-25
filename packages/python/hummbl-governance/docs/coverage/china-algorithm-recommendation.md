# China Algorithm Recommendation Provisions Coverage Matrix — HUMMBL

**Standard**: Internet Information Service Algorithmic Recommendation Management Provisions (互联网信息服务算法推荐管理规定), Order No. 9 (CAC, MIIT, MPS, SAMR)
**Effective**: March 1, 2022
**Source**: http://www.cac.gov.cn/2021-08/27/c_1631650028355286.htm
**Last reviewed**: 2026-06-25
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not Chinese legal counsel and does not provide legal advice on the Algorithm Recommendation Provisions. The Provisions are jointly enforced by the Cyberspace Administration of China (CAC), the Ministry of Industry and Information Technology (MIIT), the Ministry of Public Security (MPS), and the State Administration for Market Regulation (SAMR), with penalties under the Cybersecurity Law, Data Security Law, PIPL, and related regulations. Statutory compliance is the customer-organization responsibility. HUMMBL maps technical primitives to the Provisions' information-service norms, user-rights, content-moderation, worker-protection, filing, and security-assessment obligations.

## Scope summary

The Provisions apply to the use of algorithmic recommendation technology — including generative/synthetic, personalized-recommendation, ranking/selection, search-filter, and dispatch/decision-making algorithms — to provide Internet information services within mainland China. They establish the Algorithm Registry (算法备案系统), a public filing system for services with public-opinion or social-mobilization attributes, and introduce a world-first user right to switch off algorithmic recommendation entirely (Art. 17). The Provisions predate and form the compliance scaffolding reused by the 2022 Deep Synthesis Provisions and 2023 Generative AI Interim Measures.

## Obligations + coverage

### Information service norms (Arts. 6–9)

| Obligation | Coverage | Evidence |
|---|---|---|
| Uphold mainstream value orientations, optimize recommendation mechanisms, disseminate positive energy (Art. 6) | 🟡 Partial: output-validation gate enforces content policy; "positive energy" value-orientation is content-policy org task | `hummbl_governance/output_validator.py`, `hummbl_governance/compliance_mapper.py` |
| Not use algorithms to harm national security/social public interest, upset economic/social order, or infringe others' lawful rights (Art. 6) | ✅ Prohibited-content gate + kill-switch halt | `hummbl_governance/output_validator.py`, `hummbl_governance/kill_switch.py` |
| Not disseminate information prohibited by laws/regulations; take measures to prevent and curb harmful information (Art. 6) | ✅ Content-filtering primitive + output-blocking gate | `hummbl_governance/output_validator.py`, `hummbl_governance/capability_fence.py` |
| Fulfil primary responsibility for algorithm security; establish management systems and technical measures for mechanism review, tech-ethics review, user registration, info-dissemination review, security assessment & monitoring, incident response, data security & PI protection, anti-fraud (Art. 7) | ✅ Governance-kernel authority + law engine + audit-log responsibility record | `hummbl_governance/kernel/authority_engine.py`, `hummbl_governance/kernel/law_engine.py`, `hummbl_governance/audit_log.py` |
| Formulate and disclose algorithmic recommendation service-related norms (Art. 7) | 🟡 Partial: compliance-report generator produces norms; public disclosure is org task | `hummbl_governance/compliance_mapper.py` |
| Allocate specialized personnel and technical support suited to the scale of algorithmic recommendation services (Art. 7) | ⚪ Boundary: personnel allocation is organizational | |
| Regularly examine, verify, assess, and check algorithmic mechanisms, models, data, and application outcomes; not set up models leading to addiction or excessive consumption (Art. 8) | ✅ Audit-log assessment tuple + health-probe monitoring + reward-monitor addictive-pattern detection | `hummbl_governance/audit_log.py`, `hummbl_governance/health_probe.py`, `hummbl_governance/reward_monitor.py` |
| Strengthen info security management; establish feature databases to identify unlawful/harmful information (Art. 9) | ✅ Content-feature database + output-validation gate | `hummbl_governance/output_validator.py`, `hummbl_governance/audit_log.py` |
| Mark algorithmically generated/synthetic information with an indicator before dissemination (Art. 9) | ✅ Content-labeling tuple + provenance-labeling primitive (cross-ref GenAI Measures Art. 12, SB 942) | `hummbl_governance/output_validator.py`, `hummbl_governance/audit_log.py` |
| Cease transmission of unlawful info immediately, delete, prevent spread, preserve records, and report to cybersecurity and informatization departments (Art. 9) | ✅ Kill-switch halt + incident-report tuple + immutable audit-log retention | `hummbl_governance/kill_switch.py`, `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py` |

### Algorithmic manipulation and competition (Arts. 10–15)

| Obligation | Coverage | Evidence |
|---|---|---|
| Strengthen user model and tagging management; not enter unlawful/harmful info as keywords or user tags for recommendation (Art. 10) | ✅ Schema-validation on user tags + audit-log tag record | `hummbl_governance/schema_validator.py`, `hummbl_governance/audit_log.py` |
| Strengthen page ecology management; establish manual intervention and autonomous user choice mechanisms; present mainstream-value info in key segments (Art. 11) | ✅ Capability-fence + output-validator intervention gate + human-oversight delegation | `hummbl_governance/capability_fence.py`, `hummbl_governance/output_validator.py`, `hummbl_governance/delegation.py` |
| Use content de-weighting and scattering interventions; optimize transparency and understandability of search, ranking, push, display norms (Art. 12) | 🟡 Partial: transparency-disclosure tuple; de-weighting algorithm design is org task | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/output_validator.py` |
| Obtain Internet news info service permit; not generate/synthesize fake news; not disseminate news outside State-determined scope (Art. 13) | ⚪ Boundary: government licensing and news-content verification is organizational | |
| Not use algorithms for false registration, account trading, fake likes/comments/reshares, shielding info, over-recommendation, manipulating topic lists/search rankings/hot search, influencing public opinion, or evading supervision (Art. 14) | ✅ Output-validation gate + capability-fence + audit-log manipulation-detection tuple | `hummbl_governance/output_validator.py`, `hummbl_governance/capability_fence.py`, `hummbl_governance/audit_log.py` |
| Not use algorithms to unreasonably restrict other providers, obstruct regular operation, or engage in monopolistic/improper competition acts (Art. 15) | ⚪ Boundary: antitrust and competition compliance is legal-organizational | |

### User rights protection (Arts. 16–22)

| Obligation | Coverage | Evidence |
|---|---|---|
| Notify users clearly about algorithmic recommendation services; publicize basic principles, purposes, motives, and main operational mechanisms (Art. 16) | ✅ Transparency-notification tuple + disclosure primitive (cross-ref Korea Art. 31, EU AI Act Art. 50) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Provide users a choice not targeted at personal characteristics, or a convenient option to switch off algorithmic recommendation; cease immediately when switched off (Art. 17) | ✅ Kill-switch user-initiated halt + capability-fence opt-out enforcement | `hummbl_governance/kill_switch.py`, `hummbl_governance/capability_fence.py` |
| Provide functions to choose or delete user tags used for personal-characteristic recommendations (Art. 17) | ✅ Identity-tag management + deletion primitive | `hummbl_governance/identity.py`, `hummbl_governance/audit_log.py` |
| Where algorithms create major influence on users' rights and interests, provide an explanation and bear related liability (Art. 17) | 🟡 Partial: explanation-disclosure generator; liability determination is legal | `hummbl_governance/compliance_mapper.py` |
| Fulfill minor protection duties; develop minor-suited models; not push harmful or addiction-causing info to minors (Art. 18) | 🟡 Partial: output-validation gate enforces content policy; age-verification and minor-model design is org task | `hummbl_governance/output_validator.py`, `hummbl_governance/reward_monitor.py` |
| Protect elderly rights; provide smart services suited to elderly; monitor, identify, and handle telecom and online fraud targeting elderly (Art. 19) | 🟡 Partial: fraud-detection tuple + output-validation; elderly-specific service design is org task | `hummbl_governance/output_validator.py`, `hummbl_governance/audit_log.py` |
| Protect workers' rights (remuneration, rest, vacation); establish algorithms for platform sign-on/allocation, remuneration, work time, rewards (Art. 20) | 🟡 Partial: audit-log records algorithmic dispatch decisions; worker-protection algorithm design is org task | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Protect consumers' fair trading rights; not use algorithms for unreasonable differentiated treatment in trading conditions/prices (big-data price discrimination) (Art. 21) | ✅ Output-validation anti-discrimination gate + audit-log pricing-decision record | `hummbl_governance/output_validator.py`, `hummbl_governance/audit_log.py` |
| Install convenient complaint/reporting access; clarify handling workflows and feedback timeframes; timely receive, handle, and provide feedback (Art. 22) | ✅ Complaint-intake tuple + SLA-tracking primitive + lifecycle handling | `hummbl_governance/audit_log.py`, `hummbl_governance/lifecycle.py` |

### Supervision and management (Arts. 23–30)

| Obligation | Coverage | Evidence |
|---|---|---|
| Graded and categorized algorithm security management based on public-opinion properties, social mobilization, content categories, user scale, data importance, interference degree (Art. 23) | ✅ Compliance-mapper risk-classification tuple + stride-mapper categorization | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/stride_mapper.py` |
| Providers with public-opinion/social-mobilization attributes file within 10 working days via algorithm filing system; modifications within 10 days; cancellation within 20 days of ceasing (Art. 24) | ⚪ Boundary: government-filing procedure is organizational | |
| Display filing number in a clear position on website/app; provide link to published info (Art. 26) | ⚪ Boundary: public-facing display is organizational | |
| Providers with public-opinion/social-mobilization attributes conduct security assessment per State regulations (Art. 27) | ✅ Security-assessment template + risk-assessment primitive (cross-ref GenAI Measures Art. 17, NIST AI RMF MAP) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Preserve network logs; cooperate with security assessment/supervision/inspection; provide necessary technical and data support (Art. 28) | 🟡 Partial: audit-log export + log retention supports inspection; cooperation act is org task | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Assessment/inspection personnel maintain confidentiality of personal info and commercial secrets learned in exercising duties (Art. 29) | ⚪ Boundary: personnel confidentiality is organizational | |
| Accept and handle public complaints/reports about violations (Art. 30) | ✅ Complaint-intake tuple + audit-log record | `hummbl_governance/audit_log.py` |

### Penalties (Arts. 31–33)

| Obligation | Coverage | Evidence |
|---|---|---|
| Warnings, criticism, rectification orders, info-update suspension, and fines (RMB 10K–100K) for violations of Arts. 7, 8, 9(1), 10, 14, 16, 17, 22, 24, 26 (Art. 31) | ⚪ Boundary: administrative-penalty exposure is legal | |
| Violations of Arts. 6, 9(2), 11, 13, 15, 18, 19, 20, 21, 27, 28(2) processed under relevant laws, administrative regulations, and departmental rules (Art. 32) | ⚪ Boundary: legal-penalty framework is institutional | |
| Filing revocation for fraudulently obtained filing; cancellation for service cessation without deregistration or serious violations leading to license revocation (Art. 33) | ⚪ Boundary: regulatory filing-revocation is institutional | |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| Information service norms (Arts. 6–9) | 10 | 7 | 1 | 2 |
| Algorithmic manipulation + competition (Arts. 10–15) | 6 | 3 | 1 | 2 |
| User rights protection (Arts. 16–22) | 9 | 5 | 4 | 0 |
| Supervision and management (Arts. 23–30) | 7 | 3 | 1 | 3 |
| Penalties (Arts. 31–33) | 3 | 0 | 0 | 3 |
| **Totals** | **35** | **18** | **7** | **10** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Content labeling overlaps China Generative AI Interim Measures Art. 12 — see [`china-genai-measures.md`](./china-genai-measures.md)
- Transparency notification overlaps South Korea AI Basic Act Art. 31 — see [`south-korea-ai-basic-act.md`](./south-korea-ai-basic-act.md)
- Transparency notification overlaps EU AI Act Art. 50 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Security assessment overlaps NIST AI RMF MAP — see [`nist-ai-rmf.md`](./nist-ai-rmf.md)
- Kill switch for content blocking and opt-out — see [`stride.md`](./stride.md) D — Denial of Service
- Personal information protection overlaps GDPR — see [`gdpr.md`](./gdpr.md)
