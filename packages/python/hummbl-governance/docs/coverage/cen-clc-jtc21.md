# CEN-CENELEC JTC 21 (M/613) Coverage Matrix — HUMMBL

**Standard**: CEN-CENELEC JTC 21 European AI Act harmonized-standards programme (Commission standardisation request M/613 amending M/593)
**Source (live 2026-08-31 snapshot)**: https://jtc21.eu/significant-milestone-for-european-ai-standardization/ (JTC 21 secretariat, 9 July 2026)
**Secondary status check**: CEN-CENELEC deliverable designations confirmed against public OJ-citation trackers that read the CEN-CENELEC standards database (1BusinessWorld AI Center tracker, last verified 2026-08-01). Digital Strategy / Commission AI Act standardisation page was not independently fetched this session.
**Last reviewed**: 2026-08-31
**Reviewer**: documentation pass per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md) and LANDING-013
**HUMMBL version mapped against**: hummbl-governance v1.4.2 (`pyproject.toml` on this tree)

## Boundary disclaimer (statutory)

HUMMBL is **not** a Notified Body under EU AI Act Article 31. HUMMBL is **not** a European or national standards body. Applying a harmonized standard does **not** by itself confer AI Act conformity.

Article 40(1) of Regulation (EU) 2024/1689 attaches a presumption of conformity only to harmonised standards whose references have been **published in the Official Journal of the European Union**, and only so far as those standards cover the requirements concerned. **EN 18286:2026 has no OJ citation as of this review → no presumption of conformity yet.** Customer assessment, and where required a Notified Body, remain the customer's.

This matrix is **document-level**. Unpublished drafts do not have public clause numbers in this corpus. **No clause numbers are invented.**

EN 18286 is a QMS standard for AI Act regulatory purposes (Art. 17). It is **not** ISO/IEC 42001. Do not collapse them. QMS / AIMS authorship is the customer organisation.

## Coverage state legend

| Glyph | State | Meaning |
|---|---|---|
| ✅ | Fulfilled | Named HUMMBL primitive implements the control; evidence artifact must be validated before public use |
| 🟡 | Partial | HUMMBL primitive provides part; customer policy / unpublished draft / OJ citation completes it. Both parts named. |
| ⚪ | Boundary | Control is organizational, regulatory, or institutional; HUMMBL provides evidence interface where applicable. |
| ⛔ | Out of scope | Control does not apply to the AI governance platform context (retained for completeness). |

**Overlap with HUMMBL is Partial at most.** No row in this file is ✅.

## Completeness

Completeness for this first matrix = one row per **named JTC 21 deliverable confirmed without inventing a number**, plus explicit programme-boundary rows (mandate, OJ citation, QMS≠AIMS). Drafts confirmed only as designations + titles. Enquiry dates below are from the 9 July 2026 JTC 21 post; later CEN-CENELEC stage labels (Enquiry vs Approval) may have moved and are noted where a secondary source disagrees.

## Programme-boundary rows

| ID | Requirement | HUMMBL coverage | Evidence |
|---|---|---|---|
| M/613 (mandate) | Commission standardisation request for AI Act harmonised standards (amends M/593) | ⚪ Boundary: institutional mandate. HUMMBL is not a CEN-CENELEC participant and does not author European standards. | n/a — boundary |
| Art. 40 OJ citation | Presumption of conformity requires OJ publication of the standard's reference | ⚪ Boundary: no JTC 21 deliverable in this file has an OJ citation as of 2026-08-31. Applying EN 18286 does not confer Art. 40 presumption. | n/a — boundary; see `eu-ai-act.md` Art. 40 (Partial in that file, last reviewed 2026-05-14) |
| EN 18286 ≠ ISO 42001 | QMS for AI Act Art. 17 vs organisation AIMS | ⚪ Boundary: different instruments. ISO 42001 rows stay in [`iso-42001.md`](./iso-42001.md). This file does not treat EN 18286 as 42001. | n/a — boundary |

## Document-level rows (confirmed designations)

| Deliverable | Title / public status (do not invent clauses) | HUMMBL coverage | Evidence |
|---|---|---|---|
| EN 18286:2026 | Quality Management System for EU AI Act regulatory purposes (Art. 17). JTC 21 (9 July 2026): expected publication; CEN project record cited elsewhere as ratification ~12 July 2026 / availability ~22 July 2026. **OJ citation pending.** | 🟡 Partial: QMS is customer. HUMMBL provides technical artifacts a QMS may reference — Art. 12-style logs (`audit_log`), risk-register tuples (`coordination_bus`), documentation generation (`compliance_mapper`). Same split as `eu-ai-act.md` Art. 17 (Partial in that file). Not a QMS and not ISO 42001. | `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py`, `hummbl_governance/compliance_mapper.py` |
| prEN 18228 | AI Risk Management. JTC 21: Public Hearing / enquiry cited through **30 July 2026**. Draft — not in force; cannot be OJ-cited. | 🟡 Partial: unpublished draft. HUMMBL overlap is toward existing Art. 9 evidence substrate (`audit_log`, `coordination_bus`) already marked in `eu-ai-act.md`. Residual-risk acceptance and RM procedure authorship are customer. No prEN 18228 clauses claimed. | `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py` |
| prEN 18282 | Cybersecurity specifications for AI systems. JTC 21: enquiry cited through **30 July 2026**. Draft — not in force. | 🟡 Partial: unpublished draft. Overlap is toward existing Art. 15 robustness/cyber cells (`circuit_breaker`, `delegation`) in `eu-ai-act.md`. Network / product cybersecurity programme is customer. No prEN 18282 clauses claimed. | `hummbl_governance/circuit_breaker.py`, `hummbl_governance/delegation.py` |
| prEN 18229-1 | AI Trustworthiness Framework — Part 1: Logging. JTC 21: enquiry cited through **20 August 2026**. Draft — not in force. | 🟡 Partial: unpublished draft. Overlap is toward existing Art. 12 / Art. 19 record-keeping (`audit_log`, `coordination_bus`, receipts). Logging policy, retention schedule, and any draft-specific log fields are customer. No Part 1 clauses claimed. | `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py` |
| prEN 18229-2 | AI Trustworthiness Framework — Part 2: Transparency. Designation confirmed (CEN-CENELEC database via 2026-08-01 tracker); **Under Drafting**. JTC 21 9 July post does not name this part. | 🟡 Partial: unpublished draft. Overlap is toward existing Art. 13 / Art. 50 transparency cells (`compliance_mapper`). Customer-facing UX disclosure remains product/org. No Part 2 clauses claimed. KLA June 2026 tracker combined later part titles differently; this row follows the later CEN-CENELEC designation “Part 2: Transparency.” | `hummbl_governance/compliance_mapper.py` |
| prEN 18229-3 | AI Trustworthiness Framework — Part 3: Human oversight. Designation confirmed (2026-08-01 tracker); **Under Enquiry**. | 🟡 Partial: unpublished draft. Overlap is toward existing Art. 14 cells (`kill_switch`, `delegation`). Oversight procedure authorship is customer. No Part 3 clauses claimed. | `hummbl_governance/kill_switch.py`, `hummbl_governance/delegation.py` |
| prEN 18229-4 | AI Trustworthiness Framework — Part 4: Accuracy. Designation confirmed (2026-08-01 tracker); **Under Drafting**. | ⚪ Boundary: unpublished draft; no public accuracy-test method in this corpus. HUMMBL does not implement a JTC 21 accuracy evaluation suite. Performance-declaration authorship is customer (see `eu-ai-act.md` Art. 15). | n/a — boundary; no invented clauses |
| prEN 18229-5 | AI Trustworthiness Framework — Part 5: Robustness. Designation confirmed (2026-08-01 tracker); **Under Drafting**. | 🟡 Partial: unpublished draft. Overlap is toward existing Art. 15 robustness (`circuit_breaker`). Robustness test plan is customer. No Part 5 clauses claimed. | `hummbl_governance/circuit_breaker.py` |
| prEN 18284 | Quality and governance of datasets in AI. Designation confirmed (2026-08-01 tracker); **Under Drafting**. | 🟡 Partial: unpublished draft. Overlap is toward existing Art. 10 data-governance cells (`schema_validator`, `audit_log`). Dataset QMS / statistical representativeness programme is customer. No prEN 18284 clauses claimed. | `hummbl_governance/schema_validator.py`, `hummbl_governance/audit_log.py` |
| prEN 18285 | AI conformity assessment framework. Designation confirmed (2026-08-01 tracker); **Under Drafting**. | ⚪ Boundary: conformity assessment is provider procedure + (where required) Notified Body. HUMMBL is not a CAB. Same split as `eu-ai-act.md` Art. 43 (Partial there for an evidence bundle; this unpublished draft adds no new HUMMBL claim). | n/a — boundary |
| prEN 18288 | Taxonomy of AI tasks in computer vision. Named on JTC 21 9 July 2026 post (Public Hearing until **16 July 2026**). Draft — not in force. | ⚪ Boundary: computer-vision task taxonomy. HUMMBL is a governance library, not a CV evaluation method. | n/a — boundary |

## Deliverables seen in secondary trackers but not required for this first cut

The 2026-08-01 CEN-CENELEC-database tracker also lists prEN 18281 (CV evaluation methods), prEN 18283 (bias), prEN ISO/IEC 23282 (NLP evaluation), and prEN ISO/IEC 24970 (AI system logging). They are **not** given rows here: the operator-requested first cut is the JTC 21 9 July named set plus the 18229-2…5 / 18284 / 18285 designations that could be confirmed without inventing numbers. Adding those four later is a follow-on; omitting them is deliberate, not a silent “does not exist.”

## Summary

| Section | Rows | ✅ | 🟡 | ⚪ | ⛔ |
|---|---:|---:|---:|---:|---:|
| Programme-boundary | 3 | 0 | 0 | 3 | 0 |
| Document-level deliverables | 11 | 0 | 8 | 3 | 0 |
| **Totals** | **14** | **0** | **8** | **6** | **0** |

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills EN 18286, any prEN, M/613, or the EU AI Act. **No public “fulfills EN 18286.”**

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- EU AI Act workpaper (Art. 9, 12, 14, 15, 17, 40, 43): [`eu-ai-act.md`](./eu-ai-act.md) — last reviewed 2026-05-14 / v0.8.0; this file does not upgrade those ✅ counts
- ISO/IEC 42001 (do not collapse with EN 18286): [`iso-42001.md`](./iso-42001.md)
- ISO/IEC 42006 (certification-body competence, not a JTC 21 deliverable): [`iso-42006.md`](./iso-42006.md)
- JTC 21 milestone post: https://jtc21.eu/significant-milestone-for-european-ai-standardization/
