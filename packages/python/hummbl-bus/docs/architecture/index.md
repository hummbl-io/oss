# Architecture

This document describes the internal architecture of hummbl-bus: the TSV message format, flock-based locking, message signing, policy enforcement, and the bridge client/server topology for cross-machine coordination.

## TSV Message Format

Every bus message is a single line of tab-separated values with exactly five columns:

```
timestamp_utc\tfrom\tto\ttype\tmessage
```

| Column | Description | Example |
|---|---|---|
| `timestamp_utc` | UTC timestamp in ISO 8601 with `Z` suffix (`YYYY-MM-DDTHH:MM:SSZ`) | `2026-06-25T14:30:00Z` |
| `from` | Sender agent identifier | `devin` |
| `to` | Recipient identifier (`all` for broadcast) | `codex` |
| `type` | Message type from the coordination taxonomy | `STATUS` |
| `message` | Message content (escaped for TSV safety) | `Task complete` |

The format is defined in `bus_writer_core.py`. The canonical line is constructed at line 1446:

```python
tsv_line = f"{timestamp}\t{from_id}\t{to_id}\t{msg_type}\t{safe_message}\n"
```

### Message Escaping

Before writing, `escape_message()` (line 136 of `bus_writer_core.py`) transforms the message content to keep it on a single line:

- Newlines (`\n`, `\r\n`, `\r`) → escaped literal `\n`
- Tabs (`\t`) → spaces

Header fields (`from_id`, `to_id`, `msg_type`) are sanitized by `_sanitize_field()` (line 222), which strips whitespace and replaces tabs and newlines similarly.

### Timestamp Normalization

`_normalize_timestamp()` (line 188) converts caller-supplied timestamps to UTC with a `Z` suffix. Timestamps with timezone offsets (e.g., `-05:00`) are converted to UTC. Sub-second precision is stripped to maintain the canonical `YYYY-MM-DDTHH:MM:SSZ` format. This prevents ordering drift when agents post local-time timestamps.

## Flock-Based Mutual Exclusion

The core guarantee of hummbl-bus is that concurrent writers never corrupt each other's entries. This is achieved through advisory file locking in `_append_tsv_line()` (line 429 of `bus_writer_core.py`):

```
┌─────────────────────────────────────────────────────────┐
│                   _append_tsv_line()                     │
│                                                         │
│  1. mkdir -p (create parent dirs)                       │
│  2. open(bus_path, "a")                                 │
│  3. fcntl.flock(f, LOCK_EX)     ← exclusive lock        │
│     ┌────────────────────────────────────────┐          │
│     │  4. write header (if new file)         │          │
│     │  5. f.write(tsv_line)                  │          │
│     │  6. f.flush()                          │          │
│     │  7. os.fsync(f.fileno())  ← durability │          │
│     └────────────────────────────────────────┘          │
│  8. fcntl.flock(f, LOCK_UN)     ← release lock          │
│  9. harden_bus_file_permissions() (if new file)         │
└─────────────────────────────────────────────────────────┘
```

On POSIX systems, `fcntl.flock(LOCK_EX)` acquires an exclusive lock on the file descriptor. Multiple processes attempting to write simultaneously block until the lock holder releases. The `f.flush()` followed by `os.fsync()` ensures the data reaches durable storage before the lock is released.

On Windows, `msvcrt.locking()` is used instead (line 449). A per-path `threading.Lock` (`_msvcrt_path_lock()`, line 42) serializes same-process writers to prevent `EDEADLK` from `msvcrt.locking` when multiple threads contend for the same byte-range lock.

### Post-Write Verification

When the `BUS_DEBUG` environment variable is set, `post_message()` performs a lightweight post-write check (line 1603): it reads the last 4 KB of the file and verifies the last line matches what was written. This is best-effort and non-fatal on failure.

## Message Signing

When a signing secret is available, `post_message()` wraps the message content in a JSON signing envelope before writing. This preserves the 5-column TSV shape while embedding a verifiable HMAC-SHA256 signature.

### Signing Flow

```
┌──────────────┐    ┌──────────────────┐    ┌─────────────────────────┐
│  post_message│───▶│ resolve secret   │───▶│ KeyManager.get_key()    │
│              │    │ (line 1355)      │    │ or BUS_SIGNING_SECRET   │
└──────────────┘    └──────────────────┘    └─────────────────────────┘
                           │                            │
                           ▼                            ▼
                    ┌──────────────┐    ┌─────────────────────────┐
                    │ policy check │    │ generate_nonce()        │
                    │ (PERMISSIVE/ │    │ sign_payload()          │
                    │  WARN/STRICT)│    │ → HMAC-SHA256           │
                    └──────────────┘    └─────────────────────────┘
                                               │
                                               ▼
                                    ┌─────────────────────────┐
                                    │ message = json.dumps({  │
                                    │   "c": content,         │
                                    │   "n": nonce,           │
                                    │   "s": signature        │
                                    │ })                      │
                                    └─────────────────────────┘
```

The signing envelope uses short keys to minimize size: `c` (content), `n` (nonce), `s` (signature). The envelope is parsed by `_parse_signing_envelope()` in `bus_writer_signing.py` (line 195).

### Verification

`verify_bus_message()` (line 228 of `bus_writer_signing.py`) reconstructs the signing payload from the TSV header columns and envelope content, then calls `verify_signature()` to check the HMAC. `read_verified_messages()` (line 87) uses this to filter out messages with invalid signatures for safety-critical consumers.

## Policy Enforcement

`BusSecurityPolicy` in `bus_policy.py` controls how unsigned messages are handled. The policy is checked in `post_message()` at line 1372 via `get_bus_policy().check_signing()`.

```
┌─────────────────┐     secret=None?     ┌──────────────────────┐
│ check_signing() │────────────────────▶│ Is msg_type exempt?  │
│ (line 80)       │                     │ (allow_unsigned_types)│
└─────────────────┘                     └──────────┬───────────┘
                                                   │
              ┌────────────────┬───────────────────┼──────────────────┐
              ▼                ▼                   ▼                  ▼
         PERMISSIVE        WARN              STRICT            Exempt type
         (no-op)           (log warning)     (raise ValueError) (no-op)
```

The default exempt type is `HEARTBEAT` (line 78 of `bus_policy.py`), since heartbeats are high-frequency and low-sensitivity. The policy level is read from the `BUS_SECURITY_POLICY` environment variable on first access via the `get_bus_policy()` singleton (line 138).

## Privileged Message Type Enforcement

Beyond the signing policy, `bus_writer_core.py` enforces role-based restrictions on privileged message types via `_validate_privileged_message_type()` (line 739):

- **`DIRECTIVE`** — human senders only (`human`, `reuben`, `dan`). All other senders are rejected.
- **`DECISION`** — human senders OR Steward proxy senders (`claude-code`, `devin`, `opencode`). Steward proxy `DECISION` posts require both an audit flag (`On-behalf-of: human`) and a citation of operator instruction in the message body.
- **Sender-specific prohibitions** — e.g., `apex` cannot post `ACK` or `VETO` (Structure A: Strategic Assessor).

Rejections are recorded to `auth_events.jsonl` via `_record_privileged_type_event()` (line 700) for forensic audit.

## Bridge Architecture

The bridge enables cross-machine coordination by exposing the bus over HTTP. One machine runs the bridge server; others post messages to it via the bridge client.

```
┌──────────────┐         HTTP POST /bus          ┌──────────────────┐
│  Machine A   │  ────────────────────────────▶  │  Machine B       │
│ (bridge_client)                                │ (bridge_server)  │
│              │  Authorization: Bearer <token>  │                  │
│  agent posts │  {"from":..., "to":...,         │  post_message()  │
│  message     │   "type":..., "message":...}    │  → local bus.tsv │
└──────────────┘                                 └──────────────────┘
                                                        │
                                                        ▼
                                               ┌──────────────────┐
                                               │  messages.tsv    │
                                               │  (append-only)   │
                                               └──────────────────┘
```

### Bridge Server (`bridge_server.py`)

The server is a `ThreadingHTTPServer` with a `BusBridgeHandler` (line 169). Key design decisions:

- **Tailscale-only binding** — by default, `run_server()` (line 506) binds to the Tailscale interface IP (`100.x.x.x`) via `get_tailscale_ip()`. Falls back to `127.0.0.1` if no Tailscale IP is found. Use `--bind-all` to bind to `0.0.0.0`.
- **Bearer token auth** — `_check_post_auth()` (line 182) uses `hmac.compare_digest()` for constant-time token comparison to prevent timing attacks. When `BUS_BRIDGE_TOKEN` is not configured, auth is disabled (and logged as `no_auth`).
- **Idempotency / replay protection** — when a `request_id` is provided, the server checks the replay ledger (`lookup_request()`) and the auth event log (`_lookup_auth_event_request()`) for duplicates. Duplicates return `{"duplicate": true}` with the original receipt.
- **Client-supplied bus_path rejection** — the server rejects any request containing a `bus_path` field (line 237) to prevent path traversal.
- **Auth event logging** — all auth outcomes (success, failure, no_auth, accepted, duplicate, rejected) are appended to `auth_events.jsonl` via `_record_auth_event()` (line 63). The token itself is never logged.

### Bridge Client (`bridge_client.py`)

The client provides several posting functions:

- `post_to_remote_bus()` (line 165) — simple boolean return
- `post_to_remote_bus_result()` (line 132) — structured result dict with `ok`, `status_code`, `duplicate`, `permanent_error`
- `post_to_remote_bus_url_result()` (line 45) — accepts a full base URL instead of host:port

The client loads the bridge token from `BUS_BRIDGE_TOKEN` env var, then from a mode-600 token file (`~/.config/foundermode/bus_bridge_token` by default, or `BUS_BRIDGE_TOKEN_FILE`). The token is sent as `Authorization: Bearer <token>`.

### Remote-First Write Mode

When `BUS_CANONICAL_BRIDGE_URL` is set, `post_message()` enters remote-first mode (line 1450 of `bus_writer_core.py`): it posts directly to the canonical bridge URL and does not fall back to a local file on transient network failure. Instead, failed writes are either dead-lettered (permanent errors) or spooled for later retry (transient errors). This ensures a single authoritative bus across machines.

## Module Dependency Graph

```
hummbl_bus/__init__.py
  ├── bus_policy.py        (BusSecurityPolicy, get_bus_policy)
  ├── secure_tsv.py        (BusMessage, SecureTSVEncoder/Decoder)  [external]
  ├── bus_verifier.py      (audit_bus, BusAuditReport)  [lazy]
  └── bus_writer.py        (post_message, signing, CLI)  [lazy]
        ├── bus_writer_core.py    (post_message, validation, locking, routing)
        ├── bus_writer_signing.py (HMAC signing, verification, permissions)
        └── bus_writer_cli.py     (CLI main)  [external]

bridge_client.py    →  urllib (HTTP POST to remote bus)
bridge_server.py    →  bus_writer.post_message + replay_ledger  [external]
bus_utils.py        →  parse_bus_line (shared parser)
```

Modules marked `[external]` are part of the broader hummbl_governance codebase that hummbl-bus is extracted from. The package is designed to work as a slice of that system while maintaining stdlib-only operation for the core write path.
