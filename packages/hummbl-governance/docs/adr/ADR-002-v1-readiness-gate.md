# ADR-002 — v1.0.0 Readiness Gate

- **Status:** proposed
- **Date:** 2026-06-16
- **Decision owner:** Reuben Bowlby
- **Steward:** HUMMBL Research Institute
- **Authors:** devin (anvil)
- **Supersedes:** none
- **Superseded by:** none
- **Related:** `hummbl-governance#47` (release readiness gate), `docs/coverage/EVIDENCE_VALIDATION.md`

---

## Context

`hummbl-governance` has shipped 25 governance primitives, 7 MCP servers, and 1026 tests (current `main`). It is a healthy v0.x public package (PyPI `0.8.0`). The question is whether the codebase and its claims are defensible as a v1.0.0 release.

A v1.0.0 release in the Python ecosystem carries a conventional signal of API stability and production readiness. In the HUMMBL context, it also signals that public compliance and safety claims are evidence-backed.

## Decision

**v1.0.0 is HELD** until the gates below are closed. The package continues as `0.x` with feature and test improvements.

v1.0.0 means **both** of the following:

1. **API stability**: The public Python API (module boundaries, function signatures, class constructors, return types) is frozen and documented. Breaking changes after v1 require a v2 major bump with a migration guide.
2. **Evidence readiness**: Every public compliance or safety claim is backed by validated evidence (per ADR-001) or carries an explicit boundary disclaimer.

## Gates

### Gate A: Release surface alignment

| Item | Current state | Target for v1 | Owner |
|---|---|---|---|
| PyPI version | `0.8.0` | `1.0.0` at tag time | operator |
| GitHub release | Stale at `v0.2.0` | Aligned with PyPI | operator |
| Package classifier | `Development Status :: 3 - Alpha` | `Development Status :: 5 - Production/Stable` | operator |
| README test count | Updated to 1026 | Must match CI on tag commit | agent |
| README Python support | `3.11 - 3.13` (CI-tested) | Must match CI matrix on tag commit | agent |

### Gate B: CI and support matrix

| Item | Current state | Target for v1 | Owner |
|---|---|---|---|
| CI Python versions | 3.11, 3.12, 3.13 | Same, or add 3.14 if claimed | agent |
| Test count | 1026 passed | Stable or growing; no regressions | agent |
| Coverage target | ~80% | Maintain or improve | agent |

### Gate C: Evidence readiness (gated by ADR-001)

| Item | Current state | Target for v1 | Owner |
|---|---|---|---|
| Coverage matrices | 12 frameworks scoped, EU AI Act pilot started | All frameworks complete with validated evidence cells | agent/operator |
| EVIDENCE_VALIDATION.md | 5/198 fulfilled rows validated | 100% of "fulfilled" rows validated | agent |
| Public claim surface | Zero self-grades (per ADR-001) | Same; validated matrices may become public | operator |

### Gate D: API stability

| Item | Current state | Target for v1 | Owner |
|---|---|---|---|
| Public API surface | 25 primitives, documented in README | Frozen; `__all__` declared in every module | agent |
| Breaking change policy | None | Documented in `docs/API_STABILITY.md` | agent |
| Deprecation path | None | First deprecation warning in `0.9.x` if needed | agent |

## Non-goals for v1

v1.0.0 does **not** require:
- Third-party certifications (SOC 2, ISO 27001, etc.). These are separate engagements.
- Feature completeness for all planned primitives.
- All 12 coverage matrices to be **public**; they may remain internal until validated.

## Immediate next steps (before v1)

1. **Agent**: Close Gate A by updating README/Python support claims to match CI reality.
2. **Agent**: Draft `docs/API_STABILITY.md` with public API surface and breaking-change policy.
3. **Agent/Operator**: Close EU AI Act pilot matrix as the template for remaining frameworks.
4. **Operator**: Decide whether to add Python 3.14 to CI or explicitly defer it to post-v1.
5. **Operator**: Tag `0.9.0` after Gate A and B are closed, with a release note pointing to this ADR.

## What "hold v1" means for day-to-day work

- `main` branch continues to ship features, tests, and documentation.
- PRs are reviewed against v1 gate criteria (especially API stability and evidence readiness).
- Breaking changes are still permitted on `main` while in `0.x`, but each one resets the API stability clock.
- When all gates are green, the operator flips this ADR to `ACCEPTED` and tags `1.0.0`.
