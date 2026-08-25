# GDPR Coverage Matrix — HUMMBL

**Standard**: Regulation (EU) 2016/679 — General Data Protection Regulation
**OJ reference**: published 4 May 2016; applicable 25 May 2018
**Source**: https://eur-lex.europa.eu/eli/reg/2016/679/oj
**Last reviewed**: 2026-05-14
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is **not** a supervisory authority, not a Data Protection Officer (DPO) service, and does not provide legal advice on data-protection law. This matrix maps technical primitives to controller/processor obligations. Customer organizations remain responsible for lawful-basis determination (Art. 6), DPIA execution (Art. 35), DPO appointment (Art. 37), and authority cooperation (Art. 31, 33).

## Summary

| Chapter | Articles | ✅ | 🟡 | ⚪ |
|---|---|---|---|---|
| I — General provisions | Art. 1–4 | 0 | 0 | 4 |
| II — Principles | Art. 5–11 | 5 | 2 | 0 |
| III — Rights of the data subject | Art. 12–23 | 9 | 3 | 0 |
| IV — Controller and processor | Art. 24–43 | 7 | 6 | 7 |
| V — Transfers to third countries | Art. 44–50 | 0 | 3 | 4 |
| VI — Supervisory authorities | Art. 51–59 | 0 | 0 | 9 |
| VII — Cooperation and consistency | Art. 60–76 | 0 | 0 | 17 |
| VIII — Remedies, liability, penalties | Art. 77–84 | 0 | 5 | 3 |
| IX — Specific data-processing situations | Art. 85–91 | 0 | 1 | 6 |
| X — Delegated acts | Art. 92–93 | 0 | 0 | 2 |
| XI — Final provisions | Art. 94–99 | 0 | 0 | 6 |
| **Totals** | **99** | **21** | **20** | **58** |

**Draft coverage intent (not public claim): every article in GDPR has a row. Load-bearing primitives concentrate in Chapter II (Principles) and Chapter IV (Controller obligations).

---

## Chapter I — General provisions (Art. 1–4)

| Article | Topic | Coverage |
|---|---|---|
| Art. 1 | Subject matter and objectives | ⚪ Boundary: regulatory framing |
| Art. 2 | Material scope | ⚪ Boundary: scope-defining |
| Art. 3 | Territorial scope (establishment + targeting + monitoring) | ⚪ Boundary: applicability test, customer-org determination |
| Art. 4 | Definitions (26 defined terms) | ⚪ Boundary: documentation aligned with Art. 4 terminology |

## Chapter II — Principles (Art. 5–11)

| Article | Requirement | HUMMBL coverage | Evidence |
|---|---|---|---|
| Art. 5 | Principles relating to processing — lawfulness, fairness, transparency, purpose limitation, data minimisation, accuracy, storage limitation, integrity & confidentiality, accountability | ✅ INTENT tuples capture purpose; data-governance tuples track minimisation + accuracy + retention; integrity via HMAC-signed entries; accountability via append-only governance bus. | `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py` |
| Art. 6 | Lawfulness of processing — one of 6 lawful bases must apply (consent, contract, legal obligation, vital interests, public task, legitimate interests) | 🟡 Partial: lawful-basis tuple type records which Art. 6(1) basis applies per processing activity. Determination of basis is controller-org decision. | `hummbl_governance/schema_validator.py` |
| Art. 7 | Conditions for consent — demonstrable, distinguishable, withdrawable, freely given | ✅ Consent-record tuples capture timestamp + scope + withdrawal-link. Append-only, so consent history is provable. | `hummbl_governance/audit_log.py` |
| Art. 8 | Conditions applicable to child's consent (information society services) | 🟡 Partial: age-verification tuple type for under-16 cases; parental-consent capture. Age threshold per Member State is controller-org configuration. | `hummbl_governance/schema_validator.py`, `hummbl_governance/audit_log.py` |
| Art. 9 | Processing of special categories — racial origin, political opinions, religious beliefs, trade-union membership, genetic, biometric, health, sex life/orientation. Prohibited except 10 explicit exceptions. | ✅ Special-category tag enforced at INTENT tuple boundary; processing of tagged data requires explicit Art. 9(2)(a-j) exception code on the tuple. Default-deny with audit-traced exception. | `hummbl_governance/schema_validator.py`, `hummbl_governance/audit_log.py` |
| Art. 10 | Processing of personal data relating to criminal convictions and offences | ✅ Criminal-data tag enforced at INTENT tuple boundary (same mechanism as Art. 9); authority-only-access mode via capability fence; all access audit-traced. Default-deny with audit-traced exception. | `hummbl_governance/schema_validator.py`, `hummbl_governance/capability_fence.py`, `hummbl_governance/audit_log.py` |
| Art. 11 | Processing which does not require identification | ✅ Anonymised-processing tuple type; controller can demonstrate Art. 11(2) inability-to-identify. | `hummbl_governance/audit_log.py` |

## Chapter III — Rights of the data subject (Art. 12–23)

### Section 1 — Transparency and modalities (Art. 12)

| Art. 12 | Transparent information, communication, and modalities — concise, transparent, intelligible, easily accessible form, plain language; respond within 1 month (extendable 2 months); free of charge except manifestly unfounded | 🟡 Partial: response-time tracker tuples + response-content templates. Customer-org composes responses; HUMMBL tracks SLA + provides audit log. | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |

### Section 2 — Information and access (Art. 13–15)

| Article | Requirement | HUMMBL coverage | Evidence |
|---|---|---|---|
| Art. 13 | Information to be provided where data collected from data subject | ✅ Privacy-notice generator from data-flow tuples per processing activity. | `hummbl_governance/compliance_mapper.py` |
| Art. 14 | Information to be provided where data NOT obtained from data subject (within 1 month) | ✅ Indirect-collection privacy-notice + 1-month-window tracker. | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Art. 15 | Right of access — confirmation of processing, copy of personal data, processing details | ✅ DSAR (data subject access request) export — generates copy of personal data + Art. 15 disclosures from governance bus. | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |

### Section 3 — Rectification and erasure (Art. 16–20)

| Article | Requirement | HUMMBL coverage | Evidence |
|---|---|---|---|
| Art. 16 | Right to rectification — without undue delay | ✅ Rectification tuple type — append-only correction, original retained for audit, current view reflects rectification. | `hummbl_governance/audit_log.py` |
| Art. 17 | Right to erasure ('right to be forgotten') — 6 grounds, 5 exceptions | ✅ Erasure tuple + tombstone pattern. Append-only governance bus preserves audit trail (Art. 17(3)(b) exception for legal claims); query layer suppresses subject's PII per erasure record. | `hummbl_governance/audit_log.py` |
| Art. 18 | Right to restriction of processing | ✅ Restriction-flag tuple — processing primitives consult flag and block on match. | `hummbl_governance/schema_validator.py` |
| Art. 19 | Notification obligation regarding rectification or erasure or restriction | ✅ Downstream-notification tuples — when controller has shared data with third parties (per DCT delegation chain), erasure/rectification events propagate via signed notifications. | `hummbl_governance/delegation.py`, `hummbl_governance/coordination_bus.py` |
| Art. 20 | Right to data portability — receive in structured, commonly used, machine-readable format; transmit to another controller | ✅ Portability export — JSON/CSV format per Art. 20(1). Direct controller-to-controller transmission per Art. 20(2) where technically feasible. | `hummbl_governance/compliance_mapper.py` |

### Section 4 — Right to object (Art. 21–22)

| Article | Requirement | HUMMBL coverage | Evidence |
|---|---|---|---|
| Art. 21 | Right to object to processing | 🟡 Partial: objection-record tuple + processing-pause primitive. Override evaluation (compelling legitimate grounds) is controller-org decision. | `hummbl_governance/audit_log.py`, `hummbl_governance/kill_switch.py` |
| Art. 22 | Automated individual decision-making, including profiling — right not to be subject to decision based solely on automated processing producing legal/similarly-significant effects | ✅ Solely-automated tuple flag; Art. 22 enforcement primitives — human-in-the-loop required for solely-automated + legal-effects decisions. INTENT tuple chain proves human review where required. | `hummbl_governance/delegation.py`, `hummbl_governance/kill_switch.py` |

### Section 5 — Restrictions (Art. 23)

| Art. 23 | Restrictions — Union/Member State law may restrict rights for national security, defence, public security, criminal prosecution, etc. | 🟡 Partial: restriction-flag tuple type allows controller to invoke Art. 23 restrictions; processing primitives consult flag and block on match. Legislative determination of which restrictions apply is MS law. | `hummbl_governance/schema_validator.py`, `hummbl_governance/audit_log.py` |

## Chapter IV — Controller and processor (Art. 24–43)

### Section 1 — General obligations (Art. 24–31)

| Article | Requirement | HUMMBL coverage | Evidence |
|---|---|---|---|
| Art. 24 | Responsibility of the controller — implement appropriate technical/organisational measures to demonstrate processing per GDPR | ✅ Governance bus IS the demonstration substrate. Every processing event tuple-recorded. | `hummbl_governance/coordination_bus.py`, `hummbl_governance/audit_log.py` |
| Art. 25 | Data protection by design and by default — Art. 25(1) embed at design time; Art. 25(2) defaults minimise data | ✅ Tuple schemas enforce minimisation (only declared fields accepted); INTENT tuples document design-time consideration. | `hummbl_governance/schema_validator.py`, `hummbl_governance/audit_log.py` |
| Art. 26 | Joint controllers — arrangement transparently determined | 🟡 Partial: joint-controller tuple type captures arrangement metadata; arrangement-doc authorship is org responsibility. | `hummbl_governance/audit_log.py` |
| Art. 27 | Representatives of controllers/processors not established in EU | ⚪ Boundary: corporate-legal designation |
| Art. 28 | Processor — binding contract per Art. 28(3); processing only on documented instructions | 🟡 Partial: DCT tuples (delegation tokens) implement Art. 28(3) instruction discipline — processor scope cryptographically bound. DPA contract is legal artifact, separate from technical primitive. | `hummbl_governance/delegation.py` for instruction binding |
| Art. 29 | Processing under the authority of the controller or processor | ✅ DCT chain enforces — no processing without authorising delegation. | `hummbl_governance/delegation.py` |
| Art. 30 | Records of processing activities — Art. 30(1) controllers, Art. 30(2) processors; maintain in writing including electronic | ✅ Governance bus IS the Art. 30 record. Required fields (name, contact, purposes, categories, recipients, transfers, retention, security measures) generated from tuple aggregations. | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/coordination_bus.py` |
| Art. 31 | Cooperation with the supervisory authority | ✅ Export-on-demand per Art. 21 (mirroring EU AI Act). | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |

### Section 2 — Security of personal data (Art. 32–34)

| Article | Requirement | HUMMBL coverage | Evidence |
|---|---|---|---|
| Art. 32 | Security of processing — appropriate technical/organisational measures: pseudonymisation, encryption, CIA + resilience, restoration, regular testing | ✅ HMAC-SHA256 signed entries (integrity), encryption-at-rest configurable, append-only (no overwrite = strong integrity), circuit-breaker (resilience), 927 tests = regular testing per Art. 32(1)(d), Bandit/Semgrep + pip-audit blocking (security testing CI). | `hummbl_governance/audit_log.py`, `hummbl_governance/circuit_breaker.py`, `.github/workflows/ci.yml` |
| Art. 33 | Notification of personal data breach to supervisory authority — within 72 hours | ✅ Breach-detection tuple → 72-hour-notification primitive; clock starts at controller-awareness tuple, alert escalates at hour 60/72. | `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py` |
| Art. 34 | Communication of personal data breach to the data subject | 🟡 Partial: subject-notification primitive composes per Art. 34(2) content; high-risk determination is controller-org judgment. | `hummbl_governance/coordination_bus.py`, `hummbl_governance/compliance_mapper.py` |

### Section 3 — Data protection impact assessment + prior consultation (Art. 35–36)

| Article | Requirement | HUMMBL coverage | Evidence |
|---|---|---|---|
| Art. 35 | DPIA — required for high-risk processing (Art. 35(3): solely-automated decisions, large-scale special-category, large-scale public monitoring); content per Art. 35(7) | 🟡 Partial: DPIA template + evidence-bundle generator pulling from governance bus. Authorship of risk assessment is controller-org responsibility. | `[DRAFT — planned per ADR-001] compliance_mapper --export dpia-template --activity <id>` |
| Art. 36 | Prior consultation — controller shall consult supervisory authority where DPIA indicates high residual risk | 🟡 Partial: compliance mapper exports DPIA evidence bundle (processing records, risk assessment inputs, audit trail) for prior consultation with supervisory authority. Consultation itself is authority engagement, controller-org responsibility. | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |

### Section 4 — DPO (Art. 37–39)

| Article | Requirement | HUMMBL coverage | Evidence |
|---|---|---|---|
| Art. 37 | Designation of the DPO | ⚪ Boundary: organizational designation | |
| Art. 38 | Position of the DPO | ⚪ Boundary: org reporting structure | |
| Art. 39 | Tasks of the DPO | 🟡 Partial: governance bus provides the visibility substrate for DPO tasks (compliance monitoring, audit review, processing-activity records). DPO appointment and role definition remain org responsibility. | `hummbl_governance/coordination_bus.py`, `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |

### Section 5 — Codes of conduct + certification (Art. 40–43)

| Articles | Topics | HUMMBL coverage |
|---|---|---|
| Art. 40 | Codes of conduct (industry codes) | ⚪ Boundary: voluntary association |
| Art. 41 | Monitoring of approved codes of conduct | ⚪ Boundary: code-body function |
| Art. 42 | Certification mechanisms, seals, marks | ⚪ Boundary: accredited certification |
| Art. 43 | Certification bodies | ⚪ Boundary: accreditation regime |

## Chapter V — Transfers to third countries (Art. 44–50)

| Article | Requirement | HUMMBL coverage | Evidence |
|---|---|---|---|
| Art. 44 | General principle — transfer only if conditions in Chapter V met | 🟡 Partial: cross-border-transfer tuple type enforces that any transfer must reference a Chapter V legal basis (adequacy, SCC, BCR, or derogation code) before processing primitives accept it. Determination of which basis applies is controller-org decision. | `hummbl_governance/schema_validator.py`, `hummbl_governance/audit_log.py` |
| Art. 45 | Transfers on basis of adequacy decision | ⚪ Boundary: Commission adequacy decision |
| Art. 46 | Transfers subject to appropriate safeguards (SCCs, BCRs, certification) | 🟡 Partial: cross-border-transfer tuple type captures legal-basis (SCC ref, BCR ref, adequacy decision). SCC/BCR document authorship is legal-org task. | `hummbl_governance/schema_validator.py`, `hummbl_governance/audit_log.py` |
| Art. 47 | Binding corporate rules | ⚪ Boundary: BCR is intra-group legal instrument |
| Art. 48 | Transfers or disclosures not authorised by Union law | ⚪ Boundary: foreign-court-order regime |
| Art. 49 | Derogations for specific situations (consent, contract, public interest, vital interests) | 🟡 Partial: derogation-basis tuple type captures which Art. 49 derogation applies per transfer; audit log records invocation. Determination of whether derogation conditions are met is controller-org decision. | `hummbl_governance/schema_validator.py`, `hummbl_governance/audit_log.py` |
| Art. 50 | International cooperation for the protection of personal data | ⚪ Boundary: Commission cooperation |

## Chapter VI — Independent supervisory authorities (Art. 51–59)

All boundary rows — Member State authority structure.

| Articles | Topic | Coverage |
|---|---|---|
| Art. 51 | Supervisory authority | ⚪ Boundary: Member State authority establishment |
| Art. 52 | Independence | ⚪ Boundary: institutional independence guarantee |
| Art. 53 | General conditions for the members of the supervisory authority | ⚪ Boundary: member appointment conditions |
| Art. 54 | Rules on the establishment of the supervisory authority | ⚪ Boundary: MS institutional structure |
| Art. 55 | Competence | ⚪ Boundary: authority competence rules |
| Art. 56 | Competence of the lead supervisory authority | ⚪ Boundary: lead-authority designation |
| Art. 57 | Tasks | ⚪ Boundary: authority statutory tasks |
| Art. 58 | Powers (investigative, corrective, authorisation, advisory) | ⚪ Boundary: authority statutory powers |
| Art. 59 | Activity reports | ⚪ Boundary: authority reporting obligation |

All ⚪ Boundary.

## Chapter VII — Cooperation and consistency (Art. 60–76)

17 articles — all institutional procedure between authorities.

| Articles | Topic | Coverage |
|---|---|---|
| Art. 60 | Cooperation between the lead supervisory authority and the other supervisory authorities concerned | ⚪ Boundary: authority-to-authority cooperation |
| Art. 61 | Mutual assistance | ⚪ Boundary: authority mutual-assistance procedure |
| Art. 62 | Joint operations of supervisory authorities | ⚪ Boundary: authority joint-operation procedure |
| Art. 63 | Consistency mechanism | ⚪ Boundary: Board consistency mechanism |
| Art. 64 | Opinion of the Board | ⚪ Boundary: Board opinion procedure |
| Art. 65 | Dispute resolution by the Board | ⚪ Boundary: Board dispute-resolution procedure |
| Art. 66 | Urgency procedure | ⚪ Boundary: Board urgency procedure |
| Art. 67 | Exchange of information | ⚪ Boundary: authority information exchange |
| Art. 68 | European Data Protection Board | ⚪ Boundary: Board establishment |
| Art. 69 | Independence of the Board | ⚪ Boundary: Board independence guarantee |
| Art. 70 | Tasks of the Board | ⚪ Boundary: Board statutory tasks |
| Art. 71 | Reports | ⚪ Boundary: Board reporting obligation |
| Art. 72 | Procedure | ⚪ Boundary: Board procedural rules |
| Art. 73 | Chair | ⚪ Boundary: Chair election |
| Art. 74 | Tasks of the Chair | ⚪ Boundary: Chair statutory tasks |
| Art. 75 | Secretariat | ⚪ Boundary: Secretariat establishment |
| Art. 76 | Confidentiality | ⚪ Boundary: Board confidentiality rules |

All ⚪ Boundary — authority-to-authority cooperation, no software primitive.

## Chapter VIII — Remedies, liability and penalties (Art. 77–84)

| Article | Topic | HUMMBL coverage | Evidence |
|---|---|---|---|
| Art. 77 | Right to lodge a complaint with a supervisory authority | 🟡 Partial: compliance mapper exports evidence-on-demand (processing records, audit trail, DSAR history) to support data-subject complaint lodgement. Complaint submission itself is subject–authority interaction. | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Art. 78 | Right to an effective judicial remedy against a supervisory authority | ⚪ Boundary: judicial procedure | |
| Art. 79 | Right to an effective judicial remedy against a controller or processor | 🟡 Partial: audit log + compliance mapper export evidence-on-demand (processing history, access logs, breach records) for judicial proceedings against controller/processor. Liability determination is judicial. | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Art. 80 | Representation of data subjects | ⚪ Boundary: representation regime | |
| Art. 81 | Suspension of proceedings | ⚪ Boundary: judicial procedure | |
| Art. 82 | Right to compensation and liability | 🟡 Partial: audit log + compliance mapper export evidence-on-demand (processing history, access logs, breach records) for liability defense and compensation proceedings. Liability determination is judicial. | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Art. 83 | General conditions for imposing administrative fines — up to €20M or 4% global annual turnover (Tier 1), up to €10M or 2% (Tier 2) | 🟡 Partial: audit log + compliance mapper export evidence-on-demand for due-diligence demonstration and defense against fines. Fine imposition is supervisory-authority action. | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Art. 84 | Penalties (Member State criminal penalties for infringements not subject to Art. 83) | 🟡 Partial: evidence-on-demand for criminal proceedings | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |

## Chapter IX — Specific data-processing situations (Art. 85–91)

| Articles | Topic | HUMMBL coverage | Evidence |
|---|---|---|---|
| Art. 85 | Processing and freedom of expression and information | ⚪ Boundary: MS legislative carve-out | |
| Art. 86 | Processing and public access to official documents | ⚪ Boundary: MS carve-out | |
| Art. 87 | Processing of the national identification number | ⚪ Boundary: MS regime | |
| Art. 88 | Processing in the context of employment | ⚪ Boundary: MS carve-out | |
| Art. 89 | Safeguards and derogations for archiving / research / statistical purposes | 🟡 Partial: purpose-tag tuples (archiving, research, statistical) enforce minimisation + accuracy + storage-limitation safeguards at INTENT boundary; audit log tracks purpose-bound processing. Specific derogations and safeguards are MS-law-determined. | `hummbl_governance/schema_validator.py`, `hummbl_governance/audit_log.py` |
| Art. 90 | Obligations of secrecy | ⚪ Boundary: profession-specific regime | |
| Art. 91 | Existing data-protection rules of churches and religious associations | ⚪ Boundary: religious-association carve-out | |

## Chapter X — Delegated acts and implementing acts (Art. 92–93)

| Art. 92 | Exercise of the delegation | ⚪ Boundary: Commission rule-making |
| Art. 93 | Committee procedure | ⚪ Boundary: Commission procedure |

## Chapter XI — Final provisions (Art. 94–99)

| Art. 94 | Repeal of Directive 95/46/EC | ⚪ Boundary |
| Art. 95 | Relationship with Directive 2002/58/EC | ⚪ Boundary |
| Art. 96 | Relationship with previously concluded agreements | ⚪ Boundary |
| Art. 97 | Commission reports | ⚪ Boundary |
| Art. 98 | Review of other Union legal acts on data protection | ⚪ Boundary |
| Art. 99 | Entry into force and application | ⚪ Boundary |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- EU AI Act matrix: [`eu-ai-act.md`](./eu-ai-act.md)
- Prior partial mapping: `docs/gdpr-mapping.md` (covers 6 articles; superseded by this full enumeration)
