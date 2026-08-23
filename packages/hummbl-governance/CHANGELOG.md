# Changelog

All notable changes to **hummbl-governance** are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added

- **HUMMBL Repo Standard v0.1** (`docs/standards/HUMMBL_REPO_STANDARD.md`) — global baseline for all `hummbl-io` repositories: 15-item artifact stack, five repo classes with required/prescribed/optional weightings, conflict-precedence ladder, provider-neutrality constraint, and routing doctrine (deterministic spine, stochastic muscle).
- **`hummbl-repo-manifest.schema.json`** (`schemas/`) — JSON Schema Draft 2020-12 for the machine-readable `hummbl.repo.yaml` registry atom. Enforces provider neutrality (`model_provider_neutral: const true`) and KRINEIA operator surface (`append`/`project`/`cut` only).
- **ADR-003** (`docs/adr/ADR-003-hummbl-repo-standard.md`) — decision record for the standard, including the live 91-repo audit findings (0% `KRINEIA.md`, 0% `hummbl.repo.yaml`, 1% `CONSTITUTION.md` coverage) and the split-home choice (canonical in `hummbl-governance`, templates mirrored in `.github`).

### Security

- **BREAKING**: `CapabilityFence.from_delegation_token()` now cryptographically
  verifies delegation tokens instead of trusting `ops_allowed` at face value.
  Previously, a tampered/forged token was silently accepted, and a token with
  an empty `ops_allowed` granted allow-all instead of deny-all. Both were
  live in `1.2.2`. Callers must now pass `token_manager`, `expected_issuer`,
  `expected_subject`, `expected_task_id`, and `expected_contract_id`; the
  method raises `ValueError`/`TypeError` on invalid or unauthenticated
  tokens.
- Fixed a second, separate unauthenticated-token path in
  `DelegationTokenManager.check_least_privilege()` that had the same root
  cause (checked `ops_allowed` without calling signature verification first).

## [1.2.2] — 2026-07-08

### Fixed

- Prepared package metadata and release surfaces for a fresh patch publication with a new package identity (`1.2.2`) so the stale `1.2.0`/`1.2.1` PyPI text can be replaced.

### Changed

- `__version__` bumped to `1.2.2` in package metadata and runtime package headers.
- `hummbl_governance/governance.yml`, kernel spec/version, and public claim surfaces aligned to `1.2.2`.
- `.github/workflows/publish.yml` keeps `skip-existing: true` for production PyPI publish retries.

## [1.2.1] — 2026-07-06

### Fixed

- Rebuilt the PyPI long description from the current README so package metadata advertises 34 implemented governance primitives and 2027 collected tests instead of the stale 1.2.0 `26` / `1032` text.
- Published metadata now matches the supported Python surface: Python 3.11, 3.12, and 3.13 only.

### Changed

- `__version__` bumped to `1.2.1`.
- `hummbl_governance/governance.yml` package metadata bumped to `1.2.1`.

## [1.2.0] — 2026-06-23

### Added

- **API server auth + CORS** — opt-in authentication and CORS for the governance API server (STD-004/007)
- **Repo naming exception policy** — governance for authorized repo naming deviations
- **Scientific grounding coordination matrix** — ecosystem-wide evidence chain documentation
- **Contestability (P31)** — new governance standard for challenging automated decisions
- **DoctrineAmendment (P38)** — new governance standard for doctrine evolution
- **Python 3.14 classifiers** — added to pyproject.toml

### Changed

- `__version__` bumped to `1.2.0`.
- Total test suite: 1032 → 1244 tests (+212).
- SECURITY.md supported-version table updated for v1.2.x line.

---

## [1.1.0] — 2026-06-14

### Added
- **Governance Kernel** — the 26th primitive. Signed receipts, identity registry, role claims, sequence enforcement, evidence grading, authority scoping, schedule tracking, and scaling-law evaluation against the HUMMBL Scaling Law Atlas (17 empirically-tested laws).
  - 12 runtime modules, 10 test files, 136 tests
  - Full CLI: `python -m hummbl_governance.kernel boot|status|health|inspect|laws|roles`
  - Portable paths via `HUMMBL_KERNEL_STATE_DIR` and `HUMMBL_KERNEL_ATLAS_DIR`

### Changed
- `__version__` bumped to `1.1.0`.
- Total test suite: 927 → 1032 tests (+105).

---

## [1.0.0] — 2026-06-03

### Added
- **API Stability Guarantee** — Formal API stability policy with SemVer compliance. All 25 primitives have stable public interfaces guaranteed through v1.x.
- **Complete Documentation** — Sphinx-based documentation with Read the Docs configuration. Full API reference, quick start guide, and examples for all 25 primitives.
- **25 Usage Examples** — Complete example scripts for every primitive in the `examples/` directory.
- **Performance Benchmarks** — Benchmark suite for core primitives (KillSwitch, CircuitBreaker, DelegationToken, AuditLog) in `benchmarks/`.
- **Quick Start README** — "Getting Started in 5 Minutes" section with 60-second install+run, Mermaid architecture diagram, and runnable examples table.

### Changed
- `__version__` bumped to `1.0.0`.
- Development status upgraded from Alpha to Production/Stable.

---

## [0.8.0] — 2026-05-04

### Added
- **`mcp_identity.py`** — MCP server exposing `AgentRegistry`, `DelegationTokenManager`, and `LamportClock` as 10 JSON-RPC tools: `identity_register`, `identity_lookup`, `identity_list`, `identity_validate`, `delegation_create`, `delegation_validate`, `delegation_check_op`, `clock_tick`, `clock_receive`, `clock_compare`.
- **`mcp_agent_monitor.py`** — MCP server exposing `BehaviorMonitor`, `ConvergenceDetector`, `GovernanceLifecycle`, and `EvolutionLineage` as 11 tools: `behavior_record`, `behavior_snapshot_baseline`, `behavior_detect_drift`, `convergence_record`, `convergence_check`, `convergence_scores`, `lifecycle_authorize`, `lifecycle_status`, `lineage_record_variant`, `lineage_get`, `lineage_drift`.
- **`mcp_reasoning.py`** — MCP server exposing `ReasoningEngine`, `SchemaValidator`, and `ContractNetManager` as tools: reasoning model/rule/prompt tools, `schema_validate`/`schema_validate_dict`, and `contract_net_announce`/`bid`/`evaluate`/`status`.
- **`mcp_physical.py`** — MCP server exposing `KinematicGovernor` and `pHRISafetyMonitor` as 6 tools: `kinematic_check_motion`, `kinematic_get_limits`, `kinematic_scaled_velocity`, `phri_check_safety`, `phri_get_config`, `phri_batch_check`.
- **4 new `[project.scripts]` entries**: `hummbl-identity-mcp`, `<private-repo>-monitor-mcp`, `hummbl-reasoning-mcp`, `hummbl-physical-mcp`.
- **143 new tests** across `test_mcp_identity.py` (34), `test_mcp_agent_monitor.py`, `test_mcp_reasoning.py`, `test_mcp_physical.py`.

### Changed
- `__version__` bumped to `0.8.0`.
- Total test suite: 784 → 927 tests (+143).
- Total MCP servers: 3 → 7.

---

## [0.7.0] — 2026-05-04

### Added
- **`mcp_server.py`** — MCP server exposing core governance primitives as 10 JSON-RPC tools: `governance_status`, `kill_switch_status`, `kill_switch_engage`, `kill_switch_disengage`, `circuit_breaker_status`, `cost_budget_check`, `cost_record_usage`, `audit_query`, `compliance_report`, `health_check`.
- **`mcp_compliance.py`** — MCP server for compliance analysis: `nist_map_controls`, `soc2_assess`, `iso_crosswalk`, `stride_analysis`, `compliance_evidence_export`.
- **`mcp_sandbox.py`** — MCP server for capability sandboxing: `sandbox_create`, `sandbox_check`, `sandbox_validate_output`, `sandbox_status`, `sandbox_destroy`.
- **`hummbl-governance-mcp`**, **`<private-repo>-mcp`**, **`hummbl-sandbox-mcp`** CLI entry points.
- **84 new tests** covering all MCP tool handlers and protocol-level JSON-RPC round-trips.

### Changed
- `__version__` bumped to `0.7.0`.
- Total test suite: 700 → 784 tests (+84).

---

## [0.6.0] — 2026-05-04

### Added
- **`generate_nist_rmf_report()`** on `ComplianceMapper` — Maps governance traces to the four NIST AI RMF core functions: GOVERN, MAP, MEASURE, MANAGE. Controls mapped: GOVERN-1.1 (risk policies, via INTENT tuples), GOVERN-1.7 (risk identification, via CB/KS events), MAP-1.1 (organisational context, via CONTRACT/DCTX/DCT), MAP-2.2 (risk assessment basis, via ATTEST/EVIDENCE), MEASURE-2.5 (trustworthiness, via signed entries), MEASURE-2.8 (impact metrics, via COST_GOVERNOR events), MANAGE-1.3 (response plans, via KILLSWITCH), MANAGE-2.4 (risk treatment, via CIRCUIT_BREAKER). Reference: NIST AI 100-1 (2023).
- **`generate_eu_ai_act_report()`** on `ComplianceMapper` — Maps governance traces to EU AI Act Articles 9, 10, 12, 13, 14, 17 (High-Risk AI, Annex III). Art.9: risk management system (CB/KS events); Art.10: data governance (ATTEST/EVIDENCE); Art.12: record-keeping (signed entries); Art.13: transparency (INTENT tuples); Art.14: human oversight (KILLSWITCH with `human_initiated` flag); Art.17: quality management (DCTX delegation chain). Reference: Regulation (EU) 2024/1689.
- CLI `--framework` flag extended with `nist-rmf` and `eu-ai-act` options.
- `CHANGELOG.md` — first changelog, covering v0.1.0 through v0.6.0.
- 36 new tests (NIST RMF: 16, EU AI Act: 16, CLI: 2, fixtures: 2). Total: 673 tests.

### Changed
- `__version__` bumped to `0.6.0`.
- `ComplianceMapper` docstring updated to list all five supported frameworks.
- `__init__.py` description line updated to include NIST AI RMF and EU AI Act.

---

## [0.5.0] — 2026-05-04

### Added
- **`EvolutionLineage`** (`evolution_lineage.py`) — In-memory lineage tracking for evolving AI agent variants. Supports variant registration, modification chains, drift detection, and provenance queries. Adds `VariantRecord`, `ModificationRecord`, `EvolutionDriftReport`. Closes the eAI governance foundation.
- **`LamportTimestamp`** export added to `__init__` alongside `LamportClock` — explicit timestamp type now part of the public API.
- CI matrix expanded to 3 OS × 3 Python versions (3.11, 3.12, 3.13) with install smoke test on each combination.
- OWASP Top 10 for Agentic Applications mapping documented in README — all 10 risks mapped to specific primitives.

### Changed
- `__version__` bumped to `0.5.0`.
- Test suite: 577 → 637 tests (+60 for EvolutionLineage). 93% overall coverage.
- Primitive count: 23 → 25 (EvolutionLineage + hardened LamportClock promoted).

---

## [0.4.0] — 2026-04-xx

### Added
- **`EAL` (Execution Assurance Layer)** (`eal.py`) — Deterministic receipt validation against declared contracts. Functions: `eal_validate`, `eal_revalidate`, `eal_compat`. Implements the AAA (Announce → Act → Attest) execution loop from the HUMMBL research paper.
- **`errors.py`** — Unified FM (Failure Mode) taxonomy with `FailureMode` enum, `HummblError` base exception, and `fm_to_errors` mapping. 21 named failure modes covering all nine CAES dimensions.
- **`failure_modes.py`** — Full failure-mode record store with `FailureModeRecord`, `ErrorRecord`, `all_failure_modes()`, `get_fm()`, `classify_subclass()`, `get_errors_for_fm()`, `all_error_records()`.
- **`physical_governor.py`** — Safety and kinematic constraints for physical AI and pHRI (physical Human-Robot Interaction). Classes: `KinematicGovernor`, `pHRISafetyMonitor`, `PhysicalSafetyMode`.
- **Governance timeline visualizer** (`data/timeline_viz.py`) — ASCII/ANSI timeline graph of governance events with `--watch` live-tail mode.
- Dependabot configuration fixed; GitHub Actions dependency pins corrected.

### Changed
- `__version__` bumped to `0.4.0`.
- Test suite: 503 → 577 tests (+74 for EAL, errors taxonomy, physical governor, timeline viz).
- `v0.4.0` PR (#16) included hardening pass: tightened thread-safety on `CircuitBreaker`, `AuditLog` rotation edge cases, `CostGovernor` ceiling enforcement under concurrent load.

---

## [0.3.0] — 2026-03-xx

### Added
- **`ReasoningEngine`** (`reasoning.py`) — Structured chain-of-thought capture and replay. `explain()` produces human-readable derivation traces; `ApplyResult` models the conclusion of a governance decision.
- **`ValidationError`** — explicitly exported from `schema_validator.py` and added to `__all__` (was previously internal-only).
- MCP (Model Context Protocol) server for governance primitives — exposes kill switch, circuit breaker, and audit log over the MCP JSON-RPC interface.
- REST API skeleton and CLI entry points (see `data/` directory).
- CI workflow (GitHub Actions), CONTRIBUTING.md, and coverage badge.
- GEO-optimized README — structured for AI assistant discoverability.
- `CODEOWNERS` file added.
- Ruff lint: all 34 findings resolved; CI now enforces lint-clean on every push.
- Code quality hardening pass (complexity reduction, dead-code removal) — quality grade D → A.

### Changed
- `__version__` bumped to `0.3.0`.
- Test suite: ~350 → 503 tests.
- Primitive count: 17 → 20 (added ReasoningEngine; OutputValidator and CapabilityFence counted individually).

---

## [0.2.0] — 2026-02-xx

### Added
- **`OutputValidator`** (`output_validator.py`) — Rule-based content validation for agent outputs. Implements OWASP ASI-06. Includes `PIIDetector`, `InjectionDetector`, `LengthBounds`, `BlocklistFilter`.
- **`CapabilityFence`** (`capability_fence.py`) — Soft sandbox enforcing capability scope boundaries per agent. Implements OWASP ASI-07. Raises `CapabilityDenied`.
- **`ContractNetManager`** (`contract_net.py`) — FIPA Contract Net protocol implementation for multi-agent task negotiation. Includes `Bid`, `TaskAnnouncement`, `ContractPhase`.
- **`ConvergenceDetector`** (`convergence_guard.py`) — Monitors multi-agent convergence toward declared goals; raises `ConvergenceAlert` on drift. Includes `ConvergentGoal`.
- **`BehaviorMonitor`** (`reward_monitor.py`) — Tracks reward signals and flags reward hacking or specification gaming. Produces `DriftReport`.

### Changed
- `__version__` bumped to `0.2.0`.
- Test suite: ~200 → 350 tests.
- Primitive count: 12 → 17.

---

## [0.1.0] — 2026-01-xx

### Added
- Initial release. Extracted from the `hummbl-governance` internal ops platform.
- Core primitives (12 modules):
  - **`KillSwitch`** — 4-mode emergency halt (DISENGAGED → HALT_NONCRITICAL → HALT_ALL → EMERGENCY).
  - **`CircuitBreaker`** — 3-state failure isolation (CLOSED → HALF_OPEN → OPEN).
  - **`CostGovernor`** — Budget tracking with soft/hard caps; ALLOW / WARN / DENY decisions.
  - **`DelegationToken`** — HMAC-SHA256 signed capability tokens with scope, expiry, and chain-depth enforcement.
  - **`AuditLog`** — Append-only JSONL governance audit log with file rotation and retention policies.
  - **`AgentRegistry`** — Configurable agent identity registry with aliases and trust tiers.
  - **`SchemaValidator`** — Stdlib-only JSON Schema validator (Draft 2020-12 subset). Zero dependencies.
  - **`BusWriter`** — Append-only TSV coordination bus with flock-based mutual exclusion and optional HMAC signing.
  - **`ComplianceMapper`** — Maps governance traces to SOC 2, GDPR, and OWASP controls; generates structured `ComplianceReport`.
  - **`HealthCollector`** — Composable health probe framework with latency tracking. Includes `HealthProbe`, `HealthReport`, `ProbeResult`.
  - **`LamportClock`** — Logical clock for causal ordering in distributed agent systems.
  - **`StrideMapper`** — STRIDE threat categorization for governance interactions. Includes `StrideReport`, `Interaction`, `ThreatFinding`.
  - **`GovernanceLifecycle`** — Request authorization lifecycle (PENDING → AUTHORIZED → DENIED → REVOKED). Includes `AuthorizationDecision`, `GovernanceStatus`.
- Interactive Google Colab demo notebook.
- Apache 2.0 license.
- Zero third-party runtime dependencies (stdlib only).

---

[0.5.0]: https://github.com/hummbl-io/hummbl-governance/releases/tag/v0.5.0
[0.4.0]: https://github.com/hummbl-io/hummbl-governance/releases/tag/v0.4.0
[0.3.0]: https://github.com/hummbl-io/hummbl-governance/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/hummbl-io/hummbl-governance/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/hummbl-io/hummbl-governance/releases/tag/v0.1.0
