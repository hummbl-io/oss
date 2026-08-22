# HUMMBL Fleet Inventory — 2026-06-22

**Standard:** HUMMBL Repo Standard v0.1
**Audit date:** 2026-06-22
**Auditor:** devin (automated)
**Total repos inventoried:** 91 GitHub + 6 Gitea-only + 24 local-only + 10 non-git directories

## Purpose

This document is the canonical inventory of every HUMMBL repository, local
directory, and dependency across all surfaces. It is the source of truth for
fleet planning, dependency management, and initialization.

---

## Surface 1: Private GitHub + Gitea (mirrored)

Private repos mirrored to the self-hosted Gitea instance at
the internal `HUMMBL` Gitea organization. Gitea is the canonical host for CI;
GitHub is the mirror.

### Active, private, with Gitea mirror

| Repo | GitHub | Gitea | Description | Lang | Runtime Deps |
|------|--------|-------|-------------|------|--------------|
| `hummbl-governance` | `hummbl-io/hummbl-governance` | `HUMMBL/hummbl-governance` | Governed multi-agent AI OS, 138 modules, 14k+ tests | Python | stdlib-only; test: pytest, pytest-cov, pytest-asyncio, numpy, jsonschema |
| `hummbl-governance` | `hummbl-io/hummbl-governance` | `HUMMBL/hummbl-governance` | PyPI v1.2.2, 34 governance primitives, 7 MCP servers | Python | stdlib-only; test: pytest, pytest-cov, build, ruff |
| `hummbl-production` | `hummbl-io/hummbl-production` | `reuben/hummbl-production` | Cloudflare Workers/Pages stack for hummbl.io | TS/JS | hono, wrangler, vitest; dashboard: next 15, react 18, recharts, tailwind |
| `arbiter` | `hummbl-io/arbiter` | `HUMMBL/arbiter` | Agent-aware code quality scoring A-F | Python | stdlib-only |
| `fleet-standard` | `hummbl-io/fleet-standard` | `HUMMBL/fleet-standard` | Fleet standard definitions | - | - |
| `_between` | (not on GitHub) | `HUMMBL/_between` | Fleet-standard migration staging | - | - |

### Active, private, GitHub-only (no Gitea mirror found)

| Repo | Description | Lang | Deps |
|------|-------------|------|------|
| `agent-tools` | Canonical CLI tools for the agent fleet | - | - |
| `apex-nexus` | Pre-action analysis and dispatch | - | - |
| `arcana` | Multi-lens governance/political-philosophy analysis pipeline | Python | stdlib-only |
| `autoresearch-pipeline` | GPU research agent framework | Python | stdlib-only |
| `baseN` | Base-N tier multi-variant operator catalog | - | - |
| `claude-config` | Claude Code profile config (machine-side) | - | - |
| `coaching` | Open-source coaching methodology (NSCA All-American) | - | - |
| `corpus` | - | - | - |
| `crab` | CRAB methodology: Check, Reason, Act, Bus | - | - |
| `fractional-bench` | 16-arc Haiku Hardening methodology | - | - |
| `general-claim-validator` | - | - | - |
| `huaomp` | 6-lens analytical framework | - | - |
| `hummbl` | Structured reasoning framework for AI agents | - | - |
| `hummbl-brainstorm` | Brainstorming and working-material | - | - |
| `hummbl-brand` | Brand assets | - | - |
| `hummbl-cca-f` | Certified Claude Architect -- Foundation cert | - | - |
| `hummbl-dev` | Org profile repo | - | - |
| `hummbl-doctrine` | Internal R&D operator framework | - | - |
| `hummbl-gameboard` | Canonical integration surface for fleet governance | - | - |
| `hummbl-graphs` | - | - | - |
| `hummbl-iac` | IaC -- chezmoi dotfiles, package manifests, network topology | - | - |
| `hummbl-kernel-factory` | Meta-kernel factory for domain-specific agentic kernels | - | - |
| `hummbl-medical` | Medical research and experimental tooling | Python | test: pytest, pytest-cov, bandit, semgrep |
| `hummbl-models` | Canonical registries, schemas, graphs for mental model library | - | - |
| `hummbl-music` | - | - | - |
| `hummbl-research` | Research repo | Python | stdlib-only |
| `hummbl-skills` | Canonical skill definitions, CI-validated SKILL.md | - | - |
| `hummbl-spacetime` | Prompt composition for spacetime mental models | Python | stdlib-only |
| `hummbl-system-prompts` | - | - | - |
| `hummbl-theory` | Theoretical foundations -- Base120, HCC, BKI | - | - |
| `hummbl-transparency` | AI Transparency Registry -- vendor prompt auditing | - | - |
| `hummbl-tuples` | Governed IDP tuples for reasoning mesh | Python | stdlib-only |
| `idp-spec` | Intelligent Delegation Profile spec | - | - |
| `job-search-2026` | Job search tracker for Reuben | - | - |
| `krineia` | Krineia research and reasoning workspace | - | - |
| `meeting-archive` | Meeting transcripts (Dan & Reuben syncs) | - | - |
| `mtsmu` | - | - | - |
| `psychedelic-claim-validator` | - | - | - |
| `swarm-test` | Multi-machine swarm dispatch testing | Python | stdlib-only |

### Archived, private

| Repo | Description |
|------|-------------|
| `hummbl-asi` | HUMMBL Artificial Super Intelligence Framework |
| `hummbl-assurance` | EAL merged into hummbl-governance (PR #12) |

---

## Surface 2: Public GitHub (maximally promotable)

These are the repos visible to the world. They are the promotable surface --
PyPI packages, open-source frameworks, showcase demos, papers.

### Active, public

| Repo | Description | Lang | Promotable angle |
|------|-------------|------|------------------|
| `hummbl-governance` | v1.2.2 on PyPI, 34 primitives, 7 MCP servers, zero deps | Python | **Flagship** -- `pip install hummbl-governance` |
| `base120` | v2.0.0, deterministic governance substrate for system design | Python | Cognitive framework reference impl |
| `hummbl-agent` | TypeScript agent orchestration runtime -- kernel, router, adapters | TypeScript | Multi-agent coordination with Base120 |
| `hummbl-bibliography` | Provenance corpus, BibTeX citations, position papers | JSON/MD | Research credibility |
| `hummbl-dev` | Org profile repo | MD | Org landing page |
| `hummbl-papers` | Governance infrastructure papers and reproducibility artifacts | MD/TeX | Academic positioning |
| `hummbl-toolkit` | Supplementary tooling -- evidence-gate, batch ingestion, showcase | Python | Utility belt |
| `mcp-server` | HUMMBL MCP Server | - | MCP ecosystem entry point |
| `arbiter` | Agent-aware code quality scoring A-F | Python | Dev tooling |
| `coaching` | Open-source coaching methodology, CC BY 4.0 | - | Personal brand |
| `hummbl` | (public-facing placeholder) | - | - |
| `.github` | Org profile and templates | MD | Org defaults |

### Archived, public (reference material)

| Repo | Description |
|------|-------------|
| `agent-governance-demo` | Runtime safety primitives demo -- kill switch, circuit breaker, 58 tests |
| `adversary-emulation-playbook` | MITRE ATT&CK adversary emulation with HUMMBL governance audit trails |
| `autoresearch-reports` | Collected outputs from autoresearch pipeline runs |
| `bif` | Batch Ingestion Framework -- systematic technical knowledge acquisition |
| `evidence-gate` | Pre-publish source-verification rule library |
| `hummbl-governance-showcase` | Demo the HUMMBL governance mesh in 5 minutes -- zero config |
| `governed-compression` | Governed vector and KV-cache compression research |
| `HUMMBL-Unified-Tier-Framework` | Problem complexity classification, 5 tiers, Base-N architecture |
| `autoresearch-win-rtx` | Windows RTX autoresearch experiments |

### Archived, public forks (boundary layer)

`CL4R1T4S`, `G0DM0D3`, `L1B3RT4S`, `NATURALIS-FUTURA`, `OBLITERATUS`,
`Real-Time-Voice-Cloning`, `ST3GG`, `V3SP3R`, `autoresearch`,
`awesome-ai-agents`, `awesome-ai-agents-1`, `awesome-ai-agents-2026`,
`awesome-python`, `cli`, `deer-flow`, `hermes-agent`, `markitdown`,
`open_teamsuzie`, `paramiko`, `rich`, `sint-protocol`, `skills`

---

## Surface 3: Gitea-Only Repos (not on GitHub)

| Repo | Gitea path | Description |
|------|-----------|-------------|
| `_between` | `HUMMBL/_between` | Fleet-standard migration staging |
| `hummbl-jepa` | `HUMMBL/hummbl-jepa` | JEPA reference mirror |
| `hummbl-live` | `HUMMBL/hummbl-live` | Live runtime |
| `hummbl-media` | `HUMMBL/hummbl-media` | Media assets |
| `hummbl-randy` | `HUMMBL/hummbl-randy` | - |
| `hummbl-telemetry` | `HUMMBL/hummbl-telemetry` | Telemetry |

---

## Surface 4: Local Git Repos (no remote)

### In `~/PROJECTS/` with `.git` but no remote

| Repo | Py | TS | MD | Description |
|------|----|----|-----|-------------|
| `arcana-platform` | 6 | 18 | 4 | ARCANA web platform (Next.js + MDX) |
| `arcana` | 1 | 0 | 2 | ARCANA core (stub) |
| `bioinformatics-grid-experiment` | - | - | - | Bioinformatics experiment |
| `coaching-private` | - | - | - | Private coaching content |
| `governance-bench` | 165 | 1 | 73 | Governance benchmarking suite (large) |
| `hummbl-agent-sdk` | 1 | 0 | 1 | Agent SDK stub |
| `hummbl-alerts` | 1 | 0 | 1 | Alerts module stub |
| `hummbl-audit` | 1 | 0 | 1 | Audit module stub |
| `hummbl-autonomy` | 1 | 0 | 1 | Autonomy module stub |
| `hummbl-bus` | 9 | 0 | 1 | Bus subsystem (extracted from hummbl-governance) |
| `hummbl-cli` | 1 | 0 | 1 | CLI stub |
| `hummbl-cognition` | 8 | 0 | 1 | Cognition subsystem (extracted) |
| `hummbl-dashboard` | 14 | 0 | 1 | Dashboard backend (FastAPI) |
| `hummbl-eval` | 1 | 0 | 1 | Eval stub |
| `hummbl-foundry` | 2 | 0 | 1 | Foundry stub |
| `hummbl-py` | 1 | 0 | 1 | Python package stub |
| `hummbl-quality` | 8 | 0 | 1 | Quality module |
| `hummbl-scheduler` | 2 | 0 | 1 | Scheduler (extracted) |
| `hummbl-scripts` | 5 | 0 | 1 | Scripts collection |
| `hummbl-security-auditor` | 16 | 0 | 3 | Security auditor (16 py files) |
| `hummbl-security` | 10 | 0 | 1 | Security module |
| `hummbl-testing` | 1 | 0 | 1 | Testing infrastructure stub |
| `hummbl-wiki` | 16 | 0 | 7 | Wiki with 16 Python files |
| `platform` | 98 | 0 | 202 | Platform docs (202 MD files, 98 Python) |
| `trellis` | 0 | 0 | 2 | Trellis (markdown only) |

---

## Surface 5: Local Non-Git Directories

### In `~/PROJECTS/` (no `.git`)

| Directory | Files | Py | TS | MD | Description |
|-----------|-------|----|----|-----|-------------|
| `_archived` | 3,913 | 2,203 | 369 | 221 | Large archive of old code (2.2k Python files) |
| `agent-archive` | 3 | 0 | 0 | 3 | Agent archive notes |
| `arbiter-wt-compliance` | 118 | 85 | 0 | 10 | Arbiter compliance worktree |
| `arbiter-wt-lboard` | 126 | 93 | 0 | 10 | Arbiter leaderboard worktree |
| `carl` | 4 | 0 | 0 | 4 | Carl (markdown notes) |
| `devin-wiki` | 17 | 3 | 0 | 14 | Devin wiki research |
| `governance-bench-space` | 7 | 1 | 0 | 1 | Governance bench workspace |
| `hummbl-brand` | 33 | 1 | 0 | 5 | Brand assets (non-git) |
| `hummbl-intel-atlas` | 320 | 24 | 0 | 101 | Intel atlas (101 MD files, 24 Python) |
| `hummbl-wiki-research` | 33 | 0 | 0 | 33 | Wiki research (33 MD files) |

### In `~/` (home directory, outside PROJECTS)

| Directory | Git? | Files | Py | MD | Description |
|-----------|------|-------|----|----|-------------|
| `~/hummbl_governance` | No | 343 | 82 | 90 | Untracked cruft (path drift artifact) |
| `~/hummbl-governance` | No | 5,752 | 1,545 | 2,273 | Large untracked copy of hummbl-governance |
| `~/hummbl-governance-prsplit` | Yes (Gitea) | 4,865 | 1,546 | 2,472 | PR-split worktree (Gitea remote) |
| `~/founder-archetype-generator` | No | 1,052 | 24 | 1,027 | Archetype generator (1k MD files) |
| `~/hummbl` | No | 1,217 | 67 | 1,382 | HUMMBL content (1.4k MD files, no git) |
| `~/hummbl-langchain` | No | 19 | 10 | 2 | LangChain experiment (10 Python files) |
| `~/hummbl-papers` | Yes | 17 | 0 | 9 | Papers clone |
| `~/hummbl-research` | Yes | 428 | 26 | 339 | Research clone |
| `~/hummbl-brand-design-system-kit-*` | No | - | - | - | Brand kit archives (unzipped + .zip) |

---

## Surface 6: Gitignored Content (within tracked repos)

Inside `hummbl-governance` (the main repo), the `.gitignore` deny-by-default
policy hides significant local-only content:

| Path | Type | Description |
|------|------|-------------|
| `_state/` | Gitignored | Operational state -- coordination bus, governance logs |
| `hummbl-governance/_state/` | Gitignored | Nested operational state |
| `hummbl-governance/bus/` | Gitignored | Bus subsystem (runtime module, NOT just state) |
| `.pytest_cache/` | Gitignored | Test cache |
| `__pycache__/` | Gitignored | Python bytecode cache |
| `_internal/` | Gitignored | Internal mirror (memory-tier-b, local-mirror) |
| `.claude/` | Tracked | Skills, rules, hooks, agents, tempos |
| `.devin/` | Tracked | Devin CLI config |
| `.agents/` | Tracked | Agent fleet config |

---

## Complete Dependency Inventory

### Python runtime dependencies (production code)

| Dependency | Used by | Justification | Stdlib alternative? |
|------------|---------|---------------|---------------------|
| *(none)* | hummbl-governance, base120, arbiter, hummbl-tuples, hummbl-spacetime, hummbl-research, hummbl-agent (kernel/control-plane) | Zero runtime deps is a constitutional invariant | N/A -- stdlib only |

### Python test/dev dependencies

| Dependency | Version | Used by | Purpose |
|------------|---------|---------|---------|
| `pytest` | >=7.0 / >=9.1 | hummbl-governance, hummbl-governance, hummbl-medical, base120, arbiter | Test runner |
| `pytest-cov` | >=4.0 | hummbl-governance, hummbl-governance, hummbl-medical | Coverage measurement |
| `pytest-asyncio` | >=1.4 | hummbl-governance | Async test support |
| `build` | >=1.0 | hummbl-governance | PyPI package build |
| `ruff` | >=0.4 | hummbl-governance | Linter/formatter |
| `bandit` | >=1.7 | hummbl-medical, hummbl-governance (CI) | Security scanner |
| `semgrep` | >=1.0 | hummbl-medical, hummbl-governance (CI) | Security scanner |
| `numpy` | >=2.4.6 | hummbl-governance (test) | Numerical test fixtures |
| `jsonschema` | >=4.26.0 | hummbl-governance (test) | Schema validation in tests |

### Python dashboard/API dependencies (hummbl-governance dashboard)

| Dependency | Version | Purpose | Stdlib alternative? |
|------------|---------|---------|---------------------|
| `fastapi` | >=0.109.0 | Dashboard API framework | No -- ASGI framework needs this |
| `uvicorn[standard]` | >=0.27.0 | ASGI server | No -- server runtime |
| `pydantic` | >=2.5.0 | Data validation for API models | Could use dataclasses but loses auto-validation |
| `python-multipart` | >=0.0.6 | Form parsing | No -- stdlib has no multipart parser |
| `httpx` | >=0.26.0 | HTTP client for API-to-service calls | Could use urllib but loses async + connection pooling |

### TypeScript/JavaScript dependencies

#### hummbl-production (Cloudflare Workers API)

| Dependency | Version | Purpose |
|------------|---------|---------|
| `hono` | ^4.12.18 | Web framework for Workers (devDep) |
| `wrangler` | ^4.90.0 | Cloudflare Workers CLI (devDep) |
| `vitest` | ^4.1.2 | Test runner (devDep) |
| `@vitest/coverage-v8` | ^4.1.5 | Coverage (devDep) |
| `@vitest/ui` | ^4.1.2 | Test UI (devDep) |
| `@cloudflare/workers-types` | ^4.20260510.1 | Workers type defs (devDep) |
| `typescript-eslint` | ^8.59.2 | Linting (devDep) |
| `eslint` | ^10.0.0 | Linter (devDep) |
| `jsdom` | ^29.1.1 | DOM testing (devDep) |
| `prettier` | ^3.8.2 | Formatter (devDep) |

#### hummbl-production (dashboard frontend)

| Dependency | Version | Purpose |
|------------|---------|---------|
| `next` | 15.5.18 | React framework |
| `react` | ^18 | UI library |
| `react-dom` | ^18 | React DOM renderer |
| `@tanstack/react-query` | ^5.99.0 | Server state management |
| `recharts` | ^3.8.1 | Charting library |
| `lucide-react` | ^1.8.0 | Icon set |
| `clsx` | ^2.1.1 | Class name utility |
| `tailwind-merge` | ^3.5.0 | Tailwind class dedup |
| `next-themes` | ^0.4.6 | Theme switching |
| `tailwindcss` | ^3.4.1 | CSS framework (devDep) |
| `typescript` | ^5 | Type system (devDep) |
| `eslint` + `eslint-config-next` | ^8 / 15.5.18 | Linting (devDep) |

#### hummbl-agent (TypeScript runtime)

| Dependency | Version | Purpose |
|------------|---------|---------|
| `yaml` | ^2.9.0 | YAML parsing (governance package) |
| `ajv` | ^8.20.0 | JSON Schema validation (devDep) |
| `ajv-cli` | ^5.0.0 | CLI schema validation (devDep) |
| `fast-glob` | ^3.3.2 | File globbing (devDep) |
| `markdownlint-cli2` | ^0.22.1 | Markdown linting (devDep) |
| `tsx` | ^4.22.4 | TypeScript execution (devDep) |
| `typescript` | ^5 | Type system (devDep) |
| `vite` | - | Build tool (governance package devDep) |
| `vitest` | - | Test runner (governance package devDep) |

#### arcana-platform (web frontend)

| Dependency | Version | Purpose |
|------------|---------|---------|
| `next` | 16 | React framework |
| `react` / `react-dom` | ^18 | UI library |
| `gray-matter` | ^4.0.3 | Frontmatter parsing |
| `@next/mdx` | ^14 | MDX integration |
| `@mdx-js/loader` | ^3 | MDX webpack loader |
| `@mdx-js/react` | ^3 | MDX React components |
| `tailwindcss` | ^3 | CSS framework (devDep) |
| `@tailwindcss/typography` | ^0.5 | Typography plugin (devDep) |

### Infrastructure dependencies

| Dependency | Where | Purpose |
|------------|-------|---------|
| Cloudflare Workers | hummbl-production | Edge compute platform |
| Cloudflare Pages | hummbl-production | Static site hosting for hummbl.io |
| Cloudflare D1 | hummbl-production | SQLite-at-edge database |
| Cloudflare KV | hummbl-production | Key-value store |
| Gitea | self-hosted on <machine> | Canonical git host + CI runner |
| `tea` CLI | local | Gitea API client (token expired) |
| `gh` CLI | local | GitHub API client |
| Ollama | <machine> (dormant since 2026-07-13) | Local LLM inference — offline, rejoin pending re-onboarding |
| OpenClaw | <machine> (dormant since 2026-07-13) | Agent gateway — offline with host |

---

## Non-stdlib exceptions (with reasons)

| Dependency | Reason we'd need it | When it's justified |
|------------|---------------------|---------------------|
| `fastapi` + `uvicorn` | ASGI web framework -- no stdlib equivalent for async HTTP server with routing | Dashboard API only (hummbl-governance dashboard). Never in governance core. |
| `pydantic` | Auto-validation of API models -- stdlib dataclasses lack runtime validation | Dashboard API only. Could be replaced with manual validation if needed. |
| `httpx` | Async HTTP client -- stdlib urllib lacks async + connection pooling | Dashboard API only. Could use urllib.request in sync mode. |
| `hono` | Cloudflare Workers web framework -- Workers runtime has no stdlib HTTP router | Workers API only. Could use raw `fetch` handler but loses routing/middleware. |
| `next` + `react` | SPA framework -- no stdlib equivalent | Frontend only. Always devDep, never in governance core. |
| `yaml` | YAML parsing -- stdlib has no YAML parser | hummbl-agent governance package only. Could use JSON instead. |
| `ajv` | JSON Schema validation in TS -- no stdlib equivalent in JS runtime | hummbl-agent devDep only. Python side uses stdlib schema_validator. |
| `numpy` | Numerical computation -- stdlib math is insufficient for matrix ops | Test fixtures only in hummbl-governance. Never in governance core. |
| `jsonschema` | Full JSON Schema validation -- stdlib has only a subset implementation | Test fixtures only. hummbl-governance ships its own stdlib `schema_validator`. |

**Principle:** Runtime code stays stdlib-only. Third-party deps are confined to:
1. Dashboard/API surfaces (FastAPI, Next.js)
2. Cloudflare Workers (Hono, Wrangler)
3. Test/dev extras (pytest, ruff, bandit)
4. TypeScript tooling (TypeScript, Vite, Vitest)
