# CLI Reference

hummbl-bus provides three command-line interfaces: the bus writer for posting messages, the bus verifier for integrity audits, and the bridge client/server for cross-machine coordination.

## Bus Writer CLI

**Entry point:** `hummbl_bus.bus_writer_cli:main` (registered as `hummbl-bus` in `pyproject.toml` line 29)

**Source:** `bus_writer.py` re-exports `main` from `bus_writer_cli` (line 83)

### Usage

```bash
python -m hummbl_bus.bus_writer <from> <to> <type> <message> [--bus PATH]
```

Or using the installed entry point:

```bash
hummbl-bus <from> <to> <type> <message> [--bus PATH]
```

### Positional Arguments

| Argument | Required | Description |
|---|---|---|
| `from` | Yes | Sender agent identifier (e.g., `devin`) |
| `to` | Yes | Recipient identifier (e.g., `all`, `codex`) |
| `type` | Yes | Message type (e.g., `STATUS`, `DECISION`, `HANDOFF`) |
| `message` | Yes | Message content |

### Options

| Flag | Description |
|---|---|
| `--bus PATH` | Override the bus file path. If omitted, resolves from `COORDINATION_BUS` env var, then git repo root, then default `hummbl_governance/_state/coordination/messages.tsv` |
| `--sign` | Enable HMAC signing (uses `BUS_SIGNING_SECRET` env var) |
| `--secret-file PATH` | Load signing secret from a JSON file with a `key` field (base64-encoded) |

### Examples

Post a simple status message:

```bash
python -m hummbl_bus.bus_writer devin all STATUS "Build complete, tests passing"
```

Post to a specific bus file:

```bash
python -m hummbl_bus.bus_writer codex devin HANDOFF "PR #42 ready for review" --bus /tmp/my-bus.tsv
```

Post a signed message:

```bash
export BUS_SIGNING_SECRET="your-32-byte-secret-here-1234567890ab"
python -m hummbl_bus.bus_writer devin all STATUS "Signed message" --sign
```

Post with a secret file:

```bash
python -m hummbl_bus.bus_writer devin all STATUS "Signed message" --secret-file signing-key.json
```

The secret file is a JSON file with a base64-encoded key:

```json
{"key": "eW91ci0zMi1ieXRlLXNlY3JldC1oZXJlLTEyMzQ1Njc4OTA="}
```

### Bus Path Resolution

The CLI resolves the bus path via `_resolve_bus_path()` with this priority:

1. `--bus PATH` flag (highest priority)
2. `COORDINATION_BUS` environment variable
3. Git repo root + `DEFAULT_BUS_PATH` (`hummbl_governance/_state/coordination/messages.tsv`)
4. `DEFAULT_BUS_PATH` as a relative path (fallback)

---

## Bus Verifier CLI

**Entry point:** `hummbl_bus.bus_verifier:main` (line 270 of `bus_verifier.py`)

### Usage

```bash
python -m hummbl_bus.bus_verifier [options]
```

### Options

| Flag | Description |
|---|---|
| `--bus PATH` | Override bus file path. Resolves from `COORDINATION_BUS` env var or git root if omitted |
| `--secret-file PATH` | Verify signatures using the key from a JSON file (`{"key": "base64..."}`) |
| `--json` | Output as JSON instead of text summary |
| `--quiet` | Only print issues to stderr; suppress summary. Exit non-zero on problems |

### Exit Codes

| Code | Meaning |
|---|---|
| `0` | Clean — no signature failures or duplicate nonces |
| `1` | Issues found — signature verification failures or duplicate nonces detected |
| `2` | Argument error — unknown argument passed |

### Examples

Text summary audit:

```bash
python -m hummbl_bus.bus_verifier --bus /tmp/messages.tsv
```

Output:

```
Bus Integrity Audit: /tmp/messages.tsv
  Total messages:     142
  Signed:             98 (69.0%)
  Unsigned:           44
  Verified OK:        95
  Verified FAIL:      3
  Unknown senders:    2
  Issues found:       5
    - Line 23: signature verification FAILED (from=agent-x)
    - Line 45: duplicate nonce a1b2c3d4e5f6...
    ...
```

JSON output for programmatic consumption:

```bash
python -m hummbl_bus.bus_verifier --bus /tmp/messages.tsv --json
```

Verify signatures with a secret file:

```bash
python -m hummbl_bus.bus_verifier --bus /tmp/messages.tsv --secret-file key.json
```

Quiet mode for CI/CD integration (prints only issues, exits non-zero):

```bash
python -m hummbl_bus.bus_verifier --bus /tmp/messages.tsv --quiet
```

---

## Bridge Client CLI

**Entry point:** `hummbl_bus.bridge_client:main` (line 202 of `bridge_client.py`)

### Usage

```bash
python -m hummbl_bus.bridge_client [-p PORT] <host> <from> <to> <type> <message>
```

### Positional Arguments

| Argument | Required | Description |
|---|---|---|
| `host` | Yes* | Remote host (Tailscale IP or hostname) |
| `from_agent` | Yes* | Sender agent ID |
| `to_agent` | Yes* | Recipient agent ID |
| `msg_type` | Yes* | Message type |
| `message` | Yes* | Message content |

*Required for message posting. Only `host` is required for `--health` mode.

### Options

| Flag | Default | Description |
|---|---|---|
| `--port`, `-p` | `18790` | Remote bridge server port |
| `--health`, `-c` | — | Health check only (GET `/health`); no message posted |

### Exit Codes

| Code | Meaning |
|---|---|
| `0` | Message posted successfully / health check OK |
| `1` | Post failed / health check failed / missing arguments |

### Examples

Post a message to a remote machine:

```bash
python -m hummbl_bus.bridge_client mini kimi-mini kimi-mbp STATUS "Hello from Mac Mini"
```

Post to a non-default port:

```bash
python -m hummbl_bus.bridge_client -p 8080 100.64.0.1 devin all STATUS "Remote post"
```

Health check:

```bash
python -m hummbl_bus.bridge_client --health mini
# Output: Health check for mini:18790: OK
```

### Token Configuration

The bridge client automatically loads the Bearer token from:

1. `BUS_BRIDGE_TOKEN` environment variable
2. `BUS_BRIDGE_TOKEN_FILE` environment variable (path to token file)
3. Default: `~/.config/foundermode/bus_bridge_token`

When a token is available, it is sent as `Authorization: Bearer <token>`.

---

## Bridge Server CLI

**Entry point:** `hummbl_bus.bridge_server:__main__` (line 539 of `bridge_server.py`)

### Usage

```bash
python -m hummbl_bus.bridge_server [--port PORT] [--bind-all]
```

### Options

| Flag | Default | Description |
|---|---|---|
| `--port` | `18790` | Port to listen on |
| `--bind-all` | — | Bind to `0.0.0.0` (all interfaces) instead of Tailscale-only |

### Examples

Start the bridge server on the default port (Tailscale-only):

```bash
python -m hummbl_bus.bridge_server
# Output:
# Binding to Tailscale interface: 100.64.0.1
# Bus Bridge Server running on http://100.64.0.1:18790
# Endpoints: POST /bus, GET /health, GET /bus/status, GET /bus/tail, GET /bus/search
# Auth: DISABLED — set BUS_BRIDGE_TOKEN env var to require auth on POST
```

Start on a custom port with auth enabled:

```bash
export BUS_BRIDGE_TOKEN="my-secret-bridge-token"
python -m hummbl_bus.bridge_server --port 9000
# Output:
# Auth: POST endpoints require Authorization: Bearer <BUS_BRIDGE_TOKEN>
```

Bind to all interfaces (use with caution):

```bash
python -m hummbl_bus.bridge_server --bind-all
```

### Server Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/bus` | Bearer token (if configured) | Post a bus message |
| POST | `/api/bus/send` | Bearer token (if configured) | Alias for `/bus` |
| POST | `/bus/post` | Bearer token (if configured) | Alias for `/bus` |
| GET | `/health` | None | Health check: `{"status":"up","service":"bus-bridge","version":"1.3","auth_enabled":bool}` |
| GET | `/bus/status` | None | Bus line count and last write timestamp |
| GET | `/bus/tail?n=50&date=YYYY-MM-DD` | None | Last N bus lines, optionally filtered by date prefix |
| GET | `/bus/search?q=pattern&n=200` | None | Search bus lines by case-insensitive substring |
