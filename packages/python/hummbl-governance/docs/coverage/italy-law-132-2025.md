# Italy Law No. 132/2025 Coverage Matrix — HUMMBL

**Standard**: Law No. 132 of September 23, 2025 — Disposizioni e deleghe al Governo in materia di intelligenza artificiale (Provisions and Delegations to the Government on Artificial Intelligence)
**Effective**: October 10, 2025
**Source**: https://www.normattiva.it/eli/id/2025/09/25/25G00143/CONSOLIDATED
**Last reviewed**: 2026-05-14
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not Italian legal counsel and does not provide legal advice on Law No. 132/2025. The Law is the first domestic AI law in the EU and complements the EU AI Act. It is enforced through designated National Authorities (AgID, ACN) with implementing decrees expected within 12 months. Statutory compliance is the customer-organization responsibility. HUMMBL maps technical primitives to the Law's transparency, human oversight, data protection, cybersecurity, and sector-specific obligations.

## Scope summary

Law No. 132/2025 is a cross-sector AI law covering healthcare, labor, intellectual professions, public administration, justice, education, sport, and cybersecurity. It establishes general principles (anthropocentric, transparency, proportionality, security, non-discrimination), designates AgID and ACN as National Authorities, authorizes €1 billion in AI investments, establishes criminal offenses for deepfakes, and delegates implementing decrees to the Government within 12 months.

## Obligations + coverage

### General principles (Arts. 1-3)

| Obligation | Coverage | Evidence |
|---|---|---|
| Compliance with EU AI Act — all provisions interpreted in conformity with Regulation (EU) 2024/1689 | ✅ EU AI Act coverage matrix = alignment evidence (cross-ref) | `docs/coverage/eu-ai-act.md` |
| Anthropocentric approach — human autonomy and decision-making power | ✅ Human-oversight delegation token + decision-authority primitive (cross-ref EU AI Act Art. 14) | `hummbl_governance/delegation.py`, `hummbl_governance/identity.py` |
| Fundamental rights compliance | ✅ Rights-impact-assessment tuple + fairness-evaluation primitive | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Core principles — transparency, proportionality, security, data protection, accuracy, non-discrimination, sustainability | ✅ Principles-alignment tuple + compliance-framework primitive | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Data and process quality — correctness, reliability, security, quality, appropriateness, transparency | ✅ Data-quality-assessment tuple + validation primitive (cross-ref EU AI Act Art. 10) | `hummbl_governance/schema_validator.py`, `hummbl_governance/audit_log.py` |
| Human oversight and intervention | ✅ Human-oversight delegation + kill-switch halt (cross-ref EU AI Act Art. 14) | `hummbl_governance/delegation.py`, `hummbl_governance/kill_switch.py` |
| Cybersecurity as essential precondition — resilience against alteration attempts | ✅ Cybersecurity-controls tuple + circuit-breaker + audit-trail (cross-ref ISO 27001, NIST CSF PR) | `hummbl_governance/circuit_breaker.py`, `hummbl_governance/audit_log.py` |

### Data protection and transparency (Art. 4)

| Obligation | Coverage | Evidence |
|---|---|---|
| Media pluralism protection — AI must not prejudice press freedom and pluralism | ⚪ Boundary: media-pluralism is institutional, not software-addressable | |
| Lawful, fair, transparent data processing compatible with collection purposes | ✅ Data-lawfulness tuple + purpose-limitation primitive (cross-ref GDPR Art. 5) | `hummbl_governance/audit_log.py`, `hummbl_governance/schema_validator.py` |
| Clear and simple information about data processing and AI use | ✅ Plain-language-disclosure tuple + transparency primitive (cross-ref EU AI Act Art. 50) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/output_validator.py` |
| Parental consent for under-14s accessing AI technologies | ✅ Consent-verification tuple + age-gate primitive (cross-ref GDPR Art. 8) | `hummbl_governance/audit_log.py`, `hummbl_governance/delegation.py` |
| Autonomous consent for 14-18 year olds with accessible information | ✅ Consent-verification tuple + accessible-information primitive | `hummbl_governance/audit_log.py` |

### Healthcare sector (Arts. 7-10)

| Obligation | Coverage | Evidence |
|---|---|---|
| AI must improve healthcare, prevention, diagnosis, treatment respecting rights | ✅ Purpose-alignment tuple + rights-respect primitive | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Non-discrimination in healthcare access | ✅ Discrimination-detection primitive + fairness-evaluation tuple (cross-ref Colorado SB 24-205) | `hummbl_governance/audit_log.py`, `hummbl_governance/schema_validator.py` |
| Patient right to be informed about AI use | ✅ Transparency-notification primitive (cross-ref EU AI Act Art. 50) | `hummbl_governance/audit_log.py` |
| Medical decision authority remains with professionals — AI is support only | ✅ Human-decision-authority tuple + oversight-delegation primitive | `hummbl_governance/delegation.py`, `hummbl_governance/identity.py` |
| System reliability, periodic verification, and updates to minimize errors | ✅ Reliability-verification tuple + lifecycle-monitoring primitive | `hummbl_governance/audit_log.py`, `hummbl_governance/lifecycle.py` |
| Secondary use of health data for research via website notice (without further consent) | 🟡 Partial: data-use-notification tuple; website-notice implementation is org task | `hummbl_governance/audit_log.py` |
| Health data processing as significant public interest | 🟡 Partial: compliance-mapper can record legal-basis classification for health data processing; legal determination of "significant public interest" is org/legal task | `hummbl_governance/compliance_mapper.py` |
| Ministry of Health decree for AI in healthcare, EHR, surveillance systems | ⚪ Boundary: government-rulemaking is institutional | |

### Labor and employment (Arts. 11-12)

| Obligation | Coverage | Evidence |
|---|---|---|
| AI must improve working conditions and protect worker psychophysical integrity | ✅ Purpose-alignment tuple + safety-primitive | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Workplace AI must be safe, reliable, transparent, non-violating of dignity | ✅ Safety-reliability-transparency tuple + output-validation gate | `hummbl_governance/output_validator.py`, `hummbl_governance/audit_log.py` |
| Employer must inform worker of AI use per remote-worker monitoring rules | ✅ Worker-notification tuple + disclosure primitive | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Non-discrimination in employment AI (sex, age, ethnicity, religion, sexual orientation, political opinions) | ✅ Discrimination-detection primitive + protected-class tuple | `hummbl_governance/audit_log.py`, `hummbl_governance/schema_validator.py` |
| Labor Observatory establishment at Ministry of Labor | ⚪ Boundary: government-observatory is institutional | |
| Observatory training promotion for workers and employers | ⚪ Boundary: government-training is institutional | |

### Intellectual professions (Art. 13)

| Obligation | Coverage | Evidence |
|---|---|---|
| AI use in intellectual professions is ancillary and supportive only | ✅ Ancillary-use-classification tuple + human-oversight primitive | `hummbl_governance/delegation.py`, `hummbl_governance/audit_log.py` |
| Professional must inform client of AI use in clear, simple, exhaustive language | ✅ Client-disclosure tuple + transparency primitive | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |

### Public administration (Art. 14)

| Obligation | Coverage | Evidence |
|---|---|---|
| PA must use AI to increase efficiency, reduce time, improve service quality | ✅ Purpose-alignment tuple + efficiency-metric primitive | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| PA must ensure knowability of AI functioning and traceability of use | ✅ Audit-trail immutability + traceability tuple + explainability primitive | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| AI use is instrumental and supportive — decision authority with human | ✅ Human-decision-authority tuple + oversight-delegation primitive | `hummbl_governance/delegation.py`, `hummbl_governance/identity.py` |
| PA must adopt technical, organizational, and training measures for responsible AI use | 🟡 Partial: technical-measures via governance primitives; organizational/training measures are org task | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| PA must fulfill obligations with available human, instrumental, financial resources | 🟡 Partial: cost-governor manages financial resource budgets for AI operations; human/instrumental resource allocation is org task | `hummbl_governance/cost_governor.py` |

### Judicial activity (Art. 15)

| Obligation | Coverage | Evidence |
|---|---|---|
| Magistrate decision authority — all interpretation, fact assessment, measures reserved to magistrate | ✅ Human-decision-authority tuple + oversight-delegation primitive | `hummbl_governance/delegation.py`, `hummbl_governance/identity.py` |
| Ministry of Justice regulation of AI use in judicial services | ⚪ Boundary: government-rulemaking is institutional | |
| Authorization required for AI experimentation in judicial offices | 🟡 Partial: admission-control gates agent execution requiring authorization; governmental authorization process for judicial offices is institutional | `hummbl_governance/kernel/admission_control.py` |
| Magistrate AI training in programmatic guidelines | ⚪ Boundary: government-training is institutional | |
| Administrative staff AI training | ⚪ Boundary: government-training is institutional | |

### Civil procedure (Art. 17)

| Obligation | Coverage | Evidence |
|---|---|---|
| Tribunal exclusive competence for AI system functioning disputes | ⚪ Boundary: judicial-jurisdiction is legal determination | |

### National cybersecurity (Art. 18)

| Obligation | Coverage | Evidence |
|---|---|---|
| ACN must promote AI for strengthening national cybersecurity | 🟡 Partial: cybersecurity-resilience primitives (circuit-breaker, audit-trail, STRIDE threat-mapping) support AI system hardening; ACN national promotion initiative is institutional | `hummbl_governance/circuit_breaker.py`, `hummbl_governance/audit_log.py`, `hummbl_governance/stride_mapper.py` |

### National strategy (Art. 19)

| Obligation | Coverage | Evidence |
|---|---|---|
| National AI Strategy preparation and biennial update | ⚪ Boundary: government-strategy is institutional | |
| Strategy content — cooperation, coordination, research, incentives | ⚪ Boundary: government-strategy is institutional | |
| Strategy coordination and monitoring via Agency for Digital Italy | ⚪ Boundary: government-monitoring is institutional | |

### National authorities (Art. 20)

| Obligation | Coverage | Evidence |
|---|---|---|
| AgID and ACN designated as National Authorities for AI | ⚪ Boundary: government-authority designation is institutional | |
| AgID — promote innovation, notification/accreditation of conformity bodies | ⚪ Boundary: government-authority function is institutional | |
| ACN — supervision, inspection, sanctioning of AI systems | ⚪ Boundary: government-authority function is institutional | |
| AgID and ACN — joint management of experimentation spaces | ⚪ Boundary: government-facility is institutional | |
| AgID as notifying authority under EU AI Act Art. 70 | ⚪ Boundary: government-role designation is institutional | |
| ACN as market surveillance authority under EU AI Act Art. 70 | ⚪ Boundary: government-role designation is institutional | |
| Coordination between National Authorities and other administrations | ⚪ Boundary: inter-governmental coordination is institutional | |
| Coordination Committee establishment | ⚪ Boundary: government-committee is institutional | |

### Coordination Committee (Art. 21)

| Obligation | Coverage | Evidence |
|---|---|---|
| High-level Coordination Committee for digital innovation and AI guidance | ⚪ Boundary: government-committee is institutional | |
| Committee composition (multiple ministers and authorities) | ⚪ Boundary: government-composition is institutional | |
| Committee coordination functions for AI research, experimentation, adoption | ⚪ Boundary: government-coordination is institutional | |
| Committee training policy coordination | ⚪ Boundary: government-policy is institutional | |
| No compensation for Committee participation | ⚪ Boundary: government-compensation policy is institutional | |

### Young people and sport (Art. 22)

| Obligation | Coverage | Evidence |
|---|---|---|
| AI research recognition for youth benefit programs | ⚪ Boundary: government-benefit program is institutional | |
| High-potential student AI programs in upper secondary school | ⚪ Boundary: education-policy is institutional | |
| Training credit recognition for AI activities | ⚪ Boundary: education-policy is institutional | |
| AI for sports well-being and disability inclusion | ⚪ Boundary: government-promotion is institutional | |
| AI for sports organization in compliance with general principles | ✅ Principles-alignment tuple + compliance primitive | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |

### Investments (Art. 23)

| Obligation | Coverage | Evidence |
|---|---|---|
| €1 billion authorized investment in AI, cybersecurity, quantum entities | ⚪ Boundary: government-investment is institutional | |
| Investment targets — SMEs, innovative, Italy-based, AI/cyber/quantum/5G | ⚪ Boundary: investment-fund management is institutional | |
| Technology transfer poles and acceleration programs | ⚪ Boundary: government-program is institutional | |
| Investment mechanism via Venture Capital Support Fund | ⚪ Boundary: government-fund mechanism is institutional | |

### Government delegations — data and algorithms (Art. 16)

| Obligation | Coverage | Evidence |
|---|---|---|
| Government delegated to define data/algorithm use discipline within 12 months | ⚪ Boundary: government-rulemaking is institutional | |
| Delegation procedure — proposal, parliamentary opinion, 60-day wait | ⚪ Boundary: legislative-procedure is institutional | |
| Legal regime definition for data/algorithm use and party rights/obligations | ⚪ Boundary: government-rulemaking is institutional | |
| Protective and sanctioning measures in implementing decrees | ⚪ Boundary: government-rulemaking is institutional | |

### Government delegations — general implementation (Art. 24)

| Obligation | Coverage | Evidence |
|---|---|---|
| National legislation adaptation to EU AI Act within 12 months | ⚪ Boundary: government-rulemaking is institutional | |
| Authority powers attribution (supervisory, inspection, sanctioning) | ⚪ Boundary: government-rulemaking is institutional | |
| Financial sector adaptation for EU AI Act compliance | ⚪ Boundary: government-rulemaking is institutional | |
| Sanctions compliance with EU AI Act Art. 99 editorial limits | ⚪ Boundary: government-rulemaking is institutional | |
| Unlawful AI use regulation — precautionary and sanctioning measures | 🟡 Partial: kill-switch and circuit-breaker provide technical precautionary measures against unlawful AI use; governmental sanctioning regulation is institutional | `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py` |

### Copyright and AI-generated works (Art. 25)

| Obligation | Coverage | Evidence |
|---|---|---|
| Human creativity specification — copyright protects human intellectual work, including AI-assisted | 🟡 Partial: audit-log records human creative inputs vs AI-generated content + identity attributes contributions to human creators; legal copyright determination is legal task | `hummbl_governance/audit_log.py`, `hummbl_governance/identity.py` |
| Text and data mining for AI training per TDM exceptions (Arts. 70-ter, 70-quater) | 🟡 Partial: compliance-mapper can track TDM exception applicability for training datasets; legal exception determination is legal task | `hummbl_governance/compliance_mapper.py` |

### Criminal provisions (Art. 26)

| Obligation | Coverage | Evidence |
|---|---|---|
| Deepfake offense — 1-5 years imprisonment for distributing falsified images/videos/voices without consent | ⚪ Boundary: criminal-offense definition is legal | |
| Deepfake prosecution rules — complaint within 6 months, ex officio for vulnerable victims | ⚪ Boundary: criminal-procedure is legal | |
| Aggravating circumstance for AI use in committing crimes (insidious means or obstruction of defense) | ⚪ Boundary: criminal-sentencing is legal | |
| Copyright violation for AI data extraction | ⚪ Boundary: criminal-offense is legal | |
| Market manipulation AI aggravation in financial legislation | ⚪ Boundary: criminal-offense is legal | |

### Pending implementing decrees

| Obligation | Coverage | Evidence |
|---|---|---|
| Conformity assessment body accreditation procedures | ⚪ Boundary: government-rulemaking is institutional | |
| High-risk system lists and thresholds for Italy | 🟡 Partial: compliance-mapper can classify systems against EU AI Act risk tiers; Italian-specific lists and thresholds are government-determined | `hummbl_governance/compliance_mapper.py` |
| Notification and conformity assessment procedures | 🟡 Partial: compliance-mapper can track conformity assessment notifications and status for AI systems; governmental procedure definition is institutional | `hummbl_governance/compliance_mapper.py` |
| Sanctions and fines scales | ⚪ Boundary: government-rulemaking is institutional | |
| Inspection procedures | 🟡 Partial: audit-log provides inspectable trail for AI system operations; governmental inspection procedure definition is institutional | `hummbl_governance/audit_log.py` |
| Healthcare platform rules | ⚪ Boundary: government-rulemaking is institutional | |
| Financial services AI rules | ⚪ Boundary: government-rulemaking is institutional | |
| Civil liability for unlawful AI development or use | 🟡 Partial: audit-log provides evidence trail of AI development and use activities for liability determinations; governmental liability regime definition is institutional | `hummbl_governance/audit_log.py` |
| Criminal liability criteria for AI-committed offenses | ⚪ Boundary: government-rulemaking is institutional | |
| Liability for safety measure omission creating danger | 🟡 Partial: audit-log records safety-measure activation status (kill-switch, circuit-breaker) for liability determinations; governmental liability regime definition is institutional | `hummbl_governance/audit_log.py`, `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py` |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| General principles (Arts. 1-3) | 7 | 7 | 0 | 0 |
| Data protection + transparency (Art. 4) | 5 | 4 | 0 | 1 |
| Healthcare (Arts. 7-10) | 8 | 5 | 2 | 1 |
| Labor + employment (Arts. 11-12) | 6 | 4 | 0 | 2 |
| Intellectual professions (Art. 13) | 2 | 2 | 0 | 0 |
| Public administration (Art. 14) | 5 | 3 | 2 | 0 |
| Judicial activity (Art. 15) | 5 | 1 | 1 | 3 |
| Civil procedure (Art. 17) | 1 | 0 | 0 | 1 |
| National cybersecurity (Art. 18) | 1 | 0 | 1 | 0 |
| National strategy (Art. 19) | 3 | 0 | 0 | 3 |
| National authorities (Art. 20) | 8 | 0 | 0 | 8 |
| Coordination Committee (Art. 21) | 5 | 0 | 0 | 5 |
| Young people + sport (Art. 22) | 5 | 1 | 0 | 4 |
| Investments (Art. 23) | 4 | 0 | 0 | 4 |
| Delegations — data/algorithms (Art. 16) | 4 | 0 | 0 | 4 |
| Delegations — implementation (Art. 24) | 5 | 0 | 1 | 4 |
| Copyright (Art. 25) | 2 | 0 | 2 | 0 |
| Criminal provisions (Art. 26) | 5 | 0 | 0 | 5 |
| Pending implementing decrees | 10 | 0 | 5 | 5 |
| **Totals** | **91** | **27** | **14** | **50** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- EU AI Act alignment — see [`eu-ai-act.md`](./eu-ai-act.md)
- Human oversight overlaps EU AI Act Art. 14 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Data protection overlaps GDPR — see [`gdpr.md`](./gdpr.md)
- Cybersecurity overlaps ISO 27001 — see [`iso-27001.md`](./iso-27001.md)
- Discrimination detection overlaps Colorado SB 24-205 — see [`colorado-ai-act.md`](./colorado-ai-act.md)
