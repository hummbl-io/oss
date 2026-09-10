"""Deterministic runtime safety primitives for AI agents.

Zero third-party runtime dependencies (pure Python standard library).
"""

from __future__ import annotations

import base64
import contextlib
import enum
import hashlib
import hmac
import json
import logging
import sqlite3
import threading
import time
from collections import deque
from contextvars import ContextVar
from dataclasses import asdict, dataclass, field
from decimal import Decimal
from typing import Any, Callable, Dict, List, Optional, Iterator

# ---------------------------------------------------------
# Stdlib Observability & Tracing Context
# ---------------------------------------------------------
trace_id_var: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)

class JSONFormatter(logging.Formatter):
    """Stdlib-only JSON structured formatter for OSS log aggregators."""
    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "trace_id": trace_id_var.get()
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)

logger = logging.getLogger(__name__)
if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(JSONFormatter())
    logger.addHandler(_handler)
    logger.setLevel(logging.INFO)
# ---------------------------------------------------------

class KillSwitchState(enum.Enum):
    """4-stage operational kill switch states.

    NORMAL:     All executions allowed (default).
    SHADOW:     All executions allowed but flagged for observation. Use during
                rollout to observe what would be blocked before enforcing.
    RESTRICTED: Read-only executions allowed; write mutations blocked.
    ENGAGED:    All executions blocked (full fleet halt).
    """
    NORMAL = "NORMAL"
    SHADOW = "SHADOW"
    RESTRICTED = "RESTRICTED"
    ENGAGED = "ENGAGED"


class ActionType(enum.Enum):
    """Strict action types to prevent semantic spoofing."""
    TOOL_EXECUTION = "TOOL_EXECUTION"
    HEARTBEAT_TELEMETRY = "HEARTBEAT_TELEMETRY"
    BENCHMARK_PROBE = "BENCHMARK_PROBE"
    STATE_MUTATION = "STATE_MUTATION"
    SECURITY_OVERRIDE = "SECURITY_OVERRIDE"


class KillSwitchOpenError(Exception):
    """Raised when execution is attempted while KillSwitch is engaged."""
    pass


class KillSwitch:
    """Operational kill switch for AI agent fleets."""
    __slots__ = ["_state", "_lock"]

    def __init__(self, state: KillSwitchState = KillSwitchState.NORMAL) -> None:
        self._state = state
        self._lock = threading.RLock()
        logger.info(f"KillSwitch initialized in {state.name} state.")

    def set_state(self, new_state: KillSwitchState, auth_token: Optional[DelegationToken] = None, secret_key: Optional[str] = None) -> None:
        if not isinstance(new_state, KillSwitchState):
            raise TypeError("State must be a KillSwitchState enum.")
            
        with self._lock:
            # Cryptographic Monotonic Latching: Once ENGAGED, requires admin token to disengage.
            if self._state == KillSwitchState.ENGAGED and new_state != KillSwitchState.ENGAGED:
                if not auth_token or not secret_key or not auth_token.verify(secret_key, required_scope="admin:killswitch"):
                    logger.warning(f"Unauthorized attempt to disengage KillSwitch to {new_state.name}.")
                    raise PermissionError("Valid admin:killswitch token required to disengage an ENGAGED KillSwitch.")
            
            old_state = self._state
            self._state = new_state
            logger.info(f"KillSwitch state transitioned: {old_state.name} -> {new_state.name}")

    @property
    def state(self) -> KillSwitchState:
        with self._lock:
            return self._state

    def check_execution_allowed(self, is_read_only: bool = False) -> bool:
        with self._lock:
            if self._state == KillSwitchState.ENGAGED:
                return False
            if self._state == KillSwitchState.RESTRICTED and not is_read_only:
                return False
            return True

    @contextlib.contextmanager
    def guard(self, is_read_only: bool = False) -> Iterator[None]:
        """Atomic execution guard to prevent TOCTOU races."""
        with self._lock:
            if not self.check_execution_allowed(is_read_only):
                logger.warning(f"KillSwitch blocked execution. State: {self._state.name}")
                raise KillSwitchOpenError(f"Execution blocked. Switch state: {self._state.name}")
            yield


class CircuitBreakerOpenError(Exception):
    """Raised when an action is attempted on an open circuit breaker."""
    pass


class CircuitBreaker:
    """Deterministic circuit breaker for external API adapters."""
    __slots__ = ["name", "failure_threshold", "recovery_timeout", "failure_count", "last_failure_time", "is_open", "half_open_probe_active", "_lock"]

    def __init__(self, name: str, failure_threshold: int = 3, recovery_timeout: float = 30.0) -> None:
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.is_open = False
        self.half_open_probe_active = False
        self._lock = threading.RLock()
        logger.info(f"CircuitBreaker '{self.name}' initialized (threshold: {failure_threshold}).")

    def __enter__(self) -> CircuitBreaker:
        with self._lock:
            if self.is_open:
                if time.time() - self.last_failure_time > self.recovery_timeout:
                    if self.half_open_probe_active:
                        logger.debug(f"Circuit '{self.name}' HALF-OPEN. Probe already in flight.")
                        raise CircuitBreakerOpenError(f"Circuit '{self.name}' is HALF-OPEN. Probe already in flight.")
                    # Allow exactly one probe request
                    self.half_open_probe_active = True
                    logger.info(f"Circuit '{self.name}' HALF-OPEN. Allowing probe request.")
                else:
                    logger.warning(f"Circuit '{self.name}' OPEN. Fast failing request.")
                    raise CircuitBreakerOpenError(f"Circuit '{self.name}' is OPEN. Fast failing request.")
            return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        with self._lock:
            if exc_type is not None and issubclass(exc_type, Exception):
                self.failure_count += 1
                self.last_failure_time = time.time()
                self.half_open_probe_active = False
                logger.error(f"Circuit '{self.name}' failure recorded ({self.failure_count}/{self.failure_threshold}): {exc_type.__name__}")
                if self.failure_count >= self.failure_threshold and not self.is_open:
                    self.is_open = True
                    logger.critical(f"Circuit '{self.name}' TRIPPED OPEN.")
                return False  # Do not suppress exception
            elif exc_type is None:
                if self.is_open or self.failure_count > 0:
                    logger.info(f"Circuit '{self.name}' RECOVERED. Resetting to CLOSED.")
                self.failure_count = 0
                self.is_open = False
                self.half_open_probe_active = False
                return True
            return False


@dataclass
class DelegationToken:
    """HMAC-SHA256 cryptographically signed agent delegation token."""
    token_id: str
    issuer: str
    delegate: str
    scope: str
    issued_at: float
    expires_at: float
    signature: str

    @classmethod
    def issue(cls, issuer: str, delegate: str, scope: str, secret_key: str, ttl_seconds: float = 3600.0) -> DelegationToken:
        now = time.time()
        # Use JSON serialization to prevent delimiter collision attacks
        token_id_payload = json.dumps([issuer, delegate, now])
        token_id = hashlib.sha256(token_id_payload.encode()).hexdigest()[:16]
        expires_at = now + ttl_seconds
        payload = json.dumps([token_id, issuer, delegate, scope, now, expires_at])
        sig = hmac.new(secret_key.encode(), payload.encode(), hashlib.sha256).hexdigest()
        logger.info(f"Issued DelegationToken '{token_id}' to '{delegate}' (scope: {scope}).")
        return cls(
            token_id=token_id,
            issuer=issuer,
            delegate=delegate,
            scope=scope,
            issued_at=now,
            expires_at=expires_at,
            signature=sig,
        )

    def verify(self, secret_key: str, required_scope: Optional[str] = None) -> bool:
        if time.time() > self.expires_at:
            logger.warning(f"DelegationToken '{self.token_id}' rejected: EXPIRED.")
            return False
        payload = json.dumps([self.token_id, self.issuer, self.delegate, self.scope, self.issued_at, self.expires_at])
        expected_sig = hmac.new(secret_key.encode(), payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(self.signature, expected_sig):
            logger.warning(f"DelegationToken '{self.token_id}' rejected: INVALID SIGNATURE.")
            return False
        if required_scope and self.scope != "*" and self.scope != required_scope:
            logger.warning(f"DelegationToken '{self.token_id}' rejected: INSUFFICIENT SCOPE.")
            return False
        return True


class CostGovernor:
    """Token and dollar budget watchdog for LLM invocations."""
    __slots__ = ["max_budget_usd", "spend_usd", "_lock"]

    def __init__(self, max_budget_usd: float | Decimal) -> None:
        self.max_budget_usd = Decimal(str(max_budget_usd))
        self.spend_usd = Decimal("0.0")
        self._lock = threading.RLock()
        logger.info(f"CostGovernor initialized with budget: ${self.max_budget_usd}")

    def record_spend(self, amount_usd: float | Decimal) -> None:
        with self._lock:
            spend = Decimal(str(amount_usd))
            self.spend_usd += spend
            logger.info(f"CostGovernor recorded spend: ${spend}. Total: ${self.spend_usd}/${self.max_budget_usd}")

    def is_within_budget(self, prospective_spend: float | Decimal = 0.0) -> bool:
        with self._lock:
            within = (self.spend_usd + Decimal(str(prospective_spend))) <= self.max_budget_usd
            if not within:
                logger.warning(f"CostGovernor budget exhausted/exceeded! Spend: ${self.spend_usd}, Prospective: ${prospective_spend}, Limit: ${self.max_budget_usd}")
            return within


@dataclass
class AuditRecord:
    """Tamper-evident, cryptographically chained audit log entry."""
    seq: int
    timestamp: float
    agent_id: str
    action_type: str
    payload: Dict[str, Any]
    prev_hash: str
    entry_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AuditBus:
    """Append-only, SHA-256 hash-chained audit bus with SQLite and JSONL backends."""

    def __init__(self, log_file: Optional[str] = None, db_file: Optional[str] = None) -> None:
        self.log_file = log_file
        self.db_file = db_file
        # Capped deque prevents OOM memory leak on long-running instances
        self.records: deque[AuditRecord] = deque(maxlen=1000)
        self._last_hash = "0" * 64
        self._seq = 0
        self._lock = threading.RLock()

        if self.db_file:
            conn = sqlite3.connect(self.db_file)
            try:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS audit_events (
                        seq INTEGER PRIMARY KEY,
                        timestamp REAL,
                        agent_id TEXT,
                        action_type TEXT,
                        payload TEXT,
                        prev_hash TEXT,
                        entry_hash TEXT
                    )
                """)
                # Restore sequence state to prevent SQLite IntegrityError on restart
                cursor = conn.execute("SELECT seq, entry_hash FROM audit_events ORDER BY seq DESC LIMIT 1")
                row = cursor.fetchone()
                if row:
                    self._seq = row[0]
                    self._last_hash = row[1]
                conn.commit()
                # Resume chain from the last persisted record so new events
                # extend the existing chain instead of resetting it.
                row = conn.execute(
                    "SELECT seq, entry_hash FROM audit_events ORDER BY seq DESC LIMIT 1"
                ).fetchone()
                if row is not None:
                    self._seq = row[0]
                    self._last_hash = row[1]
            finally:
                conn.close()
        logger.info(f"AuditBus initialized (SQLite: {bool(self.db_file)}, Seq Start: {self._seq})")

    def record_event(self, agent_id: str, action_type: ActionType | str, payload: Dict[str, Any]) -> AuditRecord:
        """Record an event with deterministic cryptographic chaining."""
        with self._lock:
            self._seq += 1
            now = time.time()
            
            act_type_str = action_type.value if isinstance(action_type, ActionType) else str(action_type)
            
            # Safe JSON serialization fallback for datetimes/UUIDs
            payload_str = json.dumps(payload, sort_keys=True, default=str)
            
            # Use JSON serialization for hash payload to prevent injection parsing ambiguity
            hash_payload = json.dumps([self._seq, f"{now:.6f}", agent_id, act_type_str, payload_str, self._last_hash])
            entry_hash = hashlib.sha256(hash_payload.encode()).hexdigest()

            record = AuditRecord(
                seq=self._seq,
                timestamp=now,
                agent_id=agent_id,
                action_type=act_type_str,
                payload=payload,
                prev_hash=self._last_hash,
                entry_hash=entry_hash,
            )

            self._last_hash = entry_hash
            self.records.append(record)

            if self.log_file:
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(record.to_dict()) + "\n")

            if self.db_file:
                conn = sqlite3.connect(self.db_file)
                try:
                    conn.execute(
                        "INSERT INTO audit_events VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (record.seq, record.timestamp, record.agent_id, record.action_type, payload_str, record.prev_hash, record.entry_hash)
                    )
                    conn.commit()
                finally:
                    conn.close()
                    
            logger.info(f"AuditBus recorded '{act_type_str}' for agent '{agent_id}' (Seq: {self._seq})")
            return record

    def verify_chain(self, external_records: Optional[List[AuditRecord]] = None) -> bool:
        """Mathematically verify the hash integrity across records."""
        records_to_verify = external_records if external_records is not None else list(self.records)
        if not records_to_verify:
            return True
            
        expected_prev = records_to_verify[0].prev_hash
        for record in records_to_verify:
            if record.prev_hash != expected_prev:
                logger.error(f"AuditBus verification FAILED at seq {record.seq}: prev_hash mismatch.")
                return False
            payload_str = json.dumps(record.payload, sort_keys=True, default=str)
            hash_payload = json.dumps([record.seq, f"{record.timestamp:.6f}", record.agent_id, record.action_type, payload_str, record.prev_hash])
            calculated_hash = hashlib.sha256(hash_payload.encode()).hexdigest()
            if record.entry_hash != calculated_hash:
                logger.error(f"AuditBus verification FAILED at seq {record.seq}: entry_hash tampering detected.")
                return False
            expected_prev = record.entry_hash
        logger.info("AuditBus chain cryptographic verification passed.")
        return True
