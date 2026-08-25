# PRD: hummbl-bus v0.2.0
**Product**: hummbl-bus  
**Version**: 0.2.0  
**Date**: 2026-05-04  
**Status**: APPROVED — execute Q2 2026  
**Author**: Reuben Bowlby

---

## 1. Purpose

hummbl-bus is the HUMMBL coordination transport layer. It owns the TSV append-only bus,
signing/verification, bridge server/client for cross-machine coordination, and an MCP server
surface for agent tool access. v0.2.0 ships the first full test suite and publishes to PyPI.

---

## 2. Background

### Current state (v0.1.0)

| Module | Lines | Status |
|--------|-------|--------|
| `src/bus_writer.py` | ~300 | Production quality — no tests |
| `src/bus_verifier.py` | ~250 | Production quality — no tests |
| `src/bus_security.py` | ~200 | Production quality — no tests |
| `src/secure_tsv.py` | ~150 | Production quality — no tests |
| `src/bus_manager.py` | ~200 | Production quality — no tests |
| `src/bus_policy.py` | ~150 | Production quality — no tests |
| `src/message_signing.py` | ~200 | Production quality — no tests |
| `src/bridge_server.py` | ~300 | Novel (not in hummbl-governance) — no tests |
| `src/bridge_client.py` | ~200 | Novel (not in hummbl-governance) — no tests |
| `src/bridge_tcp_client.py` | ~150 | Novel (not in hummbl-governance) — no tests |
| `src/bus_integration.py` | ~200 | Novel — no tests |
| `src/mcp_server.py` | ~250 | Novel — no tests |
| `tests/` | `.gitkeep` | Empty |

The package was extracted from `hummbl-governance` and extended with bridge and MCP capabilities.
Business logic is complete. Gap: test coverage before public release.

### Why publish now

- `hummbl-governance` (PyPI, v0.8.0) references bus concepts in its governance audit log.
- `hummbl-crucible` trust scorer reads the TSV bus directly; a stable `hummbl-bus` API removes that coupling.
- The Chief-of-Staff always-on agent (Phase 1) requires a reliable cross-machine write path.
- `bus-global.py` on Anvil is an ad-hoc workaround; `hummbl-bus` bridge replaces it permanently.

---

## 3. Target users

| User | Need |
|------|------|
| **hummbl-crucible** | Parse and iterate over TSV bus messages via `BusReader` |
| **hummbl-clp** | Write ledger receipts to bus optionally |
| **Chief-of-Staff agent** | Post messages from Anvil to nodezero bus via bridge |
| **agentic developers** | Import `BusWriter`, `BusVerifier` to wire their own coordination |
| **MCP-enabled agents** | Call `bus_write`, `bus_read` MCP tools |

---

## 4. Requirements

### 4.1 Functional

**F-BUS-001** — `BusWriter.write(from_, to, type_, message)` appends a TSV row with ISO 8601Z
timestamp, validates all fields, and optionally appends an HMAC-SHA256 signature column.

**F-BUS-002** — `SecureTSV.encode(row)` / `SecureTSV.decode(line)` round-trip without data loss
and prevent tab/newline injection in any field.

**F-BUS-003** — `BusVerifier.verify_file(path)` reads a TSV bus file and returns an audit report:
total messages, signed messages, failed signatures, unknown senders, and anomalies.

**F-BUS-004** — `BusSecurityPolicy.check_nonce(nonce, timestamp)` rejects replayed messages
(nonce already seen within the replay window) and expired messages (timestamp > tolerance).

**F-BUS-005** — `MessageSigner.sign(payload)` → `str` produces a deterministic HMAC-SHA256 hex
signature given the same secret key and payload.

**F-BUS-006** — `BridgeServer.run(host, port)` listens for TCP connections and relays bus writes
to the canonical TSV path. Authenticated via shared token.

**F-BUS-007** — `BridgeClient.post(from_, to, type_, message)` connects to a bridge server and
delivers a signed message. Retries up to 3× with exponential backoff.

**F-BUS-008** — `BusMCPServer` exposes `bus_write` and `bus_read_tail` as MCP tools conforming
to the MCP 1.0 JSON-RPC envelope.

**F-BUS-009** — `BusPolicy` enforces allowed sender identities; unknown senders → warning logged,
message optionally rejected based on `strict_mode` flag.

**F-BUS-010** — File permissions on bus TSV are set to `0o600` (owner-only) on creation and
enforced on each write (POSIX) or skipped gracefully on Windows.

### 4.2 Non-functional

**NF-BUS-001** — Zero runtime dependencies beyond stdlib.

**NF-BUS-002** — All modules pass `ruff check` with no warnings.

**NF-BUS-003** — Test suite achieves ≥ 85% branch coverage.

**NF-BUS-004** — BusWriter is thread-safe (uses `fcntl.flock` on POSIX, `msvcrt.locking` on Windows).

**NF-BUS-005** — Bridge server tolerates connection loss without crashing; each client connection
is handled in a daemon thread.

---

## 5. Out of scope for v0.2.0

- Persistent nonce store (currently in-memory; v0.3.0 adds SQLite)
- TLS for bridge connections (v0.3.0; today uses shared-token auth over Tailscale)
- Bus compaction / rotation (v0.3.0)
- Prometheus metrics endpoint (v0.3.0)

---

## 6. Test plan

### 6.1 tests/test_bus_writer.py

| Test | Description |
|------|-------------|
| `test_write_creates_file` | First write creates TSV file with header |
| `test_write_appends_row` | Second write appends row without header |
| `test_write_tab_injection_prevented` | Tab in message field → escaped |
| `test_write_newline_injection_prevented` | Newline in message field → escaped |
| `test_write_timestamp_is_utc_z` | Timestamp column ends with Z |
| `test_write_with_signing` | Signed write → 6 columns (extra signature column) |
| `test_write_idempotent_on_same_file` | Multiple writes to same file → all rows present |
| `test_bus_writer_thread_safe` | 10 threads writing concurrently → 10 rows, no corruption |

### 6.2 tests/test_secure_tsv.py

| Test | Description |
|------|-------------|
| `test_encode_decode_roundtrip` | Normal row → encoded → decoded → identical |
| `test_encode_escapes_tab` | Tab in field → escaped |
| `test_encode_escapes_newline` | Newline in field → escaped |
| `test_decode_rejects_wrong_column_count` | TSV with 3 cols → ValueError |
| `test_empty_message_allowed` | Empty string message → encodes/decodes correctly |

### 6.3 tests/test_bus_verifier.py

| Test | Description |
|------|-------------|
| `test_verify_empty_bus` | Empty file → report with zero messages |
| `test_verify_unsigned_bus` | 5-col TSV → all messages unsigned → 0 failed signatures |
| `test_verify_signed_bus_all_valid` | 6-col TSV with valid HMAC → 0 failed |
| `test_verify_signed_bus_one_tampered` | Tampered signature → 1 failed |
| `test_verify_unknown_sender_flagged` | Unknown sender in from col → flagged in anomalies |
| `test_audit_report_structure` | Report has all expected keys |

### 6.4 tests/test_bus_security.py

| Test | Description |
|------|-------------|
| `test_new_nonce_accepted` | Fresh nonce + valid timestamp → True |
| `test_replay_nonce_rejected` | Same nonce twice → second call False |
| `test_expired_timestamp_rejected` | Timestamp > tolerance in past → False |
| `test_future_timestamp_rejected` | Timestamp > tolerance in future → False |
| `test_nonce_window_clears_old_entries` | Old nonces evicted after window expires |

### 6.5 tests/test_bridge_client.py

| Test | Description |
|------|-------------|
| `test_client_posts_to_mock_server` | HTTP mock → BridgeClient.post() → 200 |
| `test_client_retries_on_connection_error` | First call fails → client retries → eventually succeeds |
| `test_client_raises_after_max_retries` | All retries fail → BridgeError raised |
| `test_client_sends_auth_token` | Request includes Authorization header |

### 6.6 tests/test_message_signing.py

| Test | Description |
|------|-------------|
| `test_sign_deterministic` | Same inputs → same signature |
| `test_sign_different_key` | Different key → different signature |
| `test_verify_valid_signature` | Verify(sign(msg)) → True |
| `test_verify_tampered_payload` | Tamper payload → False |

---

## 7. API surface (v0.2.0 — stable public)

```python
from hummbl_bus import BusWriter, BusWriterConfig
from hummbl_bus import BusVerifier, AuditReport
from hummbl_bus import BusSecurityPolicy, BusPolicy
from hummbl_bus import SecureTSV
from hummbl_bus import MessageSigner
from hummbl_bus import BridgeClient, BridgeClientConfig
from hummbl_bus import BridgeServer, BridgeServerConfig
from hummbl_bus import BusMCPServer
```

---

## 8. CLI entry points (already in pyproject.toml)

```
hummbl-bus-writer   -- write a message to the bus
hummbl-bus-verifier -- verify a bus file and print audit report
hummbl-bus-bridge   -- start or query the bridge server
```

---

## 9. Acceptance criteria

- [ ] `pytest tests/ -v` passes with zero failures
- [ ] `pytest --cov=src --cov-report=term-missing` shows ≥ 85% branch coverage
- [ ] `ruff check src/ tests/` exits 0
- [ ] `pip install hummbl-bus==0.2.0` succeeds from PyPI
- [ ] `hummbl-bus-writer --help` exits 0
- [ ] ADR-001 written and committed

---

## 10. Risks and mitigations

| Risk | Mitigation |
|------|-----------|
| Windows msvcrt locking path differs from fcntl | Separate test fixtures for each platform; CI runs on both |
| Bridge server tests require network | Tests use `socketpair()` or mock; no external network calls |
| MCP server tests require JSON-RPC harness | Minimal inline harness (stdlib only) in test helper |
| BusPolicy sender list diverges from hummbl-crucible registry | Import canonicalize() from hummbl-crucible at policy load time |
