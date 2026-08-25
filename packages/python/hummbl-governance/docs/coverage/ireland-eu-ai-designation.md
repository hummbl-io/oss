# Ireland EU AI Designation Regulations Coverage Matrix — HUMMBL

**Standard**: European Union (Artificial Intelligence) (Designation) Regulations 2025, S.I. No. 366 of 2025
**Effective**: July 25, 2025 (signed by Minister for Enterprise, Tourism and Employment 25 July 2025; published in Iris Oifigiúil 29 July 2025)
**Source**: https://www.irishstatutebook.ie/eli/2025/si/366/made/en/pdf
**Last reviewed**: 2026-06-25
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not Irish legal counsel and does not provide legal advice on S.I. No. 366/2025. These Regulations are Ireland's national designation instrument under the European Communities Act 1972 (s. 3) giving further effect to the EU AI Act (Regulation (EU) 2024/1689). The instrument does not transpose the EU regulation's substantive AI governance rules (which are directly applicable) but designates national competent authorities, market surveillance authorities, notifying authorities, and a single point of contact for EU AI Act implementation. Statutory compliance is the customer-organization responsibility. HUMMBL maps technical primitives to the Ireland-specific institutional, surveillance, coordination, and record-keeping provisions while cross-referencing the EU AI Act matrix for shared substantive obligations.

## Scope summary

The Regulations apply to the designation of Irish national competent authorities for the purposes of EU AI Act Article 70. They adopt a distributed implementation model: the Minister for Enterprise, Tourism and Employment is designated as a national competent authority and the single point of contact (Art. 70(2)), while existing sectoral regulators are designated as market surveillance authorities and national competent authorities for specific Section A, Annex I points. The Central Bank of Ireland is designated as market surveillance authority for Article 74(6) (financial services); the Data Protection Commission for Article 74(8) (personal data). Notifying authorities are designated by Annex I point across the Minister, the Minister for Transport, the Health Products Regulatory Authority, and the Commission for Communications Regulation. The Schedule maps 14 Annex I reference points to named market surveillance authorities (Health and Safety Authority, Competition and Consumer Protection Commission, Marine Survey Office, Commission for Railway Regulation, Commission for Communications Regulation, Health Products Regulatory Authority). A National AI Office (NAIO) is anticipated to centralise coordination, expertise, and a regulatory sandbox in due course.

## Obligations + coverage

### Citation, commencement, and purpose (Regs 1–2)

| Obligation | Coverage | Evidence |
|---|---|---|
| Citation as the "European Union (Artificial Intelligence) (Designation) Regulations 2025" (Reg. 1) | ⚪ Boundary: legal instrument citation is statutory, not software-addressable | |
| Regulations made under European Communities Act 1972 s. 3 to give further effect to EU AI Act (Reg. 2024/1689) | ⚪ Boundary: statutory basis and purpose are legal determinations | |
| Commencement upon publication in Iris Oifigiúil (29 July 2025) | ⚪ Boundary: legal commencement is statutory | |

### Designation of national competent authorities (Reg. 3)

| Obligation | Coverage | Evidence |
|---|---|---|
| Minister for Enterprise, Tourism and Employment designated as a national competent authority (EU AI Act Art. 70(1)(a)) | ⚪ Boundary: government authority designation is institutional, not software-addressable | |
| Sectoral market surveillance authorities designated as national competent authorities for Section A, Annex I points (per Schedule) | ⚪ Boundary: government authority designation is institutional | |
| Distributed implementation model using existing sectoral regulators rather than a single new authority | ⚪ Boundary: institutional governance-model choice is organizational | |
| Registration and recording of designated authority identities and jurisdictional scope | ✅ Identity registry records authority-identity tuples with role and jurisdiction metadata; legal designation act is institutional | `hummbl_governance/identity.py`, `hummbl_governance/kernel/identity_engine.py` |

### Designation of market surveillance authorities (Reg. 4)

| Obligation | Coverage | Evidence |
|---|---|---|
| Central Bank of Ireland designated as market surveillance authority for EU AI Act Art. 74(6) (financial-sector AI) | ⚪ Boundary: government authority designation is institutional | |
| Data Protection Commission designated as market surveillance authority for EU AI Act Art. 74(8) (AI processing personal data) | ⚪ Boundary: government authority designation is institutional | |
| Market surveillance authorities may demand information from providers, deployers, importers, and distributors (EU AI Act Art. 73, via designation) | 🟡 Partial: audit-log export + evidence engine produce structured information packages for authority requests; response to demand is org task | `hummbl_governance/audit_log.py`, `hummbl_governance/kernel/evidence_engine.py` |
| Authorities may conduct technical examinations and on-site inspections of AI systems and documentation | 🟡 Partial: audit-log + evidence export provide inspectable technical records; on-site inspection execution is authority task | `hummbl_governance/audit_log.py`, `hummbl_governance/kernel/evidence_engine.py` |

### Designation of notifying authorities (Reg. 5)

| Obligation | Coverage | Evidence |
|---|---|---|
| Minister designated as notifying authority for Annex I points 1, 2, 4, 5, 7, 9 and 10 | ⚪ Boundary: government authority designation is institutional | |
| Minister for Transport designated as notifying authority for Annex I points 3 and 8 | ⚪ Boundary: government authority designation is institutional | |
| Health Products Regulatory Authority designated as notifying authority for Annex I points 11 and 12 | ⚪ Boundary: government authority designation is institutional | |
| Commission for Communications Regulation designated as notifying authority for Annex I point 6 | ⚪ Boundary: government authority designation is institutional | |
| Notifying authority oversight of conformity-assessment bodies and notified-body accreditation (EU AI Act Art. 28–30) | 🟡 Partial: compliance mapper + receipt engine can record conformity-assessment body accreditation and notification receipts; authority oversight is institutional | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/kernel/receipt_engine.py` |

### Single point of contact and EU coordination (Reg. 6)

| Obligation | Coverage | Evidence |
|---|---|---|
| Minister designated as single point of contact for EU AI Act Art. 70(2) | ⚪ Boundary: government role designation is institutional | |
| SPOC coordination with European Commission, AI Office, and other Member States | 🟡 Partial: coordination bus + lamport clock support inter-agent coordination and ordered messaging primitives; intergovernmental SPOC coordination is institutional | `hummbl_governance/coordination_bus.py`, `hummbl_governance/lamport_clock.py` |
| SPOC forwarding of EU AI Act implementation information to national authorities | 🟡 Partial: coordination bus supports message routing between governance agents; authority-to-authority information forwarding is institutional | `hummbl_governance/coordination_bus.py` |
| Recording of SPOC communications and coordination artifacts with tamper-evidence | ✅ Immutable audit-log retention + receipt engine record coordination communications and forwarding events with tamper-evidence | `hummbl_governance/audit_log.py`, `hummbl_governance/kernel/receipt_engine.py` |

### Schedule — sectoral market surveillance mapping

| Obligation | Coverage | Evidence |
|---|---|---|
| Health and Safety Authority designated for Annex I points 1, 4, 5, 7, 10 (non-domestic gas), and 9 (PPE in workplace) | ⚪ Boundary: sectoral authority-jurisdiction mapping is institutional | |
| Competition and Consumer Protection Commission designated for Annex I points 2, 9 (consumer products), and 10 (domestic gas appliances) | ⚪ Boundary: sectoral authority-jurisdiction mapping is institutional | |
| Marine Survey Office, Commission for Railway Regulation, Commission for Communications Regulation, and Health Products Regulatory Authority designated for respective Annex I points | ⚪ Boundary: sectoral authority-jurisdiction mapping is institutional | |
| Maintenance of authoritative mapping of Annex I points to surveillance authorities | 🟡 Partial: compliance mapper can store authority-jurisdiction mapping tuples for reference; authoritative legal mapping is institutional | `hummbl_governance/compliance_mapper.py` |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| Citation, commencement, purpose (Regs 1–2) | 3 | 0 | 0 | 3 |
| National competent authorities (Reg. 3) | 4 | 1 | 0 | 3 |
| Market surveillance authorities (Reg. 4) | 4 | 0 | 2 | 2 |
| Notifying authorities (Reg. 5) | 5 | 0 | 1 | 4 |
| Single point of contact + EU coordination (Reg. 6) | 4 | 1 | 2 | 1 |
| Schedule — sectoral surveillance mapping | 4 | 0 | 1 | 3 |
| **Totals** | **24** | **2** | **6** | **16** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated. The high proportion of ⚪ (Boundary) rows reflects the nature of S.I. No. 366/2025 as a national authority-designation instrument — most obligations are governmental authority designations, sectoral jurisdiction mappings, and inter-agency coordination that are not software-addressable. HUMMBL's substantive AI governance coverage for Ireland-operating organizations is primarily mapped through the EU AI Act matrix, which these Regulations implement.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- These Regulations implement EU AI Act (Regulation 2024/1689) Art. 70 — see [`eu-ai-act.md`](./eu-ai-act.md) for substantive AI governance obligations (prohibited practices, high-risk systems, transparency, conformity)
- Market surveillance information demands overlap EU AI Act Art. 73 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Notifying authority oversight overlaps EU AI Act Art. 28–30 — see [`eu-ai-act.md`](./eu-ai-act.md)
- DPC designation for Art. 74(8) overlaps GDPR personal-data processing — see [`gdpr.md`](./gdpr.md)
- Denmark's national AI enforcement law (Law No. 467/2025) follows a similar designation-instrument pattern — see [`denmark-ai-act.md`](./denmark-ai-act.md)
- Audit-log retention overlaps NIST AI RMF IDENTIFY — see [`nist-ai-rmf.md`](./nist-ai-rmf.md)
