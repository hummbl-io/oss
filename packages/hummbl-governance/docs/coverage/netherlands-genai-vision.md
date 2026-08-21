# Netherlands Generative AI Vision 2024 Coverage Matrix — HUMMBL

**Standard**: Government-wide Vision on Generative AI (Overheidsbrede visie generatieve AI)
**Effective**: January 18, 2024 (published January 2024; presented to Dutch Parliament via Kamerbrief)
**Source**: https://www.government.nl/site/binaries/site-content/collections/documents/2024/01/17/government-wide-vision-on-generative-ai-of-the-netherlands/Government-wide+vision+on+generative+AI+of+the+Netherlands.pdf
**Last reviewed**: 2026-06-25
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not Dutch legal counsel and does not provide legal advice on the Government-wide Vision on Generative AI. The Vision is a strategic policy document, not a statutory regulation — it sets four guiding principles (safety, fairness, human wellbeing/autonomy, sustainability/prosperity) and six action lines (collaboration, continuous monitoring, legal and policy shaping, skills and knowledge, government experimentation, and strong oversight). It anticipates and aligns with the EU AI Act rather than imposing directly enforceable obligations. Statutory compliance is the customer-organization responsibility. HUMMBL maps technical primitives to the Vision's principles and action lines where software-addressable controls exist.

## Scope summary

The Vision applies to the Dutch public sector — ministries, agencies, and public bodies — and signals expectations for the broader Dutch AI ecosystem including businesses, research institutions, and education. It covers generative AI development, deployment, and governance across all sectors, with heightened attention to high-impact use cases (public administration decisions, law enforcement, healthcare diagnostics, financial decision-making, critical infrastructure). The Vision is explicitly situated within the EU and international regulatory context, anticipating the EU AI Act, and emphasizes digital open strategic autonomy, public values, and fundamental rights (transparency, privacy, autonomy, non-discrimination).

## Obligations + coverage

### Principle 1 — Safety (safe development and application)

| Obligation | Coverage | Evidence |
|---|---|---|
| Actively mitigate misuse, accidents, and systemic security risks of and by generative AI models | ✅ Kill-switch 4-mode halt + circuit-breaker fast-fail + capability-fence isolation | `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py`, `hummbl_governance/capability_fence.py` |
| Prevent and manage accidents through rapid response capability | ✅ Circuit-breaker threshold-triggered halt + health-probe liveness checks | `hummbl_governance/circuit_breaker.py`, `hummbl_governance/health_probe.py` |
| Enforce safe operating boundaries on generative AI outputs | ✅ Output-validator content gate + schema-validator input/output contract enforcement | `hummbl_governance/output_validator.py`, `hummbl_governance/schema_validator.py` |
| Maintain systemic security through audit trail of safety-relevant events | ✅ Immutable audit-log with append-only event recording (cross-ref NIST AI RMF MEASURE) | `hummbl_governance/audit_log.py` |

### Principle 2 — Fairness and equity (fair and equitable development and application)

| Obligation | Coverage | Evidence |
|---|---|---|
| Address risks of inequality of opportunity and discrimination in generative AI outputs | ✅ Output-validator bias-detection gate + compliance-mapper fairness-assessment template | `hummbl_governance/output_validator.py`, `hummbl_governance/compliance_mapper.py` |
| Ensure transparency and explainability of generative AI decisions | ✅ Reasoning-engine rationale capture + audit-log provenance tuples (cross-ref EU AI Act Art. 13) | `hummbl_governance/reasoning.py`, `hummbl_governance/audit_log.py` |
| Maintain non-discrimination as a fundamental public value | ✅ Compliance-mapper impact-assessment with discrimination component (cross-ref EU AI Act Art. 10) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |

### Principle 3 — Human wellbeing and autonomy

| Obligation | Coverage | Evidence |
|---|---|---|
| Ensure generative AI serves human wellbeing and safeguards human autonomy | ✅ Human-oversight delegation token + kill-switch human-initiated halt (cross-ref EU AI Act Art. 14) | `hummbl_governance/delegation.py`, `hummbl_governance/kill_switch.py` |
| Preserve meaningful human control over generative AI systems | ✅ Delegation-token authority hierarchy + circuit-breaker human-override | `hummbl_governance/delegation.py`, `hummbl_governance/circuit_breaker.py` |
| Protect privacy as a fundamental right in generative AI deployment | ✅ Capability-fence data-access restriction + identity-registry scoped permissions | `hummbl_governance/capability_fence.py`, `hummbl_governance/identity.py` |
| Maintain transparency register for government generative AI initiatives | ✅ Audit-log initiative registration + compliance-mapper inventory template | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |

### Principle 4 — Sustainability and prosperity

| Obligation | Coverage | Evidence |
|---|---|---|
| Govern computational resource use to support sustainable economic growth | ✅ Cost-governor budget enforcement + lifecycle resource management | `hummbl_governance/cost_governor.py`, `hummbl_governance/lifecycle.py` |
| Address societal issues (e.g. climate) through governed AI deployment | ⚪ Boundary: societal-impact objectives are organizational, not directly software-addressable | |
| Manage ecological footprint of generative AI compute | ✅ Cost-governor compute-budget caps + lifecycle resource tracking | `hummbl_governance/cost_governor.py`, `hummbl_governance/lifecycle.py` |

### Action lines — monitoring, legislation, and oversight (Action lines 2, 3, 6)

| Obligation | Coverage | Evidence |
|---|---|---|
| Establish Rapid Response Team AI to advise on important developments | ⚪ Boundary: advisory-body establishment is governmental, not software-addressable | |
| Continuously monitor generative AI developments and public values under pressure | ✅ Health-probe continuous monitoring + audit-log event-stream tracking | `hummbl_governance/health_probe.py`, `hummbl_governance/audit_log.py` |
| Implement EU AI Act within the public sector (broad rollout from 2024) | ✅ Compliance-mapper EU AI Act crosswalk (cross-ref EU AI Act coverage matrix) | `hummbl_governance/compliance_mapper.py` |
| Develop a Dutch regulatory sandbox for generative AI | ✅ Capability-fence sandboxed execution + output-validator safe-mode validation | `hummbl_governance/capability_fence.py`, `hummbl_governance/output_validator.py` |
| Ensure strong and clear supervision and enforcement by regulators | 🟡 Partial: audit-log export + compliance-report generator supports supervisory review; enforcement action is regulatory task | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Cooperate between regulators and stakeholders through shared evidence | ✅ Audit-log evidence export + compliance-mapper multi-framework mapping | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |

### Action lines — knowledge, skills, and innovation (Action lines 4, 5)

| Obligation | Coverage | Evidence |
|---|---|---|
| Provide guidelines for deployment of generative AI within government organizations | ✅ Compliance-mapper policy-template + governance-lifecycle stage gates | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/lifecycle.py` |
| Develop ethical guidelines for responsible use of generative AI | ✅ Compliance-mapper ethics-assessment template + reasoning-engine ethical-constraint enforcement | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/reasoning.py` |
| Establish National AI Validation Team for benchmarking and tooling | ⚪ Boundary: national-team establishment is governmental, not software-addressable | |
| Ensure reliable and transparent generative AI models through validation | ✅ Schema-validator model-contract enforcement + output-validator transparency labeling | `hummbl_governance/schema_validator.py`, `hummbl_governance/output_validator.py` |
| Develop reliable Dutch-language datasets as foundation for generative AI | ⚪ Boundary: dataset curation is organizational, not directly software-addressable | |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| Principle 1 — Safety | 4 | 4 | 0 | 0 |
| Principle 2 — Fairness and equity | 3 | 3 | 0 | 0 |
| Principle 3 — Human wellbeing and autonomy | 4 | 4 | 0 | 0 |
| Principle 4 — Sustainability and prosperity | 3 | 2 | 0 | 1 |
| Action lines — monitoring, legislation, oversight | 6 | 4 | 1 | 1 |
| Action lines — knowledge, skills, innovation | 5 | 3 | 0 | 2 |
| **Totals** | **25** | **20** | **1** | **4** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated. The Netherlands Generative AI Vision is a strategic policy document, not a statutory regulation — coverage rows map HUMMBL primitives to principles and action lines where technical controls are addressable, and mark governmental, societal, and organizational responsibilities as boundary (⚪).

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- EU AI Act implementation overlaps EU AI Act Arts. 9, 10, 13, 14, 50 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Risk management and safety overlap NIST AI RMF MEASURE — see [`nist-ai-rmf.md`](./nist-ai-rmf.md)
- Human oversight overlaps EU AI Act Art. 14 and South Korea AI Basic Act Art. 34 — see [`eu-ai-act.md`](./eu-ai-act.md), [`south-korea-ai-basic-act.md`](./south-korea-ai-basic-act.md)
- Fairness and non-discrimination overlap EU AI Act Art. 10 and Colorado AI Act § 6-1-1702 — see [`eu-ai-act.md`](./eu-ai-act.md), [`colorado-ai-act.md`](./colorado-ai-act.md)
- Regulatory sandbox overlaps EU AI Act Art. 57 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Ethical guidelines overlap UNESCO AI Ethics and OECD AI Principles — see [`unesco-ai-ethics.md`](./unesco-ai-ethics.md), [`oecd-ai-principles.md`](./oecd-ai-principles.md)
