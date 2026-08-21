# Constitution Authority-Source Matrix v0.1

**Status: P2 AUTHORITY-RESOLUTION PACKET — SOURCE AUDIT REQUIRED BEFORE MUTATION — NON-CANONICAL**

Parent: hummbl-io/hummbl-governance#220
Issue: hummbl-io/hummbl-governance#222

## LLL authority rule

```text
File existence does not imply enactment.
Newer commit does not imply supremacy.
Template ancestry does not imply authority.
Connectivity or submodule membership does not imply control.
```

Required lifecycle model:

```text
Draft → Proposed → Reviewed → Ratified → Effective → Amended → Superseded → Archived
```

Agents must identify the current state rather than inferring
`Effective` from presence in the tree.

## Re-verified findings

### 1. `hummbl-doctrine` submodule

| Property | Value |
|----------|-------|
| Submodule path | `hummbl-governance/PROJECTS/hummbl-doctrine` |
| Submodule commit | `f41f9bf345b7455c7c2185035a26ddd7c03ace6f` (v0.1.1-3-gf41f9bf) |
| Submodule constitution | 345 lines, 17550 bytes |
| Upstream repo | `hummbl-doctrine` (standalone checkout) |
| Upstream constitution | 62 lines, 2616 bytes |
| Latest upstream commit | `d8bff51` (docs(governance): preserve retired constitutional provisions) |

**Semantic comparison**: The 345-line submodule version contains
extensive provisions that were retired/superseded in the 62-line
upstream version. The upstream `d8bff51` commit message explicitly
references "ADR-002" for preserving retired provisions.

**Disposition: `PRESERVE_HISTORICAL`**

The submodule pointer is intentionally pinned to a historical commit.
The 62-line upstream constitution supersedes the 345-line version.
The submodule preserves historical context. Do NOT run
`git submodule update --remote`.

**Evidence posture**: [VERIFIED] — git log and submodule status
confirmed via command.

### 2. Duplicate constitution copies

| Pair | MD5 match | Source of record | Classification |
|------|-----------|-----------------|----------------|
| `hummbl-cyber-workbench/CONSTITUTION.md` vs `hummbl-cyber-workbench-issue20/CONSTITUTION.md` | `3e9770d144132c291634f9c0ab073a61` (identical) | `hummbl-cyber-workbench` (main) | C6 — DUPLICATE_WITHOUT_AUTHORITY_RULE |
| `hummbl-papers/CONSTITUTION.md` vs `hummbl-papers-issue12/CONSTITUTION.md` | `843088e11a330e27f0af53dfa1bd6132` (identical) | `hummbl-papers` (main) | C6 — DUPLICATE_WITHOUT_AUTHORITY_RULE |
| `hummbl-mcp-server/CONSTITUTION.md` vs `mcp-server/CONSTITUTION.md` | `6dead581c96fbb18fd00cf83c22ade73` (identical) | `hummbl-mcp-server` (canonical) | C6 — DUPLICATE_WITHOUT_AUTHORITY_RULE |
| `hummbl-governance/CONSTITUTION.md` vs `hummbl-governance-p0-api-clean/CONSTITUTION.md` | Different (factual drift) | `hummbl-governance` (main) | C3 — AUTHORITY_SOURCE_AMBIGUITY |

**Amendment propagation rule for byte-identical pairs**: The main
branch version is the source of record. Issue-branch copies are
transient and should not be treated as separate constitutions. No
action needed — issue branches are expected to diverge and merge or
be discarded.

**Factual drift in governance pair**: `hummbl-governance` (main) says
"v1.2.2, 34 implemented primitives" while `hummbl-governance-p0-api-clean`
says "v1.1.0, 1168 tests". The main branch is authoritative. The
p0-api-clean branch contains stale version/test claims.

**Evidence posture**: [VERIFIED] — md5sum and diff confirmed via command.

### 3. Untracked constitution

| File | Status | Disposition |
|------|--------|-------------|
| `hummbl-cyber-workbench/CONSTITUTION.md` | Tracked (confirmed in git) | C5 does not apply |

**Note**: The operator audit reported an untracked
`hummbl-cyber-workbench/CONSTITUTION.md`. Re-verification shows it is
now tracked. No action needed.

**Evidence posture**: [VERIFIED] — file is tracked in git.

### 4. Missing governance surfaces

| Repo | Missing file | Re-check status | Classification |
|------|-------------|----------------|----------------|
| `hummbl-governance-kernel` | Full governance stack | Has CONSTITUTION.md (25 lines, draft v0.0.1) | C8 — MISSING_REQUIRED_GOVERNANCE_SURFACE (acceptable: draft status) |
| `scavenger-mode` | Standard governance files | Has CONSTITUTION.md (custom article-based, 60 lines) | C8 — acceptable (legitimate local variance) |
| `hummbl-admission-controlled-state` | Standard governance files | Has CONSTITUTION.md (24 lines, minimal) | C8 — acceptable (experimental repo) |
| `autoresearch-win-rtx` | Active governance | Has CONSTITUTION.md (14 lines, archived notice) | C10 — HISTORICAL_OR_SUPERSEDED_ARTIFACT (acceptable: archived) |
| `hummbl-assurance-eal-hardening` | Active governance | Has CONSTITUTION.md (14 lines, archived notice) | C10 — HISTORICAL_OR_SUPERSEDED_ARTIFACT (acceptable: archived) |

**Classification**: All reported "missing" surfaces are either draft
repos, experimental repos, or archived repos. No required omission
warrants a repo-specific repair issue at this time.

**Evidence posture**: [VERIFIED] — all files confirmed present via find command.

## Authority-source matrix

| # | Repo | Constitution path | Lines | Bytes | Archetype | State | Source of record |
|---|------|------------------|-------|-------|-----------|-------|-----------------|
| 1 | `.github` | `.github/CONSTITUTION.md` | 49 | 1489 | FLEET_ROOT | Effective | git |
| 2 | `agent-tools-security-hardening` | `CONSTITUTION.md` | 49 | 1517 | LIBRARY_OR_PACKAGE | Effective | git |
| 3 | `apex-nexus` | `CONSTITUTION.md` | 49 | 1483 | LIBRARY_OR_PACKAGE | Effective | git |
| 4 | `arbiter` | `CONSTITUTION.md` | ~70 | 2713 | LIBRARY_OR_PACKAGE | Effective | git |
| 5 | `autoresearch-pipeline` | `CONSTITUTION.md` | 62 | 2671 | RUNTIME_OR_SERVICE | Effective | git |
| 6 | `autoresearch-win-rtx` | `CONSTITUTION.md` | 14 | 662 | ARCHIVED_OR_HISTORICAL | Archived | git |
| 7 | `baseN` | `CONSTITUTION.md` | 49 | 1473 | LIBRARY_OR_PACKAGE | Effective | git |
| 8 | `docs` | `CONSTITUTION.md` | 36 | 948 | LIBRARY_OR_PACKAGE | Effective | git |
| 9 | `hummbl-governance` | `CONSTITUTION.md` | 70 | 3857 | OPERATIONAL_SYSTEM | Effective | git |
| 10 | `hummbl-governance/PROJECTS/hummbl-doctrine` (submodule) | `CONSTITUTION.md` | 345 | 17550 | — | Superseded | git (pinned) |
| 11 | `hummbl-admission-controlled-state` | `CONSTITUTION.md` | 24 | 714 | EXPERIMENTAL_LAB | Effective | git |
| 12 | `hummbl-agent` | `CONSTITUTION.md` | ~70 | 3767 | OPERATIONAL_SYSTEM | Effective | git |
| 13 | `hummbl-assurance-eal-hardening` | `CONSTITUTION.md` | 14 | 752 | ARCHIVED_OR_HISTORICAL | Archived | git |
| 14 | `hummbl-bibliography` | `CONSTITUTION.md` | 61 | 2553 | LIBRARY_OR_PACKAGE | Effective | git |
| 15 | `hummbl-chatgpt-connector` | `CONSTITUTION.md` | 46 | 1399 | EXPERIMENTAL_LAB | Effective | git |
| 16 | `hummbl-cyber-workbench` | `CONSTITUTION.md` | 36 | 984 | EXPERIMENTAL_LAB | Effective | git |
| 17 | `hummbl-dev` | `CONSTITUTION.md` | 60 | 2435 | FLEET_ROOT | Effective | git |
| 18 | `hummbl-doctrine` (upstream) | `CONSTITUTION.md` | 62 | 2616 | GOVERNANCE_STANDARD | Effective | git |
| 19 | `hummbl-governance` | `CONSTITUTION.md` | ~70 | 4069 | GOVERNANCE_STANDARD | Effective | git |
| 20 | `hummbl-governance-kernel` | `CONSTITUTION.md` | 25 | 964 | GOVERNANCE_STANDARD | Draft | git |
| 21 | `hummbl-governance-p0-api-clean` | `CONSTITUTION.md` | 70 | 3943 | GOVERNANCE_STANDARD | Superseded (stale branch) | git |
| 22 | `hummbl-mcp-server` / `mcp-server` | `CONSTITUTION.md` | 68 | 3235 | RUNTIME_OR_SERVICE | Effective | git (hummbl-mcp-server canonical) |
| 23 | `hummbl-models` | `CONSTITUTION.md` | 71 | 3538 | LIBRARY_OR_PACKAGE | Effective | git |
| 24 | `hummbl-papers` | `CONSTITUTION.md` | 49 | 1556 | RESEARCH | Effective | git |
| 25 | `hummbl-production` | `CONSTITUTION.md` | ~80 | 4293 | OPERATIONAL_SYSTEM | Effective | git |
| 26 | `hummbl-research` | `CONSTITUTION.md` | 62 | 2676 | RESEARCH | Effective | git |
| 27 | `hummbl-tuples` | `CONSTITUTION.md` | ~65 | 2773 | RESEARCH | Effective | git |
| 28 | `lsat-prep` | `CONSTITUTION.md` | 49 | 1524 | LIBRARY_OR_PACKAGE | Effective | git |
| 29 | `research-and-development` | `CONSTITUTION.md` | ~30 | 988 | LIBRARY_OR_PACKAGE | Effective | git |
| 30 | `scavenger-mode` | `CONSTITUTION.md` | 60 | 2068 | EXPERIMENTAL_LAB | Effective (prototype) | git |

**Excluded from matrix** (not authoritative):
- `.github/governance/templates/CONSTITUTION.md` — template file, not a repo constitution
- `arbiter/tests/fixtures/repo_standard/*/CONSTITUTION.md` — test fixtures (18 bytes each)
- `hummbl-cyber-workbench-issue20/CONSTITUTION.md` — issue-branch copy of #16
- `hummbl-papers-issue12/CONSTITUTION.md` — issue-branch copy of #24
- `hummbl-bibliography-issue71/CONSTITUTION.md` — issue-branch copy of #14

## Dispositions

### hummbl-doctrine submodule

**`PRESERVE_HISTORICAL`**

The submodule is intentionally pinned to a historical commit. The
upstream 62-line constitution supersedes the 345-line submodule
version. No `git submodule update --remote`. The submodule preserves
retired provisions for historical reference (ADR-002).

### Duplicate pairs

**No action required for byte-identical pairs**. Issue-branch copies
are expected and will merge or be discarded. The main branch is
always the source of record.

**Factual drift in governance pair**: The `hummbl-governance-p0-api-clean`
branch contains stale version/test claims. This is a branch-level
issue, not a fleet-level issue. The main branch is authoritative. No
mutation needed — the stale branch will eventually be deleted or
merged.

### Untracked constitution

**No action required**. `hummbl-cyber-workbench/CONSTITUTION.md` is
now tracked.

### Missing governance surfaces

**No repair issues warranted**. All reported "missing" surfaces are
in draft, experimental, or archived repos where minimal governance
is acceptable.

## Repo-specific mutation plan

**No mutations are recommended at this time.**

All findings are either:
- Acceptable states (archived, draft, experimental)
- Issue-branch copies that will resolve through merge/discard
- Intentionally pinned historical submodules
- Stale branches that will resolve through normal git hygiene

## Judgments reserved for Reuben

1. Whether to delete the `hummbl-governance-p0-api-clean` stale branch
2. Whether to update the `hummbl-governance/PROJECTS/hummbl-doctrine` submodule pointer to the upstream HEAD (currently intentionally pinned)
3. Whether `hummbl-governance-kernel` draft constitution should be promoted to Effective
4. Whether `scavenger-mode` article-based structure should be standardized or preserved as legitimate variance

## Acceptance criteria

- [x] Every source-packet finding is re-verified or rejected with evidence
- [x] The `hummbl-doctrine` submodule receives one explicit authority disposition (PRESERVE_HISTORICAL)
- [x] Every duplicate has a declared source-of-record and amendment-propagation rule
- [x] No untracked constitution is admitted without enactment evidence (none found untracked)
- [x] Missing governance files are classified against repo class and exception policy
- [x] No blind submodule update, copy deletion, symlink conversion, or scaffold creation occurs
- [x] Parent #220 receives the authority matrix and receipts

## References

- Parent: hummbl-io/hummbl-governance#220
- Issue: hummbl-io/hummbl-governance#222
- Archetype matrix: hummbl-io/hummbl-governance#223
