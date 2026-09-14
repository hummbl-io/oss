# Review Packet: ARCANA Ecosystem Contracts

## Scope

This packet covers the current ecosystem-contract expansion work. It is meant to
make the untracked scope explicit before review, PR creation, or commit.

## Added Surfaces

- `NOMOS/`: normative standards contract surface
- `EVIDENCE/`: observability and audit contract surface
- `RELEASE/`: release gate contract surface plus read-only gate implementation
- `LINGUA/`: editorial and narrative contract surface
- `pipeline/`: compatibility package for legacy `pipeline.*` imports
- `docs/platform-set.md`: full ecosystem surface map
- `docs/ecosystem-roadmap.md`: staged ecosystem enhancement plan
- `scripts/ecosystem_contracts.py`: canonical ecosystem registry
- `scripts/print_ecosystem_manifest.py`: machine-readable manifest CLI
- `scripts/test_ecosystem_contracts.py`: contract/doc/manifest tests
- `scripts/test_pipeline_imports.py`: import-cycle smoke tests
- `scripts/test_release_gate.py`: read-only release gate tests
- `.gitignore`: nested Python cache hygiene

## Modified Surfaces

- `Makefile`: `make test` now gates pipeline imports, ecosystem contracts, and
  release gate behavior.
- `docs/README.md`: links platform map and ecosystem roadmap.
- `scripts/arcana_praxis_poiesis_crosswalk.py`: consumes canonical PRAXIS and
  POIESIS constants from `ecosystem_contracts.py`.
- `scripts/generate_paideia_plan.py`, `scripts/overnight_v0.py`,
  `scripts/score_all.py`, `scripts/score_paideia.py`: consume canonical
  PAIDEIA constants/signature helpers.
- `.gitignore`: explicitly ignores nested `__pycache__` directories.

## Validation

Run:

```bash
make test
git diff --check
python scripts/print_ecosystem_manifest.py
python -m RELEASE.gate --article <path-to-article.md>
```

Expected current local result:

- `make test`: all script suites pass
- `git diff --check`: no whitespace errors
- manifest CLI: prints JSON with `NOMOS`, `EVIDENCE`, `RELEASE`, `LINGUA`
- release gate: prints a read-only JSON receipt bundle

## Review Risks

- Large untracked scope can be missed by `git diff --stat`; use `git status
  --short` and review every untracked directory.
- `pipeline/` is intentionally included because root modules already reference
  `pipeline.*` imports.
- RELEASE gate is intentionally read-only; it must not publish or mutate source
  artifacts.

## Next Lane Split

1. Contract/schema lane: harden receipt shapes and manifest export.
2. RELEASE lane: evolve read-only gate from report-only to configurable policy.
3. PAIDEIA lane: replace remaining hard-axis stubs with evidence-backed detector
   paths while preserving v0.1 compatibility.
