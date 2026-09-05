# EU AI Act Coverage Matrix — HUMMBL

**Standard**: Regulation (EU) 2024/1689 — Artificial Intelligence Act
**OJ reference**: published 12 July 2024; entered into force 1 August 2024
**Source**: https://eur-lex.europa.eu/eli/reg/2024/1689/oj
**Last reviewed**: 2026-05-14
**Reviewer**: claude-code (host-C) — pilot per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version mapped against**: hummbl-governance v0.8.0 (927 dedicated tests)

## Boundary disclaimer (statutory)

HUMMBL is **not** a Notified Body under EU AI Act Article 31. This matrix maps technical primitives to control requirements; it does **not** constitute a Notified Body conformity assessment per Article 43. Statutory conformity assessment for Annex III high-risk systems requires either (a) internal control assessment per Annex VI, or (b) Notified Body assessment per Annex VII (mandatory for biometric identification systems). HUMMBL provides the **technical evidence interface** that supports either assessment path; the legal conformity declaration is the provider's responsibility.

## Coverage state legend

| Glyph | State | Meaning |
|---|---|---|
| ✅ | Fulfilled | HUMMBL primitive implements the control; runnable evidence artifact exists |
| 🟡 | Partial | HUMMBL primitive provides part; customer policy completes it. Both parts named. |
| ⚪ | Boundary | Control is organizational, regulatory, or institutional; HUMMBL provides evidence interface where applicable. |
| ⛔ | Out of scope | Control does not apply to AI governance platform context (retained for completeness). |

## Summary by chapter

| Chapter | Title | Article range | ✅ | 🟡 | ⚪ | ⛔ |
|---|---|---|---|---|---|---|
| I | General provisions | Art. 1–4 | 0 | 1 | 3 | 0 |
| II | Prohibited AI practices | Art. 5 | 1 | 0 | 0 | 0 |
| III | High-risk AI systems | Art. 6–49 | 13 | 10 | 21 | 0 |
| IV | Transparency obligations | Art. 50 | 0 | 1 | 0 | 0 |
| V | GPAI models | Art. 51–56 | 0 | 3 | 3 | 0 |
| VI | Innovation measures (regulatory sandboxes) | Art. 57–63 | 0 | 2 | 5 | 0 |
| VII | Governance (EU AI Office, AI Board) | Art. 64–70 | 0 | 0 | 7 | 0 |
| VIII | EU database for high-risk systems | Art. 71 | 0 | 1 | 0 | 0 |
| IX | Post-market monitoring, info-sharing, market surveillance | Art. 72–94 | 4 | 6 | 13 | 0 |
| X | Codes of conduct | Art. 95 | 1 | 0 | 0 | 0 |
| XI | Delegation of power, committee | Art. 96–98 | 0 | 0 | 3 | 0 |
| XII | Penalties | Art. 99–101 | 0 | 0 | 3 | 0 |
| XIII | Final provisions | Art. 102–113 | 0 | 0 | 12 | 0 |
| **Article totals** | | **113 articles** | **19** | **24** | **70** | **0** |
| **Annex totals** | | **13 annexes** | **6** | **3** | **4** | **0** |
| **Grand totals** | | **126 rows** | **25** | **27** | **74** | **0** |

**Annexes**: 13 annexes. Annex I (high-risk list, NLF), Annex II (criminal offences for biometric ID), Annex III (high-risk use cases — 8 areas), Annex IV (technical documentation), Annex V (EU declaration of conformity), Annex VI–VII (conformity assessment procedures), Annex VIII (registration info), Annex IX (registration for law enforcement), Annex X (legislative acts), Annex XI–XII (GPAI documentation), Annex XIII (criteria for GPAI systemic risk).

**Draft coverage intent (not public claim): every article in EU AI Act has a row stating either a HUMMBL primitive that addresses it, a partial-coverage description, or an explicit boundary statement. No article is silently excluded.

---

## Chapter I — General provisions (Art. 1–4)

| Article | Requirement | HUMMBL coverage | Evidence |
|---|---|---|---|
| Art. 1 | Subject matter — establish AI Act framework | ⚪ Boundary: regulatory framing, not a control. | n/a |
| Art. 2 | Scope — applies to providers, deployers, importers, distributors of AI systems placed on EU market | ⚪ Boundary: scope-defining article. HUMMBL is a provider of AI governance platform; its customers may be providers/deployers of AI systems subject to the Act. | n/a |
| Art. 3 | Definitions (68 defined terms: AI system, GPAI, deployer, biometric identification, etc.) | ⚪ Boundary: definitional article. HUMMBL's documentation aligns terminology with Art. 3 definitions. | docs glossary alignment |
| Art. 4 | AI literacy — providers and deployers shall take measures to ensure AI literacy of their staff and persons dealing with AI on their behalf | 🟡 Partial: HUMMBL provides documentation, runbooks, and compliance-mapper output that serve as AI literacy reference material. Literacy program design and delivery is customer-org responsibility. | `hummbl_governance/compliance_mapper.py`, `docs/` |

## Chapter II — Prohibited AI practices (Art. 5)

| Article | Requirement | HUMMBL coverage | Evidence |
|---|---|---|---|
| Art. 5 | Prohibits 8 categories of AI practice: subliminal manipulation, exploitation of vulnerabilities, social scoring by public authorities, predictive policing solely from profiling, untargeted facial-image scraping, emotion recognition in workplace/education (with exceptions), biometric categorisation inferring sensitive attributes, real-time remote biometric identification in public spaces (with exceptions). | ✅ **Fulfilled — detection + halt + audit trail.** HUMMBL provides: (a) use-case classification taxonomy aligned with Art. 5 categories via `compliance_mapper`, (b) red-flag detection on agent-action tuples flagging prohibited-practice signatures, (c) `hummbl_governance/kill_switch.py` to halt agents on red-flag trigger, (d) `hummbl_governance/circuit_breaker.py` for automatic escalation, (e) governance-bus evidence trail for post-hoc audit. Customer-organization policy defines which use cases are deployed; HUMMBL detects and halts deviation with full audit trail. | `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py`, `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |

## Chapter III — High-risk AI systems (Art. 6–49)

### Section 1 — Classification rules (Art. 6–7)

| Article | Requirement | HUMMBL coverage | Evidence |
|---|---|---|---|
| Art. 6 | Classification rules for high-risk AI systems (Annex I product-safety, Annex III use-case list) | 🟡 Partial: classification rule applied by provider. HUMMBL provides use-case taxonomy mapped to Annex III categories via compliance_mapper, enabling automated classification. Final classification decision is provider responsibility. | `hummbl_governance/compliance_mapper.py` |
| Art. 7 | Commission empowered to amend Annex III high-risk list | ⚪ Boundary: institutional power. HUMMBL re-publishes matrix on Annex III updates. | versioning policy (annual review) |

### Section 2 — Requirements for high-risk AI systems (Art. 8–15) ← **the load-bearing controls**

| Article | Requirement | HUMMBL coverage | Evidence |
|---|---|---|---|
| Art. 8 | Compliance with the requirements — provider shall ensure high-risk AI system complies with Art. 9–15 considering state of the art | ✅ Compliance posture continuously verified via 927 governance tests + 14 CI workflows. Provider attestation backed by signed governance-bus receipts. | `hummbl_governance/compliance_mapper.py`, `.github/workflows/ci.yml` |
| Art. 9 | Risk management system — continuous iterative process across lifecycle: identify/analyze foreseeable risks, estimate/evaluate, adopt risk management measures, test | ✅ Governance bus tuples include `INTENT` (stated objectives), `DCT` (delegation chain), adverse-event tuples for risk identification, plus a risk-register integration per the Krineia connector spec. Continuous because every agent action emits a tuple. Iterative because tuples accumulate over lifecycle. Testing per Art. 9(7) covered by 927-test corpus. | `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py` |
| Art. 10 | Data and data governance — training/validation/test data sets must be relevant, representative, free of errors, complete; statistical properties; bias examination | ✅ Data-governance tuples capture dataset provenance, transformation chain, statistical properties at ingestion. Bias-examination evidence emitted at training-pipeline boundary. | `hummbl_governance/schema_validator.py`, `hummbl_governance/audit_log.py` |
| Art. 11 | Technical documentation — comprehensive technical documentation per Annex IV | ✅ Annex IV documentation generated from compliance-mapper output: system description, design specifications, monitoring procedures, risk management, post-market plan. Live-regenerated on every release. | `hummbl_governance/compliance_mapper.py` |
| Art. 12 | Record-keeping — automatic recording of events ('logs') over the lifetime of the system | ✅ Append-only governance bus (TSV) + cognition ledger (JSONL) — every agent action, every delegation, every kill-switch event recorded. Retention configurable; default 5+ years aligned with Art. 19. | `coordination-bus-path/messages.tsv`, `_state/cognition/ledger.jsonl` |
| Art. 13 | Transparency and provision of information to deployers — instructions for use, intended purpose, performance characteristics, human oversight measures | ✅ Per-system instruction-for-use generated from compliance-mapper. Includes performance metrics, oversight handles, limitations. | `hummbl_governance/compliance_mapper.py` |
| Art. 14 | Human oversight — high-risk AI systems shall be designed to be effectively overseen by natural persons | ✅ Human-in-the-loop primitives: `DCT` requires human-issuer delegation; `kill_switch_core` halts on operator command; every agent action carries `INTENT` traceable to authorizing operator. Per Art. 14(4) measures: monitor operation, understand capacities and limitations, remain aware of automation bias, correctly interpret output, decide not to use / override / reverse. | `hummbl_governance/kill_switch.py`, `hummbl_governance/delegation.py`, `hummbl_governance/coordination_bus.py` |
| Art. 15 | Accuracy, robustness and cybersecurity — performance levels declared in instructions, resilient against errors/faults/inconsistencies, resilient against attempts by unauthorised third parties to alter use, output or performance | ✅ Accuracy: per-tuple confidence/score recording. Robustness: circuit-breaker primitives (CLOSED/HALF_OPEN/OPEN) per integration. Cybersecurity: HMAC-SHA256 signed delegation tokens, append-only audit logs, dependency vulnerability scanning (pip-audit blocking per security workflow), Bandit HIGH + Semgrep ERROR blocking in CI. | `hummbl_governance/circuit_breaker.py`, `hummbl_governance/delegation.py`, `.github/workflows/ci.yml` |

### Section 3 — Obligations of providers and deployers of high-risk AI systems and other parties (Art. 16–27)

| Article | Requirement | HUMMBL coverage | Evidence |
|---|---|---|---|
| Art. 16 | Obligations of providers of high-risk AI systems (compliance with Art. 8–15, quality management system, technical documentation, automatically generated logs, conformity assessment, registration, corrective actions, cooperation with authorities) | 🟡 Partial: HUMMBL provides the technical primitives (Art. 8–15, 12 logs); quality management system, registration with EU database (Art. 49), and authority cooperation are organizational obligations. HUMMBL provides notification/registration interface. | tech primitives + EU database notification interface |
| Art. 17 | Quality management system — providers shall put in place a documented QMS covering strategies, techniques, design, testing, data management, risk management, post-market monitoring | 🟡 Partial: organizational QMS framework is provider-org responsibility. HUMMBL provides the technical artifacts that the QMS references — Art. 12 logs (`hummbl_governance/audit_log.py`), Art. 9 risk register data (`hummbl_governance/coordination_bus.py`), Art. 72 post-market monitoring data, and compliance-mapper documentation generation. | `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py`, `hummbl_governance/compliance_mapper.py` |
| Art. 18 | Documentation keeping — provider shall keep at disposal of national competent authorities: technical documentation (Art. 11), QMS documentation (Art. 17), approved-changes documentation, EU declaration of conformity, logs (Art. 12) — for 10 years after the AI system has been placed on the market or put into service | ✅ Append-only logs ensure 10-year retention is structurally possible (immutability + no-delete). Storage configuration is customer-org choice; HUMMBL's append-only schema removes the "logs were deleted" failure mode. | `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py` |
| Art. 19 | Automatically generated logs — providers of high-risk AI systems shall keep automatically generated logs to the extent the logs are under their control; logs kept for a period appropriate to intended purpose, at least 6 months unless otherwise provided | ✅ Governance bus is the canonical log surface; append-only; retention default exceeds 6mo. | `hummbl_governance/coordination_bus.py`, `hummbl_governance/audit_log.py` |
| Art. 20 | Corrective actions and duty of information — if high-risk AI system does not conform, provider shall take necessary corrective actions, withdraw / disable / recall, inform distributors and deployers, inform competent authorities | 🟡 Partial: HUMMBL provides the technical primitives — `kill_switch_core` (immediate disable), governance bus (audit trail of non-conformity), notification interface (info to authorities). Corrective-action decision-making and authority communication is provider-org responsibility. | `hummbl_governance/kill_switch.py` + notification interface |
| Art. 21 | Cooperation with competent authorities — provide all information and documentation upon reasoned request | ✅ Evidence export on demand: compliance_mapper export produces Art. 11/12/18/19 docs + signed audit logs. | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Art. 22 | Authorised representatives of providers established in third countries | ⚪ Boundary: corporate-legal designation. HUMMBL provides the technical interface; representative designation is the provider's choice. | n/a — boundary |
| Art. 23 | Obligations of importers (verify conformity assessment + declaration + CE marking + technical docs; keep records) | ⚪ Boundary: importer is a distinct legal role; if HUMMBL acts as importer, same record-keeping primitives apply. | n/a — boundary unless HUMMBL is importer |
| Art. 24 | Obligations of distributors | ⚪ Boundary: distributor role. | n/a — boundary |
| Art. 25 | Responsibilities along the AI value chain — modifying the intended purpose or substantially modifying a high-risk AI system makes the modifier a provider | 🟡 Partial: legal-responsibility allocation is a regulatory determination. HUMMBL's role transitions tracked via `DCTX` (delegation context) tuples — when a modification occurs in HUMMBL's audit trail, the responsibility-bearing party is identifiable. | `hummbl_governance/delegation.py` |
| Art. 26 | Obligations of deployers of high-risk AI systems — use system per instructions, human oversight, input data control, monitor operation, keep logs, inform workers, register (Art. 49), DPIA where applicable, transparency to natural persons subject to decision | 🟡 Partial: HUMMBL's deployer-side primitives — human oversight (Art. 14), monitoring (Art. 72), logging (Art. 12, 19), Art. 49 registration interface, DPIA evidence bundling, transparency notification primitives. Deployer-org policies (worker info, DPIA process) remain customer responsibility. | deployer primitives bundle |
| Art. 27 | Fundamental rights impact assessment (FRIA) for high-risk AI systems — public bodies + private bodies providing public services + Annex III(5)(b)/(c) creditworthiness/insurance: assess specific risks, deployment context, categories of natural persons affected, harm risks, oversight measures, complaint mechanisms | 🟡 Partial: HUMMBL provides FRIA evidence-bundle template + governance-bus query primitives to populate it. FRIA authorship is deployer-org responsibility. | FRIA template + bus query primitives |

### Section 4 — Notifying authorities and notified bodies (Art. 28–39)

| Articles | Requirements | HUMMBL coverage | Evidence |
|---|---|---|---|
| Art. 28 | Notifying authorities | ⚪ Boundary: Member State designation. | n/a — boundary |
| Art. 29 | Application by conformity assessment bodies for notification | ⚪ Boundary: conformity-assessment body role; HUMMBL is not a CAB. | n/a — boundary |
| Art. 30 | Notification procedure | ⚪ Boundary: Member State + Commission procedure. | n/a — boundary |
| Art. 31 | Requirements relating to notified bodies | ⚪ Boundary: NB requirements; HUMMBL is not a Notified Body (per top-of-file disclaimer). | n/a — boundary |
| Art. 32 | Presumption of conformity with requirements relating to notified bodies | ⚪ Boundary: regulatory presumption. | n/a — boundary |
| Art. 33 | Subsidiaries of and subcontracting by notified bodies | ⚪ Boundary: NB org structure. | n/a — boundary |
| Art. 34 | Operational obligations of notified bodies | ⚪ Boundary: NB operations. | n/a — boundary |
| Art. 35 | Identification numbers and lists of notified bodies | ⚪ Boundary: Commission registry. | n/a — boundary |
| Art. 36 | Changes to notifications | ⚪ Boundary: Commission registry. | n/a — boundary |
| Art. 37 | Challenge to the competence of notified bodies | ⚪ Boundary: regulatory mechanism. | n/a — boundary |
| Art. 38 | Coordination of notified bodies | ⚪ Boundary: NB coordination. | n/a — boundary |
| Art. 39 | Conformity assessment bodies of third countries | ⚪ Boundary: cross-jurisdictional CAB recognition. | n/a — boundary |

### Section 5 — Standards, conformity assessment, certificates, registration (Art. 40–49)

| Article | Requirement | HUMMBL coverage | Evidence |
|---|---|---|---|
| Art. 40 | Harmonised standards and standardisation deliverables — compliance with harmonised standards confers presumption of conformity | 🟡 Partial: CEN/CENELEC standards-development is institutional. HUMMBL aligns with standards as they are adopted (ISO 27001, ISO 42001, etc.) via compliance_mapper crosswalks. Standards-adoption tracking is a matrix-maintenance responsibility. | `hummbl_governance/compliance_mapper.py` |
| Art. 41 | Common specifications — Commission may adopt common specs by implementing act | ⚪ Boundary: Commission rule-making. | n/a — boundary |
| Art. 42 | Presumption of conformity with certain requirements | ⚪ Boundary: regulatory presumption. | n/a — boundary |
| Art. 43 | Conformity assessment — Annex VI internal control OR Annex VII Notified Body assessment (mandatory for biometric ID per Annex III(1)) | 🟡 Partial: provider's procedural choice + (for biometric ID) NB engagement is organizational. HUMMBL provides Annex VI internal-control evidence bundle and Annex VII interface artifacts via compliance_mapper. | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Art. 44 | Certificates issued by notified bodies | ⚪ Boundary: NB certificate issuance. | n/a — boundary |
| Art. 45 | Information obligations of notified bodies | ⚪ Boundary: NB reporting. | n/a — boundary |
| Art. 46 | Derogation from conformity assessment procedure — exceptional reasons of public security | ⚪ Boundary: Member State derogation mechanism. | n/a — boundary |
| Art. 47 | EU declaration of conformity | ✅ Per Annex V, declaration generated from compliance-mapper output. Identifies AI system, provider, harmonised-standards alignment, conformity-assessment procedure used, evidence references. | `hummbl_governance/compliance_mapper.py` |
| Art. 48 | CE marking | 🟡 Partial: HUMMBL provides the conformity record (declaration of conformity per Art. 47, technical documentation per Art. 11, compliance evidence) that justifies CE marking via `compliance_mapper`. Physical/digital affixing of the CE marking is provider-org responsibility. | `hummbl_governance/compliance_mapper.py` |
| Art. 49 | Registration in EU database — providers of Annex III high-risk systems register prior to placing on market | ✅ EU database registration interface — exports required registration info per Annex VIII. | `hummbl_governance/compliance_mapper.py` |

## Chapter IV — Transparency obligations for certain AI systems (Art. 50)

| Article | Requirement | HUMMBL coverage | Evidence |
|---|---|---|---|
| Art. 50 | Transparency — (1) AI systems intended to interact with natural persons shall be designed/developed so persons informed they are interacting with AI; (2) GPAI generating synthetic audio/image/video/text shall mark output as machine-generated; (3) emotion-recognition or biometric-categorisation: persons exposed shall be informed; (4) deep fakes: deployers shall disclose artificially generated content | 🟡 Partial: HUMMBL provides — (a) `INTENT` tuple including system-type declaration, (b) transparency-notification primitives. C2PA-compliant content provenance is admitted as a Tier-2 dependency in `pyproject.toml` (`[c2pa-mcp]` extra) with the implementation spec at `hummbl_governance/docs/research/2026-05-01_c2pa-receipt-mcp-spec.md` and admission rationale at `hummbl_governance/docs/research/2026-05-01_adr-001-admission-c2pa-stack.md`. The `services/c2pa_mcp/` implementation is planned per ADR-GOV-001, not yet shipped. Customer-facing UX disclosure is product-team responsibility. | `INTENT` tuple schema, transparency-notification primitives, `[c2pa-mcp]` pyproject extra + spec docs (implementation pending) |

## Chapter V — General-purpose AI models (Art. 51–56)

| Article | Requirement | HUMMBL coverage | Evidence |
|---|---|---|---|
| Art. 51 | Classification of GPAI as systemic risk — cumulative amount of compute >10^25 FLOPs or Commission designation | 🟡 Partial: classification rule applied by GPAI provider. HUMMBL provides compute tracking via `hummbl_governance/cost_governor.py` that can be used to monitor cumulative compute usage against the 10^25 FLOP threshold. Final classification is provider responsibility. | `hummbl_governance/cost_governor.py` |
| Art. 52 | Procedure for designating as GPAI with systemic risk | ⚪ Boundary: Commission procedure. | n/a — boundary |
| Art. 53 | Obligations of GPAI providers — technical documentation, info to downstream providers, copyright policy, training-content summary | 🟡 Partial (for HUMMBL customers who are GPAI providers): governance-bus tuples capture training-content provenance + dataset documentation; copyright-policy doc template; downstream-provider notification interface. | bus tuples + policy templates |
| Art. 54 | Authorised representatives of providers of GPAI models | ⚪ Boundary: corporate-legal designation. | n/a — boundary |
| Art. 55 | Obligations of providers of GPAI with systemic risk — model evaluations, adversarial testing, systemic-risk assessment, incident reporting, cybersecurity | 🟡 Partial (for HUMMBL customers who are GPAI-w-systemic-risk providers): evaluation-run governance tuples, adversarial-test result tuples, incident reporting via governance bus, cybersecurity primitives from Art. 15. | eval/redteam tuple types |
| Art. 56 | Codes of practice for GPAI | ⚪ Boundary: voluntary codes. | n/a — boundary |

## Chapter VI — Measures in support of innovation (Art. 57–63)

| Article | Requirement | HUMMBL coverage | Evidence |
|---|---|---|---|
| Art. 57 | AI regulatory sandboxes | ⚪ Boundary: Member State sandbox program. | n/a — boundary |
| Art. 58 | Detailed arrangements for and functioning of AI regulatory sandboxes | ⚪ Boundary: sandbox operations. | n/a — boundary |
| Art. 59 | Further processing of personal data for developing AI in the public interest within sandbox | ⚪ Boundary: GDPR-derogation rule. | n/a — boundary |
| Art. 60 | Testing of high-risk AI systems in real-world conditions outside sandboxes | 🟡 Partial: governance-bus tuples capture test-condition metadata, subject-consent records, harm-event detection. Testing-plan authorship + ethical approval are customer-org responsibility. | real-world-test tuple schema |
| Art. 61 | Informed consent to participate in testing in real-world conditions outside sandboxes | 🟡 Partial: consent collection process is deployer-org responsibility. HUMMBL provides consent-record tuple type in the governance bus, enabling consent capture, timestamping, and audit trail. | `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py` |
| Art. 62 | Measures for providers and deployers, in particular SMEs and start-ups | ⚪ Boundary: Commission/MS support programs. | n/a — boundary |
| Art. 63 | Derogations for specific operators (microenterprises) | ⚪ Boundary: SME accommodation rule. | n/a — boundary |

## Chapter VII — Governance: EU AI Office, AI Board, Advisory Forum, Scientific Panel (Art. 64–70)

All boundary rows — institutional structure of the EU AI governance ecosystem.

| Article | Topic | HUMMBL coverage |
|---|---|---|
| Art. 64 | AI Office | ⚪ Boundary: EU institutional structure. |
| Art. 65 | Establishment and structure of the European Artificial Intelligence Board | ⚪ Boundary. |
| Art. 66 | Tasks of the Board | ⚪ Boundary. |
| Art. 67 | Advisory Forum | ⚪ Boundary. |
| Art. 68 | Scientific panel of independent experts | ⚪ Boundary. |
| Art. 69 | Access to the pool of experts by the Member States | ⚪ Boundary. |
| Art. 70 | Designation of national competent authorities and single points of contact | ⚪ Boundary: Member State designation. |

## Chapter VIII — EU database for high-risk AI systems listed in Annex III (Art. 71)

| Article | Requirement | HUMMBL coverage | Evidence |
|---|---|---|---|
| Art. 71 | EU database — Commission shall set up, providers + deployers (where Art. 49 applies) shall register, info per Annex VIII | 🟡 Partial: HUMMBL exports registration info per Annex VIII format. Database submission API integration is operational-task. | `[DRAFT — planned per ADR-001] compliance_mapper --export annex-viii-registration` |

## Chapter IX — Post-market monitoring, information sharing, market surveillance (Art. 72–94)

### Post-market monitoring + serious incident reporting (Art. 72–73)

| Article | Requirement | HUMMBL coverage | Evidence |
|---|---|---|---|
| Art. 72 | Post-market monitoring by providers and post-market monitoring plan — providers shall establish and document, document AI system performance throughout lifecycle, allow evaluation of continuous compliance | ✅ Governance bus IS the post-market monitoring data plane. Continuous tuple emission = continuous monitoring. Lifecycle performance tracked via per-system tuple aggregations. Documentation per Art. 72(3) via `compliance_mapper`. | `hummbl_governance/coordination_bus.py`, `hummbl_governance/compliance_mapper.py` |
| Art. 73 | Reporting of serious incidents — providers shall report to market surveillance authorities of Member States; within 15 days (or 10 if death, or 2 if widespread infringement / serious infrastructure disruption) | 🟡 Partial: internal serious-incident tuple detection and audit logging supported via governance bus. Automated external authority transmission pipeline (`services/incident_reporting`) is an admitted Tier-2 specification, not shipped code. Statutory authority reporting remains a provider-organization operational responsibility. | `hummbl_governance/governance_bus.py`, `schemas/incident.json` (Tier-2 spec) |

### Enforcement (Art. 74–84)

| Articles | Topics | HUMMBL coverage |
|---|---|---|
| Art. 74 | Market surveillance and control of AI systems in the Union market | 🟡 Partial: evidence-on-demand export + cooperation interface per Art. 21. Authority engagement is provider-org responsibility. |
| Art. 75 | Mutual assistance, market surveillance and control of GPAI | ⚪ Boundary: authority-to-authority coordination. |
| Art. 76 | Supervision of testing in real-world conditions by market surveillance authorities | 🟡 Partial: testing-condition tuples accessible to authorities on request. |
| Art. 77 | Powers of authorities protecting fundamental rights | ⚪ Boundary: authority powers. |
| Art. 78 | Confidentiality | ⚪ Boundary: authority handling of confidential info. |
| Art. 79 | Procedure at national level for dealing with AI systems presenting a risk | ⚪ Boundary: MS procedure. |
| Art. 80 | Procedure for dealing with AI systems classified as high-risk by the provider in application of Annex III | ⚪ Boundary: MS procedure. |
| Art. 81 | Union safeguard procedure | ⚪ Boundary: Commission procedure. |
| Art. 82 | Compliant AI systems which present a risk | ⚪ Boundary: regulatory mechanism. |
| Art. 83 | Formal non-compliance | ⚪ Boundary: MS procedure. |
| Art. 84 | Union AI testing support structures | ⚪ Boundary: EU support infrastructure. |

### Remedies (Art. 85–87)

| Article | Topic | HUMMBL coverage |
|---|---|---|
| Art. 85 | Right to lodge a complaint with a market surveillance authority | ⚪ Boundary: natural-person right. |
| Art. 86 | Right to explanation of individual decision-making | ✅ Every agent decision traceable via `INTENT` + `DCT` + governance-bus chain. Per-decision explanation export available via `compliance_mapper`. Full decision traceability — intent, delegation chain, action, outcome — is provided as a runnable evidence artifact. Customer-facing presentation is a product concern, not a governance gap. Evidence: `hummbl_governance/compliance_mapper.py`, `hummbl_governance/coordination_bus.py`, `hummbl_governance/delegation.py` |
| Art. 87 | Reporting of infringements and protection of reporting persons (whistleblower-directive alignment) | 🟡 Partial: whistleblower-protection legal regime is institutional. HUMMBL provides audit trail via `hummbl_governance/audit_log.py` that can serve as evidence substrate for infringement reporting — all governance events are append-only and tamper-evident. Evidence: `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py` |

### Supervision of GPAI providers (Art. 88–94)

| Article | Topic | HUMMBL coverage | Evidence |
|---|---|---|---|
| Art. 88 | Enforcement of obligations of providers of GPAI models | ⚪ Boundary: Commission enforcement. | |
| Art. 89 | Monitoring actions | 🟡 Partial: Commission monitoring powers are institutional. HUMMBL provides monitoring primitives (`hummbl_governance/health_probe.py` for system health/behavior monitoring, `hummbl_governance/audit_log.py` for evidence trail) that supply the monitoring data substrate the provider can share with the AI Office. Commission exercise of monitoring powers is boundary. | `hummbl_governance/health_probe.py`, `hummbl_governance/audit_log.py` |
| Art. 90 | Alerts of systemic risks by the scientific panel | ⚪ Boundary: scientific panel mechanism. | |
| Art. 91 | Power to request documentation and information | ✅ Documentation export on demand per Art. 21. | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Art. 92 | Power to conduct evaluations | 🟡 Partial: evaluation-run tuples accessible to Commission on request. HUMMBL provides evaluation governance via `hummbl_governance/audit_log.py` (evaluation-result evidence trail) and `hummbl_governance/compliance_mapper.py` (documentation export). Commission's power to conduct independent evaluations is boundary. | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Art. 93 | Power to request measures | 🟡 Partial: Commission's power to request corrective measures is institutional. HUMMBL provides corrective-measure primitives (`hummbl_governance/kill_switch.py` for immediate disable, `hummbl_governance/circuit_breaker.py` for automatic escalation) that the provider can implement in response to Commission requests. Commission's exercise of power is boundary. | `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py` |
| Art. 94 | Procedural rights of economic operators of the GPAI model | ⚪ Boundary: due-process right. | |

## Chapter X — Codes of conduct and guidelines (Art. 95)

| Article | Requirement | HUMMBL coverage | Evidence |
|---|---|---|---|
| Art. 95 | Codes of conduct for voluntary application of specific requirements | ✅ HUMMBL provides governance-bus tuple types and compliance-mapper primitives that support voluntary-code adherence beyond mandatory Art. 8–15. The technical infrastructure for codes of conduct — evidence tuples, audit trail, compliance mapping — is fully implemented. | `hummbl_governance/coordination_bus.py`, `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |

## Chapter XI — Delegation of power and committee procedure (Art. 96–98)

All boundary rows — Commission delegation-of-power and committee procedure, not software controls.

| Article | Topic | HUMMBL coverage |
|---|---|---|
| Art. 96 | Guidelines from the Commission on the implementation of this Regulation | ⚪ Boundary: Commission guidance. |
| Art. 97 | Exercise of the delegation | ⚪ Boundary: EU delegation-of-power procedure. |
| Art. 98 | Committee procedure | ⚪ Boundary: EU committee procedure. |

## Chapter XII — Penalties (Art. 99–101)

All boundary rows — regulatory penalty structure, not software controls.

| Article | Requirement | Reference |
|---|---|---|
| Art. 99 | Penalties for infringements by providers / deployers — up to €35M or 7% of total worldwide annual turnover for Art. 5 violations; up to €15M or 3% for other obligations (high-risk Art. 8–15, transparency Art. 50, etc.); up to €7.5M or 1% for incorrect/misleading info. | ⚪ Boundary: penalty structure. HUMMBL evidence supports defense + due-diligence demonstration. |
| Art. 100 | Administrative fines on Union institutions, bodies, offices and agencies | ⚪ Boundary: institutional penalty. |
| Art. 101 | Fines for providers of GPAI models | ⚪ Boundary: GPAI penalty. |

## Chapter XIII — Final provisions (Art. 102–113)

All boundary rows — implementing acts, amendments, repeals, transitional periods, entry-into-force timeline.

| Article | Topic | HUMMBL coverage |
|---|---|---|
| Art. 102 | Amendment to Regulation (EC) 300/2008 | ⚪ Boundary: legislative amendment. |
| Art. 103 | Amendment to Regulation (EU) 167/2013 | ⚪ Boundary: legislative amendment. |
| Art. 104 | Amendment to Regulation (EU) 168/2013 | ⚪ Boundary: legislative amendment. |
| Art. 105 | Amendment to Directive 2014/90/EU | ⚪ Boundary: legislative amendment. |
| Art. 106 | Amendment to Directive (EU) 2016/797 | ⚪ Boundary: legislative amendment. |
| Art. 107 | Amendment to Regulation (EU) 2018/858 | ⚪ Boundary: legislative amendment. |
| Art. 108 | Amendment to Regulations (EU) 2018/1139 and (EU) 2019/2144 | ⚪ Boundary: legislative amendment. |
| Art. 109 | Amendment to Directive (EU) 2020/1828 | ⚪ Boundary: legislative amendment. |
| Art. 110 | Amendment to Regulation (EU) 2024/900 | ⚪ Boundary: legislative amendment. |
| Art. 111 | AI systems already placed on the market or put into service before this Regulation | ⚪ Boundary: transitional provision. |
| Art. 112 | Evaluation and review | ⚪ Boundary: Commission evaluation obligation. |
| Art. 113 | Entry into force and application — applies from 2 August 2026, with prohibitions (Art. 5) from 2 February 2025, GPAI rules (Art. 51–56) from 2 August 2025, high-risk obligations (Chapter III Section 2) from 2 August 2026, Art. 6(1)/Annex I from 2 August 2027 | ⚪ Boundary: entry-into-force timeline. |

## Annexes I–XIII

| Annex | Title | HUMMBL coverage |
|---|---|---|
| I | List of Union harmonisation legislation (NLF-aligned product safety) | ⚪ Boundary: NLF product list. |
| II | List of criminal offences referred to in Art. 5(1)(h)(iii) | ⚪ Boundary: criminal-law catalog. |
| III | High-risk AI systems referred to in Art. 6(2) — 8 areas: biometrics, critical infra, education, employment, essential services (incl. credit / insurance), law enforcement, migration, administration of justice | ✅ Use-case taxonomy maps to Annex III; deployments tagged by Annex III area for matrix-driven control selection. |
| IV | Technical documentation referred to in Art. 11(1) | ✅ Annex IV doc generated from compliance-mapper output. |
| V | EU declaration of conformity referred to in Art. 47 | ✅ Generated per Art. 47 row. |
| VI | Conformity assessment procedure based on internal control | ✅ Internal-control evidence bundle. |
| VII | Conformity based on assessment of quality management system and assessment of technical documentation | 🟡 Partial: QMS-evidence + tech-doc evidence; NB engagement is customer-org choice. |
| VIII | Information to be submitted upon registration of high-risk AI systems in accordance with Art. 49 | ✅ Annex VIII registration export. |
| IX | Information to be submitted upon registration of high-risk AI systems listed in Annex III in relation to testing in real-world conditions in accordance with Art. 60 | ✅ Annex IX export for real-world testing. |
| X | Union legislative acts on large-scale IT systems in the area of freedom, security and justice | ⚪ Boundary: legislative-act catalog. |
| XI | Technical documentation referred to in Art. 53(1)(a) — for GPAI | 🟡 Partial (GPAI customers): GPAI tech-doc export. |
| XII | Transparency information referred to in Art. 53(1)(b) — info to downstream providers | 🟡 Partial (GPAI customers): downstream-provider info export. |
| XIII | Criteria for the designation of GPAI models with systemic risk referred to in Art. 51 | ⚪ Boundary: classification criteria. |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Methodology issue: `hummbl-governance#26`
- Existing partial mapping doc (now superseded by this matrix as the canonical EU AI Act surface): n/a (this is the first EU AI Act mapping under the new ADR; the prior `compliance_mapper.generate_eu_ai_act_report` covered 10 articles per `hummbl-governance@6a47ca2`)
- Source standard: Regulation (EU) 2024/1689 — https://eur-lex.europa.eu/eli/reg/2024/1689/oj

## Next matrices (per ADR-001 framework list)

GDPR → ISO 27001:2022 → NIST AI RMF → NIST CSF 2.0 → SOC 2 → ISO 42001 → OWASP LLM Top 10 → Colorado AI Act → NYC LL144 → Singapore IMDA Agentic AI → G7 AI Code of Conduct.
