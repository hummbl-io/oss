# Changelog

## 0.1.0-canary.0

- Add the private, read-only Base120 Catalog v1 technical canary.
- Expose four deterministic MCP tools over local stdio.
- Support MCP `2026-07-28` discovery and per-request metadata plus the
  `2025-11-25` and `2025-06-18` initialization-based revisions.
- Validate every tool input and separate protocol errors from correctable tool
  execution errors.
- Bind generated catalog data to the canonical registry with SHA-256 provenance.
- Keep network egress, telemetry, durable writes, mutation tools, and public
  publishing disabled.
