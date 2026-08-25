# Security

This is the definitive security documentation for hummbl-bus. It covers every security feature in detail: ASI07 hardening, HMAC message signing, the PERMISSIVE/WARN/STRICT policy enforcement model, base64 injection protection, secret management, file permission hardening, bridge authentication, privileged message type enforcement, and the threat model.

## ASI07: Insecure Inter-Agent Communication

hummbl-bus was hardened against **OWASP Agentic Top 10 — ASI07 (Insecure Inter-Agent Communication)**. The hardening was implemented as a multi-layer defense:

1. **HMAC-SHA256 message signing** — verifiable integrity for every message
2. **Configurable security policy** — gradual rollout from permissive to strict
3. **File permission hardening** — restrictive `0o660` mode on bus files
4. **Verified message reading** — safety-critical consumers can reject unsigned/tampered messages
5. **Integrity audit tooling** — `audit_bus()` for continuous compliance monitoring

The ASI07 hardening is documented in the module docstrings of `bus_writer.py` (line 7), `bus_writer_signing.py` (line 3), and `bus_policy.py` (line 1).

## HMAC-SHA256 Message Signing

### How Signing Works

When a signing secret is available, `post_message()` wraps the message content in a JSON signing envelope before writing to the bus. The signing logic is in `bus_writer_core.py` lines 1424–1436:

```python
if secret is not None:
    from .bus_security import generate_nonce
    from .message_signing import sign_payload

    nonce = generate_nonce()
    signing_payload = {"message": message}
    signature = sign_payload(
        secret, timestamp, from_id, to_id, msg_type, signing_payload, nonce
    )
    message = json.dumps(
        {"c": message, "n": nonce, "s": signature}, separators=(",", ":")
    )
```

The envelope uses short keys to minimize size:

| Key | Meaning | Content |
|---|---|---|
| `c` | content | The original message text |
| `n` | nonce | A unique nonce (timestamp + random) for replay protection |
| `s` | signature | HMAC-SHA256 hex digest (64 characters) |

The signature is computed over the TSV header columns (`timestamp`, `from_id`, `to_id`, `msg_type`) and the signing payload (`{"message": content}`) with the nonce. This binds the signature to the full message context — an attacker cannot move a signed message to a different timestamp or sender without invalidating the signature.

### Why the Envelope Preserves TSV Shape

The signed envelope is a JSON string written into the 5th TSV column (`message`). Because JSON strings do not contain literal tabs or newlines (they use `\t` and `\n` escape sequences), the envelope stays on a single TSV line. The `escape_message()` function (line 136) further ensures this by converting any literal newlines to `\n` and tabs to spaces.

### Secret Resolution Priority

`post_message()` resolves the signing secret with a priority chain (line 1355):

1. **Explicit `secret=` parameter** — if the caller passes a secret, it is used directly
2. **Per-agent KeyManager** — `KeyManager().get_key(base_identity)` for agent-specific keys
3. **Shared `BUS_SIGNING_SECRET` environment variable** — `_resolve_signing_secret()` (line 33 of `bus_writer_signing.py`)

The `BUS_SIGNING_SECRET` must be at least 32 bytes. If it is shorter, a warning is logged and messages are **not** auto-signed (line 49):

```python
if len(secret_bytes) < 32:
    logger.warning(
        "BUS_SIGNING_SECRET is too short (%d bytes, need 32+). "
        "Messages will NOT be auto-signed.",
        len(secret_bytes),
    )
    return None
```

### Signature Verification

`verify_bus_message()` (line 228 of `bus_writer_signing.py`) reconstructs the signing payload from the TSV header and envelope content, then calls `verify_signature()` to check the HMAC:

```python
envelope = _parse_signing_envelope(message)
if envelope is None:
    return (False, message)

content, nonce, signature = envelope
payload = {"message": content}
verified = verify_signature(
    secret, timestamp, from_id, to_id, msg_type, payload, nonce, signature
)
return (verified, content)
```

### Signed Envelope Validation

`_validate_signed_envelope()` (line 982 of `bus_writer_core.py`) validates the envelope shape before writing:

- Must have exactly keys `c`, `n`, `s` (if it has `s`)
- `c`, `n`, `s` must all be strings
- Nonce must be at least 10 characters
- Signature should be 64 characters (SHA-256 hex); a warning is logged if not

### Replay Protection via Nonces

The `audit_bus()` function (line 131 of `bus_verifier.py`) tracks nonces across all signed messages and flags duplicates:

```python
if nonce in seen_nonces:
    report.duplicate_nonces += 1
    report.issues.append(f"Line {line_num}: duplicate nonce {nonce[:20]}...")
seen_nonces.add(nonce)
```

Duplicate nonces are a replay attack indicator. The audit CLI exits with code 1 when duplicate nonces are found.

## Security Policy Enforcement

### Policy Levels

`BusSecurityPolicy` in `bus_policy.py` (line 35) implements three enforcement levels:

| Level | Behavior for unsigned messages | Use case |
|---|---|---|
| `PERMISSIVE` | Accept silently (no-op) | Backward-compatible default; development |
| `WARN` | Accept but log a warning per message | Gradual rollout; visibility without breakage |
| `STRICT` | Reject with `ValueError` | Production; safety-critical environments |

### How the Policy Is Checked

In `post_message()`, after secret resolution, the policy is checked (line 1372):

```python
from .bus_policy import get_bus_policy

get_bus_policy().check_signing(secret=secret, from_id=from_id, msg_type=msg_type)
```

The `check_signing()` method (line 80 of `bus_policy.py`) executes this logic:

1. **Signed messages always pass** — if `secret is not None`, return immediately
2. **Exempt types always pass** — if `msg_type` is in `allow_unsigned_types` (default: `{"HEARTBEAT"}`), return
3. **PERMISSIVE** — return (no-op)
4. **WARN** — log a warning with sender and type, then return
5. **STRICT** — raise `ValueError` with instructions to provide a signing secret

The `STRICT` rejection message (line 127):

```
Bus security policy STRICT: unsigned message rejected from {from_id}
(type={msg_type}). Provide a signing secret via --sign or --secret-file.
```

### Configuration

The policy level is configured via:

- **Environment variable:** `BUS_SECURITY_POLICY=permissive|warn|strict`
- **Direct instantiation:** `BusSecurityPolicy(level="strict")`

Invalid values fall back to `PERMISSIVE` with a warning (line 70 of `bus_policy.py`).

The singleton is accessed via `get_bus_policy()` (line 138), which reads the env var on first call. Use `reset_bus_policy()` (line 155) to reset the singleton for testing.

### Exempt Message Types

The `allow_unsigned_types` parameter defaults to `{"HEARTBEAT"}` (line 78). Heartbeats are exempt because they are high-frequency and low-sensitivity — requiring signing for every heartbeat would impose unnecessary overhead. You can customize this:

```python
from hummbl_bus.bus_policy import BusSecurityPolicy

policy = BusSecurityPolicy(
    level="strict",
    allow_unsigned_types={"HEARTBEAT", "PING"},
)
```

## Base64 Injection Protection

The package `__init__.py` docstring (line 3) states:

> Provides TSV-based message bus with injection protection through base64 encoding of payloads.

The `SecureTSVEncoder` and `SecureTSVDecoder` classes (imported from the `secure_tsv` module) provide base64 encoding of message payloads to prevent TSV column-injection attacks. If an attacker crafts a message containing tab characters, it could create additional TSV columns and corrupt the bus format or inject fake messages. Base64 encoding eliminates this risk because base64 output contains only `[A-Za-z0-9+/=]` — no tabs, newlines, or other control characters.

The `TSVInjectionError` exception is raised when injection attempts are detected during encoding.

Additionally, `escape_message()` (line 136 of `bus_writer_core.py`) provides a second layer of defense by replacing tabs with spaces and newlines with escaped `\n` literals. The `_sanitize_field()` function (line 222) applies the same treatment to header fields (`from_id`, `to_id`, `msg_type`).

### Content Validation

`_validate_content()` (line 949 of `bus_writer_core.py`) provides additional injection protection:

- **Null byte rejection** — `if "\x00" in message: raise ValueError("message contains null bytes")` — prevents binary injection
- **Structured payload field count limit** — JSON payloads with more than `MAX_PAYLOAD_FIELDS` (64) fields are rejected — prevents bloated JSON injection

### Payload Size Limit

`_validate_fields()` (line 907) enforces `MAX_MESSAGE_BYTES = 65536` (64 KB). Oversized messages are rejected:

```python
message_bytes = len(message.encode("utf-8"))
if message_bytes > MAX_MESSAGE_BYTES:
    raise ValueError(
        f"message exceeds maximum size: {message_bytes} bytes > {MAX_MESSAGE_BYTES} bytes"
    )
```

## File Permission Hardening

`harden_bus_file_permissions()` (line 59 of `bus_writer_signing.py`) sets newly created bus files to mode `0o660` (owner and group read/write, no world access):

```python
current_mode = path.stat().st_mode & 0o777
if current_mode != 0o660:
    path.chmod(0o660)
```

This is called automatically by `_append_tsv_line()` when a new bus file is created (line 472 of `bus_writer_core.py`). The hardening prevents unauthorized users from reading or writing the bus file, which may contain sensitive coordination data.

## Bridge Authentication

### Bearer Token Auth

The bridge server (`bridge_server.py`) uses Bearer token authentication for POST endpoints. The token is loaded by `_load_bridge_token()` (line 31):

1. `BUS_BRIDGE_TOKEN` environment variable (checked first)
2. `BUS_BRIDGE_TOKEN_FILE` environment variable (path to a token file)
3. Default token file: `~/.config/foundermode/bus_bridge_token`

When no token is configured, auth is **disabled** and all POSTs are accepted (logged as `no_auth`). When a token is configured, the server compares the `Authorization: Bearer <token>` header using `hmac.compare_digest()` (line 196):

```python
if not hmac.compare_digest(auth_header, expected):
    _record_auth_event(outcome="failure", ...)
    self.send_response(401)
    ...
    return False
```

`hmac.compare_digest()` performs a constant-time comparison to prevent timing attacks that could allow a co-tenant tailnet observer to recover the token character by character.

### Tailscale-Only Binding

By default, `run_server()` (line 506) binds to the Tailscale interface IP (`100.x.x.x`) only, detected via `get_tailscale_ip()` (line 473). If no Tailscale IP is found, it falls back to `127.0.0.1` (localhost only). This ensures the bridge is not exposed to the public internet. Use `--bind-all` to override (with caution).

### Client-Supplied Path Rejection

The bridge server rejects any POST request containing a `bus_path` field (line 237):

```python
if data.get("bus_path"):
    _record_auth_event(
        outcome="rejected", reason="client-supplied bus_path is not accepted"
    )
    self.send_error(400, "Client-supplied bus_path is not accepted")
    return
```

This prevents path traversal attacks where a remote client could specify an arbitrary file path for the bus write.

### Replay Protection

When a `request_id` is provided in a POST, the server checks for duplicates via:

1. `lookup_request()` from the replay ledger (primary)
2. `_lookup_auth_event_request()` from the auth event log (secondary fallback)

If a duplicate is found, the server returns `{"status": "ok", "duplicate": true}` with the original receipt, without writing a new bus entry. This provides idempotency for cross-machine writes.

### Auth Event Logging

All auth outcomes are logged to `auth_events.jsonl` via `_record_auth_event()` (line 63). Valid outcomes:

| Outcome | Meaning |
|---|---|
| `success` | Bearer token verified |
| `failure` | Bearer token mismatch (401) |
| `no_auth` | No token configured; POST accepted |
| `accepted` | Message written to bus |
| `duplicate` | Duplicate request_id; no write |
| `rejected` | Client-supplied bus_path or other rejection |

**The token itself is never logged.** The log includes: timestamp, client IP, sender, recipient, message type, request ID, correlation ID, origin machine, bus path, and reason.

## Privileged Message Type Enforcement

`_validate_privileged_message_type()` (line 739 of `bus_writer_core.py`) enforces role-based access control on privileged message types:

### DIRECTIVE

- **Allowed senders:** `human`, `reuben`, `dan` (the `_PRIVILEGED_SENDERS` set, line 661)
- **All other senders:** rejected with `ValueError`

### DECISION

- **Allowed senders:** human senders OR Steward proxy senders (`claude-code`, `devin`, `opencode` — the `_STEWARD_PROXY_SENDERS` set, line 678)
- **Steward proxy requirements:** The message body must contain:
  1. The audit flag `On-behalf-of: human` (line 681)
  2. A citation of operator instruction — one of: `operator instruction`, `operator chat`, `human instruction`, `authority: operator`, `per operator` (line 691)
- **Missing either marker:** rejected with `ValueError`

### Sender-Specific Prohibitions

`_SENDER_PROHIBITED_MESSAGE_TYPES` (line 662) defines per-sender type restrictions:

| Sender | Prohibited types | Reason |
|---|---|---|
| `apex` | `ACK`, `VETO` | Structure A: Strategic Assessor, not approval/veto holder |

### Audit Trail

All privileged type rejections are recorded to `auth_events.jsonl` via `_record_privileged_type_event()` (line 700) with `client_ip` set to `"in-process"` to distinguish from HTTP bridge events. Rejection reasons include: `sender_prohibited_message_type`, `steward_proxy_missing_audit_flag`, `steward_proxy_missing_citation`, `privileged_type_unauthorized_sender`.

## Kimi Identity Retirement

Kimi is retired as of 2026-04-05. `_KIMI_APPROVED_IDENTITIES` is an empty set (line 80), meaning all `kimi-*` senders are rejected. `_validate_kimi_constraints()` (line 852) enforces this:

- Controlled by `KIMI_BUS_ENFORCE` env var: `warn` or `strict` (default)
- In `strict` mode, raises `ValueError` for any `kimi`-prefixed sender
- Also validates message type against `_KIMI_APPROVED_MESSAGE_TYPES`

## Threat Model

### Assets

- **Bus file** (`messages.tsv`) — append-only coordination log containing agent messages
- **Signing secret** — HMAC key used for message integrity
- **Bridge token** — Bearer token for cross-machine authentication

### Threats and Mitigations

| Threat | Mitigation | Source |
|---|---|---|
| **Concurrent write corruption** | `fcntl.flock(LOCK_EX)` + `os.fsync()` | `bus_writer_core.py:429` |
| **TSV column injection** | `escape_message()` replaces tabs/newlines; `SecureTSVEncoder` base64-encodes | `bus_writer_core.py:136` |
| **Message tampering** | HMAC-SHA256 signing envelope with nonce | `bus_writer_core.py:1424` |
| **Replay attacks** | Nonce tracking in `audit_bus()`; replay ledger in bridge | `bus_verifier.py:229` |
| **Unsigned message abuse** | PERMISSIVE/WARN/STRICT policy enforcement | `bus_policy.py:80` |
| **Unauthorized file access** | `chmod 0o660` on bus file creation | `bus_writer_signing.py:59` |
| **Bridge token timing attack** | `hmac.compare_digest()` constant-time comparison | `bridge_server.py:196` |
| **Bridge public exposure** | Tailscale-only binding by default | `bridge_server.py:506` |
| **Path traversal via bridge** | Client-supplied `bus_path` rejected | `bridge_server.py:237` |
| **Binary injection (null bytes)** | `_validate_content()` rejects null bytes | `bus_writer_core.py:964` |
| **Payload bloat (JSON)** | `MAX_PAYLOAD_FIELDS=64` field count limit | `bus_writer_core.py:973` |
| **Oversized messages** | `MAX_MESSAGE_BYTES=65536` size limit | `bus_writer_core.py:939` |
| **Privileged type abuse** | Role-based enforcement for DIRECTIVE/DECISION | `bus_writer_core.py:739` |
| **Deprecated identity spoofing** | `_validate_sender_identity()` + canonical registry | `bus_writer_core.py:551` |
| **Bridge replay** | `request_id` idempotency with replay ledger | `bridge_server.py:252` |

### Assumptions

- The bus file resides on a filesystem that supports `flock` advisory locking (POSIX) or `msvcrt.locking` (Windows).
- The signing secret is stored securely and not exposed to unauthorized parties.
- The bridge server is accessible only via Tailscale or a trusted network.
- Agent identities are managed through a registry that is trusted and tamper-resistant.

### Limitations

- **No encryption at rest** — the bus file is plaintext TSV. File permission hardening (`0o660`) is the primary protection. For encrypted storage, use a filesystem-level encryption layer.
- **No transport encryption** — the bridge uses plain HTTP. Tailscale provides WireGuard encryption for the transport layer. For non-Tailscale deployments, use a reverse proxy with TLS.
- **Advisory locking** — `flock` is advisory; processes that bypass `post_message()` and write directly to the file are not protected. All writers must go through the canonical write path.
- **Shared secret model** — all agents sharing a `BUS_SIGNING_SECRET` can sign messages as any sender. For per-agent signing keys, use the `KeyManager` integration.
