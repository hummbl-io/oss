# API Reference: hummbl-governance

**Version:** 1.2.2
**Package:** `hummbl_governance`
**Python:** 3.11+
**Dependencies:** None (stdlib only)

---

## Installation

```bash
pip install -e ".[test]"  # local development
```

```python
import hummbl_governance
print(hummbl_governance.__version__)  # "1.2.2"
```

---

## KillSwitch

Emergency halt system with 4 graduated response modes.

```python
from hummbl_governance import KillSwitch, KillSwitchMode
```

### KillSwitchMode (Enum)

| Mode | Behavior |
|------|----------|
| `DISENGAGED` | Normal operation |
| `HALT_NONCRITICAL` | Block non-critical tasks, allow critical |
| `HALT_ALL` | Block all tasks |
| `EMERGENCY` | Immediate halt, preserve state |

### Constructor

```python
KillSwitch(
    state_dir: Path | str,
    require_hmac: bool = True,
    signing_secret: str | None = None,
    critical_tasks: frozenset[str] | None = None,
)
```

### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `engage` | `(mode: KillSwitchMode, reason: str = "") -> bool` | Activate kill switch at specified mode |
| `disengage` | `() -> bool` | Return to DISENGAGED mode |
| `check_task_allowed` | `(task_name: str) -> bool` | Check if a task is permitted under current mode |
| `check_or_raise` | `(task_name: str) -> None` | Raise `KillSwitchEngagedError` if task blocked |
| `get_status` | `() -> KillSwitchMode` | Current mode |
| `get_history` | `() -> list[KillSwitchEvent]` | Audit trail of mode changes |
| `subscribe` | `(callback: Callable[[KillSwitchMode], None]) -> None` | Register mode-change callback |
| `load_from_file` | `(state_dir: Path \| str) -> KillSwitch` | Classmethod: restore from persisted state |

### Example

```python
ks = KillSwitch(state_dir="/tmp/ks", require_hmac=False)
ks.engage(KillSwitchMode.HALT_NONCRITICAL, reason="High error rate")

if ks.check_task_allowed("send_email"):
    send_email()  # blocked — non-critical
if ks.check_task_allowed("health_check"):
    health_check()  # allowed — critical by default

ks.disengage()
```

---

## CircuitBreaker

Automatic failure detection and recovery wrapping external calls.

```python
from hummbl_governance import CircuitBreaker, CircuitBreakerState
```

### CircuitBreakerState (Enum)

| State | Behavior |
|-------|----------|
| `CLOSED` | Normal operation, counting failures |
| `OPEN` | All calls rejected immediately |
| `HALF_OPEN` | Single probe call allowed to test recovery |

### Constructor

```python
CircuitBreaker(
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    on_state_change: Callable[[CircuitBreakerState], None] | None = None,
)
```

### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `call` | `(func: Callable[..., T], *args, **kwargs) -> T` | Execute function through circuit breaker |
| `reset` | `() -> None` | Force reset to CLOSED |
| `state` | `@property -> CircuitBreakerState` | Current state |
| `failure_count` | `@property -> int` | Consecutive failures |
| `success_count` | `@property -> int` | Consecutive successes |
| `last_failure_time` | `@property -> float \| None` | Timestamp of last failure |

### Example

```python
cb = CircuitBreaker(failure_threshold=3, recovery_timeout=30.0)

try:
    result = cb.call(requests.get, "https://api.example.com/data")
except CircuitBreakerOpen:
    result = cached_fallback()
```

---

## CostGovernor

Budget tracking with soft/hard caps and ALLOW/WARN/DENY decisions.

```python
from hummbl_governance import CostGovernor
```

### Constructor

```python
CostGovernor(
    db_path: str | Path,
    soft_cap: float = 50.0,
    hard_cap: float | None = 100.0,
    currency: str = "USD",
    retention_days: int = 90,
    on_budget_alert: Callable[[BudgetStatus], None] | None = None,
)
```

### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `record_usage` | `(provider, model, tokens_in, tokens_out, cost, timestamp?, meta?) -> UsageRecord` | Log API usage |
| `get_daily_spend` | `(target_date?: date) -> float` | Total spend for a day |
| `get_spend_by_provider` | `(provider, start, end) -> dict` | Spend breakdown by provider |
| `get_spend_by_model` | `(start, end) -> list[dict]` | Spend breakdown by model |
| `check_budget_status` | `() -> BudgetStatus` | Returns decision: ALLOW, WARN, or DENY |
| `cleanup` | `(before?: datetime) -> int` | Purge old records, returns count deleted |
| `count` | `(start?: datetime, end?: datetime) -> int` | Count records in range |

### BudgetStatus

```python
@dataclass(frozen=True)
class BudgetStatus:
    current_spend: float
    soft_cap: float
    hard_cap: float | None
    currency: str
    threshold_percent: float
    decision: str          # "ALLOW", "WARN", or "DENY"
    rationale: str
```

### Example

```python
gov = CostGovernor(db_path="/tmp/costs.db", soft_cap=10.0, hard_cap=25.0)

gov.record_usage(
    provider="anthropic", model="claude-sonnet-4-6",
    tokens_in=1000, tokens_out=500, cost=0.015,
)

status = gov.check_budget_status()
if status.decision == "DENY":
    raise BudgetExceededError(status.rationale)
```

---

## DelegationToken

HMAC-SHA256 signed capability tokens for scoped agent delegation.

```python
from hummbl_governance import DelegationToken, DelegationTokenManager
```

### DelegationTokenManager Constructor

```python
DelegationTokenManager(secret: str | None = None)
```

### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `create_token` | `(issuer, subject, resource_selectors, ops_allowed, caveats?, expiry?, binding?) -> DelegationToken` | Mint a new signed token |
| `validate_token` | `(token, task_id?, contract_id?) -> tuple[bool, str \| None]` | Validate signature, expiry, binding |
| `check_least_privilege` | `(token, required_ops) -> bool` | Verify token grants only needed ops |

### DelegationToken (frozen dataclass)

| Field | Type | Description |
|-------|------|-------------|
| `token_id` | `str` | Unique identifier |
| `issuer` | `str` | Agent that created the token |
| `subject` | `str` | Agent authorized to use the token |
| `resource_selectors` | `list[ResourceSelector]` | Scoped resources |
| `ops_allowed` | `list[str]` | Permitted operations |
| `caveats` | `list[Caveat]` | Constraints (TIME_BOUND, RATE_LIMIT, etc.) |
| `expiry` | `str` | ISO 8601 expiration |
| `signature` | `str` | HMAC-SHA256 signature |

### Example

```python
from hummbl_governance.delegation import ResourceSelector

mgr = DelegationTokenManager(secret="my-signing-secret")
token = mgr.create_token(
    issuer="orchestrator",
    subject="worker-agent",
    resource_selectors=[ResourceSelector("api", "calendar", {})],
    ops_allowed=["read"],
    expiry="2026-03-24T00:00:00Z",
)

valid, error = mgr.validate_token(token)
assert valid
assert token.verify_signature("my-signing-secret")
```

---

## AuditLog

Append-only JSONL governance audit log with rotation, retention, and query API.

```python
from hummbl_governance import AuditLog
```

### Constructor

```python
AuditLog(
    base_dir: Path | str,
    retention_days: int = 180,
    enable_async: bool = False,
    require_signature: bool = True,
    file_prefix: str = "governance",
)
```

### Supported Tuple Types

`DCTX`, `CONTRACT`, `EVIDENCE`, `ATTEST`, `DCT`, `SYSTEM`

### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `append` | `(intent_id, task_id, tuple_type, tuple_data, signature?, ...) -> tuple[bool, str \| None]` | Write an audit entry |
| `query_by_intent` | `(intent_id, tuple_type?, since?) -> Iterator[AuditEntry]` | Query by intent ID |
| `query_by_task` | `(task_id, tuple_type?) -> Iterator[AuditEntry]` | Query by task ID |
| `query_by_entry_id` | `(entry_id) -> AuditEntry \| None` | Fetch single entry |
| `query_by_contract` | `(contract_id, tuple_type?) -> Iterator[AuditEntry]` | Query by contract |
| `query_amendments` | `(entry_id) -> Iterator[AuditEntry]` | Find amendments to an entry |
| `enforce_retention` | `() -> int` | Purge expired entries, returns count |
| `close` | `() -> None` | Flush and close |

### Example

```python
with AuditLog(base_dir="/tmp/audit", require_signature=False) as log:
    ok, entry_id = log.append(
        intent_id="intent-001",
        task_id="task-001",
        tuple_type="DCT",
        tuple_data={"issuer": "scheduler", "subject": "worker"},
    )

    for entry in log.query_by_task("task-001"):
        print(entry.tuple_type, entry.timestamp)
```

---

## AgentRegistry

Agent identity management with aliases, trust tiers, and deprecation tracking.

```python
from hummbl_governance import AgentRegistry
```

### Constructor

```python
AgentRegistry(
    agents: dict[str, dict[str, str]] | None = None,
    aliases: dict[str, str] | None = None,
    services: set[str] | None = None,
    deprecated: set[str] | None = None,
    retired: dict[str, str] | None = None,
)
```

### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `register_agent` | `(name, display?, trust?, status?) -> None` | Add an agent |
| `unregister_agent` | `(name) -> None` | Remove an agent |
| `add_alias` | `(alias, canonical) -> None` | Map alias to canonical name |
| `canonicalize` | `(sender) -> str` | Resolve alias to canonical name |
| `is_valid_sender` | `(sender) -> bool` | Check if sender is known |
| `is_deprecated` | `(sender) -> bool` | Check deprecation status |
| `get_trust_tier` | `(sender) -> str` | Get trust level |
| `get_status` | `(sender) -> str` | Get agent status |
| `retire_agent` | `(name, reason) -> None` | Mark agent as retired |
| `to_dict` / `from_dict` | Serialization | Persist/restore registry |

### Example

```python
reg = AgentRegistry()
reg.register_agent("claude", display="Claude Code", trust="high")
reg.register_agent("gemini", display="Gemini CLI", trust="low")
reg.add_alias("claude-code", "claude")

assert reg.canonicalize("claude-code") == "claude"
assert reg.get_trust_tier("gemini") == "low"
assert reg.is_valid_sender("claude")
```

---

## SchemaValidator

Stdlib-only JSON Schema validator supporting a Draft 2020-12 subset.

```python
from hummbl_governance import SchemaValidator
```

### Supported Keywords

`type`, `required`, `properties`, `enum`, `pattern`, `minimum`, `maximum`, `minLength`, `maxLength`, `minItems`, `maxItems`, `items`, `additionalProperties`, `const`, `oneOf`, `anyOf`

### Static Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `validate` | `(instance, schema, path?) -> list[str]` | Validate and return error list |
| `validate_file` | `(instance_path, schema_path) -> tuple[bool, list[str]]` | Validate file against schema file |
| `validate_dict` | `(entry, schema) -> tuple[bool, list[str]]` | Validate dict against schema |

### Example

```python
schema = {
    "type": "object",
    "required": ["name", "version"],
    "properties": {
        "name": {"type": "string", "minLength": 1},
        "version": {"type": "string", "pattern": r"^\d+\.\d+\.\d+$"},
    },
}

errors = SchemaValidator.validate({"name": "test", "version": "1.0.0"}, schema)
assert errors == []

errors = SchemaValidator.validate({"name": ""}, schema)
assert len(errors) > 0  # missing "version", empty "name"
```

---

*Copyright 2026 HUMMBL, LLC. Licensed under Apache 2.0.*
