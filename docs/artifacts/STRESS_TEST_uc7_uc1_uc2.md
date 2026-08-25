# Stress-Test: UC-7, UC-1, UC-2 — Primitive Readiness, Competitive Reality, and Honest Reassessment

**Status:** live v1.0 (private — pre-decision)
**Author:** Operator, HUMMBL Research Institute
**Date:** 2026-08-24
**Tracking:** docs/artifacts/ARTIFACT_MANIFEST.md
**Reader:** Operator (go/no-go on the three preliminary picks)
**Decision:** whether to proceed with UC-7 (MCP governance), UC-1 (enterprise AI coding governance), UC-2 (cost SaaS), or pivot to use cases where HUMMBL's differentiation survives competitive pressure

**TL;DR:** The primitives are production-ready — kill switch, cost governor, and capability fence are well-built, well-tested, and have clean APIs. But the competitive landscape for all three preliminary picks is significantly harder than the use case catalog assumed. Microsoft's Agent Governance Toolkit (AGT) is a direct, well-funded competitor to UC-7 and UC-1. The cost SaaS market (UC-2) is already crowded with 5+ direct competitors offering kill switches and budget enforcement. This stress-test recommends pivoting the top-3 picks toward use cases where HUMMBL's zero-dependency, in-process, stdlib-only differentiation actually survives: defense/DoD (UC-5), fractional AIRO (UC-6), and physical AI/robotics (UC-12).

---

## Primitive readiness audit (all three use cases)

### Verdict: production-ready

The load-bearing primitives are not the bottleneck. All three are well-implemented, well-tested, and have clean public APIs.

| Primitive          | LOC | Test LOC | API readiness | Assessment                                                                                                                                                          |
| ------------------ | --- | -------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `kill_switch`      | 418 | 386      | Production    | 4 graduated modes, HMAC integrity, persistence, subscriber notifications, thread-safe (RLock). Clean `engage()` / `check_task_allowed()` API. Ready to ship.        |
| `cost_governor`    | 283 | 241      | Production    | SQLite-backed, soft/hard caps, ALLOW/WARN/DENY decisions, retention policy, alert callbacks. Clean `record_usage()` / `check_budget_status()` API. Ready to ship.   |
| `capability_fence` | 414 | 687      | Production    | Allow/deny lists, guard wrappers, audit logging, fnmatch patterns, extends delegation tokens. Clean `check()` API with `CapabilityDenied` exception. Ready to ship. |
| `output_validator` | 517 | 357      | Production    | PII detection, injection detection, blocklists. Ready but has known false-positive issues (see audit H2).                                                           |
| `audit_log`        | 445 | 449      | Production    | Append-only JSONL, rotation, retention, thread-safe. Ready to ship.                                                                                                 |
| `identity`         | 300 | 168      | Production    | Agent registry, aliases, trust tiers, canonicalization. Ready to ship.                                                                                              |
| `schema_validator` | 436 | 490      | Production    | Stdlib JSON Schema (Draft 2020-12 subset). Ready to ship.                                                                                                           |

**Conclusion:** The primitives are not what kills these use cases. The competitive landscape is.

---

## UC-7: MCP server governance — the big timing bet

### The finding that changes everything

**Microsoft's Agent Governance Toolkit (AGT)** is a direct, well-funded competitor that launched April 2026 and does exactly what UC-7 proposed.

| Attribute               | Microsoft AGT                                                                                                       | HUMMBL                                                 |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------ |
| GitHub stars            | 6,091                                                                                                               | ~not positioned for MCP yet                            |
| License                 | MIT                                                                                                                 | Apache 2.0                                             |
| Language SDKs           | Python, TypeScript, .NET, Rust, Go                                                                                  | Python only                                            |
| Framework adapters      | 20+ (LangChain, AutoGen, CrewAI, Semantic Kernel, OpenAI Agents SDK, Google ADK)                                    | None for MCP                                           |
| OWASP Agentic Top 10    | 10/10 covered                                                                                                       | Mapped (wargame skill tests 7 categories)              |
| MCP-specific governance | **MCP Security Gateway** — tool poisoning detection, drift monitoring, typosquatting, hidden instruction scanning   | Not built                                              |
| MCP proxy               | `@microsoft/agentmesh-mcp-proxy` — intercepts `tools/call`, sanitizes inputs, rate limits, evaluates policy, audits | Not built                                              |
| Policy languages        | YAML, OPA/Rego, Cedar                                                                                               | Not built (governance is code, not declarative policy) |
| Compliance mapping      | EU AI Act, HIPAA, SOC2, OWASP                                                                                       | NIST AI RMF, SOC2, GDPR, EU AI Act, OWASP              |
| Latency                 | <0.1ms p99 policy evaluation                                                                                        | Not measured for MCP use case                          |
| Backing                 | Microsoft (open-source blog launch, developer blog, docs site)                                                      | Solo founder                                           |

### What AGT has that HUMMBL doesn't

1. **The MCP proxy is built and shipped.** `@microsoft/agentmesh-mcp-proxy` sits between agent and MCP server, intercepts `tools/call`, applies policy, audits. HUMMBL would need to build this from scratch.
2. **20+ framework adapters.** AGT hooks into LangChain callbacks, CrewAI task decorators, Google ADK plugins, etc. HUMMBL has none.
3. **5 language SDKs.** MCP is multi-language. HUMMBL is Python-only.
4. **Microsoft's marketing reach.** Launch on Microsoft Open Source Blog + Microsoft Developer Blog + docs site. HUMMBL has no comparable channel.
5. **Policy-as-code (YAML/Rego/Cedar).** Enterprises want declarative policy, not Python code. HUMMBL's governance is code, not config.

### What HUMMBL has that AGT doesn't

1. **Zero third-party dependencies.** AGT is a toolkit with SDKs in 5 languages — it has dependencies. HUMMBL is stdlib-only Python. For air-gapped, security-sensitive, or supply-chain-paranoid environments, this matters.
2. **In-process, no proxy required.** AGT's MCP governance is proxy-based. HUMMBL can be embedded directly in the agent process. For edge/on-device/embedded governance, this wins.
3. **Already on PyPI.** `pip install hummbl-governance` works today. AGT's packaging is less clear (multiple packages across 5 languages).
4. **2,430 tests, deterministic.** HUMMBL has a proven test suite. AGT is newer (April 2026).

### Honest assessment

**UC-7 as originally framed (MCP governance platform) is not viable for a solo founder.** Microsoft has first-mover advantage, 6K stars, 5 SDKs, a shipped proxy, and Microsoft's marketing reach. Competing head-on would require building the proxy, 20+ adapters, 4 more language SDKs, and a policy DSL — then losing the GitHub star war to Microsoft.

**The only surviving niche:** zero-dependency, in-process MCP governance for Python-only, security-sensitive environments (defense, air-gapped, supply-chain-paranoid). This is a real niche but small. It's a feature, not a company.

### Kill criteria

- **Kill UC-7 as a standalone product.** Microsoft AGT has the category. The build effort to match them (proxy, 5 SDKs, 20 adapters, policy DSL) is beyond solo-founder scope.
- **Retain UC-7 as a feature** of a different use case (e.g., defense UC-5 where zero-dep + in-process is the differentiator and MCP governance is one capability, not the product).

---

## UC-1: Enterprise AI coding-agent governance — fastest to revenue?

### The finding that changes everything

The vendors themselves are absorbing this. Cross-tool AI coding governance is being closed by gateways, not by third-party libraries.

**What the market is doing:**

1. **Claude Code ships its own gateway** (Claude apps gateway, in the `claude` binary). Centralized credentials, usage tracking, cost controls, budget rules, audit logging — all in one place. Developers authenticate to the gateway; the gateway holds provider credentials. This is UC-1's wedge, built by Anthropic.

2. **Databricks Unity AI Gateway Budgets** — Databricks governs its own coding agent spend (Claude Code, Codex, Cursor) by routing all agent traffic through one gateway. Daily and monthly budgets, runaway spend protection, self-service budget increases. This is UC-1 + UC-2 combined, built by Databricks and shipped to customers.

3. **Cursor Enterprise** has admin console with SSO/SCIM, SOC 2 Type II, zero data retention. The vendor provides enterprise governance natively.

4. **Microsoft AGT** (see UC-7) covers AI coding governance too — framework-agnostic, 20+ adapters including the coding agent frameworks.

5. **TheRouter.ai** publishes a governance comparison guide for Claude Code, Codex, ZCode, Cursor Enterprise — the category is mature enough to have comparison content.

6. **Enterprise Coding Agent Deployment Playbook (2026)** identifies 7 non-negotiable controls: SSO/SCIM, SIEM export, secret scanning, PR gates, license governance, incident response, audit trails. These are being built by the platforms, not by third-party libraries.

### What's left for HUMMBL?

The cross-tool governance gap is closing via **gateways** (Claude apps gateway, Databricks Unity AI Gateway). The gateway pattern — route all agent traffic through one proxy that enforces policy — is the winning architecture, and it's being built by the vendors and platforms.

HUMMBL is a **library**, not a gateway. To compete, you'd need to build a gateway — which is a different product than a governance primitive library.

**The surviving niche:** HUMMBL as the governance engine _inside_ a gateway that someone else builds. But Databricks and Anthropic have built their own. There's no clear buyer for "embed HUMMBL in your gateway" when the gateway vendors are building their own governance.

### Honest assessment

**UC-1 as originally framed (cross-tool AI coding governance library) is not viable.** The vendors and platforms are absorbing it via gateways. The buyer doesn't want a library; they want a gateway or a managed service. HUMMBL's architecture (in-process library) doesn't match the winning market architecture (gateway proxy).

**The surviving niche:** HUMMBL as the governance engine for a coding-agent gateway targeting mid-market companies that can't afford Databricks Unity or don't want Anthropic's gateway. But this requires building a gateway, which is a different business than shipping a library.

### Kill criteria

- **Kill UC-1 as a standalone product.** The vendors are absorbing it. The gateway architecture wins, and HUMMBL is not a gateway.
- **Retain UC-1 as a feature** if a gateway product is built (see UC-2 below for the gateway question).

---

## UC-2: AI agent cost-management SaaS — lowest build effort?

### The finding that changes everything

The cost-management SaaS market is already crowded with 5+ direct competitors, all offering kill switches and budget enforcement — the exact wedge UC-2 proposed.

**Direct competitors (all shipping now):**

| Competitor        | Model                    | Kill switch                         | Budget enforcement                      | Key differentiator                                                                                  |
| ----------------- | ------------------------ | ----------------------------------- | --------------------------------------- | --------------------------------------------------------------------------------------------------- |
| **AICostManager** | SaaS                     | Yes (JWT kill-switches)             | Yes (per-key, per-client, per-service)  | Privacy-first (metadata only, no prompt ingestion), client billing, MCP server integration          |
| **subKey**        | Proxy SaaS               | Yes (panic mode, hard caps)         | Yes (monthly caps, scoped keys)         | Scoped temporary keys, PII redaction, allowed hours, 2-line integration                             |
| **BurnLens**      | Local-first proxy        | Yes (429 before provider)           | Yes (daily limits per API key)          | Local-first (prompts never leave machine), $29/mo teams, supports Cursor/Claude Code/Cline/Windsurf |
| **NullSpend**     | Open-source + proxy      | Yes (velocity circuit breakers)     | Yes (pre-request, sub-ms)               | Open-source, per-customer margin tracking via Stripe, human-in-the-loop approval                    |
| **Waxell**        | Runtime governance plane | Yes (session spend caps)            | Yes (per-session, per-action)           | Positions as "runtime governance" not just cost — governs tool calls, DB ops, outputs               |
| **Helicone**      | Gateway/observability    | Yes (Helicone-RateLimit-Policy 429) | Yes (per-user, per-property spend caps) | 100+ models, routing optimization, established observability player                                 |

### What every competitor has that HUMMBL doesn't

1. **A proxy or SDK that intercepts API calls.** This is the architecture that works for cost management. HUMMBL's `cost_governor` is a library you call — it doesn't intercept anything automatically.
2. **A dashboard.** Cost management is a visual product. HUMMBL has no dashboard.
3. **Multi-provider support out of the box.** All competitors support OpenAI, Anthropic, Google, etc. HUMMBL's `cost_governor` records usage but doesn't integrate with provider APIs.
4. **Real-time alerting** (Slack, email, webhooks). HUMMBL has `on_budget_alert` callback but no alerting infrastructure.

### What HUMMBL has

1. `cost_governor` — a well-built SQLite-backed budget tracker with ALLOW/WARN/DENY. But it's a component, not a product.
2. `kill_switch` — a well-built emergency halt. But it's not wired to intercept API calls.

### Honest assessment

**UC-2 as originally framed (governance-first cost SaaS) is not viable as a standalone product.** The market has 5+ competitors who all have the proxy, the dashboard, the multi-provider support, and the alerting. HUMMBL's `cost_governor` is a component that would need to be wrapped in a full SaaS product to compete — and the competitors are already there.

The "governance-first" differentiation (was it allowed to spend that, not just what did it cost) is being eroded: Waxell positions as "runtime governance" and NullSpend has "human-in-the-loop approval." The gap is closing.

**The surviving niche:** HUMMBL's `cost_governor` as an embeddable, zero-dep component for developers who want budget enforcement without a proxy or SaaS dependency. This is a library feature, not a SaaS business.

### Kill criteria

- **Kill UC-2 as a standalone SaaS product.** The market is crowded with funded competitors who have the proxy + dashboard + multi-provider stack. Building that from scratch as a solo founder is a losing race.
- **Retain `cost_governor` as a feature** of a different use case or as an open-source library feature that drives adoption.

---

## The honest conclusion: all three preliminary picks have serious competitive headwinds

The use case catalog's preliminary read was based on incomplete competitive research. The stress test reveals:

| Use case                    | Preliminary read                               | Stress-test finding                                            | Verdict                                            |
| --------------------------- | ---------------------------------------------- | -------------------------------------------------------------- | -------------------------------------------------- |
| UC-7 (MCP governance)       | "Biggest differentiation, no one owns it"      | Microsoft AGT owns it (6K stars, 5 SDKs, shipped proxy, MIT)   | **Kill as standalone.** Retain as feature.         |
| UC-1 (AI coding governance) | "Fastest to revenue, you have arbiter"         | Vendors absorbing it via gateways (Claude, Databricks, Cursor) | **Kill as standalone.** Gateway architecture wins. |
| UC-2 (cost SaaS)            | "Lowest build effort, cost_governor is proven" | 5+ funded competitors with proxy + dashboard + kill switches   | **Kill as standalone.** Crowded market.            |

### Where HUMMBL's differentiation actually survives

The stress test isn't all bad news. The competitive research revealed where HUMMBL's unique properties — **zero dependencies, in-process, stdlib-only, already on PyPI, deterministic** — are actually defensible:

1. **Defense / DoD (UC-5):** Microsoft AGT is MIT-licensed and proxy-based. Defense procurement needs air-gapped, no-cloud, no-dependency, in-process governance. HUMMBL's stdlib-only design wins here. AGT's 5 SDKs and proxy architecture are liabilities in air-gapped environments. Operator has the credentials (DoD 8140, clearance strategy, T0-T4 tiers). **This is the most defensible use case.**

2. **Fractional AIRO (UC-6):** Consulting. Microsoft doesn't compete. The competitors are Big 4 (expensive, slow, not AI-native). HUMMBL's tooling-backed assessments (compliance mapper, governance scorecard, gap analysis skills) are a differentiator. **Fastest to revenue, no competitive headwinds from Microsoft.**

3. **Physical AI / robotics (UC-12):** No competitor has `physical_governor` (kinematic constraints, pHRI safety modes). AGT is software-only. This is genuinely novel. Small market but zero competition. **Highest differentiation, smallest market.**

4. **The "zero-dep embedded" positioning:** HUMMBL as the governance library for environments that can't add dependencies — air-gapped, edge, on-device, supply-chain-paranoid, regulated. This is a positioning overlay, not a use case. It amplifies UC-5, UC-10 (healthcare), UC-12 (robotics).

### Recommendation

**Pivot the top-3 stress-test picks to:**

1. **UC-5 (defense/DoD)** — most defensible against Microsoft AGT; Operator has credentials; stdlib-only wins in air-gapped environments
2. **UC-6 (fractional AIRO)** — fastest to revenue; no Microsoft competition; tooling-backed consulting
3. **UC-12 (physical AI/robotics)** — highest differentiation; zero competition; `physical_governor` is unique

**Retain UC-7, UC-1, UC-2 as features** of the above, not as standalone products:

- MCP governance (UC-7) becomes a capability of the defense offering (UC-5)
- Cost governance (UC-2) becomes a feature of the fractional AIRO assessments (UC-6)
- AI coding governance (UC-1) becomes a use case the fractional AIRO assesses for clients

### What I'd stress-test next

If you agree with the pivot, the next stress-test cycle covers UC-5, UC-6, UC-12:

- **UC-5:** DoD AI governance procurement paths (SBIR/STTR topics, defense prime subcontracting, CDAO alignment), air-gapped deployment story, Operator's clearance timeline
- **UC-6:** First 3 target clients, assessment deliverable template, pricing, channel (does Operator have a network to reach founders/VPs who need AI governance posture?)
- **UC-12:** Robotics OEM landscape, safety standard alignment (ISO 10218, ISO/TS 15066), whether `physical_governor` meets any existing safety certification path

---

## Appendix: Sources

### UC-7 (MCP governance)

- Microsoft Agent Governance Toolkit: https://github.com/microsoft/agent-governance-toolkit/ (6,091 stars, MIT, April 2026)
- Microsoft Developer Blog: "Securing MCP: A Control Plane for Agent Tool Execution"
- Microsoft Open Source Blog: "Introducing the Agent Governance Toolkit" (2026-04-02)
- AGT MCP Governance Policies: https://microsoft.github.io/agent-governance-toolkit/tutorials/policy-as-code/mcp-governance/
- OWASP MCP Tool Poisoning: https://owasp.org/www-community/attacks/MCP_Tool_Poisoning
- MCP spec security review (7 protocol-level gaps): https://github.com/modelcontextprotocol/modelcontextprotocol/issues/3180

### UC-1 (AI coding governance)

- Claude Code gateways docs: https://code.claude.com/docs/en/gateways
- Databricks: "How Databricks manages its own coding agent spend with Unity AI Gateway Budgets"
- Databricks: "Governing coding agent sprawl with Unity AI Gateway"
- TheRouter.ai: "Agentic Coding Model Governance: Operator Guide"
- Enterprise Coding Agent Deployment Playbook 2026: https://www.digitalapplied.com/blog/enterprise-coding-agent-deployment-playbook-2026

### UC-2 (cost SaaS)

- AICostManager: https://www.aicostmanager.com/
- subKey: https://subkey.ai/
- BurnLens: https://burnlens.app/
- NullSpend: https://github.com/NullSpend/nullspend
- Waxell vs Helicone: https://www.waxell.ai/blog/waxell-vs-helicone
