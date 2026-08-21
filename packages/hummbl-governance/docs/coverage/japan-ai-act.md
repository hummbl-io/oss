# Japan AI Act (Act No. 53/2025) Coverage Matrix — HUMMBL

**Standard**: Act on Promotion of Research and Development, and Utilization of Artificial Intelligence-related Technology (人工知能関連技術の研究開発及び活用の推進に関する法律), Act No. 53 of 2025
**Effective**: 2025 (promulgated May 28, 2025)
**Source**: https://www.japaneselawtranslation.go.jp/en/laws/view/5066
**Last reviewed**: 2026-05-14
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not Japanese legal counsel and does not provide legal advice on the Japan AI Act. The Act is a soft-law promotion framework with NO mandatory technical obligations on AI developers/providers and NO legal penalties for non-compliance. The only binding business obligation is cooperation with government measures. HUMMBL maps technical primitives to the voluntary guidelines and government-cooperation obligations that the Act establishes.

## Scope summary

The Japan AI Act is fundamentally different from the EU AI Act or US state AI laws — it is a **promotion framework**, not a regulatory regime. It establishes the AI Strategic Headquarters under the Cabinet, formulates a Basic Plan for AI promotion, and promotes R&D, infrastructure, guidelines, human resources, education, surveys, and international cooperation. The only binding obligation on AI business operators is to cooperate with government measures. All technical AI governance is through voluntary guidelines (AI Guidelines for Business v1.1).

## Obligations + coverage

### Business operator obligations (Art. 7)

| Obligation | Coverage | Evidence |
|---|---|---|
| Cooperate with national government measures implemented under Art. 4 (binding) | 🟡 Partial: audit-log query + compliance-evidence export + tamper-evident receipts + evidence grading support government cooperation; cooperation act (receiving inquiries, deciding what to share, sending responses, implementing recommendations) is org task | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py`, `hummbl_governance/kernel/receipt_engine.py`, `hummbl_governance/kernel/evidence_engine.py` |
| Cooperate with local government measures implemented under Art. 5 (binding) | 🟡 Partial: same primitives as national cooperation; cooperation act is org task | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py`, `hummbl_governance/kernel/receipt_engine.py`, `hummbl_governance/kernel/evidence_engine.py` |
| Endeavor to enhance business efficiency and create new industries through AI utilization (soft) | ⚪ Boundary: voluntary business-strategy obligation is organizational | |

### Government responsibilities (Arts. 10-19)

| Obligation | Coverage | Evidence |
|---|---|---|
| Establish AI Strategic Headquarters under the Cabinet (Art. 19) | ⚪ Boundary: government-institution creation is institutional | |
| Formulate Basic Plan for AI promotion (Art. 18) | ⚪ Boundary: government-planning is institutional | |
| Promote R&D of AI-related technology (Art. 10) | ⚪ Boundary: government-R&D funding is institutional | |
| Develop infrastructure and datasets for AI (Art. 11) | ⚪ Boundary: government-infrastructure is institutional | |
| Establish guidelines in accordance with international norms (Art. 13) | ⚪ Boundary: government-guideline development is institutional | |
| Secure and train personnel with AI expertise (Art. 14) | ⚪ Boundary: government-workforce development is institutional | |
| Promote AI education (Art. 15) | ⚪ Boundary: government-education policy is institutional | |
| Conduct surveys and research on AI implementation and human rights impacts (Art. 16) | ⚪ Boundary: government-research is institutional | |
| Promote international cooperation and norm-setting participation (Art. 17) | ⚪ Boundary: government-foreign-policy is institutional | |
| Issue administrative guidance or public warnings for malicious AI use (no penalties) | ⚪ Boundary: government-administrative authority is institutional | |

### Research institution obligations (Art. 6)

| Obligation | Coverage | Evidence |
|---|---|---|
| Endeavor to actively conduct AI R&D, disseminate results, train personnel (soft) | ⚪ Boundary: voluntary research obligation is organizational | |
| Cooperate with national and local government measures (soft) | 🟡 Partial: audit-log query + compliance-evidence export + tamper-evident receipts + evidence grading support government cooperation; cooperation act is org task | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py`, `hummbl_governance/kernel/receipt_engine.py`, `hummbl_governance/kernel/evidence_engine.py` |
| Endeavor interdisciplinary R&D using humanities and natural sciences (soft) | ⚪ Boundary: voluntary research approach is organizational | |

### Local government obligations (Art. 5)

| Obligation | Coverage | Evidence |
|---|---|---|
| Formulate and implement autonomous policies leveraging regional characteristics | ⚪ Boundary: local-government policy is institutional | |
| Coordinate with national government under appropriate role division | ⚪ Boundary: inter-governmental coordination is institutional | |

### Citizen obligations (Art. 8)

| Obligation | Coverage | Evidence |
|---|---|---|
| Endeavor to deepen understanding and interest in AI technology (soft) | ⚪ Boundary: voluntary citizen obligation is personal | |
| Cooperate with national and local government measures (soft) | ⚪ Boundary: voluntary citizen cooperation is personal | |

### Extraterritorial scope

| Obligation | Coverage | Evidence |
|---|---|---|
| Coverage of foreign entities (indicated in Diet discussions, not explicit in Act text) | ⚪ Boundary: jurisdictional scope is legal determination | |

### Penalties

| Obligation | Coverage | Evidence |
|---|---|---|
| None — Act contains no legal penalties for business non-compliance | ⚪ Boundary: absence of penalties is legal characteristic | |

### Voluntary guideline alignment (AI Guidelines for Business v1.1)

| Obligation | Coverage | Evidence |
|---|---|---|
| Voluntary adoption of AI governance practices per government guidelines | ✅ Governance-practice implementation + audit-log evidence (cross-ref NIST AI RMF, ISO 42001) | `hummbl_governance/coordination_bus.py`, `hummbl_governance/audit_log.py` |
| Voluntary risk management for AI systems | ✅ Risk-mgmt program substrate (cross-ref NIST AI RMF, EU AI Act Art. 9) | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Voluntary human oversight of AI systems | ✅ Human-oversight delegation token (cross-ref EU AI Act Art. 14) | `hummbl_governance/delegation.py`, `hummbl_governance/identity.py` |
| Voluntary transparency and disclosure | ✅ Transparency-notification primitive (cross-ref EU AI Act Art. 50) | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Voluntary security measures for AI systems | ✅ Kill-switch + circuit-breaker + access-control primitives (cross-ref ISO 27001, NIST CSF) | `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py` |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| Business operator obligations (Art. 7) | 3 | 0 | 2 | 1 |
| Government responsibilities (Arts. 10-19) | 10 | 0 | 0 | 10 |
| Research institution (Art. 6) | 3 | 0 | 1 | 2 |
| Local government (Art. 5) | 2 | 0 | 0 | 2 |
| Citizen obligations (Art. 8) | 2 | 0 | 0 | 2 |
| Extraterritorial scope | 1 | 0 | 0 | 1 |
| Penalties | 1 | 0 | 0 | 1 |
| Voluntary guideline alignment | 5 | 5 | 0 | 0 |
| **Totals** | **27** | **5** | **3** | **19** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Voluntary guidelines align with NIST AI RMF — see [`nist-ai-rmf.md`](./nist-ai-rmf.md)
- Voluntary guidelines align with ISO 42001 — see [`iso-42001.md`](./iso-42001.md)
- Human oversight overlaps EU AI Act Art. 14 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Risk management overlaps EU AI Act Art. 9 — see [`eu-ai-act.md`](./eu-ai-act.md)
