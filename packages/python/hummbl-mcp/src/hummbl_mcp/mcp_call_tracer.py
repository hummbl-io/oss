"""MCP Call Tracer — per-call audit entries for every MCP tool invocation.

Every MCP tool call that goes through this tracer produces two SYSTEM tuples
in the governance bus: one BEFORE execution (MCP_CALL_START) and one AFTER
(MCP_CALL_END with outcome). This closes the 'Per-call MCP tracing' gap
identified in the MCP Governance landscape research.

Feature-flagged via ENABLE_IDP (same as all IDP Phase 0/1 features).
When IDP is disabled, the tracer is a no-op transparent wrapper.

Usage (context manager)::

    tracer = MCPCallTracer(adapter="linear", intent_id="intent-abc", task_id="task-xyz")
    async with tracer.trace("list_issues", args={"limit": 20}) as ctx:
        result = await mcp__claude_ai_Linear__list_issues(limit=20)
        ctx.result_count = len(result)

Usage (decorator)::

    tracer = MCPCallTracer(adapter="linear", intent_id="intent-abc", task_id="task-xyz")

    @tracer.traced("list_issues")
    async def _list_issues(**kwargs):
        return await mcp__claude_ai_Linear__list_issues(**kwargs)

Stdlib-only. No third-party dependencies.
"""

from __future__ import annotations

import contextlib
import functools
import logging
import os
import time
import uuid
from typing import Any, AsyncIterator, Callable

logger = logging.getLogger(__name__)

_IDP_ENV_VAR = "ENABLE_IDP"


def _is_idp_enabled() -> bool:
    return os.environ.get(_IDP_ENV_VAR, "").lower() in ("true", "1", "yes")


class MCPCallTrace:
    """Context object for a single MCP tool call trace.

    Passed into the ``async with tracer.trace(...)`` block so callers can
    annotate the trace with result metadata before the END entry is emitted.
    """

    def __init__(self, tool_name: str, adapter: str) -> None:
        self.tool_name = tool_name
        self.adapter = adapter
        self.call_id: str = str(uuid.uuid4())
        # Callers may set these to enrich the END audit entry
        self.result_count: int | None = None
        self.error: str | None = None


class MCPCallTracer:
    """Emits governance bus audit entries for MCP tool calls.

    Parameters
    ----------
    adapter:
        Short name of the adapter issuing the calls (e.g., "linear", "github").
        Recorded in every audit entry for filtering.
    intent_id:
        Root intent identifier for the delegation chain. If not provided at
        construction time, a synthetic one is generated per tracer instance.
    task_id:
        Task identifier within the intent. If not provided, defaults to
        ``adapter:mcp_calls``.
    bus:
        Optional GovernanceBus instance. If None, the default bus is used
        when IDP is enabled (lazy import to avoid import-time side effects).
    """

    def __init__(
        self,
        adapter: str,
        intent_id: str | None = None,
        task_id: str | None = None,
        bus: Any | None = None,
    ) -> None:
        self.adapter = adapter
        self.intent_id = intent_id or f"mcp_trace:{adapter}:{uuid.uuid4()}"
        self.task_id = task_id or f"{adapter}:mcp_calls"
        self._bus = bus  # injected for testing; None means use default

    def _get_bus(self) -> Any:
        if self._bus is not None:
            return self._bus
        from hummbl_mcp._governance_bus import get_governance_bus
        return get_governance_bus()

    def _post(self, event: str, tool_name: str, call_id: str, extra: dict[str, Any]) -> None:
        """Post a SYSTEM audit entry.  Silent on any failure."""
        if not _is_idp_enabled():
            return
        try:
            from hummbl_mcp._governance_bus import append_audit_entry
            tuple_data: dict[str, Any] = {
                "event": event,
                "tool": tool_name,
                "adapter": self.adapter,
                "call_id": call_id,
                **extra,
            }
            append_audit_entry(
                intent_id=self.intent_id,
                task_id=self.task_id,
                tuple_type="SYSTEM",
                tuple_data=tuple_data,
            )
        except Exception:
            logger.debug("MCPCallTracer: failed to post %s for %s", event, tool_name, exc_info=True)

    @contextlib.asynccontextmanager
    async def trace(
        self, tool_name: str, args: dict[str, Any] | None = None
    ) -> AsyncIterator[MCPCallTrace]:
        """Async context manager that wraps a single MCP tool call.

        Emits MCP_CALL_START on entry and MCP_CALL_END on exit.
        The context object ``ctx`` can be annotated with result metadata.

        Example::

            async with tracer.trace("list_issues", args={"limit": 20}) as ctx:
                result = await mcp__claude_ai_Linear__list_issues(limit=20)
                ctx.result_count = len(result)
        """
        ctx = MCPCallTrace(tool_name=tool_name, adapter=self.adapter)
        start_ns = time.monotonic_ns()

        # Summarize args: keys only, no values (values may contain secrets/PII)
        arg_keys = list(args.keys()) if args else []
        self._post(
            "MCP_CALL_START",
            tool_name,
            ctx.call_id,
            {"arg_keys": arg_keys},
        )

        try:
            yield ctx
            elapsed_ms = (time.monotonic_ns() - start_ns) // 1_000_000
            extra: dict[str, Any] = {"outcome": "SUCCESS", "elapsed_ms": elapsed_ms}
            if ctx.result_count is not None:
                extra["result_count"] = ctx.result_count
            self._post("MCP_CALL_END", tool_name, ctx.call_id, extra)
        except Exception as exc:
            elapsed_ms = (time.monotonic_ns() - start_ns) // 1_000_000
            ctx.error = type(exc).__name__
            self._post(
                "MCP_CALL_END",
                tool_name,
                ctx.call_id,
                {
                    "outcome": "FAILURE",
                    "elapsed_ms": elapsed_ms,
                    "error_type": type(exc).__name__,
                },
            )
            raise

    def traced(
        self, tool_name: str, args_keys_from_kwargs: bool = True
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorator factory that wraps an async function with MCP tracing.

        Example::

            @tracer.traced("list_issues")
            async def _list_issues(**kwargs):
                return await mcp__claude_ai_Linear__list_issues(**kwargs)
        """
        def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
            @functools.wraps(fn)
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                arg_keys = list(kwargs.keys()) if args_keys_from_kwargs else []
                async with self.trace(tool_name, args=dict.fromkeys(arg_keys)) as ctx:
                    result = await fn(*args, **kwargs)
                    # Annotate count for list-returning tools
                    if isinstance(result, (list, tuple)):
                        ctx.result_count = len(result)
                    return result
            return wrapper
        return decorator


# ---------------------------------------------------------------------------
# MCP stdio server
# ---------------------------------------------------------------------------

import json

_TRACER_SERVER_NAME = "mcp-call-tracer"
_TRACER_SERVER_VERSION = "0.1.0"
_TRACER_PROTOCOL_VERSION = "2024-11-05"

_TRACER_MCP_TOOLS: list[dict[str, Any]] = [
    {
        "name": "tracer_status",
        "description": "Return whether IDP/tracing is enabled and tracer configuration.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "tracer_recent",
        "description": (
            "Return recent MCP_CALL_START/END entries from the governance bus. "
            "Reads the JSONL audit log directly."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Max entries to return (default: 20)",
                },
            },
        },
    },
    {
        "name": "tracer_stats",
        "description": (
            "Aggregated MCP call statistics: calls by adapter, average latency, error rate."
        ),
        "inputSchema": {"type": "object", "properties": {}},
    },
]


def _tracer_handle_tool(name: str, arguments: dict[str, Any]) -> Any:
    """Dispatch MCP tool call to tracer handlers."""
    if name == "tracer_status":
        return {
            "idp_enabled": _is_idp_enabled(),
            "env_var": _IDP_ENV_VAR,
            "env_value": os.environ.get(_IDP_ENV_VAR, ""),
        }
    if name == "tracer_recent":
        limit = int(arguments.get("limit", 20))
        return _read_recent_traces(limit)
    if name == "tracer_stats":
        return _compute_trace_stats()
    raise ValueError(f"Unknown tool: {name}")


def _read_recent_traces(limit: int = 20) -> list[dict[str, Any]]:
    """Read recent MCP_CALL_START/END entries from governance bus JSONL."""
    from pathlib import Path
    bus_path = Path(__file__).parent.parent / "_state" / "governance" / "audit.jsonl"
    if not bus_path.exists():
        return []
    results: list[dict[str, Any]] = []
    try:
        lines = bus_path.read_text().strip().split("\n")
        for line in reversed(lines):
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            td = entry.get("tuple_data", {})
            event = td.get("event", "")
            if event in ("MCP_CALL_START", "MCP_CALL_END"):
                results.append({
                    "timestamp": entry.get("timestamp", ""),
                    "event": event,
                    "tool": td.get("tool", ""),
                    "adapter": td.get("adapter", ""),
                    "call_id": td.get("call_id", ""),
                    "outcome": td.get("outcome", ""),
                    "elapsed_ms": td.get("elapsed_ms"),
                })
                if len(results) >= limit:
                    break
    except Exception:
        logger.debug("Failed to read governance audit log", exc_info=True)
    return results


def _compute_trace_stats() -> dict[str, Any]:
    """Aggregate stats from MCP_CALL_END entries."""
    from pathlib import Path
    bus_path = Path(__file__).parent.parent / "_state" / "governance" / "audit.jsonl"
    if not bus_path.exists():
        return {"total_calls": 0, "by_adapter": {}, "error_rate_pct": 0.0}

    by_adapter: dict[str, dict[str, Any]] = {}
    total = 0
    errors = 0
    try:
        for line in bus_path.read_text().strip().split("\n"):
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            td = entry.get("tuple_data", {})
            if td.get("event") != "MCP_CALL_END":
                continue
            total += 1
            adapter = td.get("adapter", "unknown")
            outcome = td.get("outcome", "")
            elapsed = td.get("elapsed_ms", 0)
            if outcome == "FAILURE":
                errors += 1

            if adapter not in by_adapter:
                by_adapter[adapter] = {"calls": 0, "errors": 0, "total_latency_ms": 0}
            by_adapter[adapter]["calls"] += 1
            if outcome == "FAILURE":
                by_adapter[adapter]["errors"] += 1
            by_adapter[adapter]["total_latency_ms"] += (elapsed or 0)
    except Exception:
        logger.debug("Failed to compute trace stats", exc_info=True)

    # Compute averages
    adapter_stats = {}
    for adapter, stats in by_adapter.items():
        avg_latency = stats["total_latency_ms"] / stats["calls"] if stats["calls"] else 0
        err_rate = (stats["errors"] / stats["calls"] * 100) if stats["calls"] else 0
        adapter_stats[adapter] = {
            "calls": stats["calls"],
            "errors": stats["errors"],
            "avg_latency_ms": round(avg_latency, 1),
            "error_rate_pct": round(err_rate, 1),
        }

    return {
        "total_calls": total,
        "total_errors": errors,
        "error_rate_pct": round((errors / total * 100) if total else 0, 1),
        "by_adapter": adapter_stats,
    }


def _tr_rpc_result(id_: Any, result: Any) -> dict:
    return {"jsonrpc": "2.0", "id": id_, "result": result}


def _tr_rpc_error(id_: Any, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": id_, "error": {"code": code, "message": message}}


def _tr_handle_request(request: dict[str, Any]) -> dict[str, Any] | None:
    method = request.get("method", "")
    id_ = request.get("id")
    params = request.get("params", {})

    if method == "initialize":
        return _tr_rpc_result(id_, {
            "protocolVersion": _TRACER_PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": _TRACER_SERVER_NAME, "version": _TRACER_SERVER_VERSION},
        })
    if method == "tools/list":
        return _tr_rpc_result(id_, {"tools": _TRACER_MCP_TOOLS})
    if method == "tools/call":
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})
        try:
            result = _tracer_handle_tool(tool_name, arguments)
            return _tr_rpc_result(id_, {
                "content": [{"type": "text", "text": json.dumps(result, indent=2)}],
            })
        except Exception as e:
            logger.exception("Tool call failed: %s", tool_name)
            return _tr_rpc_result(id_, {
                "content": [{"type": "text", "text": json.dumps({"error": str(e)})}],
                "isError": True,
            })
    if method in ("notifications/initialized", "notifications/cancelled"):
        return None
    if method == "ping":
        return _tr_rpc_result(id_, {})
    return _tr_rpc_error(id_, -32601, f"Method not found: {method}")


def serve_stdio() -> None:
    """Run the MCP call tracer server over stdin/stdout (JSON-RPC 2.0)."""
    import sys
    logging.basicConfig(level=logging.WARNING, stream=sys.stderr)
    logger.info("Starting %s v%s", _TRACER_SERVER_NAME, _TRACER_SERVER_VERSION)
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            sys.stdout.write(json.dumps(_tr_rpc_error(None, -32700, "Parse error")) + "\n")
            sys.stdout.flush()
            continue
        response = _tr_handle_request(request)
        if response is not None:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":  # pragma: no cover
    serve_stdio()
