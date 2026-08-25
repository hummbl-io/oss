# Integrations

How to integrate hummbl-bus into agents, consume bus messages programmatically, and set up the bridge client/server for cross-machine coordination.

## Embedding the Bus Writer in Agents

Every agent that participates in HUMMBL coordination should post messages through `post_message()` — the canonical write path that guarantees mutual exclusion via `flock`, validates fields, enforces security policy, and optionally signs messages.

### Basic Agent Integration

```python
from hummbl_bus.bus_writer import post_message


class MyAgent:
    def __init__(self, agent_id: str, bus_path: str):
        self.agent_id = agent_id
        self.bus_path = bus_path

    def post_status(self, message: str):
        """Post a STATUS message to the bus."""
        post_message(
            self.bus_path,
            from_id=self.agent_id,
            to_id="all",
            msg_type="STATUS",
            message=message,
        )

    def handoff_to(self, recipient: str, message: str):
        """Hand off work to another agent."""
        post_message(
            self.bus_path,
            from_id=self.agent_id,
            to_id=recipient,
            msg_type="HANDOFF",
            message=message,
        )

    def report_blocked(self, message: str):
        """Report a blocking issue."""
        post_message(
            self.bus_path,
            from_id=self.agent_id,
            to_id="all",
            msg_type="BLOCKED",
            message=message,
        )
```

### Signed Agent Integration

For production agents, enable signing via the `BUS_SIGNING_SECRET` environment variable or pass a secret explicitly:

```python
import os
from hummbl_bus.bus_writer import post_message


class SignedAgent:
    def __init__(self, agent_id: str, bus_path: str):
        self.agent_id = agent_id
        self.bus_path = bus_path
        # Secret is auto-resolved from BUS_SIGNING_SECRET in post_message()
        # No need to pass it explicitly if the env var is set

    def post(self, msg_type: str, message: str, to_id: str = "all"):
        post_message(
            self.bus_path,
            from_id=self.agent_id,
            to_id=to_id,
            msg_type=msg_type,
            message=message,
        )
```

Set the environment variable before running the agent:

```bash
export BUS_SIGNING_SECRET="$(openssl rand -hex 32)"
export BUS_SECURITY_POLICY=strict
python my_agent.py
```

### Structured Event Agent

For machine-parsable payloads, use `post_structured_event()`:

```python
from hummbl_bus.bus_writer import post_structured_event, generate_correlation_id


class StructuredAgent:
    def __init__(self, agent_id: str, bus_path: str):
        self.agent_id = agent_id
        self.bus_path = bus_path

    def report_milestone(self, content: str, metadata: dict):
        post_structured_event(
            self.bus_path,
            from_id=self.agent_id,
            to_id="all",
            msg_type="MILESTONE",
            content=content,
            correlation_id=generate_correlation_id(f"milestone-{self.agent_id}"),
            metadata=metadata,
        )
```

## Consuming Bus Messages

### Simple Polling with parse_bus_line()

For lightweight consumers, use `parse_bus_line()` from `bus_utils.py`:

```python
from hummbl_bus.bus_utils import parse_bus_line


def read_recent_messages(bus_path: str, since_timestamp: str = "") -> list[dict]:
    """Read messages newer than the given timestamp."""
    messages = []
    with open(bus_path, "r", encoding="utf-8") as f:
        for line in f:
            entry = parse_bus_line(line)
            if entry is None:
                continue
            if entry["timestamp"] > since_timestamp:
                messages.append(entry)
    return messages
```

### Verified Message Reading

For safety-critical consumers (kill switches, circuit breakers), use `read_verified_messages()` to filter out tampered messages:

```python
from hummbl_bus.bus_writer_signing import read_verified_messages


def check_for_kill_switch(bus_path: str, secret: bytes) -> bool:
    """Check for SAFETY messages in the last 5 minutes (verified only)."""
    messages = read_verified_messages(
        bus_path,
        secret=secret,
        msg_type_filter="SAFETY",
        since_minutes=5,
        require_signature=True,
    )
    for msg in messages:
        if "KILL_SWITCH" in msg["message"]:
            return True
    return False
```

When `require_signature=True`, only messages that are both signed AND verified are returned. Messages with invalid signatures are silently skipped (with a warning logged).

### Full Bus Audit

For monitoring and compliance, run `audit_bus()` periodically:

```python
from hummbl_bus.bus_verifier import audit_bus


def daily_bus_audit(bus_path: str, secret: bytes):
    report = audit_bus(bus_path, secret=secret)
    print(report.summary())

    if report.verified_fail > 0:
        alert_security_team(f"{report.verified_fail} signature failures detected")
    if report.duplicate_nonces > 0:
        alert_security_team(f"{report.duplicate_nonces} duplicate nonces (replay?)")
    if report.signing_coverage_pct < 80:
        alert_ops_team(f"Signing coverage only {report.signing_coverage_pct:.1f}%")

    return report
```

### Unescaping Message Content

When reading raw bus lines, use `unescape_message()` to restore original formatting:

```python
from hummbl_bus.bus_utils import parse_bus_line
from hummbl_bus.bus_writer import unescape_message

with open("/tmp/messages.tsv", "r") as f:
    for line in f:
        entry = parse_bus_line(line)
        if entry:
            original = unescape_message(entry["message"])
            print(original)
```

## Cross-Machine Bridge Setup

### Architecture

```
Machine A (agent host)                    Machine B (bus host)
┌─────────────────────┐                  ┌─────────────────────────┐
│  Agent process      │                  │  bridge_server.py       │
│  + bridge_client    │  ── HTTP POST ──▶│  (ThreadingHTTPServer)  │
│                     │  Bearer token    │                         │
│  BUS_BRIDGE_TOKEN   │                  │  post_message()         │
│  = "shared-secret"  │                  │  → messages.tsv         │
└─────────────────────┘                  │                         │
                                         │  GET /bus/tail          │
┌─────────────────────┐                  │  GET /bus/search        │
│  Machine C (agent)  │  ── HTTP POST ──▶│  GET /bus/status        │
│  + bridge_client    │                  │  GET /health            │
└─────────────────────┘                  └─────────────────────────┘
```

### Step 1: Start the Bridge Server

On the bus host machine (Machine B):

```bash
# Generate a shared token
export BUS_BRIDGE_TOKEN="$(openssl rand -hex 32)"

# Start the server (binds to Tailscale interface)
python -m hummbl_bus.bridge_server --port 18790
```

The server prints its binding address and auth status. Verify it's running:

```bash
curl http://<tailscale-ip>:18790/health
# {"status": "up", "service": "bus-bridge", "version": "1.3", "auth_enabled": true}
```

### Step 2: Configure Bridge Clients

On each agent machine (A, C):

```bash
export BUS_BRIDGE_TOKEN="same-token-as-server"
```

Optionally, store the token in a file with mode 600:

```bash
mkdir -p ~/.config/foundermode
echo -n "your-token-here" > ~/.config/foundermode/bus_bridge_token
chmod 600 ~/.config/foundermode/bus_bridge_token
```

### Step 3: Post Messages from Remote Machines

From the CLI:

```bash
python -m hummbl_bus.bridge_client <tailscale-ip> devin all STATUS "Hello from Machine A"
```

From Python:

```python
from hummbl_bus.bridge_client import post_to_remote_bus_result

result = post_to_remote_bus_result(
    "100.64.0.1",
    from_agent="devin",
    to_agent="all",
    msg_type="STATUS",
    message="Cross-machine coordination",
    request_id="macbookA-devin-abc123",
    origin_machine="macbookA",
)

if result["ok"]:
    print(f"Success! duplicate={result['duplicate']}")
elif result["permanent_error"]:
    # 400/401/403 — do not retry
    print(f"Permanent error: {result['error']}")
else:
    # Transient — safe to retry
    print(f"Transient error: {result['error']}")
```

### Step 4: Read Messages via Bridge API

Any machine can read the bus via GET endpoints:

```bash
# Last 50 messages
curl http://100.64.0.1:18790/bus/tail?n=50

# Messages from a specific date
curl http://100.64.0.1:18790/bus/tail?date=2026-06-25

# Search for "BLOCKED" messages
curl http://100.64.0.1:18790/bus/search?q=BLOCKED

# Bus status
curl http://100.64.0.1:18790/bus/status
```

### Remote-First Write Mode

For a single authoritative bus across all machines, set `BUS_CANONICAL_BRIDGE_URL` on agent machines. This makes `post_message()` post directly to the bridge without local fallback:

```bash
export BUS_CANONICAL_BRIDGE_URL="http://100.64.0.1:18790"
export BUS_BRIDGE_TOKEN="shared-secret"
export BUS_ORIGIN_MACHINE="macbookA"
```

```python
from hummbl_bus.bus_writer import post_message

# This posts directly to the canonical bridge — no local file write
post_message(
    "ignored-in-remote-first-mode.tsv",  # bus_path is bypassed
    from_id="devin",
    to_id="all",
    msg_type="STATUS",
    message="Remote-first write",
)
```

On transient failure, the message is spooled for later retry. On permanent failure (400/401/403), it is dead-lettered and `OSError` is raised.

## Integration with External Systems

### Open Brain Relay

When `OPEN_BRAIN_RELAY_URL` is set, every local bus write is also forwarded to the Open Brain server's `/bus/post` endpoint (best-effort, never raises):

```bash
export OPEN_BRAIN_RELAY_URL="http://100.109.69.16:11435"
export OPEN_BRAIN_TOKEN="relay-token"
```

### Dashboard Integration

When `BUS_REMOTE_URL` is set, `post_message()` POSTs to a dashboard's `/bus` endpoint with an `X-Dashboard-Token` header:

```bash
export BUS_REMOTE_URL="http://dashboard.example.com"
export DASHBOARD_WRITE_TOKEN="dashboard-token"
```

### CI/CD Integration

Use the verifier CLI in quiet mode as a CI gate:

```bash
#!/bin/bash
# bus-audit-gate.sh
python -m hummbl_bus.bus_verifier \
    --bus "$COORDINATION_BUS" \
    --secret-file "$BUS_SECRET_FILE" \
    --quiet
exit $?
# Exit 0 = clean, Exit 1 = issues found
```

### Signal Lane (Transport-Only)

The bus can optionally fan out selected high-priority events to Signal in a constrained transport role:

- Transport only (never source-of-truth).
- Dry-run first by default; explicit enablement required for live delivery.
- Receipt-first workflow: every candidate event is paired with a receipt.
- Bounded event classes and explicit rate limits.

See: [Signal lane policy](./signal-lane.md).
