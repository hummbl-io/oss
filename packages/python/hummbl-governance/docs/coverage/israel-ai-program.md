# Israel National AI Program Coverage Matrix — HUMMBL

**Standard**: National Program for Artificial Intelligence (Phase II), Israel Innovation Authority / National AI Program Directorate
**Effective**: May 14, 2025 (Phase II launch; multi-year program 2021–2026)
**Source**: https://innovationisrael.org.il/en/wp-content/uploads/sites/3/2025/05/AI-National-Program-ENG-14-5-25.pdf
**Last reviewed**: 2026-06-25
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not Israeli legal counsel and does not provide legal advice on the National AI Program or Israel's AI Regulation and Ethics policy. The Program is a national-strategy document — not binding statute — and covers infrastructure funding, talent, research, public-sector adoption, regulation, and international positioning. Statutory and policy compliance is the customer-organization responsibility. HUMMBL maps technical primitives to the Program's responsible-innovation, safety, data-governance, oversight, and public-sector deployment objectives where software-addressable.

## Scope summary

The National AI Program is a multi-year government program (2021–2026) budgeted at approximately NIS 1 billion, coordinated across the Ministry of Innovation, Science and Technology; the Council for Higher Education; the Directorate of Defense R&D; the National Digital Agency; and the Ministry of Finance. Phase II (May 2025) launched flagship initiatives including a national supercomputer (~4,000 B200 accelerators via Nebius), a National AI Research Institute, Moonshot research projects (~NIS 90M), AI experimental labs, an IDF graduate AI study program, and sector-specific data assets. The Program's regulatory approach — "Responsible Innovation" (Government Resolution 212, 2023 policy paper) — favours sectoral, risk-based, human-centric regulation with sandboxes and soft regulation over horizontal legislation.

## Obligations + coverage

### AI infrastructure and research (Objective 1)

| Obligation | Coverage | Evidence |
|---|---|---|
| Establish computational infrastructures (national supercomputer) with governed access via compute-voucher model | ✅ Cost-governor budget enforcement + kernel admission-control resource allocation | `hummbl_governance/cost_governor.py`, `hummbl_governance/kernel/admission_control.py` |
| Encourage groundbreaking basic and applied research with safety guardrails for high-impact experiments | 🟡 Partial: kill-switch + circuit-breaker provide runtime safety; research funding and selection is org task | `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py` |
| Promote data infrastructures and data accessibility for research and industry | 🟡 Partial: identity + audit-log provide access governance; data-infrastructure engineering is org task | `hummbl_governance/identity.py`, `hummbl_governance/audit_log.py` |
| Develop natural language processing (NLP) infrastructures in Hebrew and Arabic | ⚪ Boundary: language-model and NLP-infrastructure R&D is not software-governance-addressable | |

### Industry adoption and regulatory sandboxes (Objective 2)

| Obligation | Coverage | Evidence |
|---|---|---|
| Form regulatory sandboxes in highly regulated fields with high financial potential | ✅ Capability-fence sandboxing + compliance-mapper sandbox-mode mapping (cross-ref EU AI Act Art. 57) | `hummbl_governance/capability_fence.py`, `hummbl_governance/compliance_mapper.py` |
| Support pilot-stage projects with lifecycle oversight and health monitoring | ✅ Lifecycle phase tracking + health-probe liveness checks | `hummbl_governance/lifecycle.py`, `hummbl_governance/health_probe.py` |
| Realize potential of Israel's unique data assets with access controls and safeguards | ✅ Identity-based access control + audit-log access recording + capability-fence isolation | `hummbl_governance/identity.py`, `hummbl_governance/audit_log.py`, `hummbl_governance/capability_fence.py` |
| Improve capability of domestic industry to attract best AI minds from around the world | ⚪ Boundary: talent recruitment and immigration policy is organizational | |

### Public-sector AI implementation (Objective 3)

| Obligation | Coverage | Evidence |
|---|---|---|
| Implement AI tools in national and municipal government with full auditability | ✅ Immutable audit-log + compliance-mapper evidence export | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Improve decision-making processes based on data and technology with evidence backing | ✅ Reasoning-engine trace + kernel evidence-engine evidence tuples | `hummbl_governance/reasoning.py`, `hummbl_governance/kernel/evidence_engine.py` |
| Streamline public service processes with AI lifecycle management | 🟡 Partial: lifecycle + health-probe support operational oversight; service redesign is org task | `hummbl_governance/lifecycle.py`, `hummbl_governance/health_probe.py` |
| Assign human oversight of public-sector AI systems including named responsible parties | ✅ Human-oversight delegation token + identity registration (cross-ref EU AI Act Art. 14) | `hummbl_governance/delegation.py`, `hummbl_governance/identity.py` |

### Global position and international standards (Objective 4)

| Obligation | Coverage | Evidence |
|---|---|---|
| Actively participate in international forums to shape global AI standards and regulatory frameworks | ⚪ Boundary: diplomatic and standards-body participation is organizational | |
| Align domestic regulation with regulatory regimes established in leading countries | ✅ Compliance-mapper cross-framework mapping + STRIDE-mapper threat alignment | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/stride_mapper.py` |
| Develop dual-use technology with safety controls and capability restrictions | ✅ Capability-fence restriction + physical-governor safety enforcement | `hummbl_governance/capability_fence.py`, `hummbl_governance/physical_governor.py` |
| Preserve and expand Israel's technological sovereignty and qualitative edge | ⚪ Boundary: national-strategy objectives are governmental, not software-addressable | |

### Responsible innovation and regulatory framework

| Obligation | Coverage | Evidence |
|---|---|---|
| Sectoral, risk-based regulation led by relevant regulators with coordination | ✅ Compliance-mapper risk-based mapping + kernel law-engine sectoral rule encoding | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/kernel/law_engine.py` |
| Establish coordination mechanisms between regulators via knowledge and coordination centre | ✅ Coordination-bus inter-agent messaging + lamport-clock causal ordering | `hummbl_governance/coordination_bus.py`, `hummbl_governance/lamport_clock.py` |
| Apply rigorous risk-management procedures for high-impact AI uses | ✅ Kill-switch 4-mode halt + circuit-breaker fast-fail + audit-log risk tuples (cross-ref NIST AI RMF) | `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py`, `hummbl_governance/audit_log.py` |
| Two-tier monitoring — sectoral monitoring by regulators plus central oversight | ✅ Health-probe liveness + reward-monitor behavior detection + audit-log central evidence | `hummbl_governance/health_probe.py`, `hummbl_governance/reward_monitor.py`, `hummbl_governance/audit_log.py` |
| Human-centric approach protecting individual rights and rule-of-law values | ✅ Kernel doctrine-engine policy enforcement + authority-engine permission gating | `hummbl_governance/kernel/doctrine_engine.py`, `hummbl_governance/kernel/authority_engine.py` |
| Favor soft regulation — standards and non-binding principles over horizontal legislation | 🟡 Partial: compliance-mapper maps voluntary standards; standards adoption is org task | `hummbl_governance/compliance_mapper.py` |

### Data assets and governance

| Obligation | Coverage | Evidence |
|---|---|---|
| Consolidate fragmented datasets into accessible sector-specific data assets (agriculture, climate, education) | ⚪ Boundary: data engineering and dataset curation is organizational | |
| Ensure responsible use through privacy safeguards on data assets | ✅ Identity-based access control + audit-log access recording | `hummbl_governance/identity.py`, `hummbl_governance/audit_log.py` |
| Protect intellectual property rights in data assets | 🟡 Partial: audit-log records data access and provenance; IP enforcement is legal/org task | `hummbl_governance/audit_log.py` |
| Apply security safeguards around data reservoirs and computing infrastructure | ✅ Capability-fence isolation + physical-governor safety enforcement | `hummbl_governance/capability_fence.py`, `hummbl_governance/physical_governor.py` |

### Talent and human capital

| Obligation | Coverage | Evidence |
|---|---|---|
| Expand number of AI experts via academic training tracks and graduate scholarships | ⚪ Boundary: education funding and curriculum design is organizational | |
| Upskilling programs for existing professionals with science and technology backgrounds | ⚪ Boundary: workforce training is organizational | |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| AI infrastructure and research (Obj. 1) | 4 | 1 | 2 | 1 |
| Industry adoption and sandboxes (Obj. 2) | 4 | 3 | 0 | 1 |
| Public-sector AI implementation (Obj. 3) | 4 | 3 | 1 | 0 |
| Global position and standards (Obj. 4) | 4 | 2 | 0 | 2 |
| Responsible innovation and regulation | 6 | 5 | 1 | 0 |
| Data assets and governance | 4 | 2 | 1 | 1 |
| Talent and human capital | 2 | 0 | 0 | 2 |
| **Totals** | **28** | **16** | **5** | **7** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Regulatory sandboxes overlap EU AI Act Art. 57 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Risk management overlaps NIST AI RMF — see [`nist-ai-rmf.md`](./nist-ai-rmf.md)
- Human oversight overlaps EU AI Act Art. 14 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Responsible-innovation ethics overlap UNESCO AI Ethics — see [`unesco-ai-ethics.md`](./unesco-ai-ethics.md)
- International standards alignment overlaps OECD AI Principles — see [`oecd-ai-principles.md`](./oecd-ai-principles.md)
