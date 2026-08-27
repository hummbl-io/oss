# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- (placeholder for upcoming changes)

## [v3.0.0] - 2026-08-20

### Note
- **Release-identity reconciliation.** PyPI 3.0.0 was published from a source
  tree that predates the oss monorepo consolidation. The canonical source is
  now `oss/main` (this repo). Version 3.0.0 on PyPI is retained for
  compatibility with existing consumers; future releases will be cut from
  `oss/main` with tag `python/base120/v*`.
- No functional changes from 2.0.0; the major bump reflects the repository
  migration to the oss monorepo as the canonical home.

## [v2.0.0] - 2026-08-17

### Changed
- Repository migration: base120 now lives in `hummbl-io/oss` monorepo
  under `packages/python/base120/`.
- License clarified to Apache-2.0 with LICENSE and NOTICE files.
- Python 3.11+ floor enforced.

### Added
- PyPI discovery metadata (classifiers, project_urls).
- CI test-gate in publish workflow.

## [v1.0.0] - 2026-06-14

### Added
- 120 named mental models for structured reasoning
- 6 cognitive transformation families (P, IN, CO, DE, RE, SY)
- Stdlib-only Python SDK (zero runtime dependencies)
- CLI tooling for operator lookup and prompting
- Append-only ledger for VERUM-aligned records
- MCP integration for AI agent access
- Canonical registry and corpus documentation
