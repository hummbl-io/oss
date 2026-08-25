# California SB 53 (TFAIA) Coverage Matrix — HUMMBL

**Standard**: Transparency in Frontier Artificial Intelligence Act, California Business and Professions Code Chapter 25.1 (Sections 22757.10-22757.16)
**Effective**: January 1, 2026
**Source**: https://leginfo.legislature.ca.gov/faces/billTextClient.xhtml?bill_id=202520260SB53
**Last reviewed**: 2026-05-14
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not California-licensed counsel and does not provide legal advice on SB 53. The Act is enforced by the Attorney General with civil penalties. Statutory compliance is the customer-organization responsibility. HUMMBL maps technical primitives to the Act's frontier AI framework, safety incident reporting, and whistleblower protection obligations.

## Scope summary

SB 53 applies to "frontier developers" (persons developing frontier models) and "large frontier developers" (frontier developers with >$500M prior-year revenue). It requires written frontier AI frameworks, transparency reports, critical safety incident reporting to the Office of Emergency Services, and whistleblower protections for covered employees. The Act targets models with catastrophic-risk capabilities.

## Obligations + coverage

### Frontier AI framework requirements (§ 22757.12)

| Obligation | Coverage | Evidence |
|---|---|---|
| Write, implement, comply with, and publish frontier AI framework | ✅ Safety-framework template + compliance-report generator (cross-ref NIST AI RMF GOVERN) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Incorporate national, international, and industry-consensus standards | ✅ Framework-alignment tuple (cross-ref NIST AI RMF, ISO 42001) | `hummbl_governance/compliance_mapper.py` |
| Define and assess catastrophic-risk thresholds (may include multiple-tiered thresholds) | ✅ Risk-threshold-definition tuple + risk-assessment primitive | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Apply mitigations based on assessment results | ✅ Risk-treatment tuple + mitigation-tracking primitive | `hummbl_governance/audit_log.py` |
| Review assessments and mitigation adequacy before deployment | ✅ Pre-deployment-review tuple + lifecycle gate | `hummbl_governance/audit_log.py`, `hummbl_governance/lifecycle.py` |
| Use third parties to assess catastrophic risks and mitigation effectiveness | 🟡 Partial: third-party-assessment-evidence tuple; third-party engagement is org task | `hummbl_governance/audit_log.py` |
| Define criteria for framework updates and substantial modification disclosures | ✅ Modification-trigger tuple + change-tracking primitive | `hummbl_governance/audit_log.py`, `hummbl_governance/lifecycle.py` |
| Describe cybersecurity practices to secure frontier models | ✅ Cybersecurity-controls tuple (cross-ref ISO 27001, NIST CSF PR) | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Describe approach to identifying and responding to critical safety incidents | ✅ Incident-response tuple + kill-switch halt + audit-trail (cross-ref NIST CSF RS) | `hummbl_governance/kill_switch.py`, `hummbl_governance/audit_log.py` |
| Describe governance practices to ensure framework implementation | ✅ Governance-practice tuple + governance-bus audit log | `hummbl_governance/coordination_bus.py`, `hummbl_governance/audit_log.py` |
| Assess and manage catastrophic risk from internal use (including oversight circumvention) | ✅ Internal-use-risk tuple + oversight-monitoring primitive | `hummbl_governance/audit_log.py`, `hummbl_governance/identity.py` |
| Annual review and update of frontier AI framework | ✅ Annual-review-scheduling primitive + lifecycle trigger | `hummbl_governance/lifecycle.py`, `hummbl_governance/audit_log.py` |
| Material modification publication within 30 days with justification | ✅ Modification-disclosure tuple + 30-day-SLA primitive | `hummbl_governance/audit_log.py`, `hummbl_governance/lifecycle.py` |

### Transparency report requirements (§ 22757.12(c))

| Obligation | Coverage | Evidence |
|---|---|---|
| Publish transparency report before/concurrently with deploying new or modified frontier model | 🟡 Partial: transparency-report generator produces content; website publication is org task | `hummbl_governance/compliance_mapper.py` |
| Transparency report must contain capabilities, safety testing, and mitigations information | ✅ Report-content tuple with all required fields | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |

### Catastrophic risk assessment reporting (§ 22757.12(d))

| Obligation | Coverage | Evidence |
|---|---|---|
| Transmit catastrophic risk summaries to Office of Emergency Services per safety protocol schedule | 🟡 Partial: risk-summary generator produces content; transmission is org task | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |

### Critical safety incident reporting (§ 22757.13)

| Obligation | Coverage | Evidence |
|---|---|---|
| Report critical safety incidents to OES within 15 days of discovery | ✅ Incident-report tuple + 15-day-SLA primitive | `hummbl_governance/audit_log.py`, `hummbl_governance/lifecycle.py` |
| Report imminent-risk incidents (death/serious bodily injury) within 24 hours | ✅ Emergency-incident-report tuple + 24-hour-SLA primitive + kill-switch emergency halt | `hummbl_governance/kill_switch.py`, `hummbl_governance/audit_log.py` |
| OES to establish reporting mechanism for frontier developers and public | ⚪ Boundary: government-reporting infrastructure is institutional | |
| OES to establish confidential submission mechanism for catastrophic risk assessments | ⚪ Boundary: government-infrastructure is institutional | |
| OES to review incident reports and transmit to authorities as appropriate | ⚪ Boundary: government-review authority is institutional | |
| Critical safety incident reports exempt from California Public Records Act | ⚪ Boundary: public-records exemption is legal determination | |
| OES annual anonymized incident report beginning January 1, 2027 | ⚪ Boundary: government-reporting is institutional | |
| OES may designate federal laws meeting conditions for compliance option | ⚪ Boundary: government-regulatory authority is institutional | |
| Frontier developer may declare federal-compliance intent to OES | 🟡 Partial: federal-compliance-declaration tuple + declaration-tracking primitive; actual filing to OES is org task | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |

### Department of Technology assessments (§ 22757.14)

| Obligation | Coverage | Evidence |
|---|---|---|
| Annual technology assessment of definitions and developments beginning January 1, 2027 | ⚪ Boundary: government-assessment is institutional | |
| Submit assessment recommendations to Legislature | ⚪ Boundary: government-legislative reporting is institutional | |
| AG annual anonymized whistleblower report beginning January 1, 2027 | ⚪ Boundary: government-reporting is institutional | |

### Enforcement (§ 22757.15)

| Obligation | Coverage | Evidence |
|---|---|---|
| Civil penalties enforced by AG for failure to publish/transmit, false statements, or whistleblower violations | ⚪ Boundary: civil-penalty exposure is legal | |

### Whistleblower protections (Lab. Code § 1107-1107.2)

| Obligation | Coverage | Evidence |
|---|---|---|
| Prohibit retaliation against covered employees for disclosing catastrophic risks or violations | 🟡 Partial: disclosure-audit tuple + whistleblower-identity protection; actual employment-law enforcement is org task | `hummbl_governance/audit_log.py`, `hummbl_governance/identity.py` |
| Prohibit policies/contracts preventing protected disclosures | 🟡 Partial: policy-compliance tuple + disclosure-policy-tracking primitive; actual employment-policy enforcement is org task | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Provide anonymous internal disclosure process for covered employees | ✅ Anonymous-disclosure-channel tuple + audit-log with identity protection | `hummbl_governance/audit_log.py`, `hummbl_governance/identity.py` |
| Monthly update to whistleblowers on investigation status and actions taken | ✅ Status-update-scheduling primitive + notification tuple | `hummbl_governance/audit_log.py`, `hummbl_governance/lifecycle.py` |
| Burden of proof on developer (clear and convincing) in retaliation cases | 🟡 Partial: evidence-trail primitive + disclosure-audit log; legal-evidentiary standard application is judicial | `hummbl_governance/audit_log.py` |
| Attorney's fees for successful whistleblower plaintiffs | ⚪ Boundary: fee award is judicial | |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| Frontier AI framework (§ 22757.12) | 13 | 11 | 1 | 1 |
| Transparency report (§ 22757.12(c)) | 2 | 1 | 1 | 0 |
| Catastrophic risk reporting (§ 22757.12(d)) | 1 | 0 | 1 | 0 |
| Critical safety incident reporting (§ 22757.13) | 9 | 3 | 1 | 5 |
| Technology assessments (§ 22757.14) | 3 | 0 | 0 | 3 |
| Enforcement (§ 22757.15) | 1 | 0 | 0 | 1 |
| Whistleblower protections (Lab. Code) | 6 | 2 | 3 | 1 |
| **Totals** | **35** | **17** | **7** | **11** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Frontier AI framework overlaps NIST AI RMF GOVERN — see [`nist-ai-rmf.md`](./nist-ai-rmf.md)
- Incident response overlaps NIST CSF RS — see [`nist-csf.md`](./nist-csf.md)
- Cybersecurity overlaps ISO 27001 — see [`iso-27001.md`](./iso-27001.md)
- Kill switch for emergency incidents — see [`stride.md`](./stride.md) D — Denial of Service
