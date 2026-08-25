# ADR-001: hummbl-bus Extraction and Bridge Protocol
**Status**: ACCEPTED  
**Date**: 2026-05-04  
**Author**: Reuben Bowlby  
**Deciders**: Reuben Bowlby

---

## Context

hummbl-bus was extracted from `hummbl-governance/bus/` (7 original modules) and extended with
bridge server/client and MCP server capabilities (6 new modules). Before publishing to PyPI,
we must decide:

1. What is the transport protocol for the bridge (TCP vs HTTP vs WebSocket)?
2. How should authentication work across machines?
3. What is the canonical bus path and how is it configured?
4. How should Windows `msvcrt` vs POSIX `fcntl` locking be handled?
5. What is the MCP server surface?

---

## Decision 1: Bridge uses HTTP/1.1 (not raw TCP, not WebSocket)

**Decision**: The bridge server exposes a minimal HTTP/1.1 API (stdlib `http.server`). No
raw TCP socket protocol, no WebSocket.

**Endpoints**:
```
POST /bus/write    -- write a message (JSON body)
GET  /bus/tail     -- return last N messages (query param n=, default 50)
GET  /health       -- liveness check
```

**Rationale**:
- `http.server` is stdlib. Raw TCP requires a custom wire protocol (framing, length prefixes).
- HTTP is debuggable with `curl`. Raw TCP is not.
- WebSocket adds complexity for a low-frequency coordination bus (<<10 msg/sec typical).
- Tailscale provides transport security; application-layer TLS is deferred to v0.3.0.

**Rejected alternatives**:
- Raw TCP (`bridge_tcp_client.py` exists as legacy — keep for compatibility but deprecate): too
  low-level, requires custom framing.
- WebSocket: overkill for async coordination bus; adds no value over HTTP polling.

---

## Decision 2: Bridge authentication — shared token via Authorization header

**Decision**: Bridge client sends `Authorization: Bearer <token>` on every request. Server
validates against a token stored in an environment variable (`HUMMBL_BUS_BRIDGE_TOKEN`).

**Token storage**:
- On Windows workstations: environment variable or a user-local token file with
  owner-only permissions.
- On Unix-like service hosts: environment variable or a service-local token file
  with owner-only permissions.

**Rationale**:
- Simplest scheme that provides authentication without a PKI.
- Token is never hardcoded — always env var or file.
- Tailscale restricts which machines can reach the bridge port; token is defense in depth.
- v0.3.0 can add mutual TLS if the threat model warrants it.

**Consequence**: Token rotation requires restarting both bridge server and clients. Acceptable
for current operational tempo.

---

## Decision 3: Canonical bus path is runtime-configurable, not hardcoded

**Decision**: Default bus path is `_state/coordination/messages.tsv` (relative to CWD).
Override via:
1. `BusWriterConfig(bus_path=...)` in Python
2. `HUMMBL_BUS_PATH` environment variable
3. `--bus <path>` CLI flag

**Rationale**:
- `hummbl-governance` uses `hummbl_governance/_state/coordination/messages.tsv`
- `hummbl-bus` used as a library might write to a different path
- Tests use `tmp_path` fixtures — no hardcoded paths in test code

**Rejected alternative**: Hardcode path at `~/.hummbl/bus.tsv`. Rejected because multi-repo
setups need per-repo buses.

---

## Decision 4: Platform-specific file locking via adapter module

**Decision**: `src/_locking.py` (private) wraps `fcntl.flock` (POSIX) and `msvcrt.locking`
(Windows) behind a `FileLock` context manager. All write paths use this single abstraction.

```python
# _locking.py
import sys

if sys.platform == "win32":
    from ._win_lock import FileLock
else:
    from ._posix_lock import FileLock
```

**Rationale**:
- `fcntl` is not available on Windows; `msvcrt` is not available on POSIX.
- A single `FileLock` class prevents every caller from implementing platform checks.
- Tests mock `FileLock` to avoid platform-specific test failures in CI.

**Consequence**: `_locking.py`, `_win_lock.py`, and `_posix_lock.py` are private (underscore
prefix) and not part of the public API.

---

## Decision 5: HMAC signing is opt-in per write, not enforced globally

**Decision**: `BusWriterConfig(sign_messages: bool = False)`. When `True`, every message gets
a 7th column with the HMAC-SHA256 signature. When `False`, the bus is a standard 5-column TSV.

**Rationale**:
- `hummbl-governance` buses written before security hardening (pre-ASI07) are 5-column and valid.
- `BusVerifier` handles both formats — it flags unsigned messages as "unsigned" not "invalid".
- Forcing signing on all writes would break existing hummbl-governance bus files on import.

**Key management**: Signing key comes from `HUMMBL_BUS_SIGNING_KEY` env var. If unset, signing
is disabled even if `sign_messages=True` (with a warning). Never hardcode a default key.

---

## Decision 6: MCP server surface — two tools only (v0.2.0)

**Decision**: `BusMCPServer` exposes exactly two MCP tools:

```json
{
  "name": "bus_write",
  "description": "Append a message to the coordination bus",
  "inputSchema": {
    "from_": "string",
    "to": "string",
    "type": "string",
    "message": "string"
  }
},
{
  "name": "bus_read_tail",
  "description": "Read the last N messages from the coordination bus",
  "inputSchema": {
    "n": "integer (default 50)",
    "from_filter": "string (optional)"
  }
}
```

**Rationale**:
- Two tools cover 90% of agent use cases (write a message, read recent context).
- More tools (bus_search, bus_verify, bus_stats) can be added in v0.3.0 without breaking
  existing tool callers.
- MCP server runs via stdio (standard MCP protocol) — no HTTP port required.

---

## Decision 7: `bridge_tcp_client.py` — retained but deprecated

**Decision**: Keep `bridge_tcp_client.py` in v0.2.0 but mark it as deprecated in docstrings.
Remove in v0.4.0.

**Rationale**:
- Legacy `bus-global.py` on Anvil uses the raw TCP path. Removing it immediately would break
  the coordination bus before the HTTP bridge is deployed and tested.
- Deprecation notice gives time to migrate.

---

## Consequences

- `hummbl-bus` has zero runtime dependencies. ✅
- Bridge is debuggable with `curl`. ✅
- Both signed and unsigned bus files are handled. ✅
- Windows and POSIX have the same behavior under `FileLock`. ✅
- Token rotation requires service restart. ⚠️
- Raw TCP bridge is deprecated — one session to migrate `bus-global.py`. ⚠️
- MCP server scope is intentionally narrow in v0.2.0. ⚠️
