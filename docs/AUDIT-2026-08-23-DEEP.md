# oss Deep Audit — 2026-08-23

**Date:** 2026-08-23
**Repository:** `hummbl-io/oss`
**Scope:** Code, structure, security, version drift, public/private boundary, package integrity
**Posture:** Read-only audit; no source or configuration changes were made
**Auditor:** devin (automated audit)
**Prior audit:** `docs/AUDIT-2026-08-23.md` (Tier 1 doc/config) — this audit extends to Tier 2 (code/structure/security)

## Executive verdict

The monorepo is structurally sound with good CI hygiene (SHA-pinning, trusted publishing, workflow validation). However, it has a **critical public/private boundary violation** (internal handoffs and agent session receipts published to a public repo), **version drift across multiple surfaces** (governance.yml, SECURITY.md, TEST_COUNT_AUTHORITY.md, public-claims.md all stale vs pyproject.toml), a **broken README example** in hummbl-kernel, a **PyPI namespace collision risk** in hummbl-kernel, and **scope drift** in the hummbl package (peptide domain code in a general-purpose reasoning framework).

## Verification summary

| Check | Result |
|---|---|
| File count | 720 (up from 717 in prior audit) |
| Packages present | 3 of 7 listed in root README (hummbl, hummbl-governance, hummbl-kernel) |
| PyPI published | hummbl-governance 1.4.1 (live); hummbl + hummbl-kernel NOT on PyPI (404) |
| CI workflows | 3 (ci.yml, publish-pypi.yml, validate-workflows.yml) — all SHA-pinned |
| License | Root dual-licensed MIT OR Apache-2.0; sub-packages Apache-2.0 only (drift) |
| Secret scan | 0 actual secrets found (12 doc pattern hits — all policy/example text) |
| Public/private boundary | **CRITICAL FAILURE** — internal handoffs/AARs/receipts in public repo |
| Version drift | 5 surfaces stale vs pyproject.toml (governance.yml, SECURITY.md, TEST_COUNT_AUTHORITY.md, public-claims.md, MCP SERVER_VERSION) |
| Broken doc links | 3+ (ROADMAP.md, PRIMITIVES.md, IMPLEMENTATION_SUMMARY.md, kernel_design.md — all referenced, none exist) |
| Broken code examples | 1 (hummbl-kernel README imports `Kernel`, actual class is `MissionModeKernel`) |

## Findings

### P0 — CRITICAL: Internal handoffs and agent session artifacts in public repo

**Files:**
- `packages/hummbl-governance/docs/handoffs/2026-08-10-agentic-engineering.md`
- `packages/hummbl-governance/docs/operations/DRAFT_PR_PROMOTION_QUEUE.md`
- `packages/hummbl-governance/docs/operations/AGENT_TOOLSET_STARTER.md`
- `packages/hummbl-governance/docs/receipts/HMIK-v0.0.4-engineering-receipt.md`
- `packages/hummbl-governance/docs/benchmarks/addyosmani-adverse/receipt.md`
- `packages/hummbl-governance/docs/cross-repo-contracts/v0.1/implementation-receipt-2026-07-11.md`
- `packages/hummbl-governance/docs/AUDIT-2026-08-14.md`
- `packages/hummbl-governance/docs/aar-20260530-setup-python-ci-fix.md`
- `packages/hummbl-governance/docs/trackers/*` (6 files — internal trackers)

**Evidence:** The handoff file names internal agent sessions, describes sub-agent orchestration patterns, and references internal coordination transcripts. The benchmark receipt names internal tooling and operator identity.

**Violation:** The repo's own `docs/public-private-boundary.md` (in hummbl-governance) explicitly prohibits publishing "raw bus logs, operator-only runbooks, or internal coordination transcripts" and "private infrastructure details". These files are internal coordination transcripts.

**Impact:** Public exposure of internal agent fleet operations, model IDs, operator identity, machine hostnames, sub-agent orchestration patterns, and internal workflow details. This is a reputation and operational security issue, not a code vulnerability.

**Recommendation:** Remove `docs/handoffs/`, `docs/operations/`, `docs/trackers/`, `docs/receipts/`, and all AAR/audit files from the public repo. Move to the private `hummbl-io/hummbl-governance` repo. Keep only public-safe docs (API specs, compliance mappings, schema docs, integration guides).

---

### P0 — CRITICAL: hummbl-kernel README example is broken

**File:** `packages/hummbl-kernel/README.md` (Quick Start section)

**Evidence:** README says:
```python
from kernel import Kernel
kernel = Kernel()
result = kernel.execute(workflow)
```

But the actual class in `kernel/kernel.py` is `MissionModeKernel`, and the method is `async execute_workflow()`, not `execute()`. Running the README example would raise `ImportError: cannot import name 'Kernel' from 'kernel'`.

**Impact:** Anyone who tries the Quick Start example gets an immediate error. This is the first impression for the package.

**Recommendation:** Fix the README to use `from kernel import MissionModeKernel` and `await kernel.execute_workflow(workflow_yaml, inputs)`.

---

### P1 — HIGH: hummbl-kernel package name collides with existing PyPI package

**File:** `packages/hummbl-kernel/pyproject.toml`

**Evidence:** `[tool.setuptools.packages.find]` has `include = ["kernel*"]` — this installs a top-level `kernel` package. There is already a `kernel` package on PyPI (v0.93.0, unrelated). Installing `hummbl-kernel` alongside the existing `kernel` package would overwrite it.

**Impact:** Namespace collision. Users who have `kernel` installed and add `hummbl-kernel` will have their `kernel` package shadowed. pip does not warn about this.

**Recommendation:** Rename the import package to `hummbl_kernel` (not `kernel`). Update `pyproject.toml` to `include = ["hummbl_kernel*"]` and rename the `kernel/` directory to `hummbl_kernel/`.

---

### P1 — HIGH: Version drift across 5+ surfaces

**pyproject.toml says 1.4.1 (correct, matches PyPI).** The following are stale:

| File | Says | Should be |
|---|---|---|
| `hummbl_governance/governance.yml` (ships in wheel) | `version: 1.4.0` | `1.4.1` |
| `docs/TEST_COUNT_AUTHORITY.md` | `Package version: 1.3.0` | `1.4.1` |
| `docs/public-claims.md` | `Current package metadata: version 1.4.0` | `1.4.1` |
| `SECURITY.md` (hummbl-governance) | `v1.4.0` in scope text | `1.4.1` |
| `SECURITY.md` (hummbl-governance) | `1.2.x` as current supported | `1.4.x` |
| `mcp_server.py` (all 7 MCP servers) | `SERVER_VERSION = "0.1.0"` | `1.4.1` or derived from `__version__` |

**Impact:** `governance.yml` ships inside the wheel — PyPI users installing 1.4.1 see governance metadata claiming 1.4.0. The MCP servers all report version 0.1.0 to clients regardless of package version. SECURITY.md tells security researchers that 1.2.x is current, which is 2 minor versions behind.

**Recommendation:** Derive `governance.yml` version from `pyproject.toml` at build time, or update it in the release process. Make MCP `SERVER_VERSION` import `__version__` from the package. Update all stale doc references as part of the release checklist.

---

### P1 — HIGH: hummbl-kernel CHANGELOG claims PyPI release that doesn't exist

**File:** `packages/hummbl-kernel/CHANGELOG.md`

**Evidence:** `## [0.1.0] - 2026-08-22` says "Initial PyPI release of the hummbl-kernel package". But `hummbl-kernel` returns 404 on PyPI. The root README correctly says "Pending first release".

**Impact:** False claim of publication. Users reading the CHANGELOG believe the package is on PyPI when it isn't.

**Recommendation:** Either publish to PyPI or change the CHANGELOG entry to "Initial release candidate" / "Pre-release preparation".

---

### P2 — MEDIUM: Primitive count inconsistency (34 vs 36)

**Files:** `packages/hummbl-governance/README.md`, `SECURITY.md`, `docs/public-claims.md`

**Evidence:**
- README line 12: "36 governance primitives"
- README line 15: "Explore all 34 primitives"
- README table header: "## All 34 Primitives"
- README posture line: "36 implemented primitives"
- public-claims.md: "34 implemented governance primitives exist — verified"
- SECURITY.md: "36 implemented governance primitives"

The authority (`public-claims.md`) says 34. The README says both 34 and 36 in different places.

**Recommendation:** Pick one number and use it consistently. If 36 is correct (34 + 2 new), update `public-claims.md` and `TEST_COUNT_AUTHORITY.md`. If 34 is correct, fix the README lines that say 36.

---

### P2 — MEDIUM: License inconsistency between root and sub-packages

**Evidence:**
- Root `LICENSE` file: dual-licensed "MIT OR Apache-2.0" (per commit 55f1946)
- Root `README.md`: "Apache-2.0. See [LICENSE](LICENSE)."
- All 3 sub-package `pyproject.toml`: `license = "Apache-2.0"`
- All 3 sub-package `LICENSE` files: Apache 2.0 only
- `hummbl_governance/governance.yml`: `license: Apache-2.0`

**Impact:** The root repo is dual-licensed but the packages ship as Apache-2.0 only. This is probably intentional (packages pick one of the two options) but the root README doesn't mention the dual license or that packages are Apache-only.

**Recommendation:** Update root README to say "Dual-licensed (MIT OR Apache-2.0) at the repo level; packages ship under Apache-2.0" or harmonize.

---

### P2 — MEDIUM: hummbl package contains unrelated peptide domain code

**Files:** `packages/hummbl/hummbl/peptide_protocol.py`, `packages/hummbl/hummbl/peptide_rules.py`

**Evidence:** The `hummbl` package is described as "Structured reasoning framework for AI agents" in its README and pyproject.toml. But `__init__.py` imports and exports `PeptideQualityProtocol`, `PeptideSpec`, `PEPTIDE_SPECS`, `VENDOR_TRUST_TIERS`, `GRADE_RECOMMENDATIONS` — domain-specific code for peptide quality assessment (chemical/biochemical domain). These are not covered by any test file (tests only cover protocols, reasoning, scoring, tool_use_capture).

**Impact:** Scope drift. Users installing `hummbl` for reasoning frameworks get peptide chemistry code they don't need. The peptide code is untested and imported on package load.

**Recommendation:** Either (a) move peptide code to a separate `hummbl-peptide` package, or (b) document it as a domain example in the README and add tests, or (c) make it an optional import (`hummbl.peptide`) rather than a top-level export.

---

### P2 — MEDIUM: Broken doc references (4 files referenced but not present)

| Referenced file | Referenced in | Exists? |
|---|---|---|
| `ROADMAP.md` | `SECURITY.md` (hummbl-governance) | No |
| `PRIMITIVES.md` | `SECURITY.md`, `docs/public-claims.md`, `docs/TEST_COUNT_AUTHORITY.md` | No |
| `IMPLEMENTATION_SUMMARY.md` | `hummbl-kernel/README.md` | No |
| `kernel_design.md` | `hummbl-kernel/README.md` | No |

**Impact:** Broken links in published package docs. Users following these references hit 404s.

**Recommendation:** Either create the missing files or remove the references. `PRIMITIVES.md` is referenced as the authority for primitive counts — its absence undermines the verification chain.

---

### P2 — MEDIUM: Stale repo URLs in sub-package docs

**Files:** `CONTRIBUTING.md`, `CHANGELOG.md`, `SECURITY.md`, `REPO_HEALTH.md` (hummbl-governance)

**Evidence:** 7+ files in `hummbl-governance/docs/` still reference `github.com/hummbl-io/hummbl-governance` (the old standalone repo) instead of `github.com/hummbl-io/oss` (the monorepo). The `governance.yml` file that ships in the wheel has `source_repo: https://github.com/hummbl-io/hummbl-governance`.

**Impact:** Users following links from the published package are directed to a repo that may redirect or 404. The wheel's `governance.yml` reports the wrong source repo.

**Recommendation:** Update all `hummbl-io/hummbl-governance` references to `hummbl-io/oss` in sub-package docs. Update `governance.yml` `source_repo` field.

---

### P3 — LOW: hummbl-kernel has stub directories with no implementation

**Directories:** `kernel/adapters/`, `kernel/workflows/`

**Evidence:** Both directories contain only `__init__.py` and a `.md` doc file — no Python implementation. The `adapters/` directory has `adapter_interface.md` but no adapter code. The `workflows/` directory has `schema.md` but no workflow engine code.

**Recommendation:** Either implement the stubs or remove them and document as "planned" in the README.

---

### P3 — LOW: No CODEOWNERS or AGENTS.md at monorepo root

**Evidence:** No `.github/CODEOWNERS` and no `AGENTS.md` at the repo root. The root `CONTRIBUTING.md` is thorough but doesn't route review ownership.

**Recommendation:** Add `.github/CODEOWNERS` with at least `* @hummbl-io` and per-package routing. Add `AGENTS.md` describing the monorepo structure for agent-assisted development.

---

### P3 — LOW: Stale .gitignore entry

**File:** `.gitignore`

**Evidence:** `hummbl_governance/data/registry/*.jsonl` is ignored but the `data/registry/` directory contains only `seed_registry.py` — no `.jsonl` files exist or are expected.

**Recommendation:** Remove the stale entry or document why it's there.

---

### P3 — LOW: governance.yml hardcodes test count

**File:** `hummbl_governance/governance.yml` (ships in wheel)

**Evidence:** `tests: 2314` is hardcoded. This will drift as tests are added. The README badge also hardcodes `tests-2314%20collected`.

**Recommendation:** Either generate `governance.yml` at build time with the current test count, or omit the field (it's not actionable for consumers anyway).

---

## File inventory (verified)

```
Root:
  .github/workflows/ (3: ci.yml, publish-pypi.yml, validate-workflows.yml)
  .gitattributes, .gitignore
  CONTRIBUTING.md, LICENSE, LICENSE-APACHE, LICENSE-MIT, README.md, RELEASE.md, SECURITY.md
  docs/ (6: AUDIT-2026-08-23, DELEGATION-IETF-GAP-ANALYSIS, FLEET-GOVERNANCE-MAPPING, FULL-MENU, MONOREPO-DESIGN, PACKAGES)
  tools/scripts/ (2: validate_workflows.py, test_validate_workflows.py)

packages/hummbl/ (pending first PyPI release):
  hummbl/ (12 .py files: reasoning, protocols, peptide_protocol, peptide_rules, capture, scoring, analyzer, planner, visualize, cli, __init__, __main__)
  hummbl/hummbl_tuples/ (3 .py files: base, idp, __init__)
  tests/ (4 test files)
  pyproject.toml, README.md, LICENSE

packages/hummbl-governance/ (live on PyPI as 1.4.1):
  hummbl_governance/ (37 .py files, governance.yml, data/ with 21 JSON + 17 YAML schemas)
  mcp_*.py (7 MCP server modules at package root)
  examples/ (10 .py integration examples)
  tests/ (64 test files)
  tools/ (4 lint tools)
  scripts/ (12 utility scripts + validation/)
  docs/ (275 .md, 41 .json, 4 .py, 2 .tsv, 1 .svg, 1 .jsonl — LARGE)
  pyproject.toml, README.md, CHANGELOG.md, CONTRIBUTING.md, SECURITY.md, CODE_OF_CONDUCT.md, LICENSE, NOTICE

packages/hummbl-kernel/ (NOT on PyPI despite CHANGELOG claim):
  kernel/ (kernel.py + 3 subdirs: adapters/, audit/, fleet/, security/, workflows/ — mostly stubs)
  tests/ (4 test files)
  pyproject.toml, README.md, CHANGELOG.md, CONTRIBUTING.md, LICENSE, NOTICE
```

## Recommendations (prioritized)

1. **P0: Remove internal docs from public repo.** Move `docs/handoffs/`, `docs/operations/`, `docs/trackers/`, `docs/receipts/`, AAR files, and internal audit files to the private `hummbl-io/hummbl-governance` repo. This is a public/private boundary violation.

2. **P0: Fix hummbl-kernel README example.** Change `from kernel import Kernel` to `from kernel import MissionModeKernel` and fix the method call to `await kernel.execute_workflow(...)`.

3. **P1: Rename hummbl-kernel import package.** Change `kernel/` to `hummbl_kernel/` to avoid PyPI namespace collision with the existing `kernel` package (v0.93.0).

4. **P1: Fix version drift.** Update `governance.yml`, `TEST_COUNT_AUTHORITY.md`, `public-claims.md`, `SECURITY.md`, and MCP `SERVER_VERSION` to match `pyproject.toml` (1.4.1). Consider deriving these at build time.

5. **P1: Correct hummbl-kernel CHANGELOG.** Change "Initial PyPI release" to "Pre-release preparation" since the package is not on PyPI.

6. **P2: Resolve primitive count inconsistency.** Pick 34 or 36 and use it consistently across README, SECURITY.md, public-claims.md, and TEST_COUNT_AUTHORITY.md.

7. **P2: Move peptide code out of hummbl package.** Create `hummbl-peptide` or make it an optional import.

8. **P2: Fix broken doc references.** Create `PRIMITIVES.md` and `ROADMAP.md` or remove references to them.

9. **P2: Update stale repo URLs.** Replace `hummbl-io/hummbl-governance` with `hummbl-io/oss` in sub-package docs and `governance.yml`.

10. **P3: Add CODEOWNERS and AGENTS.md at root.**

11. **P3: Remove stale .gitignore entry** for `hummbl_governance/data/registry/*.jsonl`.

12. **P3: Remove or implement stub directories** in hummbl-kernel (`adapters/`, `workflows/`).
