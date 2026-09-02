# Changelog

All notable changes to **hummbl-bus** are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- MCP server stdio encoding: `mcp_server.py` now reconfigures `sys.stdin` and
  `sys.stdout` to UTF-8 at startup. On Windows, these default to the system
  codepage (CP1252), which corrupted non-ASCII JSON-RPC payloads (em-dashes,
  smart quotes, accented characters) via mojibake before `json.loads` ever
  saw them. The write path (`bus_writer.py`) was already UTF-8-correct; the
  corruption was upstream, at stdin decode time. The fix is a no-op on POSIX
  where stdin/stdout are already UTF-8. Added `tests/test_mcp_server.py` with
  a subprocess regression test that round-trips an em-dash through the MCP
  server and verifies no CP1252 mojibake in the bus file or read response.

### Added
- Promoted 5 bus modules from founder-mode (archived):
  - `autonomy_ladder.py` — autonomy tier labels and action validation (7 functions)
  - `bus_writer_cli.py` — CLI interface for bus writer with path resolution and signing support
  - `inference_tier.py` — inference tier classification and cost estimation (7 functions)
  - `lane_classifier.py` — foreground/background lane classification for bus messages (9 functions)
  - `work_queue.py` — task queue with push/pull/claim/complete lifecycle (TaskSpec, TaskItem, 11 functions)
- Added lazy exports in `__init__.py` for all 5 new modules (38 total exported symbols)
- Added `hummbl-bus-cli` entry point to pyproject.toml

### Deferred
- `bus_writer_core.py` (3003 lines) — needs semantic merge with existing `bus_writer.py` (1776 lines); see drift reconciliation
- `bus_writer_signing.py` — already absorbed into `bus_writer.py`

## [v0.1.0] - 2026-06-25

### Added
- Initial governance artifact stack per HUMMBL Repo Standard v0.1.
- CODEOWNERS, CHANGELOG.md established.
