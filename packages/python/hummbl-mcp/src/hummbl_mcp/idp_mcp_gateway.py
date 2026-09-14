"""IDP-over-MCP Gateway — expose IDP governance primitives as MCP tools.

This module bridges the IDP governance layer (DCTX, CONTRACT, DCT, EVIDENCE,
ATTEST) to the Model Context Protocol tool interface, allowing any MCP client
to participate in delegated governance flows.

MCP tool schema follows the 2024-11-05 MCP specification (JSON-RPC 2.0).

Stdlib-only: no third-party dependencies.

Reference:
- CRAI 2026 paper, Section 6.7 (IDP-over-MCP integration layer)
- MCP spec: https://spec.modelcontextprotocol.io/
"""

from __future__ import annotations

import json
import logging
from typing import Any

try:
    from hummbl_governance.delegation_context import (
        DelegationBudget,
        DelegationContextManager,
    )
except ImportError:
    pass
try:
    from hummbl_governance.delegation import (
        DelegationTokenManager,
        TokenBinding,
        get_token_manager,
    )
except ImportError:
    pass
from hummbl_mcp._governance_bus import (
    GovernanceBus,
    _compute_entry_signature,
    get_governance_bus,
)

logger = logging.getLogger(__name__)

_DEFAULT_TOKEN_MANAGER = object()


# ---------------------------------------------------------------------------
# MCP Tool Definitions (JSON-RPC 2.0 compatible)
# ---------------------------------------------------------------------------

IDP_MCP_TOOLS: list[dict[str, Any]] = [
    {
        "name": "idp_create_delegation",
        "description": (
            "Create a new IDP delegation context (DCTX). "
            "Returns a delegation with PROPOSED status, a signed capability token (DCT), "
            "and a governance audit entry."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["intent_id", "delegator_id", "delegatee_id", "contract_id"],
            "properties": {
                "intent_id": {"type": "string", "description": "Root intent identifier"},
                "delegator_id": {"type": "string", "description": "Agent issuing delegation"},
                "delegatee_id": {"type": "string", "description": "Agent receiving delegation"},
                "contract_id": {"type": "string", "description": "CONTRACT tuple reference"},
                "risk_tier": {
                    "type": "string",
                    "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
                    "default": "MEDIUM",
                },
                "parent_task_id": {
                    "type": "string",
                    "description": "Parent task ID for subdelegation (null for root)",
                },
                "max_tokens": {"type": "integer", "default": 0},
                "max_cost_usd": {"type": "number", "default": 0.0},
                "max_wall_time_seconds": {"type": "integer", "default": 0},
            },
        },
    },
    {
        "name": "idp_transition",
        "description": (
            "Transition a delegation to a new state. "
            "Enforces the IDP state machine (PROPOSED->ISSUED->RUNNING->EVIDENCE_READY->VERIFIED|FAILED)."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["task_id", "new_status"],
            "properties": {
                "task_id": {"type": "string", "description": "Task to transition"},
                "new_status": {
                    "type": "string",
                    "enum": [
                        "ISSUED", "RUNNING", "EVIDENCE_READY",
                        "VERIFIED", "REPLANNED", "FAILED",
                    ],
                },
            },
        },
    },
    {
        "name": "idp_submit_evidence",
        "description": (
            "Submit execution evidence for a running delegation. "
            "Records an EVIDENCE tuple on the governance bus."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["task_id", "evidence_data"],
            "properties": {
                "task_id": {"type": "string", "description": "Task that produced evidence"},
                "evidence_data": {
                    "type": "object",
                    "description": "Execution evidence (test results, logs, metrics)",
                },
            },
        },
    },
    {
        "name": "idp_attest",
        "description": (
            "Create an attestation (ATTEST tuple) for a delegation with evidence. "
            "Enforces I1: evidence-before-verify."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["task_id", "verification_id", "verdict"],
            "properties": {
                "task_id": {"type": "string", "description": "Task being attested"},
                "verification_id": {
                    "type": "string",
                    "description": "Reference to EVIDENCE entry_id (I1 enforcement)",
                },
                "verdict": {
                    "type": "string",
                    "enum": ["PASS", "FAIL", "CONDITIONAL"],
                },
                "rationale": {"type": "string", "description": "Attestation rationale"},
            },
        },
    },
    {
        "name": "idp_query_governance",
        "description": "Query the governance audit log by intent_id, task_id, or contract_id.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "intent_id": {"type": "string"},
                "task_id": {"type": "string"},
                "contract_id": {"type": "string"},
                "tuple_type": {
                    "type": "string",
                    "enum": ["DCTX", "CONTRACT", "DCT", "EVIDENCE", "ATTEST", "SYSTEM"],
                },
                "limit": {"type": "integer", "default": 50},
            },
        },
    },
]


# ---------------------------------------------------------------------------
# Gateway implementation
# ---------------------------------------------------------------------------

class IDPMCPGateway:
    """Bridge between IDP governance and MCP tool interface.

    Manages the lifecycle of delegations exposed as MCP tools.
    Each tool call maps to one or more governance bus entries.
    """

    def __init__(
        self,
        governance_bus: GovernanceBus | None = None,
        context_manager: DelegationContextManager | None = None,
        token_manager: DelegationTokenManager | None | object = _DEFAULT_TOKEN_MANAGER,
        require_dct: bool = True,
    ):
        self._bus = governance_bus
        self._ctx_mgr = context_manager or DelegationContextManager()
        if token_manager is _DEFAULT_TOKEN_MANAGER:
            self._token_mgr = get_token_manager()
        else:
            self._token_mgr = token_manager
        self._require_dct = require_dct
        # In-memory evidence registry (task_id -> evidence entry_id)
        self._evidence_map: dict[str, str] = {}

    @property
    def tools(self) -> list[dict[str, Any]]:
        """Return MCP tool definitions for registration."""
        return IDP_MCP_TOOLS

    def handle_tool_call(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        """Dispatch an MCP tool call to the appropriate handler.

        Args:
            tool_name: One of the idp_* tool names.
            arguments: Tool arguments per inputSchema.

        Returns:
            MCP tool result dict with content and isError fields.
        """
        handlers = {
            "idp_create_delegation": self._handle_create_delegation,
            "idp_transition": self._handle_transition,
            "idp_submit_evidence": self._handle_submit_evidence,
            "idp_attest": self._handle_attest,
            "idp_query_governance": self._handle_query_governance,
        }

        handler = handlers.get(tool_name)
        if handler is None:
            return _error_result(f"Unknown IDP tool: {tool_name}")

        try:
            return handler(arguments)
        except Exception as e:
            logger.exception("IDP MCP tool error: %s", tool_name)
            return _error_result(str(e))

    # -- Handlers ----------------------------------------------------------

    def _handle_create_delegation(self, args: dict[str, Any]) -> dict[str, Any]:
        """Create a DCTX + governance entry."""
        parent_task_id = args.get("parent_task_id")

        if self._require_dct and self._token_mgr is None:
            return _error_result("DCT token manager unavailable")

        if parent_task_id:
            # Subdelegation
            parent = self._ctx_mgr.get_context(parent_task_id)
            if parent is None:
                return _error_result(f"Parent task {parent_task_id} not found")
            child, error = parent.create_child(
                delegatee_id=args["delegatee_id"],
                contract_id=args["contract_id"],
                risk_tier=args.get("risk_tier"),
                budget=DelegationBudget(
                    max_tokens=args.get("max_tokens", 0),
                    max_cost_usd=args.get("max_cost_usd", 0.0),
                    max_wall_time_seconds=args.get("max_wall_time_seconds", 0),
                ),
            )
            if error:
                return _error_result(error)
            if child is None:
                return _error_result("Failed to create child delegation")
            # Register child in context manager
            self._ctx_mgr._contexts[child.task_id] = child
            ctx = child
        else:
            # Root delegation
            ctx = self._ctx_mgr.create_root(
                intent_id=args["intent_id"],
                delegator_id=args["delegator_id"],
                delegatee_id=args["delegatee_id"],
                contract_id=args["contract_id"],
                risk_tier=args.get("risk_tier", "MEDIUM"),
                budget=DelegationBudget(
                    max_tokens=args.get("max_tokens", 0),
                    max_cost_usd=args.get("max_cost_usd", 0.0),
                    max_wall_time_seconds=args.get("max_wall_time_seconds", 0),
                ),
            )

        # Create DCT if token manager is available
        token_id = None
        if self._token_mgr is not None:
            try:
                ops = args.get("ops_allowed", ["read", "write", "execute"])
                token = self._token_mgr.create_token(
                    issuer=ctx.delegator_id,
                    subject=ctx.delegatee_id,
                    ops_allowed=ops,
                    binding=TokenBinding(
                        task_id=ctx.task_id,
                        contract_id=ctx.contract_id,
                    ),
                )
                token_id = token.token_id
                ctx.capability_token_id = token_id

                # Record DCT on governance bus
                audit_ok, audit_error, _ = self._audit(
                    intent_id=ctx.intent_id,
                    task_id=ctx.task_id,
                    tuple_type="DCT",
                    tuple_data=token.to_dict(),
                    contract_id=ctx.contract_id,
                    capability_token_id=token_id,
                )
                if not audit_ok:
                    self._remove_context(ctx.task_id)
                    return _error_result(
                        f"DCT audit append failed: {audit_error or 'unknown error'}"
                    )
            except Exception:
                logger.warning("DCT creation failed", exc_info=True)
                self._remove_context(ctx.task_id)
                return _error_result("DCT creation failed")
        elif self._require_dct:
            self._remove_context(ctx.task_id)
            return _error_result("DCT token manager unavailable")

        # Record DCTX on governance bus
        audit_ok, audit_error, _ = self._audit(
            intent_id=ctx.intent_id,
            task_id=ctx.task_id,
            tuple_type="DCTX",
            tuple_data=ctx.to_dict(),
            contract_id=ctx.contract_id,
            capability_token_id=token_id,
        )
        if not audit_ok:
            self._remove_context(ctx.task_id)
            return _error_result(
                f"DCTX audit append failed: {audit_error or 'unknown error'}"
            )

        result = {
            "task_id": ctx.task_id,
            "intent_id": ctx.intent_id,
            "status": ctx.status,
            "chain_depth": ctx.chain_depth,
        }
        if token_id:
            result["token_id"] = token_id
        return _success_result(result)

    def _handle_transition(self, args: dict[str, Any]) -> dict[str, Any]:
        """Transition DCTX state."""
        task_id = args["task_id"]
        new_status = args["new_status"]

        ctx = self._ctx_mgr.get_context(task_id)
        if ctx is None:
            return _error_result(f"Task {task_id} not found")

        old_status = ctx.status
        success, error = ctx.transition(new_status)
        if not success:
            return _error_result(error)

        self._audit(
            intent_id=ctx.intent_id,
            task_id=ctx.task_id,
            tuple_type="SYSTEM",
            tuple_data={
                "event": "state_transition",
                "from": old_status,
                "to": new_status,
            },
            contract_id=ctx.contract_id,
        )

        return _success_result({
            "task_id": task_id,
            "old_status": old_status,
            "new_status": new_status,
        })

    def _handle_submit_evidence(self, args: dict[str, Any]) -> dict[str, Any]:
        """Record EVIDENCE tuple."""
        task_id = args["task_id"]

        ctx = self._ctx_mgr.get_context(task_id)
        if ctx is None:
            return _error_result(f"Task {task_id} not found")

        evidence_entry_id = str(uuid.uuid4())
        self._evidence_map[task_id] = evidence_entry_id

        self._audit(
            intent_id=ctx.intent_id,
            task_id=task_id,
            tuple_type="EVIDENCE",
            tuple_data=args["evidence_data"],
            contract_id=ctx.contract_id,
        )

        return _success_result({
            "task_id": task_id,
            "evidence_entry_id": evidence_entry_id,
        })

    def _handle_attest(self, args: dict[str, Any]) -> dict[str, Any]:
        """Record ATTEST tuple (I1 enforced by governance bus)."""
        task_id = args["task_id"]

        ctx = self._ctx_mgr.get_context(task_id)
        if ctx is None:
            return _error_result(f"Task {task_id} not found")

        verification_id = args["verification_id"]

        self._audit(
            intent_id=ctx.intent_id,
            task_id=task_id,
            tuple_type="ATTEST",
            tuple_data={
                "verdict": args["verdict"],
                "rationale": args.get("rationale", ""),
            },
            contract_id=ctx.contract_id,
            verification_id=verification_id,
        )

        return _success_result({
            "task_id": task_id,
            "verdict": args["verdict"],
            "verification_id": verification_id,
        })

    def _handle_query_governance(self, args: dict[str, Any]) -> dict[str, Any]:
        """Query governance bus entries."""
        if self._bus is None:
            return _error_result("Governance bus not configured")

        limit = args.get("limit", 50)
        results = []

        if "intent_id" in args:
            entries = self._bus.query_by_intent(
                args["intent_id"],
                tuple_type=args.get("tuple_type"),
            )
        elif "task_id" in args:
            entries = self._bus.query_by_task(
                args["task_id"],
                tuple_type=args.get("tuple_type"),
            )
        elif "contract_id" in args:
            entries = self._bus.query_by_contract(
                args["contract_id"],
                tuple_type=args.get("tuple_type"),
            )
        else:
            return _error_result("Provide intent_id, task_id, or contract_id")

        for entry in entries:
            if len(results) >= limit:
                break
            results.append({
                "entry_id": entry.entry_id,
                "timestamp": entry.timestamp,
                "tuple_type": entry.tuple_type,
                "intent_id": entry.intent_id,
                "task_id": entry.task_id,
                "contract_id": entry.contract_id,
            })

        return _success_result({"count": len(results), "entries": results})

    # -- Helpers -----------------------------------------------------------

    def _audit(self, **kwargs: Any) -> None:
        """Write to governance bus (best-effort).

        Uses the gateway's own bus if configured, otherwise the default singleton.
        """
        try:
            if self._bus is not None:
                from hummbl_mcp._governance_bus import _compute_entry_signature
                if "signature" not in kwargs or kwargs.get("signature") is None:
                    kwargs["signature"] = _compute_entry_signature(
                        intent_id=kwargs["intent_id"],
                        task_id=kwargs["task_id"],
                        tuple_type=kwargs["tuple_type"],
                        tuple_data=kwargs["tuple_data"],
                    )
                self._bus.append(**kwargs)
            else:
                append_audit_entry(**kwargs)
        except Exception:
            logger.warning("Failed to write governance audit entry", exc_info=True)


# ---------------------------------------------------------------------------
# MCP result helpers
# ---------------------------------------------------------------------------

def _success_result(data: dict[str, Any]) -> dict[str, Any]:
    """Format an MCP tool success result."""
    return {
        "content": [{"type": "text", "text": json.dumps(data, indent=2)}],
        "isError": False,
    }


def _error_result(message: str) -> dict[str, Any]:
    """Format an MCP tool error result."""
    return {
        "content": [{"type": "text", "text": message}],
        "isError": True,
    }


# ---------------------------------------------------------------------------
# MCP stdio server
# ---------------------------------------------------------------------------

import os
import sys

_IDP_SERVER_NAME = "idp-mcp-gateway"
_IDP_SERVER_VERSION = "0.1.0"
_IDP_PROTOCOL_VERSION = "2024-11-05"


def _idp_rpc_result(id_: Any, result: Any) -> dict:
    return {"jsonrpc": "2.0", "id": id_, "result": result}


def _idp_rpc_error(id_: Any, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": id_, "error": {"code": code, "message": message}}


def _idp_handle_request(
    request: dict[str, Any],
    gateway: IDPMCPGateway,
    idp_enabled: bool,
) -> dict[str, Any] | None:
    method = request.get("method", "")
    id_ = request.get("id")
    params = request.get("params", {})

    if method == "initialize":
        return _idp_rpc_result(id_, {
            "protocolVersion": _IDP_PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": _IDP_SERVER_NAME, "version": _IDP_SERVER_VERSION},
        })
    if method == "tools/list":
        return _idp_rpc_result(id_, {"tools": IDP_MCP_TOOLS})
    if method == "tools/call":
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})
        if not idp_enabled:
            return _idp_rpc_result(id_, {
                "content": [{"type": "text", "text": "IDP is disabled. Set ENABLE_IDP=true to enable."}],
                "isError": True,
            })
        try:
            result = gateway.handle_tool_call(tool_name, arguments)
            return _idp_rpc_result(id_, result)
        except Exception as e:
            logger.exception("IDP tool call failed: %s", tool_name)
            return _idp_rpc_result(id_, {
                "content": [{"type": "text", "text": json.dumps({"error": str(e)})}],
                "isError": True,
            })
    if method in ("notifications/initialized", "notifications/cancelled"):
        return None
    if method == "ping":
        return _idp_rpc_result(id_, {})
    return _idp_rpc_error(id_, -32601, f"Method not found: {method}")


def serve_stdio() -> None:
    """Run the IDP MCP gateway server over stdin/stdout (JSON-RPC 2.0)."""
    import logging as _logging
    _logging.basicConfig(level=_logging.WARNING, stream=sys.stderr)
    logger.info("Starting %s v%s", _IDP_SERVER_NAME, _IDP_SERVER_VERSION)

    idp_enabled = os.environ.get("ENABLE_IDP", "").lower() in ("true", "1", "yes")
    gateway = IDPMCPGateway()

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            sys.stdout.write(json.dumps(_idp_rpc_error(None, -32700, "Parse error")) + "\n")
            sys.stdout.flush()
            continue
        response = _idp_handle_request(request, gateway, idp_enabled)
        if response is not None:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":  # pragma: no cover
    serve_stdio()
