# PUBLIC SITES PLAN
## hummbl.io + operator.com — Content Hub Redesign

**Status:** PLANNING — No execution has occurred. This document is for agent coordination.  
**Owner:** Operator  
**Created:** 2026-08-23  
**Canonical path:** `<repo-root>/.gemini\antigravity-cli\brain\1372b0f4-d179-44ef-8671-99fc161fca6d\PUBLIC_SITES_PLAN.md`  

> **For incoming agents:** Read this entire document before taking any action. Do not deploy, commit, or modify production infrastructure without explicit human approval. This is a planning document only.

---

## 1. What We Are Building

Two public-facing content hubs, each with three clearly separated zones:

```
┌──────────────────────────────────────────────────────────────────┐
│                     THE THREE-ZONE MODEL                         │
├──────────────────┬──────────────────────┬────────────────────────┤
│  ZONE 1          │  ZONE 2              │  ZONE 3                │
│  Click Funnel    │  Documentation / OSS │  Content Hub           │
│  (Convert)       │  (Build Credibility) │  (Grow Audience)       │
├──────────────────┼──────────────────────┼────────────────────────┤
│  Buyers,         │  Developers,         │  Everyone —            │
│  executives,     │  compliance officers,│  builders, founders,   │
│  partners        │  auditors            │  students, regulators  │
│                  │                      │                        │
│  Goal: Book demo │  Goal: Self-serve    │  Goal: Follow, share,  │
│  or purchase     │  to value quickly    │  subscribe, engage     │
└──────────────────┴──────────────────────┴────────────────────────┘
```

The two sites share this structural philosophy but with distinct brand voices:
- **hummbl.io** — dark, technical, product-led (electric blue / amber)
- **operator.com** — warm, editorial, personal-brand-led (off-white / navy / terracotta)

---

## 2. Domain Inventory (Cloudflare — all confirmed)

| Domain | CF Zone ID | Status | Current Target |
|:---|:---|:---|:---|
| `hummbl.io` | `[REDACTED-ZONE-ID]` | Active | `hummbl-production.pages.dev` (CF Pages) |
| `hummbl-dev.com` | `[REDACTED-ZONE-ID]` | Active | Staging (not inspected yet) |
| `operator.com` | `[REDACTED-ZONE-ID]` | Active | `operator-site.pages.dev` (CF Pages) |
| `kernelclothing.com` | `[REDACTED-ZONE-ID]` | Active | **NOTHING — zero DNS records, parked** |

**CF API Token (DNS scope):** stored in 1Password vault `infrastructure` → item `API Credential - cf-dns - Cloudflare`

---

## 3. Current Infrastructure State (Verified)

### hummbl.io
- **Hosting:** Cloudflare Pages → `hummbl-production.pages.dev`
- **Local source repo:** Unknown (likely `hummbl-production/hummbl/` — not yet confirmed locally)
- **Deploy method:** Wrangler Pages (presumed, same pattern as operator.com)
- **Key DNS records:**

| Subdomain | Type | Target |
|:---|:---|:---|
| `hummbl.io` / `www` | CNAME | `hummbl-production.pages.dev` |
| `dashboard.hummbl.io` | CNAME | `hummbl-dashboard.pages.dev` |
| `hermes.hummbl.io` | CNAME | Cloudflare Argo Tunnel |
| `api` / `agents` / `mcp` / `mcp-public` / `mail` | AAAA | `100::` (Worker route placeholders, serving nothing) |
| `docs.hummbl.io` | — | **DOES NOT EXIST** |

- **Live navigation (current site):** Evidence / How it works / Build / Services / Research
- **Current CTAs:** "For builders" → GitHub + PyPI (free). "For teams" → `cal.com/hummbl/30min` (no price listed)
- **No `/pricing` route** — 302 redirect to homepage

### operator.com
- **Hosting:** Cloudflare Pages → `operator-site.pages.dev`
- **Live:** HTTP 200, serving content now
- **Local source:** `<repo-root>/PROJECTS\hummbl-production\operator\`
  - `wrangler.toml` — `name = "operator-site"`, `pages_build_output_dir = "./site"`
  - `site/` — static HTML output directory (editable directly)
- **Deploy command:** `wrangler pages deploy` from that directory
- **Stub subdomains (null AAAA placeholders, not serving):** `chat.operator.com`, `contact.operator.com`

### kernelclothing.com
- **Zero DNS records.** Domain registered in Cloudflare but routes nowhere.
- **No local project.** No archived content. Never publicly indexed.
- **Decision pending** — see §7.

---

## 4. Documentation Infrastructure State (Verified)

### Mintlify
- **Repo:** `<repo-root>/PROJECTS\mintlify-docs`
- **State:** Empty staging skeleton. Contains `.github/`, `docs/adr/`, `docs/issue-promotions/`. No `mint.json`. No MDX files.
- **README says:** "Staging/experimental. Canonical public docs are at `hummbl-dev/docs` (GitHub org, not local). Do not publish from this repo to production."
- **`hummbl-dev/docs`** (the actual canonical docs repo) — **not cloned locally on this machine.**
- **`docs.hummbl.io`** — DNS record does not exist. Returns NXDOMAIN.
- **Mintlify is not deployed anywhere.**

### Content / Essay Pipeline
- **CMS:** None. No Substack, Ghost, Sanity, Contentlayer, or headless CMS of any kind.
- **Framework:** None. No Next.js, Astro, Gatsby, or static site generator configured.
- **Actual pipeline today:** Manual. Essays are written as `.md` files, date-stamped, committed to git.
- **Primary essay surface:** `<repo-root>/PROJECTS\hummbl-governance\docs\research\` — **53 `.md` files** as of 2026-08-23.
- **Frontmatter:** None. Files are raw prose with an informal header (Author, Date, Canonical Surface as bold text, not YAML).
- **Most recent essays (publishable now):**
  1. `2026-08-23_inversion-of-vanity-essay.md`
  2. `2026-08-23_completeness-over-score-essay.md`
  3. `2026-08-23_hummbl_ai_governance_field_mapping_archive.md`

---

## 5. Planned Site Structure

### 5.1 hummbl.io

#### Navigation
```
HUMMBL    [Product]  [Docs ▾]  [Content ▾]  [OSS]    [Start Free →]
```

#### Hero (above fold — Zone 1 entry point)
- **Headline:** `AI Governance Infrastructure.`
- **Subline:** `Control what agents can do. Prove what they actually did.`
- **CTA Primary:** `Start Free` → `/signup`
- **CTA Secondary:** `Read the Docs` → `/docs`
- **Social proof bar:** PyPI downloads · GitHub stars · frameworks covered

#### Zone 1 — For Your Business (pages: `/product`, `/pricing`, `/demo`, `/enterprise`)

| Page | Content |
|:---|:---|
| `/product` | Narrative pitch — the vanity score problem, the HUMMBL solution |
| `/pricing` | Tiers: Community (Free) · Pro · Enterprise — **TIERS NOT YET DEFINED — see §7** |
| `/demo` | Cal.com embed or interactive playground |
| `/case-studies` | Enterprise use cases |
| `/enterprise` | SOC 2, data residency, dedicated infra, SLAs |
| `/compliance` | Regulatory readiness page linking to the 99-framework coverage matrix |

#### Zone 2 — Documentation (`/docs` → `docs.hummbl.io`)

Proposed structure (to be built in `hummbl-dev/docs` repo via Mintlify):

```
/docs
├── Getting Started
│   ├── Install: pip install hummbl-governance
│   ├── Quickstart — first governance tuple
│   └── Core Concepts: Contract (C), Delegation Token (D), Evidence (E)
│
├── Governance Primitives
│   ├── Kill Switch (P1)
│   ├── Circuit Breaker (P2)
│   ├── Cost Governor (P5)
│   ├── Capability Fence (P4)
│   ├── Delegation Token / DCT (P7)
│   ├── Audit Log
│   └── Identity Registry
│
├── Kernel Reference
│   └── K1–K11 Invariants + D1–D7 Doctrine Invariants
│
├── Compliance Coverage
│   ├── How the Coverage Matrix Works (ADR-001)
│   ├── The 4 Boundary States (✅ 🟡 ⚪ ⛔)
│   ├── 99 Framework Index
│   ├── EU AI Act Article Map
│   ├── NIST AI RMF Map
│   ├── ISO 42001 Map
│   └── SOC 2 Map
│
├── JSON Schemas
│   ├── governance_question.schema.json
│   └── capability_manifest.schema.json
│
├── OSS Packages
│   ├── hummbl-governance (PyPI)
│   ├── base120 (PyPI)
│   └── Full index → github.com/hummbl-io/oss
│
└── API Reference (auto-generated from source)
```

#### Zone 3 — Content Hub (`/content`)

| Category | Content | Source |
|:---|:---|:---|
| Essays | Long-form governance philosophy | `hummbl-governance/docs/research/` |
| Research | Field mapping archives, AARs, competitive analysis | `hummbl-governance/docs/research/` |
| Threads | X/Twitter thread embeds | Manual or API |
| LinkedIn | Post embeds | Manual |
| YouTube | Video embeds | YouTube channel |
| Substack | Newsletter archive | Substack (not yet created) |
| Podcast | Episode feed | TBD |
| GitHub | OSS activity | GitHub API |

---

### 5.2 operator.com

#### Navigation
```
Operator    [Work]  [Writing]  [Speaking]  [Contact]
```

#### Hero
- **Headline:** `Founder. Builder. Governance Architect.`
- **Subline:** `Building the infrastructure that keeps AI accountable to humans.`
- **CTA:** `Let's Talk` → `/contact` (Cal.com embed)
- **Right side:** Photo / avatar

#### Zone 1 — Hire Me (`/work`)

| Offering | Description |
|:---|:---|
| Fractional AI Governance Lead | Embedded governance function for orgs building with AI |
| Speaking | Keynotes: AI governance, agent safety, founder narrative |
| Advisory | Board / SAB roles for AI-native startups |
| Workshops | Half/full day: "Build AI Agents That Don't Break Trust" |

#### Zone 2 — Writing & Research (`/writing`)

Chronological editorial card grid of essays from `hummbl-governance/docs/research/`:
- Card: title, date, reading-time estimate, topic tag
- Cross-posted to / sourced from hummbl.io/content

#### Zone 3 — Social & Content (`/content`)

Multi-platform aggregated feed:
- X / Twitter threads
- LinkedIn posts
- YouTube videos
- Podcast episodes

---

## 6. Cross-Site Linking Strategy

```
operator.com/work    ──→  hummbl.io/product    (commercial path)
operator.com/writing ──→  hummbl.io/content    (content discovery)
hummbl.io/content        ──→  operator.com     (personal authorship)
hummbl.io docs           ──→  github.com/hummbl-io/oss  (source of truth)
hummbl.io                ──→  hummbl-dev.com       (staging preview)
```

---

## 7. Open Owner Decisions (Blocking)

These items require Operator's input before any agent should proceed with related work.

### Decision A — Pricing Tiers (blocks Zone 1 on hummbl.io)

A pricing page is net-new. No tiers, prices, or commercial infrastructure exist today. Suggested skeleton:

| Tier | Target Buyer | Suggested Price | What's Included |
|:---|:---|:---|:---|
| **Community** | Developers, researchers | Free forever | Full PyPI package, OSS, docs |
| **Pro** | Product teams | $X / month | Priority support, SLA, private channels |
| **Enterprise** | Regulated industries | Custom / annual | Data residency, dedicated support, audit exports, custom SLAs |

> **Owner:** Do you approve this structure? What is the Pro price point?

### Decision B — kernelclothing.com

The domain is registered in Cloudflare with zero DNS records and zero content. Options:

- **Option A (Recommended):** Add a 301 redirect → `hummbl.io` in Cloudflare to prevent a dark domain.
- **Option B:** Activate as a separate clothing/merch brand (requires a full separate project spec).
- **Option C:** Keep parked indefinitely (current state — no action needed).

> **Owner:** Which option?

### Decision C — Essay Frontmatter Schema

53 existing essays have no YAML frontmatter. Before building a publishing pipeline, we need to define the schema. Proposed:

```yaml
---
title: "Completeness Over Score"
date: 2026-08-23
author: Operator
tags: [governance, philosophy, architecture]
status: published   # draft | published | archived
site: hummbl.io     # hummbl.io | operator.com | both
---
```

> **Owner:** Does this schema look right? Any fields to add/remove?

---

## 8. Work Queue (For Agents — Do Not Start Without Human Approval)

| Priority | Task | Prerequisite | Est. Effort |
|:---|:---|:---|:---|
| **P0** | Ratify pricing tier structure | Owner Decision A | 0 (owner action) |
| **P0** | Approve frontmatter schema | Owner Decision C | 0 (owner action) |
| **P1** | Add YAML frontmatter to 53 essays in `docs/research/` | Decision C approved | ~2 hrs |
| **P1** | Redesign `operator.com` static site | Design mockup confirmed | 1–2 days |
| **P1** | Add `docs.hummbl.io` CNAME in Cloudflare | — | 30 min |
| **P1** | Create `mint.json` in `hummbl-dev/docs` repo and connect Mintlify | — | 2–4 hrs |
| **P2** | Build `/pricing` page on `hummbl.io` | Decision A | 4–8 hrs |
| **P2** | Build content hub zone on `hummbl.io` (essays, research, social) | Frontmatter schema | 2–3 days |
| **P2** | Build `/work` page on `operator.com` | — | 4 hrs |
| **P3** | kernelclothing.com — add redirect or activate | Decision B | 30 min |
| **P3** | Wire `chat.operator.com` and `contact.operator.com` | — | 1 hr |

---

## 9. Design Direction (Confirmed — Mockups Generated)

### hummbl.io
- **Background:** `#0A0A0F` (near-black)
- **Accent primary:** `#3B82F6` (electric blue)
- **Accent secondary:** `#F59E0B` (amber)
- **Typography:** Inter / Geist (sans-serif, technical)
- **Tone:** Professional, technical, precise — not sterile
- **Mockup:** `<repo-root>/.gemini\antigravity-cli\brain\1372b0f4-d179-44ef-8671-99fc161fca6d\hummbl_io_design_1787499611824.jpg`

### operator.com
- **Background:** `#FAFAF8` (warm off-white)
- **Text:** `#1E293B` (deep navy)
- **Accent:** `#C2410C` (terracotta / burnt orange)
- **Typography:** Serif + sans pairing (editorial, warm, intellectual)
- **Tone:** Humanistic, approachable, credible
- **Mockup:** `<repo-root>/.gemini/antigravity-cli/brain/<session-id>/public_sites_design_<timestamp>.jpg`

---

## 10. Related Artifacts (This Session)

| File | Description |
|:---|:---|
| [`completeness-over-score-essay.md`](file:///<repo-root>/PROJECTS/hummbl-governance/docs/research/2026-08-23_completeness-over-score-essay.md) | Essay: architecture of honest AI governance |
| [`inversion-of-vanity-essay.md`](file:///<repo-root>/PROJECTS/hummbl-governance/docs/research/2026-08-23_inversion-of-vanity-essay.md) | Essay: epistemology of humility in AI engineering |
| [`batch2-compliance-gaps.md`](file:///<repo-root>/PROJECTS/hummbl-governance/batch2-compliance-gaps.md) | 11-item compliance audit + gaps report |
| [`governance_question.schema.json`](file:///<repo-root>/PROJECTS/hummbl-governance/schemas/governance_question.schema.json) | JSON Schema for open governance questions |
| [`capability_manifest.schema.json`](file:///<repo-root>/PROJECTS/hummbl-governance/schemas/capability_manifest.schema.json) | JSON Schema for capability manifests |
| [`essay-peer-review.md`](file:///<repo-root>/.gemini/antigravity-cli/brain/1372b0f4-d179-44ef-8671-99fc161fca6d/essay-peer-review.md) | Peer review of both essays with P1/P2/P3 corrections |

---

## 11. Key Constraints for Any Agent Working on This

1. **Do not push to main** — all changes via PR branches only.
2. **Do not deploy to production** without explicit human `go` command.
3. **Do not modify Cloudflare DNS** without explicit human approval.
4. **operator.com source is at** `<repo-root>/PROJECTS\hummbl-production\operator\` — deploy via `wrangler pages deploy`.
5. **hummbl-governance is the essay source of truth** — all essays live in `docs/research/`.
6. **Zero third-party runtime dependencies** in any Python code written for this project.
7. **Conventional Commits** format for all commits. Branch naming: `type/agent/short-desc`.
8. **No AI agent attribution in git commits** (no Co-authored-by, Generated-by, etc.).
