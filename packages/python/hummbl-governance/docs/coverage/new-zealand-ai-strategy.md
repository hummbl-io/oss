# New Zealand AI Strategy 2025 Coverage Matrix — HUMMBL

**Standard**: New Zealand's Strategy for Artificial Intelligence: Investing with confidence
**Effective**: July 8, 2025
**Source**: https://www.mbie.govt.nz/dmsdocument/30888-new-zealands-strategy-for-artificial-intelligence-investing-with-confidence
**Last reviewed**: 2026-06-25
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not New Zealand legal counsel and does not provide legal advice on the AI Strategy or the Responsible AI Guidance for Businesses. The Strategy is a non-binding national policy document framed around the OECD AI Principles, not a statute. The accompanying Responsible AI Guidance for Businesses is explicitly voluntary. The Public Service AI Framework applies to government agencies and is administratively binding within the Public Service. Statutory compliance with underlying laws (Privacy Act 2020, Human Rights Act 1993, Bill of Rights Act 1990, Copyright Act 1994, Public Records Act 2005, Treaty of Waitangi obligations) is the customer-organization responsibility. HUMMBL maps technical primitives to the Strategy's transparency, safety, oversight, data-governance, and accountability objectives.

## Scope summary

The Strategy applies to all AI use and development in New Zealand, with a deliberate emphasis on private-sector adoption rather than foundational model development. It is framed around the five OECD AI Principles policy recommendations: (1) an enabling policy environment, (2) building Kiwi capacity, (3) fostering the AI ecosystem, (4) cooperating internationally, and (5) strengthening AI R&D. The Responsible AI Guidance for Businesses is a voluntary resource covering governance and accountability, supporting capabilities (procurement, cybersecurity, staff training), stakeholder interactions, data and modelling, and human-in-the-loop decision-making. The Public Service AI Framework extends the Strategy into government agencies with obligations on transparency, safety by design, human oversight, traceability, risk management, and Māori data/Treaty of Waitangi considerations. The Strategy explicitly addresses Māori data sovereignty, recognising mātauranga Māori and Māori data as taonga requiring special protections against misappropriation.

## Obligations + coverage

### Enabling policy environment and responsible AI guidance (OECD Principles 2.3, 1.3)

| Obligation | Coverage | Evidence |
|---|---|---|
| Adopt OECD AI Principles — inclusive growth, human rights, transparency, robustness, accountability | ✅ Cross-framework compliance mapper with OECD principle mapping (cross-ref OECD AI Principles) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Light-touch, principles-based policy aligned with OECD to reduce regulatory uncertainty | ✅ Compliance-mapper framework ingestion + control-to-principle mapping | `hummbl_governance/compliance_mapper.py` |
| Responsible AI Guidance for Businesses — voluntary good-practice resource for trustworthy AI | ✅ Guidance-control ingestion + assessment template (cross-ref NIST AI RMF GOVERN) | `hummbl_governance/compliance_mapper.py` |
| Transparency and responsible disclosure regarding AI systems and outputs | ✅ Provenance-labeling + output-validation gate (cross-ref EU AI Act Art. 50, OECD 1.3) | `hummbl_governance/output_validator.py`, `hummbl_governance/audit_log.py` |

### Safety, security, and risk management (OECD Principle 1.4)

| Obligation | Coverage | Evidence |
|---|---|---|
| Prioritise robustness, security, and safety in AI systems | ✅ Kill-switch 4-mode halt + circuit-breaker fast-fail + capability-fence sandboxing | `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py`, `hummbl_governance/capability_fence.py` |
| Establish systematic risk management approach across the AI system lifecycle | ✅ Risk-mgmt program substrate: risk-identification + assessment + treatment tuples (cross-ref NIST AI RMF MEASURE) | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Cybersecurity — integrity and protection of AI systems, datasets, and model operations | ✅ Capability-fence access control + audit-log tamper-evidence + STRIDE threat mapping | `hummbl_governance/capability_fence.py`, `hummbl_governance/audit_log.py`, `hummbl_governance/stride_mapper.py` |
| Incident response — notice, contain, assess, and respond to security or privacy breaches | 🟡 Partial: audit-log captures adverse events + STRIDE maps threats; containment and notification are org tasks | `hummbl_governance/audit_log.py`, `hummbl_governance/stride_mapper.py` |

### Human oversight and accountability (OECD Principles 1.2, 1.5)

| Obligation | Coverage | Evidence |
|---|---|---|
| Human oversight throughout the AI lifecycle with accountable humans at every stage | ✅ Human-oversight delegation token + lifecycle state machine (cross-ref EU AI Act Art. 14) | `hummbl_governance/delegation.py`, `hummbl_governance/lifecycle.py` |
| Human-in-the-loop decision-making for AI-assisted outputs and decisions | ✅ Delegation-token authority gating + reasoning-engine justification chain | `hummbl_governance/delegation.py`, `hummbl_governance/reasoning.py` |
| Clear lines of accountability, governance, and auditing with human oversight | ✅ Identity-registry accountability + immutable audit-log + compliance-report generator | `hummbl_governance/identity.py`, `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |

### Data governance and Māori data sovereignty (OECD Principles 1.2, 1.3)

| Obligation | Coverage | Evidence |
|---|---|---|
| Training data quality — accurate, complete, lawfully obtained, representative, structured for transparency | ✅ Schema-validation gate + data-quality tuple types in audit log | `hummbl_governance/schema_validator.py`, `hummbl_governance/audit_log.py` |
| Data provenance and recordkeeping — trace origin and processing of training data | ✅ Immutable audit-log provenance chain + Lamport-clock causal ordering | `hummbl_governance/audit_log.py`, `hummbl_governance/lamport_clock.py` |
| Privacy protection for personal information in AI data pipelines | ✅ Capability-fence data-access control + output-validator PII gating | `hummbl_governance/capability_fence.py`, `hummbl_governance/output_validator.py` |
| Māori data sovereignty — protect taonga, prevent misappropriation and misuse of mātauranga Māori | 🟡 Partial: capability-fence access controls + audit-log provenance support data-governance controls; consent, tikanga protocols, and iwi engagement are org tasks | `hummbl_governance/capability_fence.py`, `hummbl_governance/audit_log.py` |
| Bias minimisation — minimise misleading, biased, or discriminatory outputs | ✅ Output-validator bias-detection gate + compliance-mapper fairness assessment (cross-ref OECD 1.2) | `hummbl_governance/output_validator.py`, `hummbl_governance/compliance_mapper.py` |

### Public sector AI leadership (Public Service AI Framework)

| Obligation | Coverage | Evidence |
|---|---|---|
| Transparency — publish AI use online and maintain a register of AI use in agencies | 🟡 Partial: audit-log maintains AI-use register; online publication is org task | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Traceability of data — ensure traceable data across public-sector AI systems | ✅ Audit-log provenance chain + Lamport-clock causal ordering + receipt-engine attestation | `hummbl_governance/audit_log.py`, `hummbl_governance/lamport_clock.py`, `hummbl_governance/kernel/receipt_engine.py` |
| Procurement risk assessment and assurance for AI tools | ✅ Compliance-mapper assessment template + schema-validator for procurement criteria | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/schema_validator.py` |
| Safety by design — minimise risk to individual or national safety under normal use, misuse, or adverse conditions | ✅ Kill-switch + circuit-breaker + capability-fence defence-in-depth (cross-ref NIST AI RMF MANAGE) | `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py`, `hummbl_governance/capability_fence.py` |

### Talent, ecosystem, and international collaboration (OECD Principles 2.2, 2.5)

| Obligation | Coverage | Evidence |
|---|---|---|
| Build AI literacy and workforce capability (tertiary funding, training, AI literacy programmes) | ⚪ Boundary: workforce training and education funding are organizational/governmental policy | |
| Foster AI ecosystem and private-sector adoption (reducing barriers, providing guidance) | ⚪ Boundary: ecosystem building and barrier reduction are governmental policy | |
| International cooperation on AI governance — engage global fora, align with international standards | 🟡 Partial: compliance-mapper cross-framework mapping supports alignment; diplomatic engagement is org task | `hummbl_governance/compliance_mapper.py` |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| Enabling policy + guidance (OECD 2.3, 1.3) | 4 | 4 | 0 | 0 |
| Safety, security, risk mgmt (OECD 1.4) | 4 | 3 | 1 | 0 |
| Human oversight + accountability (OECD 1.2, 1.5) | 3 | 3 | 0 | 0 |
| Data governance + Māori data sovereignty (OECD 1.2, 1.3) | 5 | 4 | 1 | 0 |
| Public sector AI leadership (PSAI Framework) | 4 | 3 | 1 | 0 |
| Talent, ecosystem, international (OECD 2.2, 2.5) | 3 | 0 | 1 | 2 |
| **Totals** | **23** | **17** | **4** | **2** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Strategy is framed around OECD AI Principles — see [`oecd-ai-principles.md`](./oecd-ai-principles.md)
- Transparency overlaps EU AI Act Art. 50 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Risk management overlaps NIST AI RMF GOVERN/MEASURE/MANAGE — see [`nist-ai-rmf.md`](./nist-ai-rmf.md)
- Human oversight overlaps EU AI Act Art. 14 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Cybersecurity overlaps STRIDE threat model — see [`stride.md`](./stride.md)
- Māori data sovereignty overlaps UNESCO AI Ethics cultural diversity principles — see [`unesco-ai-ethics.md`](./unesco-ai-ethics.md)
