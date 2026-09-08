# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.1] - 2026-09-08

### Fixed
- Published wheel omitted the `hummbl_tuples.simulation` subpackage and `governance.yml` package data — `[tool.setuptools] packages` only listed `hummbl_tuples`, so `python -m hummbl_tuples.simulation` (documented in the README) failed against the installed 0.2.0 package. (oss#145)

### Added
- Multi-actor epistemic invariants MA-1 through MA-4: `independence_class` required on events; AGENT_INFERENCE must declare `epistemic_permission`; HANDOFF_EVENT must carry `preserved_dissent`; USER_RATIFICATION cannot authorize or execute actions. Four new invalid fixtures. Harvested from standalone hummbl-tuples `f1470c1`.
- Initial public release

## [0.2.0] - 2026-06-22

### Added
- Initial release on PyPI
