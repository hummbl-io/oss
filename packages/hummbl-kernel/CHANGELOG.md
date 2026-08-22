# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- (placeholder for upcoming changes)

## [0.1.0] - 2026-08-22

### Added
- Initial PyPI release of the hummbl-kernel package
- `MissionModeKernel` class with `async execute_workflow()` — Conductor-style YAML workflow orchestration
- Capability admission policy (`security/capability_admission_policy.py`) — grant validation, escalation prevention, secret redaction
- Fleet health checker (`fleet/fleet_health_checker.py`) — health monitoring, task routing, fallback
- Audit trail persistence (`audit/file_persistence.py`) — immutable, chain of custody
- Adapter interface for satellite registration (`adapters/`)
- Workflow schema definitions (`workflows/`)
- Zero runtime dependencies (stdlib-only)
- Optional `[reasoning]` extra for hummbl integration (plans, hypotheses, evaluations as kernel inputs)
- Apache-2.0 license
- 70 tests passing

### Designation
- Designated as the HUMMBL fleet's runtime kernel per ADR-004
- `hummbl-io/hummbl` remains the reasoning library; kernel consumes it via the `[reasoning]` extra
- First satellite consumer: `hummbl-bus` (PR #53)
