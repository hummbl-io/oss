# AI Governance Framework Inventory — Global Landscape

**Purpose**: Exhaustive catalog of AI governance frameworks, regulations, standards, and codes worldwide, to inform coverage-matrix backlog prioritization for HUMMBL.
**Method**: Three parallel web-research subagents covering (1) binding regulations by country, (2) voluntary standards and frameworks, (3) security/privacy/specialized frameworks. Results consolidated and deduplicated.
**Last updated**: 2026-07-14
**Reviewer**: claude-code (huxley)
**HUMMBL version**: hummbl-governance v0.8.0

---

## Currently Covered (12 frameworks — all with coverage matrix files)

> **Proxy clarification (added 2026-08-10):** "100% evidence validation" previously appeared here. This was ambiguous. Per ADR-001, coverage matrices are DRAFT scaffolds; per ADR-007, only 5 of 198 Fulfilled rows (2.5%) have *validated* evidence as of 2026-06-25. The accurate statement is: 12 frameworks have coverage matrix files. Evidence validation is ongoing (ratchet gate in CI). See §Terminal Values below.

| # | Framework | Type | Coverage file |
|---|-----------|------|---------------|
| 1 | EU AI Act | Binding regulation | `docs/coverage/eu-ai-act.md` |
| 2 | GDPR | Binding regulation | `docs/coverage/gdpr.md` |
| 3 | NIST AI RMF 1.0 | Voluntary framework | `docs/coverage/nist-ai-rmf.md` |
| 4 | NIST CSF 2.0 | Voluntary framework | `docs/coverage/nist-csf.md` |
| 5 | ISO/IEC 27001:2022 | Certifiable standard | `docs/coverage/iso-27001.md` |
| 6 | ISO/IEC 42001:2023 | Certifiable standard | `docs/coverage/iso-42001.md` |
| 7 | SOC 2 (TSC 2017/2022) | Attestation | `docs/coverage/soc2.md` |
| 8 | OWASP LLM Top 10 (2025) | Risk catalog | `docs/coverage/owasp-llm.md` |
| 9 | Colorado AI Act (SB 24-205) | Binding regulation | `docs/coverage/colorado-ai-act.md` |
| 10 | NYC Local Law 144 (AEDT) | Binding regulation | `docs/coverage/nyc-ll144.md` |
| 11 | Singapore IMDA Model AI Governance | Voluntary | `docs/coverage/imda-agentic.md` |
| 12 | G7 Hiroshima AI Process Code | Voluntary | `docs/coverage/g7-ai-code.md` |

---

## Newly Discovered Frameworks (218 total)

Organized by tier of relevance to HUMMBL coverage-matrix backlog.

### Tier 1 — Quick Wins (Code Already Exists in HUMMBL)

| # | Framework | Type | Status | Why It Matters | Source |
|---|-----------|------|--------|----------------|--------|
| 13 | STRIDE | Threat modeling | Shipped (`stride_mapper.py`) | Already shipped in `mcp_compliance.py`. Needs coverage matrix only. | — |
| 14 | OWASP Agentic Top 10 (ASI01-ASI10) | Risk catalog | Published Dec 9, 2025; code exists (`generate_owasp_report()`) | Distinct from LLM Top 10. HUMMBL is an agent platform — most directly relevant security framework. `docs/OWASP_MAPPING.md` already has content. | https://owasp.org/www-project-agentic-threats/ |

### Tier 1 — Enacted National AI Laws (Binding, High-Impact)

| # | Framework | Jurisdiction | Status | Effective | Key Obligations | Source |
|---|-----------|-------------|--------|-----------|-----------------|--------|
| 15 | South Korea AI Basic Act | South Korea | Enacted Jan 22, 2026 | Jan 2026 | First comprehensive AI law in Asia. Extraterritorial scope. High-impact AI obligations, transparency, compute threshold (10^26 FLOPs). Penalties up to KRW 30M. | https://regulations.ai/regulations/RAI-KR-NA-HAIESXX-2020 |
| 16 | Texas TRAIGA (HB 149) | Texas, US | Effective Jan 1, 2026 | Jan 2026 | Third US state with comprehensive AI law. Intent-based liability, 7 prohibited practices, $200K/violation. NIST AI RMF safe harbor. | https://capitol.texas.gov/tlodocs/89R/billtext/html/HB00149I.htm |
| 17 | Utah AI Policy Act (SB 149) | Utah, US | Effective May 1, 2024 | May 2024 | First US state AI law. Generative AI disclosure requirements for regulated occupations. $2,500/violation. | https://le.utah.gov/~2024S1/bills/static/SB0149.html |
| 18 | California AI Transparency Act (SB 942) | California, US | Operative Aug 2, 2026 | Aug 2026 | AI-generated content disclosure, provenance, manifest requirements. $5K/day penalties. | https://leginfo.legislature.ca.gov/faces/billTextClient.xhtml?bill_id=202320240SB942 |
| 19 | California AB 2013 (Training Data Transparency) | California, US | Effective Jan 1, 2026 | Jan 2026 | Requires disclosure of training data sources for GenAI. First-of-its-kind dataset transparency mandate. | https://leginfo.legislature.ca.gov/faces/billTextClient.xhtml?bill_id=202320240AB2013 |
| 20 | California SB 53 (TFAIA) | California, US | Effective Jan 1, 2026 | Jan 2026 | Frontier AI safety. Up to $1M/violation. Covers frontier model safety incidents. | https://leginfo.legislature.ca.gov/faces/billTextClient.xhtml?bill_id=202320240SB53 |
| 21 | Connecticut SB 2 / SB 5 | Connecticut, US | Enacted 2025/2026 | 2025-2026 | Comprehensive AI governance, algorithmic discrimination protections. | https://www.cga.ct.gov/ |
| 22 | Canada AIDA (Bill C-27) | Canada | Pending | Under review | Risk-based, mandatory impact assessments for high-impact systems, human oversight. | https://ised-isde.canada.ca/site/ised/en/legislation/initiatives/digital-charter-implementation-act-2023 |
| 23 | Brazil PL 2338/2023 | Brazil | Pending (Senate approved Dec 2024) | Pending House | Risk-based framework, rights of affected persons, high-risk AI accountability. | https://regulations.ai/regulations/brazil-2023-05-pl2338 |
| 24 | China Generative AI Measures | China | Effective Aug 15, 2023 | Aug 2023 | Content safety, labeling, training data rules, algorithm filing, security assessment. | http://www.cac.gov.cn/2023-07/13/c_1690898327029107.htm |
| 25 | China Deep Synthesis Provisions | China | Effective Jan 10, 2023 | Jan 2023 | Deepfake regulation, content labeling, security assessment. | http://www.cac.gov.cn/2022-12/11/c_1672221949354811.htm |
| 26 | China Algorithm Recommendation Regulation | China | Effective Mar 1, 2022 | Mar 2022 | Algorithm filing, transparency, user rights. | http://www.cac.gov.cn/2021-12/31/c_1643158928915665.htm |
| 27 | Taiwan AI Fundamental Act | Taiwan | Passed Dec 23, 2025 | Dec 2025 | 7 principles, AI risk classification framework. | https://www.most.gov.tw/ |
| 28 | UK AI Regulation Framework | UK | Principles-based, voluntary | Published | Sector-led, 5 principles. No central AI authority yet. | https://www.gov.uk/government/publications/ai-regulation-a-pro-innovation-approach |
| 29 | CCPA / CPRA | California, US | Effective (CPRA Jan 1, 2023) | 2023 | California Consumer Privacy Act. Most impactful US state privacy law. ADMT regulations pending. | https://oag.ca.gov/privacy/ccpa |
| 30 | Virginia HB 714 | Virginia, US | Enacted (amended Mar 2026) | 2026 | High-risk AI protections. | https://lis.virginia.gov/ |
| 31 | Japan AI Act (Act No. 53/2025) | Japan | Enacted Jun 4, 2025 | Jun 2025 | AI Strategic Headquarters; promotes R&D and utilization; international cooperation. | https://www.japaneselawtranslation.go.jp/en/laws/view/5066 |
| 32 | Peru Law No. 31814 + Supreme Decree 115-2025 | Peru | Enacted 2024/2025 | Sep 2025 | Risk-based classification; prohibited/high-risk uses; transparency; cybersecurity; audit. | https://www.gob.pe/institucion/pcm/normas-legales/7133522-115-2025-pcm |
| 33 | El Salvador AI Promotion Law (Decree 234/363) | El Salvador | Enacted Feb 2025 | Feb 2025 | National AI Agency (ANIA); tiered oversight; mandatory National Registry; Algorithmic Impact Assessment. | https://www.unesco.org/ethics-ai/en/elsalvador |
| 34 | Kazakhstan AI Law | Kazakhstan | Enacted Nov 17, 2025 | Nov 2025 | First dedicated AI law in Central Asia. Data protection, ethical use, copyright for AI prompts. | https://so-ipr.com/news-events/publications/kazakhstan-enacts-first-ai-law-central-asia |
| 35 | Italy Law No. 132/2025 | Italy | Enacted Oct 10, 2025 | Oct 2025 | Cross-sector: healthcare, work, PA, justice, education, sport; under-14 parental consent. | https://www.normattiva.it/eli/id/2025/09/25/25G00143/CONSOLIDATED |
| 36 | Denmark AI Act (Law 467/2025) | Denmark | Enacted May 14, 2025 | May 2025 | EU AI Act implementation; market surveillance and enforcement. | https://regulations.ai/regulations/RAI-DK-NA-SPAILXX-2025 |
| 37 | Malta AI Regulations (LN 226/227 of 2025) | Malta | Enacted Oct 10, 2025 | Oct 2025 | MDIA as market surveillance authority; conformity assessment; sandboxes. | https://legislation.mt/eli/ln/2025/226/eng |
| 38 | Ireland EU AI Designation Regs (S.I. 366/2025) | Ireland | Enacted Jul 2, 2025 | Jul 2025 | Central Bank + DPC as competent authorities for EU AI Act. | https://www.irishstatutebook.ie/eli/2025/si/366/made/en/pdf |
| 39 | Cyprus EU AI Governance Framework | Cyprus | Enacted Nov 2024 | Nov 2024 | National coordinator designation. | https://regulations.ai/regulations/RAI-CY-NA-GIE2AXX-2024 |
| 40 | Lithuania AI Act Amendments (XV-105/106) | Lithuania | Enacted Jan 2025 | Apr 2025 | EU AI Act implementation. | https://regulations.ai/regulations/RAI-LT-NA-AIEAIXX-2025 |
| 41 | Slovenia AI Implementation Act (ZIUDHPUI) | Slovenia | Enacted Nov 21, 2025 | Nov 2025 | Ethics council, regulatory sandboxes, public register. | https://regulations.ai/regulations/RAI-SI-NA-ZOIUEXX-2025 |
| 42 | Latvia AI Centre Law | Latvia | Enacted 2025 | 2025 | Dedicated national AI center; electoral integrity. | https://regulations.ai/regulations/latvia-summary |
| 43 | Chile AI Bill | Chile | Enacted Sep 15, 2025 | Pending impl. | Risk-based (unacceptable, high-risk, limited risk); prohibits certain uses. | https://www.camara.cl/ |
| 44 | Sweden AI Act Proposal (SOU 2025:101) | Sweden | Proposed | — | EU AI Act implementation. | https://regulations.ai/regulations/RAI-SE-NA-ATABAXX-2025 |
| 45 | Norway AI Act (KI-loven) | Norway | Proposed Jun 2025 | — | EU AI Act implementation. | https://regulations.ai/regulations/RAI-NO-NA-ARTIINT-2026 |
| 46 | Malaysia AIGE Guidelines | Malaysia | Enacted Sep 2024 | Sep 2024 | 7 core principles (voluntary): fairness, reliability, privacy, inclusivity, transparency, accountability, human benefit. | https://www.malaysia.gov.my/ |
| 47 | Indonesia AI Bill (RUU AI) | Indonesia | Proposed | — | Risk-based, National AI Strategy 2020-2045. | https://regulations.ai/regulations/RAI-ID-NA-RUTKBXX-2025 |
| 48 | Thailand AI Royal Decree | Thailand | Proposed | — | 3 categories: prohibited, high-risk, limited-risk. | https://www.mondaq.com/new-technology/1497962/ |
| 49 | Philippines HB 7913 / HB 7396 | Philippines | Proposed | — | Philippine Council on AI / AIDA. | https://issuances-library.senate.gov.ph/ |
| 50 | Colombia AI Bill (PL 098/2025) | Colombia | Proposed Jul 2025 | — | Psychosocial/digital equity focus. | https://www.camara.gov.co/ |
| 51 | Argentina AI Bill | Argentina | Proposed | — | National AI Agency (ANIA), registry of high-risk systems. | https://rest.hcdn.gob.ar/ |
| 52 | Costa Rica AI Bill (Exp. 23771) | Costa Rica | Proposed Aug 2024 | — | ARIA regulator, impact assessments. | http://www.camtic.org/ |
| 53 | Panama Draft Bill 0016 | Panama | Proposed Jul 2025 | — | Fundamental rights focus. | https://consortiumlegal.com/ |
| 54 | Kenya AI Bill 2026 (Senate Bill 4) | Kenya | Proposed 2026 | — | AI Commissioner, risk classification. | https://www.parliament.go.ke/ |
| 55 | Egypt National AI Governance Framework | Egypt | Proposed | — | "State as Orchestrator" philosophy. | https://ai.gov.eg/ |
| 56 | Turkey AI Law Draft (TBMM 2/2234) | Turkey | Proposed Jun 2024 | — | 35M TL / 7% turnover penalties. | https://regulations.ai/regulations/RAI-TR-NA-YZKTAXX-2024 |
| 57 | Azerbaijan AI Strategy 2025-2028 | Azerbaijan | Enacted Mar 2025 | Mar 2025 | Presidential decree, ethical AI. | https://ifac.az/en/blog/ |
| 58 | Spain Organic Law for AI Governance | Spain | Draft 2026 | — | EU AI Act national adaptation. | https://www.lamoncloa.gob.es/ |
| 59 | Mexico National AI Law Draft | Mexico | Proposed | — | Comprehensive legal framework for AI. | https://basham.com.mx/ |
| 60 | Mexico Chapultepec Principles 2026 | Mexico | Published Jan 2026 | Jan 2026 | Ethics and good practices for AI. | https://secihti.mx/ |

### Tier 1 — US State AI Laws (Beyond CO/NY/TX/UT/CA/CT/VA)

| # | Framework | State | Status | Key Relevance | Source |
|---|-----------|-------|--------|---------------|--------|
| 61 | Maryland AI Governance Act (SB 818) | Maryland | Enacted 2024 | State agency AI inventories; procurement ban on non-compliant AI from Jul 2025. | https://mgaleg.maryland.gov/2024RS/chapters_noln/CH_496_sb0818e.pdf |
| 62 | Illinois IHRA AI Amendment (HB 3773) | Illinois | Enacted 2024 (eff. 2026) | Employer liability for algorithmic discrimination; no statutory affirmative defense. | https://reg-intel.com/us-state-ai-laws-tracker/ |
| 63 | Iowa Conversational AI Services Act (SF 2417) | Iowa | Enacted | Minor protection, suicide/self-harm protocol; $500K penalties. | https://www.legis.iowa.gov/docs/publications/iactc/91.2/CH1068.pdf |
| 64 | Maine AI Chatbot Disclosure Law | Maine | Enacted 2025 | Trade/commerce AI chatbot disclosure; unfair trade practice if violated. | https://legislature.maine.gov/statutes/10/title10sec1500-DD.html |
| 65 | New Hampshire Ch. 5-D (State Agency AI) | New Hampshire | Enacted | Prohibits discriminatory classification; biometric ID only with warrant; deepfake ban. | https://gc.nh.gov/rsa/html/I/5-D/5-D-mrg.htm |
| 66 | Vermont Act 101 (Neurological Rights + AI) | Vermont | Enacted 2026 | Healthcare AI, AI Advisory Council. | https://legislature.vermont.gov/Documents/2026/Docs/ACTS/ACT101/ |
| 67 | Kentucky AI Governance Framework (KRS 42.731) | Kentucky | Enacted | AI Governance Committee, centralized registry, human review. | https://apps.legislature.ky.gov/ |
| 68 | Arizona HB 2394 / SB 1295 / HB 2678 / HB 2175 | Arizona | Enacted | Election deepfakes, voice fraud, child exploitation, healthcare AI claim denial. | https://www.recordinglaw.com/us-laws/ai-laws/arizona-ai-laws/ |
| 69 | North Carolina EO 24 | North Carolina | Enacted Aug 2024 | AI Leadership Council, AI Accelerator, State AI Strategic Roadmap. | https://governor.nc.gov/executive-order-no-24/ |
| 70 | Nebraska AI Consumer Protection Act (LB 642) | Nebraska | Proposed | Developer/deployer duty of care, impact assessments. | https://nebraskalegislature.gov/FloorDocs/Current/PDF/Intro/LB642.pdf |
| 71 | New Mexico AI Act (HB 60) | New Mexico | Proposed | Developer duty of care, risk incident disclosure. | https://www.nmlegis.gov/ |
| 72 | Rhode Island AI Act (S0627) | Rhode Island | Proposed | High-risk AI in consequential decisions. | https://webserver.rilegislature.gov/ |
| 73 | Minnesota RAISE Act (HF 4532) | Minnesota | Proposed | Safety protocols, incident disclosure. | https://www.revisor.mn.gov/ |
| 74 | Florida SB 482 / HB 659 / HB 1395 | Florida | Proposed | Companion chatbots, AI Bill of Rights. | https://www.flsenate.gov/ |

### Tier 1 — City/Local AI Ordinances

| # | Framework | City | Status | Key Relevance | Source |
|---|-----------|------|--------|---------------|--------|
| 75 | SF AI Inventory Ordinance (288-24) | San Francisco | Enacted Dec 2024 | Publicly available inventory of AI used by City. | https://sfgov.legistar.com/ |
| 76 | SF Ban on Automated Rent-Setting (224-24) | San Francisco | Enacted Jul 2024 | Prohibits algorithmic rent-setting devices. | https://sfgov.legistar.com/ |
| 77 | NYC Int 0926-2024 (AI Compliance Standards) | New York City | Proposed | Office of Algorithmic Accountability rules for city agencies. | https://legistar.council.nyc.gov/ |
| 78 | Chicago AI Programs (O 2024-0008943) | Chicago | Proposed | Guidelines for AI programs by City departments. | https://fastdemocracy.com/ |
| 79 | DC Mayor's Order 2024-028 | Washington DC | Enacted 2024 | AI Taskforce, privacy review, AI procurement handbook. | https://techplan.dc.gov/ |
| 80 | Austin Resolution 24-3972 | Austin | Enacted Feb 2024 | Transparent and ethical citywide AI guidelines. | https://services.austintexas.gov/ |
| 81 | LA Council File 23-1020 | Los Angeles | Enacted Dec 2024 | Digital Code of Ethics, AI Safety Checklist, AI Roadmap. | https://cityclerk.lacity.org/ |
| 82 | Seattle GenAI Policy (POL-209) + AI Policy (POL-211) | Seattle | Enacted | GenAI acquisition standards; Algorithmic Impact Assessment for high-risk. | https://seattle.gov/ |
| 83 | Boston Interim GenAI Guidelines | Boston | Enacted May 2023 | Interim guidelines for city employee GenAI use. | https://www.boston.gov/ |

### Tier 2 — ISO/IEC AI Standards

| # | Standard | Focus | Status | Source |
|---|----------|-------|--------|--------|
| 84 | ISO/IEC 22989:2022 | AI concepts and terminology | Published Jul 2022 | https://www.iso.org/standard/74296.html |
| 85 | ISO/IEC 23053:2022 | Framework for ML-based AI systems | Published Jun 2022 | https://www.iso.org/standard/74438.html |
| 86 | ISO/IEC 5338:2023 | AI system lifecycle processes | Published Dec 2023 | https://www.iso.org/standard/81118.html |
| 87 | ISO/IEC 5339:2024 | Guidance for AI applications | Published Jan 2024 | https://www.iso.org/standard/81120.html |
| 88 | ISO/IEC 12792:2025 | Transparency taxonomy of AI systems | Published Nov 2025 | https://www.iso.org/standard/84111.html |
| 89 | ISO/IEC TS 6254:2025 | Explainability/interpretability approaches | Published Sep 2025 | https://www.iso.org/standard/82148.html |
| 90 | ISO/IEC TR 24027:2021 | Bias in AI systems and decision making | Published 2021 | https://sgsystemsglobal.com/ |
| 91 | ISO/IEC TS 25058:2024 | Quality evaluation of AI systems | Published Jan 2024 | https://www.iso.org/standard/82570.html |
| 92 | ISO/IEC 25059:2023 | Quality model for AI systems | Published Jun 2023 | https://www.iso.org/standard/80655.html |
| 93 | ISO/IEC TS 4213:2022 | ML classification performance assessment | Published Oct 2022 | https://www.iso.org/standard/79799.html |
| 94 | ISO/IEC TS 42119-2:2025 | Testing of AI systems overview | Published Nov 2025 | https://www.iso.org/standard/84127.html |
| 95 | ISO/IEC 5259-1 through 5 (2024/2025) | Data quality for analytics and ML (5 parts) | Published | https://www.iso.org/standard/81088.html |
| 96 | ISO/PAS 8800:2024 | Road vehicles — Safety and AI | Published 2024 | https://www.iso.org/standard/83303.html |
| 97 | ISO/IEC 23894:2023 | AI Guidance on Risk Management | Published 2023 | https://www.iso.org/standard/77304.html |
| 98 | ISO/IEC 38507:2022 | Governance of AI for Organizations | Published 2022 | https://www.iso.org/standard/74296.html |
| 99 | ISO/IEC TR 24028:2020 | Trustworthiness of AI | Published 2020 | https://www.iso.org/ |
| 100 | ISO/IEC 42005:2025 | AI Impact Assessment | Published May 2025 | https://www.iso.org/ |
| 101 | ISO/IEC 42006:2025 | AIMS Audit/Certification | Published Jul 2025 | https://www.iso.org/ |

### Tier 2 — IEEE AI Standards

| # | Standard | Focus | Status | Source |
|---|----------|-------|--------|--------|
| 102 | IEEE 7000-2021 | Ethical concerns during system design | Published Sep 2021 | https://standards.ieee.org/ieee/7000/6781/ |
| 103 | IEEE 7001-2021 | Transparency of autonomous systems | Published Mar 2022 | https://standards.ieee.org/ieee/7001/6929/ |
| 104 | IEEE P2863 | Organizational Governance of AI | Draft Mar 2026 | https://sagroups.ieee.org/ai-sc/active-pars/ |
| 105 | IEEE 3119-2025 | Procurement of AI and Automated Decision Systems | Published May 2025 | https://standards.ieee.org/ieee/3119/10729/ |
| 106 | IEEE 2840-2024 | Responsible AI licensing | Published May 2025 | https://standards.ieee.org/ieee/2840/7673/ |
| 107 | IEEE 2941-2021 / 2941.1-2022 | AI model representation / operator interfaces | Published | https://standards.ieee.org/ieee/2941/10363/ |
| 108 | IEEE 2945-2023 | Face recognition technical requirements | Published 2023 | https://sagroups.ieee.org/ai-sc/standards/ |
| 109 | IEEE 2986-2023 | Privacy/security for federated ML | Published Apr 2024 | https://standards.ieee.org/ieee/2986/10564/ |
| 110 | IEEE 3110-2025 | Computer vision API requirements | Published May 2025 | https://standards.ieee.org/ieee/3110/11253/ |
| 111 | IEEE 3127-2025 | Blockchain-based federated ML | Published 2025 | https://standards.ieee.org/ieee/3127/10745/ |
| 112 | IEEE 3128-2025 | AI dialogue system evaluation | Published 2025 | https://sagroups.ieee.org/ai-sc/standards/ |
| 113 | IEEE 3129-2023 | Robustness testing for AI image recognition | Published 2023 | https://sagroups.ieee.org/ai-sc/standards/ |
| 114 | IEEE 3156-2023 | Privacy-preserving computation platforms | Published 2023 | https://sagroups.ieee.org/ai-sc/standards/ |
| 115 | IEEE 3168-2024 | NLP service robustness evaluation | Published 2024 | https://sagroups.ieee.org/ai-sc/standards/ |
| 116 | IEEE 3187-2024 | Trustworthy federated ML framework | Published 2024 | https://sagroups.ieee.org/ai-sc/standards/ |
| 117 | IEEE 3198-2025 | ML fairness evaluation method | Published May 2025 | https://standards.ieee.org/ieee/3198/11068/ |
| 118 | IEEE 3378-2025 | Large-scale DL model evaluation | Published Jan 2026 | https://standards.ieee.org/ieee/3378/11304/ |
| 119 | IEEE 3152-2024 | Human/machine agency identification | Published 2024 | https://sagroups.ieee.org/ai-sc/standards/ |
| 120 | IEEE 3350-2025 | AI generalizability for medical imaging | Published 2025 | https://sagroups.ieee.org/ai-sc/standards/ |
| 121 | IEEE 3410-2025 | Financial risk management models | Published 2025 | https://sagroups.ieee.org/ai-sc/standards/ |
| 122 | IEEE P2894 | Architectural framework for explainable AI | In development | https://standict.eu/ |
| 123 | IEEE P7015 | AI literacy, skills, and readiness | In development | https://sagroups.ieee.org/ai-sc/active-pars/ |
| 124 | IEEE P3395 | Safeguards/controls for AI models | In development | https://sagroups.ieee.org/ai-sc/active-pars/ |
| 125 | IEEE P3396 | AI risk/safety/trustworthiness evaluation | In development | https://sagroups.ieee.org/ai-sc/active-pars/ |
| 126 | IEEE P7999 | Ethics oversight in AI projects | In development | https://sagroups.ieee.org/ai-sc/active-pars/ |
| 127 | IEEE P3514 | AI capability levels for AI entities | In development | https://sagroups.ieee.org/ai-sc/active-pars/ |
| 128 | IEEE P3709 | Framework for agentic AI | In development | https://sagroups.ieee.org/ai-sc/active-pars/ |
| 129 | IEEE P7018 | Security for generative pretrained AI models | In development | https://sagroups.ieee.org/ai-sc/active-pars/ |

### Tier 2 — National AI Strategies/Frameworks

| # | Framework | Country | Status | Source |
|---|-----------|---------|--------|--------|
| 130 | Ireland National AI Strategy Refresh 2024 | Ireland | Published 2024 | https://enterprise.gov.ie/ |
| 131 | Netherlands Strategic Action Plan for AI | Netherlands | Published 2019 | https://www.government.nl/ |
| 132 | Netherlands GenAI Vision 2024 | Netherlands | Published Jan 2024 | https://www.government.nl/ |
| 133 | Spain AI Regulatory/Ethical Framework | Spain | Published | http://espanadigital.gob.es/ |
| 134 | Sweden AI Strategy 2026 | Sweden | Published Feb 2026 | https://www.government.se/ |
| 135 | Norway National AI Strategy | Norway | Published | https://www.regjeringen.no/ |
| 136 | France AI for Humanity Strategy | France | Published 2018 | https://regulations.ai/ |
| 137 | Germany MISSION KI Quality Standard | Germany | Published Nov 2025 | https://mission-ki.de/ |
| 138 | India AI Governance Guidelines 2026 | India | Published Nov 2025 | https://www.psa.gov.in/ |
| 139 | India Responsible AI for All Principles | India | Published 2021 | https://niti.gov.in/ |
| 140 | South Korea National AI Ethics Standards | South Korea | Published 2020 | https://regulations.ai/ |
| 141 | Canada Voluntary Code for Advanced GenAI | Canada | Published | https://ised-isde.canada.ca/ |
| 142 | Canada Guiding Principles for Gov AI Use | Canada | Published | https://www.canada.ca/ |
| 143 | Canada Privacy Principles for GenAI | Canada | Published | https://www.priv.gc.ca/ |
| 144 | Chile National AI Policy | Chile | Published 2021, updated 2024 | https://regulations.ai/ |
| 145 | African Union Continental AI Strategy | African Union | Published Jul 2024 | https://au.int/ |
| 146 | Nigeria National AI Strategy | Nigeria | Published Aug 2024 | https://ncair.nitda.gov.ng/ |
| 147 | New Zealand AI Strategy 2025 | New Zealand | Published Jul 2025 | https://www.mbie.govt.nz/ |
| 148 | NZ Public Service AI Framework | New Zealand | Published | https://www.dns.govt.nz/ |
| 149 | NZ Algorithm Charter for Aotearoa | New Zealand | Published 2020 | https://www.data.govt.nz/ |
| 150 | Israel National AI Program 2025 | Israel | Published May 2025 | https://innovationisrael.org.il/ |
| 151 | UAE AI Strategy 2017 | UAE | Published 2017 | — |
| 152 | Saudi Arabia AI Strategy (SDAIA) | Saudi Arabia | Published | — |

### Tier 2 — Regional AI Frameworks

| # | Framework | Region | Status | Source |
|---|-----------|--------|--------|--------|
| 153 | ASEAN Guide on AI Governance and Ethics | ASEAN | Published Feb 2024 | https://asean.org/ |
| 154 | ASEAN AI SAFE Network Declaration | ASEAN | Published Oct 2025 | https://asean.org/ |
| 155 | Nordic AI Partnership (MoU) | Nordic | Signed Feb 2025 | https://www.nordicpartnership.ai/ |
| 156 | NordAId — Trustworthy AI in Public Decision Making | Nordic-Baltic | Active | https://www.nordforsk.org/ |

### Tier 3 — International Treaties & Voluntary Frameworks

| # | Framework | Type | Status | Source |
|---|-----------|------|--------|--------|
| 157 | Council of Europe Framework Convention on AI (CETS 225) | Binding treaty | Open for signature Sep 5, 2024 | https://book.coe.int/ |
| 158 | OECD AI Principles | Voluntary | Adopted 2019, updated May 2024 | https://www.oecd.org/en/topics/ai-principles.html |
| 159 | UNESCO Recommendation on Ethics of AI | Voluntary | Adopted Nov 2021 | https://www.unesco.org/ |
| 160 | Australia Voluntary AI Safety Standard | Voluntary | Published Sep 2024 | — |
| 161 | Australia AI Ethics Principles | Voluntary | Published 2019 | — |
| 162 | UN General Assembly AI Resolution | Voluntary | Mar 2024 | — |
| 163 | NIST AI 600-1 (Generative AI Profile) | Voluntary | Published Jul 26, 2024 | https://www.nist.gov/ |

### Tier 3 — AI Security Frameworks

| # | Framework | Issuer | Status | Source |
|---|-----------|--------|--------|--------|
| 164 | MITRE ATLAS | MITRE | Living knowledge base | https://atlas.mitre.org/ |
| 165 | SAFE-AI (Securing AI-Enabled Systems) | MITRE | Published | https://atlas.mitre.org/pdf-files/SAFEAI_Full_Report.pdf |
| 166 | Google Secure AI Framework (SAIF) | Google | Active | https://saif.google/ |
| 167 | ETSI EN 304 223 (Securing AI) | ETSI | Published V2.1.1 | https://www.etsi.org/ |
| 168 | IFAIS AI Safety & Risk Management Framework | IFAIS | V1.0 Feb 2025 | https://www.ifais.org/ |
| 169 | GPAI SAFE Project | GPAI | Published 2024 | https://wp.oecd.ai/ |
| 170 | NSA 8-Nation AI/ML Supply Chain Guidance | NSA + 7 allies | Published Mar 2026 | https://labs.cloudsecurityalliance.org/ |
| 171 | OWASP AISVS (Supply Chain Chapter) | OWASP | Active | https://github.com/OWASP/AISVS/ |
| 172 | ETSI TR 104 048 (Data Supply Chain Security) | ETSI | Published | https://www.etsi.org/ |

### Tier 3 — Privacy Frameworks

| # | Framework | Jurisdiction | Status | Source |
|---|-----------|-------------|--------|--------|
| 173 | LGPD (Brazil Data Protection Law) | Brazil | Effective Sep 2020 | https://www.gov.br/anpd/ |
| 174 | PIPEDA | Canada | Effective, updated 2024 | https://www.linqs.net/ |
| 175 | PDPA Singapore | Singapore | Effective, AI guidelines Mar 2024 | https://www.pdpc.gov.sg/ |
| 176 | Privacy Act 1988 (Australia) | Australia | Active, 2024 amendments | https://www.oaic.gov.au/ |
| 177 | DPDP Act (India) | India | Enacted Aug 2023, Rules 2025 | https://www.indiacode.nic.in/ |
| 178 | Law 25 (Quebec) | Quebec, Canada | Complete Sep 2024 | https://www.canlii.org/ |
| 179 | POPIA (South Africa) | South Africa | Effective Jul 2020 | https://www.webberwentzel.com/ |
| 180 | APPI (Japan) | Japan | Active, 2026 amendments | https://iapp.org/ |
| 181 | NDPR/NDPA (Nigeria) | Nigeria | Effective, GAID 2025 | https://ndpc.gov.ng/ |

### Tier 3 — Sector-Specific AI Regulations

| # | Framework | Sector | Issuer | Status | Source |
|---|-----------|--------|--------|--------|--------|
| 182 | FDA AI/ML SaMD + PCCP Guidance | Healthcare | FDA | Active guidance | https://www.fda.gov/ |
| 183 | FDA AI for Regulatory Decision-Making | Healthcare | FDA | Published 2024 | https://www.fda.gov/ |
| 184 | EMA/FDA 10 Guiding Principles for GAI | Healthcare | EMA+FDA | Published Jan 2025 | https://www.simmons-simmons.com/ |
| 185 | EMA AI in Medicinal Product Lifecycle | Healthcare | EMA | Published | https://www.ema.europa.eu/ |
| 186 | EMA LLMs in Regulatory Science | Healthcare | EMA | Published | https://www.ema.europa.eu/ |
| 187 | IMDRF AI Lifecycle Management Framework | Healthcare | IMDRF | Draft 2026 | https://www.imdrf.org/ |
| 188 | OCC/FDIC/Fed Model Risk Management (SR 26-2) | Finance | US Federal | Enacted Apr 2026 | https://www.occ.gov/ |
| 189 | CFPB AI Credit Denial Guidance | Finance | CFPB | Active | https://www.consumerfinance.gov/ |
| 190 | SEC AI Trading/Advisory Guidance | Finance | SEC | Ongoing | https://www.sec.gov/ |
| 191 | FSB Responsible AI Adoption Practices | Finance | FSB | Published | https://www.fsb.org/ |
| 192 | FINOS AI Governance Framework v1.0 | Finance | FINOS | Published 2024 | https://www.finos.org/ |
| 193 | EEOC AI Adverse Impact Guidance (Title VII) | Employment | EEOC | Published May 2023 | https://www.eeoc.gov/ |
| 194 | US DOL AI and Worker Well-being Principles | Labor | US DOL | Published | https://www.dol.gov/ |
| 195 | SAE J3321 (V&V of AI/ML in Vehicles) | Automotive | SAE | Published 2026 | https://saemobilus.sae.org/ |
| 196 | HIPAA | Healthcare | US Federal | Effective since 1996 | https://www.hhs.gov/hipaa/ |
| 197 | PCI DSS | Finance | PCI SSC | v4.0 effective | https://www.pcisecuritystandards.org/ |
| 198 | FedRAMP | US Federal | GSA | Active | https://www.fedramp.gov/ |

### Tier 3 — AI Risk Taxonomies & Incident Reporting

| # | Framework | Issuer | Status | Source |
|---|-----------|--------|--------|--------|
| 199 | MIT AI Risk Navigator Taxonomies | MIT AI Risk Initiative | Active, updated Apr 2025 | https://www.airi-navigator.com/ |
| 200 | AI Risk Atlas | Academic (arXiv) | Published 2025 | https://arxiv.org/abs/2503.05780 |
| 201 | AIR 2024 (AI Risk Categorization) | Academic | Published 2024 | https://arxiv.org/abs/2406.17864 |
| 202 | OECD Common Reporting Framework of AI Incidents | OECD | Published | https://oecd.ai/ |
| 203 | ETSI TS 104 158 (AI Incident Expression) | ETSI | Published V1.1.1 | https://www.etsi.org/ |
| 204 | AI-IRS (AI Incident Response System) | Japan AISI | V1.0 | https://aisi.go.jp/ |

### Tier 3 — AI Red Teaming/Testing Frameworks

| # | Framework | Issuer | Status | Source |
|---|-----------|--------|--------|--------|
| 205 | Japan AISI Red Teaming Guide | Japan AISI | V1.10 | https://aisi.go.jp/ |
| 206 | AI Red Team Framework (GitHub) | Open source | V0.1 | https://github.com/emmanuelgjr/AI-RedTeam-Framework |
| 207 | GLACIS Red Team Framework | GLACIS | Active | https://www.glacis.io/ |

### Tier 3 — AI Model Documentation Standards

| # | Framework | Issuer | Status | Source |
|---|-----------|--------|--------|--------|
| 208 | Open Model Card (OMC) | Open source | Active | https://openmodelcard.org/ |
| 209 | Model Card Report Ontology (MCRO) | Biomedical research | Published | https://bmcbioinformatics.biomedcentral.com/ |
| 210 | Hugging Face Model Cards | Hugging Face | Industry standard | https://huggingface.co/docs/hub/en/model-cards |
| 211 | System Cards | Meta/Anthropic/AWS | Multiple implementations | https://ai.meta.com/tools/system-cards/ |
| 212 | Datasheets for Datasets | Microsoft Research | Academic standard | https://www.microsoft.com/en-us/research/publication/datasheets-for-datasets |

### Tier 3 — AI Bias/Fairness & Explainability

| # | Framework | Issuer | Status | Source |
|---|-----------|--------|--------|--------|
| 213 | AIF360 (AI Fairness 360) | IBM / LF AI Foundation | Active | https://github.com/ibm/aif360 |
| 214 | Fairlearn | Microsoft (open source) | Active | https://fairlearn.org/ |
| 215 | VXAI (eValuation of Explainable AI) | DFKI | Published | https://vxai.dfki.de/ |
| 216 | Qi-Framework | Academic | Published 2025 | https://link.springer.com/ |

### Tier 3 — AI Content Authenticity/Provenance

| # | Framework | Issuer | Status | Source |
|---|-----------|--------|--------|--------|
| 217 | C2PA (Content Provenance and Authenticity) | C2PA Coalition | Spec 2.2 | https://spec.c2pa.org/ |
| 218 | SynthID | Google DeepMind | Active, deployed | https://arxiv.org/abs/2510.09263 |

### Tier 3 — Children's Safety, DSA, Liability

| # | Framework | Issuer | Status | Source |
|---|-----------|--------|--------|--------|
| 219 | KOSA (Kids Online Safety Act) | US Congress | Passed Senate Jul 2024 | https://www.congress.gov/ |
| 220 | COPPA 2.0 | US Congress | Proposed | — |
| 221 | UK Online Safety Act | UK Parliament | Effective 2023-2024 | https://www.legislation.gov.uk/ |
| 222 | EU Digital Services Act (DSA) | EU | Fully applicable Feb 2024 | https://digital-strategy.ec.europa.eu/ |
| 223 | EU AI Liability Directive | EU Commission | Proposed 2022 | https://eur-lex.europa.eu/ |

### Tier 3 — Defense/Military AI

| # | Framework | Issuer | Status | Source |
|---|-----------|--------|--------|--------|
| 224 | DoD Responsible AI Strategy & Implementation | US DoD | Published Oct 2024 | https://media.defense.gov/ |
| 225 | NATO AI Strategy (Revised) | NATO | Revised Jul 2024 | https://www.nato.int/ |
| 226 | NATO DARB (Data & AI Review Board) | NATO | Established 2022 | https://www.nato.int/ |
| 227 | NATO DCRA v2 | NATO | Published 2025 | https://nhqc3s.hq.nato.int/ |

### Tier 3 — Environmental/ESG, Accessibility, Election, Labor

| # | Framework | Issuer | Status | Source |
|---|-----------|--------|--------|--------|
| 228 | ETSI ES 204 135 (Environmental Impact of AI) | ETSI | Published | https://www.etsi.org/ |
| 229 | W3C AI Accessibility | W3C | Active community group | https://w3c.github.io/ai-accessibility/ |
| 230 | ASC-62 (Accessible & Equitable AI) | Accessibility Standards Canada | In development | https://accessible.canada.ca/ |
| 231 | WCAG 3.0 | W3C | In development | https://www.w3.org/TR/wcag3/ |
| 232 | Munich Security Conference AI Elections Accord | MSC | Active 2025 | https://securityconference.org/ |
| 233 | TIAL Electoral Integrity Framework | TIAL | Published 2025 | https://tial.org/ |
| 234 | EU DSA Electoral Process Guidelines | EU Commission | Published 2024 | https://ec.europa.eu/ |
| 235 | Fairwork AI Principles | Fairwork | V2, effective Nov 2025 | https://fair.work/ |
| 236 | Partnership on AI Workforce Well-being | PAI | Active | https://partnershiponai.org/ |
| 237 | GPAI AI for Fair Work Principles | GPAI | V2 | https://wp.oecd.ai/ |

### Tier 4 — Corporate AI Principles & Frontier Safety

| # | Framework | Issuer | Status | Source |
|---|-----------|--------|--------|--------|
| 238 | Google AI Principles | Google | Updated Feb 2024 | https://ai.google/principles/ |
| 239 | Microsoft Responsible AI Principles | Microsoft | Published | https://www.microsoft.com/en-us/ai/principles-and-approach |
| 240 | OpenAI Principles | OpenAI | Published | https://openai.com/index/our-principles/ |
| 241 | Meta Responsible Use Guide | Meta | Published | https://ai.meta.com/static-resource/responsible-use-guide |
| 242 | Meta Advanced AI Scaling Framework v2 | Meta | Published | https://ai.meta.com/ |
| 243 | IBM AI Ethics Governance Framework | IBM | Published | https://www.ibm.com/think/insights/ |
| 244 | IBM AI Safety and Governance Framework | IBM | Published 2024 | https://newsroom.ibm.com/ |
| 245 | OpenAI Preparedness Framework v2.0 | OpenAI | Published | https://openai.com/index/frontier-risk-and-preparedness/ |
| 246 | OpenAI Frontier Governance Framework | OpenAI | Published May 2026 | https://openai.com/index/openai-frontier-governance-framework/ |
| 247 | Google DeepMind Frontier Safety Framework v3 | Google DeepMind | Published 2025 | https://deepmind.google/ |
| 248 | Anthropic Responsible Scaling Policy v3.0 | Anthropic | Published | https://www.anthropic.com/news/responsible-scaling-policy-v3 |

### Tier 4 — AI Assurance/Certification

| # | Framework | Issuer | Status | Source |
|---|-----------|--------|--------|--------|
| 249 | DNV RP-0671 (Assurance of AI Systems) | DNV | Published | https://www.gov.uk/ai-assurance-techniques/ |
| 250 | AI Trust Alliance Base Specification | AI Trust Alliance | V1.0 Mar 2025 | https://www.trustalliance.ai/ |
| 251 | ETSI TS 104 008 (Continuous Auditing for AI) | ETSI | Published | https://www.etsi.org/ |
| 252 | IEEE ECPAIS (Ethics Certification) | IEEE | Active | https://sagroups.ieee.org/ic16-002/ |

### Tier 4 — Professional Bodies, Multi-Stakeholder, ITU, EU Harmonized

| # | Framework | Issuer | Status | Source |
|---|-----------|--------|--------|--------|
| 253 | ACM Code of Ethics | ACM | Published | https://www.acm.org/code-of-ethics |
| 254 | ACM/IEEE-CS Software Engineering Code | ACM/IEEE-CS | V5.2 | https://www.acm.org/code-of-ethics/software-engineering-code |
| 255 | Partnership on AI (PAI) | PAI | Active | https://partnershiponai.org/ |
| 256 | GPAI (Global Partnership on AI) | OECD/GPAI | Active (46 members) | https://oecd.ai/en/about/about-gpai |
| 257 | ITU-T Y.Sup72 (AI Standardization Roadmap) | ITU-T | Published Nov 2022 | https://www.itu.int/ |
| 258 | ITU-T Y.3172 (ML in Networks) | ITU-T | Published | https://www.itu.int/ |
| 259 | ITU-T Y.4612 (AI of Things) | ITU-T | Published Nov 2025 | https://www.itu.int/ |
| 260 | ITU-T F.748.43 (Foundation Model Platform) | ITU-T | Published Mar 2025 | https://www.itu.int/ |
| 261 | ITU AI Readiness Framework | ITU | Published Sep 2024 | https://www.itu.int/ |
| 262 | CEN-CENELEC JTC 21 (EU AI Act Harmonized Standards) | CEN-CENELEC | Under development | https://www.cencenelec.eu/ |

### Tier 4 — China Technical Standards

| # | Framework | Issuer | Status | Source |
|---|-----------|--------|--------|--------|
| 263 | China AI Safety Governance Framework v1.0 | TC260 | Adopted Sep 2024 | https://digitalpolicyalert.org/change/10871 |
| 264 | China GenAI Safety Requirements Standard | China | Published | https://cset.georgetown.edu/ |
| 265 | China AI Content Labeling Measures | CAC | Effective Sep 2025 | https://reg-intel.com/ |
| 266 | China Facial Recognition Measures | CAC + MPS | Effective Jun 2025 | https://reg-intel.com/ |

---

## Expansion Pass 2 — Additional Frameworks (232 new)

Three parallel research subagents covering (1) binding regulations in uncovered US states and sub-national jurisdictions, (2) new ISO/IEEE/ETSI standards, corporate frameworks, and assurance schemes, (3) security, privacy, sector-specific, risk, auditing, procurement, safety, and multilateral frameworks. Results consolidated and deduplicated against the existing 266.

### Tier 1 — Additional US State AI Laws (52 frameworks)

| # | Framework | State | Status | Key Relevance | Source |
|---|-----------|-------|--------|---------------|--------|
| 267 | Nevada AB 406 | Nevada | Enacted Jul 2025 | Prohibits AI mental health services; requires AI education policies. | https://www.recordinglaw.com/us-laws/ai-laws/nevada-ai-laws/ |
| 268 | Nevada SB 263 | Nevada | Enacted Oct 2025 | AI-generated child pornography coverage. | https://www.recordinglaw.com/us-laws/ai-laws/nevada-ai-laws/ |
| 269 | Nevada SB 213 | Nevada | Enacted 2025 | Nonconsensual deepfake intimate images. | https://www.recordinglaw.com/us-laws/ai-laws/nevada-ai-laws/ |
| 270 | Nevada AB 73 | Nevada | Enacted Jan 2026 | AI disclosure in paid political communications. | https://www.recordinglaw.com/us-laws/ai-laws/nevada-ai-laws/ |
| 271 | Nevada AB 325 | Nevada | Enacted 2025 | AI in emergency planning. | https://www.ailawsbystate.com/state/NV |
| 272 | Wisconsin Act 34 (2025) | Wisconsin | Enacted Oct 2025 | AI-generated intimate imagery criminal code. | https://www.recordinglaw.com/us-laws/ai-laws/wisconsin-ai-laws/ |
| 273 | Michigan Protection from Intimate Deep Fakes Act (HB 4047/4048) | Michigan | Enacted Aug 2025 | Criminal penalties for AI intimate deepfakes. | https://www.recordinglaw.com/us-laws/ai-laws/michigan-ai-laws/ |
| 274 | Michigan Political Deepfake Disclosure (HB 5141/5143/5144/5145) | Michigan | Enacted Feb 2024 | Political AI content disclosure; 90-day election ban. | https://www.recordinglaw.com/us-laws/ai-laws/michigan-ai-laws/ |
| 275 | Michigan HB 4668 (AI Safety and Security Transparency Act) | Michigan | Proposed | Foundation model safety protocols; effective Jan 2026 if passed. | https://legislature.mi.gov/documents/2025-2026/billintroduced/House/htm/2025-HIB-4668.htm |
| 276 | Michigan HB 5579 | Michigan | Proposed | Employer AI monitoring limits (wage, hiring, facial tracking). | https://www.freep.com/story/news/politics/2026/03/16/michigan-artificial-intelligence-regulations-proposals/89137783007/ |
| 277 | Michigan SB 760 | Michigan | Proposed (passed Senate) | Ban chatbots mimicking emotional support for minors. | https://legislature.mi.gov/Bills/Bill?ObjectName=2025-SB-0760 |
| 278 | Georgia SB 9 | Georgia | Enacted 2025 | Criminalizes AI deepfakes in political ads within 90 days of election. | https://www.recordinglaw.com/us-laws/ai-laws/georgia-ai-laws/ |
| 279 | Georgia SB 444 | Georgia | Enacted 2026 | Prohibits AI-only health insurance coverage denials; requires clinical peer review. | https://practiceguides.chambers.com/practice-guides/artificial-intelligence-2026/usa-georgia/trends-and-developments |
| 280 | Georgia SB 540 (Conversational AI Safety Act) | Georgia | Enacted Jul 2027 | Chatbot transparency, child safety, crisis response protocols. | https://regulations.ai/regulations/RAI-US-GA-SB54000-2026 |
| 281 | Georgia HB 147 | Georgia | Proposed (passed House) | State agency AI usage reporting to GTA; annual inventories. | https://www.recordinglaw.com/us-laws/ai-laws/georgia-ai-laws/ |
| 282 | Tennessee SB 0837/HB 0849 | Tennessee | Enacted Apr 2026 | Clarifies "person" excludes AI, algorithms, software, machines. | https://wapp.capitol.tn.gov/apps/BillInfo/Default?BillNumber=HB0849&ga=114 |
| 283 | Tennessee SB 1493 | Tennessee | Enacted May 2026 | Establishes TN AI Advisory Council. | https://wapp.capitol.tn.gov/apps/BillInfo/Default?BillNumber=SB1493&ga=114 |
| 284 | Tennessee SB 2171 (AI Public Safety and Child Protection Transparency Act) | Tennessee | Proposed | Frontier developer safety plans; chatbot child safety plans. | https://capitol.tn.gov/Bills/114/Bill/SB2171.pdf |
| 285 | Alabama HB 172 | Alabama | Enacted Oct 2024 | Criminalizes AI deepfakes used to influence elections. | https://www.recordinglaw.com/us-laws/ai-laws/alabama-ai-laws/ |
| 286 | Alabama SB 63 | Alabama | Proposed (passed Senate) | AI insurer coverage determination limits; physician review for denials. | https://alison.legislature.state.al.us/files/pdf/SearchableInstruments/2026RS/SB63-eng.pdf |
| 287 | Alabama HB 325 | Alabama | Proposed | AI chatbot disclosure; unfair trade practice without notification. | https://alison.legislature.state.al.us/files/pdf/SearchableInstruments/2026RS/HB325-int.pdf |
| 288 | Alabama SB 129 | Alabama | Proposed | GenAI content disclosure (image/video); conspicuous and unavoidable. | https://alison.legislature.state.al.us/files/pdf/SearchableInstruments/2026RS/SB129-int.pdf |
| 289 | Montana SB 212 (Right to Compute Act) | Montana | Enacted Apr 2025 | Constitutional right to own/use computational technology; AI critical infrastructure risk management. | https://regulations.ai/regulations/RAI-US-MT-MS2RCXX-2025 |
| 290 | Montana HB 178 | Montana | Enacted 2025 | Prohibits government AI surveillance/behavioral manipulation; human review of AI decisions. | https://www.recordinglaw.com/us-laws/ai-laws/montana-ai-laws/ |
| 291 | Montana SB 25 | Montana | Enacted 2025 | Bans unlabeled deepfakes of candidates within 60 days of election. | https://www.recordinglaw.com/us-laws/ai-laws/montana-ai-laws/ |
| 292 | Montana HB 514 | Montana | Enacted May 2025 | Criminalizes digitally fabricated sexually explicit imagery. | https://www.recordinglaw.com/us-laws/ai-laws/montana-ai-laws/ |
| 293 | Wyoming HB 102 | Wyoming | Enacted Jul 2026 | Criminal offenses for synthetic sexual material, AI child pornography, AI self-harm promotion. | https://www.wyoleg.gov/2026/Enroll/HB0102.pdf |
| 294 | Wyoming HB 91 | Wyoming | Proposed | Prohibits government AI social scoring and biometric identification without consent. | https://www.wyoleg.gov/Legislation/2026/HB0091 |
| 295 | Idaho SB 1297 (Conversational AI Safety Act) | Idaho | Enacted Jul 2027 | AI disclosure, suicide prevention, mental health misrepresentation prohibition, minor protections. | https://tallyidaho.com/bills/2026/s1297 |
| 296 | Idaho SB 1227 | Idaho | Enacted Jul 2026 | GenAI in public education provisions. | https://legislature.idaho.gov/sessioninfo/2026/legislation/S1227/ |
| 297 | Idaho HB 687 | Idaho | Enacted 2026 | Unbiased AI in state government purchasing. | https://legislature.idaho.gov/sessioninfo/2026/legislation/H0687 |
| 298 | Idaho HB 917 (AI Regulatory Review Act) | Idaho | Proposed | State agency AI for regulation review; human review of AI recommendations. | https://tallyidaho.com/bills/2026/h917 |
| 299 | Hawaii SB 3001 (AI Disclosure and Safety Act) | Hawaii | Proposed (passed May 2026) | AI companion disclosures, suicidal ideation protocols, minor safeguards, annual reports. | https://data.capitol.hawaii.gov/sessions/session2026/bills/SB3001_SD2_.HTM |
| 300 | Hawaii SB 2923 (AI Safety and Regulation Act) | Hawaii | Proposed | Establishes Office of AI Safety and Regulation within DCCA. | https://data.capitol.hawaii.gov/sessions/session2026/bills/SB2923_.PDF |
| 301 | Hawaii SB 2967 | Hawaii | Proposed | Technology-neutral AI disclosure, right to explanation, human review for automated decisions. | https://data.capitol.hawaii.gov/sessions/session2026/bills/SB2967_.HTM |
| 302 | New Jersey A3540/S2544 | New Jersey | Enacted Apr 2025 | Civil and criminal penalties for deceptive AI-generated audio/visual media. | https://www.recordinglaw.com/us-laws/ai-laws/new-jersey-ai-laws/ |
| 303 | New Jersey A4731 | New Jersey | Proposed Mar 2026 | Professional board rules for licensee GenAI use within 3 months. | https://pub.njleg.state.nj.us/Bills/2026/A5000/4731_I1.HTM |
| 304 | New Jersey A5089 (AI Image Disclosure Act) | New Jersey | Proposed May 2026 | Manifest and latent disclosures in AI-generated images/video/audio. | https://pub.njleg.state.nj.us/Bills/2026/A5500/5089_I1.HTM |
| 305 | Pennsylvania HB 2215 | Pennsylvania | Proposed | AI chatbot age verification, responsible dialogue, minor protection offenses. | https://www.palegis.us/legislation/bills/text/HTM/2025/0/HB2215/PN2909 |
| 306 | Pennsylvania HB 2006 (AI Companionship Apps Safety Act) | Pennsylvania | Proposed (advancing) | Companion AI safety features; chatbot suicidal ideation/self-harm prevention. | https://www.transparencycoalition.ai/news/pennsylvania-ai-bills-advancing-prior-to-summer-recess |
| 307 | Pennsylvania HB 2637 | Pennsylvania | Proposed 2026 | Three-year moratorium on children's toys with AI chatbots. | https://www.transparencycoalition.ai/news/pennsylvania-ai-bills-advancing-prior-to-summer-recess |
| 308 | Pennsylvania SB 1368 | Pennsylvania | Proposed Jun 2026 | Prohibits AI nudification apps; $100K/violation civil penalty. | https://www.transparencycoalition.ai/news/pennsylvania-ai-bills-advancing-prior-to-summer-recess |
| 309 | Pennsylvania HB 2534 (AI Disclosure Act) | Pennsylvania | Proposed (advancing) | Large online AI providers (2M+ monthly users) must offer manifest disclosure option. | https://www.transparencycoalition.ai/news/pennsylvania-ai-bills-advancing-prior-to-summer-recess |
| 310 | Ohio HB 813 | Ohio | Proposed | AI-generated product watermarks; disclosure when AI mimics human behavior. | https://search-prod.lis.state.oh.us/api/v2/general_assembly_136/legislation/hb813/00_IN/html/ |
| 311 | Ohio HB 392 (Right to Compute Act) | Ohio | Proposed | AI in critical infrastructure regulation; risk management for AI-controlled systems. | https://www.ailawsbystate.com/state/OH |
| 312 | Ohio HB 579/SB 164 | Ohio | Proposed | Transparency and ethical guidelines for AI in health insurance decisions. | https://www.ailawsbystate.com/state/OH |
| 313 | Ohio HB 469 | Ohio | Proposed | Declares AI nonsentient; prohibits legal personhood for AI. | https://search-prod.lis.state.oh.us/api/v2/general_assembly_136/legislation/hb469/00_IN/pdf/ |
| 314 | Louisiana SB 474 (Protecting LA Infrastructure from AI Risk Act) | Louisiana | Proposed (Senate final passage) | Frontier AI developer frameworks, transparency reports, catastrophic risk assessments. | https://legis.la.gov/legis/ViewDocument.aspx?d=1457225 |
| 315 | Louisiana HB 734 | Louisiana | Proposed | Prohibits state AI contracts with foreign countries of concern; AI bill of rights; minor chatbot restrictions. | https://www.legis.la.gov/Legis/ViewDocument.aspx?d=1446623 |
| 316 | Alaska HB 47 | Alaska | Proposed (passed House Feb 2026) | Criminalizes AI-generated child sexual abuse material as Class B felony. | https://alaskabeacon.com/2026/02/04/lawmakers-advance-bill-to-add-state-felony-charges-for-ai-generated-child-sexual-abuse-material/ |
| 317 | Alaska SB 2 | Alaska | Proposed | Election deepfake disclosures; state agency AI restrictions; data transfer rules. | https://www.recordinglaw.com/us-laws/ai-laws/alaska-ai-laws/ |
| 318 | Alaska HCR 3 | Alaska | Proposed | Joint Legislative Task Force on AI; policy recommendations. | https://www.akleg.gov/basis/Bill/Detail/?Root=HCR++3 |

### Tier 1 — Additional Sub-National/Regional Regulations (19 frameworks)

| # | Framework | Jurisdiction | Status | Key Relevance | Source |
|---|-----------|-------------|--------|---------------|--------|
| 319 | Catalonia AI 2030 Strategy | Catalonia (Spain) | Enacted Dec 2025 | €1B investment, 88 actions across 8 pillars for responsible AI leadership. | https://regulations.ai/regulations/RAI-ES-CT-CA2SEXX-2025 |
| 320 | Catalonia AI Registry | Catalonia (Spain) | Operational | Public administration AI system registry; EU AI Act compliance. | https://web.gencat.cat/en/generalitat/dades-indicadors/intelligencia-artificial |
| 321 | Catalonia FRIA Methodology | Catalonia (Spain) | Implemented 2025 | First European fundamental rights impact assessment methodology for AI. | https://www.apdcat.cat/en/actualitat/noticies/2025/ |
| 322 | Scotland AI Strategy 2026-2031 | Scotland (UK) | Enacted Mar 2026 | Five-year strategy; OECD-aligned; AI Scotland transformation programme. | https://www.gov.scot/ |
| 323 | UK DPA 2018 (Code of Practice on AI) Regulations 2026 | UK | Enacted May 2026 | Requires ICO to prepare code on AI/ADM personal data processing. | https://www.legislation.gov.uk/uksi/2026/425/made |
| 324 | Quebec Loi 25 §12.1 (Automated Decision Disclosure) | Quebec (Canada) | Enacted Sep 2023 | Automated decision disclosure, explanation on request, human review right. | https://silaws.com/2026/05/31/automated-decision-ai-disclosure-loi25/ |
| 325 | Quebec GenAI in Public Administration | Quebec (Canada) | Enacted Dec 2025 | Governance framework for GenAI by public bodies; data protection, training. | https://www.newswire.ca/fr/ |
| 326 | Quebec Guide for Workplaces on AI Implementation | Quebec (Canada) | Published Jun 2026 | Benchmarks for responsible AI integration; health and safety considerations. | https://www.quebec.ca/ |
| 327 | Ontario Responsible Use of AI Directive | Ontario (Canada) | Enacted Dec 2024 | Transparent, responsible AI use by ministries and agencies; risk management. | https://www.ontario.ca/page/responsible-use-artificial-intelligence-directive |
| 328 | Ontario Enhancing Digital Security and Trust Act, 2024 | Ontario (Canada) | Enacted (not in force) | Public sector AI disclosure, accountability frameworks, risk management. | https://www.ontario.ca/laws/statute/24e24/v1 |
| 329 | Ontario Superior Court AI Practice Directions | Ontario (Canada) | Enacted Feb 2026 | Responsible AI use in civil, family, criminal court proceedings. | https://www.ontariocourts.ca/scj/ |
| 330 | Flanders AI Policy Plan 2024-2028 | Flanders (Belgium) | Enacted Jan 2024 | €70M/year for AI ecosystem; ethical impact assessments for funded projects. | https://regulations.ai/regulations/RAI-BE-NA-FAP2XXX-2024 |
| 331 | Flanders AI-Ready Public Administration | Flanders (Belgium) | Operational | AI governance tools for 90+ Flemish public entities; EU AI Act guidance. | https://www.unesco.org/en/artificial-intelligence/recommendation-ethics/flemish-government |
| 332 | Lombardy AI Project of Law | Lombardy (Italy) | Proposed (approved by Giunta) | AI in PA and business; Scientific Committee, Regional Charter for AI. | https://www.regione.lombardia.it/ |
| 333 | Baden-Württemberg LDSG Reform | Baden-Württemberg (Germany) | Enacted Feb 2026 | State data protection law incorporating EU AI Act definitions for AI systems. | https://www.datenschutzticker.de/2026/03/ |
| 334 | Baden-Württemberg E-Government Act Amendments | Baden-Württemberg (Germany) | Enacted 2026 | Allows fully automated administrative acts including AI use. | https://www.baden-wuerttemberg.de/ |
| 335 | Brittany Mégalis Sovereign AI Initiative | Brittany (France) | Operational 2025-2026 | Sovereign GenAI for 15 Breton collectivities; sovereignty, environmental, security focus. | https://www.megalis.bretagne.bzh/ |
| 336 | Alberta OIPC AI Framework Report | Alberta (Canada) | Report Aug 2025 | Recommends standalone provincial AI law; contest automated decisions, privacy-by-design. | https://oipc.ab.ca/ |
| 337 | Bavarian AI Act Accelerator | Bavaria (Germany) | Operational 2024-2026 | €1.6M to help SMEs implement EU AI Act; lower barriers for AI use. | https://www.stmd.bayern.de/ |

### Tier 2 — Additional ISO/IEC Standards (9 frameworks)

| # | Standard | Focus | Status | Source |
|---|----------|-------|--------|--------|
| 338 | ISO/IEC FDIS 27090 | Cybersecurity — AI security threats and compromises | FDIS (approval phase 2026) | https://www.iso.org/standard/56581.html |
| 339 | ISO/IEC FDIS 24970 | AI system logging — capabilities, requirements, information model | FDIS (under development) | https://www.iso.org/standard/88723.html |
| 340 | ISO/IEC TR 42106 | Differentiated benchmarking of AI system quality characteristics | Under publication (expected May 2026) | https://www.iso.org/standard/86903.html |
| 341 | ISO/IEC CD TS 25568 | Guidance on addressing risks in generative AI systems | Committee Draft | https://www.iso.org/standard/90754.html |
| 342 | ISO/IEC AWI 26160 | Enhancing ISO/IEC 15408 (Common Criteria) for AI functionality evaluation | Approved Work Item | https://www.iso.org/standard/92749.html |
| 343 | ISO/IEC AWI 25589 | Framework for human-machine teaming | Approved Work Item | https://www.iso.org/standard/90831.html |
| 344 | ISO/IEC AWI 25870 | Data elements for reporting AI system incidents | Approved Work Item | https://www.iso.org/standard/91804.html |
| 345 | ISO/IEC AWI 25623 | Machine learning model description framework | Approved Work Item | https://www.iso.org/standard/90933.html |
| 346 | ISO/IEC AWI 25704 | Process assessment model for AI system life cycle processes | New Project | https://www.iso.org/standard/91246.html |

### Tier 2 — Additional IEEE Standards (6 frameworks)

| # | Standard | Focus | Status | Source |
|---|----------|-------|--------|--------|
| 347 | IEEE 3559-2026 | Technical requirements for multimodal LLMs in smart home applications | Published Jan 2026 | https://standards.ieee.org/ieee/3559/11980/ |
| 348 | IEEE 7014.1-2026 | Ethical considerations of emulated empathy in partner-based GPAI systems | Published Jun 2026 | https://standards.ieee.org/ieee/7014.1/11609/ |
| 349 | IEEE P8000.1 | Method and criteria to assess trustworthiness of AI systems | Active PAR | https://standards.ieee.org/ieee/8000.1/12593/ |
| 350 | IEEE 3482-2026 | Technical requirements for modeling/control of 3D digital human based on ML | Published 2026 | https://standards.ieee.org/ |
| 351 | IEEE P4501 | Framework and requirements of physical AI in manufacturing | Under development | https://standards.ieee.org/ |
| 352 | IEEE P3123 | AI and machine learning terminology | Under development | https://standards.ieee.org/ |

### Tier 2 — Additional ETSI Standards (4 frameworks)

| # | Standard | Focus | Status | Source |
|---|----------|-------|--------|--------|
| 353 | ETSI TS 104 223 V1.1.1 | Baseline cyber security requirements for AI models and systems (TS version) | Published Apr 2025 | https://www.etsi.org/deliver/etsi_TS/104200_104299/104223/01.01.01_60/ts_104223v010101p.pdf |
| 354 | ETSI TR 104 128 V1.1.1 | Guide to cyber security for AI models and systems | Published May 2025 | https://www.etsi.org/deliver/etsi_tr/104100_104199/104128/01.01.01_60/tr_104128v010101p.pdf |
| 355 | ETSI TS 104 224 V1.1.1 | Explicability and transparency of AI processing | Published Mar 2025 | https://www.etsi.org/deliver/etsi_ts/104200_104299/104224/01.01.01_60/ts_104224v010101p.pdf |
| 356 | ETSI TS 104 033 V1.1.1 | Security requirements for an AI computing platform | Published May 2026 | https://www.etsi.org/deliver/etsi_ts/104000_104099/104033/01.01.01_60/ts_104033v010101p.pdf |

### Tier 2 — Additional National Standards Body AI Standards (11 frameworks)

| # | Standard | Issuer | Status | Focus | Source |
|---|----------|--------|--------|-------|--------|
| 357 | DIN SPEC 92004 | DIN (Germany) | Published | AI quality requirements: risk analysis for development and operation | https://www.din.de/en/innovation-and-research/artificial-intelligence/ai-din-spec |
| 358 | DIN SPEC 92001-3 | DIN (Germany) | Published | AI lifecycle processes and quality: explainability | https://www.din.de/en/innovation-and-research/artificial-intelligence/ai-din-spec |
| 359 | AFNOR Spec 2314 | AFNOR (France) | Published | General framework for frugal AI | https://www.afnor.org/en/artificial-intelligence/ |
| 360 | AFNOR Spec 2401 | AFNOR (France) | Published | AI skills assessment test | https://www.afnor.org/en/artificial-intelligence/ |
| 361 | PR NF EN 18286 | AFNOR (France) | Draft | AI quality management system for EU AI Regulation | https://norminfo.afnor.org/ |
| 362 | GB/T 45288.1-2025 | SAC (China) | Published Feb 2025 | AI large models Part 1: general requirements | https://std.samr.gov.cn/ |
| 363 | GB/T 47507-2026 | SAC (China) | Published Apr 2026 | AI trustworthiness: general rules | https://ndls.cnis.ac.cn/ |
| 364 | GB/T 46284-2025 | SAC (China) | Published Oct 2025 | AI: technical specifications of federated learning | https://ndls.cnis.ac.cn/ |
| 365 | GB/T 46069.2-2025 | SAC (China) | Published Aug 2025 | AI operator interface Part 2: neural network class | https://std.samr.gov.cn/ |
| 366 | GB/T 45654-2025 | SAC (China) | Published Apr 2025 | Cybersecurity: basic security requirements for GenAI service | https://www.gb-gbt.com/PDF/Chinese.aspx/GBT45654-2025 |
| 367 | UNI 11621-8:2026 | UNI (Italy) | Published Apr 2026 | Professional profiles in AI sector: governance, risk, security, compliance | https://store.uni.com/en/uni-11621-8-2026 |

### Tier 2 — Additional National AI Strategies (7 frameworks)

| # | Framework | Country | Status | Source |
|---|-----------|---------|--------|--------|
| 368 | Brazil AI Plan (PBIA) 2025 | Brazil | Published Jun 2025 | https://www.gov.br/mcti/ |
| 369 | Poland AI Policy 2030 (Updated 2025) | Poland | Published 2025 | https://www.gov.pl/web/cyfryzacja/ |
| 370 | Hungary Renewed AI Strategy 2025-2030 | Hungary | Published Sep 2025 | https://cms.law/en/hun/ |
| 371 | Czech Republic AI Strategy 2030 Action Plan 2025 | Czech Republic | Published Apr 2025 | https://regulations.ai/regulations/RAI-CZ-NA-APNAIXX-2025 |
| 372 | Singapore National AI Strategy Update 2026 | Singapore | Published May 2026 | https://www.smartnation.gov.sg/initiatives/national-ai-strategy/ |
| 373 | Malaysia National AI Office Action Plan 2026-2030 | Malaysia | Published 2025 | https://ai.gov.my/ |
| 374 | Indonesia AI Roadmap and Ethics Presidential Regulation | Indonesia | Draft (expected early 2026) | https://regulations.ai/regulations/RAI-ID-NA-RPPTKXX-2025 |

### Tier 3 — Additional Security Frameworks (6 frameworks)

| # | Framework | Issuer | Status | Source |
|---|-----------|--------|--------|--------|
| 375 | NIST IR 8596 (Cyber AI Profile) | NIST | Preliminary Draft Dec 2025 | https://csrc.nist.gov/pubs/ir/8596/iprd |
| 376 | NIST SP 800-53 COSAiS (Control Overlays for Securing AI) | NIST | In development | https://csrc.nist.gov/Projects/cosais |
| 377 | ENISA FAICP | ENISA (EU) | Published Jun 2026 | https://www.faicp-framework.com/ |
| 378 | UK/US Guidelines for Secure AI System Development | NCSC + CISA | Published 2025 | https://www.ncsc.gov.uk/ |
| 379 | AATMF v2 (Adversarial AI Threat Modeling Framework) | Open source | Public Release Aug 2025 | https://github.com/SnailSploit/AATMF-Adversarial-AI-Threat-Modeling-Framework |
| 380 | FCC CSRIC IX: AI-ML Threats to Networks | FCC | Report published 2025 | https://www.fcc.gov/ |

### Tier 3 — Additional Privacy Frameworks (3 frameworks)

| # | Framework | Jurisdiction | Status | Source |
|---|-----------|-------------|--------|--------|
| 381 | California AB-853 (AI Transparency Act) | California | Enacted Sep 2025 | https://leginfo.legislature.ca.gov/faces/billCompareClient.xhtml?bill_id=202520260AB853 |
| 382 | S. 2367 (AI Accountability and Personal Data Protection Act) | US Federal | Introduced Jul 2025 | https://www.govtrack.us/congress/bills/119/s2367/text |
| 383 | EDPS Orientations on Generative AI and EUDPR | EU (EDPS) | Published Oct 2025 | https://www.edps.europa.eu/ |

### Tier 3 — Additional Sector-Specific Frameworks (22 frameworks)

| # | Framework | Sector | Issuer | Status | Source |
|---|-----------|--------|--------|--------|--------|
| 384 | Virginia AI in Education Act | Education | Virginia GA | Enacted Apr 2026 | https://lis.blob.core.windows.net/files/1224760.PDF |
| 385 | Maryland Subtitle 22: AI in Education | Education | Maryland GA | Enacted 2026 | https://mgaleg.maryland.gov/ |
| 386 | Scottish Guidelines for AI in Schools | Education | Scottish Gov | Published Mar 2026 | https://www.gov.scot/ |
| 387 | EU Council Conclusions on Teachers in Era of AI | Education | Council of EU | Adopted 2026 | https://eur-lex.europa.eu/ |
| 388 | Ofgem AI in Energy Sector Guidance | Energy | Ofgem (UK) | Consultation concluded May 2025 | https://www.ofgem.gov.uk/ |
| 389 | California SB-1011 (Utility Infrastructure AI Safety Act) | Energy | California | Introduced 2025-2026 | https://leginfo.legislature.ca.gov/ |
| 390 | UNECE Framework for Fully Driverless ADS | Transportation | UNECE WP.29 | Adopted Jun 2026 | https://unece.org/ |
| 391 | UK Automated Vehicles Permits Regulations 2026 | Transportation | UK | Made May 2026 | https://www.legislation.gov.uk/uksi/2026/439/made |
| 392 | US H.R. 7390 (SELF DRIVE Act 2026) | Transportation | US House | Introduced Feb 2026 | https://www.congress.gov/119/bills/hr7390/ |
| 393 | Maharashtra MahaAgri-AI Policy 2025-29 | Agriculture | Maharashtra (India) | Approved Jun 2025 | https://regulations.ai/regulations/RAI-IN-MA-MAHMA20-2025 |
| 394 | USDA FY 2025-2026 AI Strategy | Agriculture | USDA | Published 2025 | https://data.aclum.org/ |
| 395 | Joint Declaration on AI, Freedom of Expression and Media Freedom | Media | UN/OSCE/OAS/ACHPR | Adopted Oct 2025 | https://www.ohchr.org/ |
| 396 | UNESCO Regional Declaration of Press Councils on AI | Media | UNESCO | Adopted Jun 2025 | https://articles.unesco.org/ |
| 397 | UNESCO Guidelines for AI in Courts and Tribunals | Legal/Judicial | UNESCO | Published Dec 2025 | https://www.unesco.org/en/articles/guidelines-use-ai-systems-courts-and-tribunals |
| 398 | Brazil CNJ Resolution 615/2025 | Legal/Judicial | Brazilian National Council of Justice | Effective Jul 2025 | https://regulations.ai/regulations/RAI-BR-NA-RCN6CXX-2025 |
| 399 | CEPEJ Guidelines on Generative AI for Courts | Legal/Judicial | CEPEJ (Council of Europe) | Draft 2025 | https://rm.coe.int/ |
| 400 | IAIS Application Paper on AI Supervision | Insurance | IAIS | Published Jul 2025 | https://www.iais.org/ |
| 401 | Hawaii Insurance Division AI Memorandum | Insurance | Hawaii Insurance Division | Issued Dec 2025 | https://cca.hawaii.gov/ |
| 402 | NCOIL Model AI for Insurers Compliance Act | Insurance | NCOIL | Draft Nov 2025 | https://ncoil.org/ |
| 403 | NY A3930 (AI in Rental Housing and Loans) | Real Estate | NY Assembly | Introduced 2025-2026 | https://www.nysenate.gov/legislation/bills/2025/A3930 |
| 404 | NY A9028 (Virtual Agents and AI in Real Estate) | Real Estate | NY Assembly | Introduced Sep 2025 | https://assembly.state.ny.us/ |
| 405 | BEREC Report on AI in Telecommunications | Telecommunications | BEREC (EU) | Published Jun 2023 | https://www.berec.europa.eu/ |

### Tier 3 — Additional Risk Frameworks (2 frameworks)

| # | Framework | Issuer | Status | Source |
|---|-----------|--------|--------|--------|
| 406 | Frontier AI Risk Management Framework in Practice | Academic (Liu et al.) | Technical Report Feb 2026 | https://arxiv.org/pdf/2602.14457 |
| 407 | NIST AI 100-2 E2025 (Adversarial ML Taxonomy) | NIST | Final Mar 2025 | https://csrc.nist.gov/pubs/ai/100/2/e2025/final |

### Tier 3 — Additional Auditing/Assessment Frameworks (5 frameworks)

| # | Framework | Issuer | Status | Source |
|---|-----------|--------|--------|--------|
| 408 | IIA AI Auditing framework | Institute of Internal Auditors | Updated Sep 2024 | https://www.theiia.org/ |
| 409 | TÜV AUSTRIA Trusted AI Framework | TÜV AUSTRIA | Continuous development | https://arxiv.org/html/2509.08852v1 |
| 410 | CSA AI Controls Matrix (AICM) | Cloud Security Alliance | Published | https://cloudsecurityalliance.org/artifacts/ai-controls-matrix |
| 411 | EDPB AI Auditing Checklist | European Data Protection Board | Published 2024 | https://www.edpb.europa.eu/ |
| 412 | Multidimensional Approach to Ethical AI Auditing | Academic (Teixeira et al.) | Published Oct 2025 | https://ojs.aaai.org/index.php/AIES/article/view/36732 |

### Tier 3 — Additional Procurement Frameworks (5 frameworks)

| # | Framework | Issuer | Status | Source |
|---|-----------|--------|--------|--------|
| 413 | UK Crown Commercial Service AI DPS (RM6200) | UK Government | Extended to Feb 2029 | https://www.webprod-cms.crowncommercial.gov.uk/agreements/RM6200 |
| 414 | EU Model Contractual AI Clauses | European Commission | Updated 2025 | https://public-buyers-community.ec.europa.eu/ |
| 415 | OMB M-25-22 (Federal AI Buying Spec) | US OMB | Effective Oct 2025 | https://truvisory.com/federal/omb-buying-spec/ |
| 416 | California EO N-5-26 (Trusted AI Procurement) | California Governor | Issued 2026 | https://www.gov.ca.gov/ |
| 417 | Japanese Government Guideline for Procurement of GenAI | Japan Digital Agency | Published Jun 2025 | https://www.digital.go.jp/ |

### Tier 3 — Additional Safety/Testing Frameworks (5 frameworks)

| # | Framework | Issuer | Status | Source |
|---|-----------|--------|--------|--------|
| 418 | SAGE (Safety AI Generic Evaluation Framework) | Academic (Jindal et al.) | Published 2025 | https://aclanthology.org/2025.emnlp-industry.2.pdf |
| 419 | NVIDIA Whetstone (GenAI Robustness Testing) | NVIDIA | Open source 2025 | https://github.com/NVIDIA/whetstone |
| 420 | OpenAgentSafety | Academic | Published 2025 | https://arxiv.org/html/2507.06134v1 |
| 421 | OASIS (AI Agent Safety/Security Evaluation) | OpenCompass | Open source | https://github.com/open-compass/OASIS |
| 422 | Anthropic Petri (Parallel Exploration for Risky Interactions) | Anthropic | Open source 2025 | https://www.anthropic.com/research/petri-open-source-auditing |

### Tier 3 — Additional Technology-Specific Frameworks (8 frameworks)

| # | Framework | Type | Issuer | Status | Source |
|---|-----------|------|--------|--------|--------|
| 423 | EU General-Purpose AI Code of Practice | LLM/Foundation Model | European Commission | Published Jul 2025 | https://digital-strategy.ec.europa.eu/en/policies/contents-code-gpai |
| 424 | PAI Documenting the Impacts of Foundation Models | LLM/Foundation Model | Partnership on AI | Progress Report Feb 2025 | https://partnershiponai.org/ |
| 425 | From Models to Metrics (LLM Governance) | LLM/Foundation Model | Academic | Published 2025 | https://www.mdpi.com/2813-2203/5/1/8 |
| 426 | Singapore MGF for Agentic AI v1.5 | Agentic AI | IMDA Singapore | Published May 2026 | https://www.imda.gov.sg/ |
| 427 | SARC (Governance-by-Architecture for Agentic AI) | Agentic AI | Academic | Published 2025 | https://arxiv.org/pdf/2605.07728 |
| 428 | CAIS (Controlled Agentic AI Systems) | Agentic AI | Academic | Published May 2026 | https://www.mdpi.com/2504-4990/8/5/125 |
| 429 | Generative AI Governance Framework (Connor Group) | Generative AI | Connor Group | Published | https://www.genai.global/frameworks/GenAI_Framework_English.pdf |
| 430 | Linux Foundation Responsible Generative AI Framework (RGAF) | Generative AI | Linux Foundation | Published Mar 2025 | https://lfaidata.foundation/ |

### Tier 3 — Additional Ethics Frameworks (3 frameworks)

| # | Framework | Issuer | Status | Source |
|---|-----------|--------|--------|--------|
| 431 | IFAIS Ethical AI Development Guidelines (IFAIS-ETH-001) | IFAIS | V1.0 Feb 2025 | https://ifais.org/files/publications/Ethical_AI_Development_Guidelines.pdf |
| 432 | Vietnam Circular 05/2026 (National AI Ethics Framework) | Vietnam Ministry of Science and Technology | Effective Mar 2026 | https://thuvienphapluat.vn/ |
| 433 | Building the Ethical AI Framework: From Philosophy to Practice | Academic (Springer AI and Ethics) | Published Feb 2026 | https://link.springer.com/article/10.1007/s43681-026-01003-8 |

### Tier 3 — Additional Multilateral Organization Frameworks (14 frameworks)

| # | Framework | Issuer | Status | Source |
|---|-----------|--------|--------|--------|
| 434 | World Bank AI Playbook Handbook | World Bank | Published 2025 | https://documents1.worldbank.org/ |
| 435 | World Bank Global Trends in AI Governance | World Bank | Published Jul 2025 | https://www.worldbank.org/en/topic/digital/publication/global-trends-in-ai-governance |
| 436 | World Bank Digital Progress and Trends Report 2025 | World Bank | Published 2025 | https://www.worldbank.org/en/publication/dptr2025-ai-foundations |
| 437 | IMF AI Projects in Financial Supervisory Authorities | IMF | Working Paper WP/25/199 Oct 2025 | https://www.imf.org/en/publications/wp/issues/2025/10/03/ai-projects-in-financial-supervisory-authorities-570625 |
| 438 | IMF GenAI for Compliance Risk Analysis in Tax/Customs | IMF | Technical Note TNM/2025/13 Aug 2025 | https://www.imf.org/ |
| 439 | WHO Ethics and Governance of AI for Health: LMMs | WHO | Published 2025 | https://www.who.int/publications/i/item/9789240084759 |
| 440 | WHO Regulatory Considerations on AI for Health | WHO + ITU | Published | https://www.who.int/publications/i/item/9789240078871 |
| 441 | WHO European Regional Report: AI Reshaping Health Systems | WHO Europe | Published 2025 | https://www.who.int/europe/publications/i/item/WHO-EURO-2025-12707-52481-81028 |
| 442 | ILO Report: A Moment of Choice — Harnessing AI for Decent Work | ILO | ILC.114/Report I(B) 2026 | https://www.ilo.org/ |
| 443 | ILO Compendium of Best Practices for Human-Centered AI | ILO/OECD | Published 2024 | https://www.ilo.org/ |
| 444 | ILO Global Case Studies of Social Dialogue on AI | ILO | Working Paper 144, 2025 | https://www.ilo.org/ |
| 445 | World Trade Report 2025: Making Trade and AI Work Together | WTO | Published Sep 2025 | https://www.wto.org/english/res_e/booksp_e/wtr25_e.pdf |
| 446 | WTO Trading with Intelligence: How AI Shapes International Trade | WTO | Published 2025 | https://www.wto.org/english/res_e/booksp_e/trading_with_intelligence_e.pdf |
| 447 | WIPO AI Infrastructure Interchange (AIII) Framework | WIPO | Launched 2026 | https://www.wipo.int/ |

### Tier 4 — Additional Corporate AI Governance Frameworks (11 frameworks)

| # | Framework | Issuer | Status | Source |
|---|-----------|--------|--------|--------|
| 448 | Anthropic Frontier Compliance Framework (FCF) | Anthropic | Published Mar 2026 | https://trust.anthropic.com/ |
| 449 | Cohere Secure AI Frontier Model Framework | Cohere | Published Feb 2025 | https://cohere.com/security/ |
| 450 | xAI Risk Management Framework | xAI | Published Aug 2025 | https://data.x.ai/2025-08-20-xai-risk-management-framework.pdf |
| 451 | xAI Frontier Artificial Intelligence Framework | xAI | Published Dec 2025 | https://data.x.ai/2025-12-31-xai-frontier-artificial-intelligence-framework.pdf |
| 452 | AWS Responsible AI Lens (Well-Architected Framework) | AWS | Published Nov 2025 | https://docs.aws.amazon.com/wellarchitected/latest/responsible-ai-lens/ |
| 453 | AWS Cloud Adoption Framework for AI, ML and GenAI | AWS | Published 2025 | https://docs.aws.amazon.com/whitepapers/latest/aws-caf-for-ai/ |
| 454 | NVIDIA Frontier AI Risk Assessment Framework | NVIDIA | Published 2025 | https://images.nvidia.com/content/pdf/NVIDIA-Frontier-AI-Risk-Assessment.pdf |
| 455 | SAP Responsible AI Framework | SAP | Published 2025 | https://www.sap.com/products/artificial-intelligence/ai-ethics.html |
| 456 | Oracle OCI AI Governance Framework | Oracle | Published 2026 | https://docs.oracle.com/en-us/iaas/Content/generative-ai/governance.htm |
| 457 | Salesforce AI Acceptable Use Policy | Salesforce | Updated Dec 2025 | https://www.salesforce.com/ |
| 458 | Mistral AI Studio Governance Framework | Mistral AI | Published 2025 | https://mistral.ai/news/ai-studio/ |

### Tier 4 — Additional Assurance/Certification Schemes (7 frameworks)

| # | Framework | Issuer | Status | Source |
|---|-----------|--------|--------|--------|
| 459 | CSA STAR for AI | Cloud Security Alliance | Launched Oct 2025 | https://cloudsecurityalliance.org/star/ai |
| 460 | Global AI Assurance Sandbox | IMDA + AI Verify Foundation | Launched Jul 2025 | https://oecd.ai/en/dashboards/policy-initiatives/global-ai-assurance-sandbox |
| 461 | UK Trusted Third-Party AI Assurance Roadmap | UK DSIT | Published 2025 | https://www.gov.uk/government/publications/trusted-third-party-ai-assurance-roadmap/ |
| 462 | UK AI Assurance Stakeholder Consortium | UK DSIT + BCS | Launched Jun 2025 | https://www.computerweekly.com/ |
| 463 | PwC Assurance for AI | PwC | Launched Jun 2025 | https://www.pwc.com/us/en/about-us/newsroom/assurance-ai-press-release.html |
| 464 | CompTIA SecAI+ Certification | CompTIA | Launched Feb 2026 | https://www.comptia.org/en/certifications/secai/ |
| 465 | CSA Trusted AI Safety Expert (TAISE) Certificate | CSA + Northeastern University | Published 2026 | https://cloudsecurityalliance.org/education/taise |

### Tier 4 — Additional Industry Consortium Frameworks (4 frameworks)

| # | Framework | Issuer | Status | Source |
|---|-----------|--------|--------|--------|
| 466 | NIST AI Consortium (expanded scope) | NIST | Expanded May 2026 | https://www.nist.gov/news-events/news/2026/05/nist-expands-ai-consortiums-scope-calls-new-members |
| 467 | Appia Foundation | Linux Foundation | Launched 2025 | https://www.linuxfoundation.org/press/linux-foundation-launches-appia-foundation-to-establish-standardized-conformity-specifications-across-the-ai-value-chain |
| 468 | African-European Pan-African AI Governance Consortium | University of Bremen + partners | Launched 2025 | https://trendsnafrica.com/ |
| 469 | Berkeley GPAI Risk-Management Standards Profile | UC Berkeley CLTC | V1.2.1 Apr 2026 | https://cltc.berkeley.edu/ |

### Tier 4 — Additional Open-Source AI Governance Frameworks (5 frameworks)

| # | Framework | Issuer | Status | Source |
|---|-----------|--------|--------|--------|
| 470 | Agent Decision Protocol (ADP) | OpenAgentGovernance | Published 2025 | https://github.com/OpenAgentGovernance/agent-decision-protocol |
| 471 | Microsoft Agent Governance Toolkit | Microsoft | Published Mar 2026 | https://github.com/microsoft/Agent-Governance-Toolkit |
| 472 | GovAI — AI Governance-as-Code | Articence | Published Mar 2026 | https://github.com/articenceinc/govai |
| 473 | AIGRC Open Standard | AIGRC | Published Dec 2025 | https://github.com/aigrc/aigrc |
| 474 | AEGIS Governance | AEGIS Initiative | Published Mar 2026 | https://github.com/aegis-initiative/aegis-governance |

### Tier 4 — Additional Professional/Multi-Stakeholder Frameworks (6 frameworks)

| # | Framework | Issuer | Status | Source |
|---|-----------|--------|--------|--------|
| 475 | OECD Due Diligence Guidance for Responsible AI | OECD | Published 2025 | https://www.oecd.org/en/publications/oecd-due-diligence-guidance-for-responsible-ai_41671712-en.html |
| 476 | AI Governance Playbook | Council on AI Governance (CAIG) | Published 2025 | https://oecd.ai/en/catalogue/tools/ai-governance-playbook |
| 477 | AI Governance Principles for Boards | KPMG | Published Jun 2026 | https://assets.kpmg.com/ |
| 478 | WEF Advancing Responsible AI Innovation: A Playbook | WEF AI Governance Alliance | Published 2025 | https://www.weforum.org/publications/advancing-responsible-ai-innovation-a-playbook/ |
| 479 | WEF Blueprint for Intelligent Economies | WEF AI Governance Alliance | Published 2025 | https://www.weforum.org/publications/blueprint-for-intelligent-economies/ |
| 480 | International AI Safety Report 2026 | International expert panel (UK-led) | Published 2026 | https://internationalaisafetyreport.org/ |

### Tier 4 — Additional Government Technical Standards (4 frameworks)

| # | Framework | Issuer | Status | Source |
|---|-----------|--------|--------|--------|
| 481 | Australian Government AI Technical Standard | Digital Transformation Agency (Australia) | Published Aug 2025 | https://www.digital.gov.au/policy/ai/AI-technical-standard |
| 482 | Canada Directive on Automated Decision-Making (Updated 2025) | Treasury Board of Canada | Updated Jun 2025 | https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=32592 |
| 483 | Japan AI Guidelines for Business Ver1.2 | Japan (MIC + METI) | Published 2025 | https://www.soumu.go.jp/main_content/001064309.pdf |
| 484 | Japan AI Act Guidelines | Japan (CSTP) | Published Dec 2025 | https://www8.cao.go.jp/cstp/ai/ai_guideline/ai_gl_2025.pdf |

### Tier 4 — Additional National Frameworks (3 frameworks)

| # | Framework | Country | Status | Source |
|---|-----------|---------|--------|--------|
| 485 | Japan AI Guidelines for Business Ver1.1 | Japan | Published Mar 2025 | https://www.soumu.go.jp/main_content/001003032.pdf |
| 486 | Canada AI Strategy for Federal Public Service 2025-2027 | Canada | Published 2025 | https://www.canada.ca/en/government/system/digital-government/digital-government-innovations/responsible-use-ai/gc-ai-strategy-overview.html |
| 487 | Canada's National AI Strategy: AI for All | Canada | Published 2025 | https://ised-isde.canada.ca/site/ised/en/canadas-national-artificial-intelligence-strategy-ai-all |

### Tier 4 — Additional Evaluation/Assessment Methodologies (9 frameworks)

| # | Framework | Issuer | Status | Source |
|---|-----------|--------|--------|--------|
| 488 | OECD AI Capability Indicators | OECD | Beta Jun 2025 | https://www.oecd.org/ |
| 489 | Conceptual Framework for AI Capability Evaluations | Academic (OpenReview) | Published 2025 | https://openreview.net/pdf?id=I8gacZXsFW |
| 490 | CIRCLE Framework (Real-World AI Measurement) | Forum for Real-World AI Measurement | Published 2025 | https://arxiv.org/pdf/2602.24055v1 |
| 491 | EvalSense (Domain-Specific LLM Meta-Evaluation) | Academic | Published 2025 | https://arxiv.org/pdf/2602.18823 |
| 492 | EM Foundation Intelligence Assessment Framework v1.0 | EM Foundation | Proposed May 2026 | https://emfoundation.net/emf-iaf-v1.html |
| 493 | General Scales for AI Evaluation | Academic (Nature) | Published 2026 | https://link.springer.com/article/10.1038/s41586-026-10303-2 |
| 494 | CAIE (Cognitive and AI Evaluation) Framework | Academic (AI Review) | Published 2026 | https://link.springer.com/article/10.1007/s10462-026-11493-x |
| 495 | TEACH-AI (Evaluating AI Assistants in Education) | Academic | Published 2025 | https://arxiv.org/abs/2512.04107v1 |
| 496 | PEARL (Rubric-Driven Multi-Metric LLM Evaluation) | Academic | Published 2025 | https://www.mdpi.com/2078-2489/16/11/926 |

### Tier 4 — Additional Enterprise/Organizational Frameworks (2 frameworks)

| # | Framework | Issuer | Status | Source |
|---|-----------|--------|--------|--------|
| 497 | Unified Control Framework (UCF) for Enterprise AI Governance | Academic | Published 2025 | https://arxiv.org/html/2503.05937 |
| 498 | BEATS (Data and AI Governance Framework for LLMs) | Academic | Published 2025 | https://www.arxiv.org/pdf/2508.03970 |

---

## Summary Statistics

| Category | Count |
|----------|-------|
| **Previously covered** | 12 |
| **Pass 1 newly discovered** | 254 |
| **Pass 2 newly discovered** | 232 |
| **Grand total** | **498** |

### Breakdown by tier (Pass 1 + Pass 2):
| Tier | Description | Count |
|------|-------------|-------|
| Tier 1 | Quick wins (code exists) | 2 |
| Tier 1 | Enacted/pending national AI laws | 46 |
| Tier 1 | US state AI laws (Pass 1) | 14 |
| Tier 1 | US state AI laws (Pass 2) | 52 |
| Tier 1 | City/local ordinances | 9 |
| Tier 1 | Sub-national/regional (Pass 2) | 19 |
| Tier 2 | ISO/IEC standards (Pass 1) | 18 |
| Tier 2 | ISO/IEC standards (Pass 2) | 9 |
| Tier 2 | IEEE standards (Pass 1) | 28 |
| Tier 2 | IEEE standards (Pass 2) | 6 |
| Tier 2 | ETSI standards (Pass 2) | 4 |
| Tier 2 | National standards body (Pass 2) | 11 |
| Tier 2 | National AI strategies (Pass 1) | 23 |
| Tier 2 | National AI strategies (Pass 2) | 7 |
| Tier 2 | Regional frameworks | 4 |
| Tier 3 | International treaties & voluntary | 7 |
| Tier 3 | AI security frameworks (Pass 1) | 9 |
| Tier 3 | AI security frameworks (Pass 2) | 6 |
| Tier 3 | Privacy frameworks (Pass 1) | 9 |
| Tier 3 | Privacy frameworks (Pass 2) | 3 |
| Tier 3 | Sector-specific regulations (Pass 1) | 17 |
| Tier 3 | Sector-specific regulations (Pass 2) | 22 |
| Tier 3 | Risk taxonomies/incident reporting | 6 |
| Tier 3 | Risk frameworks (Pass 2) | 2 |
| Tier 3 | Red teaming/testing | 3 |
| Tier 3 | Auditing/assessment (Pass 2) | 5 |
| Tier 3 | Procurement (Pass 2) | 5 |
| Tier 3 | Safety/testing (Pass 2) | 5 |
| Tier 3 | Technology-specific (Pass 2) | 8 |
| Tier 3 | Ethics frameworks (Pass 2) | 3 |
| Tier 3 | Multilateral organizations (Pass 2) | 14 |
| Tier 3 | Model documentation | 5 |
| Tier 3 | Bias/fairness/explainability | 4 |
| Tier 3 | Content authenticity | 2 |
| Tier 3 | Children's safety/DSA/liability | 5 |
| Tier 3 | Defense/military | 4 |
| Tier 3 | Environmental/accessibility/election/labor | 10 |
| Tier 4 | Corporate/frontier safety (Pass 1) | 11 |
| Tier 4 | Corporate (Pass 2) | 11 |
| Tier 4 | Assurance/certification (Pass 1) | 4 |
| Tier 4 | Assurance/certification (Pass 2) | 7 |
| Tier 4 | Professional/multi-stakeholder/ITU/EU (Pass 1) | 10 |
| Tier 4 | Industry consortium (Pass 2) | 4 |
| Tier 4 | Open-source governance (Pass 2) | 5 |
| Tier 4 | Professional/multi-stakeholder (Pass 2) | 6 |
| Tier 4 | Government technical standards (Pass 2) | 4 |
| Tier 4 | National frameworks (Pass 2) | 3 |
| Tier 4 | Evaluation methodologies (Pass 2) | 9 |
| Tier 4 | Enterprise/organizational (Pass 2) | 2 |
| Tier 4 | China technical standards | 4 |

### Breakdown by type:
| Type | Count |
|------|-------|
| Binding regulation (enacted) | ~120 |
| Binding regulation (pending/proposed) | ~50 |
| Certifiable standard | ~25 |
| Voluntary framework / guidance | ~80 |
| Technical standard (ISO/IEEE/ETSI/ITU/national) | ~75 |
| National strategy / policy | ~35 |
| Corporate / industry code | ~25 |
| Risk catalog / taxonomy / evaluation | ~20 |
| Assurance / certification | ~15 |
| Open-source governance | ~5 |
| Multilateral / treaty | ~20 |
| Other (auditing, procurement, safety, ethics) | ~28 |

---

## Recommended Backlog Prioritization

### Phase 1 — Quick Wins (code already exists, matrix only)
1. **STRIDE** — `stride_mapper.py` already shipped
2. **OWASP Agentic Top 10 (ASI01-ASI10)** — `generate_owasp_report()` already maps ASI01-ASI10

### Phase 2 — High-Impact Enacted Regulations (effective 2024-2026)
3. **South Korea AI Basic Act** — Asia's first comprehensive AI law, extraterritorial
4. **Texas TRAIGA** — third US state AI law, NIST RMF safe harbor
5. **Utah AI Policy Act** — first US state AI law
6. **California SB 942 / AB 2013 / SB 53** — three CA AI laws
7. **China Generative AI Measures** — largest AI market by users
8. **CCPA/CPRA** — most impactful US privacy law
9. **Japan AI Act** — Asia's second comprehensive law
10. **Italy Law 132/2025** — EU member state cross-sector AI law

### Phase 3 — Foundational Voluntary Frameworks
11. **OECD AI Principles** — 47 adherents, foundational
12. **NIST AI 600-1 (GenAI Profile)** — directly relevant to HUMMBL
13. **Council of Europe Framework Convention** — first binding AI treaty
14. **UNESCO Recommendation on Ethics of AI** — 194 member states
15. **MITRE ATLAS** — AI threat catalog, complements STRIDE

### Phase 4 — ISO Family Completion
16. **ISO/IEC 23894:2023** (AI risk management)
17. **ISO/IEC 38507:2022** (AI governance)
18. **ISO/IEC 42005:2025** (AI impact assessment)
19. **ISO/IEC TR 24028:2020** (AI trustworthiness)
20. **ISO/IEC 42006:2025** (AIMS audit)

### Phase 5 — Privacy Frameworks
21. **LGPD** (Brazil)
22. **PIPEDA** (Canada)
23. **PDPA** (Singapore)
24. **DPDP Act** (India)
25. **Law 25** (Quebec)

### Phase 6 — Sector-Specific
26. **FDA AI/ML SaMD** (healthcare)
27. **EEOC AI Guidance** (employment)
28. **CFPB AI Guidance** (finance)
29. **SEC AI Guidance** (finance)
30. **DoD Responsible AI** (defense)

### Phase 7+ — Long Tail
Remaining ~462 frameworks as customer demand and jurisdictional relevance dictate.

---

## Research Methodology

### Pass 1 (266 frameworks)

Three parallel subagents were dispatched:

1. **Regulations by country** — Searched for AI regulations in every country, US state, and city. Covered sector-specific AI regulations and AI provisions in existing laws.
2. **Standards and voluntary frameworks** — Searched ISO, IEEE, ITU, ETSI, national AI strategies, corporate AI principles, frontier AI safety frameworks, AI assurance/certification schemes, multi-stakeholder initiatives, and regional AI frameworks.
3. **Security/privacy/specialized frameworks** — Searched AI-specific security frameworks, privacy frameworks by country, sector-specific security frameworks, AI risk taxonomies, incident reporting, red teaming, model documentation, bias/fairness, explainability, supply chain, content authenticity, children's safety, DSA, liability, defense, procurement, environmental/ESG, accessibility, election integrity, and labor frameworks.

Results were consolidated and deduplicated against the 12 already-covered frameworks. Each framework includes official name, jurisdiction/issuer, status, key focus areas, and source URL where available.

### Pass 2 (232 additional frameworks)

Three parallel subagents were dispatched to expand coverage:

1. **Binding regulations (uncovered jurisdictions)** — Searched for AI laws in US states not covered in Pass 1 (Nevada, Wisconsin, Michigan, Georgia, Tennessee, Alabama, Montana, Wyoming, Idaho, Hawaii, New Jersey, Pennsylvania, Ohio, Louisiana, Alaska) and sub-national/regional jurisdictions (Catalonia, Scotland, Quebec, Ontario, Flanders, Lombardy, Baden-Württemberg, Brittany, Alberta, Bavaria).
2. **Standards and technical frameworks** — Searched for new ISO/IEC standards (2025-2026), IEEE standards, ETSI standards, national standards body AI standards (DIN, AFNOR, SAC, UNI), new corporate AI governance frameworks, assurance/certification schemes, industry consortium frameworks, open-source governance frameworks, and professional/multi-stakeholder frameworks.
3. **Security/privacy/sector/specialized** — Searched for AI security frameworks (NIST, ENISA, UK/US guidelines), privacy frameworks, sector-specific regulations (education, energy, transportation, agriculture, media, legal, insurance, real estate, telecommunications), risk frameworks, auditing/assessment frameworks, procurement frameworks, safety/testing frameworks, technology-specific frameworks (LLM, agentic, generative AI), ethics frameworks, multilateral organization frameworks (World Bank, IMF, WHO, ILO, WTO, WIPO), and evaluation/assessment methodologies.

Results were consolidated and deduplicated against the existing 266 frameworks. Cross-subagent duplicates were also resolved. Each framework includes official name, jurisdiction/issuer, status, key focus areas, and source URL where available.

---

## Maintenance

- This inventory is a living document. Update as new frameworks are enacted, published, or identified.
- When a coverage matrix is created for a framework, move it from "Newly Discovered" to "Currently Covered" and update the count.
- Annual review minimum; on-publication review for binding-law updates.
- Cross-reference with `docs/coverage/README.md` index when matrices are added.

---

## Terminal Values and Proxy Validation

**Added 2026-08-10** in response to independent review (arcana-peer-review fleet) identifying the proxy-terminal validation gap.

### The Problem

This inventory tracks "frameworks covered" and "evidence validation" as proxies for actual compliance outcomes. Without explicit terminal values, the system optimizes for adding frameworks and filling evidence cells — not for demonstrating actual compliance to a knowledgeable buyer or auditor.

### Terminal Values

| ID | Terminal Value | How to observe directly |
|----|---------------|------------------------|
| TV1 | A knowledgeable buyer reading a coverage matrix row-by-row alongside the source standard finds every control accounted for | Buyer due-diligence review, auditor feedback |
| TV2 | HUMMBL can produce evidence for any "Fulfilled" row on demand | Evidence artifact resolves when the evidence command is run |
| TV3 | Boundary rows preempt the "but you don't implement X" objection | Buyer does not raise objections that boundary rows already address |

### Proxy-Terminal Linkage

| Proxy | Terminal Value | Linkage | What would invalidate the proxy |
|-------|---------------|---------|--------------------------------|
| Number of frameworks with coverage matrix files | TV1 | More frameworks → more complete landscape. But completeness of the *list* is not completeness of *coverage*. | A framework has a matrix file but the matrix is incomplete (missing controls). Count goes up, TV1 doesn't improve. |
| "100% evidence validation" (former claim) | TV2 | All evidence cells filled → evidence exists. But "filled" ≠ "validated." | Evidence cells contain content that doesn't resolve (broken paths, stale commands). "100%" is claimed but TV2 fails. |
| Validated evidence row count (ADR-007 ratchet) | TV2 | Validated rows → evidence resolves. This is a stronger proxy than "cells filled." | A row validates in CI but fails in a real audit context (different environment, missing dependencies). |
| Number of boundary rows | TV3 | More boundary rows → more objections preempted. | Boundary rows are generic ("organizational responsibility") without naming what specifically is the customer's obligation. Count goes up, TV3 doesn't improve. |

### Proxy Validation Protocol

1. **Quarterly:** Sample 5 "Fulfilled" rows per framework. Run the evidence command. If it doesn't resolve, the proxy is invalid — the row is not actually fulfilled.
2. **On buyer engagement:** Walk through the matrix with the buyer. If they raise objections that boundary rows don't address, TV3 is not met — add boundary rows for those objections.
3. **On framework addition:** Verify the matrix is complete (every control has a row) before counting it as "covered." A partial matrix inflates the framework count without improving TV1.

### Deprecation Criteria

- "Number of frameworks covered" is deprecated as a public claim when a framework is counted but its matrix is incomplete (ADR-001 Completeness invariant violated).
- "100% evidence validation" is deprecated as a claim (replaced by ADR-007 ratchet: validated row count / total Fulfilled rows).
- Validated evidence row count is deprecated for a specific row when the evidence command fails in 3 consecutive quarterly checks.

### Relationship to ADR-001 and ADR-007

ADR-001 already rejects self-grades (A+, 92%) as public claims and replaces them with coverage matrices. ADR-007 adds a ratchet gate to prevent regression of validated evidence. This section extends those ADRs by making the terminal values explicit and establishing a validation protocol for the proxies that remain in internal use.
