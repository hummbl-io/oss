# Norway National AI Strategy Coverage Matrix — HUMMBL

**Standard**: National Strategy for Artificial Intelligence (Nasjonal strategi for kunstig intelligens), Norway
**Effective**: January 14, 2020
**Source**: https://www.regjeringen.no/en/documents/nasjonal-strategi-for-kunstig-intelligens/id2685594/
**Last reviewed**: 2026-06-25
**Reviewer**: claude-code (huxley) per [ADR-001](../adr/ADR-001-coverage-matrix-not-self-grade.md)
**HUMMBL version**: hummbl-governance v0.8.0

## Boundary disclaimer

HUMMBL is not Norwegian legal counsel and does not provide legal advice on the National Strategy for Artificial Intelligence. The Strategy is a national policy framework issued by Kommunal- og moderniseringsdepartementet (Ministry of Local Government and Modernisation), not a binding statutory law with penalties. It is complemented by existing Norwegian law — the Personal Data Act (implementing the GDPR), the Public Administration Act, the Archival Act, and sectoral statutes (health, transport, energy) — under which supervisory authorities (e.g., Datatilsynet) retain enforcement powers. The Strategy covers the civilian sector (private and public) and excludes the defence sector. Statutory compliance and national-policy implementation are the customer-organization and government responsibility. HUMMBL maps technical primitives to the Strategy's data-sharing, regulatory-sandbox, infrastructure, transparency, human-oversight, privacy, and security objectives.

## Scope summary

The Strategy applies to AI development and use across Norway's civilian public and private sectors, organised around five thematic chapters: (1) a working definition of AI; (2) a good basis for AI — data and data management, language resources, regulations and regulatory sandboxes, infrastructure (networks and computing power); (3) developing and leveraging AI — research, higher education, and skills; (4) enhancing innovation capacity — industrial policy instruments and public-sector AI adoption; and (5) trustworthy AI — ethical principles, privacy by design, consumer protection, international cooperation, and security. Norway commits to world-class AI infrastructure (digitalisation-friendly regulations, language resources for Norwegian and Sami, robust communication networks, sufficient computing power), data sharing within and across sectors, and leadership in "human-friendly" AI grounded in ethical principles, respect for privacy, and good cyber security. Priority sectors include health, seas and oceans, public administration, energy, and mobility. The Strategy anticipates alignment with the EU AI Act, OECD AI Principles, and Council of Europe instruments via Norway's EEA relationship.

## Obligations + coverage

### Data and data management (Ch. 2.1)

| Obligation | Coverage | Evidence |
|---|---|---|
| Facilitate sharing of public-sector data so business, academia, and civil society can reuse it in new ways | 🟡 Partial: schema-validator enforces data-quality at creation + audit-log records data-lineage tuples; national data-sharing infrastructure and API catalog are org tasks | `hummbl_governance/schema_validator.py`, `hummbl_governance/audit_log.py` |
| Make open public data machine-readable and accessible through a common API catalog and base-data registers | 🟡 Partial: schema-validator validates machine-readable structure + compliance-mapper data-governance policy tuples; national open-data platform provisioning is org task | `hummbl_governance/schema_validator.py`, `hummbl_governance/compliance_mapper.py` |
| Protect personal data per the Personal Data Act/GDPR in AI systems with privacy-by-design and data minimisation | ✅ Capability-fence data-access restriction + identity-based authorization + output-validation privacy gate (cross-ref GDPR Art. 5, EU AI Act Art. 10) | `hummbl_governance/capability_fence.py`, `hummbl_governance/identity.py`, `hummbl_governance/output_validator.py` |
| Establish a national resource centre for data sharing with legal, technical, and process expertise | ⚪ Boundary: government institutional capacity-building is organizational, not software-addressable | |

### Regulations and regulatory sandboxes (Ch. 2.3)

| Obligation | Coverage | Evidence |
|---|---|---|
| Evaluate and modernize regulations that unintentionally hamper appropriate AI use in public and private sectors | ⚪ Boundary: legislative review and regulatory reform are governmental, not software-addressable | |
| Impose transparency and accountability requirements on new public-administration AI systems | ✅ Immutable audit-log for decision records + compliance-mapper transparency-policy tuples + receipt-engine provenance (cross-ref EU AI Act Art. 50, Korea AI Basic Act Art. 31) | `hummbl_governance/audit_log.py`, `hummbl_governance/compliance_mapper.py`, `hummbl_governance/kernel/receipt_engine.py` |
| Establish regulatory sandboxes for AI, including a data-protection sandbox supervised by Datatilsynet | 🟡 Partial: capability-fence + kernel admission-control provide controlled sandboxed test environments; government sandbox establishment and supervisory oversight are org tasks | `hummbl_governance/capability_fence.py`, `hummbl_governance/kernel/admission_control.py` |
| Apply the Public Administration Act and Archival Act to AI-assisted public decisions (records, accountability, archival retention) | ✅ Immutable audit-log retention + receipt-engine decision provenance + law-engine doctrine enforcement for public-sector rules (cross-ref EU AI Act Art. 12) | `hummbl_governance/audit_log.py`, `hummbl_governance/kernel/receipt_engine.py`, `hummbl_governance/kernel/law_engine.py` |

### Infrastructure: networks and computing power (Ch. 2.4)

| Obligation | Coverage | Evidence |
|---|---|---|
| Deploy robust and fast electronic communication networks (5G) to support AI development and use | ⚪ Boundary: telecommunications infrastructure deployment is governmental/organizational | |
| Ensure access to high-performance computing (HPC) resources for AI research and industry | 🟡 Partial: cost-governor budget enforcement + circuit-breaker fast-fail + kernel admission-control govern compute allocation; physical HPC procurement and national compute provisioning are org tasks | `hummbl_governance/cost_governor.py`, `hummbl_governance/circuit_breaker.py`, `hummbl_governance/kernel/admission_control.py` |
| Develop Norwegian data centres as a resource for AI compute and data storage | ⚪ Boundary: data-centre infrastructure provisioning is organizational, not software-addressable | |

### Research, skills & talent (Ch. 3)

| Obligation | Coverage | Evidence |
|---|---|---|
| Boost funding for basic and applied AI research through the Research Council of Norway and grant programmes | ⚪ Boundary: research-funding allocation is governmental, not software-addressable | |
| Embed AI topics across higher education and build interdisciplinary expertise | ⚪ Boundary: curriculum development and education-programme delivery are organizational | |
| Develop retraining, upskilling, and workplace-training programmes for AI and digital skills | ⚪ Boundary: workforce-training programmes are organizational, not software-addressable | |

### Innovation and public sector AI (Ch. 4)

| Obligation | Coverage | Evidence |
|---|---|---|
| Use public procurement and industrial policy instruments to stimulate AI development in priority sectors | ⚪ Boundary: procurement policy and industrial-incentive design are governmental | |
| Foster AI-based innovation in the public sector across priority areas (health, maritime, energy, mobility, public administration) | 🟡 Partial: kernel admission-control + capability-fence + compliance-mapper support controlled public-sector AI deployment; sectoral innovation programmes and pilot projects are org tasks | `hummbl_governance/kernel/admission_control.py`, `hummbl_governance/capability_fence.py`, `hummbl_governance/compliance_mapper.py` |
| Establish centres of excellence and shared public services for AI (language datasets, HPC access) | ⚪ Boundary: institutional capacity-building and shared-service provisioning are organizational | |

### Trustworthy AI — ethics, transparency, security (Ch. 5)

| Obligation | Coverage | Evidence |
|---|---|---|
| Promote ethical principles for AI: transparency, human oversight, privacy protection, cautious testing, explainability | ✅ Output-validation gate for transparency/explainability + human-oversight delegation token + capability-fence cautious-testing boundary + audit-log accountability (cross-ref OECD AI Principles, UNESCO Ethics of AI, EU AI Act Art. 5 + 13 + 14) | `hummbl_governance/output_validator.py`, `hummbl_governance/delegation.py`, `hummbl_governance/capability_fence.py`, `hummbl_governance/audit_log.py` |
| Ensure transparency and accountability for AI outputs and decisions in public and private deployment | ✅ Immutable audit-log decision records + output-validator provenance labeling + receipt-engine evidence chain (cross-ref EU AI Act Art. 50, Korea AI Basic Act Art. 31) | `hummbl_governance/audit_log.py`, `hummbl_governance/output_validator.py`, `hummbl_governance/kernel/receipt_engine.py` |
| Maintain human oversight of AI systems with named responsible contacts and intervention capability | ✅ Human-oversight delegation token + identity-registry role assignment + kill-switch 4-mode halt for human intervention (cross-ref EU AI Act Art. 14, Korea AI Basic Act Art. 34) | `hummbl_governance/delegation.py`, `hummbl_governance/identity.py`, `hummbl_governance/kill_switch.py` |
| Apply privacy by design and ethics in AI development and deployment | ✅ Capability-fence data-access restriction + output-validation privacy gate + audit-log privacy-by-design evidence tuples (cross-ref GDPR Art. 25, EU AI Act Art. 10) | `hummbl_governance/capability_fence.py`, `hummbl_governance/output_validator.py`, `hummbl_governance/audit_log.py` |
| Ensure security in AI-based systems (robustness, resilience, cyber-security protections) | ✅ Circuit-breaker fast-fail + health-probe reliability monitoring + capability-fence attack-surface restriction + kernel admission-control robustness gating (cross-ref NIST AI RMF MEASURE, ISO 27001) | `hummbl_governance/circuit_breaker.py`, `hummbl_governance/health_probe.py`, `hummbl_governance/capability_fence.py`, `hummbl_governance/kernel/admission_control.py` |
| Participate in international cooperation on ethical and trustworthy AI (EU, OECD, Council of Europe) | 🟡 Partial: compliance-mapper crosswalks international standards (EU AI Act, NIST, ISO, OECD); diplomatic and intergovernmental alignment is government task | `hummbl_governance/compliance_mapper.py` |

## Summary

| Section | Obligations | ✅ | 🟡 | ⚪ |
|---|---:|---:|---:|---:|
| Data and data management (Ch. 2.1) | 4 | 1 | 2 | 1 |
| Regulations and regulatory sandboxes (Ch. 2.3) | 4 | 2 | 1 | 1 |
| Infrastructure: networks and computing power (Ch. 2.4) | 3 | 0 | 1 | 2 |
| Research, skills & talent (Ch. 3) | 3 | 0 | 0 | 3 |
| Innovation and public sector AI (Ch. 4) | 3 | 0 | 1 | 2 |
| Trustworthy AI — ethics, transparency, security (Ch. 5) | 6 | 5 | 1 | 0 |
| **Totals** | **23** | **8** | **6** | **9** |

---

## Draft coverage summary (not public claim)

This matrix is internal starter material. It must not be used as public evidence that HUMMBL fulfills this framework until row counts, evidence commands, artifact paths, and boundary classifications are validated.

## Cross-references

- ADR: [`docs/adr/ADR-001-coverage-matrix-not-self-grade.md`](../adr/ADR-001-coverage-matrix-not-self-grade.md)
- Transparency and accountability overlap EU AI Act Art. 50 and Korea AI Basic Act Art. 31 — see [`eu-ai-act.md`](./eu-ai-act.md), [`south-korea-ai-basic-act.md`](./south-korea-ai-basic-act.md)
- Human oversight overlaps EU AI Act Art. 14 and Korea AI Basic Act Art. 34 — see [`eu-ai-act.md`](./eu-ai-act.md), [`south-korea-ai-basic-act.md`](./south-korea-ai-basic-act.md)
- Privacy by design overlaps GDPR Art. 5 + 25 and EU AI Act Art. 10 — see [`gdpr.md`](./gdpr.md), [`eu-ai-act.md`](./eu-ai-act.md)
- Ethical principles overlap OECD AI Principles and UNESCO Ethics of AI — see [`oecd-ai-principles.md`](./oecd-ai-principles.md), [`unesco-ai-ethics.md`](./unesco-ai-ethics.md)
- Security and robustness overlap NIST AI RMF MEASURE and ISO 27001 — see [`nist-ai-rmf.md`](./nist-ai-rmf.md), [`iso-27001.md`](./iso-27001.md)
- Regulatory sandbox approach overlaps Saudi Arabia NSDAI and EU AI Act Art. 57 — see [`saudi-arabia-ai-strategy.md`](./saudi-arabia-ai-strategy.md), [`eu-ai-act.md`](./eu-ai-act.md)
- Data sharing and open data overlap Saudi Arabia NSDAI Dimension 3 — see [`saudi-arabia-ai-strategy.md`](./saudi-arabia-ai-strategy.md)
- International alignment overlaps Council of Europe AI Convention — see [`council-of-europe-ai-convention.md`](./council-of-europe-ai-convention.md)
