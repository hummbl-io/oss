# Repository Scripts Lifecycle and Integration Contract

**Specification Version**: `hummbl.repository-scripts.v1`  
**Governing Issue**: `hummbl-io/oss#214`  
**Schema Definition**: [`schemas/public/repository-scripts-contract-v1.schema.json`](../../schemas/public/repository-scripts-contract-v1.schema.json)  
**Machine-Readable Inventory**: [`tools/scripts-inventory.json`](../../tools/scripts-inventory.json)  
**Automated Validator**: [`tools/scripts/check_scripts_inventory.py`](../../tools/scripts/check_scripts_inventory.py)

---

## 1. Purpose & System Boundaries

Automation scripts within `hummbl-io/oss` enforce security boundaries, validate monorepo integrity, guard package release pipelines, and compute open-source adoption signals.

To prevent unmaintained script drift, fragile workflow coupling, or unredacted operational leaks, every repository script must satisfy:
1. An explicit lifecycle classification (`maintain`, `connect`, `productize`, `deprecate`, `retire`).
2. An unambiguous owner and invocation contract.
3. Explicit failure behaviors and exit code definitions.
4. Bounded system interactions (zero network egress by default, strict file isolation).
5. A deterministic automated test or smoke execution path.

---

## 2. Lifecycle Classifications

| Classification | Meaning | Entrance Criteria | Exit / Transition Gate |
|---|---|---|---|
| `maintain` | Actively supported repository automation. | Required by CI, release, or compliance; has dedicated unit tests and maintainer. | Deprecated when superseded by upstream or monorepo tools. |
| `connect` | Telemetry or ingestion bridges feeding broader systems. | Feeds package adoption, claim honesty, or multi-fleet signals; documented integration hook. | Productized when packaged into an installable CLI. |
| `productize` | High-value capability candidate for standalone package export. | Mature domain logic, stable API, minimal external coupling. | Migrated to `packages/python/<name>/` or CLI toolset. |
| `deprecate` | Obsolete or duplicate tooling marked for phase-out. | Superseded by standard monorepo tooling or newer contracts; callers time-bounded. | Retired after all callers migrate (max 1 release cycle). |
| `retire` | Slated for deletion. | Zero active callers in workflows or scripts; safe-delete confirmed. | File removed from repository tree. |

---

## 3. Invocation Standards & Exit Codes

All maintained scripts must adhere to standard exit code semantics:

- **`0` (Success)**: Verification passed, operation completed cleanly.
- **`1` (Check Failure)**: Deterministic policy violation, schema mismatch, unpinned dependency, or security failure.
- **`2` (Usage / Input Error)**: Invalid CLI arguments, missing input files, unparseable JSON/YAML.

### Security Invariants
- **Zero Network Egress**: Unless classified as `connect` with explicit network needs (e.g. `pypi_download_tracker.py`), scripts must execute hermetically offline.
- **Secret & Boundary Protection**: Scripts must never log, process, or emit unredacted secrets, internal hostnames, or private IP addresses.
- **Deterministic Runs**: Scripts must not rely on wall-clock nondeterminism or unordered filesystem traversals.

---

## 4. Current Inventory Matrix

| Path | Classification | Owner | Test Path | Primary Caller / Hook |
|---|---|---|---|---|
| `.github/scripts/check_license_consistency.py` | `maintain` | `governance` | `ci.yml` (`check-licenses`) | CI license gate |
| `.github/scripts/lock_build_env.py` | `maintain` | `release-engineering` | `ci.yml` & `publish-pypi.yml` | Hermetic build check |
| `tools/assessor-v0/verify.py` | `productize` | `governance` | Fixture smoke test | Governance CLI packaging |
| `tools/validate_ai_positions.py` | `maintain` | `research-ethics` | `tools/test_validate_ai_positions.py` | Position whitepaper gate |
| `tools/scripts/check_boundary_patterns.py` | `maintain` | `security-architecture` | `test_check_boundary_patterns.py` | `boundary-check.yml` |
| `tools/scripts/check_rights_distribution.py` | `maintain` | `compliance` | `test_check_rights_distribution.py` | `boundary-check.yml` |
| `tools/scripts/check_scripts_inventory.py` | `maintain` | `architecture` | `test_check_scripts_inventory.py` | `validate-workflows.yml` |
| `tools/scripts/pypi_download_tracker.py` | `connect` | `developer-relations` | `pypi-download-tracker.yml` | Adoption signal telemetry (Issue #215) |
| `tools/scripts/validate_landing_comprehension_receipt.py` | `maintain` | `operations` | `test_validate_landing_comprehension_receipt.py` | Landing page gate |
| `tools/scripts/validate_product_manifests.mjs` | `maintain` | `product` | `test_validate_product_manifests.mjs` | Product Admission v1 |
| `tools/scripts/validate_workflows.py` | `maintain` | `ci-cd` | `test_validate_workflows.py` | Action SHA-pinning gate |
| `packages/python/hummbl-governance/scripts/check_public_count_claims.py` | `connect` | `governance` | `ci.yml` (`verify-claims`) | Claim Honesty Protocol |
| `packages/python/hummbl-bus/scripts/release/normalize_sdist.py` | `maintain` | `release-engineering` | `publish-pypi.yml` | Reproducible PyPI dists |
| `packages/python/base120/scripts/extract_deterministic_results.py` | `connect` | `base120` | `packages/python/base120/tests/` | Golden eval fixtures |
| `packages/python/hummbl-tuples/scripts/check_schema_code_consistency.py` | `maintain` | `tuples` | `packages/python/hummbl-tuples/tests/` | Protocol contract sync |

---

## 5. Integration Hooks

1. **Package Release Integration**:
   - `lock_build_env.py` and `normalize_sdist.py` directly guarantee that PyPI release artifacts published via `.github/workflows/publish-pypi.yml` are byte-reproducible and locked to tested dependency manifests.
2. **Product Admission Gate**:
   - `validate_product_manifests.mjs` and `check_rights_distribution.py` guard `schemas/public/product-admission-v1.schema.json`, ensuring every published product declares explicit license, distribution policy, and local execution mode boundaries.
3. **Adoption & Offering Prioritization (Issue #215 & #216)**:
   - `pypi_download_tracker.py` populates `tools/data/pypi-downloads.csv`, supplying empirical download volume and velocity data to inform open-source vs. commercial packaging decisions.
4. **Automated Enforcement**:
   - `check_scripts_inventory.py` runs on every pull request touching workflows or tooling, ensuring any new script addition is immediately cataloged with complete lifecycle metadata.
