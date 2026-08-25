# Sweden AI Strategy 2026 Coverage Matrix — HUMMBL

**Standard**: Sweden's AI Strategy (Sveriges AI-strategi), Government of Sweden
**Effective**: February 20, 2026
**Source**: https://www.government.se/contentassets/4e6b2d34f81048d688c35c831065395f/swedens-ai-strategy.pdf
**Last reviewed**: 2026-06-25
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not Swedish legal counsel and does not provide legal advice on Sweden's AI Strategy. The Strategy is a national policy document, not a binding statute; it sets strategic objectives for Sweden to rank among the world's top ten AI nations and to be world-leading in public-sector AI use. The accompanying action plan assigns tasks to government agencies (Vinnova, Agency for Digital Government, Swedish Authority for Privacy Protection, Defence Research Agency, and others). Statutory compliance for Swedish operators flows from the EU AI Act (Regulation 2024/1689) and national implementing legislation (SOU 2025:101). HUMMBL maps technical primitives to the Strategy's responsible-AI, safety, data-governance, public-sector, infrastructure, and security objectives.

## Scope summary

The Strategy applies to all AI-related work in Sweden — public administration, research, business, and total defence. It is organised into three overarching areas: (1) societal development, (2) sustainable development, and (3) competitiveness and innovation. The action plan concretises these into sections covering competitiveness and innovation, a public sector in the vanguard, digital infrastructure and computing capacity, data access and utilisation, standardisation, and security and defence. Key measures include a national AI coordinator for Swedish language models, an AI workshop (AI-verkstad) for public administration, a new act on interoperability requirements for data sharing, an AI Factory (Mimer) at Linköping, an inquiry on safe and reliable AI aligned with the EU AI Act, and an AI Security Institute.

## Obligations + coverage

### Responsible and secure AI (Strategy §1, cross-cutting)

| Obligation | Coverage | Evidence |
|---|---|---|
| Drive development of responsible AI that maximises benefits, reduces risks, and increases trust; mitigate risks to personal privacy, copyright, and security | ✅ Governance-kernel doctrine + law engines encode responsible-AI policy as enforceable rules; capability-fence restricts data access (cross-ref EU AI Act Art. 9, GDPR) | `hummbl_governance/kernel/doctrine_engine.py`, `hummbl_governance/kernel/law_engine.py`, `hummbl_governance/capability_fence.py` |
| Promote effective, secure, and ethical use of generative AI in public administration (DIGG/IMY guidelines) | ✅ Output-validation gate + audit-log provenance for generative outputs (cross-ref EU AI Act Art. 50(2)) | `hummbl_governance/output_validator.py`, `hummbl_governance/audit_log.py` |
| Support inquiry on safe and reliable AI aligned with EU AI Act national amendments (SOU 2025:101) | ✅ Compliance-mapper crosswalks to EU AI Act risk tiers + evidence-export for national reporting | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/kernel/evidence_engine.py` |
| Increase trust through transparency of AI-assisted decisions in public services | ✅ Receipt-engine issues immutable decision receipts + audit-log retains explanation tuples | `hummbl_governance/kernel/receipt_engine.py`, `hummbl_governance/audit_log.py` |

### Competitiveness, innovation, and research (Strategy §3)

| Obligation | Coverage | Evidence |
|---|---|---|
| Appoint national AI coordinator for Swedish language models to coordinate actors and rights issues | ⚪ Boundary: inter-organisational coordination role is governmental, not software-addressable | |
| Establish AI Factory Mimer at Linköping for HPC access by companies, startups, and researchers | ⚪ Boundary: national compute-infrastructure provisioning is governmental | |
| Support world-class research in machine learning, language models, computer vision, and AI safety | 🟡 Partial: reasoning-engine + reward-monitor support research-grade agent evaluation; research funding is governmental | `hummbl_governance/reasoning.py`, `hummbl_governance/reward_monitor.py` |

### Public sector AI adoption (Strategy §1, action plan "A public sector in the vanguard")

| Obligation | Coverage | Evidence |
|---|---|---|
| Establish AI-verkstad (AI workshop) for public administration to develop and deploy AI services | 🟡 Partial: lifecycle + coordination-bus support governed deployment pipelines; workshop hosting is org task | `hummbl_governance/lifecycle.py`, `hummbl_governance/coordination_bus.py` |
| Improve efficiency and shorten processing times via AI-supported automation of permit processes | ✅ Workflow sequencing via schedule + sequence engines with human-oversight gates | `hummbl_governance/kernel/schedule_engine.py`, `hummbl_governance/kernel/sequence_engine.py` |
| Maintain equitable treatment, transparency, and data protection in public-sector AI use | ✅ Authority-engine enforces role-based access + identity-engine attributes decisions to accountable agents | `hummbl_governance/kernel/authority_engine.py`, `hummbl_governance/kernel/identity_engine.py` |
| Eliminate erroneous disbursements and criminal exploitation of benefit systems using AI | ✅ Anomaly-detection substrate via health-probe + audit-log adverse-event tuples | `hummbl_governance/health_probe.py`, `hummbl_governance/audit_log.py` |

### Data access, sharing, and governance (Strategy §2, action plan "Data access and utilisation")

| Obligation | Coverage | Evidence |
|---|---|---|
| Enable simple and secure data sharing among public and private actors with interoperability | ✅ Schema-validator enforces data-contract interoperability + coordination-bus mediates sharing | `hummbl_governance/schema_validator.py`, `hummbl_governance/coordination_bus.py` |
| Identify and classify intellectual property and sensitive data; determine what is protected vs shareable | ✅ Capability-fence data-classification tags + identity-engine attribute scoping | `hummbl_governance/capability_fence.py`, `hummbl_governance/kernel/identity_engine.py` |
| Improve data-driven approach and secure data-sharing capability in public administration | ✅ Audit-log data-lineage tuples + receipt-engine provenance for shared datasets | `hummbl_governance/audit_log.py`, `hummbl_governance/kernel/receipt_engine.py` |
| Influence and capitalise on EU data-sharing initiatives (European Health Data Space, interoperability) | 🟡 Partial: compliance-mapper tracks EU regulatory crosswalks; policy influence is governmental | `hummbl_governance/compliance_mapper.py` |

### Digital infrastructure, compute, and security/defence (Strategy §2–3, action plan "Security and defence")

| Obligation | Coverage | Evidence |
|---|---|---|
| Ensure secure and competitive digital infrastructure including subsea cable expansion | ⚪ Boundary: physical-infrastructure buildout is governmental | |
| Provide access to computing capacity (HPC) for AI training and inference | 🟡 Partial: cost-governor enforces compute budgets at agent level; national HPC provisioning is governmental | `hummbl_governance/cost_governor.py` |
| Use AI to protect internal and external security and freedom of action (total defence) | ✅ Physical-governor + capability-fence constrain autonomous systems in safety-critical contexts | `hummbl_governance/physical_governor.py`, `hummbl_governance/capability_fence.py` |
| Mitigate malicious use of AI and build resilience against cyber threats | ✅ Kill-switch 4-mode halt + circuit-breaker fast-fail for adversarial-trigger containment | `hummbl_governance/kill_switch.py`, `hummbl_governance/circuit_breaker.py` |
| Address existential and safety risks from advanced AI development (AI Security Institute) | 🟡 Partial: reward-monitor + convergence-guard detect misaligned agent behaviour; institute funding is governmental | `hummbl_governance/reward_monitor.py`, `hummbl_governance/convergence_guard.py` |

### Talent, skills, and AI literacy (Strategy §1, action plan education measures)

| Obligation | Coverage | Evidence |
|---|---|---|
| Invest in AI skills for all through public education, libraries, and free quality-tested AI tools | ⚪ Boundary: national education policy and public-tool provisioning are governmental | |
| Develop AI courses for professionals, integrate AI into university curricula, and adopt STEM strategy | ⚪ Boundary: academic curriculum design and higher-education funding are governmental | |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| Responsible and secure AI (§1, cross-cutting) | 4 | 4 | 0 | 0 |
| Competitiveness, innovation, and research (§3) | 3 | 0 | 1 | 2 |
| Public sector AI adoption (§1) | 4 | 3 | 1 | 0 |
| Data access, sharing, and governance (§2) | 4 | 3 | 1 | 0 |
| Digital infrastructure, compute, and security/defence (§2–3) | 5 | 2 | 2 | 1 |
| Talent, skills, and AI literacy (§1) | 2 | 0 | 0 | 2 |
| **Totals** | **22** | **12** | **5** | **5** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Responsible-AI and transparency overlap EU AI Act Arts. 9, 13, 50 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Risk management and safety overlap NIST AI RMF — see [`nist-ai-rmf.md`](./nist-ai-rmf.md)
- Data governance and privacy overlap GDPR — see [`gdpr.md`](./gdpr.md)
- Security and autonomous-systems safety overlap IEEE 7001 — see [`ieee-7001.md`](./ieee-7001.md)
- Public-sector AI reporting overlaps Denmark AI Act — see [`denmark-ai-act.md`](./denmark-ai-act.md)
