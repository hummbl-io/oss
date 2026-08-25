# Getting Started

This guide covers installing hummbl-bus, posting your first message, using the CLI, and reading messages back from the bus.

## Installation

```bash
pip install hummbl-bus
```

hummbl-bus requires Python 3.11+ and has zero third-party dependencies — it uses only the Python standard library (`fcntl`, `hmac`, `json`, `urllib`, `http.server`, etc.).

## Your First Message

The canonical write path is `post_message()`, defined in `hummbl_bus/bus_writer_core.py` (line 1276) and re-exported from `hummbl_bus/bus_writer.py`. Every bus write — whether from Python, shell, or an agent — should go through this function to guarantee mutual exclusion via `fcntl.flock(LOCK_EX)`.

```python
from hummbl_bus.bus_writer import post_message

post_message(
    "/tmp/messages.tsv",
    from_id="devin",
    to_id="all",
    msg_type="STATUS",
    message="Hello from hummbl-bus!",
)
```

After running this, your bus file contains a single 5-column TSV line:

```
2026-06-25T14:30:00Z	devin	all	STATUS	Hello from hummbl-bus!
```

The five columns are: `timestamp_utc`, `from`, `to`, `type`, `message`. The timestamp is generated automatically in UTC with a `Z` suffix (see `_normalize_timestamp()` at line 188 of `bus_writer_core.py`).

### What Happens Under the Hood

When you call `post_message()`, the following steps execute in order (see `bus_writer_core.py` lines 1346–1564):

1. **Secret resolution** — checks for a per-agent `KeyManager` key, then falls back to the `BUS_SIGNING_SECRET` environment variable (line 1355).
2. **Security policy check** — `get_bus_policy().check_signing()` is called; this is a no-op at the default `PERMISSIVE` level (line 1372).
3. **Field validation** — `_validate_fields()` ensures all fields are non-empty strings and the message is under 64 KB (`MAX_MESSAGE_BYTES = 65536`, line 128). `_validate_content()` rejects null bytes and JSON payloads with more than 64 fields (line 949).
4. **Identity validation** — `_validate_sender_identity()` checks the sender against known agent IDs from the registry and roster. By default this logs warnings for unknown senders; set `enforce_sender_identity=True` to raise `ValueError` instead.
5. **Privileged type check** — `_validate_privileged_message_type()` rejects `DIRECTIVE` from non-human senders and `DECISION` from unauthorized agents (line 739).
6. **Timestamp generation** — if not provided, the current UTC time is used in `YYYY-MM-DDTHH:MM:SSZ` format.
7. **Message escaping** — `escape_message()` converts newlines to literal `\n` and tabs to spaces, ensuring the payload stays on a single TSV line (line 136).
8. **File locking and append** — `_append_tsv_line()` opens the file in append mode, acquires `fcntl.flock(LOCK_EX)`, writes the line, calls `f.flush()` and `os.fsync()`, then releases the lock (line 429).
9. **Permission hardening** — if the file was newly created, `harden_bus_file_permissions()` sets it to mode `0o660` (line 59 of `bus_writer_signing.py`).

## Using the CLI

hummbl-bus ships with a CLI entry point registered as `hummbl-bus` in `pyproject.toml` (line 29):

```toml
[project.scripts]
hummbl-bus = "hummbl_bus.bus_writer_cli:main"
```

Post a message directly from the command line:

```bash
python -m hummbl_bus.bus_writer devin all STATUS "Hello world"
```

The CLI accepts positional arguments `<from> <to> <type> <message>` and an optional `--bus PATH` flag to specify the bus file location. If `--bus` is omitted, the path is resolved from the `COORDINATION_BUS` environment variable, then from the git repo root, then from the default `hummbl_governance/_state/coordination/messages.tsv`.

### Bus Integrity Audit CLI

The verifier has its own CLI (`hummbl_bus/bus_verifier.py`, `main()` at line 270):

```bash
# Text summary
python -m hummbl_bus.bus_verifier --bus /tmp/messages.tsv

# JSON output
python -m hummbl_bus.bus_verifier --bus /tmp/messages.tsv --json

# Verify signatures with a secret file
python -m hummbl_bus.bus_verifier --bus /tmp/messages.tsv --secret-file key.json

# Quiet mode — print only issues, exit non-zero on problems
python -m hummbl_bus.bus_verifier --bus /tmp/messages.tsv --quiet
```

The audit exits with code `0` when clean and `1` when signature verification failures or duplicate nonces are found.

## Reading Bus Messages

### Simple Parsing

Use `parse_bus_line()` from `hummbl_bus/bus_utils.py` (line 14) for lightweight parsing:

```python
from hummbl_bus.bus_utils import parse_bus_line

with open("/tmp/messages.tsv", "r", encoding="utf-8") as f:
    for line in f:
        entry = parse_bus_line(line)
        if entry is None:
            continue  # skip headers, blanks, comments
        print(
            f"[{entry['timestamp']}] {entry['from']} -> {entry['to']}: {entry['message']}"
        )
```

`parse_bus_line()` returns a dict with keys `timestamp`, `from`, `to`, `type`, `message`, or `None` for header lines, blank lines, comments, and malformed rows. It preserves literal tab characters in the message field by joining extra columns back with `\t`.

### Verified Reading

For safety-critical consumers, use `read_verified_messages()` from `hummbl_bus/bus_writer_signing.py` (line 87). This function filters out messages with invalid HMAC signatures and can require signatures:

```python
from hummbl_bus.bus_writer_signing import read_verified_messages

# Read last 5 minutes, verify signatures
messages = read_verified_messages(
    "/tmp/messages.tsv",
    secret=b"your-32-byte-secret-here-1234567890",
    since_minutes=5,
    require_signature=True,
)

for msg in messages:
    print(
        f"[{msg['timestamp']}] {msg['sender']} -> {msg['recipient']}: {msg['message']}"
    )
```

When `secret` is `None`, the function falls back to the `BUS_SIGNING_SECRET` environment variable. When `require_signature=True`, unsigned messages are silently skipped.

### Full Audit

For a comprehensive integrity scan, use `audit_bus()` from `hummbl_bus/bus_verifier.py` (line 131):

```python
from hummbl_bus.bus_verifier import audit_bus

report = audit_bus("/tmp/messages.tsv", secret=b"your-secret")
print(report.summary())
```

The report includes total message count, signed vs unsigned counts, signature verification results, duplicate nonce detection, unknown senders, and timestamp anomalies.

## Next Steps

- [Architecture](../architecture/index.md) — understand the TSV format, locking mechanism, and bridge topology
- [Security](../security/index.md) — learn about HMAC signing, policy enforcement, and injection protection
- [Configuration](../configuration/index.md) — all environment variables for tuning bus behavior
- [Examples](../examples/index.md) — worked examples for signed messages and multi-agent coordination
