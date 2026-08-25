# Batch Ingestion Framework (BIF)
## A Systematic Methodology for Technical Knowledge Acquisition
> Version: 1.0
> Created: 2026-03-24
> Author: Reuben + Claude (Anthropic Academy project)
> License: Use freely, adapt as needed

---

## Executive Summary

Batch Ingestion Framework (BIF) is a repeatable methodology for building comprehensive knowledge bases on any company, product, service, or technical domain. It was developed during Reuben's Anthropic Academy coursework and proven across 10 canonical batches covering the entire Anthropic ecosystem.

The core insight: **structured consumption in priority order, with each batch building on the last, creates layered understanding that random reading never achieves.**

---

## Part 1: The Framework

### 1.1 The Four Phases

Every ingestion project follows four phases, each containing 2-4 batches:

```
Phase 1: FOUNDATION (Batches 1-4)
  → What it is, how it works, what's current
  
Phase 2: TECHNIQUE (Batches 5-7)  
  → How to use it well, how to avoid mistakes, what the experts think

Phase 3: SOURCE (Batches 8-10)
  → How the creators use it themselves, what to clone, why it works this way

Phase 4: ECOSYSTEM (Batches 11+)
  → Adjacent tools, community patterns, competitive context
```

### 1.2 Phase Details

#### Phase 1: Foundation (Map the Canonical Sources)

| Batch | Name | What to Capture | Priority |
|-------|------|----------------|----------|
| 1 | **Core Reference** | Official API/product docs, `llms.txt` or equivalent, site map of all available documentation | Critical |
| 2 | **Protocol / Architecture** | How the system works under the hood — architecture, data flow, core abstractions | Critical |
| 3 | **Tooling Docs** | CLI tools, SDKs, IDE integrations, developer experience layer | Critical |
| 4 | **Delta Document** | What's changed recently — new features, deprecations, migration guides, breaking changes vs. your current knowledge | Critical |

**Exit criteria**: You can explain the product's architecture, use its primary API, and know what's current vs. outdated.

#### Phase 2: Technique (Go Deep on How-To)

| Batch | Name | What to Capture | Priority |
|-------|------|----------------|----------|
| 5 | **Best Practices** | Official best practices, techniques, patterns. The "how to use this well" docs. | High |
| 6 | **Production Hardening** | Guardrails, error handling, security, reliability, monitoring. The "don't ship without this" docs. | High |
| 7 | **Thought Leadership** | Engineering blog posts, conference talks, case studies. How the creators think about their product. | High |

**Exit criteria**: You can build production-quality implementations and articulate why certain patterns work better than others.

#### Phase 3: Source (Study the Creators)

| Batch | Name | What to Capture | Priority |
|-------|------|----------------|----------|
| 8 | **Production Configs** | System prompts, default configurations, internal settings the creators actually use | Medium-High |
| 9 | **Code Repositories** | What repos to clone, directory structures, key files, how to use them | Medium-High |
| 10 | **Research & Philosophy** | Why the product works this way — research papers, design decisions, safety frameworks, model cards | Medium |

**Exit criteria**: You understand not just how to use it, but why it was built this way and how the creators use it themselves.

#### Phase 4: Ecosystem (Expand Outward)

| Batch | Name | What to Capture | Priority |
|-------|------|----------------|----------|
| 11+ | **Cookbooks & Deep-Dives** | Hands-on implementations, notebooks, worked examples | As needed |
| 12+ | **Integrations & Ecosystem** | Complementary tools, plugins, server galleries, partner docs | As needed |
| 13+ | **Consumer/Product Docs** | End-user documentation, pricing, plans, feature availability | As needed |
| 14+ | **Community Analysis** | Expert commentary, benchmarks, comparisons, leaked internals | As needed |
| 15+ | **Competitive Context** | How this compares to alternatives — for positioning and decision-making | As needed |

**Exit criteria**: You can operate as a subject matter expert, make architectural decisions, create content, and advise others.

### 1.3 Batch Execution Protocol

Each batch follows the same execution steps:

```
1. IDENTIFY sources (search for official docs, llms.txt, sitemaps)
2. FETCH content (web_fetch, web_search, or manual copy)
3. EXTRACT key information (concepts, code patterns, architecture, changes)
4. COMPILE into a clean knowledge file (markdown, structured, searchable)
5. VALIDATE coverage (does this batch answer all its intended questions?)
6. DELIVER as uploadable knowledge file with metadata header
```

### 1.4 Knowledge File Format Standard

Every batch output should follow this template:

```markdown
# [Topic] — [Subtitle]
> Source: [primary URL(s)]
> Fetched: [date]
> Purpose: [one-line description of what this file covers]

---

## [Section 1]
[Content organized for quick scanning — headers, tables, code blocks]

## [Section 2]
[...]

---

## [Topic] Documentation Site Map
[If applicable — navigation structure of the source]
```

**File naming convention**: `##_Topic_Name.md` (e.g., `01_Claude_API_Primer.md`)

### 1.5 Source Priority Hierarchy

When multiple sources exist, prioritize in this order:

1. **`llms-full.txt` / `llms.txt`** — purpose-built for LLM ingestion
2. **Official documentation** (docs.*, platform.*, code.*)
3. **API reference pages** — exact parameters, schemas, examples
4. **Engineering blog posts** — from the company's own team
5. **GitHub repositories** — READMEs, changelogs, key source files
6. **Model/system cards** — capabilities, limitations, safety
7. **Release notes / changelogs** — what's new, what's deprecated
8. **Community analysis** — expert blogs, teardowns, benchmarks
9. **Press coverage / Wikipedia** — context, timeline, positioning
10. **Forum discussions** — edge cases, gotchas, real-world experience

---

## Part 2: PRD Template for Ingestion Projects

Use this template to plan any new ingestion project before starting.

---

### INGESTION PROJECT PRD

**Project Name**: [e.g., "Anthropic Ecosystem Ingestion" or "AWS Solutions Architect Prep"]

**Objective**: [What you're trying to understand/achieve]

**Timeline**: [Target completion]

**Context**: [Why now — course, certification, job requirement, product evaluation]

---

#### Target Domain Profile

| Field | Value |
|-------|-------|
| Company/Product | |
| Primary documentation URL | |
| `llms.txt` / `llms-full.txt` available? | Yes / No / Unknown |
| Documentation format | Docs site / PDF / GitHub / Wiki / Other |
| Estimated total doc size | Small (<50 pages) / Medium (50-500) / Large (500+) / Massive (1000+) |
| Rate of change | Stable / Monthly updates / Weekly updates / Rapidly evolving |
| SDK/API involved? | Yes / No |
| Code repos to analyze? | List URLs |
| Certification/exam involved? | Yes (name) / No |
| Competitive alternatives | List 2-3 |

---

#### Source Inventory

*List every source you'll draw from, in priority order:*

| # | Source | URL | Type | Est. Size | Phase |
|---|--------|-----|------|-----------|-------|
| 1 | | | Docs / Blog / Repo / API Ref / Paper | | 1-4 |
| 2 | | | | | |
| 3 | | | | | |
| ... | | | | | |

---

#### Batch Plan

| Batch | Phase | Name | Primary Sources | Key Questions to Answer |
|-------|-------|------|----------------|------------------------|
| 01 | Foundation | | | |
| 02 | Foundation | | | |
| 03 | Foundation | | | |
| 04 | Foundation | | | |
| 05 | Technique | | | |
| 06 | Technique | | | |
| 07 | Technique | | | |
| 08 | Source | | | |
| 09 | Source | | | |
| 10 | Source | | | |
| 11+ | Ecosystem | | | |

---

#### Success Criteria

After completing all batches, I should be able to:

- [ ] Explain the product/service architecture to a technical audience
- [ ] Use the primary API/SDK to build working implementations
- [ ] Know what's current vs. outdated in my knowledge
- [ ] Apply official best practices and avoid common mistakes
- [ ] Articulate why certain patterns work (not just how)
- [ ] Reference the creators' own usage patterns and configs
- [ ] Clone and work with the relevant code repositories
- [ ] Understand the research/philosophy behind design decisions
- [ ] Pass the relevant certification/exam (if applicable)
- [ ] Create content or advise others on this domain

---

#### Knowledge File Delivery Plan

| File | Batch | Upload To | Format |
|------|-------|-----------|--------|
| `01_[name].md` | 1 | Project knowledge / Drive / Repo | Markdown |
| `02_[name].md` | 2 | | Markdown |
| ... | | | |

---

#### Maintenance Plan

| Trigger | Action |
|---------|--------|
| Major version release | Re-run Batch 4 (Delta Document) |
| New feature announced | Append to relevant batch file |
| Certification exam updated | Re-evaluate batch plan |
| Quarterly review | Check changelogs, refresh stale batches |

---

## Part 3: Technical Specs Checklists

### 3.1 Pre-Ingestion Checklist

Before starting any batch ingestion project:

- [ ] **Identify the llms.txt**: Check `[domain]/llms.txt` and `[domain]/llms-full.txt`
- [ ] **Map the docs site structure**: Capture the full navigation/sitemap
- [ ] **Check for API primer**: Look for LLM-optimized summary docs (e.g., `/for-claude`, `/claude_api_primer`)
- [ ] **Identify the changelog/release notes**: Where do updates get announced?
- [ ] **Find the engineering blog**: Company's technical thought leadership
- [ ] **Locate code repos**: GitHub org, key repos, stars/activity
- [ ] **Check for system cards/model cards**: Capabilities and limitations docs
- [ ] **Identify the SDK(s)**: Language-specific packages and install commands
- [ ] **Note rate limits / access requirements**: API keys, pricing tiers, beta headers
- [ ] **Assess documentation freshness**: When was it last updated?

### 3.2 Per-Batch Execution Checklist

For each batch:

- [ ] **Define the batch scope**: What specific questions will this batch answer?
- [ ] **List target URLs**: 3-10 specific pages/resources to fetch
- [ ] **Fetch content**: Use web_search → web_fetch pipeline
- [ ] **Handle token limits**: If content exceeds fetch limits, split into multiple fetches
- [ ] **Extract key patterns**: Code examples, architecture diagrams, configuration templates
- [ ] **Identify deltas**: What's different from my current knowledge?
- [ ] **Compile knowledge file**: Clean markdown with metadata header
- [ ] **Cross-reference**: Does this batch contradict or update anything from previous batches?
- [ ] **Name consistently**: `##_Topic_Name.md` format
- [ ] **Upload to project**: Add as knowledge file in Claude Project

### 3.3 Quality Checklist for Knowledge Files

Each knowledge file should pass these checks:

- [ ] **Metadata header present**: Source URL, fetch date, purpose statement
- [ ] **Structured with headers**: Scannable — a reader can find any section in 10 seconds
- [ ] **Code examples included**: Where applicable, with current model IDs and syntax
- [ ] **Tables for comparisons**: Models, features, pricing, options
- [ ] **No stale information**: Model names, API endpoints, feature availability all current
- [ ] **Site map captured**: If this is a docs source, include the navigation structure
- [ ] **Delta noted**: What's new vs. what a reader might already know
- [ ] **Actionable**: A developer could use this file to start building immediately
- [ ] **Self-contained**: Doesn't require opening external links to be useful (though links are included for reference)
- [ ] **Under context budget**: Each file should be usable as a Claude Project knowledge file (target: under 50K tokens per file)

### 3.4 Certification / Exam Adaptation Checklist

When the ingestion project targets a certification:

- [ ] **Exam guide obtained**: Official exam blueprint/domains/objectives
- [ ] **Domains mapped to batches**: Each exam domain has at least one corresponding batch
- [ ] **Weightings noted**: Higher-weighted domains get more batch coverage
- [ ] **Practice questions sourced**: Official practice exams, sample questions
- [ ] **Gap analysis done**: After Phase 1-2, identify which domains need more depth
- [ ] **Flashcard extraction**: Key facts, numbers, and distinctions pulled into study format
- [ ] **Hands-on labs identified**: Which repos/quickstarts to clone for practical experience
- [ ] **Time-boxed review plan**: Spaced repetition schedule for knowledge retention

### 3.5 Product/Service Evaluation Checklist

When the ingestion project evaluates a product for professional use:

- [ ] **Use case defined**: What specific problem am I evaluating this for?
- [ ] **Decision criteria listed**: Performance, cost, developer experience, ecosystem, support
- [ ] **Quick-start completed**: Actually built something with the product (not just read about it)
- [ ] **Pricing modeled**: Cost at my expected usage level
- [ ] **Limitations documented**: What can't it do? What are the known issues?
- [ ] **Migration path assessed**: How hard is it to switch to/from this product?
- [ ] **Competitive comparison captured**: How does it stack up on my specific criteria?
- [ ] **Team readiness evaluated**: Can my team adopt this? Learning curve?
- [ ] **Security/compliance checked**: Data residency, ZDR, SOC2, etc.
- [ ] **Decision documented**: Go/no-go with reasoning

### 3.6 Content Creation Adaptation Checklist

When the ingestion project supports content creation (blog, course, talks):

- [ ] **Audience defined**: Who am I creating for? What do they already know?
- [ ] **Unique angles identified**: What can I say that others aren't saying?
- [ ] **Key narratives extracted**: Stories, milestones, surprising facts from the research
- [ ] **Code examples adapted**: Modified for my audience's context
- [ ] **Visual opportunities flagged**: Diagrams, comparisons, architecture visuals
- [ ] **Thought leadership hooks**: Contrarian takes, predictions, framework applications
- [ ] **Series structure planned**: How to break the knowledge into publishable chunks
- [ ] **Sources cited**: All claims traceable to specific batch files

---

## Part 4: Domain-Specific Starter Templates

### 4.1 Cloud Platform Ingestion (AWS / GCP / Azure)

| Batch | Name | Sources |
|-------|------|---------|
| 01 | Service Overview | Official docs, service FAQ, pricing page |
| 02 | Architecture & Patterns | Well-Architected Framework, reference architectures |
| 03 | SDK & CLI | SDK docs, CLI reference, CloudFormation/Terraform |
| 04 | What's New | re:Invent announcements, service changelog, deprecations |
| 05 | Best Practices | Whitepapers, solution guides, performance tuning |
| 06 | Security & Compliance | IAM, encryption, compliance certifications, shared responsibility |
| 07 | Case Studies & Blogs | AWS Architecture Blog, customer case studies |
| 08 | Default Configs & Templates | CloudFormation samples, CDK constructs, SAM templates |
| 09 | GitHub Repos | AWS samples, CDK library, official examples |
| 10 | Exam Prep (if applicable) | Exam guide, practice questions, domain mapping |

### 4.2 SaaS Product Evaluation

| Batch | Name | Sources |
|-------|------|---------|
| 01 | Product Overview & API | Docs, API reference, quickstart |
| 02 | Architecture & Integrations | How it works, webhook/event model, data flow |
| 03 | SDK & Developer Tools | SDKs, CLI, Postman collections, sandbox |
| 04 | Pricing & Limits | Pricing page, rate limits, plan comparison |
| 05 | Best Practices | Implementation guides, common patterns |
| 06 | Security & Compliance | SOC2, GDPR, data handling, SSO |
| 07 | Customer Stories & Reviews | Case studies, G2/Capterra reviews, community forums |
| 08 | Changelog & Roadmap | Release notes, public roadmap, feature requests |
| 09 | Competitive Analysis | Alternatives, comparison matrices, migration guides |
| 10 | Decision Document | Go/no-go assessment with evidence from batches 1-9 |

### 4.3 Programming Framework / Library

| Batch | Name | Sources |
|-------|------|---------|
| 01 | Core Docs & Concepts | Official docs, getting started, core API |
| 02 | Architecture & Design Decisions | RFC/design docs, architecture overview |
| 03 | CLI & Toolchain | Build tools, dev server, testing utilities |
| 04 | Migration & Changelog | Upgrade guides, breaking changes, version history |
| 05 | Patterns & Anti-Patterns | Best practices guide, style guide, common mistakes |
| 06 | Performance & Production | Optimization, deployment, monitoring, SSR/ISR |
| 07 | Core Team Blog & Talks | Team blog posts, conference talks, RFCs |
| 08 | Source Code Study | Key files, plugin architecture, extension points |
| 09 | Ecosystem & Plugins | Popular packages, middleware, community tools |
| 10 | Comparison & Selection | vs. alternatives, benchmark results, adoption trends |

### 4.4 AI/ML Model or Platform

| Batch | Name | Sources |
|-------|------|---------|
| 01 | API Reference & Quickstart | Docs, API primer, model IDs, basic requests |
| 02 | Model Architecture & Capabilities | Model cards, benchmarks, context limits |
| 03 | SDK & Developer Tools | SDKs, playground, CLI tools, IDE extensions |
| 04 | What's New & Migration | Changelog, new features, deprecations, breaking changes |
| 05 | Prompt Engineering & Best Practices | Prompting guides, techniques, evaluation methods |
| 06 | Production & Safety | Guardrails, rate limits, content filtering, monitoring |
| 07 | Research & Engineering Blog | Papers, technical posts, benchmark analysis |
| 08 | System Prompts & Configs | Default prompts, recommended settings, tuning guides |
| 09 | Code Repos & Examples | Cookbooks, quickstarts, sample apps |
| 10 | Research & Safety Philosophy | Alignment approach, safety framework, model cards |

---

## Part 4B: Hardening Protocols

### 4B.1 Token Budget Management

Each knowledge file should stay under 50K tokens to remain usable as a Claude Project knowledge file. To manage this:

**Measuring tokens:**
```python
# Quick estimate: 1 token ≈ 4 characters in English
char_count = len(open("batch_file.md").read())
estimated_tokens = char_count / 4
print(f"~{estimated_tokens:,.0f} tokens")
```

**When a batch exceeds 50K tokens:**
1. Split into sub-batches: `05a_Prompt_Engineering.md` and `05b_Guardrails.md`
2. Extract code examples into a companion file: `05_code_examples.md`
3. Move reference tables to an appendix file: `05_appendix.md`
4. Keep the main batch file as a summary with pointers to sub-files

**Budget allocation guide:**
| Content type | Token budget |
|---|---|
| Core concepts + architecture | 40% |
| Code examples | 30% |
| Tables + comparisons | 15% |
| Navigation / site map | 10% |
| Metadata + headers | 5% |

### 4B.2 Stale Fetch Detection

Web fetches can return cached, outdated, or CDN-stale content. Protect against this:

**Before trusting a fetch:**
1. Check the page for a "last updated" or "last modified" date
2. Compare version numbers mentioned in the page against the latest release
3. Cross-reference with the changelog — if the changelog mentions features not in your fetch, the page is stale
4. If the page references a model ID that's been superseded (e.g., `claude-3-opus` when `claude-opus-4-6` exists), the content is outdated

**Freshness markers to look for:**
- `Last updated: [date]` in page footer or header
- API version strings (e.g., `2025-01-01` in Anthropic's API version header)
- Model IDs (current: `claude-opus-4-6`, `claude-sonnet-4-6`, `claude-haiku-4-5`)
- SDK version numbers (compare against `npm view @anthropic-ai/sdk version` or `pip show anthropic`)

**If a fetch seems stale:**
1. Try fetching with a cache-busting query parameter: `?t=[timestamp]`
2. Search for the same content via web_search to find a fresher source
3. Check the Wayback Machine to confirm whether the content has changed
4. Note the staleness risk in the knowledge file metadata: `> Freshness: UNCERTAIN — page has no date stamp`

### 4B.3 Version Diff Protocol

Batch 4 (Delta Document) requires identifying what's changed since your last ingestion. This is hard because documentation doesn't have git-style diffs. Use this protocol:

**Method 1: Changelog-first (preferred)**
1. Fetch the official changelog/release notes
2. Filter to entries since your last ingestion date
3. For each change, fetch the updated documentation page
4. Document: what changed, what was added, what was deprecated/removed

**Method 2: Structural diff**
1. Compare your previous batch file's table of contents against the current docs site navigation
2. New sections = new content to ingest
3. Missing sections = deprecated content to flag
4. Changed section titles = potential rewrites to review

**Method 3: Search-based diff**
1. Search for `"new" OR "updated" OR "deprecated" OR "breaking change" site:[docs.domain.com]`
2. Filter results by date range (since last ingestion)
3. Fetch and document each result

**Method 4: Model-assisted diff**
1. Provide Claude with your previous batch file + the current page content
2. Ask: "What has changed between these two versions? List additions, removals, and modifications."
3. This works well for pages under 10K tokens

**Delta file format:**
```markdown
# Delta Document — [Product] — [Date]
> Previous ingestion: [date]
> Sources checked: [list]

## New Since Last Ingestion
- [feature/concept]: [one-line summary] — [source URL]

## Changed
- [feature/concept]: [what changed] — [source URL]

## Deprecated / Removed
- [feature/concept]: [status] — [migration path if any]

## Unchanged (Spot-Checked)
- [list of major features confirmed still current]
```

---

## Part 5: Maintenance & Evolution

### 5.1 When to Re-Ingest

| Trigger | Action | Scope |
|---------|--------|-------|
| Major version release | Full re-run of Batch 4 (Delta), spot-check Batches 1-3 | Foundation |
| Breaking change announced | Update affected batch files, note in Delta | Targeted |
| New feature launch | Append to relevant batch or create new ecosystem batch | Targeted |
| Quarterly review | Scan changelogs, refresh any stale pricing/limits | Light pass |
| Pre-certification exam | Re-run all batches with exam blueprint as filter | Full |
| Competitive landscape shift | Update ecosystem batches, add comparison batch | Ecosystem |

### 5.2 Scaling to Teams

This framework works for individual learning but scales to team knowledge:

- **Shared project**: Upload all batch files to a Claude Project that team members can access
- **Division of labor**: Assign different batches to different team members
- **Review process**: Each batch file gets a quality review before upload
- **Living documentation**: Designate an owner for each batch file who keeps it current
- **Onboarding tool**: New team members work through batches 1-4 as orientation

### 5.3 Framework Versioning

As you use BIF across multiple projects, patterns will emerge:

- Some domains need more Foundation batches (complex architectures)
- Some need more Ecosystem batches (rich integration landscape)
- Certification projects need a specialized exam-prep batch
- Product evaluations need a decision-document batch

Adapt the template. The four phases are constant; the specific batches flex to the domain.

---

## Appendix A: Tool Commands Quick Reference

For Claude-assisted ingestion:

```
# Search for documentation
web_search: "[product] llms.txt documentation"
web_search: "site:[docs.domain.com] [topic]"

# Fetch specific pages
web_fetch: "[URL]" with text_content_token_limit=15000-30000

# Check for LLM-optimized docs
web_fetch: "[domain]/llms.txt"
web_fetch: "[domain]/llms-full.txt"

# Save knowledge file
create_file: "/mnt/user-data/outputs/##_Topic_Name.md"

# Present to user
present_files: ["/mnt/user-data/outputs/##_Topic_Name.md"]
```

## Appendix B: Proven Results

### Anthropic Ecosystem Ingestion (March 2026)

| Metric | Value |
|--------|-------|
| Total batches | 10 canonical + ecosystem planned |
| Total knowledge files | 13 (10 batches + 3 support files) |
| Sources covered | docs.anthropic.com, platform.claude.com, modelcontextprotocol.io, anthropic.com/engineering, github.com/anthropics |
| Web searches executed | ~50+ |
| Pages fetched | ~30+ |
| Documentation coverage | Comprehensive — all major developer docs, API reference, MCP spec, Claude Code, engineering blog, system prompts, research |
| Time to complete | Single session (~4 hours) |
| Reusable for | Any future Anthropic course, HUMMBL MCP development, API projects |

---

*This framework is a living document. Update it as you complete more ingestion projects and discover patterns that work for your specific learning style and professional needs.*
