# Colorado AI Act (SB 24-205) Coverage Matrix — HUMMBL

**Standard**: Colorado Senate Bill 24-205 — Consumer Protections for Interactions with Artificial Intelligence Systems (signed May 17, 2024)
**Effective**: February 1, 2026
**Source**: https://leg.colorado.gov/bills/sb24-205
**Last reviewed**: 2026-05-14
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v1.2.2

## Boundary disclaimer

HUMMBL is **not** Colorado-licensed counsel and does not provide legal advice on the Colorado AI Act. The Act distinguishes "developer" and "deployer" of high-risk AI systems; obligations differ. Statutory compliance is the customer-organization (developer or deployer) responsibility. HUMMBL maps technical primitives to the Act's algorithmic-discrimination and consumer-notice obligations.

## Scope summary

The Act applies to "high-risk artificial intelligence systems" — defined as systems making or being a substantial factor in making consequential decisions (employment, education, financial/lending, essential government services, healthcare, housing, insurance, legal services). Obligations split between developers (those who develop or substantially modify) and deployers (those who use).

## Obligations + coverage

### Developer obligations (§ 6-1-1702)

| Obligation | Coverage | Evidence |
|---|---|---|
| Duty of reasonable care to avoid algorithmic discrimination | ✅ Algorithmic-discrimination-detection primitives + bias-evaluation tuples (cross-ref EU AI Act Art. 9, NIST AI RMF MS-2.11) | `hummbl_governance/audit_log.py`, `hummbl_governance/schema_validator.py` |
| Provide deployers with statement disclosing intended uses, known/foreseeable limitations, performance evaluations, data used to train | ✅ Developer-disclosure-statement generator (cross-ref EU AI Act Art. 13) | `hummbl_governance/compliance_mapper.py` |
| Disclose to deployers known/foreseeable algorithmic discrimination risks | ✅ Risk-disclosure tuple type | `hummbl_governance/audit_log.py` |
| Make available documentation needed to complete impact assessment | ✅ Impact-assessment evidence bundle (cross-ref Colorado deployer obligations below) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Public statement summarizing types of high-risk AI systems developed | 🟡 Partial: public-statement generator from system-inventory tuples; publication is org task | |
| Disclose to attorney general + known deployers within 90 days when discovers high-risk AI system has caused or is reasonably likely to cause algorithmic discrimination | ✅ Discrimination-event tuple + 90-day notification SLA primitive | `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py` |

### Deployer obligations (§ 6-1-1703)

| Obligation | Coverage | Evidence |
|---|---|---|
| Duty of reasonable care to avoid algorithmic discrimination | ✅ Same primitives as developer | `hummbl_governance/audit_log.py`, `hummbl_governance/schema_validator.py` |
| Implement risk-management policy + program — iterative, identify+document+mitigate known/foreseeable risks | ✅ Risk-mgmt program substrate: `INTENT` + adverse-event tuples + risk-treatment tuples + monitoring; risk-register integration per Krineia connector spec (cross-ref NIST AI RMF + EU AI Act Art. 9) | `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py` |
| Complete impact assessment annually + within 90 days after intentional + substantial modification | ✅ Impact-assessment template + annual + modification-triggered scheduling primitive | `hummbl_governance/audit_log.py`, `hummbl_governance/lifecycle.py` |
| Specific impact-assessment contents — purpose, intended use cases, deployment context, benefits, analysis of risks, transparency measures, post-deployment monitoring | ✅ All 7 components captured as tuple-types; assessment generator produces complete document | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Notify consumer of high-risk AI system use before/at time of consequential decision | ✅ Pre-decision notification primitive | `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py` |
| Provide consumer with statement disclosing — purpose, decision basis, principal factors, sources, right to opt out (where applicable) | ✅ Consumer-disclosure generator | `hummbl_governance/compliance_mapper.py` |
| Provide opportunity to correct incorrect personal data | ✅ Rectification tuple (cross-ref GDPR Art. 16) | `hummbl_governance/audit_log.py` |
| Provide opportunity to appeal adverse consequential decision to human reviewer | ✅ Appeal tuple + human-review delegation | `hummbl_governance/audit_log.py`, `hummbl_governance/delegation.py` |
| Public statement summarizing types of high-risk AI systems deployed | 🟡 Partial: same as developer obligation | |
| Disclose to attorney general within 90 days of discovering high-risk AI system has caused algorithmic discrimination | ✅ Same 90-day SLA primitive | `hummbl_governance/audit_log.py`, `hummbl_governance/coordination_bus.py` |

### Consumer-facing transparency (§ 6-1-1704)

| Obligation | Coverage | Evidence |
|---|---|---|
| AI system interacting with consumer shall disclose AI involvement (unless obvious) | ✅ Transparency-notification primitive (cross-ref EU AI Act Art. 50) | `hummbl_governance/audit_log.py` |

### Affirmative defense + safe harbor

| Provision | Coverage | Evidence |
|---|---|---|
| Affirmative defense for developers + deployers using nationally/internationally recognized risk-management framework (e.g., NIST AI RMF) | ✅ This very matrix + NIST AI RMF coverage matrix = framework adoption evidence; governance bus = continuous compliance demonstration | `docs/coverage/nist-ai-rmf.md`, `hummbl_governance/coordination_bus.py` |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---|---|---|---|
| Developer (§ 6-1-1702) | 6 | 5 | 1 | 0 |
| Deployer (§ 6-1-1703) | 10 | 9 | 1 | 0 |
| Consumer transparency (§ 6-1-1704) | 1 | 1 | 0 | 0 |
| Affirmative defense framework | 1 | 1 | 0 | 0 |
| **Totals** | **18** | **16** | **2** | **0** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Algorithmic-discrimination primitives cross-ref [`eu-ai-act.md`](./eu-ai-act.md) Art. 9 + [`nist-ai-rmf.md`](./nist-ai-rmf.md) MEASURE
- Impact-assessment overlaps EU AI Act Art. 27 (FRIA)
