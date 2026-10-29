# Changelog

All notable changes to **hummbl-cognition** are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- `validate_integrity` now advances the chain predecessor on every line, so one rejected
  entry no longer reports every later `previous_hash` link as broken.
- Open Brain briefings pool also reads `~/.agents/_state/briefings`, where briefing jobs write;
  `HUMMBL_BRIEFINGS_DIRS` overrides.
- `memory_search` MCP tool accepts `bibliography` as a source.

### Added
- Open Brain pools `closeouts` (secondary CLP ledgers, `HUMMBL_SECONDARY_LEDGERS`),
  `handoffs` (`HUMMBL_HANDOFF_DIRS`) and `aar` (`HUMMBL_AAR_DIRS`), searched by default.
- Scavenged cognition subsystem from hummbl-cognition (archived):
  - 48 Python modules (ledger_writer, query, boot_context, server, consolidator, indexer, retriever, models, state_manager, verified_writer, migration, schema_validator, feedback_tracker, lattice_advisor, belonging_check, hrsi_checkin, hrsi_bridge_client/server, working_memory, mcp_server, mcp_cognitive_state, mcp_working_memory, agenthub_bridge, autoresearch_bridge, research_processor, scoring_lenses, session_artifacts, surface_audit, duplicate_detector, issue_quality, issueops_harvest/receipt, startup_context, client, and 17 receipt modules)
  - sigil_forge/ subpackage (15 modules: compiler, engine, parser, IR, policy, preprocessors, receipts, retrievers, rituals, roles, critique, evals, graph, race)
  - 16 JSON Schema files for receipt validation
  - seed_registries/ and data/ directories
  - CLI entry point (__main__.py) with post, query, validate, state, boot, search, reindex commands
- pyproject.toml with hummbl-bus dependency and optional hummbl-governance extra
- Updated README, AGENTS.md, hummbl.repo.yaml to reflect actual codebase

## [v0.1.0] - 2026-06-25

### Added
- Initial governance artifact stack per HUMMBL Repo Standard v0.1.
- CODEOWNERS, CHANGELOG.md established.
