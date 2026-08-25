# South Korea AI Basic Act Coverage Matrix — HUMMBL

**Standard**: Act on the Development of Artificial Intelligence and Establishment of Trust (AI Basic Act), Act No. 20676
**Effective**: January 22, 2026
**Source**: https://elaw.klri.re.kr/eng_service/lawViewTitle.do?hseq=71019
**Last reviewed**: 2026-05-14
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not Korean legal counsel and does not provide legal advice on the AI Basic Act. The Act distinguishes "AI business operators" (developers and utilization operators), "high-impact AI," and systems exceeding a 10²⁶ FLOPs compute threshold. Statutory compliance is the customer-organization responsibility. HUMMBL maps technical primitives to the Act's transparency, safety, risk-management, and human-oversight obligations.

## Scope summary

The Act applies to AI business operators providing products or services in South Korea, including foreign operators meeting revenue/user thresholds (KRW 1T total revenue, KRW 10B AI revenue, or 1M+ daily Korean users). High-impact AI covers 11 sectors including healthcare, finance, education, public services, and criminal justice. Compute-threshold systems (≥10²⁶ FLOPs) carry additional safety obligations.

## Obligations + coverage

### Transparency obligations (Art. 31)

| Obligation | Coverage | Evidence |
|---|---|---|
| Prior AI use notification to users for high-impact AI or generative AI | ✅ Transparency-notification primitive (cross-ref EU AI Act Art. 50, Colorado § 6-1-1704) | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Generative AI output labeling when outputs may be difficult to distinguish from non-AI content | ✅ Provenance-labeling tuple type + output-validation gate | `hummbl_governance/output_validator.py`, `hummbl_governance/audit_log.py` |
| Realistic content (deepfake) labeling with clear AI-generation indicators | ✅ Content-authenticity tuple + labeling primitive (cross-ref EU AI Act Art. 50(2)) | `hummbl_governance/output_validator.py` |

### Safety obligations for high-performance AI (Art. 32)

| Obligation | Coverage | Evidence |
|---|---|---|
| Implement safety measures for compute-threshold systems (≥10²⁶ FLOPs) | ✅ Kill-switch 4-mode halt + circuit-breaker fast-fail + cost-governor budget enforcement | `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py`, `hummbl_governance/cost_governor.py` |
| Establish risk management system to monitor and respond to AI safety accidents | ✅ Risk-mgmt program substrate: INTENT + adverse-event tuples + risk-treatment tuples (cross-ref NIST AI RMF, EU AI Act Art. 9) | `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py` |
| Identify, assess, and mitigate risks for compute-threshold systems | ✅ Risk-identification + assessment + treatment tuple types | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Report implementation outcomes of risk management to MSIT | 🟡 Partial: compliance-report generator produces the report; submission is org task | `hummbl_governance/compliance_mapper.py` |

### High-impact AI obligations (Art. 34)

| Obligation | Coverage | Evidence |
|---|---|---|
| Conduct prior review to determine whether AI constitutes high-impact AI | ✅ Impact-assessment template + classification tuple | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Formulate and operate risk management plan for high-impact AI | ✅ Risk-mgmt plan substrate with iterative identify+document+mitigate cycle | `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py` |
| Formulate and implement explanation plan (results, criteria, training data overview) | ✅ Explanation-disclosure generator (cross-ref EU AI Act Art. 13, Colorado deployer disclosure) | `hummbl_governance/compliance_mapper.py` |
| Formulate and operate user protection plan for high-impact AI | ✅ User-protection tuple + adverse-event monitoring | `hummbl_governance/audit_log.py` |
| Assign human management and oversight of high-impact AI, including named contact person | ✅ Human-oversight delegation token + contact-registration tuple (cross-ref EU AI Act Art. 14) | `hummbl_governance/delegation.py`, `hummbl_governance/identity.py` |
| Prepare and retain documentation verifying safety and trustworthiness measures for 5 years | ✅ Immutable audit-log retention + documentation-retention tuple | `hummbl_governance/audit_log.py` |
| Implement additional measures deliberated by National AI Committee | ⚪ Boundary: government-committee deliberation is organizational, not software-addressable | |
| Publish all high-impact AI measures on operator's website | 🟡 Partial: report generator produces publishable content; website publication is org task | `hummbl_governance/compliance_mapper.py` |

### Impact assessment (Art. 35)

| Obligation | Coverage | Evidence |
|---|---|---|
| Human rights impact assessment for high-impact AI (soft obligation — "should endeavor") | ✅ Impact-assessment template with human-rights component (cross-ref EU AI Act Art. 27 FRIA) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Government agencies must prioritize impact-assessed high-impact AI systems | 🟡 Partial: impact-assessment tuples + compliance-mapper generate structured impact assessment evidence for high-impact AI systems; government procurement preference policy remains organizational | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |

### Domestic representative (Art. 36)

| Obligation | Coverage | Evidence |
|---|---|---|
| Foreign operators meeting thresholds must designate domestic representative in writing and report to MSIT | ⚪ Boundary: legal-entity registration is organizational, not software-addressable | |
| Domestic representative is legally responsible for implementation reporting, confirmation requests, and safety measure support | ⚪ Boundary: legal-responsibility designation is organizational | |

### Extraterritorial scope and government cooperation (Art. 4, Art. 40)

| Obligation | Coverage | Evidence |
|---|---|---|
| Extraterritorial application — conduct outside Korea with domestic impact is covered | ⚪ Boundary: jurisdictional scope is legal determination | |
| Cooperate with government inspections and fact-finding investigations | 🟡 Partial: audit-log export + compliance-report generator supports inspection; cooperation act is org task | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Comply with MSIT corrective orders for transparency, safety, or reliability violations | 🟡 Partial: kill-switch + circuit-breaker provide corrective-action primitives for immediate response to regulatory orders; regulatory-order compliance process and MSIT reporting remain organizational | `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py` |

### Penalties (Arts. 42–43)

| Obligation | Coverage | Evidence |
|---|---|---|
| Criminal penalty (up to 3 years imprisonment or KRW 30M fine) for confidentiality breach by Committee members | ⚪ Boundary: criminal liability is legal, not software-addressable | |
| Administrative fine (up to KRW 30M) for failure to provide prior AI use notification | ⚪ Boundary: administrative-fine exposure is legal | |
| Administrative fine (up to KRW 30M) for failure to designate domestic representative | ⚪ Boundary: administrative-fine exposure is legal | |
| Administrative fine (up to KRW 30M) for noncompliance with suspension or corrective orders | ⚪ Boundary: administrative-fine exposure is legal | |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| Transparency (Art. 31) | 3 | 3 | 0 | 0 |
| Safety — high-performance AI (Art. 32) | 4 | 3 | 1 | 0 |
| High-impact AI (Art. 34) | 8 | 6 | 1 | 1 |
| Impact assessment (Art. 35) | 2 | 1 | 0 | 1 |
| Domestic representative (Art. 36) | 2 | 0 | 0 | 2 |
| Extraterritorial + cooperation (Arts. 4, 40) | 3 | 0 | 1 | 2 |
| Penalties (Arts. 42–43) | 4 | 0 | 0 | 4 |
| **Totals** | **26** | **13** | **3** | **10** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Transparency overlaps EU AI Act Art. 50 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Risk management overlaps NIST AI RMF MEASURE — see [`nist-ai-rmf.md`](./nist-ai-rmf.md)
- Human oversight overlaps EU AI Act Art. 14 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Impact assessment overlaps EU AI Act Art. 27 (FRIA) — see [`eu-ai-act.md`](./eu-ai-act.md)
