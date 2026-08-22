---
expires_for_review: 2026-11-16
last_reviewed: 2026-08-18
---

# Proposal: Consolidate Repo Proliferation (164 repos)

**Status:** DECIDED — operator ratified 2026-08-18: Option B (Conservative archive)
**Date:** 2026-08-18
**Author:** Devin (action #13)
**Steward:** HUMMBL Research Institute

## Decision (operator-ratified 2026-08-18)

**Option B (Conservative archive)** — archive stale/duplicate repos only. Move 13 no-.git dirs to _archive/, merge bibliography variants, pick canonical homebrew/founder-mode/hummbl-dev variants. ~4h, low risk.

## 1. Problem Statement

The PROJECTS directory has 164 repos. This creates:

1. **Cognitive overhead** — finding the right repo requires memorizing a 164-entry map
2. **Drift** — related code lives in separate repos (e.g., `hummbl-bibliography` + 5 numbered variants) with no sync mechanism
3. **Empty/stale repos** — 13 directories have no `.git`, 3 have no remote (local-only experiments)
4. **Naming inconsistency** — `hummbl-homebrew` vs `homebrew-hummbl` vs `homebrew-tap` (3 repos for the same purpose)
5. **Split-brain variants** — `hummbl-dev` vs `hummbl-dev-rewrite` vs `hummbl-dev-pub` vs `hummbl-dev-hummbl-dev`
6. **CI overhead** — each repo with a workflow consumes runner time independently

## 2. Current State

### By prefix

| Category | Count | Notes |
|----------|-------|-------|
| `hummbl-*` | 63 | The core fleet; includes 6 bibliography variants, 4 production variants, 4 dev variants |
| `hd-*` | 4 | HUMMBL Education / AI adoption |
| `agent-*` | 7 | Agent patterns, tools, runtime |
| `governance/policy/compliance` | 13 | Governance docs and code |
| `*-as-code` | 11 | "As-code" pattern repos |
| `research/benchmark` | 8 | Research and benchmarking |
| `bibliography` | 6 | Numbered bibliography snapshots |
| `homebrew/scoop/winget` | 5 | Package manager manifests |
| `production` | 4 | Production deployment variants |
| Other | 43 | Misc projects, tools, personal |

### Git status

| Status | Count | Examples |
|--------|-------|----------|
| Has remote | 148 | Standard repos with GitHub/Gitea remotes |
| No remote | 3 | `founder-mode-clean-cherry`, `hummbl-learning`, `research-worktree` |
| No `.git` | 13 | `founder-mode`, `hummbl-brand-assets`, `hummbl-tuples`, `on-device-llm-benchmark`, `org-consolidation-backups`, `ownward-temp-push`, `resilient-comms-lab`, `session-artifacts`, `stealthops-slate-commercial`, `study-companion`, `transcripts`, `zai-model-benchmark` |

### Obvious duplicate/variant clusters

| Cluster | Repos | Consolidation action |
|---------|-------|---------------------|
| Bibliography | `hummbl-bibliography`, `-89`, `-96`, `-97`, `-118`, `-119` | Merge into one `hummbl-bibliography` with tagged releases; archive numbered variants |
| Homebrew | `hummbl-homebrew`, `homebrew-hummbl`, `homebrew-tap` | Pick one (likely `homebrew-tap`); archive the other two |
| hummbl-dev | `hummbl-dev`, `hummbl-dev-rewrite`, `hummbl-dev-pub`, `hummbl-dev-hummbl-dev`, `hummbl-dev-workflow-remediation`, `hummbl-dev-org-dot-github` | Determine which is canonical; archive the rest |
| Production | `hummbl-production`, `-codex-landing`, `-codex-main-gates`, `-codex-postdeploy-evidence` | Merge into `hummbl-production` with subdirectories or branches |
| founder-mode | `founder-mode`, `founder-mode-repo`, `founder-mode-clean-cherry` | Pick one; archive the rest |
| apex-nexus | `apex-nexus`, `apex-nexus-profiles-codex`, `apex-nexus-retirement-index` | Merge profiles and retirement-index into apex-nexus |

## 3. Options

### Option A: Monorepo consolidation (aggressive)

**Approach**: Merge related repos into a small number of monorepos organized by domain.

Proposed monorepos:
- `hummbl-governance` (absorb `governance-as-code`, `compliance-as-code`, `policy-as-code`, `governance-docs`, `governance-tuple-reference`, `governed-compression`, `governed-counterpart`, `governed-agents-agent-governance-demo`, `execution-receipts`)
- `hummbl-fleet` (absorb `agent-tools`, `agent-as-code`, `agent-evaluation-patterns`, `agent-instruction-format`, `agent-runtime-governance`, `agents`, `apex-nexus` + variants, `fleet-standard`, `fleet-repo`)
- `hummbl-research` (absorb `hummbl-bibliography` + variants, `hummbl-papers`, `research-and-development`, `corpus`, `autoresearch-pipeline`, benchmark repos)
- `hummbl-infra` (absorb `infrastructure-as-code`, `observability-as-code`, `security-as-code`, `hummbl-docker`, `ollama-mon`, `workspace-mcp`)
- `hummbl-edu` (absorb `hd-*` repos, `coaching`, `coaching-private`, `study-companion`, `hummbl-learning`)

**Pros**: Minimal repo count (~20-30), shared CI, easier cross-repo refactoring
**Cons**: Large migration effort, loses independent versioning, mixed CI signals, large clone size

**Effort**: High. 3-5 days of careful migration + testing.

### Option B: Archive stale/duplicate repos only (conservative)

**Approach**: Don't merge active repos. Only archive:
1. The 13 no-`.git` directories (move to `_archive/`)
2. The 3 no-remote repos (evaluate if they're experiments; archive or push)
3. The 6 numbered bibliography variants (merge into `hummbl-bibliography` with tags)
4. The 3 homebrew variants (pick one, archive two)
5. The `hummbl-dev-*` variants (determine canonical, archive rest)
6. The `founder-mode-*` variants (pick one, archive rest)

**Pros**: Low risk, immediate cognitive-load reduction, preserves all active repos
**Cons**: Still ~120+ repos after cleanup, doesn't solve the fundamental proliferation

**Effort**: Low. ~4 hours of archive + redirect setup.

### Option C: Category-based grouping with archive (moderate)

**Approach**: Option B plus reorganize the remaining repos into category subdirectories under PROJECTS:
```
PROJECTS/
  governance/    (governance, compliance, policy, krineia)
  fleet/         (agent-tools, apex-nexus, fleet-standard, etc.)
  research/      (bibliography, papers, benchmarks, corpus)
  product/       (hummbl-production, hummbl-brand, hummbl-cli, etc.)
  infra/         (infrastructure-as-code, docker, ollama-mon, etc.)
  edu/           (hd-*, coaching, study-companion)
  personal/      (lsat-prep, career-ops, peptide-check, etc.)
  archive/       (stale/duplicate repos moved here)
```

**Pros**: Significant cognitive-load reduction, no git history changes, visual grouping
**Cons**: Breaks scripts that expect flat PROJECTS layout, requires updating path references, git remotes stay the same

**Effort**: Medium. ~1 day for reorganization + path reference updates.

### Option D: PROPOSAL only — defer consolidation to operator-driven process

**Approach**: Draft this proposal, identify the clear archive candidates, and defer the actual consolidation to an operator-driven session where each merge/archive decision is made individually.

**Pros**: No risk of wrong decisions, operator retains full control
**Cons**: Proliferation continues until the operator acts

**Effort**: Zero (this proposal is the deliverable).

## 4. Recommendation

**Option B (conservative archive)** is recommended as a first pass, with **Option C (category grouping)** as a follow-up if the operator wants further organization.

**Rationale**:
1. Option A (monorepo) is high-risk and high-effort; the fleet is actively shipping from several repos and a merge could break CI
2. Option B delivers immediate value (removing ~30-40 stale/duplicate repos) with near-zero risk
3. Option C can be done later as a separate, non-breaking step
4. The 13 no-`.git` directories are clearly not repos — they're workspace artifacts that belong in `_archive/` or should be deleted

## 5. Immediate archive candidates (no operator decision needed)

These 13 directories have no `.git` and are not version-controlled repos:

| Directory | Likely status | Recommended action |
|-----------|---------------|-------------------|
| `founder-mode` | Local working copy (founder-mode-repo is the git version) | Move to `_archive/` |
| `founder-mode-repo` | Duplicate of founder-mode | Move to `_archive/` |
| `hummbl-brand-assets` | Asset dump, no git | Move to `_archive/` |
| `hummbl-tuples` | Experimental, no git | Move to `_archive/` |
| `on-device-llm-benchmark` | Benchmark workspace, no git | Move to `_archive/` |
| `org-consolidation-backups` | Backup from prior consolidation | Move to `_archive/` |
| `ownward-temp-push` | Temp push workspace | Delete (if confirmed stale) |
| `resilient-comms-lab` | Lab workspace, no git | Move to `_archive/` |
| `session-artifacts` | Session output dump | Move to `_archive/` |
| `stealthops-slate-commercial` | Commercial workspace, no git | Move to `_archive/` |
| `study-companion` | App prototype, no git | Move to `_archive/` |
| `transcripts` | Transcript dump | Move to `_archive/` |
| `zai-model-benchmark` | Benchmark workspace, no git | Move to `_archive/` |

## 6. Open questions

1. Which `hummbl-dev-*` variant is canonical?
2. Which `founder-mode-*` variant is canonical?
3. Which `homebrew-*` repo is canonical?
4. Should the numbered bibliography variants be merged into `hummbl-bibliography` with tags, or kept as historical snapshots?
5. Should `hummbl-production-codex-*` be merged into `hummbl-production` or kept separate for deployment independence?
6. Are the 3 no-remote repos (`founder-mode-clean-cherry`, `hummbl-learning`, `research-worktree`) experiments that should be archived or pushed?

## 7. Decision

**Operator decision required.** Select A, B, C, or D. If B, confirm the 13 no-`.git` directories should be moved to `_archive/` and answer the open questions for the duplicate-cluster consolidation.
