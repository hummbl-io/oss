# Texas TRAIGA (HB 149) Coverage Matrix — HUMMBL

**Standard**: Texas Responsible Artificial Intelligence Governance Act, Texas Business & Commerce Code Chapter 552 (Subtitle D)
**Effective**: January 1, 2026
**Source**: https://capitol.texas.gov/tlodocs/89R/billtext/html/HB00149F.htm
**Last reviewed**: 2026-05-14
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not Texas-licensed counsel and does not provide legal advice on TRAIGA. The Act is enforced exclusively by the Attorney General with civil penalties. Statutory compliance is the customer-organization responsibility. HUMMBL maps technical primitives to the Act's prohibited-practices, disclosure, and NIST AI RMF safe-harbor provisions.

## Scope summary

TRAIGA applies to all persons who develop or deploy AI systems in Texas. It prohibits nine categories of harmful AI practices, requires government-agency AI disclosure to consumers, and provides a rebuttable presumption of reasonable care for organizations that implement the NIST AI RMF or equivalent standards. Enforcement is exclusively by the Attorney General.

## Obligations + coverage

### Prohibited practices (§ 552.101)

| Obligation | Coverage | Evidence |
|---|---|---|
| Prohibition on AI manipulation to incite self-harm | ✅ Output-validation gate + kill-switch halt for harmful outputs | `hummbl_governance/output_validator.py`, `hummbl_governance/kill_switch.py` |
| Prohibition on AI manipulation to harm others | ✅ Output-validation gate + harm-prevention tuple | `hummbl_governance/output_validator.py` |
| Prohibition on AI manipulation to encourage criminal activity | ✅ Output-validation gate + prohibited-output tuple | `hummbl_governance/output_validator.py` |
| Prohibition on government social scoring systems | ✅ Discrimination-detection primitives + fairness-evaluation tuples (cross-ref EU AI Act Art. 5) | `hummbl_governance/audit_log.py`, `hummbl_governance/schema_validator.py` |
| Prohibition on government biometric data capture without consent | ✅ Consent-verification tuple + data-minimization primitive (cross-ref GDPR Art. 9) | `hummbl_governance/audit_log.py`, `hummbl_governance/delegation.py` |
| Prohibition on AI designed to infringe constitutional rights | ✅ Rights-impact assessment tuple + kill-switch halt | `hummbl_governance/audit_log.py`, `hummbl_governance/kill_switch.py` |
| Prohibition on AI designed for unlawful discrimination | ✅ Algorithmic-discrimination-detection primitives (cross-ref Colorado SB 24-205, EU AI Act Art. 5) | `hummbl_governance/audit_log.py`, `hummbl_governance/schema_validator.py` |
| Prohibition on AI for child pornography production/distribution | ✅ Prohibited-content-output gate + kill-switch emergency halt | `hummbl_governance/output_validator.py`, `hummbl_governance/kill_switch.py` |
| Prohibition on AI simulating child sexual conduct | ✅ Prohibited-content-output gate + kill-switch emergency halt | `hummbl_governance/output_validator.py`, `hummbl_governance/kill_switch.py` |

### Disclosure requirements (§ 552.102)

| Obligation | Coverage | Evidence |
|---|---|---|
| Government agency AI disclosure to consumers before/at interaction | ✅ Transparency-notification primitive (cross-ref EU AI Act Art. 50, Colorado § 6-1-1704) | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Disclosure must be clear, conspicuous, plain language, no dark patterns | ✅ Disclosure-format-validation tuple + dark-pattern detection | `hummbl_governance/output_validator.py`, `hummbl_governance/compliance_mapper.py` |
| Healthcare AI disclosure timing — by date service first provided (emergency: ASAP) | ✅ Time-bound disclosure-scheduling primitive | `hummbl_governance/audit_log.py`, `hummbl_governance/lifecycle.py` |

### Enforcement provisions (§ 552.103)

| Obligation | Coverage | Evidence |
|---|---|---|
| AG exclusive enforcement authority | ⚪ Boundary: government-enforcement authority is institutional | |
| AG online complaint mechanism | ⚪ Boundary: government-complaint infrastructure is institutional | |
| AG civil investigative demand authority | ⚪ Boundary: government-investigatory power is institutional | |
| AG documentation request authority (system descriptions, training data, inputs, outputs, limitations) | 🟡 Partial: audit-log + compliance-report generator can produce requested documentation; response act is org task | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| AG notice of violation with 30-day cure period for curable violations | ⚪ Boundary: legal-process compliance is organizational | |
| Civil penalties ($10K–$12K curable; $80K–$200K uncurable; $2K–$40K/day continued) | ⚪ Boundary: civil-penalty exposure is legal | |
| Injunctive relief authority | ⚪ Boundary: judicial relief is institutional | |
| State agency enforcement within jurisdiction | ⚪ Boundary: agency enforcement authority is institutional | |
| Local preemption — supersedes political subdivision AI ordinances | ⚪ Boundary: preemption is legal determination | |

### NIST AI RMF safe harbor (§ 552.103)

| Obligation | Coverage | Evidence |
|---|---|---|
| Rebuttable presumption of reasonable care for NIST AI RMF compliance | ✅ This very matrix + NIST AI RMF coverage matrix = framework adoption evidence; governance bus = continuous compliance demonstration | `docs/coverage/nist-ai-rmf.md`, `hummbl_governance/coordination_bus.py` |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| Prohibited practices (§ 552.101) | 9 | 9 | 0 | 0 |
| Disclosure (§ 552.102) | 3 | 3 | 0 | 0 |
| Enforcement (§ 552.103) | 9 | 0 | 1 | 8 |
| NIST AI RMF safe harbor | 1 | 1 | 0 | 0 |
| **Totals** | **22** | **13** | **1** | **8** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- NIST AI RMF safe harbor — see [`nist-ai-rmf.md`](./nist-ai-rmf.md)
- Prohibited practices overlap EU AI Act Art. 5 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Disclosure overlaps EU AI Act Art. 50 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Discrimination detection overlaps Colorado SB 24-205 — see [`colorado-ai-act.md`](./colorado-ai-act.md)
