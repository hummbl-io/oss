# Agentic Engineering Directory Taxonomy v0.1

**Date:** 2026-08-10
**Author:** Devin (root agent, GLM-5.2 High)
**Status:** SYNTHESIS — pending arcana peer review
**Evidence base:** 13 sub-agent reports (6 internal recon, 7 external research) + 9 root-agent web searches + git archaeology across 8 local repos
**Confidence:** HIGH for internal/fleet evidence (S1 primary source); MEDIUM for external industry evidence (mix of S1 docs and S2 secondary); VERIFIED for 4 key academic papers (MemGPT, Generative Agents, Memory Survey, CoALA — all confirmed real via webfetch 2026-08-10); S3 for remaining ledger arxiv URLs (unverified)

---

## Executive Summary

The field of "agentic engineering" is an emerging paradigm — not yet a formalized discipline — characterized by the transition from single-turn code generation ("vibe coding") to multi-step, environment-interacting agents that plan, execute, verify, and self-correct. No industry-wide standard exists for agent-native repository structure. However, strong convergence is visible across three independent evidence streams: (1) vendor conventions (Claude Code, Cursor, Codex, Devin, Windsurf), (2) the HUMMBL fleet's production implementation, and (3) academic literature on agent memory, evaluation, and coordination.

This synthesis identifies **seven fundamental directory structures** for agentic engineering, classifies them by maturity (universal / converging / emerging / experimental), and proposes a minimum viable agentic-engineering repository layout.

---

## Part 1: Evidence Inventory and Source Classification

### Source Tiers
- **S1 (Primary):** Official vendor documentation, live local installations, git-tracked artifacts
- **S2 (Secondary):** Community guides, blog posts, framework docs cited indirectly
- **S3 (Tertiary):** Academic papers cited in research ledger (URLs not independently verified this session)

### Evidence Streams

| Stream | Source | Tier | What it provides |
|--------|--------|------|------------------|
| Vendor docs | Claude Code docs (code.claude.com), Cursor docs (cursor.com), MCP spec (modelcontextprotocol.io), Aider docs (aider.chat) | S1 | Official directory conventions for each agent tool |
| Fleet internal recon | 6 sub-agents analyzing 8 local repos via filesystem + git | S1 | Production implementation of agent-native structures |
| Git archaeology | Root agent, `git log --diff-filter=A` across 8 repos | S1 | Adoption timeline for each structure |
| External research | 7 GLM-5.2 sub-agents (knowledge synthesis, no web tools) | S2-S3 | Framework comparisons, academic context |
| Root web research | 9 web searches (Claude, Cursor, MCP, MemGPT, Aider, SWE-bench, handoffs, ADRs, best practices) | S1-S2 | Industry convergence signals |
| Intel-surge ledger | Pre-existing research corpus (365+ entries, 7,177 sources) | S3 | Academic paper citations (unverified URLs) |

### Dropped/Low-Confidence Evidence
- **All arxiv URLs from the intel-surge ledger** are marked S3 (unverified). They are cited as "ledger claims" not as verified sources.
- **GLM sub-agent training-knowledge claims** about AutoGen, CrewAI, LangGraph directory structures are explicitly flagged as unverified.
- **SSH-based recon of 3 missing repos** failed — SSH access was unavailable. These repos are absent from the evidence base.

---

## Part 2: The Seven Fundamental Directory Structures

### Structure 1: Root Instruction File (`AGENTS.md` / `CLAUDE.md`)

**Maturity: UNIVERSAL** — present in every agent tool examined, adopted fleet-wide 2026-06-22.

**Evidence:**
- Claude Code: `CLAUDE.md` at repo root or `.claude/CLAUDE.md`, auto-loaded every session, <200 lines recommended [S1: code.claude.com/docs/en/claude-md]
- Codex/OpenAI: `AGENTS.md` at repo root, can nest at subdirectory levels [S1: local installations]
- Cursor: `.cursorrules` (deprecated) → `.cursor/rules/*.mdc` [S1: cursor.com/docs/rules]
- Aider: `.aider.conf.yml` + `CONVENTIONS.md` [S1: aider.chat/docs/config]
- HUMMBL fleet: `AGENTS.md` present in 8/8 local repos, first committed 2026-06-22 across 5 repos [S1: git archaeology]
- Industry convergence: harness.io, claudelab.net, taim.io, reopt.ai all describe AGENTS.md as "the new standard" [S2]

**Canonical structure:**
- Single markdown file at repo root
- Contains: build commands, test commands, coding conventions, directory boundaries, prohibited patterns, permission boundaries
- Loaded automatically into agent context at session start
- <200 lines (Claude Code recommendation); longer files reduce adherence

**Divergence:** Claude Code reads `CLAUDE.md` but NOT `AGENTS.md` (the official pattern is `CLAUDE.md` containing `@AGENTS.md`). Codex reads `AGENTS.md` directly. The industry has NOT converged on a single filename.

**Verdict: FUNDAMENTAL.** Every agent tool has a root instruction file. The filename varies but the pattern is universal.

---

### Structure 2: Agent Configuration Directory (`.devin/` / `.claude/` / `.cursor/` / `.codex/`)

**Maturity: UNIVERSAL** — every vendor has their own dotfile directory.

**Evidence:**
- Claude Code: `.claude/` with `rules/`, `skills/`, `agents/`, `hooks/`, `settings.json`, `commands/` [S1: code.claude.com/docs/en/claude-directory]
- Cursor: `.cursor/` with `rules/` (.mdc files), `mcp.json` [S1: cursor.com/docs/rules]
- Devin: `.devin/` with `agents/`, `skills/`, `config.json`, `mcp_config.local.json` [S1: local installation]
- Codex: `.codex/` with `config.toml`, `worktrees/`, `.sandbox/` [S1: local installation]
- Windsurf: `.windsurf/` with `rules/` (.md files, mirrors Cursor) [S1: local installation]
- HUMMBL fleet: `.devin/` present in multiple fleet repos; `.codex/` + `.opencode/` in fleet repos [S1: git archaeology]

**Canonical structure (vendor-specific, no convergence):**
```
.<vendor>/
├── config.{json,toml,yml}     # Permissions, MCP servers, hooks
├── agents/                    # Subagent profiles (Devin, Claude)
├── skills/                    # Skill definitions (Devin, Claude, Codex)
├── rules/                     # Rule files (Cursor, Claude, Windsurf)
└── hooks/                     # Git/session hooks (Claude)
```

**The junction model:** The HUMMBL fleet uses `.agents/` as a canonical shared root, with vendor-specific directories (`.claude/`, `.devin/`, `.codex/`) as junctions/projections into it. This is a fleet-specific pattern, not an industry standard. [S1: internal review]

**Divergence:** No standard internal structure. Each vendor invented their own. Config formats differ (JSON, TOML, YAML). The only cross-vendor interop mechanism found is Devin's `read_config_from` field. [S1: local .devin/config.json]

**Verdict: FUNDAMENTAL (the directory), EXPERIMENTAL (the junction model).** Every agent tool has a config directory. The HUMMBL junction model for multi-runtime support is a novel contribution not seen elsewhere.

---

### Structure 3: Skills Directory (`skills/<name>/SKILL.md`)

**Maturity: CONVERGING** — present in Claude Code, Devin, Codex, Windsurf, CodeBuddy; the HUMMBL fleet has 1,000 skills.

**Evidence:**
- Claude Code: `.claude/skills/<name>/SKILL.md` with frontmatter (name, description, version) [S1: code.claude.com/docs/en/claude-directory]
- Devin: `.devin/skills/<name>/SKILL.md` with frontmatter (name, description, version, execution-mode, argument-hint) [S1: local installation]
- Codex: `.codex/skills/<name>/SKILL.md` [S1: local installation]
- HUMMBL fleet: `skills/` with 1,000 skills in hummbl-skills, 658 in hummbl-governance, 188 in hummbl-agent [S1: sub-agent recon]
- skills.sh ecosystem: `npx skills` marketplace [S2: sub-agent report]
- Anthropic Managed Agents API: Skills as first-class API objects (`skills-2025-10-02` beta) [S2: sub-agent report]

**Canonical skill internal structure:**
```
<skill-name>/
├── SKILL.md              # REQUIRED: YAML frontmatter + markdown procedure
├── references/           # OPTIONAL: retrieval augmentation docs
├── eval/                 # OPTIONAL: behavioral test suite (see Structure 4)
│   ├── corpus/           # Ground truth test cases (JSON)
│   ├── scorer.py         # Stdlib-only scoring engine
│   ├── run_eval.py       # Eval runner
│   └── results/          # Generated outputs (gitignored)
├── scripts/              # OPTIONAL: executable code
├── templates/            # OPTIONAL: code templates
└── assets/               # OPTIONAL: icons, fonts
```

**Standard frontmatter fields (cross-vendor convergence):**
| Field | Claude | Devin | Cursor | HUMMBL |
|-------|--------|-------|--------|--------|
| `name` | ✓ | ✓ | ✓ | ✓ |
| `description` | ✓ | ✓ | ✓ | ✓ |
| `version` | ✓ | ✓ | — | ✓ |
| `execution-mode` | — | ✓ | — | ✓ |
| `argument-hint` | — | ✓ | — | ✓ |
| `triggers` | — | — | — | ✓ |
| `alwaysApply` | — | — | ✓ | — |
| `globs` | — | — | ✓ | — |
| `contracts` | — | — | — | ✓ (HUMMBL-specific) |

**Key insight from sub-agent SWE-C:** "SKILL.md is a behavioral contract, not code documentation. Traditional SE: README.md explains how code works. Agentic: SKILL.md specifies how an AGENT should behave." [S1: sub-agent report]

**Verdict: FUNDAMENTAL for production agent systems.** The skills/ directory with SKILL.md is the dominant pattern for agent capability extension. The minimum viable skill is just SKILL.md; production-grade skills add eval/ for behavioral verification.

---

### Structure 4: Co-located Eval Suite (`<skill>/eval/`)

**Maturity: EMERGING** — present in HUMMBL fleet (11 eval-tested skills), Anthropic's skill-creator pattern; NOT present in most vendor defaults.

**Evidence:**
- HUMMBL fleet: 11 skills with eval suites (claim-verify, hallucination-check, evidence-grade, proof-check, doc-harden, backup-verify, case-study-verify, coverage, complexity-score, secret-scan, regression-check) [S1: sub-agent recon]
- Anthropic skill-creator: `evals/evals.json` with prompts + assertions, with-skill vs. baseline runs [S2: sub-agent report]
- SWE-bench: External benchmark, NOT co-located — different evaluation philosophy [S1: web search]
- OpenAI Evals: `evals/<name>/` directory, Python framework [S2: sub-agent report]

**Canonical eval structure (HUMMBL fleet, most mature implementation found):**
```
<skill>/eval/
├── corpus/               # Ground truth test cases (JSON, min 8)
│   ├── case_001_*.json
│   └── case_NNN_*.json
├── scorer.py             # Stdlib-only, defines PROMOTION_GATES
├── run_eval.py           # Eval runner (generate/score modes)
├── run_eval.sh           # CLI entry point
├── report.py             # Markdown report with confusion matrix
├── README.md             # Eval suite documentation
├── results/              # Generated outputs (gitignored)
└── baselines/            # Regression baselines
```

**Promotion gate pattern (HUMMBL-specific, novel contribution):**
```python
PROMOTION_GATES = {
    "verdict_accuracy": {"threshold": 0.90, "direction": "gte", "hard": False},
    "false_support_rate": {"threshold": 0.05, "direction": "lte", "hard": True},
    "schema_validity": {"threshold": 1.00, "direction": "gte", "hard": True},
}
```
HARD gates block promotion on any failure. SOFT gates contribute to overall score. [S1: sub-agent recon, claim-verify/eval/scorer.py]

**Skill lifecycle:** candidate (0.2.0-0.3.0) → tested (1.0.0, eval passing) → stable (1.x.y, cross-agent regression) → canonical (2.0.0, fleet-wide standard) [S1: rules/SKILL_VERSIONING.md]

**Key distinction:** Co-located evals (in-skill, behavioral unit testing) vs. external benchmarks (SWE-bench, AgentBench, GAIA — integration testing for agent systems). Both are needed; they serve different purposes. [S1: sub-agent report]

**Verdict: EMERGING FUNDAMENTAL.** Co-located eval suites are the most mature quality-assurance pattern for agentic skills. Not yet universal, but the convergence between HUMMBL's corpus+scorer pattern and Anthropic's evals.json pattern suggests this is becoming standard for production agent systems.

---

### Structure 5: Decision Records (`docs/adr/`)

**Maturity: CONVERGING** — traditional SE practice now being automated by AI agents.

**Evidence:**
- HUMMBL fleet: `docs/adr/` present in 5/8 repos, 9 ADRs in hummbl-governance, 1 each in base120/arbiter/hummbl-skills/hummbl-governance [S1: git archaeology]
- Industry: Multiple AI-agent-native ADR tools emerging (arch-decision, adr-kit, auto-adr, decider) [S1: web search]
- arch-decision: Claude Code plugin, 8-phase ADR lifecycle, writes to `docs/decisions/` [S1: github.com/jsingh6/arch-decision]
- adr-kit: "Architecture decisions your AI coding agents actually follow" — enforces ADRs as guardrails [S1: github.com/rvdbreemen/adr-kit]
- auto-adr: Claude Code skill, auto-generates ADRs from session conversations [S1: github.com/tanRdev/auto-adr]
- decider: Git-native ADRs with YAML frontmatter, CI-enforceable constraints [S1: github.com/sventorben/decider]

**Canonical ADR format (HUMMBL fleet):**
```markdown
# ADR-XXX: Title

**Status:** accepted | proposed | superseded
**Date:** YYYY-MM-DD
**Decision owner:** ...
**Steward:** ...
**Supersedes:** ADR-YYY (if applicable)

## Context
## Decision
## Consequences
## Receipts (HUMMBL-specific)
```

**Industry convergence signal:** Multiple independent tools (arch-decision, adr-kit, auto-adr, decider) all converge on `docs/decisions/` or `docs/adr/` with agent-authored ADRs. The pattern of "AI agent writes ADR → human approves → ADR becomes enforceable constraint" is emerging as a distinct agentic-engineering pattern. [S1: web search]

**HUMMBL-specific extension:** ADRs are linked to KRINEIA receipt chains — each governance decision generates a receipt proving the ADR was adopted. This is not seen in industry tools. [S1: sub-agent recon]

**Verdict: FUNDAMENTAL (the directory), EMERGING (agent-authored ADRs).** ADRs are a traditional SE practice now being automated by agents. The directory `docs/adr/` or `docs/decisions/` is converging. Agent-authored ADRs with enforcement are an emerging agentic-engineering pattern.

---

### Structure 6: Session Handoff Directory (`docs/handoffs/`)

**Maturity: EMERGING** — multiple independent tools converging on the same pattern.

**Evidence:**
- HUMMBL fleet: `docs/handoffs/` present in 5/8 repos [S1: git archaeology]
- Industry tools (all discovered via web search):
  - `agent-handoff` (wecansync): `.ai/` directory with `PROJECT.md`, `PATHS.md`, `PLAN.md`, `conversations/HANDOFF.md`, `conversations/LOG.md` [S1: github.com/wecansync/agent-skills]
  - `handoff` (rosehgal): `~/.handoff/{dir}-handoff.md` + append-only JSONL event log [S1: github.com/rosehgal/handoff]
  - `agent-handoff` (cellear): `HANDOFF/` directory with session journals [S1: github.com/cellear/agent-handoff]
  - `ctx handover`: `.context/handovers/` with timestamped files [S1: ctx.ist/cli/handover]
  - SAM Documentation: Timestamped handoff directory with `CONTINUATION_PROMPT.md`, `AGENT_PLAN.md`, `NOTES.md` [S2: syntheticautonomicmind.org]
  - Compound Engineering: `/tmp/compound-engineering/ce-handoff/` [S2: github.com/EveryInc/compound-engineering-plugin]

**Canonical handoff format (HUMMBL fleet):**
```markdown
# Handoff: [session description]

## Purpose
## What Was Done
## What's Left
## Key Files Touched
## Gotchas & Context
## Test Status
## Entry Points
```

**Industry convergence signal:** At least 6 independent tools implement session handoff for AI agents. All converge on: (1) markdown format, (2) structured sections (what was done / what's next / context), (3) timestamped or append-only, (4) designed for cross-session or cross-agent continuity. The directory name varies (`.ai/`, `.context/handovers/`, `HANDOFF/`, `~/.handoff/`, `docs/handoffs/`) but the pattern is consistent. [S1-S2: web search]

**Verdict: EMERGING FUNDAMENTAL.** Session handoff is a distinct agentic-engineering need (agents lose context between sessions). Multiple independent implementations confirm this is a real pattern, not HUMMBL-specific. The directory location is not yet standardized.

---

### Structure 7: Agent State / Memory Directory (`_state/`)

**Maturity: EXPERIMENTAL** — no industry convergence; HUMMBL fleet has the most mature implementation found.

**Evidence:**
- HUMMBL fleet: `_state/` intentionally gitignored in all repos (runtime state, not committed) [S1: git archaeology]
- HUMMBL `_state/` architecture (from sub-agent GLM-E, the most detailed report):
  ```
  _state/
  ├── coordination/
  │   └── messages.tsv          # Append-only TSV bus
  ├── cognition/
  │   ├── ledger.jsonl           # Append-only cognitive ledger
  │   ├── state.json             # Current state (last-writer-wins)
  │   ├── intent.md              # Current intent
  │   └── index.json             # BM25 inverted index
  ├── memory/
  │   └── <agent>.design.md      # Per-agent memory design docs
  ├── dreams/                    # Divergent synthesis captures
  ├── snapshots/                 # Tarball backups
  ├── swarm-reports/             # Subagent fan-out results
  └── governance/
      └── reports/               # AAR files
  ```
- Industry frameworks (from sub-agent GLM-E, training knowledge — S3):
  - MemGPT/Letta: SQLite + vector DB, `~/.letta/`, 3-tier (core/archival/recall)
  - LangGraph: Checkpointers (MemorySaver, SqliteSaver, PostgresSaver), no fixed directory
  - AutoGen: `FileBasedStateStore`, JSON files, no standard directory
  - CrewAI: SQLite + ChromaDB, `~/.crewai/`, 3-tier (short/long/entity)
  - Cloudflare Agents: SQLite (D1/Durable Objects), server-managed

**Key design principles from HUMMBL implementation:**
1. **Append-only vs. last-writer-wins distinction** — `ledger.jsonl` and `messages.tsv` are append-only (sort-union merge for sync); `state.json` and `intent.md` are last-writer-wins (overwrite OK)
2. **Cross-machine sync** — rsync for non-append files, sort-union merge for append-only files
3. **Snapshot/rollback** — tarball backups with restore verification
4. **Content scanning before persistence** — prompt injection, credential leakage, exfiltration vector scanning
5. **4-tier memory hierarchy** — short-term (context window), episodic (ledger.jsonl), semantic (index.json/BM25), long-term (snapshots)

**Sub-agent GLM-E verdict:** "A `_state/` directory with JSONL files is superior for single-machine, multi-agent coordination (auditability, sync, human-readiness, git-diffability). Framework DB approaches are superior for semantic retrieval at scale. The local fleet infra already bridges this by adding a BM25 index on top of the JSONL ledger." [S2: sub-agent report]

**Industry convergence:** NONE. Each framework invents its own approach. The closest to a convention is "put a SQLite file somewhere and optionally a vector DB." The HUMMBL `_state/` convention is more architecturally complete than any single framework's default. [S2-S3: sub-agent report]

**Verdict: EXPERIMENTAL but ARCHITECTURALLY SIGNIFICANT.** No industry convergence. The HUMMBL `_state/` pattern (append-only JSONL + mutable JSON + BM25 index + tarball snapshots) is a novel contribution that deserves documentation as a potential standard. The minimum viable persistence is 2 files: an append-only event log (JSONL) + a mutable state snapshot (JSON).

---

## Part 3: HUMMBL-Specific Structures (Not Fundamental, But Noteworthy)

These structures are present in the HUMMBL fleet but have no industry equivalent. They are HUMMBL-specific governance innovations:

| Structure | Purpose | Industry equivalent | Verdict |
|-----------|---------|---------------------|---------|
| `KRINEIA.md` | Receipt manifest (SHA-256 chained provenance) | NONE found | HUMMBL-specific. The principle (immutable provenance chain) is sound, but the implementation is fleet-specific. |
| `CONSTITUTION.md` | Binding repo law with protected invariants | NONE found | HUMMBL-specific. Similar in spirit to governance frameworks but more prescriptive. |
| `hummbl.repo.yaml` | Machine-readable repo manifest | `server.json` (MCP registry), `package.json` (npm) | Partial industry equivalent. The MCP registry's `server.json` is a similar pattern for MCP servers specifically. |
| `_receipts/krineia/*.jsonl` | Append-only hash-chained receipt log | NONE found in agent tools; similar to blockchain/audit log patterns | HUMMBL-specific. The SHA-256 chained receipt structure is a sound pattern for proving state transitions. |
| `DOCTRINE.md` | Interpretive framework | NONE found | HUMMBL-specific. |
| `CODEOWNERS` | Review authority per path | GitHub native (not agentic) | Inherited from traditional SE, not agentic-specific. |
| `.agents/` (shared root) | Canonical governance root with junctions | NONE found | HUMMBL-specific. The junction model for multi-runtime support is a novel contribution. |

**Key finding from sub-agent SWE-B:** "The specific implementation (KRINEIA, HUMMBL Repo Standard, the exact artifact stack, the operator set, the authority structure) is HUMMBL-specific. However, the underlying principles — separating identity/authority/execution, using receipt chains for provenance, maintaining decision records, documenting handoffs — could be fundamental patterns for agentic engineering that other frameworks might implement differently." [S1: sub-agent report]

---

## Part 4: Adoption Timeline (Git Archaeology)

From git log analysis across 8 local repos:

| Date | Event | Significance |
|------|-------|--------------|
| 2026-01-26 | `_state/` first appears in hummbl-agent | Earliest agentic structure adoption |
| 2026-01-30 | `AGENTS.md` first appears in hummbl-agent | Root instruction file adoption |
| 2026-05-14 | `docs/adr/` first appears in hummbl-governance | ADR infrastructure (pre-standard) |
| 2026-06-15 | `.devin/`, `.codex/`, `.opencode/` appear in fleet repos | Multi-runtime config directories |
| **2026-06-22** | **HUMMBL Repo Standard v0.1 fleet-wide rollout** | **Coordinated adoption of AGENTS.md + KRINEIA.md + CONSTITUTION.md + hummbl.repo.yaml + _receipts/ + docs/adr/ + docs/handoffs/ across 5 repos** |
| 2026-06-25 | `DOCTRINE.md` added across fleet | Interpretive framework layer |
| 2026-07-23 | hummbl-governance adopts full governance stack | Latest fleet member onboarded |
| 2026-08-06 | Fleet repo adopts governance stack | Most recent adoption |

**Presence matrix (8 repos × 14 structures):**

| Structure | Present in N/8 repos | First commit |
|-----------|---------------------|--------------|
| AGENTS.md | 8/8 (100%) | 2026-01-30 |
| KRINEIA.md | 7/8 (87.5%) | 2026-06-22 |
| CONSTITUTION.md | 7/8 (87.5%) | 2026-06-22 |
| hummbl.repo.yaml | 7/8 (87.5%) | 2026-06-22 |
| DOCTRINE.md | 7/8 (87.5%) | 2026-06-25 |
| _receipts/ | 6/8 (75%) | 2026-06-22 |
| docs/adr/ | 5/8 (62.5%) | 2026-05-14 |
| docs/handoffs/ | 5/8 (62.5%) | 2026-06-22 |
| _state/ | 2/8 (25%, gitignored) | 2026-01-26 |
| .devin/ | 2/8 (25%) | 2026-06-15 |
| .agents/ | 1/8 (12.5%) | 2026-07-23 |
| .claude/ | 1/8 (12.5%) | 2026-07-23 |
| .codex/ | 1/8 (12.5%) | 2026-06-15 |
| .opencode/ | 1/8 (12.5%) | 2026-06-15 |

---

## Part 5: Minimum Viable Agentic-Engineering Repository

Based on the evidence, the minimum viable agentic-engineering repository layout is:

```
project-root/
├── AGENTS.md                      # REQUIRED: Root instruction file
├── .<vendor>/                     # REQUIRED: Agent config directory
│   ├── config.{json,toml,yml}     # Permissions, MCP, hooks
│   ├── skills/                    # Skill definitions
│   │   └── <name>/
│   │       ├── SKILL.md           # Behavioral contract (frontmatter + procedure)
│   │       └── eval/              # OPTIONAL: Behavioral test suite
│   │           ├── corpus/        # Ground truth cases
│   │           ├── scorer.py      # Promotion gates
│   │           └── run_eval.py
│   └── agents/                    # OPTIONAL: Subagent profiles
├── docs/
│   ├── adr/                       # RECOMMENDED: Architecture Decision Records
│   └── handoffs/                  # RECOMMENDED: Session handoff documents
└── _state/                        # OPTIONAL: Runtime state (gitignored)
    ├── ledger.jsonl               # Append-only event log
    └── state.json                 # Mutable current state
```

**Tier 1 (Universal — required for any agent-assisted repo):**
- `AGENTS.md` (or `CLAUDE.md` for Claude Code)
- `.<vendor>/` config directory

**Tier 2 (Converging — required for production agent systems):**
- `skills/<name>/SKILL.md` directory
- `docs/adr/` for decision records
- `docs/handoffs/` for session continuity

**Tier 3 (Emerging — required for safety-critical agent systems):**
- `<skill>/eval/` co-located eval suites with promotion gates
- `_state/` runtime state directory (gitignored)

**Tier 4 (Experimental — HUMMBL-specific, not yet industry-standard):**
- `KRINEIA.md` + `_receipts/` receipt chain
- `CONSTITUTION.md` with protected invariants
- `hummbl.repo.yaml` machine-readable manifest
- `.agents/` shared governance root with junctions

---

## Part 6: Novelty Stress-Test

### What is genuinely novel in the HUMMBL fleet vs. what is inherited?

| Pattern | Origin | Novel? |
|---------|--------|--------|
| AGENTS.md root instruction | Industry (Codex/OpenAI) | No — industry convergence |
| .devin/ config directory | Vendor-specific (Devin) | No — every vendor has one |
| skills/ with SKILL.md | Industry (Claude, Codex, Devin) | No — converging pattern |
| eval/ co-located with skills | HUMMBL extension of Anthropic pattern | PARTIALLY — the corpus+scorer+promotion-gate pattern is more mature than Anthropic's evals.json |
| docs/adr/ | Traditional SE (Nygard 2011) | No — inherited, but agent-authored ADRs are emerging |
| docs/handoffs/ | Industry (6+ independent tools) | No — converging pattern |
| _state/ with JSONL+JSON | HUMMBL-specific | YES — no industry equivalent found |
| KRINEIA receipt chain | HUMMBL-specific | YES — no industry equivalent found |
| CONSTITUTION.md | HUMMBL-specific | YES — no industry equivalent found |
| .agents/ junction model | HUMMBL-specific | YES — no industry equivalent found |
| Skill promotion gates (hard/soft) | HUMMBL-specific | YES — not found in Anthropic, OpenAI, or any other framework |
| Cognitive architecture as directory structure | HUMMBL-specific | YES — organizing doctrine files around cognitive layers is novel |

### What should be documented as a potential standard?

1. **The `_state/` pattern** (append-only JSONL + mutable JSON + BM25 index + tarball snapshots) — more architecturally complete than any framework's default memory approach. Should be documented as a spec.

2. **The eval suite promotion gate pattern** (corpus + scorer.py + PROMOTION_GATES with hard/soft thresholds) — extends Anthropic's skill-creator pattern with formal quality gates. Should be proposed as an extension to the skill-creator standard.

3. **The junction model** (`.agents/` canonical root with vendor-specific projections) — solves the multi-runtime fragmentation problem. Should be documented as a reference architecture for multi-agent fleets.

4. **The KRINEIA receipt chain** — sound provenance pattern for agent governance. The principle (immutable, hash-chained receipts for state transitions) is fundamental; the specific implementation is HUMMBL-specific.

---

## Part 7: Open Questions for Arcana Peer Review

1. **Is "agentic engineering" a real discipline or a marketing term?** The academic literature (S3, unverified) uses it, but no IEEE/ACM standard exists. The ARCANA lens should assess whether this is a genuine paradigm shift or hype.

2. **Should the `_state/` pattern be proposed as a standard?** It's more mature than any framework's default, but it's a single implementation. The Ostrom lens (polycentric governance) might assess whether this should be a standard or a reference architecture.

3. **Are promotion gates necessary for all skills or only safety-critical ones?** The HUMMBL fleet requires evals only for skills that make factual claims. The Russell lens (alignment) might assess whether this threshold is correct.

4. **Is the junction model scalable beyond a single operator?** The HUMMBL fleet is a single-operator setup. The Ashby lens (requisite variety) might assess whether the junction model can handle organizational-scale multi-agent fleets.

5. **Does the KRINEIA receipt chain add value over git history alone?** Git already provides immutable history. The Schneier lens (security mindset) might assess whether the receipt chain is security theater or substantive.

---

## Appendix A: Evidence Source Inventory

### Internal Recon (S1, primary source)
- SWE-A: hummbl-governance + hummbl-agent structure analysis
- SWE-B: hummbl-governance + base120 + arbiter governance analysis
- SWE-C: hummbl-skills repo (1,000 skills, eval infrastructure)
- SWE-D: fleet repos + user-level .agents/.devin
- SWE-E: git archaeology presence matrix
- SWE-F: fleet skill health, drift, eval infrastructure

### External Research (S2-S3)
- GLM-A: agent-native repo conventions (local evidence)
- GLM-B: MCP ecosystem + multi-agent orchestration
- GLM-C: cross-lane gap-fill from intel-surge ledger
- GLM-D: eval frameworks + skill management
- GLM-E: memory architectures (MemGPT, LangGraph, etc.)
- GLM-F: SSH-attempted (failed — no SSH access)
- GLM-G: SSH-attempted (failed — no SSH access)

### Root Agent Web Research (S1-S2)
- Claude Code CLAUDE.md / .claude directory (code.claude.com)
- Cursor .cursorrules / .cursor/rules (cursor.com)
- MCP server structure (modelcontextprotocol.io, deepwiki.com)
- MemGPT/Letta memory architecture (docs.letta.com, arxiv.org)
- Agentic engineering best practices (claudelab.net, harness.io, aiarch.dev)
- Aider conventions (aider.chat)
- SWE-bench / AgentBench eval structure (github.com/SWE-bench)
- AI agent handoff tools (github.com — 6 independent tools found)
- ADR automation tools (github.com — 4 independent tools found)

### Git Archaeology (S1)
- 8 repos × 14 structures, first-commit dates extracted via `git log --diff-filter=A`

---

## Appendix B: Sub-Agent Tool Limitations

**Critical disclosure:** The `devin-researcher` profile (GLM-5.2) does NOT have `web_search` or `webfetch` tools in this runtime — only filesystem tools (`find_file_by_name`, `grep`, `read`, `notebook_read`). This was discovered mid-sweep and compensated by:
1. Root agent executing all web research directly (9 web searches)
2. GLM sub-agents providing knowledge-grounded syntheses from training data (clearly flagged as S3)
3. GLM sub-agents analyzing the local intel-surge ledger (pre-existing research corpus with 7,177 sources)

The `subagent_explore` profile (SWE-1.6) has filesystem tools only (no exec, no SSH) — this was the known constraint. The `devin-swe-recon` profile (SWE-1.7) failed to launch entirely (invalid model ID).

**Impact on evidence quality:** Internal recon (S1) is unaffected — all based on local filesystem analysis. External research is a mix of root-agent web searches (S1-S2) and sub-agent training-knowledge syntheses (S3). Academic paper URLs from the intel-surge ledger are unverified.

---

## Next Steps

1. **Arcana peer review** — route this synthesis through 2-3 ARCANA lenses (recommended: ostrom for polycentric governance, ashby for requisite variety, schneier for security assessment of KRINEIA)
2. **Verify academic URLs** — the intel-surge ledger's arxiv citations need independent verification via webfetch
3. **Document the `_state/` pattern as a spec** — this is the most novel contribution and deserves formal documentation
4. **Document the eval promotion gate pattern** — propose as extension to Anthropic's skill-creator standard
5. **Document the junction model** — propose as reference architecture for multi-agent fleets
6. **Research the 3 missing repos** when SSH access is restored
