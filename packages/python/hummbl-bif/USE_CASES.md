# BIF Use Cases

A brainstorm of ways to apply the Batch Ingestion Framework beyond the four domain templates shipped in `templates/`. Each entry is a starting point, not a finished template — the canonical methodology lives in [FRAMEWORK.md](FRAMEWORK.md), and the four phases (Foundation → Technique → Source → Ecosystem) stay constant. What flexes are the specific batches inside each phase.

The goal here is breadth. Entries are short on purpose: pick one that fits your situation, copy the closest template from `templates/`, and bend the batches using the notes below.

---

## By Persona

**Certification candidate.** Ingest an exam's target ecosystem in priority order so every batch maps to a published exam domain. Already proven against the Anthropic CCA-F ecosystem (see `examples/README.md`).
_Batch flex:_ Add an explicit exam-map batch after Phase 1; weight Phase 2 (Technique) toward the domains with highest exam weighting.

**Architect onboarding to an unfamiliar stack.** A new role, a new team, or a new acquisition drops an entire stack on your desk; BIF gives you a four-phase ramp instead of random doc-surfing.
_Batch flex:_ Heavier Foundation (often 5–6 batches) to cover each layer of the stack; Phase 3 (Source) focuses on internal runbooks and ADRs rather than public research.

**Consultant ramping on a client's tech.** You need to sound credible in a kickoff meeting next week and build delivery plans the week after.
_Batch flex:_ Collapse Phase 4 (Ecosystem); swap Phase 3 "Source" for interviews with the client's engineers where public docs don't exist.

**Team lead building a shared Claude Project.** Treat BIF as the pipeline that fills a Claude Project knowledge base the whole team leans on.
_Batch flex:_ Add an ownership/refresh-cadence field to every knowledge file; schedule recurring delta batches per Section 5.2 of FRAMEWORK.md.

**Sales engineer preparing for a competitive deal.** Ingest both the prospect's incumbent and your own product, then produce side-by-side talking points and migration outlines.
_Batch flex:_ Double-run Phases 1–2 (once per product); add a dedicated "objection map" batch at the end.

**Technical writer researching a new product line.** Build an accurate mental model before drafting a single page of docs.
_Batch flex:_ Emphasize Phase 3 (Source) — system prompts, research papers, design docs — because writers need to know the "why", not just the "what".

**Developer advocate preparing a talk or series.** Ingest a topic end-to-end so the narrative, code samples, and citations all come from primary sources.
_Batch flex:_ Use the Content Creation adaptation in Section 3.6; add a "hooks and angles" batch between Phase 2 and Phase 3.

**M&A or investment diligence team.** Evaluate a target company's tech credibility, IP, and technical debt against public and disclosed artifacts.
_Batch flex:_ Add a "red flags" batch (abandoned repos, stale blogs, deprecated APIs, security advisories); Phase 4 covers competitive and regulatory context.

---

## By Domain

**Enterprise software (ERP, CRM, ITSM).** Salesforce, Workday, ServiceNow, SAP — huge surface area, heavy customization layer, certification economy.
_Batch flex:_ Add an "extension model" batch (Apex, SuiteScript, flow designers) and a "role-based licensing" batch; Phase 4 often balloons because of partner ecosystems.

**Data platform.** Snowflake, Databricks, BigQuery, Iceberg, DuckDB — moving quickly, lots of overlapping primitives.
_Batch flex:_ Add a "cost model" batch (slot pricing, DBU consumption, storage tiers); Phase 2 weights heavily toward query optimization and governance.

**Database or storage engine.** Postgres, MongoDB, ClickHouse, Redis, object stores.
_Batch flex:_ Phase 1 adds a storage/indexing internals batch; Phase 2 emphasizes operational hardening (backups, replication, failover).

**DevOps and observability toolchain.** Terraform, Kubernetes, Datadog, OpenTelemetry, Grafana.
_Batch flex:_ Collapse Phase 3 (Source) unless studying a specific OSS project; Phase 4 expands into provider/module ecosystems.

**Security tool or threat intel source.** Cloud security posture tools, EDRs, SIEMs, MITRE ATT&CK, CVE feeds.
_Batch flex:_ Add an "indicators and mappings" batch (taxonomies, rule packs); Phase 2 emphasizes detection engineering patterns.

**Compliance and regulatory framework.** SOC 2, HIPAA, GDPR, FedRAMP, PCI DSS, EU AI Act.
_Batch flex:_ Replace "Tooling Docs" (Batch 3) with a "controls catalog" batch; replace Phase 3 (Source) with auditor guidance and case law.

**Open source project you're about to contribute to.** Understand architecture, contribution norms, recent PRs, and the maintainer's worldview before your first patch.
_Batch flex:_ Pull CONTRIBUTING, CODE_OF_CONDUCT, and recent merged PRs into Batch 2; Phase 3 leans heavily on GitHub history and maintainer blog posts.

**Hardware, firmware, or embedded platform.** Silicon SDKs, RTOS, IoT stacks, robotics middleware.
_Batch flex:_ Phase 1 needs datasheets and reference boards; add a "toolchain and flashing" batch; Phase 3 often requires errata sheets.

**Blockchain or web3 protocol.** L1s, L2s, rollups, bridges, zk proving systems.
_Batch flex:_ Add a "economic and governance model" batch; Phase 3 (Source) is dominated by yellow papers and core-dev calls.

**Design system or component library.** Internal design systems, Material, shadcn/ui, Radix.
_Batch flex:_ Phase 1 emphasizes tokens and accessibility; Phase 2 emphasizes composition patterns; Phase 4 tracks adoption across consuming apps.

---

## By Goal / Outcome

**Vendor evaluation → decision memo.** Produce a go / no-go with pricing, limits, risks, and a migration sketch (aligns with Section 3.5 of FRAMEWORK.md).
_Batch flex:_ Add an explicit "decision document" batch at the end; Phase 4 always includes at least two alternatives for comparison.

**Technology migration plan.** Moving off a deprecated SDK, runtime, or platform — for example, a v1 → v2 API cutover or a cloud provider swap.
_Batch flex:_ Run Phase 1 twice (source and target); Batch 4 (Delta) becomes a structured breaking-change diff; add a "parity matrix" batch.

**MCP server design research.** Before wrapping an API or service in an MCP server, ingest it end-to-end so your tool surface matches the mental model the vendor intended.
_Batch flex:_ Phase 1 emphasizes the API reference and auth model; Phase 2 focuses on rate limits and error semantics; skip most of Phase 4.

**Competitive intelligence refresh.** Recurring, lightweight delta runs on competitors so briefings stay current.
_Batch flex:_ Run only Batches 1, 4, and 7 on a quarterly cadence; keep the knowledge files small and timestamped.

**Incident post-mortem playbook generation.** Ingest related tooling, past incidents, and vendor guidance to build a repeatable playbook for a failure mode.
_Batch flex:_ Replace Phase 3 (Source) with internal incident reports; add a "decision tree" batch at the end.

**RFP response preparation.** Ingest the RFP, the buyer's public tech context, and your own product to produce a response grounded in both sides.
_Batch flex:_ Treat the RFP itself as Batch 1; Phase 2 is requirements mapping; Phase 4 is competitive differentiation.

**Curriculum or training program development.** Build a structured course on a new topic — internal bootcamp, customer training, university module.
_Batch flex:_ Phase 1 becomes the learning-objective map; Phase 2 generates exercises; Phase 4 sources case studies and capstones.

**Technology radar entry.** Produce a short, opinionated entry (Adopt / Trial / Assess / Hold) backed by primary-source evidence.
_Batch flex:_ Compress to 3–4 batches total; Phase 4 becomes the rationale and recommendation.

---

## Mobile / Claude Code (Sonnet on the Claude App)

Patterns for using BIF from the Claude mobile app via Claude Code. The methodology doesn't change; what changes is the trigger — these use cases arise while you're away from a desk, and the window is short. Full treatment in [MOBILE_USE_CASES.md](MOBILE_USE_CASES.md).

**Capture-and-Classify on Encounter.** You spot a new tool at a conference, in Slack, or in an article. Describe it; Sonnet classifies it against BIF's four domain templates, drafts a source inventory, and creates a PRD stub for a future desktop ingestion session.
_Batch flex:_ Output is a PRD stub only (FRAMEWORK.md Part 2). Ingestion happens later.

**Delta Document on Breaking News.** A new model, framework version, or API change drops while you're on your phone. Paste the changelog; Sonnet formats it as a Batch 4 Delta Document (New / Changed / Deprecated / Unchanged) matching the `examples/anthropic/04_Delta_Document.md` schema.
_Batch flex:_ Scope is Batch 4 only. Use the Version Diff Protocol from FRAMEWORK.md Part 4B.

**Photo-to-Source Inventory.** Photograph a whiteboard, conference slide, or product screen. Sonnet extracts tool/platform names, cross-references open BIF sessions (`bif status`), and flags which have no ingestion started.
_Batch flex:_ Output feeds the Pre-Ingestion Checklist (FRAMEWORK.md Part 3). Camera and vision input are mobile-native; no desktop equivalent.

**Competitive Intelligence Capture.** During a vendor demo or sales call, describe what you observed; Sonnet structures it as a SaaS Evaluation Batch 10 (Competitive Analysis / Decision Document) while details are fresh. Voice input works well.
_Batch flex:_ Use `templates/saas-evaluation.md` as the base. Plan a full four-phase BIF run later if the vendor warrants it.

**Certification Flashcard Session.** Commuting or waiting — ask Sonnet to generate spaced-repetition Q&A from any completed batch file. Idle time is the right cadence; a desktop session adds no value here.
_Batch flex:_ Follow the Certification Adaptation checklist in FRAMEWORK.md Part 3. Weight questions to published exam domain weightings.

**Batch Planning for a New Domain.** A meeting or conversation surfaces a new domain with a tight deadline. Describe the domain, goal, and timeline; Sonnet maps phases, front-loads the right batches, and drafts a ready-to-use PRD.
_Batch flex:_ Short timelines compress Phase 4; narrow goals compress Phase 3. Use `bif start` with the resulting PRD to open the session.

---

## Cross-Cutting Notes

**Cadence.** BIF is usually described as a one-shot deep dive, but the same pipeline supports two other modes:
- _Recurring delta_ — re-run Batch 4 (Delta Document) on a fixed cadence (weekly for rapidly evolving domains, quarterly for stable ones).
- _Event-driven_ — trigger a partial run on a new release, a vendor acquisition, or a major version bump; scope is usually Foundation + Delta + any affected Technique batches.

**How Phase 4 flexes.** The "Ecosystem" phase is the one most people over- or under-scope. Rough heuristic:
- _Compress_ Phase 4 for time-boxed work (consultant ramp, radar entry, MCP research).
- _Expand_ Phase 4 for domains with rich partner ecosystems (enterprise software, data platforms) or when producing competitive / decision artifacts.
- _Replace_ Phase 4 with internal artifacts (incident reports, ADRs, interviews) when the subject is an internal system with no public ecosystem.

**Reuse before you write.** Four templates already exist under `templates/`. Before drafting a new one, check whether one of them is 80% of what you need and only the batch names change. Most domains above are reachable by flexing an existing template rather than starting from scratch.
