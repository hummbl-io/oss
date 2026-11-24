# Roadmap

Status: public roadmap
Last updated: 2026-11-23

## Current

- **v1.5.1** — Alpha, live on PyPI (see [docs/public-claims.md](docs/public-claims.md))
- 51 implemented governance primitives (see [PRIMITIVES.md](PRIMITIVES.md)), 7 MCP server entry points, zero third-party Core runtime dependencies
- CI-tested on Python 3.11, 3.12, 3.13, and 3.14

## Planned

- **HMAC-verified audit log append** — `AuditLog.append()` currently presence-checks the `signature` field but does not cryptographically verify it against the entry body. HMAC verification is tracked as a roadmap item. See `SECURITY.md` for current behavior.
- **Additional MCP server tool definitions** for primitives not yet exposed as MCP tools.

## Not planned

- Third-party runtime dependencies — the package will remain stdlib-only.
- Framework lock-in — the package wraps any agent framework.
