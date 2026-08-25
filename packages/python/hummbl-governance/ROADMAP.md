# Roadmap

Status: public roadmap
Last updated: 2026-08-23

## Current

- **v1.4.x** — stable, on PyPI
- 34 governance primitives, 7 MCP server entry points, zero runtime dependencies
- CI-tested on Python 3.11, 3.12, 3.13

## Planned

- **HMAC-verified audit log append** — `AuditLog.append()` currently presence-checks the `signature` field but does not cryptographically verify it against the entry body. HMAC verification is tracked as a roadmap item. See `SECURITY.md` for current behavior.
- **Python 3.14 support** — will be claimed only after the CI matrix includes 3.14 and passes.
- **Additional MCP server tool definitions** for primitives not yet exposed as MCP tools.

## Not planned

- Third-party runtime dependencies — the package will remain stdlib-only.
- Framework lock-in — the package wraps any agent framework.
