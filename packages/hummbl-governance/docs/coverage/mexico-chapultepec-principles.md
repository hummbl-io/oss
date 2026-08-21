# Mexico Chapultepec Principles Coverage Matrix — HUMMBL

**Standard**: Principios de Chapultepec — Declaración de ética y buenas prácticas para el uso y desarrollo de la Inteligencia Artificial
**Effective**: January 29, 2026 (non-binding guiding declaration)
**Source**: https://secihti.mx/sala-de-prensa/presentan-declaracion-de-etica-y-buenas-practicas-para-el-uso-y-desarrollo-de-la-ia-en-mexico-secihti-y-atdt/
**Last reviewed**: 2026-06-25
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not Mexican legal counsel and does not provide legal advice on the Chapultepec Principles. The Declaration is a non-binding (no vinculante) ethical guide issued by the Secretaría de Ciencia, Humanidades, Tecnología e Innovación (SECIHTI) and the Agencia de Transformación Digital y Telecomunicaciones (ATDT). It orients public policy, regulation, and institutional instruments across the AI lifecycle; it does not impose statutory obligations. Statutory compliance and voluntary adoption are the customer-organization responsibility. HUMMBL maps technical primitives to the Declaration's ten guiding principles covering human rights, accountability, explainability, collective governance, well-being, impact awareness, strategic sovereignty, education, cultural diversity, and data responsibility.

## Scope summary

The Declaration applies as a voluntary guide to public institutions, government agencies, autonomous bodies, and private and social-sector actors that design, implement, or evaluate AI systems in Mexico. Its ten principles are: (1) AI must expand rights, never reduce them; (2) every AI-supported decision must have human accountability under clear institutional frameworks; (3) if a decision cannot be explained, it must not be automated; (4) AI is best governed through collective decision-making; (5) AI is only valuable if it generates well-being for people; (6) before automating, understand who and what it affects; (7) strategic technology must respond to the country's needs; (8) AI development requires strengthening education and knowledge in the country; (9) AI cannot be alien to the cultural and linguistic diversity of the country; (10) data is a public good that must be handled responsibly. The federal administration plans to open a national debate to determine the legal nature of future regulatory instruments.

## Obligations + coverage

### Human rights and well-being (Principles 1, 5)

| Obligation | Coverage | Evidence |
|---|---|---|
| AI must expand rights, never reduce them — systems must not reproduce or perpetuate inequalities or generate new forms of discrimination | ✅ Bias-detection + adverse-event tuples + fairness-monitoring substrate (cross-ref NIST AI RMF GOVERN, EU AI Act Art. 10) | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| AI must contribute to well-being, inclusion, and social benefit rather than harm | ✅ Reward-monitor alignment to well-being objective + convergence guard on value drift | `hummbl_governance/reward_monitor.py`, `hummbl_governance/convergence_guard.py` |
| Public-sector AI must reduce inequalities and improve access to essential services | 🟡 Partial: governance primitives support equitable-deployment auditing; service-access outcomes are org task | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| AI must not affect human rights if used inappropriately — preventive risk controls | ✅ Kill-switch 4-mode halt + circuit-breaker fast-fail + capability fence on unsafe actions | `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py`, `hummbl_governance/capability_fence.py` |

### Accountability and explainability (Principles 2, 3)

| Obligation | Coverage | Evidence |
|---|---|---|
| Every AI-supported decision must have human accountability under clear institutional frameworks defining who designs, decides, supervises, and answers for effects | ✅ Human-oversight delegation token + identity registry + authority-engine role assignment (cross-ref EU AI Act Art. 14) | `hummbl_governance/delegation.py`, `hummbl_governance/identity.py`, `hummbl_governance/kernel/authority_engine.py` |
| If a decision cannot be explained, it must not be automated — explainability gate before deployment | ✅ Reasoning-engine explanation record + output-validator explainability check + doctrine-engine policy gate | `hummbl_governance/reasoning.py`, `hummbl_governance/output_validator.py`, `hummbl_governance/kernel/doctrine_engine.py` |
| Scientific research and knowledge production must use open and responsible practices allowing verification of results, reproduction of processes, and explicit declaration of AI use | ✅ Immutable audit-log provenance + receipt-engine evidence tuples + provenance-labeling on outputs | `hummbl_governance/audit_log.py`, `hummbl_governance/kernel/receipt_engine.py`, `hummbl_governance/output_validator.py` |
| Institutional frameworks must define supervision and response chains for AI effects | ✅ Delegation-token chain + authority-engine supervision graph + lifecycle state transitions | `hummbl_governance/delegation.py`, `hummbl_governance/kernel/authority_engine.py`, `hummbl_governance/lifecycle.py` |

### Impact awareness and collective governance (Principles 4, 6)

| Obligation | Coverage | Evidence |
|---|---|---|
| Before automating, understand who and what the system affects — prior impact analysis | ✅ Impact-assessment template + stakeholder-affected tuple + compliance-mapper assessment record (cross-ref EU AI Act Art. 27 FRIA) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| AI is best governed through collective decision-making — participatory governance | 🟡 Partial: coordination-bus multi-agent consensus + contract-net negotiation support collective deliberation; human collective process is org task | `hummbl_governance/coordination_bus.py`, `hummbl_governance/contract_net.py` |
| Citizen participation and public-value generation must be central to AI governance | ⚪ Boundary: citizen-participation process design is organizational, not software-addressable | |
| Decisions must reflect diverse stakeholder input and avoid concentration of automated authority | ✅ Convergence guard on multi-agent agreement + lamport-clock ordered deliberation + delegation scope limits | `hummbl_governance/convergence_guard.py`, `hummbl_governance/lamport_clock.py`, `hummbl_governance/delegation.py` |

### Data responsibility (Principle 10)

| Obligation | Coverage | Evidence |
|---|---|---|
| Data is a public good that must be handled responsibly — data stewardship controls | ✅ Audit-log data-lineage tuples + receipt-engine provenance + identity-engine access scoping | `hummbl_governance/audit_log.py`, `hummbl_governance/kernel/receipt_engine.py`, `hummbl_governance/kernel/identity_engine.py` |
| Avoid deliberate misuse of data and enable timely correction of erroneous data | ✅ Output-validator correction gate + audit-log amendment tuples + schema-validator data-quality check | `hummbl_governance/output_validator.py`, `hummbl_governance/audit_log.py`, `hummbl_governance/schema_validator.py` |
| Data processing must not reproduce algorithmic bias or opacity in deep-learning models | ✅ Bias-detection tuples + compliance-mapper fairness assessment + stride-mapper threat modeling | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/stride_mapper.py`, `hummbl_governance/audit_log.py` |
| Protect personal data throughout the AI lifecycle | ✅ Capability-fence data-access restriction + identity-engine least-privilege + lifecycle retention controls | `hummbl_governance/capability_fence.py`, `hummbl_governance/kernel/identity_engine.py`, `hummbl_governance/lifecycle.py` |

### Strategic sovereignty, safety, and education (Principles 7, 8)

| Obligation | Coverage | Evidence |
|---|---|---|
| Strategic technology must respond to the country's needs — sovereign AI deployment alignment | ⚪ Boundary: national-strategic-needs determination is policy/organizational, not software-addressable | |
| AI development requires strengthening education and knowledge in the country | ⚪ Boundary: education policy and capacity-building are organizational/governmental | |
| AI systems must be safe and not generate risks to social structures and fundamental rights | ✅ Kill-switch + circuit-breaker + cost-governor budget enforcement + health-probe monitoring | `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py`, `hummbl_governance/cost_governor.py`, `hummbl_governance/health_probe.py` |
| Technical neutrality does not exist — systems must be governed against algorithmic bias and opacity | ✅ Doctrine-engine policy enforcement + evidence-engine bias evidence + reasoning-engine transparency record | `hummbl_governance/kernel/doctrine_engine.py`, `hummbl_governance/kernel/evidence_engine.py`, `hummbl_governance/reasoning.py` |
| Right to information must not be compromised by automation mechanisms | ✅ Output-validator transparency labeling + audit-log disclosure tuples + compliance-mapper explanation generator | `hummbl_governance/output_validator.py`, `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |

### Cultural and linguistic diversity (Principle 9)

| Obligation | Coverage | Evidence |
|---|---|---|
| AI cannot be alien to the cultural and linguistic diversity of the country — inclusive model design | 🟡 Partial: schema-validator supports multilingual schema validation; cultural-inclusiveness auditing is org task | `hummbl_governance/schema_validator.py`, `hummbl_governance/compliance_mapper.py` |
| Recover and strengthen indigenous languages and build linguistic corpora for AI | ⚪ Boundary: corpus construction and language-preservation policy are organizational/academic | |
| AI must reflect the cultural diversity of the country in its outputs and training | 🟡 Partial: output-validator content checks + audit-log diversity-metric tuples; cultural-adequacy review is org task | `hummbl_governance/output_validator.py`, `hummbl_governance/audit_log.py` |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| Human rights and well-being (Principles 1, 5) | 4 | 3 | 1 | 0 |
| Accountability and explainability (Principles 2, 3) | 4 | 4 | 0 | 0 |
| Impact awareness and collective governance (Principles 4, 6) | 4 | 2 | 1 | 1 |
| Data responsibility (Principle 10) | 4 | 4 | 0 | 0 |
| Strategic sovereignty, safety, and education (Principles 7, 8) | 5 | 3 | 0 | 2 |
| Cultural and linguistic diversity (Principle 9) | 3 | 0 | 2 | 1 |
| **Totals** | **24** | **16** | **4** | **4** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated. The Chapultepec Principles are a non-binding ethical declaration; coverage rows map technical primitives to guiding principles, not statutory obligations.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Human accountability overlaps EU AI Act Art. 14 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Impact assessment overlaps EU AI Act Art. 27 (FRIA) — see [`eu-ai-act.md`](./eu-ai-act.md)
- Risk management and bias detection overlap NIST AI RMF GOVERN/MEASURE — see [`nist-ai-rmf.md`](./nist-ai-rmf.md)
- Transparency and AI-use disclosure overlap South Korea AI Basic Act Art. 31 — see [`south-korea-ai-basic-act.md`](./south-korea-ai-basic-act.md)
- Data responsibility overlaps OECD AI Principles data stewardship — see [`oecd-ai-principles.md`](./oecd-ai-principles.md)
