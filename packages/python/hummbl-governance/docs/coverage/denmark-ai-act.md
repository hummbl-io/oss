# Denmark AI Act Coverage Matrix — HUMMBL

**Standard**: Act on Supplementary Provisions to the Regulation on Artificial Intelligence (Lov om supplerende bestemmelser til forordningen om kunstig intelligens), Law No. 467 of 14 May 2025
**Effective**: August 2, 2025 (enacted 14 May 2025; in force 2 August 2025 per EU AI Act Art. 113)
**Source**: https://regulations.ai/regulations/RAI-DK-NA-SPAILXX-2025
**Last reviewed**: 2026-06-25
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not Danish legal counsel and does not provide legal advice on Law No. 467/2025. This Act is Denmark's national implementation of the EU AI Act (Regulation (EU) 2024/1689) — it does not transpose the EU regulation's substantive AI governance rules (which are directly applicable) but designates national competent authorities, establishes market surveillance and enforcement powers, and sets penalty frameworks. Statutory compliance is the customer-organization responsibility. HUMMBL maps technical primitives to the Denmark-specific institutional, surveillance, enforcement, and penalty provisions while cross-referencing the EU AI Act matrix for shared substantive obligations.

## Scope summary

The Act applies to providers, deployers, importers, distributors, and authorised representatives of AI systems within Denmark as defined by Article 2(1) of the EU AI Act. It designates three national competent authorities: Digitaliseringsstyrelsen (Agency for Digital Government) as notifying authority, central contact point, and market surveillance authority for most Art. 5 prohibited practices; Datatilsynet (Danish Data Protection Authority) for prohibited practices involving personal data; and Domstolsstyrelsen (Danish Court Administration) for AI systems in judicial contexts. The Act does not apply to the Faroe Islands or Greenland. It is designed as an initial measure covering the early EU AI Act provisions (primarily Art. 5 prohibited practices effective 2 August 2025), with a comprehensive successor law anticipated for the full EU AI Act scope.

## Obligations + coverage

### Institutional framework and authority designation (§ 2)

| Obligation | Coverage | Evidence |
|---|---|---|
| Designation of Digitaliseringsstyrelsen as notifying authority and central single point of contact (EU AI Act Art. 28, Art. 70) | ⚪ Boundary: government authority designation is institutional, not software-addressable | |
| Designation of Datatilsynet as market surveillance authority for Art. 5(1)(d, g) prohibited practices involving personal data | ⚪ Boundary: government authority designation is institutional | |
| Designation of Domstolsstyrelsen as market surveillance authority for courts' AI use outside judicial capacity | ⚪ Boundary: government authority designation is institutional | |
| Functional independence of market surveillance authorities in exercise of statutory duties | ⚪ Boundary: institutional independence is a governance-structure requirement | |

### Market surveillance powers (§§ 5–9)

| Obligation | Coverage | Evidence |
|---|---|---|
| Authorities may demand all necessary information from providers, deployers, importers, and distributors for surveillance purposes (§ 5) | 🟡 Partial: audit-log export + evidence engine produces structured information; receipt engine signs and chains information artifacts for tamper-evidence; response to authority demand is org task | `hummbl_governance/audit_log.py`, `hummbl_governance/kernel/evidence_engine.py`, `hummbl_governance/kernel/receipt_engine.py` |
| Providers/deployers must demonstrate how compliance measures were implemented upon authority request (§ 5) | 🟡 Partial: compliance mapper generates compliance evidence and implementation records; law engine evaluates obligations against receipts to surface violations; submission is org task (cross-ref EU AI Act Art. 9, Art. 12) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/kernel/evidence_engine.py`, `hummbl_governance/kernel/law_engine.py` |
| On-site access to business premises and documentation without prior judicial authorization (§ 6) | 🟡 Partial: audit-log + evidence engine provide structured documentation for on-site access; receipt engine chains documentation artifacts with tamper-evidence; physical premises access is org task | `hummbl_governance/audit_log.py`, `hummbl_governance/kernel/evidence_engine.py`, `hummbl_governance/kernel/receipt_engine.py` |
| Technical examinations of AI systems by authorities or designated independent experts (§ 9) | 🟡 Partial: audit-log + evidence export provides technical records for examination; health probe exposes runtime health state; reasoning engine records decision traces for review; on-site technical review is authority task | `hummbl_governance/audit_log.py`, `hummbl_governance/kernel/evidence_engine.py`, `hummbl_governance/health_probe.py`, `hummbl_governance/reasoning.py` |
| Registration and retention of information collected during surveillance activities (§ 5(2)) | ✅ Immutable audit-log retention + receipt engine records surveillance artifacts with tamper-evidence | `hummbl_governance/audit_log.py`, `hummbl_governance/kernel/receipt_engine.py` |

### Enforcement and corrective measures (§§ 7–8)

| Obligation | Coverage | Evidence |
|---|---|---|
| Temporary prohibitions on AI systems using Art. 5 prohibited practices (§ 7) | ✅ Kill-switch HALT mode + circuit-breaker fast-fail enforce prohibition at technical level; capability_fence blocks prohibited capabilities (cross-ref EU AI Act Art. 5) | `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py`, `hummbl_governance/capability_fence.py` |
| Corrective orders requiring remediation of non-compliant AI systems (§ 8) | 🟡 Partial: compliance mapper tracks remediation status and corrective-action tuples; schedule engine registers remediation loops and records run outcomes; stride mapper detects violations triggering corrective action; compliance with authority order is org task | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py`, `hummbl_governance/kernel/schedule_engine.py`, `hummbl_governance/stride_mapper.py` |
| Product recalls and market withdrawals of non-compliant AI systems (§ 8) | 🟡 Partial: lifecycle management tracks decommissioning/withdrawal status; kill-switch HALT enforces technical system withdrawal; schedule engine registers withdrawal loops; sequence engine orders decommission steps with continuity checks; market recall logistics are org task | `hummbl_governance/lifecycle.py`, `hummbl_governance/kill_switch.py`, `hummbl_governance/kernel/schedule_engine.py`, `hummbl_governance/kernel/sequence_engine.py` |
| Publication of enforcement decisions by market surveillance authorities | ⚪ Boundary: authority publication of rulings is institutional, not software-addressable | |

### Penalties and sanctions (§§ 10–11, § 18)

| Obligation | Coverage | Evidence |
|---|---|---|
| Criminal fines for violations of Art. 5 prohibited AI practices (§ 10(1)) | ⚪ Boundary: criminal penalty exposure is legal, not software-addressable (cross-ref EU AI Act Art. 5, Art. 99) | |
| Criminal fines for providing false, incorrect, or misleading information to authorities or notified bodies (§ 10(2)) | ⚪ Boundary: criminal penalty exposure is legal | |
| Criminal fines for non-compliance with information demands (§ 5), inspection access (§ 6), or temporary prohibitions (§ 7) (§ 10) | ⚪ Boundary: criminal penalty exposure is legal | |
| Bødeforelæg — administrative fine settlement without court proceedings when accused admits liability (§ 11, § 18) | ⚪ Boundary: legal proceeding and fine settlement are organizational | |
| Corporate criminal liability for legal persons and 5-year limitation period (§ 10(3), § 18(4)) | ⚪ Boundary: corporate liability and statute-of-limitations are legal determinations | |

### Procedural safeguards, appeals, and cooperation (§§ 3–4)

| Obligation | Coverage | Evidence |
|---|---|---|
| Decisions of national competent authorities cannot be appealed to other administrative authority — judicial review only (§ 3) | ⚪ Boundary: procedural appeal rights are legal determinations | |
| National competent authorities monitor compliance with EU AI Act, this law, and secondary rules (§ 4) | 🟡 Partial: compliance mapper + audit-log support compliance monitoring and violation detection; stride mapper surfaces STRIDE threat findings; law engine evaluates receipts against obligations to flag violations; authority monitoring is institutional | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py`, `hummbl_governance/stride_mapper.py`, `hummbl_governance/kernel/law_engine.py` |
| Inter-authority cooperation and coordination among Digitaliseringsstyrelsen, Datatilsynet, and Domstolsstyrelsen | ⚪ Boundary: inter-agency coordination is institutional | |
| Cross-border cooperation with EU Commission, AI Office, and other Member States (EU AI Act Art. 70–71) | ⚪ Boundary: intergovernmental coordination is institutional | |

### Territorial scope and implementation (§ 1)

| Obligation | Coverage | Evidence |
|---|---|---|
| Act supplements EU AI Act (Regulation 2024/1689) — establishes enforcement machinery, does not transpose substantive rules | ⚪ Boundary: legal framework designation is statutory, not software-addressable | |
| Territorial exclusion of the Faroe Islands and Greenland from Act application | ⚪ Boundary: jurisdictional scope is a legal determination | |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| Institutional framework (§ 2) | 4 | 0 | 0 | 4 |
| Market surveillance powers (§§ 5–9) | 5 | 1 | 4 | 0 |
| Enforcement and corrective measures (§§ 7–8) | 4 | 1 | 2 | 1 |
| Penalties and sanctions (§§ 10–11, § 18) | 5 | 0 | 0 | 5 |
| Procedural safeguards, appeals, cooperation (§§ 3–4) | 4 | 0 | 1 | 3 |
| Territorial scope and implementation (§ 1) | 2 | 0 | 0 | 2 |
| **Totals** | **24** | **2** | **7** | **15** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated. The high proportion of ⚪ (Boundary) rows reflects the nature of Law No. 467/2025 as a national enforcement and institutional designation law — most obligations are governmental authority designations, criminal penalty frameworks, and inter-agency coordination that are not software-addressable. HUMMBL's substantive AI governance coverage for Denmark-operating organizations is primarily mapped through the EU AI Act matrix, which this Act supplements.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- This Act implements EU AI Act (Regulation 2024/1689) — see [`eu-ai-act.md`](./eu-ai-act.md) for substantive AI governance obligations (prohibited practices, high-risk systems, transparency, conformity)
- Temporary prohibition enforcement overlaps EU AI Act Art. 5 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Compliance evidence production overlaps EU AI Act Art. 9 (risk management) and Art. 12 (record-keeping) — see [`eu-ai-act.md`](./eu-ai-act.md)
- Audit-log retention overlaps NIST AI RMF IDENTIFY — see [`nist-ai-rmf.md`](./nist-ai-rmf.md)
- Italy's national AI enforcement law (Law 132/2025) follows a similar implementation pattern — see [`italy-law-132-2025.md`](./italy-law-132-2025.md)
