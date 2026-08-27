# Technical Research Report: Public Surface Architecture & Content Distribution
**Subject:** Discovery of Local Repositories, Historical Page Decommissions, and Multi-Platform Distribution Infrastructure  
**Date:** 2026-08-23  
**Status:** Complete Research Archive  
**Target Repositories:** [`hummbl-production`](https://github.com/hummbl-io/hummbl-production), [`hummbl-governance`](https://github.com/hummbl-io/oss/tree/main/packages/python/hummbl-governance), [`oss`](https://github.com/hummbl-io/oss)  

---

## 1. Local Codebase Discovery & Source Mapping

Our deep inspection of the local filesystem resolved the exact source code locations for both live production web surfaces:

```
<repo-root>/PROJECTS\hummbl-production\
├── wrangler.toml                    --> CF Pages Project: "hummbl-production" (hummbl.io)
│                                        Deploy Directory: ./web
├── web\                             --> Static source for hummbl.io
│   ├── index.html                   --> 16.7KB single-page landing surface
│   ├── _redirects                   --> 60 active 302 rules (contains historical page registry)
│   ├── _headers                     --> Security headers (CSP, HSTS, X-Frame-Options)
│   ├── llms.txt / llms-full.txt     --> LLM crawler context specs
│   └── shared.css / landing.css     --> Dark-theme stylesheet system
│
└── operator\
    ├── wrangler.toml                --> CF Pages Project: "operator-site" (operator.com)
    │                                    Deploy Directory: ./site
    └── site\                        --> Static source for operator.com
        ├── index.html               --> 9.6KB personal landing page
        ├── about.html, capability.html, methods.html, operationalizations.html, primitives.html
        └── landing.css / shared.css --> Clean, warm-theme stylesheet system
```

---

## 2. Forensic Discovery: The 2026-08-11 Decommissioning

In `hummbl-production/web/_redirects`, we uncovered a crucial architectural event: on **2026-08-11**, the previous multi-page version of `hummbl.io` was collapsed into the current single landing page. 

**47 specific sub-pages were 302-redirected to `/`:**
- **Commercial & Consulting:** `/pricing`, `/consulting`, `/services`, `/case-studies`, `/solutions/*`
- **Technical & Docs:** `/docs`, `/docs/*`, `/architecture`, `/primitives/*`, `/explorer`, `/playground`, `/validation`
- **Compliance Framework Checklists:** `/eu-ai-act-readiness`, `/iso-42001-readiness`, `/iso27001`, `/nist-ai-rmf-checklist`, `/nist-csf`, `/gdpr`, `/soc2`, `/owasp`, `/ai-compliance-standards`
- **Content & Updates:** `/blog`, `/newsletter`, `/research`, `/ship-log`, `/changelog`

### Key Takeaway for the Redesign:
The original site had sprawling sub-pages that became hard to maintain. The new **Three-Zone Model** (Funnel vs. Mintlify Docs vs. Content Hub) does not require resurrecting 47 bespoke HTML files; instead:
1. **Zone 1 (Funnel)**: Reclaims `/product`, `/pricing`, `/demo`, `/enterprise`.
2. **Zone 2 (Docs)**: Offloads the 99 compliance frameworks, primitives, and API references to **Mintlify (`docs.hummbl.io`)**.
3. **Zone 3 (Content)**: Houses essays and social aggregations systematically under `/content`.

---

## 3. Social Media & Multi-Platform Distribution Architecture

In `hummbl-production/_internal/content-distribution/` and `_internal/substack/`, we discovered an existing, highly structured 3-tier distribution hierarchy and API feasibility audit:

```
┌────────────────────────────────────────────────────────┐
│               CONTENT DISTRIBUTION CASCADE             │
├────────────────────────────────────────────────────────┤
│ 1. PRIMARY: Git / Ship Log                             │
│    • Daily append-only JSON + HTML log                 │
│    • Source of truth for all technical milestones      │
├────────────────────────────────────────────────────────┤
│ 2. SECONDARY: Substack / Long-form Essays              │
│    • 800–1,200 word deep dives (Weekly)                │
│    • 53 research essays in docs/research/ as raw feed  │
├────────────────────────────────────────────────────────┤
│ 3. TERTIARY DERIVATIVES (Every Category):              │
│    • X/Twitter: 8–15 post threads (Hook + CTA)         │
│    • LinkedIn: 150–300 word professional takeaways     │
│    • Hacker News: "Show HN" technical problem-first    │
│    • Reddit: r/MachineLearning, r/LocalLLaMA, r/webdev │
│    • Dev.to / Hashnode: Cross-posted technical guides  │
│    • Python Newsletters: PyCoders, Python Weekly       │
│    • Audio/Podcasts: 5–10 min spoken summaries         │
│    • YouTube: 3–5 min terminal/code demo screen-casts  │
└────────────────────────────────────────────────────────┘
```

### Verified API Feasibility Audit (14 Platforms)

| Platform | Official API? | Auth Type | Automated Write Feasibility | Recommended Tooling |
|:---|:---:|:---:|:---:|:---|
| **GitHub** | Yes | Fine-grained PAT | ✅ Production Ready | `octokit`, `gh` CLI |
| **Substack** | No (Undocumented) | Session Cookie | 🟡 Unofficial CLI / MCP | `@postcli/substack` |
| **X / Twitter** | Yes (v2) | OAuth 2.0 / Bearer | ✅ Production Ready | `@zen_tools/x-sdk` |
| **LinkedIn** | Yes | OAuth 2.0 | ✅ Production Ready | Official REST API |
| **Reddit** | Yes | OAuth 2.0 | ✅ Production Ready | `praw` (Python) |
| **Dev.to** | Yes | API Key | ✅ Production Ready | `devto-cli` |
| **Hashnode** | Yes | GraphQL + PAT | ✅ Production Ready | `hashnode-mcp` |
| **Hacker News** | Read-Only | None | ❌ Manual Only | Firebase / Algolia |
| **YouTube** | Yes | OAuth 2.0 | ✅ Production Ready | Google APIs Client |
| **Discord** | Yes | Bot Token | ✅ Production Ready | `discord.js` |
| **Slack** | Yes | Webhooks / Bot | ✅ Production Ready | `@slack/web-api` |
| **Ghost** | Yes | Admin API Key | ✅ Production Ready | `@tryghost/admin-api` |

---

## 4. Synthesis for the Fleet

1. **No New Server Infrastructure Needed:** Both `hummbl.io` and `operator.com` build static HTML/CSS files hosted directly on **Cloudflare Pages** from `<repo-root>/PROJECTS\hummbl-production\`.
2. **Docs Strategy Validated:** Moving documentation and the 99-framework compliance catalog to `docs.hummbl.io` (Mintlify) avoids bloating the core static landing page while restoring the 47 decommissioned knowledge pages in a clean, maintainable structure.
3. **Content Pipeline Alignment:** The 53 essays in `hummbl-governance/docs/research/` serve as the single source of truth feeding the Substack and social distribution waterfall.
