# M&A Consolidation Plan Reconciliation

**Date:** 2026-08-27
**Author:** Devin fleet (devin)
**Purpose:** Reconcile the original M&A consolidation plan (Option B: conservative archive) against the current `hummbl-io/oss` monorepo reality.

---

## Executive Summary

The original M&A consolidation plan proposed a phased migration of ~100 HUMMBL packages into a single `hummbl-io/oss` monorepo. The monorepo migration has **substantially overtaken** the original plan — Phase 1 is complete, Phase 3 is partially done, and 23 repos have been archived. The original "Option B: conservative archive" proposal is now largely **stale** because the oss monorepo already absorbed most of the packages that were candidates for consolidation.

**Current state:** 303 total repos, 23 archived, 280 active. 14 Python packages in oss monorepo.

---

## Phase-by-Phase Reconciliation

### Phase 0: Structure — COMPLETE

| Task | Status |
|------|--------|
| Create `docs/MONOREPO-DESIGN.md` | DONE |
| Create `docs/PACKAGES.md` | DONE |
| Move to `packages/python/<name>/` layout | DONE |
| Update `publish-pypi.yml` tag filter | DONE |
| Update README.md package table | DONE |

### Phase 1: Migrate live PyPI packages — COMPLETE (7/7)

| Package | Status | Archived Repo |
|---------|--------|---------------|
| `hummbl-governance` | DONE | `hummbl-governance` (archived 2026-08-27) |
| `hummbl-bus` | DONE | — |
| `hummbl-cognition` | DONE | — |
| `hummbl-tuples` | DONE | — |
| `hummbl-bif` | DONE | — |
| `base120` | DONE | — |
| `governed-compression` | DONE | — |

**Additional packages in oss beyond Phase 1 (7):** `hummbl`, `hummbl-compass`, `hummbl-free-models`, `hummbl-kernel`, `hummbl-rubric-templates`, `hummbl-taxonomy`, `hummbl-validation`

### Phase 2: Publish npm packages — NOT STARTED

No `packages/node/` directory exists in oss yet. The `@hummbl` npm scope is retained but no packages have been re-published.

### Phase 3: Publish not-yet-live packages — PARTIALLY DONE

| Priority package | In oss? | Archived? |
|-----------------|---------|-----------|
| `hummbl-validation` | YES | — |
| `hummbl-lattice` | NO | — |
| `hummbl-eval` | NO | `hummbl-eval` (archived) |
| `hummbl-clp` | NO | — |
| `hummbl-contracts` | NO | — |
| `hummbl-axis` | NO | — |
| `hummbl-crucible` | NO | `hummbl-crucible` (archived) |
| `hummbl-intel` | NO | — |
| `hummbl-dashboard` | NO | — |
| `hummbl-lint-config` | NO | — |

### Phase 4: Publish new-language packages — NOT STARTED

No `packages/rust/`, `packages/go/`, `packages/jvm/`, or `packages/nix/` directories exist yet.

### Phase 5: Papers, docs, sites, CLI manifests — NOT STARTED

No `papers/`, `sites/`, or `cli/` directories exist yet.

### Phase 6: Archive legacy repos — PARTIALLY DONE (23 archived)

23 repos have been archived. Key archived repos with oss counterparts:
- `hummbl-governance` → `packages/python/hummbl-governance/`
- `hummbl` (old root) → `packages/python/hummbl/`

Archived repos without clear oss counterparts (may need investigation):
- `hummbl-eval`, `hummbl-crucible`, `hummbl-library`, `hummbl-scripts`, `hummbl-security`, `hummbl-wiki`, `hummbl-audit`, `hummbl-scheduler`, `hummbl-alerts`, `hummbl-paralegal`, `hummbl-py`, `founder-mode`, `hermes-agent`

---

## What's Stale in the Original Plan

1. **"Option B: conservative archive"** — The conservative approach has been abandoned in practice. The oss migration is more aggressive than the original proposal, having already absorbed 14 packages and archived 23 repos.

2. **Phase 1 package list** — All 7 Phase 1 packages are done. The plan's Phase 1 checklist is fully complete.

3. **Repo-specific consolidation proposals** — Many repos that had individual `docs/consolidation-plan.md` files (hummbl-framework-crosswalks, hummbl-crosswalk-engine, hummbl-response-objects, hummbl-repo-factory, etc.) have been superseded by the monorepo migration. Their per-repo plans are stale.

4. **`hummbl-governance` as a standalone repo** — Archived 2026-08-27. All future development goes to `oss/packages/python/hummbl-governance/`. The 10 gap PRs (#419-#427) that were blocked by archival have been ported to oss as PR #65.

---

## What Remains Valid

1. **Phase 2 (npm)** — Still needs to be done. No npm packages in oss yet.
2. **Phase 3 (not-yet-live packages)** — Partially done. ~20+ packages still need migration.
3. **Phase 4 (new languages)** — Rust, Go, JVM, Nix packages not started.
4. **Phase 5 (papers, sites, CLI)** — Not started.
5. **Phase 6 (archive legacy)** — Ongoing. 23 done, ~20+ remaining candidates.

---

## Recommendations

1. **Update MONOREPO-DESIGN.md** — Mark Phase 1 as complete, update Phase 3 with current status.
2. **Investigate archived repos without oss counterparts** — Determine if their content was absorbed into other packages or needs separate migration.
3. **Prioritize Phase 3 governance ecosystem packages** — `hummbl-lattice`, `hummbl-clp`, `hummbl-contracts` are highest value.
4. **Defer Phase 2/4/5** — Until Phase 3 is further along.
5. **Continue Phase 6 archiving** — As packages migrate to oss, archive their legacy repos.

---

## Open Questions for Operator

1. Should the 10 gap commits (PR #65) be merged before or after the `hummbl-governance` archival is fully reconciled?
2. Are the archived repos without oss counterparts (hummbl-eval, hummbl-crucible, etc.) intentionally dropped, or do they need migration?
3. Should Phase 2 (npm) be prioritized now that Phase 1 is complete?
