# ARCANA Platform Set

This is the full module surface currently visible in this repository, plus a
disciplined expansion path for siblings that are now authorized.

## Current Set (implemented in this repo)

## 1) ARCANA Core

- `cli.py`
- `api_client.py`
- `models.py`
- `ollama_client.py`
- `scripts/overnight_v0.py`
- `scripts/arcana_praxis_poiesis_crosswalk.py`
- `scripts/ecosystem_contracts.py`
- `scripts/test_ecosystem_contracts.py`
- `scripts/print_ecosystem_manifest.py`

Responsibilities:
- multi-agent orchestration (rationale + synthesis path)
- article model contracts and governance receipts
- run-time CLI for article generation and review workflow
- shared ecosystem constants for ARCANA/PRAXIS/POIESIS/PAIDEIA contracts

## 2) Sibling: PRAXIS

- `PRAXIS/README.md`
- `PRAXIS/` directory is authorized as active sibling surface for enacted
  governance archetypes.

Responsibilities:
- enacted governance archetypes (lenses like `mond`, `aurelius`, `cincinnatus`, etc.)
- counterpart to ARCANA's theoretical layer

## 3) Sibling: POIESIS

- `POIESIS/README.md`
- `POIESIS/` directory is authorized as active sibling surface for production
  staging archetypes.

Responsibilities:
- production/staging sequence archetypes (`seed`, `demiurge`, `crucible`, `loom`, `threshold`)
- coordination and release-shaping lens for ARCANA outputs

## 4) Sibling: PAIDEIA

- `docs/paideia-9.md`
- `docs/paideia-9-v0.2-draft.md`
- `docs/llm-content-templates.md`
- `scripts/generate_paideia_plan.py`
- `scripts/score_paideia.py`
- `scripts/score_all.py`
- `scripts/paideia_detectors_llm.py`
- `scripts/paideia/`

Responsibilities:
- 9-axis quality contract
- scoring and style diagnostics
- generation and scoring feedback loop

## 5) Generator Family / Content Ops

- `docs/generator-family.md`
- `scripts/generate_topics.py`
- `scripts/generate_agents.py`
- `scripts/generate_pairings.py`
- `scripts/generate_synthesis_variants.py`
- `scripts/generate_scenarios.py`
- `scripts/generate_article_variants.py`
- `scripts/generate_llms_txt.py`
- `scripts/analyze_logs.py`, `scripts/migrate_logs.py`
- prompts in `scripts/prompts/`
- staged outputs/logs in `scripts/*/*.json` and `scripts/*/*.tsv`

Responsibilities:
- structured generator pattern
- staged merge workflows
- telemetry for acceptance/rejection quality

## 6) Compatibility + Runtime Facades

- `pipeline/__init__.py`
- `pipeline/api_client.py`
- `pipeline/cli.py`
- `pipeline/models.py`
- `pipeline/governance.py`
- `pipeline/renderer.py`
- `pipeline/ollama_client.py`

Responsibilities:
- legacy import compatibility (`pipeline.*`) while preserving `api_client.py`/`models.py`
- review-state and rendering helpers used by the runtime CLI

## 7) Sibling Surface Expansion

- `NOMOS/README.md`
- `NOMOS/contracts.py`
- `EVIDENCE/README.md`
- `EVIDENCE/contracts.py`
- `RELEASE/README.md`
- `RELEASE/contracts.py`
- `RELEASE/gate.py`
- `LINGUA/README.md`
- `LINGUA/contracts.py`

Responsibilities:
- policy and compliance mapping (NIST AI RMF, EU AI Act, ISO 42001)
- evidence capture, drift telemetry, and audit indexing
- release gating and rollout authorization
- read-only release receipt bundles before publication automation
- editorial variant governance, citation safety, and style constraints

## 8) Missing but expected sibling layers (roadmap)

These remain intentionally out of scope in this phase:

- `SYNTHESIS` (runtime orchestration surface)
- `CANON` (public artifact registry and policy baseline mirror)

## Full-set check

If you want the above set to be complete and unambiguous, keep these three as the
ground truth:

- Platform core + runtime should remain minimal and fully testable.
- Every sibling module should own one sharp concern and expose a versioned contract.
- Any new sibling must include:
  - a README with module purpose and boundary
  - a compatibility surface (if any) that is explicit about what can be imported
  - a test scaffold that proves contract shape and critical invariants
