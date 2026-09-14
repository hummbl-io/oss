# PROVENANCE — hummbl-agent-governance

- **Original repo:** https://github.com/hummbl-io/agent-governance
- **Original maintainer:** Reuben Bowlby
- **Import date:** 2026-09-09
- **Import mechanism:** File-copy only (no git history imported)
- **Known consumers:** HUMMBL fleet agent runtime safety controls
- **Release history:** Not yet published to PyPI (was v0.2.0 in standalone)
- **Why this package exists:** Provides deterministic runtime safety primitives for multi-agent AI fleets — kill switches, circuit breakers, computer-use boundaries, and audit bus integration. The `primitives` module is the core; it implements the safety controls that agent runtimes use to enforce operational boundaries.
- **Naming change:** Renamed from `agent-governance` to `hummbl-agent-governance` per oss naming convention (hummbl- prefix for all new imports).
- **Gitleaks scan:** Clean (0 hits across 20 commits).
