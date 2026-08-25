# Examples

Worked examples covering signed and unsigned messages, policy enforcement scenarios, bridge client/server setup, and multi-agent coordination patterns. All examples are grounded in the actual source code.

## Unsigned Messages

The simplest case — no signing secret is configured, so messages are written as plain text in the 5th TSV column.

```python
from hummbl_bus.bus_writer import post_message

post_message(
    "/tmp/messages.tsv",
    from_id="devin",
    to_id="all",
    msg_type="STATUS",
    message="Build complete, all tests passing",
)
```

Resulting bus line:

```
2026-06-25T14:30:00Z	devin	all	STATUS	Build complete, all tests passing
```

The message column is plain text. `escape_message()` (line 136 of `bus_writer_core.py`) has converted any newlines to literal `\n` and tabs to spaces.

## Signed Messages

When a signing secret is available, the message column is wrapped in a JSON signing envelope.

### Explicit Secret

```python
from hummbl_bus.bus_writer import post_message

secret = b"my-32-byte-signing-secret-here-1234567890ab"

post_message(
    "/tmp/messages.tsv",
    from_id="devin",
    to_id="codex",
    msg_type="HANDOFF",
    message="PR #42 ready for your review",
    secret=secret,
)
```

Resulting bus line:

```
2026-06-25T14:30:00Z	devin	codex	HANDOFF	{"c":"PR #42 ready for your review","n":"20260625143000a1b2c3d4","s":"a1b2c3d4e5f6...64hexchars"}
```

The 5th column is a JSON object with keys `c` (content), `n` (nonce), `s` (signature). The TSV shape is preserved — the JSON string contains no literal tabs or newlines.

### Auto-Signing via Environment Variable

```bash
export BUS_SIGNING_SECRET="my-32-byte-signing-secret-here-1234567890ab"
```

```python
from hummbl_bus.bus_writer import post_message

# No secret= parameter needed — auto-resolved from BUS_SIGNING_SECRET
post_message(
    "/tmp/messages.tsv",
    from_id="devin",
    to_id="all",
    msg_type="STATUS",
    message="Auto-signed message",
)
```

The secret is resolved by `_resolve_signing_secret()` (line 33 of `bus_writer_signing.py`), which checks `BUS_SIGNING_SECRET` and requires at least 32 bytes.

### Reading Signed Messages

```python
from hummbl_bus.bus_writer_signing import read_verified_messages

secret = b"my-32-byte-signing-secret-here-1234567890ab"

# Read only verified signed messages from the last 10 minutes
messages = read_verified_messages(
    "/tmp/messages.tsv",
    secret=secret,
    since_minutes=10,
    require_signature=True,
)

for msg in messages:
    print(
        f"[{msg['timestamp']}] {msg['sender']} -> {msg['recipient']}: {msg['message']}"
    )
```

Messages with invalid signatures are silently skipped. Unsigned messages are also skipped when `require_signature=True`.

## Policy Enforcement Scenarios

### PERMISSIVE (Default)

```python
from hummbl_bus.bus_writer import post_message

# No BUS_SECURITY_POLICY set — defaults to permissive
post_message(
    "/tmp/messages.tsv",
    from_id="devin",
    to_id="all",
    msg_type="STATUS",
    message="Unsigned message accepted silently",
)
# → Message written, no warning
```

### WARN

```bash
export BUS_SECURITY_POLICY=warn
```

```python
from hummbl_bus.bus_writer import post_message

post_message(
    "/tmp/messages.tsv",
    from_id="devin",
    to_id="all",
    msg_type="STATUS",
    message="Unsigned message with warning",
)
# → Message written, warning logged:
#   "Unsigned bus message from devin (type=STATUS) -- set BUS_SECURITY_POLICY=strict to enforce signing"
```

### STRICT

```bash
export BUS_SECURITY_POLICY=strict
```

```python
from hummbl_bus.bus_writer import post_message

post_message(
    "/tmp/messages.tsv",
    from_id="devin",
    to_id="all",
    msg_type="STATUS",
    message="Unsigned message in strict mode",
)
# → ValueError raised:
#   "Bus security policy STRICT: unsigned message rejected from devin (type=STATUS).
#    Provide a signing secret via --sign or --secret-file."
```

### STRICT with Exempt Type

```bash
export BUS_SECURITY_POLICY=strict
```

```python
from hummbl_bus.bus_writer import post_message

# HEARTBEAT is exempt from signing requirements by default
post_message(
    "/tmp/messages.tsv",
    from_id="devin",
    to_id="all",
    msg_type="HEARTBEAT",
    message="alive",
)
# → Message written (HEARTBEAT is in allow_unsigned_types)
```

## Privileged Message Type Examples

### DIRECTIVE (Human Only)

```python
from hummbl_bus.bus_writer import post_message

# Human sender — allowed
post_message(
    "/tmp/messages.tsv",
    from_id="human",
    to_id="all",
    msg_type="DIRECTIVE",
    message="Prioritize security audit over feature work",
)
# → Message written

# Agent sender — rejected
post_message(
    "/tmp/messages.tsv",
    from_id="devin",
    to_id="all",
    msg_type="DIRECTIVE",
    message="Prioritize security audit",
)
# → ValueError: "Privileged message type 'DIRECTIVE' from 'devin' not permitted.
#    DIRECTIVE is human-only..."
```

### DECISION (Steward Proxy)

```python
from hummbl_bus.bus_writer import post_message

# Steward proxy with required audit markers — allowed
post_message(
    "/tmp/messages.tsv",
    from_id="claude-code",
    to_id="all",
    msg_type="DECISION",
    message="On-behalf-of: human. Per operator instruction, shipping v2.1 today.",
)
# → Message written (has audit flag + citation pattern "operator instruction")

# Steward proxy without audit markers — rejected
post_message(
    "/tmp/messages.tsv",
    from_id="claude-code",
    to_id="all",
    msg_type="DECISION",
    message="Shipping v2.1 today",
)
# → ValueError: "Steward proxy DECISION from 'claude-code' requires
#    'On-behalf-of: human' marker in message body."
```

## Structured Events

```python
from hummbl_bus.bus_writer import post_structured_event

post_structured_event(
    "/tmp/messages.tsv",
    from_id="devin",
    to_id="codex",
    msg_type="MILESTONE",
    content="Phase 1 complete: all unit tests green",
    correlation_id="corr-a1b2c3d4e5f6",
    metadata={"phase": 1, "test_count": 142, "duration_seconds": 3600},
)
```

The 5th column contains a JSON envelope with schema `hummbl_governance.bus.event.v1`:

```json
{"schema":"hummbl_governance.bus.event.v1","timestamp":"2026-06-25T14:30:00Z","sender":"devin","recipient":"codex","type":"MILESTONE","content":"Phase 1 complete: all unit tests green","correlation_id":"corr-a1b2c3d4e5f6","metadata":{"phase":1,"test_count":142,"duration_seconds":3600}}
```

Parse it back:

```python
from hummbl_bus.bus_writer import parse_structured_event

event = parse_structured_event(message_column)
if event:
    print(event["content"], event.get("metadata"))
```

## Bridge Client/Server Setup

### Start the Bridge Server

On machine B (the bus host):

```bash
export BUS_BRIDGE_TOKEN="shared-secret-token"
python -m hummbl_bus.bridge_server --port 18790
```

Output:

```
Binding to Tailscale interface: 100.64.0.1
Bus Bridge Server running on http://100.64.0.1:18790
Endpoints: POST /bus, GET /health, GET /bus/status, GET /bus/tail, GET /bus/search
Auth: POST endpoints require Authorization: Bearer <BUS_BRIDGE_TOKEN>
```

### Post from a Remote Machine

On machine A:

```bash
export BUS_BRIDGE_TOKEN="shared-secret-token"
python -m hummbl_bus.bridge_client 100.64.0.1 devin all STATUS "Hello from machine A"
```

### Programmatic Bridge Client

```python
from hummbl_bus.bridge_client import post_to_remote_bus_result, health_check

# Health check first
if not health_check("100.64.0.1", port=18790):
    print("Bridge is down!")
    exit(1)

# Post with structured result
result = post_to_remote_bus_result(
    "100.64.0.1",
    from_agent="devin",
    to_agent="all",
    msg_type="STATUS",
    message="Remote post via Python",
    request_id="macbook-devin-a1b2c3d4e5f6",
    origin_machine="macbook",
    port=18790,
)

if result["ok"]:
    print(f"Posted! duplicate={result['duplicate']}")
elif result["permanent_error"]:
    print(f"Permanent error: {result['error']}")
else:
    print(f"Transient error: {result['error']}")
```

### Reading Bus Messages via Bridge

```bash
# Get last 50 messages
curl http://100.64.0.1:18790/bus/tail?n=50

# Search for messages containing "error"
curl http://100.64.0.1:18790/bus/search?q=error

# Get bus status
curl http://100.64.0.1:18790/bus/status
```

## Multi-Agent Coordination Patterns

### Task Handoff

Agent A posts a HANDOFF, Agent B polls for messages addressed to it:

```python
# Agent A (devin) hands off to Agent B (codex)
from hummbl_bus.bus_writer import post_message

post_message(
    "/tmp/messages.tsv",
    from_id="devin",
    to_id="codex",
    msg_type="HANDOFF",
    message="I've completed the API refactor. Your turn to update the docs.",
    correlation_id="task-refactor-001",
)
```

```python
# Agent B (codex) reads its messages
from hummbl_bus.bus_writer_signing import read_verified_messages

messages = read_verified_messages(
    "/tmp/messages.tsv",
    since_minutes=60,
    msg_type_filter="HANDOFF",
)

for msg in messages:
    if msg["recipient"] == "codex":
        print(f"Handoff from {msg['sender']}: {msg['message']}")
```

### Broadcast Status

```python
from hummbl_bus.bus_writer import post_message

post_message(
    "/tmp/messages.tsv",
    from_id="devin",
    to_id="all",
    msg_type="SITREP",
    message="Sprint day 3: 8/12 tasks complete, on track for Friday deadline",
)
```

### Heartbeat (Unsigned, Exempt)

```python
from hummbl_bus.bus_writer import post_message

# Even in STRICT mode, HEARTBEAT is exempt from signing
post_message(
    "/tmp/messages.tsv",
    from_id="devin",
    to_id="all",
    msg_type="HEARTBEAT",
    message="alive",
)
```

### Dead Letter on Failure

When a remote-first write encounters a permanent error, the message is preserved in the dead-letter queue:

```python
# With BUS_CANONICAL_BRIDGE_URL set and a 401 response:
# → write_dead_letter() is called with the failed payload
# → The dead letter is written to dead_letters.jsonl as JSONL
# → OSError is raised to the caller

# Dead letters can be inspected:
import json

with open("hummbl_governance/_state/coordination/dead_letters.jsonl") as f:
    for line in f:
        record = json.loads(line)
        print(f"[{record['timestamp']}] {record['source']}: {record['reason']}")
```

## Bus Integrity Audit

```python
from hummbl_bus.bus_verifier import audit_bus

secret = b"my-32-byte-signing-secret-here-1234567890ab"
report = audit_bus("/tmp/messages.tsv", secret=secret)

print(report.summary())
print(f"\nSigning coverage: {report.signing_coverage_pct:.1f}%")
print(
    f"Top senders: {dict(sorted(report.sender_counts.items(), key=lambda x: -x[1])[:5])}"
)
```

Sample output:

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
    - Line 67: future timestamp 2027-01-01T00:00:00Z
    - Line 89: unknown sender 'rogue-agent'
    - Line 102: signature verification FAILED (from=agent-y)

Signing coverage: 69.0%
Top senders: {'devin': 52, 'codex': 38, 'claude-code': 25, 'human': 15, 'apex': 12}
```
