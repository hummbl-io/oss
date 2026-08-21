# ADR Drift Audit — 2026-06-22

**Auditor:** devin (automated)
**Date:** 2026-06-22
**Remediation date:** 2026-06-22
**Scope:** All 68 non-fork repos on `hummbl-dev` GitHub + local repos
**Total ADRs found:** 60 repos with ADRs, 100+ individual ADR files
**Status:** ALL 10 FINDINGS REMEDIATED

## Executive summary

**10 distinct drift issues found across the fleet.** All 10 have been
remediated as of 2026-06-22. The most severe were: numbering scheme
fragmentation (3+ schemes), path fragmentation (11+ ADR directories in
hummbl-governance alone), and phantom cross-references in the hummbl-governance ADR
index.

## Remediation summary

| ID | Severity | Issue | Status | PR/Commit |
|----|----------|-------|--------|-----------|
| D1 | SEVERE | 3+ incompatible numbering schemes | RESOLVED | hummbl-governance#1019 |
| D2 | SEVERE | 11+ ADR directory paths in hummbl-governance | RESOLVED | hummbl-governance#1019 |
| D3 | MODERATE | 5 different status field formats | RESOLVED | hummbl-governance#1019 |
| D4 | MODERATE | 4 different date field formats | RESOLVED | hummbl-governance#1019 |
| D5 | MODERATE | hummbl-iac ADR-001 numbering collision | RESOLVED | hummbl-iac#8 |
| D6 | MODERATE | swarm-test ADRs 001-006 missing ADR- prefix | RESOLVED | swarm-test#7 |
| D7 | LOW | hummbl-governance DOCS/adr/ casing drift | RESOLVED | hummbl-governance#1019 |
| D8 | MODERATE | ADR_INDEX.md stale (claimed 90+, listed ~30) | RESOLVED | hummbl-governance#1019 |
| D9 | MODERATE | Phantom cross-references | RESOLVED | hummbl-governance#1019 |
| D10 | LOW | Missing fields in baseline ADRs | RESOLVED (44/48) | Direct commits to 44 repos |

D10 note: 4 repos could not be updated because they are archived
(autoresearch-win-rtx, governed-compression, hummbl-asi, hummbl-assurance).
Archived repos are read-only on GitHub.

---

## Fleet ADR inventory

| Repo | ADR count | Notes |
|------|-----------|-------|
| 59 repos | 1 each | All `ADR-001-repo-governance-baseline.md` from fleet rollout |
| `hummbl-governance` | 5 | ADR-001 through ADR-005 (canonical standards) |
| `hummbl-iac` | 3 | 2 real ADRs + 1 baseline (numbering collision) |
| `swarm-test` | 7 | 6 real ADRs + 1 baseline (non-standard naming) |
| `hummbl-governance` | 30+ | Across 7+ directories, 4+ naming schemes |

---

## Drift findings

### D1: Numbering scheme fragmentation (SEVERE)

**3+ incompatible numbering schemes in production:**

| Scheme | Example | Where | Standard? |
|--------|---------|-------|-----------|
| `ADR-NNN-kebab-title.md` | `ADR-001-repo-governance-baseline.md` | Fleet rollout (59 repos), hummbl-governance | Yes (Init Standard v0.1) |
| `NNN-kebab-title.md` | `001-lazy-spawn.md` | swarm-test ADRs 001-006 | No |
| `ADR-{DOMAIN}-NNN-title.md` | `ADR-GOV-002-runtime-agnostic-agent-execution.md` | hummbl-governance governance/agent/kernel/mobile | No (domain-prefixed) |
| `ADR-NNNN-title.md` | `ADR-0001-monorepo.md` | hummbl-governance platform | No (4-digit) |
| `ADR-NNNN-kebab-title.md` | `ADR-0012-push-pull-loop-adr.md` | hummbl-governance design | No (4-digit, no domain) |

**Fix:** The Init Standard v0.1 mandates `ADR-NNN-kebab-title.md` (3-digit,
zero-padded, ADR prefix, no domain prefix). All non-standard ADRs should be
renamed. Domain prefixing is useful but should be in the title, not the
number: `ADR-006-gov-runtime-agnostic-agent-execution.md` not
`ADR-GOV-002-runtime-agnostic-agent-execution.md`.

### D2: Path fragmentation (SEVERE)

**11+ different ADR directory paths in hummbl-governance alone:**

| Path | Count | Standard? |
|------|-------|-----------|
| `docs/adr/` | 59 repos | Yes (Init Standard v0.1) |
| `DOCS/adr/` | hummbl-governance (uppercase, from rollout) | No — casing drift |
| `docs/governance/adr/` | hummbl-governance (7 ADRs) | No — extra nesting |
| `docs/agent-onboarding/surface-identity/adr/` | hummbl-governance (4 ADRs) | No — deep nesting |
| `docs/design/agent-kernel-v0/adr/` | hummbl-governance (5 ADRs) | No — deep nesting |
| `docs/mobile-ops/adr/` | hummbl-governance (5 ADRs) | No — domain subdir |
| `docs/audit/` | hummbl-governance (1 ADR, no adr/ subdir) | No |
| `docs/design/` | hummbl-governance (1 ADR, no adr/ subdir) | No |
| `docs/infrastructure/` | hummbl-governance (ADRs mixed with non-ADR docs) | No |
| `PROJECTS/platform/docs/ARCHITECTURE_DECISIONS/` | hummbl-governance (2 ADRs) | No |
| `hummbl_governance/docs/governance/adr/` | hummbl-governance (snake_case cruft) | No — untracked dir |

**Fix:** All ADRs should live at `docs/adr/`. Domain subdirectories
(`docs/adr/governance/`, `docs/adr/agent-kernel/`) are acceptable for repos
with 10+ ADRs. The `DOCS/` casing in hummbl-governance should be lowered to
`docs/`.

### D3: Status field format drift (MODERATE)

**5 different status field formats:**

| Format | Example | Where |
|--------|---------|-------|
| `- **Status:** accepted` | `- **Status:** accepted` | Fleet rollout, hummbl-governance ADR-003+ | 
| `**Status**: ACCEPTED` | `**Status**: ACCEPTED` | hummbl-governance ADR-001/002, hummbl-governance design |
| `**Status**: Accepted` | `**Status**: Accepted` | hummbl-iac |
| `## Status\n\nAccepted` | `## Status\n\nAccepted` | swarm-test, hummbl-governance platform |
| `- Status: Accepted` | `- Status: Accepted` | hummbl-governance audit |

**Fix:** Init Standard v0.1 mandates `- **Status:** accepted` (lowercase
value, bold key with colon, dash prefix). All ADRs should be normalized.

### D4: Date field format drift (MODERATE)

**4 different date field formats:**

| Format | Where |
|--------|-------|
| `- **Date:** 2026-06-22` | Fleet rollout, hummbl-governance ADR-003+ |
| `**Decided**: 2026-05-14` | hummbl-governance ADR-001 |
| `**Date**: 2026-06-16` | hummbl-governance ADR-002, hummbl-iac |
| No date in header | swarm-test 001-004, hummbl-governance many |

**Fix:** Init Standard v0.1 mandates `- **Date:** YYYY-MM-DD`.

### D5: hummbl-iac ADR-001 numbering collision (MODERATE)

`hummbl-iac` has two ADRs both numbered 001:
- `ADR-001-chezmoi-for-dotfiles.md` (real decision, 2026-03-26)
- `ADR-001-repo-governance-baseline.md` (fleet rollout, 2026-06-22)

**Fix:** Renumber the chezmoi ADR to `ADR-001` and the baseline to
`ADR-003` (after the per-machine-keys ADR which is already 002). Or
renumber the baseline to `ADR-003` and leave the originals as-is.

### D6: swarm-test ADR naming non-standard (MODERATE)

swarm-test ADRs 001-006 use `NNN-kebab-title.md` (no `ADR-` prefix).
ADR-007 uses the standard `ADR-007-repo-governance-baseline.md`.

**Fix:** Rename `001-lazy-spawn.md` → `ADR-001-lazy-spawn.md`, etc.

### D7: hummbl-governance DOCS/ casing drift (LOW)

The fleet rollout placed the governance baseline ADR at `DOCS/adr/` in
hummbl-governance (uppercase) due to the `.gitignore` deny-by-default issue.
The repo's other ADRs use `docs/` (lowercase).

**Fix:** Rename `DOCS/adr/` → `docs/adr/` and update `.gitignore` to
allow `docs/`.

### D8: ADR_INDEX.md drift (MODERATE)

The `hummbl-governance/docs/ADR_INDEX.md` claims "90+ across 7 directories"
but:
- Only lists ~30 ADRs (60+ are missing from the index)
- Many entries have "—" for all metadata (status, date, owner, disposition)
- Infrastructure section says 8 ADRs but lists 7 (ADR-007 FastAPI is in
  `docs/audit/` not `docs/infrastructure/`)
- Research section says "50+" but lists only 8
- ADR-GOV-005 appears with two different titles:
  - "Bus Token Encryption" (in index table)
  - "AI Factory Simulation Mesh" (actual file at `hummbl_governance/docs/...`)

**Fix:** Rebuild the ADR index from a filesystem scan. Add a CI check
that validates the index against actual files.

### D9: Phantom cross-references (MODERATE)

Several ADRs reference files that don't exist at the expected path:

| Reference | Expected path | Actual path | Issue |
|-----------|--------------|-------------|-------|
| `ADR-GOV-001` | `docs/governance/adr/` | `hummbl-governance/docs/governance/adr/` | Path prefix drift |
| `ADR-006-tricloud` | `docs/infrastructure/` | `hummbl-governance/docs/infrastructure/` | Not in an `adr/` subdir |
| `ADR-007-fastapi` | `docs/adr/` | `hummbl-governance/docs/audit/` | Not in an `adr/` subdir |

**Fix:** Consolidate all ADRs to `docs/adr/` and update cross-references.

### D10: Missing fields in baseline ADRs (LOW)

Some fleet rollout baseline ADRs are missing standard fields:

| Repo | Missing |
|------|---------|
| `hummbl-production` | `**Steward:**` |
| `swarm-test` ADR-007 | Most fields (truncated content) |
| Many repos | `**Supersedes:**` and `**Superseded by:**` |

**Fix:** The generator script (`tools/init_repo.py`, not yet built) should
always include all standard fields with `none` as the default value.

---

## Recommended remediation

### Priority order

1. **D7 (DOCS/ casing)** — Quick fix, unblocks hummbl-governance consistency
2. **D5 (hummbl-iac collision)** — Renumber one ADR
3. **D6 (swarm-test naming)** — Rename 6 files
4. **D3 + D4 (status/date format)** — Batch normalize across fleet
5. **D2 (path consolidation)** — Move hummbl-governance ADRs to `docs/adr/`
6. **D1 (numbering scheme)** — Rename all non-standard ADR numbers
7. **D8 (ADR_INDEX.md)** — Rebuild from filesystem scan
8. **D9 (phantom refs)** — Fix after D2 consolidates paths
9. **D10 (missing fields)** — Fix in next rollout generator

### What NOT to do

- Do not mass-rename ADRs in repos that have active CI checking ADR paths
- Do not renumber hummbl-governance ADRs 001-005 (they are the canonical
  standards and referenced by other repos)
- Do not delete the `hummbl_governance/` (snake_case) ADRs until confirming
  they are truly untracked cruft (the path drift note in AGENTS.md says so,
  but verify before deleting)
