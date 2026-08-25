# hummbl-bus Documentation

> **Extraction warning:** this documentation set contains target-state and
> hummbl-governance-derived behavior that is not yet present in the standalone
> package. Do not treat feature descriptions below as a production cutover
> contract. Start with the [Phase −1 evidence report](research/PHASE_MINUS1_EVIDENCE_AND_GAPS_2026-08-08.md),
> [program plan](program/PHASE_MINUS1_0_1_PROGRAM.md), and
> [versioning plan](architecture/VERSIONING_AND_COMPATIBILITY_PLAN.md).

**HUMMBL coordination bus** — append-only TSV messaging with `flock`-based mutual exclusion, HMAC signing, configurable security policy enforcement, and an HTTP bridge for cross-machine coordination.

hummbl-bus is a stdlib-only Python package (no third-party dependencies) that provides a coordination bus for multi-agent systems. Every message is a single line of tab-separated values appended to a shared file. Mutual exclusion is enforced via `fcntl.flock(LOCK_EX)` on POSIX (or `msvcrt.locking` on Windows), so concurrent writers from multiple processes, languages, and machines never corrupt each other's entries.

## Key Features

- **Append-only TSV bus** — 5-column format: `timestamp_utc`, `from`, `to`, `type`, `message`. One line per message, fsync'd on every write.
- **`flock`-based mutual exclusion** — exclusive file locking guarantees atomic appends across processes and agents.
- **HMAC-SHA256 message signing** — opt-in signing wraps the message column in a JSON envelope `{"c":..., "n":..., "s":...}` that preserves the 5-column TSV shape while embedding a verifiable signature and nonce.
- **Configurable security policy** — `PERMISSIVE`, `WARN`, and `STRICT` enforcement levels for unsigned message handling, controlled by the `BUS_SECURITY_POLICY` environment variable.
- **Base64 injection protection** — `SecureTSVEncoder` / `SecureTSVDecoder` base64-encode payloads to prevent TSV column-injection attacks.
- **Bus integrity audit** — `audit_bus()` scans the bus file for signing coverage, duplicate nonces (replay indicators), unknown senders, and timestamp anomalies.
- **HTTP bridge** — `bridge_server.py` exposes a REST endpoint for cross-machine message posting; `bridge_client.py` sends messages to a remote bus. Bearer-token auth with constant-time comparison, Tailscale-only binding by default.
- **Privileged message type enforcement** — `DIRECTIVE` is human-only; `DECISION` accepts human senders or Steward proxy agents (claude-code, devin, opencode) with required audit markers.
- **Dead-letter queue** — failed bus operations are preserved as JSONL records for later replay.

## Documentation Sections

| Section | Description |
|---|---|
| [Getting Started](getting-started/index.md) | Installation, first message, CLI usage, reading bus messages |
| [Architecture](architecture/index.md) | TSV format, flock locking, signing, policy enforcement, bridge topology |
| [API Reference](reference/api-reference.md) | Complete Python API: every public function, class, and constant |
| [Security](security/index.md) | ASI07 hardening, HMAC signing, policy levels, injection protection, threat model |
| [CLI Reference](cli/index.md) | Full command-line interface for bus writer, verifier, and bridge |
| [Configuration](configuration/index.md) | All environment variables with types, defaults, and valid values |
| [Examples](examples/index.md) | Signed/unsigned messages, policy scenarios, bridge setup, multi-agent patterns |
| [Integrations](integrations/index.md) | Embedding the bus in agents, consuming messages, cross-machine bridge |
| [Troubleshooting](troubleshooting/index.md) | Common issues with causes and fixes |
| [Phase −1/0/1 program](program/PHASE_MINUS1_0_1_PROGRAM.md) | Evidence freeze, contract design, and implementation-ready planning gates |
| [Versioning plan](architecture/VERSIONING_AND_COMPATIBILITY_PLAN.md) | Parallel package, wire, schema, bridge, delivery, configuration, and deployment versions |
| [First-principles proposal](architecture/FIRST_PRINCIPLES_PROPOSAL.md) | Proposed invariants and operational whether-tests; not adopted doctrine |

## Quick Start

```bash
pip install hummbl-bus
```

Post a message from Python:

```python
from hummbl_bus.bus_writer import post_message

post_message(
    "/path/to/messages.tsv",
    from_id="devin",
    to_id="all",
    msg_type="STATUS",
    message="Hello from hummbl-bus!",
)
```

Post a message from the CLI:

```bash
python -m hummbl_bus.bus_writer devin all STATUS "Hello world"
```

## Package Layout

```
hummbl_bus/
  __init__.py              Package exports with lazy loading
  bus_writer.py            Re-export facade (backward compat)
  bus_writer_core.py       Core: post_message, validation, flock locking, routing
  bus_writer_signing.py    HMAC signing, verification, nonce, permission hardening
  bus_policy.py            BusSecurityPolicy: PERMISSIVE / WARN / STRICT
  bus_verifier.py          audit_bus(), BusAuditReport, CLI audit tool
  bus_utils.py             parse_bus_line() shared TSV parser
  bridge_client.py         HTTP client for remote bus posting
  bridge_server.py         HTTP server receiving cross-machine bus messages
```

## License

Apache-2.0
