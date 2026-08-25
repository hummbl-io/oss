# Public Content Hub — Design Specification
**Domains:** hummbl.io · operator.com  
**Adjacent:** hummbl-dev.com (staging) · kernelclothing.com  
**Status:** Design Draft — 2026-08-23

---

## Domain Architecture

```
┌─────────────────────────────┬──────────────────────────────────────────┐
│ Domain                      │ Purpose                                  │
├─────────────────────────────┼──────────────────────────────────────────┤
│ hummbl.io                   │ Product + Docs + Content (HUMMBL brand)  │
│ hummbl-dev.com              │ Staging / dev preview                    │
│ operator.com            │ Personal brand + Writing + Speaking      │
│ kernelclothing.com          │ Separate product (scoped separately)     │
└─────────────────────────────┴──────────────────────────────────────────┘
```

---

## The Three-Zone Model

Both sites share the same structural philosophy with different brand voices:

```
┌──────────────────┬──────────────────────────┬──────────────────────────┐
│  ZONE 1          │  ZONE 2                  │  ZONE 3                  │
│  Click Funnel    │  Documentation / OSS     │  Content Hub             │
│  (Convert)       │  (Build Trust / Depth)   │  (Grow Audience)         │
├──────────────────┼──────────────────────────┼──────────────────────────┤
│  Who: Buyers,    │  Who: Developers,        │  Who: Everyone —         │
│  executives,     │  compliance officers,    │  builders, founders,     │
│  partners        │  auditors, researchers   │  students, regulators    │
│                  │                          │                          │
│  Goal: Book      │  Goal: Self-serve        │  Goal: Follow, share,    │
│  demo / purchase │  to value in minutes     │  subscribe, engage       │
└──────────────────┴──────────────────────────┴──────────────────────────┘
```

---

## hummbl.io — Page Structure

### Navigation
```
HUMMBL    [Product]  [Docs ▾]  [Content ▾]  [OSS]    [Start Free →]
```

---

### Hero (Zone 1 Entry Point — above fold)
- **Headline:** `AI Governance Infrastructure.`
- **Subline:** `Control what agents can do. Prove what they actually did.`
- **CTA Primary:** `Start Free` → /signup
- **CTA Secondary:** `Read the Docs` → /docs
- **Social proof bar:** PyPI downloads · GitHub stars · frameworks covered

---

### Zone 1 — For Your Business (`/product`, `/pricing`, `/demo`)

| Page | Purpose |
|:---|:---|
| `/product` | Narrative pitch — the vanity score problem, the HUMMBL solution |
| `/pricing` | Tiers: OSS Community · Pro · Enterprise |
| `/demo` | Calendly embed or interactive playground |
| `/case-studies` | Enterprise use cases (redacted or consented) |
| `/enterprise` | SOC 2, data residency, dedicated infra, SLAs |
| `/compliance` | Regulatory readiness page (EU AI Act, NIST, ISO 42001) — link to coverage matrix |

---

### Zone 2 — Documentation (`/docs`)

Powered by **Mintlify** (existing `mintlify-docs` repo).

```
/docs
├── Getting Started
│   ├── Install (pip install hummbl-governance)
│   ├── Quickstart — your first governance tuple
│   └── Core Concepts (Contract, DCT, Evidence)
│
├── Governance Primitives
│   ├── Kill Switch
│   ├── Circuit Breaker
│   ├── Cost Governor
│   ├── Capability Fence
│   ├── Delegation Token (DCT)
│   ├── Audit Log
│   └── Identity Registry
│
├── Kernel Reference (K1–K11 Invariants)
│
├── Compliance Coverage
│   ├── Coverage Matrix (99 frameworks)
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
│   ├── hummbl-tuples
│   └── Full OSS index → hummbl-io/oss
│
└── API Reference (auto-generated)
```

---

### Zone 3 — Content Hub (`/content`)

#### Essays & Long-Form
| Title | Status |
|:---|:---|
| Completeness Over Score | ✅ Published |
| The Inversion of Vanity | ✅ Published |
| *(next)* The Three Axioms of Humility as Engineering Constraints | Draft |

#### Research
- AI governance field mapping archive (2026-08-23)
- Base120 operator lattice overview
- Domain120 legitimization strategy
- OSS competitive landscape

#### Social Content (every platform)

| Platform | Content Type | Cadence |
|:---|:---|:---|
| X / Twitter | Threads, hot takes, governance insights | 3–5x/week |
| LinkedIn | Long-form posts, career/founder narrative | 2–3x/week |
| Substack | Full essays + research digests | Weekly |
| YouTube | Explainers, walkthroughs, demos | Bi-weekly |
| Podcast | Conversations (founder, researcher, regulator guests) | Monthly |
| GitHub | OSS releases, READMEs, changelogs | Continuous |

---

## operator.com — Page Structure

### Navigation
```
Operator    [Work]  [Writing]  [Speaking]  [Contact]
```

---

### Hero (Personal Brand)
- **Headline:** `Founder. Builder. Governance Architect.`
- **Subline:** `Building the infrastructure that keeps AI accountable to humans.`
- **CTA:** `Let's Talk` → /contact (Cal.com embed)

---

### Zone 1 — Hire Me / Work With Me (`/work`)

| Offering | Description |
|:---|:---|
| Fractional AI Governance Lead | Embedded governance function for AI-building orgs |
| Speaking | Keynotes on AI governance, agent safety, founder+builder |
| Advisory | Board / SAB roles for AI-native startups |
| Workshops | Half/full day: "Build AI Agents That Don't Break Trust" |

---

### Zone 2 — Writing & Research (`/writing`)

Chronological feed of:
- Essays from `hummbl-governance/docs/research/`
- Research notes and AARs
- Cross-posted from Substack / hummbl.io/content

Displayed as: **editorial card grid** — title, date, reading time, topic tag.

---

### Zone 3 — Social & Content (`/content`)

Aggregated feed across all platforms:
- Latest X threads
- LinkedIn posts
- YouTube videos
- Podcast episodes

With platform-icon badges and direct links out.

---

## Cross-Site Linking Strategy

```
operator.com  ──────→  hummbl.io/docs   (technical credibility)
operator.com  ──────→  hummbl.io/product (commercial path)
hummbl.io/content ──────→  operator.com/writing (authorship)
hummbl.io OSS     ──────→  github.com/hummbl-io/oss (source of truth)
```

---

## Intelligence Summary — 5 Open Questions Resolved
*All findings from parallel subagent investigation, 2026-08-23*

---

### Q1: Does `/pricing` exist? ✅ No — net-new work required

**Finding:** Zero pricing infrastructure exists anywhere — no page, tiers, price points, or Stripe config. `hummbl.io/pricing` returns HTTP 302 → homepage. Only commercial touchpoint is `cal.com/hummbl/30min`. HUMMBL is currently 100% open-source Apache 2.0.

**Suggested tier skeleton for owner to ratify:**

| Tier | Target | Price |
|:---|:---|:---|
| **Community** | Developers, researchers | Free — OSS forever |
| **Pro** | Teams building AI products | $X/mo — priority support, SLA |
| **Enterprise** | Regulated industries | Custom — data residency, audit exports |

---

### Q2: Is Mintlify wired to hummbl.io? ✅ No — completely unwired

**Finding:** `mintlify-docs` is an empty skeleton with no `mint.json`, no MDX, no CI publishing. `docs.hummbl.io` has **zero DNS records**. `hummbl.io` → `hummbl-production.pages.dev` (Cloudflare Pages).

The canonical docs target referenced in README is `hummbl-dev/docs` on GitHub — a repo not present locally.

**Full hummbl.io DNS map (key records):**

| Subdomain | Target |
|:---|:---|
| `hummbl.io` / `www` | `hummbl-production.pages.dev` |
| `dashboard.hummbl.io` | `hummbl-dashboard.pages.dev` |
| `hermes.hummbl.io` | Cloudflare Argo Tunnel |
| `api` / `agents` / `mcp` / `mcp-public` | Worker route placeholders |

**To go live with docs:** (1) create `mint.json`, (2) connect Mintlify cloud, (3) add `docs.hummbl.io CNAME → mintlify servers` in Cloudflare.

---

### Q3: What CMS / publishing pipeline exists? ✅ None — git-native markdown only

**Finding:** No CMS, no MDX, no SSG, no Substack/Ghost/Sanity config anywhere. Today's pipeline:
- **53 `.md` files** in `hummbl-governance/docs/research/` (flat, date-stamped)
- No YAML frontmatter schema — raw prose only
- No automated publishing step — essays committed to git and stay there

**Recommendation:** Add lightweight frontmatter (title, date, tags, status) to existing `.md` files and use Astro or Next.js MDX reading from `hummbl-governance/docs/research/` — no external CMS needed.

---

### Q4: Where does operator.com point? ✅ Cloudflare Pages — live, HTTP 200

**Finding:** `operator.com` → `operator-site.pages.dev`. Local source at:

```
<repo-root>/PROJECTS\hummbl-production\operator\
├── wrangler.toml   (name = "operator-site", pages_build_output_dir = "./site")
└── site/           (static output, editable now)
```

`chat.` and `contact.` subdomains are null AAAA placeholders — ready to wire. Deploys via `wrangler pages deploy`. **No new infra needed.**

---

### Q5: Is kernelclothing.com in scope? ✅ Out of scope — owner decision needed

**Finding:** Zero DNS records. Never hosted content. Never indexed. No local project. Likely parked for brand protection.

> [!IMPORTANT]
> **Owner decision required for kernelclothing.com:**
> - **Option A:** Redirect → `hummbl.io` (recommended — prevents dark domain)
> - **Option B:** Activate as a future clothing/merch brand (needs separate spec)
> - **Option C:** Keep parked (current state, do nothing)

**Excluded from this content hub scope until decided.**

---

## Revised Next Steps — Prioritized

| Priority | Action | Effort | Status |
|:---|:---|:---|:---|
| **P0** | Define pricing tiers (owner ratification) | 1hr | ⚠️ Owner decision |
| **P0** | Add frontmatter schema to `docs/research/*.md` | 2hr | ✅ Ready to start |
| **P1** | Redesign `operator.com` — edit `hummbl-production/operator/site/` | 1–2 days | ✅ Ready to start |
| **P1** | Add `docs.hummbl.io` CNAME in Cloudflare + create `mint.json` | 4hr | ✅ Ready to start |
| **P2** | Build `hummbl.io` content hub additions (pricing zone, content zone) | 2–3 days | 🔒 Blocked on P0 pricing |
| **P3** | kernelclothing.com — redirect or activate | 30min | ⚠️ Owner decision |

> [!NOTE]
> Both mockup images are ready. Visual direction confirmed: dark/electric for hummbl.io, warm/editorial for operator.com. The operator.com redesign can begin immediately — source is local.
