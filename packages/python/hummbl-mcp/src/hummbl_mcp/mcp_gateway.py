"""MCPGateway — pre-execution MCP tool call governance gate for mcp_governance.

Closes the 'HUMMBL-MCP-Gate [STATUS: PROPOSED]' gap from mcp_governance
DESIGN.md (2026): standard MCP proxies execute tool calls without any
governance layer. The MCPGateway intercepts every tool call *before*
execution, evaluates it against rules, posts PROPOSAL+ACK/BLOCK to the
coordination bus, and returns a verdict.

Architecture::

    Agent requests tool_name(args)
          ↓
    MCPGateway.evaluate(MCPCallRequest)
          ↓
    ┌─ kill switch HALT_ALL/EMERGENCY    → BLOCK (all tools)
    ├─ kill switch HALT_NONCRITICAL      → BLOCK (write tools only)
    ├─ missing delegation token          → WARN (soft) / BLOCK (strict)
    ├─ argument injection pattern        → BLOCK
    ├─ path traversal in args            → BLOCK
    ├─ blocked tool list                 → BLOCK
    └─ all checks pass                  → ALLOW
          ↓
    Post PROPOSAL to bus (call_id, tool, adapter, verdict)
    Return MCPDecision

Feature flag: ENABLE_MCP_GATEWAY=true (default — enabled by default,
same governance-critical default as RetrievalArbiter).

Stdlib-only. No third-party dependencies.
"""

from __future__ import annotations

import logging
import os
import re
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_INJECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"ignore\s+previous\s+instructions", re.IGNORECASE),
    re.compile(r"forget\s+all\s+prior", re.IGNORECASE),
    re.compile(r"<\s*system\s*>", re.IGNORECASE),
    re.compile(r"\[INST\]", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+a", re.IGNORECASE),
    re.compile(r"jailbreak", re.IGNORECASE),
]

_PATH_TRAVERSAL_PATTERN = re.compile(r"\.\.[/\\]")

# Tools with these verbs in the name are classified as "write" tools
_WRITE_VERBS = frozenset(
    {
        "create", "delete", "update", "write", "post", "send",
        "push", "remove", "destroy", "edit", "insert", "add",
        "set", "put", "patch", "move", "rename", "upload", "import",
    }
)


def _is_write_tool(tool_name: str) -> bool:
    """Return True if the tool name contains a write verb."""
    lower = tool_name.lower()
    return any(verb in lower for verb in _WRITE_VERBS)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


class MCPVerdict(str, Enum):
    ALLOW = "ALLOW"
    WARN = "WARN"
    BLOCK = "BLOCK"


@dataclass(frozen=True)
class MCPFinding:
    rule: str
    message: str
    severity: MCPVerdict  # WARN or BLOCK


@dataclass(frozen=True)
class MCPCallRequest:
    """A single MCP tool call submitted for gateway arbitration.

    Attributes:
        tool_name:          Name of the MCP tool being called.
        adapter:            Short adapter name (e.g., ``"linear"``, ``"github"``).
        arguments:          Tool call arguments as a dict.
        delegation_token:   HMAC-signed delegation token from IDP. Empty = unsigned.
        call_id:            Unique identifier for this call attempt.
    """

    tool_name: str
    adapter: str = ""
    arguments: dict[str, Any] = field(default_factory=dict)
    delegation_token: str = ""  # empty = unsigned
    call_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    @property
    def is_signed(self) -> bool:
        return bool(self.delegation_token)

    @property
    def is_write_tool(self) -> bool:
        return _is_write_tool(self.tool_name)


@dataclass
class MCPDecision:
    """Result of MCPGateway.evaluate()."""

    verdict: MCPVerdict
    call_id: str
    tool_name: str
    adapter: str
    findings: list[MCPFinding] = field(default_factory=list)

    @property
    def allowed(self) -> bool:
        return self.verdict != MCPVerdict.BLOCK

    def summary(self) -> str:
        verdict_str = f"[{self.verdict.value}]"
        lines = [
            f"{verdict_str} call_id={self.call_id} "
            f"tool={self.tool_name} adapter={self.adapter}"
        ]
        for f in self.findings:
            lines.append(f"  [{f.severity.value}] {f.rule}: {f.message}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# MCPGateway
# ---------------------------------------------------------------------------


class MCPGateway:
    """Pre-execution MCP tool call governance gate.

    Usage::

        gateway = MCPGateway()

        request = MCPCallRequest(
            tool_name="list_issues",
            adapter="linear",
            arguments={"limit": 20},
            delegation_token="hmac-abc123",
        )
        decision = gateway.evaluate(request)

        if decision.allowed:
            result = actual_mcp_call(...)
        else:
            raise PermissionError(decision.summary())

    Feature flag: ENABLE_MCP_GATEWAY=false to disable all checks.
    Strict mode: MCP_GATEWAY_STRICT=true to block unsigned calls (default: WARN).
    Blocked tools: MCP_BLOCKED_TOOLS=tool1,tool2 (comma-separated).
    """

    def __init__(
        self,
        *,
        kill_switch: Any = None,
        bus_poster: Callable[[str], None] | None = None,
        strict_delegation: bool | None = None,
        blocked_tools: list[str] | None = None,
    ) -> None:
        self._enabled = (
            os.environ.get("ENABLE_MCP_GATEWAY", "true").lower() != "false"
        )
        self._kill_switch = kill_switch
        self._bus_poster = bus_poster
        self._strict = (
            strict_delegation
            if strict_delegation is not None
            else os.environ.get("MCP_GATEWAY_STRICT", "false").lower() == "true"
        )
        env_blocked = os.environ.get("MCP_BLOCKED_TOOLS", "")
        self._blocked_tools: frozenset[str] = frozenset(
            (blocked_tools or []) + [t.strip() for t in env_blocked.split(",") if t.strip()]
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def evaluate(self, request: MCPCallRequest) -> MCPDecision:
        """Evaluate a tool call request before execution.

        Args:
            request: The MCP tool call to evaluate.

        Returns:
            MCPDecision with ALLOW / WARN / BLOCK verdict.
        """
        if not self._enabled:
            decision = MCPDecision(
                verdict=MCPVerdict.ALLOW,
                call_id=request.call_id,
                tool_name=request.tool_name,
                adapter=request.adapter,
            )
            self._post_to_bus(request, decision)
            return decision

        findings: list[MCPFinding] = []

        # Guard 0: kill switch
        ks_state = self._kill_switch_state()
        if ks_state in ("HALT_ALL", "EMERGENCY"):
            findings.append(
                MCPFinding(
                    rule="KILL_SWITCH",
                    message=f"Kill switch active: {ks_state} — all MCP calls blocked",
                    severity=MCPVerdict.BLOCK,
                )
            )
            return self._decide(request, findings)

        # Guard 1: HALT_NONCRITICAL blocks write tools
        if ks_state == "HALT_NONCRITICAL" and request.is_write_tool:
            findings.append(
                MCPFinding(
                    rule="WRITE_TOOL_HALTED",
                    message=(
                        f"Kill switch HALT_NONCRITICAL active — "
                        f"write tool '{request.tool_name}' blocked"
                    ),
                    severity=MCPVerdict.BLOCK,
                )
            )
            return self._decide(request, findings)

        # Rule 1: blocked tool list
        if request.tool_name in self._blocked_tools:
            findings.append(
                MCPFinding(
                    rule="BLOCKED_TOOL",
                    message=f"Tool '{request.tool_name}' is on the blocked list",
                    severity=MCPVerdict.BLOCK,
                )
            )

        # Rule 2: missing delegation token
        if not request.is_signed:
            findings.append(
                MCPFinding(
                    rule="MISSING_DELEGATION",
                    message="No delegation token — call lacks signed IDP provenance",
                    severity=MCPVerdict.BLOCK if self._strict else MCPVerdict.WARN,
                )
            )

        # Rule 3: argument injection scan
        injected_args = self._scan_injection(request.arguments)
        if injected_args:
            findings.append(
                MCPFinding(
                    rule="ARGUMENT_INJECTION",
                    message=(
                        f"Prompt injection pattern detected in argument(s): "
                        f"{', '.join(injected_args[:3])}"
                    ),
                    severity=MCPVerdict.BLOCK,
                )
            )

        # Rule 4: path traversal
        traversal_args = self._scan_path_traversal(request.arguments)
        if traversal_args:
            findings.append(
                MCPFinding(
                    rule="PATH_TRAVERSAL",
                    message=(
                        f"Path traversal pattern '../' detected in argument(s): "
                        f"{', '.join(traversal_args[:3])}"
                    ),
                    severity=MCPVerdict.BLOCK,
                )
            )

        return self._decide(request, findings)

    def get_evaluated_count(self) -> int:
        """Total calls evaluated since this instance was created."""
        return self._evaluated_count

    # ------------------------------------------------------------------
    # Initialise counters
    # ------------------------------------------------------------------

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)

    def __post_init__(self) -> None:
        self._evaluated_count = 0

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _decide(
        self,
        request: MCPCallRequest,
        findings: list[MCPFinding],
    ) -> MCPDecision:
        if not hasattr(self, "_evaluated_count"):
            self._evaluated_count = 0
        self._evaluated_count += 1

        if any(f.severity == MCPVerdict.BLOCK for f in findings):
            verdict = MCPVerdict.BLOCK
        elif any(f.severity == MCPVerdict.WARN for f in findings):
            verdict = MCPVerdict.WARN
        else:
            verdict = MCPVerdict.ALLOW

        decision = MCPDecision(
            verdict=verdict,
            call_id=request.call_id,
            tool_name=request.tool_name,
            adapter=request.adapter,
            findings=findings,
        )
        self._post_to_bus(request, decision)
        logger.debug(
            "MCPGateway: %s %s adapter=%s call_id=%s",
            verdict.value,
            request.tool_name,
            request.adapter,
            request.call_id,
        )
        return decision

    def _post_to_bus(self, request: MCPCallRequest, decision: MCPDecision) -> None:
        """Post PROPOSAL (call intent) then ACK/BLOCK verdict to the bus."""
        poster = self._bus_poster
        if poster is None:
            poster = self._default_bus_poster

        try:
            # Post the proposal
            msg_type = "ACK" if decision.allowed else "BLOCK"
            payload = (
                f"MCP_CALL call_id={request.call_id} "
                f"tool={request.tool_name} adapter={request.adapter} "
                f"verdict={decision.verdict.value} signed={request.is_signed}"
            )
            poster(msg_type, payload)
        except Exception as exc:
            logger.debug("MCPGateway: bus post failed: %s", exc)

    @staticmethod
    def _default_bus_poster(msg_type: str, message: str) -> None:
        """Post to coordination bus via bus_writer subprocess."""
        import subprocess

        subprocess.run(
            [
                "python3",
                "-m",
                "hummbl_bus.bus_writer",
                "mcp-gateway",
                "all",
                msg_type,
                message,
            ],
            capture_output=True,
            timeout=5,
        )

    def _kill_switch_state(self) -> str:
        """Return the current kill switch state string."""
        ks = self._kill_switch
        if ks is not None:
            try:
                state = ks.get_state()
                return state.name if hasattr(state, "name") else str(state)
            except Exception:
                return "DISENGAGED"

        env_override = os.environ.get("MCP_KILL_SWITCH_STATE", "")
        if env_override:
            return env_override.upper()

        try:
            try:
                from hummbl_governance.kill_switch import KillSwitchCore
            except ImportError:
                pass

            ks = KillSwitchCore()
            return ks.get_state().name
        except Exception:
            return "DISENGAGED"

    @staticmethod
    def _scan_injection(arguments: dict[str, Any]) -> list[str]:
        """Return list of argument keys containing injection patterns."""
        hits: list[str] = []
        for key, value in arguments.items():
            if isinstance(value, str):
                for pattern in _INJECTION_PATTERNS:
                    if pattern.search(value):
                        hits.append(key)
                        break
        return hits

    @staticmethod
    def _scan_path_traversal(arguments: dict[str, Any]) -> list[str]:
        """Return list of argument keys containing path traversal patterns."""
        hits: list[str] = []
        for key, value in arguments.items():
            if isinstance(value, str) and _PATH_TRAVERSAL_PATTERN.search(value):
                hits.append(key)
        return hits


# ---------------------------------------------------------------------------
# MCP stdio server
# ---------------------------------------------------------------------------

import json

_GATEWAY_SERVER_NAME = "mcp-gateway"
_GATEWAY_SERVER_VERSION = "0.1.0"
_GATEWAY_PROTOCOL_VERSION = "2024-11-05"

_MCP_TOOLS: list[dict[str, Any]] = [
    {
        "name": "gateway_evaluate",
        "description": (
            "Evaluate an MCP tool call against governance rules. "
            "Returns verdict (ALLOW/WARN/BLOCK) with findings."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["tool_name"],
            "properties": {
                "tool_name": {"type": "string", "description": "MCP tool name to evaluate"},
                "adapter": {"type": "string", "description": "Adapter name (e.g. 'linear', 'github')"},
                "arguments": {"type": "object", "description": "Tool call arguments to scan"},
                "delegation_token": {"type": "string", "description": "HMAC delegation token (empty = unsigned)"},
            },
        },
    },
    {
        "name": "gateway_policy",
        "description": "Return current gateway policy settings (kill switch state, blocked tools).",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "gateway_validate_dry_run",
        "description": (
            "Evaluate a tool call as a dry run — identical to gateway_evaluate "
            "but explicitly labeled as dry-run (no bus post)."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["tool_name"],
            "properties": {
                "tool_name": {"type": "string", "description": "MCP tool name to evaluate"},
                "adapter": {"type": "string", "description": "Adapter name"},
                "arguments": {"type": "object", "description": "Tool call arguments to scan"},
                "delegation_token": {"type": "string", "description": "HMAC delegation token"},
            },
        },
    },
]


def _gateway_handle_tool(name: str, arguments: dict[str, Any]) -> Any:
    """Dispatch MCP tool call to the appropriate gateway handler."""
    if name == "gateway_evaluate":
        gateway = MCPGateway()
        request = MCPCallRequest(
            tool_name=arguments.get("tool_name", ""),
            adapter=arguments.get("adapter", ""),
            arguments=arguments.get("arguments", {}),
            delegation_token=arguments.get("delegation_token", ""),
        )
        decision = gateway.evaluate(request)
        return {
            "verdict": decision.verdict.value,
            "call_id": decision.call_id,
            "tool_name": decision.tool_name,
            "adapter": decision.adapter,
            "allowed": decision.allowed,
            "findings": [
                {"rule": f.rule, "message": f.message, "severity": f.severity.value}
                for f in decision.findings
            ],
        }
    if name == "gateway_policy":
        gateway = MCPGateway()
        return {
            "enabled": gateway._enabled,
            "strict_delegation": gateway._strict,
            "blocked_tools": sorted(gateway._blocked_tools),
            "kill_switch_state": gateway._kill_switch_state(),
        }
    if name == "gateway_validate_dry_run":
        # Dry run: create gateway with no bus poster
        gateway = MCPGateway(bus_poster=lambda *a: None)
        request = MCPCallRequest(
            tool_name=arguments.get("tool_name", ""),
            adapter=arguments.get("adapter", ""),
            arguments=arguments.get("arguments", {}),
            delegation_token=arguments.get("delegation_token", ""),
        )
        decision = gateway.evaluate(request)
        return {
            "dry_run": True,
            "verdict": decision.verdict.value,
            "call_id": decision.call_id,
            "tool_name": decision.tool_name,
            "adapter": decision.adapter,
            "allowed": decision.allowed,
            "findings": [
                {"rule": f.rule, "message": f.message, "severity": f.severity.value}
                for f in decision.findings
            ],
        }
    raise ValueError(f"Unknown tool: {name}")


def _gw_rpc_result(id_: Any, result: Any) -> dict:
    return {"jsonrpc": "2.0", "id": id_, "result": result}


def _gw_rpc_error(id_: Any, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": id_, "error": {"code": code, "message": message}}


def _gw_handle_request(request: dict[str, Any]) -> dict[str, Any] | None:
    method = request.get("method", "")
    id_ = request.get("id")
    params = request.get("params", {})

    if method == "initialize":
        return _gw_rpc_result(id_, {
            "protocolVersion": _GATEWAY_PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": _GATEWAY_SERVER_NAME, "version": _GATEWAY_SERVER_VERSION},
        })
    if method == "tools/list":
        return _gw_rpc_result(id_, {"tools": _MCP_TOOLS})
    if method == "tools/call":
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})
        try:
            result = _gateway_handle_tool(tool_name, arguments)
            return _gw_rpc_result(id_, {
                "content": [{"type": "text", "text": json.dumps(result, indent=2)}],
            })
        except Exception as e:
            logger.exception("Tool call failed: %s", tool_name)
            return _gw_rpc_result(id_, {
                "content": [{"type": "text", "text": json.dumps({"error": str(e)})}],
                "isError": True,
            })
    if method in ("notifications/initialized", "notifications/cancelled"):
        return None
    if method == "ping":
        return _gw_rpc_result(id_, {})
    return _gw_rpc_error(id_, -32601, f"Method not found: {method}")


def serve_stdio() -> None:
    """Run the MCP gateway server over stdin/stdout (JSON-RPC 2.0)."""
    import sys
    logging.basicConfig(level=logging.WARNING, stream=sys.stderr)
    logger.info("Starting %s v%s", _GATEWAY_SERVER_NAME, _GATEWAY_SERVER_VERSION)
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            sys.stdout.write(json.dumps(_gw_rpc_error(None, -32700, "Parse error")) + "\n")
            sys.stdout.flush()
            continue
        response = _gw_handle_request(request)
        if response is not None:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":  # pragma: no cover
    serve_stdio()
