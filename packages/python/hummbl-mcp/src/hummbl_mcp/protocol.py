"""MCP protocol primitives — JSON-RPC 2.0 framing over stdio.

Implements the subset of MCP spec we need for a tool-providing stdio server:
- initialize / initialized
- tools/list
- tools/call
- ping

No third-party deps. Stdlib json + typing only.

References:
- JSON-RPC 2.0: https://www.jsonrpc.org/specification
- MCP spec 2024-11-05: https://spec.modelcontextprotocol.io/
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


# JSON-RPC 2.0 error codes
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603

# MCP-specific error codes (application-level, in the -32000 to -32099 range)
TOOL_NOT_FOUND = -32001
TOOL_EXECUTION_ERROR = -32002


class ProtocolError(Exception):
    """Raised when the wire protocol itself is malformed."""


@dataclass
class JsonRpcError(Exception):
    """Structured JSON-RPC error for clean over-the-wire reporting."""

    code: int
    message: str
    data: Any = None

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"code": self.code, "message": self.message}
        if self.data is not None:
            out["data"] = self.data
        return out


@dataclass
class JsonRpcRequest:
    method: str
    params: dict[str, Any]
    id: Any  # int, str, or None (for notifications)
    jsonrpc: str = "2.0"

    @classmethod
    def from_obj(cls, obj: dict[str, Any]) -> "JsonRpcRequest":
        if not isinstance(obj, dict):
            raise JsonRpcError(INVALID_REQUEST, "Request must be a JSON object")
        if obj.get("jsonrpc") != "2.0":
            raise JsonRpcError(INVALID_REQUEST, "jsonrpc must be '2.0'")
        method = obj.get("method")
        if not isinstance(method, str) or not method:
            raise JsonRpcError(INVALID_REQUEST, "method must be a non-empty string")
        params = obj.get("params", {})
        if params is None:
            params = {}
        if not isinstance(params, dict):
            raise JsonRpcError(INVALID_PARAMS, "params must be an object or omitted")
        return cls(method=method, params=params, id=obj.get("id"), jsonrpc="2.0")

    @property
    def is_notification(self) -> bool:
        return self.id is None


@dataclass
class JsonRpcResponse:
    id: Any
    result: Any = None
    error: dict[str, Any] | None = None
    jsonrpc: str = "2.0"

    def to_obj(self) -> dict[str, Any]:
        out: dict[str, Any] = {"jsonrpc": self.jsonrpc, "id": self.id}
        if self.error is not None:
            out["error"] = self.error
        else:
            out["result"] = self.result
        return out


@dataclass
class ToolDefinition:
    """MCP tool schema — name + description + inputSchema (JSON Schema subset)."""

    name: str
    description: str
    input_schema: dict[str, Any] = field(default_factory=lambda: {"type": "object", "properties": {}})

    def to_obj(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema,
        }


def parse_request_line(line: str) -> JsonRpcRequest:
    """Parse one line of JSON-RPC input. Raises JsonRpcError on malformed input."""
    try:
        obj = json.loads(line)
    except json.JSONDecodeError as e:
        raise JsonRpcError(PARSE_ERROR, f"Parse error: {e}") from e
    return JsonRpcRequest.from_obj(obj)


def serialize_response(resp: JsonRpcResponse) -> str:
    """Serialize a JSON-RPC response to a newline-terminated string for stdout."""
    return json.dumps(resp.to_obj(), separators=(",", ":")) + "\n"


def error_response(request_id: Any, err: JsonRpcError) -> JsonRpcResponse:
    return JsonRpcResponse(id=request_id, error=err.to_dict())


def success_response(request_id: Any, result: Any) -> JsonRpcResponse:
    return JsonRpcResponse(id=request_id, result=result)
