# Saudi Arabia National Strategy for Data & AI Coverage Matrix — HUMMBL

**Standard**: National Strategy for Data & Artificial Intelligence (NSDAI), Kingdom of Saudi Arabia
**Effective**: October 21, 2020 (announced at Global AI Summit, Riyadh; Royal approval July 17, 2020)
**Source**: https://sdaia.gov.sa/en/SDAIA/about/Pages/NationalStrategyForAI.aspx
**Last reviewed**: 2026-06-25
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not Saudi legal counsel and does not provide legal advice on the National Strategy for Data & AI (NSDAI). The Strategy is a national policy framework issued by the Saudi Data & Artificial Intelligence Authority (SDAIA) under Royal approval, not a binding statutory law with penalties. It is complemented by the SDAIA "Principles and Controls of AI Ethics" (September 2023, seven principles + four-tier risk classification), the National Data Governance Interim Regulations (June 2020), the Open Data Strategy (February 2022), and the Personal Data Protection Law (PDPL). Statutory compliance and national-policy implementation are the customer-organization and government responsibility. HUMMBL maps technical primitives to the Strategy's ethical-AI, data-governance, risk-management, transparency, and human-oversight objectives.

## Scope summary

The Strategy applies to AI and data development and deployment across Saudi Arabia's public and private sectors, targeting a phased roadmap — national-priority needs by 2021, competitive-advantage foundations by 2025, and international Data & AI leadership by 2030. It is built on six strategic dimensions — Ambition, Skills, Policies & Regulations, Investment, Research & Innovation, and Ecosystem — with measurable targets including ranking among the top 15 countries in AI, top 10 in open data, top 20 in scientific contribution, 20,000+ data & AI specialists, 300+ startups, and ~75B SAR in investment. Priority sectors include education, healthcare, energy, mobility, government, and financial services. SDAIA serves as the national competent authority for data and AI regulation, oversight, and the AI Ethics Principles, supported by the National Data Management Office (NDMO) for data governance.

## Obligations + coverage

### Ambition & global leadership (Dimension 1)

| Obligation | Coverage | Evidence |
|---|---|---|
| Position KSA as the global hub where the best of Data & AI is made reality | ⚪ Boundary: national-positioning and global-leadership ambition is governmental, not software-addressable | |
| Rank among top 15 countries in AI through international competitiveness | ⚪ Boundary: national-ranking targets are governmental policy metrics, not software-addressable | |
| Establish international partnerships and network for Data & AI leadership | ⚪ Boundary: diplomatic and intergovernmental partnerships are organizational | |

### Skills & talent development (Dimension 2)

| Obligation | Coverage | Evidence |
|---|---|---|
| Transform KSA's workforce with a steady local supply of Data & AI-empowered talents | ⚪ Boundary: national workforce-development strategy is governmental, not software-addressable | |
| Develop 20,000+ data & AI specialists and experts through training and education | ⚪ Boundary: educational-capacity building and training programs are organizational | |
| Build AI literacy and technical training programs across the education system | 🟡 Partial: compliance-mapper generates AI literacy training materials and technical documentation aligned with national AI strategy; curriculum delivery and educational-institution integration remain organizational | `hummbl_governance/compliance_mapper.py` |

### Policies, regulations & AI ethics (Dimension 3 + SDAIA AI Ethics Principles)

| Obligation | Coverage | Evidence |
|---|---|---|
| Enact welcoming, flexible, and stable regulatory frameworks for Data & AI businesses and talents | 🟡 Partial: compliance-mapper maps regulatory requirements and generates framework documentation for AI business compliance; legislative enactment and statutory drafting remain governmental | `hummbl_governance/compliance_mapper.py` |
| Develop adaptive policy frameworks and standards on Data & AI including ethical use of AI | ✅ Compliance-mapper with ethical-principle tuples + law-engine doctrine enforcement (cross-ref EU AI Act Art. 9, NIST AI RMF GOVERN) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/kernel/law_engine.py`, `hummbl_governance/kernel/doctrine_engine.py` |
| Apply SDAIA AI Ethics Principles across lifecycle: fairness, privacy & security, humanity, social & environmental benefit, reliability & safety, transparency & explainability, accountability | ✅ Output-validation gate for fairness/bias + immutable audit-log for accountability + human-oversight delegation token + health-probe reliability monitoring (cross-ref UNESCO Ethics of AI, EU AI Act Art. 5 + 14) | `hummbl_governance/output_validator.py`, `hummbl_governance/audit_log.py`, `hummbl_governance/delegation.py`, `hummbl_governance/health_probe.py` |
| Apply four-tier risk classification to AI systems across the lifecycle (design, data, deployment, monitoring, decommissioning) | ✅ Impact-assessment template + risk-tier classification tuple with four-tier mapping (cross-ref EU AI Act Art. 6, Egypt Governance Framework) | `hummbl_governance/compliance_mapper.py`, `hummbl_governance/audit_log.py` |
| Appoint Responsible AI Officers and establish AI ethics governance committee with clear accountability chain in entities | 🟡 Partial: delegation-token issuance + identity-registry role assignment support accountable-owner designation; committee formation and organizational authority are org tasks | `hummbl_governance/delegation.py`, `hummbl_governance/identity.py` |
| Align AI ethics framework with international norms (OECD, UNESCO, EU AI Act) and national laws (PDPL) | 🟡 Partial: compliance-mapper crosswalks international standards (EU AI Act, NIST, ISO, OECD); diplomatic and legislative alignment is government task | `hummbl_governance/compliance_mapper.py` |

### Data governance, privacy & open data (Dimension 3 + National Data Governance Interim Regulations + PDPL)

| Obligation | Coverage | Evidence |
|---|---|---|
| Implement national data governance framework covering data classification, sharing, open data, and freedom of information | ✅ Schema-validator for data-quality enforcement + audit-log data-lineage tuples + compliance-mapper data-governance policy tuples (cross-ref EU AI Act Art. 10, Egypt Pillar 3) | `hummbl_governance/schema_validator.py`, `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py` |
| Apply "open by default", "need to know", least privilege, and segregation of duties for government-held data | ✅ Capability-fence restricting data access + identity-based authorization + schema-validation for classification-at-creation (cross-ref NIST CSF AC, ISO 27001) | `hummbl_governance/capability_fence.py`, `hummbl_governance/identity.py`, `hummbl_governance/schema_validator.py` |
| Protect personal data per PDPL in AI systems; minimize data collection and apply strong security controls | ✅ Capability-fence data-access restriction + identity authorization + output-validation privacy gate (cross-ref GDPR Art. 5, EU AI Act Art. 10) | `hummbl_governance/capability_fence.py`, `hummbl_governance/identity.py`, `hummbl_governance/output_validator.py` |
| Rank among top 10 countries in open data; publish machine-readable public data free of restriction | 🟡 Partial: schema-validator + audit-log support data-quality and sharing controls; national open-data platform infrastructure and ranking are government tasks | `hummbl_governance/schema_validator.py`, `hummbl_governance/audit_log.py` |

### Investment & ecosystem (Dimensions 4 + 6)

| Obligation | Coverage | Evidence |
|---|---|---|
| Attract ~75B SAR investments in data & AI through public and private incentives | ⚪ Boundary: investment-attraction and financial-incentive policy are governmental/organizational | |
| Stimulate Data & AI entrepreneurship by creating 300+ startups and supporting SMEs | ⚪ Boundary: startup-creation and venture-support programs are organizational | |
| Build collaborative, forward-thinking ecosystem with test-bed environments and world-class infrastructure | 🟡 Partial: kernel admission-control + capability-fence provide controlled test-bed sandboxing; ecosystem-building and infrastructure provisioning are org tasks | `hummbl_governance/kernel/admission_control.py`, `hummbl_governance/capability_fence.py` |

### Research, innovation & infrastructure (Dimensions 5 + 6)

| Obligation | Coverage | Evidence |
|---|---|---|
| Empower top Data & AI institutions to spearhead innovation and impact creation | ⚪ Boundary: research-institution empowerment and R&D funding are organizational | |
| Rank among top 20 countries in scientific contribution and intellectual output | ⚪ Boundary: national research-ranking targets are governmental policy metrics | |
| Develop world-class AI infrastructure and compute resources for model training and deployment | 🟡 Partial: cost-governor budget enforcement + circuit-breaker fast-fail + kernel admission-control govern compute allocation; physical-infrastructure procurement is org task | `hummbl_governance/cost_governor.py`, `hummbl_governance/circuit_breaker.py`, `hummbl_governance/kernel/admission_control.py` |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| Ambition & global leadership (Dimension 1) | 3 | 0 | 0 | 3 |
| Skills & talent development (Dimension 2) | 3 | 0 | 0 | 3 |
| Policies, regulations & AI ethics (Dimension 3 + Principles) | 6 | 3 | 2 | 1 |
| Data governance, privacy & open data (Dimension 3 + Interim Regs + PDPL) | 4 | 3 | 1 | 0 |
| Investment & ecosystem (Dimensions 4 + 6) | 3 | 0 | 1 | 2 |
| Research, innovation & infrastructure (Dimensions 5 + 6) | 3 | 0 | 1 | 2 |
| **Totals** | **22** | **6** | **5** | **11** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- AI Ethics Principles overlap UNESCO Ethics of AI and EU AI Act Art. 5 — see [`eu-ai-act.md`](./eu-ai-act.md)
- Four-tier risk classification overlaps EU AI Act Art. 6 and Egypt Governance Framework — see [`eu-ai-act.md`](./eu-ai-act.md), [`egypt-ai-strategy.md`](./egypt-ai-strategy.md)
- Data governance and privacy overlap GDPR Art. 5 and EU AI Act Art. 10 — see [`gdpr.md`](./gdpr.md), [`eu-ai-act.md`](./eu-ai-act.md)
- Open-data and least-privilege controls overlap NIST CSF and ISO 27001 — see [`nist-csf.md`](./nist-csf.md), [`iso-27001.md`](./iso-27001.md)
- Human oversight overlaps EU AI Act Art. 14 and Azerbaijan Pillar 1 — see [`eu-ai-act.md`](./eu-ai-act.md), [`azerbaijan-ai-strategy.md`](./azerbaijan-ai-strategy.md)
- Transparency and explainability overlap EU AI Act Art. 50 and Korea AI Basic Act Art. 31 — see [`eu-ai-act.md`](./eu-ai-act.md), [`south-korea-ai-basic-act.md`](./south-korea-ai-basic-act.md)
- Risk management overlaps NIST AI RMF MEASURE — see [`nist-ai-rmf.md`](./nist-ai-rmf.md)
- Standards alignment overlaps ISO 42001 — see [`iso-42001.md`](./iso-42001.md)
