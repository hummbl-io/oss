"""HUMMBL MCP server — stdio JSON-RPC dispatcher.

Minimal MCP server implementing:
  - initialize / notifications/initialized
  - tools/list
  - tools/call
  - ping

Auth for GCP tools: via GOOGLE_APPLICATION_CREDENTIALS env var (service account
key JSON path). Configure via the env var; see deployment docs for setup.
"""

from __future__ import annotations

import json
import sys
from typing import Any, Callable

from hummbl_mcp.protocol import (
    INTERNAL_ERROR,
    INVALID_PARAMS,
    METHOD_NOT_FOUND,
    TOOL_NOT_FOUND,
    JsonRpcError,
    JsonRpcRequest,
    ToolDefinition,
    error_response,
    parse_request_line,
    serialize_response,
    success_response,
)
from hummbl_mcp.receipts import ReceiptTimer
from hummbl_mcp import gcp_tools, bridge_tools, billing_tools
from hummbl_mcp.billing_middleware import BillingMiddleware, apply_billing_middleware
try:
    from hummbl_integrations.cost_tracker import CostTracker
except ImportError:
    pass


MCP_PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "hummbl-mcp"
SERVER_VERSION = "0.1.0"


class HummblMCPServer:
    """Dispatcher. Holds a registry of tool-name → handler."""

    def __init__(
        self,
        *,
        tool_definitions: list[ToolDefinition] | None = None,
        handlers: dict[str, Callable[[dict[str, Any]], Any]] | None = None,
        receipt_identity: str = "hummbl-mcp",
        cost_tracker: CostTracker | None = None,
        enable_billing: bool = False,
    ) -> None:
        if tool_definitions is None:
            tool_definitions = gcp_tools.get_tool_definitions() + bridge_tools.get_tool_definitions()
        if handlers is None:
            handlers = {**gcp_tools.get_handlers(), **bridge_tools.get_handlers()}
        
        self.tool_definitions = tool_definitions
        self.handlers = handlers
        self.receipt_identity = receipt_identity
        self._initialized = False
        self.cost_tracker = cost_tracker
        self.enable_billing = enable_billing
        
        # Add billing tools if enabled
        if enable_billing and cost_tracker is not None:
            billing_defs = billing_tools.get_tool_definitions()
            billing_handlers = billing_tools.get_handlers(cost_tracker)
            self.tool_definitions.extend(billing_defs)
            self.handlers.update(billing_handlers)
            
            # Apply billing middleware to all handlers
            middleware = BillingMiddleware(cost_tracker, require_api_key=True)
            self.tool_definitions, self.handlers = apply_billing_middleware(
                self.tool_definitions,
                self.handlers,
                middleware,
            )

    # ------------------------------------------------------------------
    # Request dispatch
    # ------------------------------------------------------------------

    def handle(self, request: JsonRpcRequest) -> dict[str, Any] | None:
        """Dispatch a JSON-RPC request. Returns a response dict, or None for notifications."""
        try:
            if request.method == "initialize":
                result = self._handle_initialize(request.params)
            elif request.method == "notifications/initialized":
                self._initialized = True
                return None  # notification, no response
            elif request.method == "ping":
                result = {}
            elif request.method == "tools/list":
                result = self._handle_tools_list(request.params)
            elif request.method == "tools/call":
                result = self._handle_tools_call(request.params)
            else:
                raise JsonRpcError(METHOD_NOT_FOUND, f"method not found: {request.method}")
        except JsonRpcError as err:
            if request.is_notification:
                return None
            return error_response(request.id, err).to_obj()
        except Exception as e:  # noqa: BLE001
            if request.is_notification:
                return None
            return error_response(
                request.id,
                JsonRpcError(INTERNAL_ERROR, f"internal error: {type(e).__name__}: {e}"),
            ).to_obj()

        if request.is_notification:
            return None
        return success_response(request.id, result).to_obj()

    def _handle_initialize(self, params: dict[str, Any]) -> dict[str, Any]:
        # MCP initialize handshake. Report our protocol version + capabilities.
        return {
            "protocolVersion": MCP_PROTOCOL_VERSION,
            "capabilities": {
                "tools": {"listChanged": False},
            },
            "serverInfo": {
                "name": SERVER_NAME,
                "version": SERVER_VERSION,
            },
        }

    def _handle_tools_list(self, params: dict[str, Any]) -> dict[str, Any]:
        return {"tools": [t.to_obj() for t in self.tool_definitions]}

    def _handle_tools_call(self, params: dict[str, Any]) -> dict[str, Any]:
        name = params.get("name")
        if not isinstance(name, str) or not name:
            raise JsonRpcError(INVALID_PARAMS, "tools/call: 'name' is required")
        args = params.get("arguments", {})
        if args is None:
            args = {}
        if not isinstance(args, dict):
            raise JsonRpcError(INVALID_PARAMS, "tools/call: 'arguments' must be an object")

        handler = self.handlers.get(name)
        if handler is None:
            raise JsonRpcError(TOOL_NOT_FOUND, f"tool not found: {name}")

        with ReceiptTimer(name, args, identity=self.receipt_identity) as timer:
            try:
                result = handler(args)
            except JsonRpcError as err:
                timer.error(err.message)
                raise
            except Exception as e:  # noqa: BLE001
                timer.error(f"{type(e).__name__}: {e}")
                raise JsonRpcError(INTERNAL_ERROR, f"tool crashed: {type(e).__name__}: {e}") from e
            timer.ok(result)

        # MCP tools/call response format: wrap result in a 'content' array
        if isinstance(result, (dict, list)):
            content_text = json.dumps(result, indent=2, default=str)
        else:
            content_text = str(result)
        return {
            "content": [{"type": "text", "text": content_text}],
            "isError": False,
        }


# ------------------------------------------------------------------
# stdio serve loop
# ------------------------------------------------------------------

def serve_stdio(
    server: HummblMCPServer | None = None,
    *,
    enable_billing: bool = False,
    cost_tracker: CostTracker | None = None,
) -> None:
    """Read newline-delimited JSON-RPC from stdin, write responses to stdout.

    Exits on EOF or SIGTERM.
    """
    if server is None:
        server = HummblMCPServer(
            enable_billing=enable_billing,
            cost_tracker=cost_tracker,
        )

    stdin = sys.stdin
    stdout = sys.stdout

    for raw_line in stdin:
        line = raw_line.strip()
        if not line:
            continue
        try:
            req = parse_request_line(line)
        except JsonRpcError as err:
            # Malformed — best we can do is a parse error response with id=null
            resp_obj = error_response(None, err).to_obj()
            stdout.write(json.dumps(resp_obj, separators=(",", ":")) + "\n")
            stdout.flush()
            continue

        resp_obj = server.handle(req)
        if resp_obj is None:
            continue  # notification, no response
        stdout.write(json.dumps(resp_obj, separators=(",", ":")) + "\n")
        stdout.flush()


if __name__ == "__main__":  # pragma: no cover
    serve_stdio()
