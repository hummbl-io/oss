# Configuration

hummbl-bus is configured entirely through environment variables. There are no configuration files — the bus is designed for zero-config operation with sensible defaults, with environment variables for tuning security, routing, and bridge behavior.

## Environment Variables

### Security & Signing

| Variable | Type | Default | Valid Values | Description |
|---|---|---|---|---|
| `BUS_SECURITY_POLICY` | string | `permissive` | `permissive`, `warn`, `strict` | Bus security enforcement level. Controls whether unsigned messages are accepted silently, warned about, or rejected. Invalid values fall back to `permissive` with a warning. **Source:** `bus_policy.py:64` |
| `BUS_SIGNING_SECRET` | string | (unset) | 32+ byte string | HMAC-SHA256 signing secret for auto-signing messages. If set and at least 32 bytes, all messages are signed automatically. If shorter than 32 bytes, a warning is logged and messages are NOT signed. **Source:** `bus_writer_signing.py:45` |

### Bus Path & File Location

| Variable | Type | Default | Valid Values | Description |
|---|---|---|---|---|
| `COORDINATION_BUS` | string | (unset) | filesystem path | Override the bus file path. Checked by the CLI and verifier when `--bus` is not provided. **Source:** `bus_verifier.py:262` |
| `BUS_CANONICAL_FILE_PATH` | string | (unset) | filesystem path | Migration-safe override for the authoritative local bus file. When set, `resolve_canonical_bus_path()` returns this path. **Source:** `bus_writer_core.py:282` |
| `BUS_WRITE_HEADER` | string | (unset) | `1`, `true`, `yes` | When set, writes a TSV header line (`timestamp_utc\tfrom\tto\ttype\tmessage`) to newly created bus files. **Source:** `bus_writer_core.py:453` |

### Bus Hygiene Enforcement

| Variable | Type | Default | Valid Values | Description |
|---|---|---|---|---|
| `BUS_ENFORCE_CANONICAL_PATH` | string | (unset) | `1`, `true`, `yes`, `on` | When set, rejects writes to non-canonical bus paths with `ValueError`. **Source:** `bus_writer_core.py:352` |
| `BUS_REJECT_SHADOW_BUSES` | string | (unset) | `1`, `true`, `yes`, `on` | When set, rejects writes when shadow bus files are detected nearby. **Source:** `bus_writer_core.py:360` |

### Remote Bus & Bridge

| Variable | Type | Default | Valid Values | Description |
|---|---|---|---|---|
| `BUS_REMOTE_URL` | string | (unset) | HTTP URL | When set, `post_message()` POSTs to this URL's `/bus` endpoint instead of appending locally. Falls back to local write on failure. **Source:** `bus_writer_core.py:1528` |
| `BUS_CANONICAL_BRIDGE_URL` | string | (unset) | HTTP URL | Canonical remote-first write mode. Posts to this bridge URL and does NOT fall back to local on transient failure — instead spools or dead-letters. **Source:** `bus_writer_core.py:1450` |
| `BUS_BRIDGE_TOKEN` | string | (unset) | any string | Bearer token for bridge client/server authentication. When unset on the server, auth is disabled. **Source:** `bridge_client.py:27`, `bridge_server.py:33` |
| `BUS_BRIDGE_TOKEN_FILE` | string | (unset) | filesystem path | Path to a file containing the bridge token. Falls back to `~/.config/foundermode/bus_bridge_token`. **Source:** `bridge_client.py:31`, `bridge_server.py:37` |
| `BUS_AUTH_EVENT_LOG` | string | (unset) | filesystem path | Override path for the bridge auth event log (`auth_events.jsonl`). Default: next to bus file under `_state/bus/auth_events.jsonl`. **Source:** `bridge_server.py:56` |

### Relay & Dashboard

| Variable | Type | Default | Valid Values | Description |
|---|---|---|---|---|
| `OPEN_BRAIN_RELAY_URL` | string | (unset) | HTTP URL | When set, bus messages are also forwarded to this Open Brain server's `/bus/post` endpoint. Best-effort, never raises. **Source:** `bus_writer_core.py:1570` |
| `OPEN_BRAIN_TOKEN` | string | (unset) | any string | Bearer token for Open Brain relay authentication. **Source:** `bus_writer_core.py:1583` |
| `DASHBOARD_WRITE_TOKEN` | string | (unset) | any string | Token sent as `X-Dashboard-Token` header when posting to `BUS_REMOTE_URL`. **Source:** `bus_writer_core.py:1539` |

### Machine Identity

| Variable | Type | Default | Valid Values | Description |
|---|---|---|---|---|
| `BUS_ORIGIN_MACHINE` | string | (unset) | any string | Origin machine name for remote-first writes. Checked first by `current_machine_name()`. **Source:** `bus_writer_core.py:1456` |
| `MACHINE_ID` | string | (unset) | any string | Machine identifier fallback. **Source:** `bus_writer_core.py:1456` |
| `COMPUTERNAME` | string | (unset) | any string | Windows machine name fallback. **Source:** `bus_writer_core.py:1456` |
| `HOSTNAME` | string | (unset) | any string | POSIX hostname fallback. **Source:** `bus_writer_core.py:1456` |

### Testing & Debug

| Variable | Type | Default | Valid Values | Description |
|---|---|---|---|---|
| `FM_TEST_MODE` | string | (unset) | `1` | When set to `1`, `enforce_sender_identity` defaults to `False`, allowing test fixtures with synthetic identities (e.g., `agent-0`, `test-agent`). **Source:** `bus_writer_core.py:1352` |
| `BUS_DEBUG` | string | (unset) | any value | When set, enables post-write verification that reads the last 4 KB of the bus file and checks the last line matches what was written. **Source:** `bus_writer_core.py:1603` |
| `KIMI_BUS_ENFORCE` | string | `strict` | `warn`, `strict` | Controls Kimi identity enforcement. `strict` raises `ValueError` for kimi-prefixed senders; `warn` logs warnings. **Source:** `bus_writer_core.py:882` |

## Configuration Profiles

### Development (Default)

No environment variables needed. Unsigned messages are accepted, local bus file is used, no bridge.

```bash
python -m hummbl_bus.bus_writer devin all STATUS "Dev message"
```

### Production with Signing

```bash
export BUS_SECURITY_POLICY=strict
export BUS_SIGNING_SECRET="$(openssl rand -hex 32)"
python -m hummbl_bus.bus_writer devin all STATUS "Signed production message" --sign
```

### Cross-Machine with Bridge

On the server machine:

```bash
export BUS_BRIDGE_TOKEN="$(openssl rand -hex 32)"
python -m hummbl_bus.bridge_server --port 18790
```

On the client machine:

```bash
export BUS_BRIDGE_TOKEN="same-token-as-server"
python -m hummbl_bus.bridge_client mini devin all STATUS "Cross-machine message"
```

### Remote-First Canonical Bus

```bash
export BUS_CANONICAL_BRIDGE_URL="http://100.64.0.1:18790"
export BUS_SIGNING_SECRET="$(openssl rand -hex 32)"
export BUS_ORIGIN_MACHINE="macbook"
python -m hummbl_bus.bus_writer devin all STATUS "Remote-first write"
```

In this mode, messages are posted directly to the canonical bridge. Transient failures are spooled for retry; permanent failures (400/401/403) are dead-lettered.

## Default Values Reference

| Setting | Default Value | Source |
|---|---|---|
| Bus file path | `hummbl_governance/_state/coordination/messages.tsv` | `bus_writer_core.py:59` |
| Dead letter path | `hummbl_governance/_state/coordination/dead_letters.jsonl` | `bus_writer_core.py:60` |
| Bridge port | `18790` | `bridge_client.py:21` |
| Bridge token file | `~/.config/foundermode/bus_bridge_token` | `bridge_client.py:22` |
| Max message size | 65,536 bytes (64 KB) | `bus_writer_core.py:128` |
| Max payload fields | 64 | `bus_writer_core.py:946` |
| Default policy level | `permissive` | `bus_policy.py:64` |
| Default exempt types | `{"HEARTBEAT"}` | `bus_policy.py:78` |
| Bridge server version | `1.3` | `bridge_server.py:369` |
| Health check timeout | 5 seconds | `bridge_client.py:195` |
| Post timeout | 10 seconds | `bridge_client.py:87` |
