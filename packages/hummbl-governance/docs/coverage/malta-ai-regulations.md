# Malta AI Regulations Coverage Matrix — HUMMBL

**Standard**: Artificial Intelligence Regulations, 2025 (Legal Notice 226 of 2025) and Artificial Intelligence (Designation of the Information and Data Protection Commissioner for the purposes of Regulation (EU) 2024/1689) Regulations, 2025 (Legal Notice 227 of 2025)
**Effective**: 2 August 2026 (bulk of provisions align with EU AI Act application date); enacted 10 October 2025
**Source**: https://legislation.mt/eli/ln/2025/226/eng
**Last reviewed**: 2026-06-25
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not Maltese legal counsel and does not provide legal advice on LN 226/227 of 2025. The Regulations implement Regulation (EU) 2024/1689 (EU AI Act) into Maltese law, designating the Malta Digital Innovation Authority (MDIA) as the default market surveillance authority and Notifying Authority, and the Information and Data Protection Commissioner (IDPC) as market surveillance authority for specified data-sensitive high-risk AI systems. Statutory compliance is the customer-organization responsibility. HUMMBL maps technical primitives to the Regulations' conformity-assessment, risk-management, transparency, human-oversight, post-market-monitoring, and sandbox obligations.

## Scope summary

The Regulations apply to operators (providers, deployers, importers, distributors) of AI systems placed on the Maltese market or whose output is used in Malta, mirroring the EU AI Act's risk-based tiers (prohibited, high-risk, limited-transparency, minimal-risk). LN 226 designates MDIA as default Market Surveillance Authority, Notifying Authority for conformity assessment bodies, single point of contact, and operator of the national AI regulatory sandbox. LN 227 designates IDPC as Market Surveillance Authority for high-risk AI systems involving biometrics, law enforcement, migration/border control, emergency services, and administration of justice, and as fundamental rights authority. Administrative penalties reach €350,000 or 1% of worldwide annual turnover (whichever higher) for undertakings, with daily penalties up to €12,000.

## Obligations + coverage

### Authority designation, coordination & single point of contact (LN 226)

| Obligation | Coverage | Evidence |
|---|---|---|
| MDIA designated as default Market Surveillance Authority for AI systems not allocated to another authority | ⚪ Boundary: government-authority designation is legal, not software-addressable | |
| MDIA as Notifying Authority responsible for recognising conformity assessment bodies | ⚪ Boundary: accreditation/notification of third-party bodies is organizational | |
| MDIA serves as single point of contact for AI Act matters at national level | ⚪ Boundary: legal-entity contact registration is organizational | |
| MDIA–MFSA coordination on market surveillance for high-risk AI used by financial institutions | 🟡 Partial: coordination-bus provides inter-agent coordination substrate; inter-authority information-sharing act is org task | `hummbl_governance/coordination_bus.py`, `hummbl_governance/audit_log.py` |
| MDIA coordination with other market surveillance authorities listed in Section A of Annex 1 of the EU AI Act | 🟡 Partial: coordination-bus + audit-log export supports cross-authority evidence sharing; formal cooperation is org task | `hummbl_governance/coordination_bus.py`, `hummbl_governance/compliance_mapper.py` |

### Conformity assessment & registration of high-risk AI systems (LN 226)

| Obligation | Coverage | Evidence |
|---|---|---|
| Providers of high-risk AI systems under Point 2 of Annex III must register the system with MDIA | 🟡 Partial: compliance-mapper produces registration records and evidence bundles; submission to MDIA is org task | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Conformity assessment procedures for high-risk AI systems prior to market placement | ✅ Conformity-assessment evidence template + assessment-record tuple (cross-ref EU AI Act Art. 43) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Providers and importers maintain technical files and make them available to MDIA on request | ✅ Immutable audit-log retention + documentation-retention tuple with on-request export | `hummbl_governance/audit_log.py`, `hummbl_governance/kernel/receipt_engine.py` |
| Timelines for conformity assessment outcomes and corrective actions where non-conformity is detected | 🟡 Partial: schedule-engine tracks assessment deadlines; enforcement of corrective timelines is org task | `hummbl_governance/kernel/schedule_engine.py`, `hummbl_governance/compliance_mapper.py` |
| Accreditation and notification of conformity assessment bodies per national and EU standards | ⚪ Boundary: third-party-body accreditation is organizational | |

### Risk management, technical documentation & data governance (LN 226)

| Obligation | Coverage | Evidence |
|---|---|---|
| Implement risk management system for high-risk AI systems (identify, assess, mitigate) | ✅ Risk-mgmt program substrate: INTENT + risk-treatment tuples (cross-ref EU AI Act Art. 9, NIST AI RMF) | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Maintain technical documentation demonstrating conformity (Annex IV) | ✅ Documentation-retention tuple + immutable audit-log with evidence export | `hummbl_governance/audit_log.py`, `hummbl_governance/kernel/evidence_engine.py` |
| Data governance for training, validation and testing datasets (quality, relevance, bias mitigation) | 🟡 Partial: schema-validator enforces data-schema integrity; dataset-quality and bias-mitigation processes are org task | `hummbl_governance/schema_validator.py`, `hummbl_governance/compliance_mapper.py` |
| Automatic event logging for high-risk AI systems operating with recorded logs | ✅ Immutable append-only audit-log with Lamport-clock ordering | `hummbl_governance/audit_log.py`, `hummbl_governance/lamport_clock.py` |
| Record-keeping of risk-management iterations and design decisions | ✅ Audit-log lineage + evolution-lineage tracking for design changes | `hummbl_governance/audit_log.py`, `hummbl_governance/kernel/sequence_engine.py` |

### Transparency, human oversight & cybersecurity (LN 226 / LN 227)

| Obligation | Coverage | Evidence |
|---|---|---|
| Transparency obligations — notify users when interacting with AI (limited-transparency systems) | ✅ Transparency-notification primitive (cross-ref EU AI Act Art. 50) | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Label AI-generated content (deepfakes, synthetic media) distinguishable from non-AI content | ✅ Content-authenticity tuple + output-validation gate (cross-ref EU AI Act Art. 50(2)) | `hummbl_governance/output_validator.py` |
| Human oversight of high-risk AI systems, including named responsible person | ✅ Human-oversight delegation token + contact-registration tuple (cross-ref EU AI Act Art. 14) | `hummbl_governance/delegation.py`, `hummbl_governance/identity.py` |
| Operational limits on automated decision-making with human-in-the-loop review | ✅ Kill-switch 4-mode halt + capability-fence enforcement of human-approval gates | `hummbl_governance/kill_switch.py`, `hummbl_governance/capability_fence.py` |
| Cybersecurity and model security (vulnerability management, patching, secure design) | 🟡 Partial: capability-fence + output-validator enforce runtime security boundaries; vulnerability/patch management is org task | `hummbl_governance/capability_fence.py`, `hummbl_governance/output_validator.py` |

### Post-market monitoring, incident reporting & regulatory sandbox (LN 226)

| Obligation | Coverage | Evidence |
|---|---|---|
| Providers implement post-market monitoring system for high-risk AI | ✅ Post-market-monitoring template + adverse-event tuple + health-probe monitoring | `hummbl_governance/audit_log.py`, `hummbl_governance/health_probe.py` |
| Report serious incidents and malfunctions to MDIA | 🟡 Partial: incident-report generator + audit-log export produces the report; submission to MDIA is org task | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| MDIA establishes and operates the national AI regulatory sandbox | ⚪ Boundary: government-sandbox operation is organizational, not software-addressable | |
| Sandbox confidentiality and IP safeguards for participating businesses (SMEs, start-ups) | ⚪ Boundary: legal confidentiality/IP protections are organizational | |
| MDIA issues guidance, templates and non-binding technical standards | ⚪ Boundary: authority-issued guidance is organizational | |

### Enforcement, penalties & appeals (LN 226 / LN 227)

| Obligation | Coverage | Evidence |
|---|---|---|
| Administrative penalties up to €350,000 or 1% of worldwide annual turnover for infringements by undertakings | ⚪ Boundary: administrative-fine exposure is legal, not software-addressable | |
| Daily penalties up to €12,000 for ongoing infringements (€50/day for public authorities) | ⚪ Boundary: administrative-fine exposure is legal | |
| MDIA may issue reprimands, warnings or non-monetary disciplinary measures | ⚪ Boundary: regulatory-order compliance is organizational | |
| MDIA corrective measures including recalls, withdrawals and suspension of market placement | ⚪ Boundary: regulatory-order compliance is organizational | |
| 2-year prescription period for proceedings; appeal to Part IX of Cap. 591 | ⚪ Boundary: legal procedure and appeal rights are legal, not software-addressable | |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| Authority designation & coordination (LN 226) | 5 | 0 | 2 | 3 |
| Conformity assessment & registration (LN 226) | 5 | 2 | 2 | 1 |
| Risk management, documentation & data governance (LN 226) | 5 | 4 | 1 | 0 |
| Transparency, oversight & cybersecurity (LN 226/227) | 5 | 4 | 1 | 0 |
| Post-market monitoring, incident reporting & sandbox (LN 226) | 5 | 1 | 1 | 3 |
| Enforcement, penalties & appeals (LN 226/227) | 5 | 0 | 0 | 5 |
| **Totals** | **30** | **11** | **7** | **12** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- LN 226/227 implement Regulation (EU) 2024/1689 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Risk management overlaps NIST AI RMF MEASURE — see [`nist-ai-rmf.md`](./nist-ai-rmf.md)
- Human oversight overlaps EU AI Act Art. 14 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Transparency overlaps EU AI Act Art. 50 and South Korea AI Basic Act Art. 31 — see [`eu-ai-act.md`](./eu-ai-act.md), [`south-korea-ai-basic-act.md`](./south-korea-ai-basic-act.md)
- Post-market monitoring overlaps EU AI Act Art. 72 — see [`eu-ai-act.md`](./eu-ai-act.md)
