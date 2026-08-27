# Gap-10: Air-Gap Capability Mapping to S9 Level 0-5 Track

**Issue:** #415 (gap-10)
**Federal standards:** DoD Zero Trust "Assume Breach" pillar, DISA STIG,
S9 Air-Gap Proof Track
**Date:** 2026-08-27
**Status:** PREP ONLY ΓÇö operator decision (2026-08-27): prep, no demo run

## 1. Purpose

This document maps existing HUMMBL air-gap capability to the S9
Air-Gap Proof Track (Level 0-5). It is the prep artifact for gap-10.
The operator chose prep-only for this phase; demo runbooks are provided
in `docs/operations/air-gap-demo-runbooks.md` for future execution.

## 2. S9 Level 0-5 track

| Level | Name | Description | HUMMBL status |
|-------|------|-------------|---------------|
| 0 | Connected | Standard internet-connected operation | ACTIVE (default) |
| 1 | Network-Restricted | Firewall rules, egress filtering | PARTIAL (Tailscale ACLs) |
| 2 | Offline Capable | All deps cached locally, no internet needed to build/test | READY (platform has local PyPI, Docker registry) |
| 3 | Air-Gapped | No network path to internet, data transfer via sneakernet | DESIGNED (platform docs, not yet deployed for governance kernel) |
| 4 | Cross-Domain | Data diode or controlled interface between domains | PLANNED (not yet implemented) |
| 5 | TEMPEST-Hardened | EM shielding, SCIF, physical security | N/A (requires physical facility) |

## 3. Existing air-gap capability inventory

### Platform repo (`platform/tools/scripts/`)

| Artifact | Type | S9 Level | Notes |
|----------|------|----------|-------|
| `test_air_gapped_environment.py` | Test | 2-3 | 33+ air-gap references, validates offline operation |
| `AIR_GAPPED_OPERATIONS.md` | Doc | 3 | Day-to-day ops for air-gapped host (Gitea, Ollama, registry) |
| `AIR_GAPPED_DEPS.md` | Doc | 2 | Dependency download strategy for offline use |
| `AIR_GAPPED_AUDIT.md` | Doc | 3 | Audit procedures for air-gapped environment |
| `AIR_GAPPED_DATA_TRANSFER.md` | Doc | 3 | Sneakernet data transfer procedures |
| `AIR_GAPPED_ISOLATION.md` | Doc | 3 | Isolation verification methodology |
| `AIR_GAPPED_CLOUD_CONNECTIVITY.md` | Doc | 4 | Cross-domain cloud connectivity patterns |
| `AIR_GAPPED_REGISTRY.md` | Doc | 2 | Local Docker registry setup |
| `AIR_GAPPED_HARDWARE_CANDIDATES.md` | Doc | 3-5 | Hardware recommendations for air-gapped hosts |
| `AIR_GAPPED_GITHUB_ACCOUNTS.md` | Doc | 3 | GitHub account strategy for air-gapped ops |
| `AIR_GAPPED_INTEL_SOURCES.md` | Doc | 3 | Intel feed strategy for offline threat intel |
| `AIR_GAPPED_ONBOARDING_EXERCISE.md` | Doc | 3 | Onboarding exercise for air-gapped environment |
| `AIR_GAPPED_OS_AND_HARDWARE_RESEARCH.md` | Doc | 3-5 | OS and hardware research for air-gapped hosts |

### provider-governance repo (`.github/workflows/`)

| Artifact | Type | S9 Level | Notes |
|----------|------|----------|-------|
| `ci-air-gapped.yml` | CI workflow | 2-3 | Air-gapped CI pipeline |
| `security-air-gapped.yml` | CI workflow | 2-3 | Air-gapped security scanning |

### hummbl-governance repo (this PR)

| Artifact | Type | S9 Level | Notes |
|----------|------|----------|-------|
| Zero runtime dependencies | Code | 2 | Stdlib-only production code ΓÇö no PyPI needed at runtime |
| `sbom.cdx.json` (gap-5) | SBOM | 2 | Component inventory for offline verification |
| `scripts/gap5-audit-ci-pinning.py` | Script | 2 | CI pinning audit (runs offline) |

## 4. Gap analysis: governance kernel integration

### What exists

- Platform has comprehensive air-gap ops docs (Level 2-3)
- provider-governance has air-gapped CI workflows (Level 2-3)
- hummbl-governance has zero runtime deps (Level 2 ready)

### What's missing

1. **Governance kernel air-gap test** ΓÇö no test verifies that
   `hummbl_governance` package imports and runs in an air-gapped
   environment (no internet, no PyPI)
2. **Level 2 demo for governance kernel** ΓÇö no documented demonstration
   that the governance kernel passes its test suite offline
3. **Level 3 demo for governance kernel** ΓÇö no documented demonstration
   on a fully air-gapped host
4. **Evidence package integration** ΓÇö air-gap test results not in the
   20-artifact evidence package (S8 #14)

### Remediation path

| Step | Action | S9 Level | Owner | Status |
|------|--------|----------|-------|--------|
| 1 | Map existing capability (this doc) | 0-5 | devin | DONE (this PR) |
| 2 | Write demo runbooks | 2-3 | devin | DONE (this PR) |
| 3 | Add governance kernel air-gap test | 2 | devin | NEXT |
| 4 | Run Level 2 demo | 2 | operator | PENDING (operator gate) |
| 5 | Run Level 3 demo | 3 | operator | PENDING (operator gate) |
| 6 | Add results to evidence package | 2-3 | devin | PENDING (after demos) |

## 5. Why governance kernel is Level 2 ready

The `hummbl-governance` package is uniquely suited for air-gapped
operation:

1. **Zero runtime dependencies** ΓÇö `dependencies = []` in pyproject.toml.
   The package uses only Python stdlib in production code. No PyPI
   access needed at runtime.
2. **Test deps are optional** ΓÇö `[test]` extras (pytest, ruff,
   cryptography) can be pre-cached via `AIR_GAPPED_DEPS.md` procedures.
3. **No network calls in production code** ΓÇö the governance primitives
   (kill switch, circuit breaker, Merkle anchor, etc.) make no HTTP
   calls. Network calls are only in scripts that interact with GitHub
   or the bus bridge.
4. **SBOM exists** (gap-5) ΓÇö component inventory available for offline
   verification.

This means the governance kernel can be installed, imported, and
exercised in a fully offline environment with only the Python stdlib
and pre-cached test dependencies.

## 6. Open question (from issue)

> Should DDIL (GAP-10) be elevated ahead of supply chain hardening
> (GAP-5/8)?

**Recommendation:** No. GAP-5 (SBOMs, pinning) and GAP-8 (baseline
linting) are prerequisites for a credible air-gap demo. An air-gapped
environment with unpinned dependencies and no SBOM is not verifiable.
The current ordering (5, 8, then 10) is correct.

## 7. Change history

| Date | Change | Author |
|------|--------|--------|
| 2026-08-27 | Initial capability mapping (gap-10 prep) | devin |
