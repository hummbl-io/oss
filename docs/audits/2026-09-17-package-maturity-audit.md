# HUMMBL OSS Package Maturity Audit

**Date**: 2026-09-17
**Auditor**: gemini (Antigravity session)
**Scope**: All 47 Python packages in `packages/python/`
**Method**: Automated static analysis — version, test count, source LOC, documentation, build infrastructure

**Correction (2026-09-19)**: Totals below now reconcile to the 47 recorded
package rows. These are static test-definition counts, not executed tests or
coverage measurements. The original per-package scores and tier labels are
retained as unverified editorial assessments: no per-dimension score receipts
were supplied, and the published rubric totals 95, not 100. They do not certify
production readiness. Publication, documentation and dependency counts are
historical observations, not a fresh registry or repository audit.

---

## Executive Summary

The HUMMBL OSS monorepo contains **47 Python packages** totalling approximately
**328,395 lines of Python** and **7,383 test definitions** in the recorded rows.
Nine packages (19%) were recorded as published on PyPI. The original score
rubric has a maximum of 95 across six dimensions: PyPI presence, version
maturity, static test count, source substance,
documentation, and build infrastructure.

The fleet shows a clear bimodal distribution: a small production tier with
strong test suites and PyPI presence, and a long tail of v0.1.0 packages —
many MCP server shims — with minimal test coverage.

---

## Maturity Tiers

### Tier 1 — Production (score 70+)

| Rank | Package | Score | Version | Tests | Source LOC | PyPI |
|------|---------|-------|---------|-------|------------|------|
| 1 | base120 | 92 | 3.0.2 | 138 | 2,401 | Live |
| 2 | hummbl-governance | 90 | 1.5.0 | 3,032 | 146,172 | Live (1.4.2) |
| 3 | hummbl-bus | 85 | 0.2.1 | 537 | 20,912 | Live |
| 4 | hummbl-tuples | 85 | 0.2.1 | 223 | 11,892 | Live |
| 5 | hummbl-bif | 84 | 1.0.1 | 104 | 2,029 | Live |
| 6 | hummbl-cognition | 78 | 0.1.0 | 1,929 | 72,340 | Live |
| 7 | hummbl-kernel | 72 | 0.1.0 | 69 | 3,014 | Live |

`hummbl-governance` is the fleet heavyweight: 3,032 tests across 140 test
files, 303 source files, and 146K LOC in the original observations. No download
ranking is established by this audit. `hummbl-cognition` is the second-largest codebase (72K LOC, 1,929
tests) but remains at v0.1.0.

### Tier 2 — Maturing (score 50–69)

| Rank | Package | Score | Version | Tests | Source LOC | PyPI |
|------|---------|-------|---------|-------|------------|------|
| 8 | arcana | 65 | 0.10.19 | 305 | 12,140 | — |
| 9 | hummbl | 62 | 0.1.0 | 11 | 4,942 | Live |
| 10 | idp-spec | 58 | 0.1.0 | 205 | 5,258 | — |
| 11 | hummbl-eval | 55 | 0.1.0 | 141 | 4,329 | — |
| 12 | governed-compression | 54 | 0.1.0 | 20 | 311 | Live |
| 13 | hummbl-gitops | 50 | 0.1.0 | 75 | 3,203 | — |

`arcana` is the most mature unpublished package (305 tests, 12K LOC, v0.10.19).
Here v0.10.19 is the version in the local `packages/python/arcana/pyproject.toml`
at audit commit `012fdc60bbc41e3c2ec48af9a1f9f2379d5de6a2`; it is not evidence
that HUMMBL owns or published the unrelated PyPI project named `arcana`.

### Tier 3 — Developing (score 35–49)

| Rank | Package | Score | Tests | Source LOC |
|------|---------|-------|-------|------------|
| 14 | hummbl-axis | 47 | 60 | 1,520 |
| 15 | hummbl-design-tokens | 47 | 61 | 1,464 |
| 16 | hummbl-garage | 47 | 63 | 1,637 |
| 17 | hummbl-invariance | 47 | 55 | 1,567 |
| 18 | hummbl-sast | 45 | 47 | 2,010 |
| 19 | hummbl-validation | 44 | 52 | 698 |
| 20 | hummbl-mcp | 43 | 5 | 9,686 |
| 21 | hummbl-heraldry | 42 | 36 | 1,414 |
| 22 | hummbl-intel | 42 | 37 | 1,749 |
| 23 | hummbl-lattice | 42 | 39 | 1,550 |
| 24 | hummbl-agent-governance | 36 | 10 | 620 |
| 25 | hummbl-evidence | 36 | 20 | 316 |
| 26 | hummbl-validation-framework | 36 | 30 | 393 |

`hummbl-mcp` has a low recorded test density: 9,686 LOC with only
5 test definitions (0.5/KLOC). `hummbl-mcp-governance` is lower at 0.3/KLOC.

### Tier 4 — Early (score 25–34)

| Rank | Package | Score | Tests | Source LOC |
|------|---------|-------|-------|------------|
| 27 | hummbl-compass | 34 | 15 | 864 |
| 28 | hummbl-contracts | 31 | 5 | 695 |
| 29 | hummbl-identity | 31 | 19 | 358 |
| 30 | hummbl-mcp-basen | 30 | 1 | 1,676 |
| 31 | hummbl-mcp-utf | 30 | 1 | 1,391 |
| 32 | hummbl-free-models | 29 | 5 | 1,143 |
| 33 | hummbl-rubric-templates | 29 | 12 | 628 |
| 34 | hummbl-mcp-governance | 28 | 1 | 3,845 |
| 35 | hummbl-mcp-bif | 27 | 1 | 924 |
| 36 | hummbl-mcp-omnichannel | 27 | 1 | 708 |
| 37 | hummbl-taxonomy | 27 | 4 | 204 |

### Tier 5 — Stub (score < 25)

| Rank | Package | Score | Tests | Source LOC |
|------|---------|-------|-------|------------|
| 38 | hummbl-agent-eval-harness | 24 | 3 | 160 |
| 39 | hummbl-mcp-discord | 24 | 1 | 213 |
| 40 | hummbl-mcp-onepassword | 24 | 1 | 488 |
| 41 | hummbl-mcp-proton | 24 | 1 | 391 |
| 42 | hummbl-mcp-signal | 24 | 1 | 180 |
| 43 | hummbl-mcp-voice | 24 | 1 | 328 |
| 44 | hummbl-lint-config | 21 | 1 | 9 |
| 45 | hummbl-mcp-base120 | 19 | 3 | 481 |
| 46 | hummbl-mcp-cognitive-ledger | 16 | 1 | 72 |
| 47 | hummbl-mcp-coordination-bus | 16 | 1 | 70 |

---

## Fleet-Wide Statistics

| Metric | Value |
|--------|-------|
| Total packages | 47 |
| Live on PyPI | 9 (19%) |
| Total test definitions | 7,383 |
| Total Python LOC (including tests) | 328,395 |
| Packages with ≥100 test definitions | 9 |
| Packages with exactly 1 test definition | 13 (28%) |
| Packages with `docs/` directory | 8 (17%) |
| Packages with CHANGELOG | 8 (17%) |
| stdlib-only (zero runtime deps) | 39 (83%) |

---

## Scoring Methodology

The original rubric lists six dimensions, totaling 95 points. The individual
scores above cannot be reproduced from the supplied report alone because the
per-package dimension inputs were not recorded; use the raw counts instead
of treating the scores as verified measurements.

| Dimension | Max | Thresholds |
|-----------|-----|------------|
| PyPI presence | 20 | Live = 20 |
| Version maturity | 15 | ≥3.x = 15 · ≥1.x = 10 · ≥0.5 = 7 · ≥0.2 = 5 · ≥0.1 = 3 |
| Static test count | 25 | ≥100 = 25 · ≥50 = 20 · ≥20 = 15 · ≥10 = 10 · ≥5 = 7 · ≥1 = 3 |
| Source substance | 15 | ≥5K LOC = 15 · ≥2K = 12 · ≥1K = 9 · ≥500 = 6 · ≥100 = 3 |
| Documentation | 10 | README = 5 · docs/ = 3 · CHANGELOG = 2 |
| Build infra | 10 | Lock file = 5 · stdlib-only = 5 |

Test counts were obtained by counting `def test_` and `async def test_`
function definitions in `tests/` directories. Source LOC includes all `.py`
files in the package directory tree.

---

## Observations and Recommendations

### PyPI publication candidates

| Package | Evidence | Risk |
|---------|----------|------|
| arcana | 305 tests, 12K LOC, v0.10.19, highest unpublished maturity | Name collision on PyPI |
| idp-spec | 205 tests, 5.2K LOC, unique name | Still v0.1.0 |
| hummbl-eval | 141 tests, 4.3K LOC | Still v0.1.0 |
| hummbl-gitops | 75 tests, 3.2K LOC | Still v0.1.0 |

### Test gap priorities

Selected packages with low recorded test-definition-to-LOC ratios:

| Package | LOC | Tests | Tests/KLOC |
|---------|-----|-------|------------|
| hummbl-mcp | 9,686 | 5 | 0.5 |
| hummbl-mcp-governance | 3,845 | 1 | 0.3 |
| hummbl | 4,942 | 11 | 2.2 |
| hummbl-mcp-basen | 1,676 | 1 | 0.6 |
| hummbl-mcp-utf | 1,391 | 1 | 0.7 |

### Documentation gap

Only 8 of 47 packages (17%) have a `docs/` directory and only 8 have a
CHANGELOG. All 47 have a README. The MCP shim packages (13 recorded rows) would
benefit from a shared documentation template.

### MCP shim consolidation opportunity

The 13 recorded `hummbl-mcp-*` packages average 1.15 test definitions and
828 LOC each, excluding the core `hummbl-mcp` framework. Many are thin
shims over the core `hummbl-mcp` framework. Consider whether the messaging
and channel shims (Discord, Signal, Proton, Voice) could share a common
adapter pattern to reduce the maintenance surface.
