# California AB 2013 (Training Data Transparency) Coverage Matrix — HUMMBL

**Standard**: Generative Artificial Intelligence: Training Data Transparency, California Civil Code Title 15.2 (Sections 3110-3111)
**Effective**: January 1, 2026
**Source**: https://leginfo.legislature.ca.gov/faces/billTextClient.xhtml?bill_id=202320240AB2013
**Last reviewed**: 2026-05-14
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not California-licensed counsel and does not provide legal advice on AB 2013. The Act is enforceable under the California Unfair Competition Law (Bus. & Prof. Code § 17200) with AG enforcement and private right of action. Statutory compliance is the customer-organization responsibility. HUMMBL maps technical primitives to the Act's training-data documentation and disclosure obligations.

## Scope summary

AB 2013 applies to developers of GenAI systems or services made publicly available to Californians. It requires public posting of training data documentation on the developer's website, covering data sources, dataset characteristics, personal information inclusion, processing methods, and collection timeframes. Documentation must be posted before system release and updated for substantial modifications.

## Obligations + coverage

### Training data documentation requirements (§ 3111)

| Obligation | Coverage | Evidence |
|---|---|---|
| Post training data documentation on developer website before public release | 🟡 Partial: training-data-documentation generator produces the content; website posting is org task | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Document sources or owners of datasets used | ✅ Data-source-attribution tuple + provenance-tracking primitive | `hummbl_governance/audit_log.py` |
| Describe how datasets further the intended purpose of the AI system | ✅ Purpose-alignment documentation tuple | `hummbl_governance/compliance_mapper.py` |
| Document number of data points (general ranges, estimated for dynamic datasets) | ✅ Dataset-cardinality tuple with range support | `hummbl_governance/audit_log.py` |
| Describe types of data points within datasets | ✅ Data-type-classification tuple + schema-validation primitive | `hummbl_governance/schema_validator.py`, `hummbl_governance/audit_log.py` |
| Document copyright, trademark, or patent status of datasets | ✅ IP-status-attribution tuple | `hummbl_governance/audit_log.py` |
| Document whether datasets were purchased or licensed | ✅ Data-license-status tuple | `hummbl_governance/audit_log.py` |
| Document whether datasets include personal information (CCPA § 1798.140(v)) | ✅ PII-classification tuple + data-classification primitive (cross-ref GDPR Art. 9) | `hummbl_governance/schema_validator.py`, `hummbl_governance/audit_log.py` |
| Document whether datasets include aggregate consumer information (CCPA § 1798.140(b)) | ✅ Aggregate-data-classification tuple | `hummbl_governance/audit_log.py` |
| Document data cleaning, processing, or other modification (including intended purpose) | ✅ Data-processing-record tuple + lineage-tracking primitive | `hummbl_governance/audit_log.py` |
| Document time period during which data was collected (including ongoing notice) | ✅ Data-collection-timeframe tuple | `hummbl_governance/audit_log.py` |
| Document dates datasets were first used during development | ✅ First-use-date tuple + lifecycle-tracking primitive | `hummbl_governance/audit_log.py`, `hummbl_governance/lifecycle.py` |
| Document whether datasets were/will be distributed or posted, and terms | ✅ Data-distribution-record tuple | `hummbl_governance/audit_log.py` |
| Estimation methods allowed when information not reasonably available — describe methods and explain gaps | ✅ Estimation-methodology tuple + documentation-gap-record | `hummbl_governance/compliance_mapper.py` |

### Exemptions (§ 3111(b))

| Obligation | Coverage | Evidence |
|---|---|---|
| Exemption for national security, law enforcement, or public safety government systems | ⚪ Boundary: exemption applicability is legal determination | |
| Exemption for internal government operations (not public-facing) | ⚪ Boundary: exemption applicability is legal determination | |
| Exemption for healthcare provider internal operations (not public-facing) | ⚪ Boundary: exemption applicability is legal determination | |

### Enforcement

| Obligation | Coverage | Evidence |
|---|---|---|
| Enforcement under California Unfair Competition Law (Bus. & Prof. Code § 17200) — AG + private right of action | ⚪ Boundary: legal-enforcement mechanism is institutional | |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| Training data documentation (§ 3111) | 14 | 13 | 1 | 0 |
| Exemptions (§ 3111(b)) | 3 | 0 | 0 | 3 |
| Enforcement | 1 | 0 | 0 | 1 |
| **Totals** | **18** | **13** | **1** | **4** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Data documentation overlaps EU AI Act Art. 10 (data governance) — see [`eu-ai-act.md`](./eu-ai-act.md)
- PII classification overlaps GDPR Art. 9 — see [`gdpr.md`](./gdpr.md)
- Data governance overlaps ISO 27001 A.5.12-A.5.13 — see [`iso-27001.md`](./iso-27001.md)
