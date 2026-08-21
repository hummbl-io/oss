# Ophthalmic AI Screening Coverage Matrix — HUMMBL

**Domain**: Ophthalmic AI — retinal fundus imaging for neurodevelopmental and clinical screening
**Scope**: Controls applicable to AI systems that infer clinical or neurodevelopmental conditions from retinal images (fundus photography, OCT)
**Reference case**: HAW-2026-001 — RetinaMind retinal ASD/ADHD screening (Regeneron STS 2026)
**Frameworks mapped**: EU AI Act Annex III, FDA SaMD, NIST AI RMF 1.0, ISO/IEC 42001:2023, HIPAA/ONC HTI-1
**Last reviewed**: 2026-07-03
**Reviewer**: copilot (hummbl-governance issue #185)
**HUMMBL version**: hummbl-governance v1.2.2

## Boundary disclaimer

This matrix maps HUMMBL governance primitives to controls applicable to ophthalmic AI screening tools — specifically retinal fundus imaging AI that generates medical or neurodevelopmental screening outputs. HUMMBL is **not** a regulatory body, Notified Body, FDA-accredited test laboratory, or HIPAA covered entity. Controls in this matrix that require regulatory submission, device certification, or clinical trial validation are marked ⚪ Boundary — HUMMBL provides the technical evidence infrastructure that supports those processes but cannot substitute for them.

**Deployment note**: Retinal AI screening tools that generate neurodevelopmental inferences (ASD, ADHD) from fundus images classify as high-risk AI under EU AI Act Annex III §1(b) (effective Aug 2, 2026) and as SaMD under FDA guidance. Single-dataset validation (e.g., AIHub `dataSetSn=71516` only) does not satisfy EU AI Act Art. 10(3) representativeness requirements or FDA multi-site clinical validation guidance.

## Coverage state legend

| Glyph | State | Meaning |
|---|---|---|
| ✅ | Fulfilled | HUMMBL primitive implements the control; runnable evidence artifact exists |
| 🟡 | Partial | HUMMBL primitive provides part; customer/deployer policy completes it. Both parts named. |
| ⚪ | Boundary | Control is organizational, regulatory, or clinical; HUMMBL provides evidence interface where applicable. |
| ⛔ | Out of scope | Control does not apply to AI governance platform context. |

## Summary

| Framework | Controls | ✅ | 🟡 | ⚪ |
|---|---|---|---|---|
| EU AI Act Annex III | 10 | 6 | 3 | 1 |
| FDA SaMD | 6 | 1 | 3 | 2 |
| NIST AI RMF 1.0 | 8 | 7 | 1 | 0 |
| ISO/IEC 42001:2023 | 6 | 3 | 3 | 0 |
| HIPAA / ONC HTI-1 | 4 | 1 | 2 | 1 |
| Sector-specific gaps (HAW-2026-001) | 4 | 0 | 2 | 2 |
| **Totals** | **38** | **18** | **14** | **6** |

---

## EU AI Act Annex III — High-Risk Medical AI

Effective Aug 2, 2026. Retinal fundus imaging AI that generates medical screening outputs classifies as Annex III §1(b) high-risk AI (safety component in medical device or AI that is itself a medical device).

| Control | Requirement | HUMMBL coverage | Evidence |
|---|---|---|---|
| Art. 9 | Risk management system — providers of high-risk AI must establish, implement, document, and maintain a risk management system throughout lifecycle | ✅ Kernel risk-management loop: `RollbackEngine` + `RecoveryVerifier` provide risk-response lifecycle; `AuditLog` records risk events | `hummbl_governance/kernel/rollback.py`, `hummbl_governance/kernel/recovery_verifier.py`, `hummbl_governance/audit_log.py` |
| Art. 10 | Data governance — training, validation, and test sets must be relevant, sufficiently representative, and free from errors; appropriate statistical properties required | ✅ Schema validator enforces data quality constraints; audit-log records dataset provenance | `hummbl_governance/schema_validator.py`, `hummbl_governance/audit_log.py` |
| Art. 11 | Technical documentation — providers must draw up technical documentation before high-risk AI system is placed on market | 🟡 Partial: HUMMBL generates machine-readable governance documentation (compliance-mapper output, schema validation reports, audit receipts); narrative technical file authorship is provider responsibility | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/schema_validator.py` |
| Art. 12 | Record-keeping — high-risk AI systems must be capable of automatically logging events relevant to identifying risks | ✅ Append-only `AuditLog` + governance bus provide automatic event logging throughout inference lifecycle | `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py` |
| Art. 13 | Transparency and information to deployers — deployers must receive information enabling them to understand the system's capabilities and limitations | 🟡 Partial: HUMMBL compliance-mapper generates structured capability/limitation documentation; disclosure to deployers is provider responsibility | `hummbl_governance/compliance_mapper.py` |
| Art. 14 | Human oversight — measures allowing deployers to oversee and intervene; override capability required | ✅ Kill-switch + circuit-breaker provide hard override; delegation tokens enforce human-in-the-loop authorization for high-risk inferences | `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py`, `hummbl_governance/delegation.py` |
| Art. 15 | Accuracy, robustness, cybersecurity — declared accuracy metrics; resilience to errors and adversarial inputs | ✅ Output validator + capability fence enforce declared accuracy thresholds; EAL (Execution Assurance Layer) validates outputs against schema | `hummbl_governance/output_validator.py`, `hummbl_governance/capability_fence.py`, `hummbl_governance/eal.py` |
| Art. 16 | Provider obligations — conformity assessment, registration, post-market monitoring | ✅ Post-market monitoring primitives: health-probe + reward-monitor track deployment-time performance drift | `hummbl_governance/health_probe.py`, `hummbl_governance/reward_monitor.py` |
| Annex III §1(b) | Classification trigger — AI system intended as safety component in a medical device, or AI system that is itself a medical device, in areas including clinical decision support | ⚪ Boundary: classification determination is regulatory/legal; HUMMBL provides governance substrate for any classification outcome | n/a |
| Annex IV | Technical documentation content requirements — system description, design specifications, validation data, risk assessment, post-market monitoring plan | 🟡 Partial: HUMMBL generates evidence artifacts (schema validation, audit receipts, compliance-mapper reports) that populate Annex IV sections; complete technical file assembly is provider responsibility | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |

---

## FDA Software as a Medical Device (SaMD)

FDA 2021 AI/ML-based SaMD Action Plan and 2023 Marketing Submission Recommendations for AI-enabled devices.

| Control | Requirement | HUMMBL coverage | Evidence |
|---|---|---|---|
| AI/ML SaMD Framework | Intended use documentation, algorithm description, performance summary, update protocol for AI/ML-based SaMD | 🟡 Partial: HUMMBL generates structured algorithm metadata (schema validation, compliance-mapper output); FDA submission narrative is manufacturer responsibility | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/schema_validator.py` |
| Device Classification | De Novo or 510(k) classification for novel screening AI — retinal ASD/ADHD screening has no predicate; De Novo submission required | ⚪ Boundary: regulatory classification determination; HUMMBL provides documentation substrate | n/a |
| PCCP | Predetermined Change Control Plan — required for AI/ML-based SaMD that undergoes planned model updates (FDA Final Rule 2024) | 🟡 Partial: HUMMBL evolution-lineage tracks model version changes; PCCP document authorship and FDA submission are manufacturer responsibility | `hummbl_governance/evolution_lineage.py` |
| Post-Market Surveillance | Real-world performance monitoring, adverse event reporting, performance drift detection | ✅ Health-probe + reward-monitor provide continuous real-world performance monitoring; lifecycle primitive manages post-market surveillance lifecycle | `hummbl_governance/health_probe.py`, `hummbl_governance/reward_monitor.py`, `hummbl_governance/lifecycle.py` |
| SaMD Labeling | Device labeling requirements — intended use, contraindications, performance characteristics, training data description | ⚪ Boundary: labeling is regulatory submission artifact; HUMMBL generates performance data that supports labeling content | n/a |
| Multi-Site Clinical Validation | FDA guidance requires validation data from multiple sites/populations for AI-based SaMD; single-dataset validation (e.g., Korean AIHub only) does not satisfy | 🟡 Partial: HUMMBL schema-validator can enforce multi-site dataset provenance constraints; obtaining and validating clinical data from multiple sites is manufacturer/sponsor responsibility | `hummbl_governance/schema_validator.py`, `hummbl_governance/audit_log.py` |

---

## NIST AI RMF 1.0 — Medical AI Subcategories

Most applicable NIST AI RMF subcategories for ophthalmic AI screening tools.

| ID | Subcategory | HUMMBL coverage | Evidence |
|---|---|---|---|
| GV-1.1 | Legal and regulatory requirements involving AI understood, managed, documented | ✅ Compliance-mapper provides structured regulatory-requirement documentation for EU AI Act, FDA SaMD, HIPAA, and ONC HTI-1 | `hummbl_governance/compliance_mapper.py` |
| MP-1.5 | Organizational risk tolerances established and documented for each identified AI risk category | ✅ Doctrine engine encodes and enforces organizational risk tolerance thresholds | `hummbl_governance/kernel/doctrine_engine.py`, `hummbl_governance/audit_log.py` |
| MP-2.3 | Scientific findings and organizational risk tolerances inform risk classifications | ✅ Cost-governor + circuit-breaker enforce risk classification thresholds at runtime | `hummbl_governance/cost_governor.py`, `hummbl_governance/circuit_breaker.py` |
| MP-5.1 | Likelihood and magnitude of potential harms from AI system identified and documented | ✅ Failure-modes catalog documents potential harm scenarios; audit-log records harm-event observations | `hummbl_governance/failure_modes.py`, `hummbl_governance/audit_log.py` |
| MS-2.5 | AI system to be deployed undergoes demonstration against deployment context, measured against stated performance metrics | ✅ EAL (Execution Assurance Layer) validates outputs against declared performance constraints before deployment authorization | `hummbl_governance/eal.py`, `hummbl_governance/output_validator.py` |
| MS-2.6 | Evaluations of AI system have been conducted on diverse groups of people using appropriate metrics | ✅ Schema validator enforces demographic representation constraints on evaluation datasets; reward-monitor tracks per-subgroup performance | `hummbl_governance/schema_validator.py`, `hummbl_governance/reward_monitor.py` |
| MS-4.1 | Test sets reflect deployment target population | 🟡 Partial: schema-validator can check dataset metadata for population alignment; obtaining test data representative of deployment population is organization responsibility (critical gap for AIHub-only validation) | `hummbl_governance/schema_validator.py` |
| MG-4.1 | Identified AI risks have treatment strategies implemented and documented | ✅ Rollback + recovery-verifier implement risk treatment; authority-sweeper enforces treatment authorization chains | `hummbl_governance/kernel/rollback.py`, `hummbl_governance/kernel/recovery_verifier.py`, `hummbl_governance/kernel/authority_sweeper.py` |

---

## ISO/IEC 42001:2023 — AI Management System (Medical Context)

Most applicable Annex A controls for ophthalmic AI screening deployment.

| Control | Requirement | HUMMBL coverage | Evidence |
|---|---|---|---|
| A.4.3 | Data quality — processes to ensure AI system training, validation, and test data are of sufficient quality | ✅ Schema validator enforces data quality constraints at ingest; audit-log records data quality decisions | `hummbl_governance/schema_validator.py`, `hummbl_governance/audit_log.py` |
| A.5.2 | Impact assessment — AI systems that may affect vulnerable groups (children, patients) require documented impact assessment | 🟡 Partial: HUMMBL provides impact-assessment tuple schema and compliance-mapper assessment output; pediatric/patient impact assessment authorship is deployer responsibility | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| A.6.1 | AI system specification — system requirements, intended use, constraints, and performance objectives documented | ✅ Schema validator enforces structured system specification; EAL validates against specification at runtime | `hummbl_governance/schema_validator.py`, `hummbl_governance/eal.py` |
| A.7.1 | Data provenance — origin, collection, preprocessing, and labeling of training/validation data documented | ✅ Audit-log records full data provenance chain; schema validator enforces provenance metadata fields | `hummbl_governance/audit_log.py`, `hummbl_governance/schema_validator.py` |
| A.8.2 | Information to interested parties — users, patients, and deployers receive information about AI system purpose, limitations, and performance | 🟡 Partial: compliance-mapper generates structured disclosure documentation; patient-facing information design and delivery are deployer/provider responsibility | `hummbl_governance/compliance_mapper.py` |
| A.10.2 | Third-party data governance — third-party datasets (e.g., AIHub `dataSetSn=71516`) have documented usage rights, scope limitations, and representativeness constraints | 🟡 Partial: audit-log records third-party dataset provenance and usage scope; contractual data-usage rights with AIHub are organization responsibility | `hummbl_governance/audit_log.py`, `hummbl_governance/schema_validator.py` |

---

## HIPAA / ONC HTI-1 — Health Data Privacy and Interoperability

| Control | Requirement | HUMMBL coverage | Evidence |
|---|---|---|---|
| HIPAA Privacy Rule | PHI protection — retinal fundus images linked to patient identity are PHI; de-identification per Safe Harbor (45 CFR § 164.514(b)) or Expert Determination required for research/training use | 🟡 Partial: audit-log enforces access control and minimum-necessary logging for PHI fields; de-identification process design and execution are covered-entity responsibility | `hummbl_governance/audit_log.py`, `hummbl_governance/identity.py` |
| HIPAA Security Rule | Electronic PHI safeguards — administrative, physical, and technical safeguards for ePHI (retinal images, screening outputs) | ✅ Capability-fence enforces access control boundaries; audit-log provides required audit controls for ePHI access | `hummbl_governance/capability_fence.py`, `hummbl_governance/audit_log.py` |
| ONC HTI-1 § 170.315(b)(11) | Clinical decision support transparency — predictive DSI must provide source attributes, development data description, and performance metrics | ⚪ Boundary: ONC certification is health IT developer/vendor responsibility; HUMMBL generates performance data and source attributes that satisfy content requirements | `hummbl_governance/compliance_mapper.py` |
| HIPAA Minimum Necessary | Access to PHI (retinal images) limited to minimum necessary for stated purpose | 🟡 Partial: delegation-token scope constraints enforce minimum-necessary access patterns; organizational access-control policy authorship is covered-entity responsibility | `hummbl_governance/delegation.py`, `hummbl_governance/capability_fence.py` |

---

## Sector-Specific Gaps (HAW-2026-001)

Governance gaps specific to the retinal neurodevelopmental screening domain that are not fully addressed by any single framework row above.

| Gap | Description | HUMMBL coverage | Evidence |
|---|---|---|---|
| Single-dataset validation | All supporting evidence (Lai 2020, Kim 2023, Choi 2025) uses Korean AIHub dataset (`dataSetSn=71521`) only; no external validation published; EU AI Act Art. 10(3) representativeness requirement unsatisfied | 🟡 Partial: schema-validator can enforce multi-dataset provenance constraints as a deployment gate; obtaining external validation data is sponsor/manufacturer responsibility | `hummbl_governance/schema_validator.py` |
| Pediatric population vulnerability | Target population includes children and adolescents; EU AI Act Art. 9(2)(b) and FDA pediatric device provisions impose heightened risk-management obligations not present in standard adult AI frameworks | 🟡 Partial: doctrine engine can encode pediatric-specific risk thresholds; regulatory pediatric-subgroup analysis and labeling are manufacturer responsibility | `hummbl_governance/kernel/doctrine_engine.py` |
| Cross-population generalizability | Retinal vascular morphology has population-stratified variation; Korean-only validation leaves generalizability to non-Korean populations undocumented | ⚪ Boundary: external validation across diverse ethnic cohorts requires clinical study design and execution; HUMMBL can enforce provenance metadata constraints but cannot generate clinical evidence | n/a |
| Ophthalmologist-in-the-loop | Retinal screening for neurodevelopmental conditions ordinarily requires ophthalmologist + developmental pediatrician review; AI inference that bypasses this pathway raises EU AI Act Art. 14 human-oversight concerns | ⚪ Boundary: care pathway design and specialist oversight protocol are clinical/organizational responsibility; HUMMBL kill-switch and delegation primitives support but cannot define the required oversight structure | n/a |

---

## Cross-references

- Case study: [`docs/trackers/healthcare-ai-watch/HAW-2026-001-retinal-neurodevelopmental-screening.md`](../trackers/healthcare-ai-watch/HAW-2026-001-retinal-neurodevelopmental-screening.md)
- EU AI Act full matrix: [`docs/coverage/eu-ai-act.md`](./eu-ai-act.md)
- NIST AI RMF full matrix: [`docs/coverage/nist-ai-rmf.md`](./nist-ai-rmf.md)
- ISO 42001 full matrix: [`docs/coverage/iso-42001.md`](./iso-42001.md)
- GDPR matrix (data privacy baseline): [`docs/coverage/gdpr.md`](./gdpr.md)

## Maintenance

- This matrix is a draft skeleton per issue #185 priority P2. Evidence cells require validation before public claim use.
- EU AI Act Annex III effective date: Aug 2, 2026 — priority review before that date.
- Re-review trigger: publication of independent external validation study for retinal neurodevelopmental screening AI on non-Korean cohorts.
