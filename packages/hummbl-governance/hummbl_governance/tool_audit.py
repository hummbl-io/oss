"""Tool-call audit hook for AI agent integrations.

This module provides a small, framework-agnostic wrapper for tool execution.
Each invocation is logged to AuditLog with intent/task context and outcome.

Usage:
    from hummbl_governance import AuditLog, ToolCallAuditor

    with AuditLog("/tmp/audit", require_signature=False) as audit:
        fence = CapabilityFence(allowed=["tool:search"])
        hook = ToolCallAuditor(
            audit_log=audit,
            intent_id="i-1",
            task_id="t-1",
            capability_fence=fence,
            signature="optional-signature",
        )

        safe_search = hook.wrap("search", search_tool)
        safe_search("query")
"""

from __future__ import annotations

import time
import uuid
from collections.abc import Callable
from collections.abc import Mapping
from typing import Any

from hummbl_governance.audit_log import AuditLog
from hummbl_governance.capability_fence import CapabilityDenied, CapabilityFence
from hummbl_governance.transition_receipt import stable_sha256


class ToolCallAuditor:
    """Wrap callable tools with capability checks and governance audit logging."""

    def __init__(
        self,
        audit_log: AuditLog,
        intent_id: str,
        task_id: str,
        capability_fence: CapabilityFence | None = None,
        signature: str | None = None,
        actor_id: str = "tool-auditor",
    ) -> None:
        self._audit_log = audit_log
        self._intent_id = intent_id
        self._task_id = task_id
        self._capability_fence = capability_fence
        self._signature = signature
        self._actor_id = actor_id

    def wrap(
        self,
        tool_name: str,
        tool_fn: Callable[..., Any],
        *,
        capability: str | None = None,
        context: Mapping[str, Any] | Callable[..., Mapping[str, Any]] | None = None,
    ) -> Callable[..., Any]:
        """Wrap a tool function so each invocation emits transition-style metadata.

        Args:
            tool_name: Human-readable tool identifier.
            tool_fn: Callable to invoke.
            capability: Optional capability string. Defaults to "tool:<tool_name>".
            context: Optional context payload or callable that builds context
                from ``*args`` / ``**kwargs`` for transition hashes.

        Returns:
            Callable with identical invocation signature.
        """
        required_capability = capability or f"tool:{tool_name}"
        guard = self._capability_fence

        def wrapped(*args: Any, **kwargs: Any) -> Any:
            started_ms = time.perf_counter_ns() / 1_000_000
            transition_id = f"tool-call-{uuid.uuid4().hex}"
            call_context = self._coerce_context(context, args=args, kwargs=kwargs)

            action_hash, action_hash_error = self._hash_payload(
                {"tool_name": tool_name, "args": args, "kwargs": kwargs},
            )
            context_payload = (
                call_context if call_context is not None else {"__context_absent__": True}
            )
            context_hash, context_hash_error = self._hash_payload(context_payload)

            decision = "UNKNOWN"
            terminal_outcome = "failed_before_execution"
            try:
                if guard is not None:
                    guard.check(required_capability)
                decision = "allow"
                terminal_outcome = None
            except CapabilityDenied:
                decision = "deny"
                terminal_outcome = "blocked"
                denied_ms = time.perf_counter_ns() / 1_000_000 - started_ms
                transition_event = {
                    "event": "tool_transition",
                    "phase": "authorization",
                    "transition_id": transition_id,
                    "tool_name": tool_name,
                    "capability": required_capability,
                    "actor_id": self._actor_id,
                    "action_hash": action_hash,
                    "context_hash": context_hash,
                    "decision": decision,
                    "terminal_outcome": terminal_outcome,
                }
                if action_hash_error or context_hash_error:
                    transition_event["hash_error"] = action_hash_error or context_hash_error
                self._append_event(
                    tool_name=tool_name,
                    capability=required_capability,
                    event="tool_transition",
                    outcome="denied",
                    duration_ms=denied_ms,
                    status="blocked_by_capability",
                    transition_id=transition_id,
                    terminal_outcome="blocked",
                    event_payload=transition_event,
                )
                self._append_event(
                    tool_name=tool_name,
                    capability=required_capability,
                    event="tool_call",
                    outcome="denied",
                    duration_ms=denied_ms,
                    status="blocked_by_capability",
                    transition_id=transition_id,
                    terminal_outcome="blocked",
                    error_type="CapabilityDenied",
                    event_payload={
                        "phase": "execution",
                        "tool_name": tool_name,
                        "capability": required_capability,
                        "actor_id": self._actor_id,
                        "action_hash": action_hash,
                        "context_hash": context_hash,
                        "decision": decision,
                        "terminal_outcome": "blocked",
                    },
                )
                raise

            transition_event: dict[str, Any] = {
                "event": "tool_transition",
                "phase": "authorization",
                "transition_id": transition_id,
                "tool_name": tool_name,
                "capability": required_capability,
                "actor_id": self._actor_id,
                "action_hash": action_hash,
                "context_hash": context_hash,
                "decision": decision,
                "terminal_outcome": terminal_outcome,
            }
            if action_hash_error or context_hash_error:
                transition_event["hash_error"] = action_hash_error or context_hash_error
            self._append_event(
                tool_name=tool_name,
                capability=required_capability,
                event="tool_transition",
                outcome="ok",
                duration_ms=0.0,
                status="authorization_granted",
                transition_id=transition_id,
                event_payload=transition_event,
            )

            try:
                result = tool_fn(*args, **kwargs)
            except Exception as exc:
                failed_ms = time.perf_counter_ns() / 1_000_000 - started_ms
                terminal_event = {
                    "event": "tool_call",
                    "phase": "execution",
                    "transition_id": transition_id,
                    "tool_name": tool_name,
                    "capability": required_capability,
                    "actor_id": self._actor_id,
                    "action_hash": action_hash,
                    "context_hash": context_hash,
                    "decision": decision,
                    "terminal_outcome": "failed_after_execution",
                }
                self._append_event(
                    tool_name=tool_name,
                    capability=required_capability,
                    event="tool_call",
                    outcome="error",
                    duration_ms=failed_ms,
                    status="failed",
                    transition_id=transition_id,
                    terminal_outcome="failed_after_execution",
                    error_type=type(exc).__name__,
                    event_payload=terminal_event,
                )
                raise
            else:
                executed_ms = time.perf_counter_ns() / 1_000_000 - started_ms
                terminal_event = {
                    "event": "tool_call",
                    "phase": "execution",
                    "transition_id": transition_id,
                    "tool_name": tool_name,
                    "capability": required_capability,
                    "actor_id": self._actor_id,
                    "action_hash": action_hash,
                    "context_hash": context_hash,
                    "decision": decision,
                    "terminal_outcome": "executed",
                    "result_type": type(result).__name__,
                }
                self._append_event(
                    tool_name=tool_name,
                    capability=required_capability,
                    event="tool_call",
                    outcome="ok",
                    duration_ms=executed_ms,
                    status="success",
                    transition_id=transition_id,
                    terminal_outcome="executed",
                    event_payload=terminal_event,
                )
                return result

        return wrapped

    def _append_event(
        self,
        tool_name: str,
        capability: str,
        event: str,
        outcome: str,
        duration_ms: float,
        status: str,
        transition_id: str,
        error_type: str | None = None,
        terminal_outcome: str | None = None,
        event_payload: dict[str, Any] | None = None,
    ) -> None:
        """Append an audit entry for a tool invocation attempt."""
        data = {
            "event": event,
            "tool_name": tool_name,
            "capability": capability,
            "outcome": outcome,
            "status": status,
            "duration_ms": round(duration_ms, 3),
            "error_type": error_type,
            "terminal_outcome": terminal_outcome,
            "transition_id": transition_id,
        }
        if event_payload is not None:
            data.update(event_payload)

        self._audit_log.append(
            intent_id=self._intent_id,
            task_id=self._task_id,
            tuple_type="SYSTEM",
            tuple_data=data,
            signature=self._signature,
            require_signature=False if self._signature is None else None,
            contract_id=None,
            capability_token_id=None,
            verification_id=None,
            amendment_of=None,
        )

    @staticmethod
    def _coerce_context(
        context: Mapping[str, Any] | Callable[..., Mapping[str, Any]] | None,
        *,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> Any:
        """Resolve optional call context to a mapping."""
        if context is None:
            return None
        if isinstance(context, Mapping):
            return dict(context)
        try:
            resolved = context(*args, **kwargs)
        except TypeError:
            return {"context_error": "context_builder_signature_error"}
        if isinstance(resolved, Mapping):
            return dict(resolved)
        return {"value": resolved}

    @staticmethod
    def _hash_payload(payload: Any) -> tuple[str, str | None]:
        """Hash a payload and return an error string if canonical serialization fails."""
        try:
            return stable_sha256(payload), None
        except (TypeError, ValueError) as exc:
            fallback = stable_sha256({"__fallback_repr__": repr(payload)})
            return fallback, f"{type(exc).__name__}: {exc}"
