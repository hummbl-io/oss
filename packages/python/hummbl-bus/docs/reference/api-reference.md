# API Reference

Complete reference for every public function, class, and constant in hummbl-bus. All items are organized by source module.

---

## `hummbl_bus` (package `__init__.py`)

The package `__init__.py` uses lazy loading for `bus_verifier` and `bus_writer` exports to keep import time minimal. The following are available directly from `hummbl_bus`:

**Eagerly imported:**
- `BusSecurityPolicy`, `get_bus_policy` — from `bus_policy.py`
- `BusMessage`, `SecureTSVEncoder`, `SecureTSVDecoder`, `TSVInjectionError` — from `secure_tsv` (external module)

**Lazily imported (loaded on first access):**
- `BusAuditReport`, `audit_bus` — from `bus_verifier.py`
- `harden_bus_file_permissions`, `is_signed_message`, `post_message`, `read_verified_messages`, `verify_bus_message` — from `bus_writer.py`

---

## `bus_writer_core.py` — Core Write Path

### `post_message()`

```python
def post_message(
    bus_path: str | Path,
    from_id: str,
    to_id: str,
    msg_type: str,
    message: str,
    timestamp: str | None = None,
    correlation_id: str | None = None,
    secret: bytes | None = None,
    validate_sender_identity: bool = True,
    enforce_sender_identity: bool | None = None,
    known_agent_ids: set[str] | None = None,
    validate_recipient_identity: bool = False,
    enforce_recipient_identity: bool = False,
    known_recipient_ids: set[str] | None = None,
    validate_message_type: bool = True,
    enforce_message_type: bool = False,
    known_message_types: set[str] | None = None,
    validate: bool = True,
) -> None
```

**Source:** `bus_writer_core.py`, line 1276

Posts a message to the coordination bus with TSV-safe encoding and `flock`-based mutual exclusion.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `bus_path` | `str \| Path` | required | Path to `messages.tsv` file |
| `from_id` | `str` | required | Sender identifier (e.g., `"devin"`) |
| `to_id` | `str` | required | Recipient identifier (e.g., `"all"`) |
| `msg_type` | `str` | required | Message type (e.g., `"STATUS"`, `"DECISION"`) |
| `message` | `str` | required | Message content (escaped for TSV safety) |
| `timestamp` | `str \| None` | `None` | UTC timestamp; defaults to now with `Z` suffix |
| `correlation_id` | `str \| None` | `None` | Traceability ID; injected into payload if absent |
| `secret` | `bytes \| None` | `None` | HMAC-SHA256 key (32+ bytes); auto-resolved from KeyManager or `BUS_SIGNING_SECRET` |
| `validate_sender_identity` | `bool` | `True` | Validate `from_id` against known agent IDs |
| `enforce_sender_identity` | `bool \| None` | `None` | If `True`, raise `ValueError` for unknown senders. Defaults to `True` unless `FM_TEST_MODE=1` |
| `known_agent_ids` | `set[str] \| None` | `None` | Explicit set of known agent IDs |
| `validate_recipient_identity` | `bool` | `False` | Validate `to_id` against known IDs |
| `enforce_recipient_identity` | `bool` | `False` | Raise `ValueError` for unknown recipients |
| `known_recipient_ids` | `set[str] \| None` | `None` | Explicit set of known recipient IDs |
| `validate_message_type` | `bool` | `True` | Validate `msg_type` against known taxonomy |
| `enforce_message_type` | `bool` | `False` | Raise `ValueError` for unknown types |
| `known_message_types` | `set[str] \| None` | `None` | Explicit set of known message types |
| `validate` | `bool` | `True` | If `False`, skip all validation |

**Raises:** `ValueError` for empty fields, oversized payloads, unknown senders (when enforced), privileged type violations. `OSError` for file write failures or permanent bridge rejection.

**Example:**

```python
from hummbl_bus.bus_writer import post_message

post_message(
    "/tmp/messages.tsv",
    from_id="devin",
    to_id="codex",
    msg_type="HANDOFF",
    message="Reviewing PR #42, your turn",
    secret=b"my-32-byte-signing-secret-here!!!",
)
```

---

### `post_structured_event()`

```python
def post_structured_event(
    bus_path: str | Path,
    from_id: str,
    to_id: str,
    msg_type: str,
    content: str,
    timestamp: str | None = None,
    correlation_id: str | None = None,
    metadata: dict[str, object] | None = None,
    validate_sender_identity: bool = True,
    enforce_sender_identity: bool | None = None,
    known_agent_ids: set[str] | None = None,
    validate_recipient_identity: bool = False,
    enforce_recipient_identity: bool = False,
    known_recipient_ids: set[str] | None = None,
    validate_message_type: bool = True,
    enforce_message_type: bool = False,
    known_message_types: set[str] | None = None,
    validate: bool = True,
) -> None
```

**Source:** `bus_writer_core.py`, line 1163

Posts a structured bus event as a JSON envelope (schema `hummbl_governance.bus.event.v1`) in the 5th TSV column, preserving the 5-column format.

---

### `escape_message()`

```python
def escape_message(message: str) -> str
```

**Source:** `bus_writer_core.py`, line 136

Escapes newlines to literal `\n` and tabs to spaces for TSV safety.

```python
>>> escape_message("Line 1\nLine 2")
'Line 1\\nLine 2'
>>> escape_message("Col1\tCol2")
'Col1 Col2'
```

---

### `unescape_message()`

```python
def unescape_message(escaped: str) -> str
```

**Source:** `bus_writer_core.py`, line 169

Reverses `escape_message()`, converting escaped `\n` back to actual newlines.

---

### `generate_correlation_id()`

```python
def generate_correlation_id(prefix: str = "corr") -> str
```

**Source:** `bus_writer_core.py`, line 1059

Generates a compact correlation ID (e.g., `corr-a1b2c3d4e5f6`).

---

### `generate_request_id()`

```python
def generate_request_id(origin_machine: str, sender: str) -> str
```

**Source:** `bus_writer_core.py`, line 1065

Generates an idempotency key for remote bus writes (e.g., `mini-devin-a1b2c3d4e5f6...`).

---

### `extract_correlation_id()`

```python
def extract_correlation_id(message: str) -> str | None
```

**Source:** `bus_writer_core.py`, line 1072

Extracts a `correlation_id=...` value from a bus message payload using regex.

---

### `build_structured_event()`

```python
def build_structured_event(
    *,
    sender: str,
    recipient: str,
    msg_type: str,
    content: str,
    timestamp: str | None = None,
    correlation_id: str | None = None,
    metadata: dict[str, object] | None = None,
) -> str
```

**Source:** `bus_writer_core.py`, line 1101

Builds a canonical JSON envelope for structured bus events. Returns a JSON string with schema marker `hummbl_governance.bus.event.v1`.

---

### `parse_structured_event()`

```python
def parse_structured_event(message: str) -> dict[str, object] | None
```

**Source:** `bus_writer_core.py`, line 1142

Parses a structured event payload. Returns `None` for non-JSON or payloads without the schema marker.

---

### `validate_tsv_integrity()`

```python
def validate_tsv_integrity(bus_path: str | Path) -> tuple[int, list[str]]
```

**Source:** `bus_writer_core.py`, line 1627

Validates that all bus entries are properly formatted 5-column TSV. Returns `(valid_count, error_lines)`.

---

### `write_dead_letter()`

```python
def write_dead_letter(
    *,
    dead_letter_path: str | Path,
    source: str,
    reason: str,
    payload: dict[str, object] | None = None,
    metadata: dict[str, object] | None = None,
    timestamp: str | None = None,
) -> None
```

**Source:** `bus_writer_core.py`, line 1226

Appends a dead-letter record (JSONL) for failed bus operations, under the same advisory lock model.

---

### `load_known_agent_ids()`

```python
@lru_cache(maxsize=1)
def load_known_agent_ids() -> set[str]
```

**Source:** `bus_writer_core.py`, line 477

Loads known agent IDs from the registry JSON, coordination roster docs, and reserved IDs set. Cached via `lru_cache`.

---

### `load_known_message_types()`

```python
@lru_cache(maxsize=1)
def load_known_message_types() -> set[str]
```

**Source:** `bus_writer_core.py`, line 526

Loads known message types from defaults and vernacular docs. Cached via `lru_cache`.

---

### `route()`

```python
def route(msg_type: str, sender: str) -> str
```

**Source:** `bus_writer_core.py`, line 419

Computes the cell name for a message based on type and sender using `ROUTING_TABLE` and `SENDER_OVERRIDES`. Returns one of `"ops"`, `"coordination"`, `"reporting"`, `"meta"`, `"inference"`.

---

### Constants

| Constant | Source | Value | Description |
|---|---|---|---|
| `DEFAULT_BUS_PATH` | line 59 | `"hummbl_governance/_state/coordination/messages.tsv"` | Default bus file path relative to repo root |
| `DEFAULT_DEAD_LETTER_PATH` | line 60 | `"hummbl_governance/_state/coordination/dead_letters.jsonl"` | Dead-letter queue path |
| `DEFAULT_AGENT_REGISTRY_PATH` | line 61 | `"registry/agents_v2.json"` | Agent registry JSON path |
| `DEFAULT_COORDINATION_ROSTER_PATH` | line 62 | `"hummbl_governance/playbooks/AGENT_REGISTRY.md"` | Coordination roster markdown |
| `DEFAULT_VERNACULAR_PATH` | line 63 | `".claude/rules/bus-lexicon.md"` | Message type vernacular doc |
| `STRUCTURED_EVENT_SCHEMA` | line 64 | `"hummbl_governance.bus.event.v1"` | Structured event schema marker |
| `MAX_MESSAGE_BYTES` | line 128 | `65536` | Maximum message payload size (64 KB) |
| `MAX_PAYLOAD_FIELDS` | line 946 | `64` | Maximum structured payload field count |
| `_RESERVED_AGENT_IDS` | line 65 | set of 40+ IDs | Reserved/built-in agent identifiers |
| `_DEFAULT_MESSAGE_TYPES` | line 86 | set of 37 types | Default message type taxonomy |
| `_KIMI_APPROVED_IDENTITIES` | line 80 | `set()` | Retired — all kimi-* senders rejected |
| `_KIMI_APPROVED_MESSAGE_TYPES` | line 81 | set of 13 types | Approved message types for Kimi (retired identity) |

---

## `bus_writer_signing.py` — HMAC Signing

### `harden_bus_file_permissions()`

```python
def harden_bus_file_permissions(bus_path: str | Path) -> None
```

**Source:** `bus_writer_signing.py`, line 59

Sets the bus file to mode `0o660` (owner and group read/write). Called automatically when a new bus file is created. Logs a warning if the chmod fails.

---

### `read_verified_messages()`

```python
def read_verified_messages(
    bus_path: str | Path,
    secret: bytes | None = None,
    *,
    msg_type_filter: str | None = None,
    since_minutes: int = 5,
    require_signature: bool = False,
) -> list[dict[str, str]]
```

**Source:** `bus_writer_signing.py`, line 87

Reads bus messages with optional signature verification. Filters out messages with invalid signatures when a secret is provided. When `require_signature=True`, unsigned messages are also skipped.

Returns a list of dicts with keys: `timestamp`, `sender`, `recipient`, `msg_type`, `message` (with original content extracted from the signing envelope).

---

### `is_signed_message()`

```python
def is_signed_message(message: str) -> bool
```

**Source:** `bus_writer_signing.py`, line 223

Returns `True` if the message column content looks like a signed envelope (`{"c":..., "n":..., "s":...}`).

---

### `verify_bus_message()`

```python
def verify_bus_message(
    timestamp: str,
    from_id: str,
    to_id: str,
    msg_type: str,
    message: str,
    secret: bytes,
) -> tuple[bool, str]
```

**Source:** `bus_writer_signing.py`, line 228

Verifies a bus message's HMAC signature. Returns `(True, original_content)` if valid, `(False, message)` if unsigned or verification fails.

---

### `_resolve_signing_secret()`

```python
def _resolve_signing_secret() -> bytes | None
```

**Source:** `bus_writer_signing.py`, line 33

Resolves the HMAC signing secret from the `BUS_SIGNING_SECRET` environment variable. Returns `None` if unset or shorter than 32 bytes (with a warning).

---

### `_parse_signing_envelope()`

```python
def _parse_signing_envelope(message: str) -> tuple[str, str, str] | None
```

**Source:** `bus_writer_signing.py`, line 195

Parses a signed message envelope. Returns `(content, nonce, signature)` or `None`.

---

## `bus_policy.py` — Security Policy

### `PolicyLevel`

```python
class PolicyLevel(Enum):
    PERMISSIVE = "permissive"
    WARN = "warn"
    STRICT = "strict"
```

**Source:** `bus_policy.py`, line 27

---

### `BusSecurityPolicy`

```python
class BusSecurityPolicy:
    def __init__(
        self,
        level: str | PolicyLevel | None = None,
        allow_unsigned_types: set[str] | None = None,
    )
```

**Source:** `bus_policy.py`, line 35

Configurable security policy for coordination bus messages.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `level` | `str \| PolicyLevel \| None` | `None` | Enforcement level. If `None`, reads `BUS_SECURITY_POLICY` env var, defaulting to `permissive` |
| `allow_unsigned_types` | `set[str] \| None` | `None` | Message types exempt from signing. Defaults to `{"HEARTBEAT"}` |

#### `check_signing()`

```python
def check_signing(
    self,
    *,
    secret: bytes | None,
    from_id: str,
    msg_type: str,
) -> None
```

**Source:** `bus_policy.py`, line 80

Checks whether an unsigned message should be accepted. Signed messages (`secret is not None`) and exempt types always pass. In `STRICT` mode, raises `ValueError` for unsigned non-exempt messages.

---

### `get_bus_policy()`

```python
def get_bus_policy() -> BusSecurityPolicy
```

**Source:** `bus_policy.py`, line 138

Returns the singleton `BusSecurityPolicy` instance, initialized from the `BUS_SECURITY_POLICY` env var on first call.

---

### `reset_bus_policy()`

```python
def reset_bus_policy() -> None
```

**Source:** `bus_policy.py`, line 155

Resets the singleton policy. Intended for testing.

---

## `bus_verifier.py` — Integrity Audit

### `VerificationResult`

```python
@dataclass
class VerificationResult:
    line_number: int
    timestamp: str
    from_id: str
    to_id: str
    msg_type: str
    is_signed: bool
    signature_valid: bool | None = None
    issue: str | None = None
```

**Source:** `bus_verifier.py`, line 37

---

### `BusAuditReport`

```python
@dataclass
class BusAuditReport:
    bus_path: str
    total_messages: int = 0
    signed_messages: int = 0
    unsigned_messages: int = 0
    verified_ok: int = 0
    verified_fail: int = 0
    verification_skipped: int = 0
    malformed_lines: int = 0
    duplicate_nonces: int = 0
    unknown_senders: int = 0
    timestamp_anomalies: int = 0
    sender_counts: dict[str, int] = field(default_factory=dict)
    type_counts: dict[str, int] = field(default_factory=dict)
    issues: list[str] = field(default_factory=list)
```

**Source:** `bus_verifier.py`, line 51

#### Properties and Methods

- `signing_coverage_pct` (property) — percentage of messages that are signed
- `to_dict()` — serialize to dictionary (line 76)
- `summary()` — human-readable multi-line summary (line 101)

---

### `audit_bus()`

```python
def audit_bus(
    bus_path: str | Path,
    secret: bytes | None = None,
    known_agents: set[str] | None = None,
) -> BusAuditReport
```

**Source:** `bus_verifier.py`, line 131

Performs a read-only integrity audit. Scans for signed/unsigned counts, signature verification, duplicate nonces, unknown senders, and timestamp anomalies (future timestamps >60s ahead, out-of-order). Never writes to the bus.

---

## `bus_utils.py` — Shared Parser

### `parse_bus_line()`

```python
def parse_bus_line(line: str) -> dict[str, str] | None
```

**Source:** `bus_utils.py`, line 14

Parses a single TSV bus line into a dict with keys `timestamp`, `from`, `to`, `type`, `message`. Returns `None` for header lines, blank lines, comments, and malformed rows. Preserves literal tab characters in the message field by joining extra columns back with `\t`.

---

## `bridge_client.py` — HTTP Bridge Client

### `post_to_remote_bus()`

```python
def post_to_remote_bus(
    host: str,
    from_agent: str,
    to_agent: str,
    msg_type: str,
    message: str,
    port: int = DEFAULT_PORT,
) -> bool
```

**Source:** `bridge_client.py`, line 165

Posts a message to a remote machine's bus via HTTP. Returns `True` on success. Sends `Authorization: Bearer <token>` when a bridge token is available.

---

### `post_to_remote_bus_result()`

```python
def post_to_remote_bus_result(
    host: str,
    from_agent: str,
    to_agent: str,
    msg_type: str,
    message: str,
    *,
    request_id: str | None = None,
    correlation_id: str | None = None,
    origin_machine: str | None = None,
    port: int = DEFAULT_PORT,
) -> dict
```

**Source:** `bridge_client.py`, line 132

Posts a message and returns a structured result dict:

```python
{
    "ok": bool,
    "status_code": int | None,
    "duplicate": bool,
    "body": dict,
    "permanent_error": bool,  # True for 400/401/403
    "error": str | None,
}
```

---

### `post_to_remote_bus_url_result()`

```python
def post_to_remote_bus_url_result(
    base_url: str,
    from_agent: str,
    to_agent: str,
    msg_type: str,
    message: str,
    *,
    request_id: str | None = None,
    correlation_id: str | None = None,
    origin_machine: str | None = None,
) -> dict
```

**Source:** `bridge_client.py`, line 45

Posts to a remote bus via a full base URL (e.g., `http://100.x.x.x:18790`). Returns the same structured result dict as `post_to_remote_bus_result()`.

---

### `health_check()`

```python
def health_check(host: str, port: int = DEFAULT_PORT) -> bool
```

**Source:** `bridge_client.py`, line 190

Checks if the remote bridge server is healthy by GETting `/health`. Returns `True` on HTTP 200.

---

### `bridge_host_from_url()`

```python
def bridge_host_from_url(base_url: str) -> tuple[str, int]
```

**Source:** `bridge_client.py`, line 157

Extracts host and port from a bridge base URL. Returns `(host, port)` with port defaulting to `DEFAULT_PORT` (18790).

---

### Constants

| Constant | Source | Value | Description |
|---|---|---|---|
| `DEFAULT_PORT` | line 21 | `18790` | Default bridge server port |
| `DEFAULT_TOKEN_FILE` | line 22 | `~/.config/foundermode/bus_bridge_token` | Default bridge token file path |

---

## `bridge_server.py` — HTTP Bridge Server

### `BusBridgeHandler`

```python
class BusBridgeHandler(BaseHTTPRequestHandler)
```

**Source:** `bridge_server.py`, line 169

HTTP handler for receiving remote bus messages.

#### Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/bus`, `/api/bus/send`, `/bus/post` | Receive a bus message |
| GET | `/health` | Health check (returns status, version, auth_enabled) |
| GET | `/bus/status` | Bus line count and last write timestamp |
| GET | `/bus/tail?n=50&date=YYYY-MM-DD` | Last N bus lines, optionally filtered by date |
| GET | `/bus/search?q=pattern&n=200` | Search bus lines by case-insensitive substring |

---

### `run_server()`

```python
def run_server(port: int = 18790, bind_all: bool = False) -> None
```

**Source:** `bridge_server.py`, line 506

Starts the bridge server. Binds to Tailscale interface by default; `bind_all=True` binds to `0.0.0.0`.

---

### `get_tailscale_ip()`

```python
def get_tailscale_ip() -> str | None
```

**Source:** `bridge_server.py`, line 473

Detects the Tailscale IP (`100.x.x.x`) via `tailscale ip -4` or `ifconfig` fallback.

---

### `_record_auth_event()`

```python
def _record_auth_event(
    *,
    outcome: str,
    client_ip: str,
    sender: str | None = None,
    reason: str | None = None,
    recipient: str | None = None,
    msg_type: str | None = None,
    request_id: str | None = None,
    correlation_id: str | None = None,
    origin_machine: str | None = None,
    bus_path: str | None = None,
) -> bool
```

**Source:** `bridge_server.py`, line 63

Appends an auth event to `auth_events.jsonl`. Valid outcomes: `success`, `failure`, `no_auth`, `accepted`, `duplicate`, `rejected`. Never writes the token itself. Returns `True` on success.
