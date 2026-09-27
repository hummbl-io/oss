# Script Lifecycle & Integration Contracts

<!-- GENERATED FILE — regenerate with `python tools/scripts/script_contracts.py`.
     Verify with `--check`; do not edit by hand. -->

Every executable script in the monorepo carries a lifecycle contract:
owner, invocation contract, source-of-truth, test or smoke path, and a
lifecycle class (`maintain`, `connect`, `productize`, `deprecate`,
`retire-candidate`). New scripts fail `script_contracts.py --check`
until they are covered here — that is the contract enforcement.

## Repository scripts

| Script | Class | Owner | Invocation | Test / smoke | Purpose | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `.github/scripts/check_license_consistency.py` | maintain | oss-maintainers | `python .github/scripts/check_license_consistency.py` | executed by .github/workflows on every PR | Check LICENSE file content against pyproject.toml license field |  |
| `.github/scripts/lock_build_env.py` | maintain | oss-maintainers | `python .github/scripts/lock_build_env.py` | executed by .github/workflows on every PR | Generate and check hash-locked build environments for packages/python/* |  |
| `packages/node/mcp-base120/scripts/check-package-boundary.mjs` | maintain | oss-maintainers | `node packages/node/mcp-base120/scripts/check-package-boundary.mjs` | not recorded | (no module docstring) |  |
| `packages/node/mcp-base120/scripts/generate-catalog.mjs` | maintain | oss-maintainers | `node packages/node/mcp-base120/scripts/generate-catalog.mjs` | not recorded | (no module docstring) |  |
| `packages/python/arcana/scripts/_gen_common.py` | maintain | arcana maintainers | `python packages/python/arcana/scripts/_gen_common.py` | arcana package test suite | Shared utilities for the generator family |  |
| `packages/python/arcana/scripts/debate_protocol.py` | maintain | arcana maintainers | `python packages/python/arcana/scripts/debate_protocol.py` | arcana package test suite | Adversarial debate protocol for ARCANA topics |  |
| `packages/python/arcana/scripts/ecosystem_contracts.py` | maintain | arcana maintainers | `python packages/python/arcana/scripts/ecosystem_contracts.py` | arcana package test suite | Cross-module contracts for ARCANA ecosystem |  |
| `packages/python/arcana/scripts/gap_analysis.py` | maintain | arcana maintainers | `python packages/python/arcana/scripts/gap_analysis.py` | arcana package test suite | Compute target-vs-actual PAIDEIA-9 gaps and attribute root causes |  |
| `packages/python/arcana/scripts/generate_agents.py` | maintain | arcana maintainers | `python packages/python/arcana/scripts/generate_agents.py` | arcana package test suite | Generate new ARCANA agent/lens profiles via local Ollama |  |
| `packages/python/arcana/scripts/generate_article_variants.py` | maintain | arcana maintainers | `python packages/python/arcana/scripts/generate_article_variants.py` | arcana package test suite | Post-process an ARCANA article.md into agent-optimized + metadata variants |  |
| `packages/python/arcana/scripts/generate_content_plan_bundle.py` | maintain | arcana maintainers | `python packages/python/arcana/scripts/generate_content_plan_bundle.py` | arcana package test suite | Generate a content plan bundle: chain paideia_plan + downstream generators |  |
| `packages/python/arcana/scripts/generate_paideia_plan.py` | maintain | arcana maintainers | `python packages/python/arcana/scripts/generate_paideia_plan.py` | arcana package test suite | Generate a PAIDEIA-9 content plan for a topic + consumer profile |  |
| `packages/python/arcana/scripts/generate_pairings.py` | maintain | arcana maintainers | `python packages/python/arcana/scripts/generate_pairings.py` | arcana package test suite | Generate lens pairings — named presets of N lenses that produce productive tension |  |
| `packages/python/arcana/scripts/generate_scenarios.py` | maintain | arcana maintainers | `python packages/python/arcana/scripts/generate_scenarios.py` | arcana package test suite | Generate paradigm scenarios per lens — 3-5 short concrete cases each lens handles well |  |
| `packages/python/arcana/scripts/generate_synthesis_variants.py` | maintain | arcana maintainers | `python packages/python/arcana/scripts/generate_synthesis_variants.py` | arcana package test suite | Generate alternative synthesist prompts |  |
| `packages/python/arcana/scripts/kstar_diagnostic.py` | maintain | arcana maintainers | `python packages/python/arcana/scripts/kstar_diagnostic.py` | arcana package test suite | K* / pairwise-similarity diagnostic for ARCANA lens outputs |  |
| `packages/python/arcana/scripts/overnight_v0.py` | maintain | arcana maintainers | `python packages/python/arcana/scripts/overnight_v0.py` | arcana package test suite | Minimal overnight ARCANA runner |  |
| `packages/python/arcana/scripts/paideia_detectors_llm.py` | maintain | arcana maintainers | `python packages/python/arcana/scripts/paideia_detectors_llm.py` | arcana package test suite | LLM-based detectors for the PAIDEIA-9 HARD axes (D, V, L) |  |
| `packages/python/arcana/scripts/print_ecosystem_manifest.py` | maintain | arcana maintainers | `python packages/python/arcana/scripts/print_ecosystem_manifest.py` | arcana package test suite | Print the canonical ARCANA sibling contract manifest as JSON |  |
| `packages/python/arcana/scripts/prompt_refiner.py` | maintain | arcana maintainers | `python packages/python/arcana/scripts/prompt_refiner.py` | arcana package test suite | Propose prompt version bumps from gap_analysis output |  |
| `packages/python/arcana/scripts/score_all.py` | maintain | arcana maintainers | `python packages/python/arcana/scripts/score_all.py` | arcana package test suite | Score every article under outputs/ and append history for drift detection |  |
| `packages/python/arcana/scripts/score_paideia.py` | maintain | arcana maintainers | `python packages/python/arcana/scripts/score_paideia.py` | arcana package test suite | Score existing content on PAIDEIA-9 axes (skeleton) |  |
| `packages/python/base120/scripts/check-python-cache.sh` | maintain | base120 maintainers | `bash packages/python/base120/scripts/check-python-cache.sh` | base120 package test suite | (no module docstring) |  |
| `packages/python/base120/scripts/extract_deterministic_results.py` | maintain | base120 maintainers | `python packages/python/base120/scripts/extract_deterministic_results.py` | base120 package test suite | Extract deterministic fields from pytest JSON report for hash comparison |  |
| `packages/python/base120/scripts/validate_registry_metadata.py` | maintain | base120 maintainers | `python packages/python/base120/scripts/validate_registry_metadata.py` | base120 package test suite | Validate that registries/fm.json changes in v1.0.x are metadata-only |  |
| `packages/python/hummbl-bus/scripts/release/normalize_sdist.py` | maintain | hummbl-bus maintainers | `python packages/python/hummbl-bus/scripts/release/normalize_sdist.py` | hummbl-bus package test suite | Rewrite a Python source distribution with deterministic archive metadata |  |
| `packages/python/hummbl-eval/scripts/check_codeql_sarif.py` | maintain | hummbl-eval maintainers | `python packages/python/hummbl-eval/scripts/check_codeql_sarif.py` | hummbl-eval package test suite | (no module docstring) |  |
| `packages/python/hummbl-eval/scripts/run_a3_canonical_tests.py` | maintain | hummbl-eval maintainers | `python packages/python/hummbl-eval/scripts/run_a3_canonical_tests.py` | hummbl-eval package test suite | A3: Canonical JSON digest comparison for opencode session data |  |
| `packages/python/hummbl-eval/scripts/validate_intel_classification.py` | maintain | hummbl-eval maintainers | `python packages/python/hummbl-eval/scripts/validate_intel_classification.py` | hummbl-eval package test suite | Validate intel_type metadata at research and coordination boundaries |  |
| `packages/python/hummbl-governance/scripts/agent_toolset_scaffold.py` | maintain | hummbl-governance maintainers | `python packages/python/hummbl-governance/scripts/agent_toolset_scaffold.py` | hummbl-governance package test suite or --help smoke | Helper to onboard the approved hummbl-governance agent toolset in any repository |  |
| `packages/python/hummbl-governance/scripts/anvil_git_signing_audit.py` | maintain | hummbl-governance maintainers | `python packages/python/hummbl-governance/scripts/anvil_git_signing_audit.py` | hummbl-governance package test suite or --help smoke | Git signing and local toolchain health audit |  |
| `packages/python/hummbl-governance/scripts/arbiter_audit.py` | maintain | hummbl-governance maintainers | `python packages/python/hummbl-governance/scripts/arbiter_audit.py` | hummbl-governance package test suite or --help smoke | Arbiter audit for CI job |  |
| `packages/python/hummbl-governance/scripts/audit-github-actions.py` | maintain | hummbl-governance maintainers | `python packages/python/hummbl-governance/scripts/audit-github-actions.py` | hummbl-governance package test suite or --help smoke | GitHub Actions workflow health and posture audit |  |
| `packages/python/hummbl-governance/scripts/build_evidence_validation_report.py` | maintain | hummbl-governance maintainers | `python packages/python/hummbl-governance/scripts/build_evidence_validation_report.py` | hummbl-governance package test suite or --help smoke | Build docs/coverage/EVIDENCE_VALIDATION.{json,md} from current matrices |  |
| `packages/python/hummbl-governance/scripts/build_wheel_from_sdist.py` | maintain | hummbl-governance maintainers | `python packages/python/hummbl-governance/scripts/build_wheel_from_sdist.py` | hummbl-governance package test suite or --help smoke | Build wheel from sdist for install-smoke CI job |  |
| `packages/python/hummbl-governance/scripts/check-dependencies.py` | maintain | hummbl-governance maintainers | `python packages/python/hummbl-governance/scripts/check-dependencies.py` | hummbl-governance package test suite or --help smoke | Dependency drift check for claim-safe repository policy |  |
| `packages/python/hummbl-governance/scripts/check_public_count_claims.py` | maintain | hummbl-governance maintainers | `python packages/python/hummbl-governance/scripts/check_public_count_claims.py` | hummbl-governance package test suite or --help smoke | Verify hard-coded primitive/package counts in public copy against ground truth |  |
| `packages/python/hummbl-governance/scripts/check_release_metadata.py` | maintain | hummbl-governance maintainers | `python packages/python/hummbl-governance/scripts/check_release_metadata.py` | hummbl-governance package test suite or --help smoke | Check current release metadata claims across public package surfaces |  |
| `packages/python/hummbl-governance/scripts/claim_drift.py` | maintain | hummbl-governance maintainers | `python packages/python/hummbl-governance/scripts/claim_drift.py` | hummbl-governance package test suite or --help smoke | Claim and documentation drift checks |  |
| `packages/python/hummbl-governance/scripts/count_coverage_rows.py` | maintain | hummbl-governance maintainers | `python packages/python/hummbl-governance/scripts/count_coverage_rows.py` | hummbl-governance package test suite or --help smoke | Authoritative row-marker counter for coverage matrices |  |
| `packages/python/hummbl-governance/scripts/coverage_ratchet.py` | maintain | hummbl-governance maintainers | `python packages/python/hummbl-governance/scripts/coverage_ratchet.py` | hummbl-governance package test suite or --help smoke | Coverage matrix ratchet gate — prevents regression in evidence validation |  |
| `packages/python/hummbl-governance/scripts/financial_pulse.py` | maintain | hummbl-governance maintainers | `python packages/python/hummbl-governance/scripts/financial_pulse.py` | hummbl-governance package test suite or --help smoke | Local usage and spend-telemetry collector for agent tooling |  |
| `packages/python/hummbl-governance/scripts/fork_upstream_preflight.py` | maintain | hummbl-governance maintainers | `python packages/python/hummbl-governance/scripts/fork_upstream_preflight.py` | hummbl-governance package test suite or --help smoke | Third-Party Fork & Upstream Contribution Protocol v0.1 — Preflight Gate |  |
| `packages/python/hummbl-governance/scripts/gap2-generate-agent-keys.py` | retire-candidate | hummbl-governance maintainers | `python packages/python/hummbl-governance/scripts/gap2-generate-agent-keys.py` | hummbl-governance package test suite or --help smoke | Gap-2: Generate GPG keys for 5 fleet agents | one-shot gap remediation script; retain for audit trail |
| `packages/python/hummbl-governance/scripts/gap5-audit-ci-pinning.py` | retire-candidate | hummbl-governance maintainers | `python packages/python/hummbl-governance/scripts/gap5-audit-ci-pinning.py` | hummbl-governance package test suite or --help smoke | Gap-5: Audit CI workflows for unpinned GitHub Actions | one-shot gap remediation script; retain for audit trail |
| `packages/python/hummbl-governance/scripts/gap5-generate-sbom.py` | retire-candidate | hummbl-governance maintainers | `python packages/python/hummbl-governance/scripts/gap5-generate-sbom.py` | hummbl-governance package test suite or --help smoke | Gap-5: Generate CycloneDX SBOM for hummbl-governance | one-shot gap remediation script; retain for audit trail |
| `packages/python/hummbl-governance/scripts/gap6-merkle-anchor.py` | retire-candidate | hummbl-governance maintainers | `python packages/python/hummbl-governance/scripts/gap6-merkle-anchor.py` | hummbl-governance package test suite or --help smoke | Gap-6: Activate Merkle anchoring on the coordination bus | one-shot gap remediation script; retain for audit trail |
| `packages/python/hummbl-governance/scripts/gap7-branch-protection-audit.py` | retire-candidate | hummbl-governance maintainers | `python packages/python/hummbl-governance/scripts/gap7-branch-protection-audit.py` | hummbl-governance package test suite or --help smoke | Gap-7: Fleet-wide branch protection audit | one-shot gap remediation script; retain for audit trail |
| `packages/python/hummbl-governance/scripts/gap7-enable-branch-protection.py` | retire-candidate | hummbl-governance maintainers | `python packages/python/hummbl-governance/scripts/gap7-enable-branch-protection.py` | hummbl-governance package test suite or --help smoke | Gap-7: Enable branch protection on unprotected repos | one-shot gap remediation script; retain for audit trail |
| `packages/python/hummbl-governance/scripts/governance-timeline.js` | maintain | hummbl-governance maintainers | `node packages/python/hummbl-governance/scripts/governance-timeline.js` | hummbl-governance package test suite or --help smoke | (no module docstring) |  |
| `packages/python/hummbl-governance/scripts/hummbl_release.py` | maintain | hummbl-governance maintainers | `python packages/python/hummbl-governance/scripts/hummbl_release.py` | hummbl-governance package test suite or --help smoke | HUMMBL CalVer Release Tool |  |
| `packages/python/hummbl-governance/scripts/install_wheel_from_sdist.py` | maintain | hummbl-governance maintainers | `python packages/python/hummbl-governance/scripts/install_wheel_from_sdist.py` | hummbl-governance package test suite or --help smoke | Install wheel built from sdist for install-smoke CI job |  |
| `packages/python/hummbl-governance/scripts/issue_pr_draft_coverage.py` | maintain | hummbl-governance maintainers | `python packages/python/hummbl-governance/scripts/issue_pr_draft_coverage.py` | hummbl-governance package test suite or --help smoke | Issue/PR draft coverage helper |  |
| `packages/python/hummbl-governance/scripts/nosec_audit.py` | maintain | hummbl-governance maintainers | `python packages/python/hummbl-governance/scripts/nosec_audit.py` | hummbl-governance package test suite or --help smoke | Audit nosec suppressions in production Python code |  |
| `packages/python/hummbl-governance/scripts/pr_census.py` | maintain | hummbl-governance maintainers | `python packages/python/hummbl-governance/scripts/pr_census.py` | hummbl-governance package test suite or --help smoke | PR census report |  |
| `packages/python/hummbl-governance/scripts/pre-push-ci-check.py` | maintain | hummbl-governance maintainers | `python packages/python/hummbl-governance/scripts/pre-push-ci-check.py` | hummbl-governance package test suite or --help smoke | Pre-push CI check — catch common CI-blocking issues before pushing |  |
| `packages/python/hummbl-governance/scripts/relabel_unresolvable_evidence.py` | maintain | hummbl-governance maintainers | `python packages/python/hummbl-governance/scripts/relabel_unresolvable_evidence.py` | hummbl-governance package test suite or --help smoke | Auto-relabel unresolvable compliance_mapper invocations in matrices |  |
| `packages/python/hummbl-governance/scripts/release_registry_freshness.py` | maintain | hummbl-governance maintainers | `python packages/python/hummbl-governance/scripts/release_registry_freshness.py` | hummbl-governance package test suite or --help smoke | Release-Registry Freshness Check |  |
| `packages/python/hummbl-governance/scripts/scan-sensitive-pre-commit.py` | maintain | hummbl-governance maintainers | `python packages/python/hummbl-governance/scripts/scan-sensitive-pre-commit.py` | hummbl-governance package test suite or --help smoke | Pre-commit hook + standalone vetting tool: scan for sensitive data |  |
| `packages/python/hummbl-governance/scripts/smoke_installed_wheel.py` | maintain | hummbl-governance maintainers | `python packages/python/hummbl-governance/scripts/smoke_installed_wheel.py` | hummbl-governance package test suite or --help smoke | Smoke-test an installed hummbl-governance wheel |  |
| `packages/python/hummbl-governance/scripts/sync-gitea-to-github.sh` | deprecate | hummbl-governance maintainers | `bash packages/python/hummbl-governance/scripts/sync-gitea-to-github.sh` | hummbl-governance package test suite or --help smoke | (no module docstring) | superseded by GitHub-native sync; retained until replacement documented |
| `packages/python/hummbl-governance/scripts/validate_authority_policy.py` | maintain | hummbl-governance maintainers | `python packages/python/hummbl-governance/scripts/validate_authority_policy.py` | hummbl-governance package test suite or --help smoke | Validate the structured authority policy (gap-9) |  |
| `packages/python/hummbl-governance/scripts/validate_coverage_matrices.py` | maintain | hummbl-governance maintainers | `python packages/python/hummbl-governance/scripts/validate_coverage_matrices.py` | hummbl-governance package test suite or --help smoke | Validate coverage matrix evidence cells for CI job |  |
| `packages/python/hummbl-governance/scripts/validate_evidence_cells.py` | maintain | hummbl-governance maintainers | `python packages/python/hummbl-governance/scripts/validate_evidence_cells.py` | hummbl-governance package test suite or --help smoke | Coverage matrix evidence-cell validator |  |
| `packages/python/hummbl-governance/scripts/validate_memory_system_registry.py` | maintain | hummbl-governance maintainers | `python packages/python/hummbl-governance/scripts/validate_memory_system_registry.py` | hummbl-governance package test suite or --help smoke | Validate the candidate Memory System Registry |  |
| `packages/python/hummbl-governance/scripts/validate_registry_paths.py` | maintain | hummbl-governance maintainers | `python packages/python/hummbl-governance/scripts/validate_registry_paths.py` | hummbl-governance package test suite or --help smoke | Validate that registry entries with exists:true actually exist on disk |  |
| `packages/python/hummbl-governance/scripts/validate_signing_identity_registry.py` | maintain | hummbl-governance maintainers | `python packages/python/hummbl-governance/scripts/validate_signing_identity_registry.py` | hummbl-governance package test suite or --help smoke | Validate the signing identity registry against its schema and policy rules |  |
| `packages/python/hummbl-governance/scripts/validation/check_pep639_license.py` | maintain | hummbl-governance maintainers | `python packages/python/hummbl-governance/scripts/validation/check_pep639_license.py` | hummbl-governance package test suite or --help smoke | Pre-flight check: validate pyproject.toml license/classifier compatibility |  |
| `packages/python/hummbl-governance/scripts/validation/check_untracked_tests.py` | maintain | hummbl-governance maintainers | `python packages/python/hummbl-governance/scripts/validation/check_untracked_tests.py` | hummbl-governance package test suite or --help smoke | Pre-flight check: fail if test files exist in the working tree but are |  |
| `packages/python/hummbl-governance/scripts/verify_batch_ci.py` | maintain | hummbl-governance maintainers | `python packages/python/hummbl-governance/scripts/verify_batch_ci.py` | hummbl-governance package test suite or --help smoke | Post-execution CI verification for batch PR operations |  |
| `packages/python/hummbl-governance/scripts/verify_ci_jobs.py` | maintain | hummbl-governance maintainers | `python packages/python/hummbl-governance/scripts/verify_ci_jobs.py` | hummbl-governance package test suite or --help smoke | Verify required CI jobs passed for ci-aggregate job |  |
| `packages/python/hummbl-tuples/scripts/audit_surface.py` | maintain | hummbl-tuples maintainers | `python packages/python/hummbl-tuples/scripts/audit_surface.py` | hummbl-tuples package test suite | Audit surface minimization validator |  |
| `packages/python/hummbl-tuples/scripts/check_case_collisions.py` | maintain | hummbl-tuples maintainers | `python packages/python/hummbl-tuples/scripts/check_case_collisions.py` | hummbl-tuples package test suite | Detect case-collision paths in the git-tracked file index |  |
| `packages/python/hummbl-tuples/scripts/check_pr_body_claims.py` | maintain | hummbl-tuples maintainers | `python packages/python/hummbl-tuples/scripts/check_pr_body_claims.py` | hummbl-tuples package test suite | Verify file references in PR bodies against the actual commit |  |
| `packages/python/hummbl-tuples/scripts/check_schema_code_consistency.py` | maintain | hummbl-tuples maintainers | `python packages/python/hummbl-tuples/scripts/check_schema_code_consistency.py` | hummbl-tuples package test suite | Schema-code consistency checker for HUMMBL tuples |  |
| `packages/python/hummbl-tuples/scripts/detect_duplicate_prs.py` | maintain | hummbl-tuples maintainers | `python packages/python/hummbl-tuples/scripts/detect_duplicate_prs.py` | hummbl-tuples package test suite | Detect duplicate or superseded PRs by branch-name pattern |  |
| `packages/python/hummbl-tuples/scripts/dynamic_registry.py` | maintain | hummbl-tuples maintainers | `python packages/python/hummbl-tuples/scripts/dynamic_registry.py` | hummbl-tuples package test suite | Dynamic schema registry server (mock) |  |
| `packages/python/hummbl-tuples/scripts/generate_multi_actor_fixtures.py` | maintain | hummbl-tuples maintainers | `python packages/python/hummbl-tuples/scripts/generate_multi_actor_fixtures.py` | hummbl-tuples package test suite | Generate multi-actor epistemic event fixtures (valid and invalid) |  |
| `packages/python/hummbl-tuples/scripts/generate_multi_actor_schemas.py` | maintain | hummbl-tuples maintainers | `python packages/python/hummbl-tuples/scripts/generate_multi_actor_schemas.py` | hummbl-tuples package test suite | Generate multi-actor epistemic event schemas |  |
| `packages/python/hummbl-tuples/scripts/migrate_to_v2.py` | retire-candidate | hummbl-tuples maintainers | `python packages/python/hummbl-tuples/scripts/migrate_to_v2.py` | hummbl-tuples package test suite | Migrate schemas and examples from TUPLES_v1 to TUPLES_v2 (layered convergence) | one-shot schema migration; re-run is meaningless post-v2 |
| `packages/python/hummbl-tuples/scripts/migrate_tuples.py` | retire-candidate | hummbl-tuples maintainers | `python packages/python/hummbl-tuples/scripts/migrate_tuples.py` | hummbl-tuples package test suite | Tuple migration CLI | one-shot data migration; re-run is meaningless post-migration |
| `packages/python/hummbl-tuples/scripts/static_registry.py` | maintain | hummbl-tuples maintainers | `python packages/python/hummbl-tuples/scripts/static_registry.py` | hummbl-tuples package test suite | Static schema registry generator |  |
| `packages/python/hummbl-tuples/scripts/trace_diff.py` | maintain | hummbl-tuples maintainers | `python packages/python/hummbl-tuples/scripts/trace_diff.py` | hummbl-tuples package test suite | Tuple trace diffing CLI for comparative analysis |  |
| `packages/python/hummbl-tuples/scripts/trace_replay.py` | maintain | hummbl-tuples maintainers | `python packages/python/hummbl-tuples/scripts/trace_replay.py` | hummbl-tuples package test suite | Trace replay debugger for governance simulation traces |  |
| `packages/python/hummbl-tuples/scripts/tuple_to_events.py` | maintain | hummbl-tuples maintainers | `python packages/python/hummbl-tuples/scripts/tuple_to_events.py` | hummbl-tuples package test suite | Convert tuple traces to structured event log formats |  |
| `packages/python/hummbl-tuples/scripts/tuples_vs_logs.py` | maintain | hummbl-tuples maintainers | `python packages/python/hummbl-tuples/scripts/tuples_vs_logs.py` | hummbl-tuples package test suite | Empirical comparison: tuples vs. untyped logs at different scales |  |
| `packages/python/hummbl-tuples/scripts/validate_multi_actor_events.py` | maintain | hummbl-tuples maintainers | `python packages/python/hummbl-tuples/scripts/validate_multi_actor_events.py` | hummbl-tuples package test suite | Validate multi-actor epistemic event tuples |  |
| `packages/python/hummbl-tuples/scripts/validate_world_model_events.py` | maintain | hummbl-tuples maintainers | `python packages/python/hummbl-tuples/scripts/validate_world_model_events.py` | hummbl-tuples package test suite | Validate world-model event tuples against their schemas |  |
| `tools/assessor-v0/verify.py` | productize | oss-maintainers | `python tools/assessor-v0/verify.py` | tools/assessor-v0/verify.py --help; pack fixtures in assessor_readme.md | Assessor Pack v0 — stdlib-only CONTRACT × DCT × EVIDENCE JSONL verifier |  |
| `tools/scripts/adoption_signals.py` | maintain | oss-maintainers | `python tools/scripts/adoption_signals.py` | co-located test_*.py where present, else --help smoke | Generate the package adoption-signals report |  |
| `tools/scripts/check_boundary_patterns.py` | maintain | oss-maintainers | `python tools/scripts/check_boundary_patterns.py` | co-located test_*.py where present, else --help smoke | Scan tracked worktree files for public/private boundary patterns |  |
| `tools/scripts/check_rights_distribution.py` | maintain | oss-maintainers | `python tools/scripts/check_rights_distribution.py` | co-located test_*.py where present, else --help smoke | Fail-closed rights/distribution invariant check |  |
| `tools/scripts/pypi_download_tracker.py` | connect | oss-maintainers | `python tools/scripts/pypi_download_tracker.py` | co-located test_*.py where present, else --help smoke | Track PyPI download stats for HUMMBL OSS packages | feeds adoption signals; integration point for product admission (oss#215) |
| `tools/scripts/script_contracts.py` | maintain | oss-maintainers | `python tools/scripts/script_contracts.py` | self-check via --check in boundary-check/CI | Generate and check the repository script lifecycle contract document | this contract's own generator/enforcer |
| `tools/scripts/validate_landing_comprehension_receipt.py` | maintain | oss-maintainers | `python tools/scripts/validate_landing_comprehension_receipt.py` | co-located test_*.py where present, else --help smoke | Validate a hummbl.io landing-page comprehension receipt |  |
| `tools/scripts/validate_product_manifests.mjs` | maintain | oss-maintainers | `node tools/scripts/validate_product_manifests.mjs` | co-located test_*.py where present, else --help smoke | (no module docstring) |  |
| `tools/scripts/validate_workflows.py` | maintain | oss-maintainers | `python tools/scripts/validate_workflows.py` | co-located test_*.py where present, else --help smoke | Validate GitHub Actions workflow files for SHA-pinning and hygiene |  |
| `tools/validate_ai_positions.py` | maintain | oss-maintainers | `python tools/validate_ai_positions.py` | co-located test file | Validate public position-document structure, not source truth or adoption |  |

## Package console entrypoints

Published `[project.scripts]` surface — the contract is the package's
pyproject entry and its package test suite; version/source-of-truth is
the package version at `packages/*/pyproject.toml`.

| Package | Script | Entrypoint |
| --- | --- | --- |
| base120 | `base120` | `base120.cli:main` |
| governed-compression | `governed-compression` | `governed_compression.cli:main` |
| hummbl-agent-eval-harness | `agent-eval` | `agent_eval_harness.cli:main` |
| hummbl-axis | `axis` | `hummbl_axis.cli:main` |
| hummbl-bif | `bif` | `bif_cli:main` |
| hummbl-bus | `hummbl-bus-bridge` | `hummbl_bus.bridge_server:run_server` |
| hummbl-bus | `hummbl-bus-cli` | `hummbl_bus.bus_writer_cli:main` |
| hummbl-bus | `hummbl-bus-verifier` | `hummbl_bus.bus_verifier:main` |
| hummbl-bus | `hummbl-bus-writer` | `hummbl_bus.bus_writer:main` |
| hummbl-cognition | `hummbl-cognition` | `hummbl_cognition.__main__:main` |
| hummbl-contracts | `hummbl-contracts` | `hummbl_contracts.__main__:main` |
| hummbl-eval | `hummbl-eval` | `hummbl_eval.cli:main` |
| hummbl-garage | `hummbl-garage` | `hummbl_garage.__main__:main` |
| hummbl-gitops | `hummbl-gitops` | `hummbl_gitops.cli:main` |
| hummbl-gitops | `hummbl-gitops-mcp` | `hummbl_gitops.mcp_server:main` |
| hummbl-governance | `hummbl-agent-monitor-mcp` | `mcp_agent_monitor:main` |
| hummbl-governance | `hummbl-compliance-mcp` | `mcp_compliance:main` |
| hummbl-governance | `hummbl-governance-mcp` | `mcp_server:main` |
| hummbl-governance | `hummbl-identity-mcp` | `mcp_identity:main` |
| hummbl-governance | `hummbl-physical-mcp` | `mcp_physical:main` |
| hummbl-governance | `hummbl-reasoning-mcp` | `mcp_reasoning:main` |
| hummbl-governance | `hummbl-sandbox-mcp` | `mcp_sandbox:main` |
| hummbl-heraldry | `hummbl-heraldry` | `hummbl_heraldry.__main__:main` |
| hummbl-lattice | `hummbl-lattice` | `hummbl_lattice.cli:main` |
| hummbl-mcp-base120 | `hummbl-mcp-base120` | `base120_mcp_server:main` |
| hummbl-mcp-bif | `hummbl-mcp-bif` | `bif_mcp_server:main` |
| hummbl-mcp-cognitive-ledger | `hummbl-mcp-cognitive-ledger` | `cognitive_ledger_mcp_server:main` |
| hummbl-mcp-coordination-bus | `hummbl-mcp-coordination-bus` | `coordination_bus_mcp_server:main` |
| hummbl-mcp-discord | `hummbl-mcp-discord` | `discord_mcp_server:main` |
| hummbl-mcp-governance | `hummbl-agent-monitor-mcp` | `governance_mcp_agent_monitor:main` |
| hummbl-mcp-governance | `hummbl-compliance-mcp` | `governance_mcp_compliance:main` |
| hummbl-mcp-governance | `hummbl-governance-mcp` | `governance_mcp_server:main` |
| hummbl-mcp-governance | `hummbl-identity-mcp` | `governance_mcp_identity:main` |
| hummbl-mcp-governance | `hummbl-physical-mcp` | `governance_mcp_physical:main` |
| hummbl-mcp-governance | `hummbl-reasoning-mcp` | `governance_mcp_reasoning:main` |
| hummbl-mcp-governance | `hummbl-sandbox-mcp` | `governance_mcp_sandbox:main` |
| hummbl-mcp-omnichannel | `hummbl-mcp-omnichannel` | `omnichannel_mcp_server:main` |
| hummbl-mcp-omnichannel | `hummbl-omnichannel-http` | `omnichannel_http_server:main` |
| hummbl-mcp-omnichannel | `hummbl-omnichannel-sync` | `omnichannel_d1_sync:main` |
| hummbl-mcp-onepassword | `hummbl-mcp-onepassword` | `onepassword_mcp_server:main` |
| hummbl-mcp-proton | `hummbl-mcp-proton` | `proton_mcp_server:main` |
| hummbl-mcp-signal | `hummbl-mcp-signal` | `signal_mcp_server:main` |
| hummbl-mcp-utf | `hummbl-mcp-utf` | `utf_mcp_server:main` |
| hummbl-mcp-voice | `hummbl-mcp-voice` | `voice_mcp_server:main` |
| hummbl-sast | `hummbl-sast` | `hummbl_sast.cli:main` |

## Workflow callers

Scripts invoked by GitHub Actions (from `.github/workflows/*.yml`):

- `boundary-check.yml` -> `tools/scripts/check_boundary_patterns.py`,
  `tools/scripts/check_rights_distribution.py`
- `ci.yml` -> `.github/scripts/check_license_consistency.py`,
  `.github/scripts/lock_build_env.py`,
  `packages/python/hummbl-governance/scripts/check_public_count_claims.py`,
  `tools/scripts/validate_product_manifests.mjs`
- `publish-pypi.yml` -> `.github/scripts/lock_build_env.py` (hash-locked
  build env; failure aborts the publish before artifacts ship)
- `pypi-download-tracker.yml` -> `tools/scripts/pypi_download_tracker.py`
  (appends `tools/data/pypi-downloads.csv`)
- `validate-workflows.yml` -> `tools/scripts/validate_workflows.py`

Failure behavior: all workflow-called scripts exit nonzero on invariant
violation; none mutate repository state except the download tracker,
whose CSV append is committed by the workflow itself.

## Integration opportunities

- `pypi_download_tracker.py` -> adoption-signal feed for product
  admission decisions (oss#215).
- `gap5-generate-sbom.py` + `lock_build_env.py` -> provenance/SBOM
  evidence chain alongside publish-pypi attestations.
- `assessor-v0` -> productize candidate: verifier contract already
  documented in `tools/assessor-v0/WHAT_THIS_PROVES.md`.
- `coverage_ratchet.py` / `validate_coverage_matrices.py` -> CI gate
  candidates once evidence-matrix format stabilizes.

## Deprecation register

Scripts marked `retire-candidate` or `deprecate` are retained for
audit trail; they are not wired into new automation and should not be
referenced by new documentation.
