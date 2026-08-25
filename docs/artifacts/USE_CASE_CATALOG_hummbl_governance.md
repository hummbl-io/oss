# Use Case Catalog: hummbl-governance Product Directions

**Status:** live v1.0 (private — pre-decision)
**Author:** Operator, HUMMBL Research Institute
**Date:** 2026-08-24
**Tracking:** docs/artifacts/ARTIFACT_MANIFEST.md
**Reader:** Operator (use-case selection, stress-test prioritization)
**Decision:** which use cases to stress-test first against the actual primitives, competitive landscape, and positioning

**TL;DR:** Fifteen candidate use cases for hummbl-governance and the HUMMBL ecosystem, organized by who pays, what the wedge is, and how fast to revenue. No selections made yet — this catalog exists so we can pick 2-3 to stress-test before committing build cycles. Each entry includes the customer, the wedge, the primitives used, the competitive landscape, and an honest read on timing and risk.

**Context:** Prior use case (peptide-check) is Dan Matha's product; Operator has no ownership and is not contributing. This catalog scopes directions Operator owns — built on hummbl-governance (34 primitives, 7 MCP servers, zero deps, PyPI v1.4.1) and the broader HUMMBL ecosystem (arbiter, apex-nexus, hummbl-bus, wargame skill, cyber workbench).

---

## How to read this catalog

Each use case has:

- **Customer**: who pays and why
- **Wedge**: the entry point — what gets bought first
- **Primitives used**: which of the 34 governance primitives + ecosystem assets are load-bearing
- **Competitive landscape**: who else is there and what they lack
- **Timing**: is the market ready now, soon, or speculative
- **Risk**: what kills this direction
- **Revenue model**: how money changes hands
- **Build effort**: low / medium / high relative to the other use cases

Clusters are ordered by near-term revenue potential, not by preference. Selection happens after stress-testing.

---

## Cluster 1: Enterprise AI coding-agent governance (near-term revenue)

### UC-1: Governance layer for AI coding tools at enterprises

**Customer:** Engineering leaders at mid-market and enterprise companies deploying Cursor, Copilot, Claude Code, Windsurf, or custom AI coding agents across their engineering org. The buyer is the VP Eng / CTO who is being asked "are we governing our AI coding tools?" by security, legal, or the board.

**Wedge:** A drop-in governance package that wraps existing AI coding tools — kill switch for runaway agents, cost governor for API spend across all tools, audit log for "which AI touched which file and was it approved." Pair with `arbiter` (already built, PyPI-published) for code quality attribution. The pitch: "you've deployed 5 AI coding tools; we govern them."

**Primitives used:** `kill_switch`, `cost_governor`, `audit_log`, `identity` (agent registry), `capability_fence` (scope per tool), `eal` (execution assurance via arbiter scores). Ecosystem: `arbiter` for code quality attribution.

**Competitive landscape:**

- _Cursor/Copilot native controls_: vendor-specific, not cross-tool, no audit trail across tools
- _Langfuse/Helicone_: observability, not governance — they show what happened, not whether it was allowed
- _Snyk/Veracode_: security scanning, not runtime agent governance
- _No one_ offers cross-tool AI coding governance with kill switch + cost cap + audit log + quality attribution

**Timing:** Now. Enterprises are deploying AI coding tools faster than they can govern them. Budget is allocated. The question being asked in board rooms is "what's our AI coding governance posture."

**Risk:** Enterprises may expect platform-grade UX (dashboards, SSO, RBAC) before buying. The library is governance-first, not UI-first — may need a thin dashboard layer to cross the procurement line. Vendor-specific APIs (Cursor, Copilot) may resist wrapping.

**Revenue model:** Per-seat SaaS or per-team license. $20-50/seat/month for governed AI coding. Enterprise tier with SSO, audit export, custom policies.

**Build effort:** Medium. Primitives exist. Work is integration adapters for each coding tool + a thin dashboard. Arbiter is already built.

---

### UC-2: AI agent cost-management SaaS (governance-first Helicone/Langfuse competitor)

**Customer:** AI-native startups and mid-market companies whose AI API spend is growing faster than their ability to control it. The buyer is the eng lead or founder watching the AWS/AI cloud bill.

**Wedge:** Lightweight SaaS that monitors AI API spend across teams with kill-switch capabilities. Not "what did it cost" (Helicone does that) but "was it allowed to spend that, and we can stop it in real-time." Governance-first cost management.

**Primitives used:** `cost_governor` (soft/hard caps, ALLOW/WARN/DENY), `kill_switch` (emergency halt), `audit_log` (spend trail), `circuit_breaker` (isolate runaway agents).

**Competitive landscape:**

- _Helicone_: observability-first, logging and analytics, no real-time kill switch
- _Langfuse_: tracing and eval, no governance
- _Cloud provider cost alerts_: reactive, post-spend, no agent-level control
- _No one_ offers real-time agent-level cost governance with kill switch

**Timing:** Now. AI spend is a board-level concern. Companies are getting surprise bills from agent loops.

**Risk:** Observability tools (Helicone, Langfuse) could add governance features. Cost management is a feature, not a product — may be hard to charge standalone. Need to differentiate on the kill-switch + policy layer, not the dashboard.

**Revenue model:** Percentage of spend governed (0.5-2%) or per-team SaaS ($100-500/month). The percentage model aligns incentives — we save you money by stopping runaway spend.

**Build effort:** Low-medium. `cost_governor` is standalone and proven. Work is the SaaS wrapper, multi-tenant state, and integrations with OpenAI/Anthropic/Bedrock APIs.

---

### UC-3: AI incident response platform (PagerDuty for AI agents)

**Customer:** Companies running AI agents in production (customer support, coding, research, operations) where an agent going rogue has real cost — financial, reputational, or safety. The buyer is the SRE/platform team responsible for AI uptime.

**Wedge:** When an agent goes rogue, kill switch fires, circuit breaker isolates the failing component, post-incident audit log shows exactly what happened. Frame it as "AI incident response" — a category no one has claimed. PagerDuty + Datadog handle infrastructure incidents; no one handles AI agent incidents.

**Primitives used:** `kill_switch`, `circuit_breaker`, `audit_log`, `health_probe`, `reward_monitor` (drift detection), `lifecycle` (PROVISIONED → ACTIVE → SUSPENDED → DECOMMISSIONED).

**Competitive landscape:**

- _PagerDuty/Datadog_: infrastructure incidents, not AI agent behavior
- _LangSmith/Langfuse_: tracing, not incident response
- _No one_ has framed AI agent incidents as a category with kill + isolate + audit

**Timing:** Emerging. Companies are starting to run agents in production and hitting incidents they can't diagnose or stop fast enough. Category creation play.

**Risk:** Category creation is expensive — you have to educate the market that "AI incident response" is a thing. May be too early for buyers to have budget line items. Could be a feature of a broader platform rather than a standalone product.

**Revenue model:** Per-incident or per-agent SaaS. $50-200/agent/month for monitored + governed production agents. Enterprise tier with on-call integration (PagerDuty, Opsgenie).

**Build effort:** Medium. Primitives exist. Work is the incident console, alerting, on-call integration, and the "what happened" timeline view from audit logs.

---

## Cluster 2: Regulatory tailwinds (medium-term, high-value)

### UC-4: EU AI Act compliance tooling for AI deployers

**Customer:** Companies deploying AI in the EU or serving EU customers who must comply with the EU AI Act (risk assessments, audit logs, human oversight, transparency obligations). The buyer is the compliance/legal team under regulatory deadline pressure.

**Wedge:** "Upload your AI deployment, get your EU AI Act compliance gap report." The compliance mapper already maps to EU AI Act articles 9, 10, 12-14, 17. Productize it: a tool that ingests an AI deployment description and produces a gap report + remediation roadmap.

**Primitives used:** `compliance_mapper` (EU AI Act, NIST AI RMF, SOC2, GDPR), `audit_log` (evidence), `stride_mapper` (risk assessment), `lifecycle` (oversight orchestration).

**Competitive landscape:**

- _Big 4 consulting_: manual assessments, expensive, slow
- _OneTrust/TrustArc_: privacy/GDPR platforms adding AI modules, not AI-native
- _Credo AI / Holistic AI_: AI governance platforms, well-funded, but platform-heavy and enterprise-priced
- HUMMBL differentiator: deterministic library, in-process, no platform lock-in, open-source credibility

**Timing:** Now-urgent. EU AI Act deadlines are driving mandatory adoption. Companies that deploy AI in the EU must comply or face fines.

**Risk:** Well-funded competitors (Credo AI raised $40M+, Holistic AI). Enterprise sales cycle is long. May need compliance certifications or partnerships to be taken seriously by legal buyers.

**Revenue model:** Assessment-as-a-service ($5-25K per assessment) + ongoing compliance monitoring SaaS ($1-5K/month per deployment). Higher value per deal than SaaS-per-seat.

**Build effort:** Medium. Compliance mapper exists. Work is the ingestion flow, gap report generation, and the legal-defensible output format.

---

### UC-5: Defense / DoD AI governance (SBIR/STTR + contracts)

**Customer:** DoD components, defense primes (Lockheed, Booz Allen, SAIC, Peraton), and defense-tech startups deploying AI in government contexts. The buyer is the program manager or contracting officer's technical representative (COTR).

**Wedge:** DoD is mandating NIST AI RMF compliance for AI deployments. hummbl-governance maps to NIST AI RMF. Position for SBIR/STTR grants and defense AI governance contracts. Less competition than commercial, higher bar, but Operator has the credentials (DoD 8140 mapping, clearance strategy, T0-T4 cyber tiers in hummbl-cyber).

**Primitives used:** Full primitive suite — `compliance_mapper` (NIST AI RMF), `kill_switch` (human oversight), `audit_log` (evidence), `identity` (clearance-tiered access), `capability_fence` (scope per clearance level), `physical_governor` (kinematic safety for defense robotics).

**Competitive landscape:**

- _Defense primes_ building internal AI governance: slow, not productized
- _Credo AI_ has some federal positioning
- _No open-source, deterministic, NIST-AI-RMF-native library_ is positioned for defense
- Operator's clearance pursuit strategy and DoD 8140 mapping are unique credentials

**Timing:** Now. DoD AI directives (CDAO, Responsible AI) are driving adoption. SBIR/STTR cycles run quarterly.

**Risk:** Long sales cycles (12-24 months). Clearance requirements may gate access. SBIR/STTR is grant money, not product revenue — need to convert grants to contracts. Political risk.

**Revenue model:** SBIR/STTR grants ($50-300K Phase I, $1-1.7M Phase II) → defense contracts ($500K-5M annual). Not venture-scale but high-margin and defensible.

**Build effort:** Low-medium for the library (primitives exist). High for the contracting/clearance path. The product is ready; the go-to-market is the hard part.

---

### UC-6: AI governance audit-as-a-service (fractional AI Risk Officer)

**Customer:** Startups and mid-market companies that need AI governance posture but can't afford a full-time AI Risk Officer. The buyer is the founder/CEO or VP Eng who needs to show investors, customers, or regulators that they're governing AI.

**Wedge:** Productized consulting: use compliance mapper + audit log to run "AI governance readiness assessments." Map their AI deployments to NIST AI RMF / SOC2 / ISO 42001. Deliverable is the gap report + remediation roadmap. Operator becomes fractional AI Risk Officer for 5-10 startups.

**Primitives used:** `compliance_mapper`, `audit_log`, `stride_mapper`, `lifecycle`. Ecosystem: the `governance-scorecard`, `governance-maturity`, `gap-analysis`, `ai-risk-assessment` skills already exist.

**Competitive landscape:**

- _Big 4 consulting_: $50-200K engagements, slow, not AI-native
- _Boutique AI governance consultancies_: emerging, few have tooling
- HUMMBL differentiator: tooling-backed assessments — not just advice, but the library that implements the recommendations

**Timing:** Now. Startups raising rounds are being asked by investors "what's your AI governance posture." SOC2 auditors are starting to ask about AI.

**Risk:** Consulting doesn't scale beyond Operator's hours. Need to productize into self-serve or template-driven assessments to grow. May compete with the audit firms who have the client relationships.

**Revenue model:** $10-30K per assessment + $2-5K/month retainer for ongoing governance monitoring. Fractional AIRO retainer: $5-15K/month per client.

**Build effort:** Low. Skills and primitives exist. Work is packaging, marketing, and the client-facing deliverable template.

---

## Cluster 3: Platform / timing plays (bet on where the market goes)

### UC-7: MCP server governance (the big timing bet)

**Customer:** Companies building or consuming MCP (Model Context Protocol) servers — AI tool vendors, platform teams, and enterprises connecting AI agents to tools, databases, and APIs. The buyer is the platform/security team worried about what their MCP-connected agents can do.

**Wedge:** MCP is exploding — every AI tool is shipping MCP servers (Anthropic, Cursor, Replit, Zed, etc.). Every MCP server is an attack surface: tool injection, scope escape, data exfiltration, prompt injection through tool outputs. hummbl-governance as the governance layer for MCP ecosystems: capability fences on tools, output validation, audit logs of every tool call. The wargame skill already tests 7 attack categories including LLM jailbreak, injection, scope escape, and data exfiltration. **No one owns MCP governance yet.**

**Primitives used:** `capability_fence` (scope per MCP tool), `output_validator` (validate tool outputs for injection/exfil), `audit_log` (every tool call), `kill_switch` (halt rogue tool), `schema_validator` (validate tool I/O), `identity` (tool registry). Ecosystem: wargame skill (attack surface mapped), `stride_mapper` (threat model per tool).

**Competitive landscape:**

- _No one._ MCP is 6 months old as a widely-adopted standard. Governance is an unrecognized gap.
- _MCP server authors_ ship servers with no governance layer
- _Inlet/Letta_ are agent frameworks, not MCP governance
- First-mover advantage is large if MCP becomes the standard (it is trending that way)

**Timing:** Now-early. MCP adoption is accelerating. The governance gap will surface as the first MCP-based security incidents hit. Being positioned before the incidents is the play.

**Risk:** MCP could fragment or be replaced. Anthropic controls the spec and could ship governance natively (unlikely — they're focused on the protocol, not governance). Market may not recognize the need until an incident forces it.

**Revenue model:** Open-source library (free) + hosted governance proxy SaaS ($100-1K/month per org) + enterprise self-hosted license. The proxy intercepts MCP tool calls, applies governance, logs.

**Build effort:** Medium. Primitives exist. Work is the MCP proxy integration, the tool-registration flow, and the policy DSL for MCP-specific scopes.

---

### UC-8: AI agent marketplace governance

**Customer:** Platforms building agent marketplaces (app stores for AI agents) — could be hyperscalers, AI platforms, or vertical SaaS companies. The buyer is the platform team that needs to review, approve, and govern third-party agents.

**Wedge:** If agent marketplaces emerge, they need governance: what agents can do, safety review, audit trails, revocation. hummbl-governance as the governance SDK for agent marketplaces. Marketplace operators embed it to enforce per-agent capability fences, audit every agent action, and revoke rogue agents.

**Primitives used:** `capability_fence`, `identity` (agent registry), `audit_log`, `kill_switch`, `delegation` (scoped agent authority), `lifecycle` (agent provisioning/decommissioning).

**Competitive landscape:**

- _No agent marketplace has a governance SDK._ The marketplaces themselves are nascent.
- _App store review processes_ (Apple, etc.) are manual; AI agents need automated runtime governance
- Speculative — depends on agent marketplaces emerging

**Timing:** Speculative. Agent marketplaces are emerging (Anthropic's agent offerings, OpenAI's GPT store) but not yet a mature category. Early-mover if they consolidate.

**Risk:** Agent marketplaces may not emerge as a category, or hyperscalers may build governance natively. Very speculative — bet only if you believe agent marketplaces are the future distribution model.

**Revenue model:** Marketplace licensing (per-agent or per-marketplace) + revenue share on governed agents. Speculative pricing.

**Build effort:** Low for the library. High for the market development — you have to convince marketplace operators to adopt, and the marketplaces don't fully exist yet.

---

### UC-9: Federated / multi-org AI governance

**Customer:** Companies collaborating on AI projects across organizational boundaries — joint ventures, client-vendor AI deployments, multi-tenant AI platforms. The buyer is the platform team that needs to retain governance authority when an agent crosses org boundaries.

**Wedge:** Delegation tokens + identity registry enable governance across organizational boundaries. Use case: two companies sharing an AI agent for a joint project, each retaining governance authority over their side. The agent operates with scoped, revocable delegation from each party.

**Primitives used:** `delegation` (HMAC-signed scoped tokens), `identity` (cross-org agent registry), `audit_log` (cross-org evidence), `capability_fence` (per-org scope).

**Competitive landscape:**

- _No one_ offers federated AI agent governance
- _OAuth/OIDC_ handle auth, not governance of agent behavior
- Niche but defensible if multi-org AI collaboration grows

**Timing:** Speculative. Multi-org AI collaboration is emerging but not yet a recognized category.

**Risk:** Very niche. May be a feature of a broader platform rather than a standalone product. Depends on multi-org AI becoming common.

**Revenue model:** Platform license for federated governance nodes. Speculative pricing.

**Build effort:** Medium. Primitives exist. Work is the federation protocol and cross-org trust model.

---

## Cluster 4: Vertical-specific (deep but narrow)

### UC-10: Healthcare AI governance (HIPAA + AI)

**Customer:** Healthcare organizations deploying AI for clinical decision support, patient communication, or operational automation. The buyer is the compliance/CISO team under HIPAA + emerging AI regulations.

**Wedge:** Clinical AI needs audit trails, PHI scope control, human oversight. `capability_fence` + `audit_log` + HIPAA mapping. The `hipaa-map` skill already exists. Build a healthcare AI governance package: PHI-scoped agent capabilities, audit trails for every AI interaction with patient data, human-oversight enforcement.

**Primitives used:** `capability_fence` (PHI scope), `audit_log` (HIPAA audit trail), `compliance_mapper` (HIPAA Security Rule), `kill_switch` (halt unsafe AI), `lifecycle` (human oversight), `physical_governor` (if clinical robotics).

**Competitive landscape:**

- _Healthcare AI platforms_ (Hippocratic AI, etc.): model-first, not governance-first
- _Compliance platforms_ (Vanta, Drata): SOC2/HIPAA compliance, not AI-specific
- HUMMBL differentiator: AI-native governance with HIPAA mapping

**Timing:** Medium. Healthcare AI is regulated and growing. Sales cycles are long (12-18 months) but value per deal is high.

**Risk:** Long sales cycles. HIPAA compliance requires BAA agreements. Healthcare is risk-averse and slow to adopt new vendors. May need healthcare-specific certifications.

**Revenue model:** Per-deployment license ($10-50K/year) + implementation services. Enterprise healthcare: $100K+ contracts.

**Build effort:** Medium. Primitives + HIPAA mapping exist. Work is the healthcare-specific packaging, BAA, and the clinical workflow integrations.

---

### UC-11: Legal AI governance

**Customer:** Law firms and legal departments using AI for document review, contract analysis, legal research. The buyer is the managing partner or GC worried about confidentiality, privilege, and scope.

**Wedge:** Law firms using AI for document review need confidentiality scope control, audit trails for privilege, scope enforcement per matter. `capability_fence` + `audit_log` + `delegation` for matter-level agent scoping. An AI reviewing M&A docs shouldn't see unrelated litigation docs.

**Primitives used:** `capability_fence` (matter-level scope), `audit_log` (privilege trail), `delegation` (scoped authority per matter), `identity` (agent registry), `output_validator` (prevent privilege leakage).

**Competitive landscape:**

- _Legal AI platforms_ (Harvey, CoCounsel): model-first, governance is secondary
- _Document management systems_ (iManage, NetDocs): storage, not AI governance
- HUMMBL differentiator: governance-first, matter-scoped AI authority

**Timing:** Medium. Legal AI adoption is accelerating. Privilege and confidentiality concerns are top-of-mind.

**Risk:** Legal market is conservative. Bar association guidance on AI is still evolving. May need legal-domain expertise to sell credibly.

**Revenue model:** Per-firm license ($20-100K/year) + per-matter governance. Boutique firms: $5-20K/year.

**Build effort:** Medium. Primitives exist. Work is the matter-scoping abstraction and legal workflow integrations (iManage, Relativity).

---

### UC-12: Physical AI / robotics governance

**Customer:** Robotics companies deploying AI in shared human spaces — manufacturing cobots, service robots, autonomous vehicles (non-road), healthcare robotics. The buyer is the safety engineering team.

**Wedge:** The `physical_governor` (kinematic constraints, pHRI safety modes — NORMAL/CAUTION/EMERGENCY) is genuinely unique. Most AI governance is software-only. Robotics companies deploying AI in shared human spaces need safety governance. Small market but zero competition and high safety stakes.

**Primitives used:** `physical_governor` (kinematic constraints, pHRI safety), `kill_switch` (emergency halt), `audit_log` (safety event trail), `health_probe` (robot health), `capability_fence` (operational scope).

**Competitive landscape:**

- _No one_ offers AI governance for robotics. Safety standards (ISO 10218, ISO/TS 15066) govern the robot, not the AI.
- _Robotics frameworks_ (ROS) have safety modules but not AI-governance-aware ones
- Zero competition. Genuinely novel.

**Timing:** Emerging. AI in robotics is growing but governance is not yet a recognized category. Early-mover.

**Risk:** Very small market today. Robotics companies may not see AI governance as distinct from robot safety. Long path to revenue. Could be a research/positioning play rather than a product.

**Revenue model:** Licensing to robotics OEMs ($50-200K/year) + safety certification partnerships. Speculative.

**Build effort:** Low for the library (`physical_governor` exists). High for the robotics integrations and safety-standard alignment.

---

## Cluster 5: Open-source / credibility plays (not direct revenue)

### UC-13: AI safety benchmark suite (SWE-bench for governance)

**Customer:** AI safety researchers, academic labs, and AI companies evaluating agent safety. The buyer is the research lab (not a commercial buyer — this is a credibility play).

**Wedge:** The wargame skill + governance primitives as a benchmark suite for AI safety. Academic credibility, conference papers, citable artifact. Builds the brand that drives enterprise sales. Like SWE-bench became the coding benchmark, this becomes the governance/safety benchmark.

**Primitives used:** Wargame skill (7 attack categories, multi-round red/blue/purple), `stride_mapper`, `reward_monitor` (drift detection), full primitive suite as the defense.

**Competitive landscape:**

- _AI safety benchmarks_ exist for specific harms (toxicity, bias) but not for agent governance posture
- _AgentBench_, _GAIA_: capability benchmarks, not safety/governance
- First-mover on governance benchmarks

**Timing:** Now. AI safety research is hungry for benchmarks. Conference deadlines (NeurIPS, ICML, FAccT) drive adoption.

**Risk:** Doesn't generate revenue directly. Academic adoption is slow. May not translate to commercial credibility with enterprise buyers.

**Revenue model:** No direct revenue. Credibility, citations, conference talks → drives enterprise sales (UC-1, UC-4, UC-5).

**Build effort:** Low-medium. Wargame skill exists. Work is packaging as a benchmark, writing the paper, submitting to conferences.

---

### UC-14: AI agent insurance underwriting evidence

**Customer:** Companies that need to prove to insurers they're governing AI agents (to get AI liability insurance or reduce premiums). The buyer is the risk management team. Insurers need evidence to underwrite AI agent risk.

**Wedge:** hummbl-governance audit logs + compliance reports = the evidence artifacts insurers require. You don't sell to insurers; you sell to companies who need to prove to insurers they're governed. Niche two-sided play.

**Primitives used:** `audit_log` (evidence), `compliance_mapper` (compliance evidence), `eal` (execution assurance receipts), `stride_mapper` (risk assessment).

**Competitive landscape:**

- _No standard_ for AI agent insurance evidence exists yet
- _Insurers_ (Munich Re, Marsh) are exploring AI liability but lack evidence standards
- Early-mover if AI insurance becomes a real category

**Timing:** Speculative. AI liability insurance is nascent. Depends on insurers requiring evidence.

**Risk:** AI insurance may not emerge as a category, or insurers may define their own evidence standards without third-party input. Two-sided market is hard to bootstrap.

**Revenue model:** Evidence generation SaaS ($1-5K/month per company) + insurer partnership revenue. Speculative.

**Build effort:** Low for the library. High for the insurer partnerships and evidence-standard definition.

---

### UC-15: Hosted kill-switch-as-a-service (freemium wedge)

**Customer:** Any developer or team running AI agents who wants a safety net. The buyer is the individual developer or small team — broad top-of-funnel.

**Wedge:** The simplest primitive, hosted. Any AI agent calls your kill-switch endpoint. Freemium, upsell to full governance. Low barrier, broad top-of-funnel. Could be the on-ramp for everything above.

**Primitives used:** `kill_switch` (hosted), `audit_log` (call trail), `identity` (agent registration).

**Competitive landscape:**

- _No hosted kill-switch service_ exists for AI agents
- _Cloud provider kill switches_ exist for infrastructure, not AI agents
- Simple, defensible if it becomes the default

**Timing:** Now. Developers want a safety net for AI agents. Low friction to try.

**Risk:** Kill switch alone may be too thin to charge for. May be a feature, not a product. Freemium conversion is hard. Could be copied easily.

**Revenue model:** Freemium (free up to N agents) → $10-50/month per team for hosted kill switch + audit → upsell to full governance platform.

**Build effort:** Low. `kill_switch` is standalone. Work is the hosted endpoint, auth, and dashboard.

---

## Selection criteria for stress-testing

When we pick 2-3 to stress-test, evaluate each against:

1. **Primitive readiness**: are the load-bearing primitives production-ready, or do they need work?
2. **Competitive moat**: can a well-funded competitor copy this in 6 months?
3. **Time to first revenue**: how long from today to a paid pilot?
4. **Buyer access**: does Operator have a path to the buyer (network, credentials, channel)?
5. **Market timing**: is the market ready now, or are we educating?
6. **Build vs. sell**: is the hard part building (engineering) or selling (go-to-market)?
7. **Optionality**: does this use case open doors to other use cases, or is it a dead end?
8. **Operator-fit**: does this play to Operator's strengths (governance, cyber, DoD, open-source) or require skills he lacks (enterprise sales, healthcare domain)?

## Preliminary read (non-binding)

Strongest combinations, pending stress-test:

- **Near-term revenue**: UC-1 (enterprise AI coding governance) + UC-2 (cost SaaS) — Operator has arbiter, the THD angle, and buyer budget is allocated now
- **Biggest differentiation**: UC-7 (MCP governance) — timing is now, no one owns it, wargame attack surface is mapped
- **Highest value per deal**: UC-5 (defense) + UC-4 (EU AI Act) — regulatory pressure drives mandatory adoption
- **Fastest to ship**: UC-15 (hosted kill switch) as a wedge into anything
- **Credibility flywheel**: UC-13 (benchmark) as a non-revenue layer that amplifies everything else

No selections made. Next step: pick 2-3 and stress-test against the actual primitives, the competitive landscape, and Operator's positioning.

---

## Appendix: Primitive inventory (load-bearing mapping)

Which primitives each use case leans on (for stress-test reference):

| Primitive           | UC-1 | UC-2 | UC-3 | UC-4 | UC-5 | UC-6 | UC-7 | UC-8 | UC-9 | UC-10 | UC-11 | UC-12 | UC-13 | UC-14 | UC-15 |
| ------------------- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ----- | ----- | ----- | ----- | ----- | ----- |
| `kill_switch`       | ●    | ●    | ●    |      | ●    |      | ●    | ●    |      | ●     |       | ●     |       |       | ●     |
| `circuit_breaker`   |      | ●    | ●    |      |      |      |      |      |      |       |       |       |       |       |       |
| `cost_governor`     | ●    | ●    |      |      |      |      |      |      |      |       |       |       |       |       |       |
| `audit_log`         | ●    | ●    | ●    | ●    | ●    | ●    | ●    | ●    | ●    | ●     | ●     | ●     |       | ●     | ●     |
| `compliance_mapper` |      |      |      | ●    | ●    | ●    |      |      |      | ●     |       |       |       | ●     |       |
| `identity`          | ●    |      |      |      | ●    |      | ●    | ●    | ●    |       | ●     |       |       |       | ●     |
| `capability_fence`  | ●    |      |      |      | ●    |      | ●    | ●    | ●    | ●     | ●     | ●     |       |       |       |
| `delegation`        |      |      |      |      |      |      |      | ●    | ●    |       | ●     |       |       |       |       |
| `output_validator`  |      |      |      |      |      |      | ●    |      |      |       | ●     |       |       |       |       |
| `physical_governor` |      |      |      |      | ●    |      |      |      |      | ●     |       | ●     |       |       |       |
| `health_probe`      |      |      | ●    |      |      |      |      |      |      |       |       | ●     |       |       |       |
| `reward_monitor`    |      |      | ●    |      |      |      |      |      |      |       |       |       | ●     |       |       |
| `lifecycle`         |      |      | ●    | ●    |      |      |      | ●    |      | ●     |       |       |       |       |       |
| `eal`               | ●    |      |      |      |      |      |      |      |      |       |       |       |       | ●     |       |
| `stride_mapper`     |      |      |      | ●    |      | ●    | ●    |      |      |       |       |       | ●     | ●     |       |
| `schema_validator`  |      |      |      |      |      |      | ●    |      |      |       |       |       |       |       |       |
| `contract_net`      |      |      |      |      |      |      |      |      |      |       |       |       |       |       |       |

(● = load-bearing; blank = available but not central. Full primitive list in `PRIMITIVES.md`.)

---

## Next actions

1. **Pick 2-3 use cases** to stress-test first (Operator's call)
2. **For each selected**, produce a stress-test doc covering:
   - Primitive readiness audit (are the ● primitives production-ready?)
   - Competitive deep-dive (who, what they lack, what they could build)
   - Buyer access map (how Operator reaches the buyer)
   - 90-day build plan (what to ship to validate)
   - Kill criteria (what would make us abandon this direction)
3. **Decide** based on stress-test results
