# hummbl-bus

Append-only TSV coordination bus for multi-agent systems.

[![Runtime Deps](https://img.shields.io/badge/runtime%20deps-zero-brightgreen)]()

**Tier:** 0 — Absolute Stdlib Only. Zero third-party runtime dependencies.

## What This Is

A lightweight, file-based message bus for coordinating multiple AI agents. Messages are appended to a TSV file with flock-based mutual exclusion, HMAC-SHA256 signing, and policy enforcement.

**Extraction status: IN PROGRESS** -- this repository contains the first standalone
bus extraction, but the HUMMBL internal workspace has newer bus modules that still need a drift
review before this package becomes the canonical implementation.

Latest drift snapshot:
[`docs/DRIFT_RECONCILIATION_2026-05-24.md`](docs/DRIFT_RECONCILIATION_2026-05-24.md).

## Features

- Append-only TSV message format (immutable audit trail)
- Flock-based mutual exclusion (safe concurrent writes)
- HMAC-SHA256 message signing and verification
- Bus policy enforcement (message type validation, identity validation)
- Bridge client/server for remote bus access (TCP)
- MCP server for tool-based bus interaction

## Message Format

```
timestamp_utc	from	to	type	message
2026-03-31T12:00:00Z	claude-code	*	STATUS	Health check passed
```

## Valid Message Types

PROPOSAL, ACK, STATUS, SITREP, BLOCKED, DECISION, QUESTION, MILESTONE, RECEIPT, COMPLETE, WIP_START, WIP_END, TASK_COMPLETE, HEARTBEAT, REVIEW

## Structure

```
src/
  hummbl_bus/
    bus_writer.py        # Core write path with file-lock mutex
    bus_manager.py       # Bus lifecycle management
    bus_policy.py        # Message type and identity validation
    bus_security.py      # Security enforcement
    bus_verifier.py      # Message integrity verification
    bus_integration.py   # Integration mixin for services
    message_signing.py   # HMAC-SHA256 signing
    secure_tsv.py        # Secure TSV read/write
    bridge_client.py     # Bridge client for remote bus
    bridge_server.py     # Bridge server for remote bus
    bridge_tcp_client.py # Legacy low-level TCP client
    mcp_server.py        # MCP tool interface
docs/
  protocol.md          # Bus protocol specification
  security-model.md    # Signing and verification
tests/
examples/
```

## Origin

Extracted from the HUMMBL internal workspace
`hummbl_governance/bus/`. The production HUMMBL internal bus is still the live integration
surface until this package has test coverage, drift reconciliation, and a migration
plan.

## License

MIT
