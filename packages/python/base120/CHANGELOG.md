# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [v3.1.0] - 2026-09-27

### Added
- `base120.glyph`: round-trippable image encoding of a ledger. Visual layer
  is a 6 × 20 grid (family rows, operator columns) with an order strip and a
  digest strip; machine layer is a canonical JSON payload embedded in SVG
  `<metadata>` or a PNG `iTXt` chunk. Optional HMAC-SHA256 signature with a
  32-byte key floor; unsigned glyphs carry `"signed": false`.
- `base120 glyph render` and `base120 glyph decode` CLI subcommands. Signing
  and verification read `BASE120_SIGNING_SECRET`.
- Package exports `Glyph`, `GlyphError`, `encode_glyph`, `decode_glyph`.
- Stdlib PNG writer (RGB8, `zlib` + `struct`), no new dependencies.

### Changed
- Family palette for rendered artifacts now clears the fleet design-token
  floors (pairwise CIEDE2000 >= 10, 4.5:1 contrast on the canonical
  surface). Mirrored in `hummbl-design-tokens` as `base120_families`.

## [v3.0.3] - 2026-09-21

### Changed
- Retired-name remediation: docstrings, module docs, `llms.txt`, DOCTRINE,
  and test names now say Krineia instead of VERUM (name retired 2026-05-04;
  public language is "Krineia governance receipt chain"). No behavior change.
  Historical CHANGELOG entries left as-is; the `NOTICE` trademark list is
  unchanged by design.

## [v3.0.2] - 2026-09-07

### Fixed
- Publish workflow SBOM step: cyclonedx-py 7 dropped `--outfile`; use `-o`.
  `3.0.1` was tagged but never reached PyPI (SBOM step failed after the
  wheel built).

### Changed
- Same NOTICE alignment as 3.0.1 (issue #141). `base120==3.0.0` is not yanked.

## [v3.0.1] - 2026-09-07

### Changed
- NOTICE aligned with already-public corpus (issue #141, architecture 3):
  published names, codes, definitions, and transformation families are
  Apache-2.0 Work, not a trade secret. `base120==3.0.0` is not yanked.

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
