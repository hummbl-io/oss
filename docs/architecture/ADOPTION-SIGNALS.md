<!-- GENERATED FILE — regenerate with `python tools/scripts/adoption_signals.py`.
Verify with `--check`; do not edit by hand. -->

# Adoption signals — package activity and offering map

Data as of: 2026-08-26 (issue #215). Read-only restatement of committed
data. Download counts are **demand evidence**; priority classes and
offering fit are **assumptions** and are labeled as such.

## Canonical data sources

| Source | Role |
|--------|------|
| `tools/data/pypi-downloads.csv` | download time series collected by `pypi_download_tracker.py` |
| `docs/architecture/PACKAGES.md` | tree vs registry release state |
| `packages/**/product.json` | product-admission manifests (`product-admission-v1` schema) |
| `packages/*/pyproject.toml` | authoritative tree version |

## Package activity and release state

| Package | 30d downloads (latest) | Data points | Errors | Tree | PyPI | State |
|---------|---------------------:|------------:|-------:|------|------|-------|
| `hummbl-governance` | 1429 | 2 | 0 | 1.5.0 | 1.4.2 | live |
| `hummbl-bus` | 204 | 2 | 0 | 0.2.1 | 0.2.0 | live |
| `hummbl-cognition` | 207 | 2 | 1 | 0.1.0 | 0.1.0 | live |
| `hummbl-tuples` | 11 | 2 | 0 | 0.2.2 | 0.2.0 | live |
| `hummbl-bif` | 16 | 2 | 0 | 1.0.1 | 1.0.1 | live |
| `base120` | 210 | 2 | 1 | 3.0.3 | 3.0.2 | live |
| `governed-compression` | 12 | 2 | 0 | 0.1.0 | 0.1.0 | live |
| `hummbl` | 104 | 2 | 1 | 0.1.0 | 0.1.0 | live |
| `hummbl-kernel` | 102 | 2 | 1 | 0.1.0 | 0.1.0 | live |

Tracked for downloads: 9 packages. In-tree but untracked:
38 (see `pypi_download_tracker.py` PACKAGES list).

## Maintenance priority (ASSUMPTION — transparent heuristic, not demand)

| Package | Priority | Rationale |
|---------|----------|-----------|
| `arcana` | P3 | in-tree only; no release to maintain |
| `base120` | P1 | live with demand signal and unreleased tree changes |
| `governed-compression` | P2 | live, low signal |
| `hummbl` | P1 | live with demand signal |
| `hummbl-agent-eval-harness` | P3 | in-tree only; no release to maintain |
| `hummbl-agent-governance` | P3 | in-tree only; no release to maintain |
| `hummbl-axis` | P3 | in-tree only; no release to maintain |
| `hummbl-bif` | P2 | live, low signal |
| `hummbl-bus` | P1 | live with demand signal and unreleased tree changes |
| `hummbl-cognition` | P1 | live with demand signal |
| `hummbl-compass` | P3 | in-tree only; no release to maintain |
| `hummbl-contracts` | P3 | in-tree only; no release to maintain |
| `hummbl-design-tokens` | P3 | in-tree only; no release to maintain |
| `hummbl-eval` | P3 | in-tree only; no release to maintain |
| `hummbl-evidence` | P3 | in-tree only; no release to maintain |
| `hummbl-free-models` | P3 | in-tree only; no release to maintain |
| `hummbl-garage` | P3 | in-tree only; no release to maintain |
| `hummbl-gitops` | P3 | in-tree only; no release to maintain |
| `hummbl-governance` | P1 | live with demand signal and unreleased tree changes |
| `hummbl-heraldry` | P3 | in-tree only; no release to maintain |
| `hummbl-identity` | P3 | in-tree only; no release to maintain |
| `hummbl-intel` | P3 | in-tree only; no release to maintain |
| `hummbl-invariance` | P3 | in-tree only; no release to maintain |
| `hummbl-kernel` | P1 | live with demand signal |
| `hummbl-lattice` | P3 | in-tree only; no release to maintain |
| `hummbl-lint-config` | P3 | in-tree only; no release to maintain |
| `hummbl-mcp` | P3 | in-tree only; no release to maintain |
| `hummbl-mcp-base120` | P3 | in-tree only; no release to maintain |
| `hummbl-mcp-basen` | P3 | in-tree only; no release to maintain |
| `hummbl-mcp-bif` | P3 | in-tree only; no release to maintain |
| `hummbl-mcp-cognitive-ledger` | P3 | in-tree only; no release to maintain |
| `hummbl-mcp-coordination-bus` | P3 | in-tree only; no release to maintain |
| `hummbl-mcp-discord` | P3 | in-tree only; no release to maintain |
| `hummbl-mcp-governance` | P3 | in-tree only; no release to maintain |
| `hummbl-mcp-omnichannel` | P3 | in-tree only; no release to maintain |
| `hummbl-mcp-onepassword` | P3 | in-tree only; no release to maintain |
| `hummbl-mcp-proton` | P3 | in-tree only; no release to maintain |
| `hummbl-mcp-signal` | P3 | in-tree only; no release to maintain |
| `hummbl-mcp-utf` | P3 | in-tree only; no release to maintain |
| `hummbl-mcp-voice` | P3 | in-tree only; no release to maintain |
| `hummbl-rubric-templates` | P3 | in-tree only; no release to maintain |
| `hummbl-sast` | P3 | in-tree only; no release to maintain |
| `hummbl-taxonomy` | P3 | in-tree only; no release to maintain |
| `hummbl-tuples` | P1 | live with demand signal and unreleased tree changes |
| `hummbl-validation` | P3 | in-tree only; no release to maintain |
| `hummbl-validation-framework` | P3 | in-tree only; no release to maintain |
| `idp-spec` | P3 | in-tree only; no release to maintain |

## Offering map

Packages with a product-admission manifest (`product.json`) mapped to a
documented offering:

| Product | Source package | Lifecycle | Admission | Blockers |
|---------|---------------|-----------|-----------|----------|
| `mcp-base120` | `packages/node/mcp-base120` | technical-canary | hold | corpus-rights-reconciliation, redistributable-package-architecture, public-release-provenance, hosted-contract-parity, privacy-review |

**1 of 47 packages have product manifests.** Every other package↔offering mapping is an assumption with no
demand evidence behind it and is intentionally not asserted here.

## Evidence vs assumptions

**Evidence (from committed data):**
- Download counts per tracked package (sparse: 18 rows; treat trends as weak signal).
- Tree vs PyPI version lag per PACKAGES.md.
- Product-admission decisions and blockers per committed manifests.

**Assumptions (labeled, not evidence):**
- Priority classes above — a heuristic for attention, not measured demand.
- Any claim that a package maps to a customer offering without a
  `product.json` — no such mapping is asserted.
- Interpretation of download counts as customer demand — dogfooding and
  CI traffic are known confounders noted in `pypi_download_tracker.py`.
