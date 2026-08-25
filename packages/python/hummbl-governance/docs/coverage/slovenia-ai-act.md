# Slovenia AI Implementation Act Coverage Matrix — HUMMBL

**Standard**: Act on the Implementation of the Regulation (EU) on Harmonised Rules on Artificial Intelligence (Zakon o izvajanju uredbe (EU) o določitvi harmoniziranih pravil o umetni inteligenci — ZIUDHPUI), Official Gazette RS No. 85/2025
**Effective**: November 21, 2025
**Source**: https://pisrs.si/pregledPredpisa?id=ZAKO9225
**Last reviewed**: 2026-06-25
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not Slovenian legal counsel and does not provide legal advice on ZIUDHPUI. The Act is the national implementing law for Regulation (EU) 2024/1689 (EU AI Act) and does not create new substantive obligations for AI systems beyond the EU Regulation — it designates competent national authorities, sets enforcement and market-surveillance procedures, establishes a national ethics council and regulatory sandboxes, and prescribes administrative sanctions. Statutory compliance is the customer-organization responsibility. HUMMBL maps technical primitives to the Act's institutional, transparency, fundamental-rights, high-risk oversight, and enforcement obligations.

## Scope summary

ZIUDHPUI applies to all AI systems and operators subject to the EU AI Act within Slovenian jurisdiction. It designates notifying authorities (Ministry of the Economy, Tourism and Sport; Ministry of Infrastructure; Ministry of Health; Ministry of Digital Transformation; Public Agency for Medicinal Products and Medical Devices), market surveillance authorities (Information Commissioner; Bank of Slovenia; Insurance Supervision Agency; Market Inspectorate; Agency for Communication Networks and Services — AKOS, also the single contact point), and the Information Society Inspectorate for notified-body supervision and public-sector disclosure. The Act establishes the National Council for Ethics in AI, regulatory sandboxes (first by 2 August 2026), a national register of high-risk AI systems in critical infrastructure, a HelpDesk for SMEs and the public, and sanctions for all AI value-chain actors with fines up to €35 million or 7% of worldwide annual turnover for prohibited practices.

## Obligations + coverage

### Competent authorities and institutional framework (Arts. 3–5)

| Obligation | Coverage | Evidence |
|---|---|---|
| Designate notifying authorities for high-risk AI systems (Annex I Section A and Annex III point 1) | ⚪ Boundary: government-body designation is institutional, not software-addressable | |
| Designate national accreditation body (Slovenian Accreditation) to evaluate conformity assessment bodies | ⚪ Boundary: accreditation-body designation is institutional | |
| Designate market surveillance authorities (Information Commissioner, Bank of Slovenia, Insurance Supervision Agency, Market Inspectorate, AKOS) | ⚪ Boundary: authority designation is institutional, not software-addressable | |
| AKOS designated as single contact point for AI Act implementation and EU AI Office liaison | ⚪ Boundary: single-contact-point designation is institutional | |

### Market surveillance and enforcement (Arts. 6–8)

| Obligation | Coverage | Evidence |
|---|---|---|
| Market surveillance authorities exercise powers under technical-product and inspection legislation, with sector-specific procedures | 🟡 Partial: audit-log export + compliance-report generator supports inspection; enforcement powers are org/legal task | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Public disclosure of supervisory measures and sanctions — offender, responsible person, nature of measure, operative part, 3-year retention | ✅ Publication + sanctions-disclosure tuple with retention enforcement (cross-ref EU AI Act Art. 92) | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Establish coordination council of market surveillance authorities for coordinated action | 🟡 Partial: coordination-bus provides multi-agent coordination and audit trail infrastructure for inter-agency data sharing; council establishment and statutory authority remain institutional | `hummbl_governance/coordination_bus.py`, `hummbl_governance/audit_log.py` |
| Consultation between market surveillance authorities and sectoral inspection bodies | ⚪ Boundary: inter-agency consultation is institutional | |

### Support measures and innovation (Arts. 9–14)

| Obligation | Coverage | Evidence |
|---|---|---|
| Establish regulatory sandboxes for AI testing (AKOS, first sandbox by 2 August 2026) | 🟡 Partial: capability-fence sandbox supports controlled testing environment; national sandbox infrastructure is org task | `hummbl_governance/capability_fence.py`, `hummbl_governance/circuit_breaker.py` |
| Maintain national register of high-risk AI systems in critical infrastructure | ✅ Registration + inventory tuple (cross-ref EU AI Act Art. 49) | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Manage data submitted by providers of high-risk AI systems per Art. 49(1) EU AI Act | ✅ Evidence-submission + receipt tuple with immutable storage | `hummbl_governance/audit_log.py`, `hummbl_governance/kernel/receipt_engine.py` |
| Establish single contact point / HelpDesk for SMEs and general public on AI Act implementation | 🟡 Partial: compliance-mapper generates AI Act implementation documentation, FAQ content, and guidance templates for helpdesk use; helpdesk staffing and operation remain organizational | `hummbl_governance/compliance_mapper.py` |

### National Council for Ethics in AI and AI literacy (Arts. 15–17)

| Obligation | Coverage | Evidence |
|---|---|---|
| Establish National Council for Ethics in AI for ethical questions and responsible AI use | ⚪ Boundary: ethics-council establishment is institutional, not software-addressable | |
| Promote AI literacy per Art. 4 EU AI Act — campaigns, training for public officials | 🟡 Partial: compliance-mapper generates AI literacy training materials and documentation aligned with EU AI Act Art. 4 requirements; campaign delivery and training execution remain organizational | `hummbl_governance/compliance_mapper.py` |
| Public-sector AI systems — unified information point for disclosure of AI system information | ✅ Public-sector disclosure tuple (cross-ref EU AI Act Art. 60) | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |

### Fundamental rights and high-risk oversight (cross-ref EU AI Act)

| Obligation | Coverage | Evidence |
|---|---|---|
| Supervision of prohibited practices (Art. 5 EU AI Act) by Information Commissioner | ✅ Kill-switch prohibition enforcement + audit-log (cross-ref EU AI Act Art. 5) | `hummbl_governance/kill_switch.py`, `hummbl_governance/audit_log.py` |
| Conformity verification by importers/distributors before placing high-risk systems on market | ✅ Conformity-verification tuple + schema validation (cross-ref EU AI Act Art. 26) | `hummbl_governance/schema_validator.py`, `hummbl_governance/audit_log.py` |
| Fundamental rights impact assessment for high-risk AI deployers (Art. 27 EU AI Act) | ✅ FRIA template with fundamental-rights component (cross-ref EU AI Act Art. 27) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Human oversight of high-risk AI systems (Art. 14 EU AI Act) | ✅ Human-oversight delegation token + contact-registration tuple (cross-ref EU AI Act Art. 14) | `hummbl_governance/delegation.py`, `hummbl_governance/identity.py` |
| Transparency obligations for AI systems — user notification and content labeling (Art. 50 EU AI Act) | ✅ Transparency-notification + output-labeling primitive (cross-ref EU AI Act Art. 50) | `hummbl_governance/output_validator.py`, `hummbl_governance/audit_log.py` |

### Sanctions and penalties

| Obligation | Coverage | Evidence |
|---|---|---|
| Fines for prohibited practices — up to €35M or 7% of worldwide annual turnover | ⚪ Boundary: administrative-fine exposure is legal, not software-addressable | |
| Fines for high-risk non-compliance and transparency obligations (tiered up to €15M/3% and €7.5M/1%) | ⚪ Boundary: administrative-fine exposure is legal | |
| Sanctions for all AI value-chain actors — providers, deployers, importers, distributors, authorised representatives, notified bodies | ⚪ Boundary: sanction regime is legal, not software-addressable | |
| Storage of documentation in event of bankruptcy or cessation of business activities | 🟡 Partial: audit-log retention preserves records; legal custody transfer is org task | `hummbl_governance/audit_log.py` |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| Competent authorities (Arts. 3–5) | 4 | 0 | 0 | 4 |
| Market surveillance (Arts. 6–8) | 4 | 1 | 1 | 2 |
| Support measures (Arts. 9–14) | 4 | 2 | 1 | 1 |
| Ethics council + AI literacy (Arts. 15–17) | 3 | 1 | 0 | 2 |
| Fundamental rights + high-risk (cross-ref EU AI Act) | 5 | 5 | 0 | 0 |
| Sanctions and penalties | 4 | 0 | 1 | 3 |
| **Totals** | **24** | **9** | **3** | **12** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- ZIUDHPUI implements Regulation (EU) 2024/1689 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Prohibited-practices and transparency obligations overlap EU AI Act Arts. 5, 50 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Fundamental rights impact assessment overlaps EU AI Act Art. 27 (FRIA) — see [`eu-ai-act.md`](./eu-ai-act.md)
- Human oversight overlaps EU AI Act Art. 14 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Parallel national implementation: Italy Law No. 132/2025 — see [`italy-law-132-2025.md`](./italy-law-132-2025.md)
