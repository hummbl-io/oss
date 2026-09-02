# CMMC 2.0 Coverage Matrix — HUMMBL

**Standard**: Cybersecurity Maturity Model Certification (CMMC) Program, 32 CFR Part 170
**Model**: CMMC 2.0 — Level 2 security requirements are identical to NIST SP 800-171 Revision 2 (incorporated by reference, 32 CFR § 170.14)
**Domain list source**: DoD CIO, *CMMC Model Overview* Version 2.13 — 14 domains mapping to NIST SP 800-171 Rev 2 families
**Source**: https://www.ecfr.gov/current/title-32/subtitle-A/chapter-I/subchapter-G/part-170 ; https://dodcio.defense.gov/Portals/0/Documents/CMMC/ModelOverviewv2.pdf
**Last reviewed**: 2026-08-31
**Reviewer**: documentation pass per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md) and LANDING-013
**HUMMBL version mapped against**: hummbl-governance v1.4.2 (`pyproject.toml` on this tree)

## Boundary disclaimer (statutory / assessment)

HUMMBL does **not** claim CMMC certification, CMMC Status (Level 1 Self / Level 2 Self / Level 2 C3PAO / Level 3 DIBCAC), FedRAMP authorization, or government approval.

See [`docs/artifacts/EVIDENCE_PACKET_il4_il5_air_gap_claim.md`](../../../../../docs/artifacts/EVIDENCE_PACKET_il4_il5_air_gap_claim.md): this packet “does not claim HUMMBL is authorized for IL4 or IL5 workloads, FedRAMP authorized, CMMC certified, or approved by a government assessor.” The defense/federal public page already disclaims CMMC certification.

CMMC assesses an **Organization Seeking Assessment (OSA)** that processes, stores, or transmits FCI or CUI on contractor information systems. HUMMBL is an in-process Python library. A customer may use primitives as evidence substrate; the CMMC assessment boundary is the customer's system.

**No public “fulfills CMMC.”**

## Practice-ID honesty

Public CMMC Level 2 is the NIST SP 800-171 Rev 2 practice set (110 practices). Official practice numbers use the `3.x.y` family style (for example AC.L2-3.1.1 in CMMC assessment-guide notation). **This first matrix does not invent `3.1.1`-style numbers.** Official PDFs were fetched this session for the **14 domain abbreviations** only. Completeness here = programme rows + one row per public domain ID. Practice-level rows are a follow-on after a verified 800-171/CMMC assessment-guide ID list is copied in-tree.

## Coverage state legend

| Glyph | State | Meaning |
|---|---|---|
| ✅ | Fulfilled | Named HUMMBL primitive implements the control; evidence artifact must be validated before public use |
| 🟡 | Partial | HUMMBL primitive provides part; customer CMMC programme / 800-171 practice implementation completes it. Both parts named. |
| ⚪ | Boundary | Control is organizational, physical, assessment, or otherwise outside what software can implement. |
| ⛔ | Out of scope | Control does not apply to the AI governance platform context (retained for completeness). |

Most rows are Partial or Boundary. **No Fulfilled rows** — a Fulfilled glyph at domain grain would read as a CMMC claim.

## Programme-level rows

| ID | Requirement | HUMMBL coverage | Evidence |
|---|---|---|---|
| 32 CFR Part 170 | CMMC Program: contractors safeguarding FCI/CUI on contractor systems | ⚪ Boundary: statutory programme. HUMMBL is not an OSA and not a C3PAO. | n/a — boundary |
| Level 1 | Basic safeguarding for FCI (FAR 52.204-21) | ⚪ Boundary: contract/FAR clause implementation is customer. | n/a — boundary |
| Level 2 | NIST SP 800-171 Rev 2 practices (self-assessment or C3PAO certification assessment) | ⚪ Boundary: assessment type and CMMC Status are customer/C3PAO. Domain rows below are engineering overlays only. | n/a — boundary |
| Level 3 | Selected NIST SP 800-172 requirements with DoD parameters | ⚪ Boundary: DIBCAC assessment path. No 800-172 enhanced-practice IDs invented here. | n/a — boundary |
| C3PAO / DIBCAC | Third-party or DIBCAC certification assessments | ⚪ Boundary: HUMMBL is not a Certified Third-Party Assessment Organization and not DIBCAC. | n/a — boundary; see evidence packet |

## Domain-level rows (14 public CMMC / 800-171 families)

Abbreviations from *CMMC Model Overview* v2.13. No practice numbers.

| ID | Domain | HUMMBL coverage | Evidence |
|---|---|---|---|
| AC | Access Control | 🟡 Partial: `delegation` (HMAC tokens, `ops_allowed`, resource selectors) + `capability_fence` constrain agent actions. Account management, remote-access architecture, and CUI flow policy are customer 800-171 practices. | `hummbl_governance/delegation.py`, `hummbl_governance/capability_fence.py` |
| AT | Awareness and Training | ⚪ Boundary: workforce training programme is organizational. | n/a — boundary |
| AU | Audit and Accountability | 🟡 Partial: `audit_log` (append-only JSONL) + `coordination_bus` (append-only TSV) provide an evidence log. 800-171 audit review, correlation, retention, and failure-alerting practices are customer. | `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py` |
| CA | Security Assessment | ⚪ Boundary: organizational assessments, plans of action, and CMMC assessment execution are customer/C3PAO. `compliance_mapper` can export engineering evidence; it is not a CMMC assessment. | `hummbl_governance/compliance_mapper.py` |
| CM | Configuration Management | 🟡 Partial: `schema_validator` + change-oriented audit tuples support configuration evidence. Baseline configuration, flaw-remediation cadence, and least-functionality on the OSA system are customer. | `hummbl_governance/schema_validator.py`, `hummbl_governance/audit_log.py` |
| IA | Identification and Authentication | 🟡 Partial: `identity` (agent registry, trust tiers) + `delegation` (token issue/verify/revoke). Human/user IA, MFA, and authenticator management on the OSA system are customer. | `hummbl_governance/identity.py`, `hummbl_governance/delegation.py` |
| IR | Incident Response | 🟡 Partial: `kill_switch` (halt) + `lifecycle` (IR-shaped orchestration) + audit trail. IR plan authorship, testing, and reporting to DoD are customer. | `hummbl_governance/kill_switch.py`, `hummbl_governance/lifecycle.py`, `hummbl_governance/audit_log.py` |
| MA | Maintenance | ⚪ Boundary: system maintenance, tools, and nonlocal maintenance on the OSA system are organizational. | n/a — boundary |
| MP | Media Protection | ⚪ Boundary: media marking, storage, transport, and sanitization are organizational. | n/a — boundary |
| PS | Personnel Security | ⚪ Boundary: screening, termination, and third-party personnel controls are HR/org. | n/a — boundary |
| PE | Physical Protection | ⚪ Boundary: facility physical protection. `physical_governor` is kinematic/pHRI for physical-AI agents, not a PE facility control. | n/a — boundary |
| RA | Risk Assessment | 🟡 Partial: `stride_mapper` records threat categories. Vulnerability scanning, risk-assessment cadence, and risk-register acceptance are customer. | `hummbl_governance/stride_mapper.py` |
| SC | System and Communications Protection | 🟡 Partial: HMAC-signed delegation + append-only bus provide app-layer integrity. Boundary protection, isolation, cryptographic-module, and network practices are customer/infra. | `hummbl_governance/delegation.py`, `hummbl_governance/coordination_bus.py` |
| SI | System and Information Integrity | 🟡 Partial: `output_validator` (malicious/PII/injection content) + `circuit_breaker` (fault isolation). Flaw remediation, malicious-code protection at the OS, and CUI-input restrictions are customer. | `hummbl_governance/output_validator.py`, `hummbl_governance/circuit_breaker.py` |

## Summary

| Section | Rows | ✅ | 🟡 | ⚪ | ⛔ |
|---|---:|---:|---:|---:|---:|
| Programme-level | 5 | 0 | 0 | 5 | 0 |
| Domain-level (14 families) | 14 | 0 | 8 | 6 | 0 |
| **Totals** | **19** | **0** | **8** | **11** | **0** |

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills CMMC, NIST SP 800-171, or DFARS 252.204-7012. Domain rows are overlays, not practice scores. Existing coverage matrices last reviewed 2026-05-14 / v0.8.0 are not upgraded by this file.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Evidence / public-claim boundary: [`docs/artifacts/EVIDENCE_PACKET_il4_il5_air_gap_claim.md`](../../../../../docs/artifacts/EVIDENCE_PACKET_il4_il5_air_gap_claim.md)
- ISO 27001 overlap (logging, access, IR) — see [`iso-27001.md`](./iso-27001.md) (do not treat ISO 27001 rows as CMMC practices)
- NIST CSF 2.0 overlap — see [`nist-csf.md`](./nist-csf.md)
- April 2026 `STANDARDS_CROSSWALK_v0.1` named CMMC at header level; this is the first ADR-001 coverage file
