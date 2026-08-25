# Troubleshooting

Common issues encountered when using hummbl-bus, with their root causes and fixes. Each issue references the specific source code location.

## Permission Errors

### "Could not harden bus file permissions"

**Symptom:** Warning in logs: `Could not harden bus file permissions: [Errno 1] Operation not permitted`

**Cause:** `harden_bus_file_permissions()` (line 59 of `bus_writer_signing.py`) attempts to `chmod 0o660` the bus file when it is first created. This fails if the process does not own the file or lacks permission to change its mode.

**Fix:**
- Ensure the process running `post_message()` has write permission to the directory containing the bus file.
- If the bus file was created by a different user, change ownership: `chown <user> messages.tsv`
- The warning is non-fatal — the message is still written. However, the file remains with default permissions, which may expose it to other users. Manually fix: `chmod 660 messages.tsv`

### "Shadow bus files detected"

**Symptom:** `OSError: Shadow bus files detected: /path/to/other/messages.tsv`

**Cause:** `BUS_REJECT_SHADOW_BUSES` is enabled and `find_shadow_bus_paths()` (line 301 of `bus_writer_core.py`) found duplicate bus files in nearby directories. This happens when the bus writer was invoked from different working directories, creating multiple bus files.

**Fix:**
- Remove the shadow bus files: `rm /path/to/other/messages.tsv`
- Or unset `BUS_REJECT_SHADOW_BUSES` if you are not ready to enforce canonical path hygiene.
- Use `BUS_CANONICAL_FILE_PATH` to explicitly specify the authoritative bus file location.

### "Operational bus write rejected for non-canonical path"

**Symptom:** `ValueError: Operational bus write rejected for non-canonical path: /wrong/path.tsv (expected /correct/path.tsv)`

**Cause:** `BUS_ENFORCE_CANONICAL_PATH` is enabled and the `bus_path` passed to `post_message()` does not match `resolve_canonical_bus_path()` (line 275 of `bus_writer_core.py`).

**Fix:**
- Set `BUS_CANONICAL_FILE_PATH` to the correct path, or
- Pass the canonical path to `post_message()`, or
- Unset `BUS_ENFORCE_CANONICAL_PATH` if not ready to enforce.

## Locked Bus Files

### Writes hanging indefinitely

**Symptom:** `post_message()` hangs and never returns.

**Cause:** Another process holds an exclusive `flock` on the bus file and has not released it. This can happen if a process crashed while holding the lock (though `flock` is automatically released when the file descriptor closes, so this is rare), or if a process is stuck in a long operation.

**Fix:**
- Identify the process holding the lock: `lsof /path/to/messages.tsv` (look for file descriptors with LOCK status)
- Kill the stuck process: `kill <pid>`
- On macOS, use: `fstat /path/to/messages.tsv`
- The `flock` is advisory and automatically released when the holding process exits or closes the file descriptor.

### "EDEADLK" on Windows

**Symptom:** `msvcrt.locking` raises `EDEADLK` error on Windows.

**Cause:** Multiple threads in the same process are contending for the same byte-range lock. The per-path `threading.Lock` guard (`_msvcrt_path_lock()`, line 42 of `bus_writer_core.py`) should prevent this, but it can still occur in edge cases.

**Fix:**
- Ensure you are not spawning threads that all write to the same bus file simultaneously.
- Serialize writes within your process using a `threading.Lock` before calling `post_message()`.
- Consider using a single writer thread that queues messages from other threads.

## Signing Failures

### "BUS_SIGNING_SECRET is too short"

**Symptom:** Warning: `BUS_SIGNING_SECRET is too short (N bytes, need 32+). Messages will NOT be auto-signed.`

**Cause:** `_resolve_signing_secret()` (line 33 of `bus_writer_signing.py`) requires the secret to be at least 32 bytes. Shorter secrets are rejected for security reasons.

**Fix:**
```bash
# Generate a proper 32+ byte secret
export BUS_SIGNING_SECRET="$(openssl rand -hex 32)"
# This produces a 64-character hex string (32 bytes of entropy)
```

### "Bus security policy STRICT: unsigned message rejected"

**Symptom:** `ValueError: Bus security policy STRICT: unsigned message rejected from devin (type=STATUS).`

**Cause:** `BUS_SECURITY_POLICY=strict` is set, the message type is not in `allow_unsigned_types` (default: only `HEARTBEAT`), and no signing secret is available.

**Fix:**
- Set `BUS_SIGNING_SECRET` to a 32+ byte secret, or
- Pass `secret=` explicitly to `post_message()`, or
- Use `--sign` or `--secret-file` with the CLI, or
- Switch to `BUS_SECURITY_POLICY=warn` for gradual rollout, or
- Add the message type to `allow_unsigned_types` if it is low-sensitivity.

### Signature verification failures in audit

**Symptom:** `audit_bus()` reports `Verified FAIL: N` and issues like `Line 23: signature verification FAILED (from=agent-x)`.

**Cause:** The secret used for verification does not match the secret used for signing, or the message was tampered with after signing.

**Fix:**
- Ensure the same `BUS_SIGNING_SECRET` is used across all agents and the verifier.
- If using per-agent keys via `KeyManager`, pass the correct agent's key to `audit_bus()`.
- If signatures are genuinely failing (not a key mismatch), investigate potential tampering — check file modification times and access logs.

### "Steward proxy DECISION requires 'On-behalf-of: human' marker"

**Symptom:** `ValueError: Steward proxy DECISION from 'claude-code' requires 'On-behalf-of: human' marker in message body.`

**Cause:** `_validate_privileged_message_type()` (line 739 of `bus_writer_core.py`) requires Steward proxy senders (claude-code, devin, opencode) to include the audit flag `On-behalf-of: human` and a citation of operator instruction when posting `DECISION` messages.

**Fix:**
- Include both markers in the message body:
  ```python
  message = "On-behalf-of: human. Per operator instruction, shipping v2.1 today."
  ```
- The citation must contain one of: `operator instruction`, `operator chat`, `human instruction`, `authority: operator`, `per operator` (case-insensitive, line 691 of `bus_writer_core.py`).

## Bridge Connection Issues

### "Health check failed"

**Symptom:** `health_check()` returns `False` or the CLI reports `Health check for host:18790: FAIL`.

**Cause:** The bridge server is not running, is on a different port, or is not reachable via the network.

**Fix:**
- Verify the server is running: `curl http://<host>:18790/health`
- Check the port: `--port` must match on both client and server
- Verify Tailscale connectivity: `tailscale status` and `ping <host>`
- Check firewall rules on the server machine
- If binding to localhost, use `--bind-all` to bind to all interfaces (with caution)

### "HTTP Error 401: Unauthorized"

**Symptom:** Bridge client receives 401, or `post_to_remote_bus_result()` returns `{"ok": false, "status_code": 401, "permanent_error": true}`.

**Cause:** The Bearer token on the client does not match the token on the server. The server uses `hmac.compare_digest()` (line 196 of `bridge_server.py`) for constant-time comparison.

**Fix:**
- Ensure `BUS_BRIDGE_TOKEN` is identical on both client and server.
- If using a token file, verify the file path and contents.
- Check for trailing whitespace or newlines in the token: `echo -n` should be used when writing the token file.
- This is a permanent error (`permanent_error: true`) — do not retry without fixing the token.

### "HTTP Error 400: Client-supplied bus_path is not accepted"

**Symptom:** Bridge server returns 400 with message about `bus_path`.

**Cause:** The POST request body contained a `bus_path` field, which the server rejects (line 237 of `bridge_server.py`) to prevent path traversal attacks.

**Fix:**
- Remove the `bus_path` field from the request body. The server uses its own configured bus path via `_resolve_bus_path()`.

### "Connection error" (no HTTP status)

**Symptom:** `post_to_remote_bus_result()` returns `{"ok": false, "status_code": null, "permanent_error": false, "error": "..."}`.

**Cause:** Network-level failure — DNS resolution, connection refused, timeout, or Tailscale not connected.

**Fix:**
- Check Tailscale: `tailscale status`
- Verify the host is reachable: `ping <host>`
- Check if the server process is running on the remote machine
- This is a transient error (`permanent_error: false`) — safe to retry

### Bridge server binds to localhost only

**Symptom:** Server prints `Warning: No Tailscale IP found, binding to localhost only` and remote clients cannot connect.

**Cause:** `get_tailscale_ip()` (line 473 of `bridge_server.py`) could not detect a Tailscale IP (`100.x.x.x`) via `tailscale ip -4` or `ifconfig`.

**Fix:**
- Ensure Tailscale is installed and running: `tailscale up`
- Or use `--bind-all` to bind to `0.0.0.0` (exposes to all interfaces — use only on trusted networks)
- Or set up a reverse proxy with TLS for external access

## Policy Violations

### "Unknown bus sender identity"

**Symptom:** Warning log: `Unknown bus sender identity: 'my-agent'` or `ValueError: Unknown bus sender identity: 'my-agent'`

**Cause:** `_validate_sender_identity()` (line 551 of `bus_writer_core.py`) checks the sender against known agent IDs from the registry, roster, and reserved IDs set. The sender was not found.

**Fix:**
- Register the agent ID in the agent registry (`registry/agents_v2.json`)
- Or add it to the coordination roster (`AGENT_REGISTRY.md`)
- Or pass `enforce_sender_identity=False` (or set `FM_TEST_MODE=1` for testing)
- Or pass `known_agent_ids={"my-agent", ...}` explicitly to `post_message()`

### "Unknown bus message type"

**Symptom:** Warning: `Unknown bus message type: 'MY_TYPE'` or `ValueError: Unknown bus message type: 'MY_TYPE'`

**Cause:** `_validate_message_type()` (line 642 of `bus_writer_core.py`) checks the type against `_DEFAULT_MESSAGE_TYPES` (37 types) and the vernacular docs. The type was not found.

**Fix:**
- Use a type from the default taxonomy: `STATUS`, `SITREP`, `PROPOSAL`, `ACK`, `DECISION`, `DIRECTIVE`, `BLOCKED`, `WIP_START`, `WIP_END`, `MILESTONE`, `TASK_REQUEST`, `TASK_COMPLETE`, `RECEIPT`, `HANDOFF`, `VETO`, `ALERT`, `APPROVE`, `REJECT`, `LEDGER_QUERY`, `QUESTION`, `REVIEW`, `COMPLETE`, `SAFETY`, `HEARTBEAT`, `DISPATCH`, `ERROR`, `WARN`, `INFO`, `PHASE_TRANSITION`, `HEALTH_TRANSITION`, `STALE_STATE_RESET`, `SESSION_COMPLETE`, `SPOTREP`, `FRAGO`, `WARNO`, `CORRECTION`, `VERIFY`
- Or add the type to the vernacular docs (`.claude/rules/bus-lexicon.md`)
- Or pass `enforce_message_type=False` to `post_message()`
- Or pass `known_message_types={"MY_TYPE", ...}` explicitly

### "Privileged message type 'DIRECTIVE' from 'devin' not permitted"

**Symptom:** `ValueError` when an agent posts a `DIRECTIVE` or `DECISION` message.

**Cause:** `_validate_privileged_message_type()` (line 739 of `bus_writer_core.py`) restricts `DIRECTIVE` to human senders (`human`, `reuben`, `dan`) and `DECISION` to human senders or Steward proxies (`claude-code`, `devin`, `opencode`) with required audit markers.

**Fix:**
- Use `from_id="human"` for `DIRECTIVE` messages
- For `DECISION` via Steward proxy, include `On-behalf-of: human` and a citation of operator instruction in the message body
- Use a non-privileged type like `STATUS` or `PROPOSAL` instead

### "Unapproved Kimi identity on bus"

**Symptom:** `ValueError: Unapproved Kimi identity on bus: 'kimi-1'`

**Cause:** Kimi is retired as of 2026-04-05. `_KIMI_APPROVED_IDENTITIES` is empty (line 80 of `bus_writer_core.py`), so all `kimi-*` senders are rejected in strict mode (default).

**Fix:**
- Do not use `kimi-*` sender identities. Use a different agent ID.
- For testing, set `KIMI_BUS_ENFORCE=warn` to log warnings instead of raising errors.

## Malformed Bus Lines

### "Expected 5 columns, got N"

**Symptom:** `validate_tsv_integrity()` reports malformed lines, or `audit_bus()` reports `Malformed lines: N`.

**Cause:** A bus line has more or fewer than 5 tab-separated columns. This can happen if a process wrote to the bus file directly (bypassing `post_message()`), or if message content contained unescaped tabs.

**Fix:**
- Always use `post_message()` for writes — it escapes tabs and newlines via `escape_message()`.
- Manually fix malformed lines by editing the bus file (remove extra tabs or merge columns).
- Run `validate_tsv_integrity()` after fixes to confirm:
  ```python
  from hummbl_bus.bus_writer import validate_tsv_integrity

  valid, errors = validate_tsv_integrity("/tmp/messages.tsv")
  print(f"Valid: {valid}, Errors: {errors}")
  ```

### "message contains null bytes"

**Symptom:** `ValueError: message contains null bytes`

**Cause:** `_validate_content()` (line 949 of `bus_writer_core.py`) rejects messages containing `\x00` to prevent binary injection.

**Fix:**
- Remove null bytes from the message before posting: `message = message.replace("\x00", "")`
- Investigate the source of null bytes — they may indicate encoding issues or binary data being passed as a string.

### "structured payload has N fields, max is 64"

**Symptom:** `ValueError: structured payload has 100 fields, max is 64`

**Cause:** `_validate_content()` rejects JSON payloads with more than `MAX_PAYLOAD_FIELDS` (64) fields to prevent bloated JSON injection.

**Fix:**
- Reduce the number of fields in the JSON payload, or
- Use `post_message()` with a plain text message instead of JSON, or
- Move excess data to an external store and reference it by ID in the message.
