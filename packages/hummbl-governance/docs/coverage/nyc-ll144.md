# NYC Local Law 144 (AEDT) Coverage Matrix — HUMMBL

**Standard**: NYC Local Law 144 of 2021 — Automated Employment Decision Tools (AEDT)
**Effective**: July 5, 2023 (enforcement began)
**Source**: https://www1.nyc.gov/site/dca/about/automated-employment-decision-tools.page
**Last reviewed**: 2026-05-14
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v1.2.2

## Boundary disclaimer

HUMMBL is **not** a bias-audit firm and does not perform the independent bias audit required by Local Law 144. The audit must be performed by an "independent auditor" — a person/group exercising objective + impartial judgment. This matrix maps HUMMBL primitives to the law's notice and audit-evidence obligations.

## Scope summary

Local Law 144 applies to employers + employment agencies using "automated employment decision tools" (AEDTs) for hiring or promotion decisions of candidates for employment in NYC. Key obligations: independent bias audit, public summary of audit results, candidate notice (10 business days in advance), data + retention requirements.

## Obligations + coverage

### Bias audit (§ 20-870(b))

| Obligation | Coverage | Evidence |
|---|---|---|
| AEDT shall not be used unless bias audit conducted within 1 year prior | 🟡 Partial: audit-cadence tuple + scheduling primitive; independent audit engagement is org responsibility | |
| Audit summary made publicly available on employer/agency website | 🟡 Partial: audit-result tuple + publication primitive; publication action is org task | |
| Audit must include: selection rates per category, impact ratios per category, number of individuals assessed | ✅ Selection-rate + impact-ratio + assessment-count metrics computed from governance bus | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Audit summary must include date of audit, source + explanation of data used, categories assessed | ✅ Audit-metadata tuple captures all 3 fields | `hummbl_governance/audit_log.py`, `hummbl_governance/schema_validator.py` |

### Candidate notice (§ 20-870(c))

| Obligation | Coverage | Evidence |
|---|---|---|
| Notice to candidate residing in NYC at least 10 business days before AEDT use — that AEDT will be used + job qualifications + characteristics AEDT uses | ✅ Pre-AEDT notification primitive + 10-business-day SLA tracker | `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py` |
| Allow candidate to request alternative selection process or accommodation | ✅ Alternative-process tuple + accommodation request primitive | `hummbl_governance/audit_log.py`, `hummbl_governance/schema_validator.py` |
| Information about data type + source + retention policy | ✅ Data-disclosure generator | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |

### Audit data + retention

| Obligation | Coverage | Evidence |
|---|---|---|
| Employer/agency must retain audit data for period required for re-auditing | ✅ Append-only governance bus + retention policy ≥ 1 year (audit cycle) | `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py` |

### Penalties

| Provision | Coverage | Evidence |
|---|---|---|
| Civil penalty up to $500 per first violation per day, $1,500 per subsequent | ⚪ Boundary: penalty regime | |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---|---|---|---|
| Bias audit | 4 | 2 | 2 | 0 |
| Candidate notice | 3 | 3 | 0 | 0 |
| Data + retention | 1 | 1 | 0 | 0 |
| Penalties | 1 | 0 | 0 | 1 |
| **Totals** | **9** | **6** | **2** | **1** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Algorithmic-discrimination overlap with [`colorado-ai-act.md`](./colorado-ai-act.md)
- Employment-context overlap with EU AI Act Annex III(4) high-risk
