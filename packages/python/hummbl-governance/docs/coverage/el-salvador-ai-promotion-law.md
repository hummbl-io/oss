# El Salvador AI Promotion Law Coverage Matrix — HUMMBL

**Standard**: Law for the Promotion of Artificial Intelligence and Technologies (AI Promotion Law), Legislative Decree No. 234, amended by Decree No. 363
**Effective**: March 11, 2025 (published March 3, 2025; full enforcement September 2, 2025)
**Source**: https://www.unesco.org/ethics-ai/en/elsalvador
**Last reviewed**: 2026-06-25
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not Salvadoran legal counsel and does not provide legal advice on the AI Promotion Law. The Law establishes the National Artificial Intelligence Agency (ANIA), a mandatory National Registry of Development, Innovation, and Application of AI, a tiered oversight system based on "Consequential Decision" deployments, and an Algorithmic Impact Assessment Framework. Statutory compliance is the customer-organization responsibility. HUMMBL maps technical primitives to the Law's registry, risk-assessment, transparency, safeguard, and ethical-principle obligations.

## Scope summary

The Law applies to all natural or legal persons — domestic or foreign — engaged in AI development, research, training, implementation, or data collection/storage/processing for AI activities within El Salvador (Art. 3). A tiered oversight system distinguishes voluntary registration (for safeguards access), mandatory registration (for Consequential Decision systems deployed in critical sectors), and lighter obligations for open-domain/proprietary-data projects. Consequential Decision systems — where AI as a "controlling factor" materially affects a person's legal status, rights, or access to essential goods, services, or opportunities — trigger mandatory registration and Algorithmic Impact Assessment. Systems handling confidential, restricted, or personal data face mandatory risk-assessment compliance. The Law has special status over other laws save for cybersecurity and personal-data legislation (Art. 28).

## Obligations + coverage

### National Registry obligations (Art. 8(d), 16, 27; Impl. Decree Art. 11–13)

| Obligation | Coverage | Evidence |
|---|---|---|
| All AI entities must register with the National Registry of Development, Innovation, and Application of AI administered by ANIA (Art. 8(d), 16) | ⚪ Boundary: government-registry enrollment is organizational, not software-addressable | |
| Mandatory registration for operators of Consequential Decision systems deployed in El Salvador (Impl. Decree Art. 11) | ⚪ Boundary: government-registry enrollment is organizational | |
| Voluntary registration available to access statutory safeguards and liability protections (Impl. Decree Art. 11, Art. 19) | ⚪ Boundary: government-registry enrollment is organizational | |
| Maintain registration and comply with ANIA-issued technical security criteria for registered entities (Art. 27) | 🟡 Partial: compliance-mapper tracks registration status and criteria; ANIA criteria compliance is org task | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Open-domain or proprietary-data, non-commercial projects require only registration to access safeguards (Art. 16) | ⚪ Boundary: registry-tier classification and enrollment is organizational | |

### Risk assessment and Algorithmic Impact Assessment (Art. 17; Impl. Decree Art. 14–15)

| Obligation | Coverage | Evidence |
|---|---|---|
| ANIA establishes a Comprehensive Risk Assessment Framework balancing innovation with public safety (Art. 17) | ⚪ Boundary: government-framework establishment is organizational | |
| Mandatory compliance for systems handling confidential, restricted, or personal data (Art. 17) | ✅ Risk-assessment template + data-classification tuple (cross-ref EU AI Act Art. 9, NIST AI RMF GOVERN) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Algorithmic Impact Assessment for Consequential Decision systems before deployment (Impl. Decree Art. 15) | ✅ Impact-assessment template + algorithmic-impact tuple (cross-ref EU AI Act Art. 27 FRIA) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Identify, assess, and mitigate risks for high-risk AI systems within ANIA framework | ✅ Risk-identification + assessment + treatment tuple types with iterative cycle | `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py` |
| Regulatory sandbox / testing environment for experimental AI activities (Art. 4(f), 19(b)) | ✅ Capability-fence sandbox isolation + output-validator sandbox mode | `hummbl_governance/capability_fence.py`, `hummbl_governance/output_validator.py` |

### Transparency and AI-driven decisions (Art. 18)

| Obligation | Coverage | Evidence |
|---|---|---|
| Inform users whether a decision was made directly by AI or driven by AI for commercial or rights/services access (Art. 18) | ✅ Transparency-notification primitive (cross-ref EU AI Act Art. 50, South Korea AI Basic Act Art. 31) | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Provide understandable and transparent explanations of the decision-making process (Art. 18) | ✅ Explanation-disclosure generator (cross-ref EU AI Act Art. 13, Colorado deployer disclosure) | `hummbl_governance/compliance_mapper.py` |
| Establish mechanisms to challenge AI decisions before a competent natural person who may confirm, modify, or revoke (Art. 18) | ✅ Human-oversight delegation token + appeal-channel tuple (cross-ref EU AI Act Art. 14) | `hummbl_governance/delegation.py`, `hummbl_governance/identity.py` |
| Compliance with Art. 18 transparency is a mandatory prerequisite to access statutory safeguards (Art. 18) | 🟡 Partial: compliance-mapper tracks Art. 18 compliance status; safeguard eligibility is legal determination | `hummbl_governance/compliance_mapper.py` |

### Safeguards and lifecycle liability (Art. 19–20)

| Obligation | Coverage | Evidence |
|---|---|---|
| Liability exemption for third-party misuse of AI tools if reasonable safety/ethical/operational efforts demonstrated (Art. 19(c)) | 🟡 Partial: audit-log records safety measures and compliance evidence; liability determination is legal | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| No liability for research/experimental/sandbox activities not commercially deployed and not interfering with user rights (Art. 19(b)) | ✅ Sandbox isolation via capability-fence + audit-log sandbox-activity records with non-commercial tag | `hummbl_governance/capability_fence.py`, `hummbl_governance/audit_log.py` |
| No liability for AI exported and used outside Salvadoran jurisdiction if compliant with export law (Art. 19(d)) | ⚪ Boundary: export-jurisdiction liability is legal determination | |
| All lifecycle stakeholders — developers, implementers, service providers, end-users — responsible for their respective roles (Art. 20) | ✅ Role-based identity registry + delegation tokens for lifecycle-role attribution | `hummbl_governance/identity.py`, `hummbl_governance/delegation.py` |
| Developers must design AI systems complying with ethical and technical standards; implementers ensure proper implementation and security (Art. 20) | ✅ Output-validator + capability-fence for design-time enforcement + compliance-mapper for verification | `hummbl_governance/output_validator.py`, `hummbl_governance/capability_fence.py`, `hummbl_governance/compliance_mapper.py` |

### Ethical principles and non-discrimination (Art. 5, 25–26)

| Obligation | Coverage | Evidence |
|---|---|---|
| Respect fairness, transparency, accountability, informed consent, data minimization, inclusion, and non-discrimination (Art. 5) | ✅ Output-validator bias-detection + audit-log accountability records + data-minimization enforcement | `hummbl_governance/output_validator.py`, `hummbl_governance/audit_log.py` |
| Address risks of biases, misuse, and misinformation in AI systems (Art. 2(b)) | ✅ Output-validator + reward-monitor for bias/misuse/misinformation detection | `hummbl_governance/output_validator.py`, `hummbl_governance/reward_monitor.py` |
| No restrictions on use, modification, development, or integration of open-source AI models, datasets, weights, or software (Art. 26) | ⚪ Boundary: open-source licensing policy is organizational, not software-addressable | |
| No anti-competitive practices that unjustifiably restrict free competition in AI development (Art. 25) | ⚪ Boundary: competition-law compliance is legal, not software-addressable | |

### Data protection and security (Art. 16, 22)

| Obligation | Coverage | Evidence |
|---|---|---|
| Personal data use in AI must comply with the Law for the Protection of Personal Data (Art. 22) | ✅ Audit-log + compliance-mapper for data-protection compliance tracking (cross-ref GDPR) | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Personal data use in AI is under strict supervision of ANIA and the State Cybersecurity Agency (ACE) (Art. 22) | 🟡 Partial: audit-log export supports supervision; supervision act is org task | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Public-sector AI must comply with ACE technical security regulations in addition to ANIA criteria (Art. 16) | ✅ Capability-fence + output-validator for security-control enforcement + compliance-mapper for ACE criteria | `hummbl_governance/capability_fence.py`, `hummbl_governance/output_validator.py`, `hummbl_governance/compliance_mapper.py` |

### Institutional authority and enforcement (Art. 7–8, 27–28)

| Obligation | Coverage | Evidence |
|---|---|---|
| ANIA coordinates and supervises compliance by obligated subjects and files complaints with regulators (Art. 8(a)) | ⚪ Boundary: government supervision and enforcement is organizational | |
| ANIA issues technical security criteria and registry regulations within 90 days of enactment (Art. 27) | ⚪ Boundary: government rulemaking is organizational | |
| Law has special status over other laws, except cybersecurity and personal-data legislation (Art. 28) | ⚪ Boundary: legal-hierarchy determination is legal, not software-addressable | |
| ANIA conducts annual accountability reporting and promotes maximum transparency of its activities (Art. 8(g)) | 🟡 Partial: compliance-report generator produces accountability reports; submission is org task | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| National Registry (Art. 8(d), 16, 27; Impl. Decree Art. 11–13) | 5 | 0 | 1 | 4 |
| Risk assessment + AIA (Art. 17; Impl. Decree Art. 14–15) | 5 | 4 | 0 | 1 |
| Transparency + AI-driven decisions (Art. 18) | 4 | 3 | 1 | 0 |
| Safeguards + lifecycle liability (Art. 19–20) | 5 | 3 | 1 | 1 |
| Ethical principles + non-discrimination (Art. 5, 25–26) | 4 | 2 | 0 | 2 |
| Data protection + security (Art. 16, 22) | 3 | 2 | 1 | 0 |
| Institutional authority + enforcement (Art. 7–8, 27–28) | 4 | 0 | 1 | 3 |
| **Totals** | **30** | **14** | **5** | **11** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Transparency overlaps EU AI Act Art. 50 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Transparency overlaps South Korea AI Basic Act Art. 31 — see [`south-korea-ai-basic-act.md`](./south-korea-ai-basic-act.md)
- Risk assessment overlaps EU AI Act Art. 9 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Risk assessment overlaps NIST AI RMF GOVERN/MEASURE — see [`nist-ai-rmf.md`](./nist-ai-rmf.md)
- Human oversight overlaps EU AI Act Art. 14 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Impact assessment overlaps EU AI Act Art. 27 (FRIA) — see [`eu-ai-act.md`](./eu-ai-act.md)
- Data protection overlaps GDPR — see [`gdpr.md`](./gdpr.md)
- Sandbox isolation overlaps EU AI Act regulatory sandbox — see [`eu-ai-act.md`](./eu-ai-act.md)
