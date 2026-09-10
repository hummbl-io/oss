# Copyright 2024-2026 HUMMBL, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

"""1Password MCP server — JSON-RPC 2.0 over stdio.

Wraps the 1Password CLI (`op`) as MCP tools so agents can retrieve secrets
autonomously without human intervention. Uses the service account token
from the environment (OP_SERVICE_ACCOUNT_TOKEN), which is auto-loaded from
Windows Credential Manager by the PowerShell profile.

Exposes five MCP tools:

  onepassword_get       — retrieve a secret value by item title + vault
  onepassword_list      — list items in a vault (title, category, id)
  onepassword_vaults    — list accessible vaults
  onepassword_fields    — discover field names for an item (no values)
  onepassword_resolve   — look up a secret by common name (e.g. "github pat")

Security: secret values are returned in MCP content but agents MUST redact
them in user-facing output. The `onepassword_fields` tool returns field names
only (no values) for safe discovery.

Wire into MCP config (settings.json / mcp_config.local.json)::

    {
      "mcpServers": {
        "onepassword": {
          "command": "hummbl-mcp-onepassword"
        }
      }
    }

Zero third-party dependencies. Stdlib only. JSON-RPC 2.0.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Any

# JSON-RPC 2.0 error codes
_METHOD_NOT_FOUND = -32601
_INVALID_PARAMS = -32602
_INTERNAL_ERROR = -32603

# Vaults accessible to the service account.
# Users should update this set to match their own 1Password vault names.
_KNOWN_VAULTS = {"api-keys", "bots", "infrastructure"}

# Common-name resolver: maps friendly names to (title, vault, field)
# Agents can call onepassword_resolve("github pat") instead of remembering exact titles.
# Users should populate this map with their own 1Password vault item titles.
_RESOLVE_MAP: dict[str, tuple[str, str, str]] = {}


# ---------------------------------------------------------------------------
# MCP content helpers
# ---------------------------------------------------------------------------


def _ok_content(text: str) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": text}]}


def _error_content(message: str) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": message}], "isError": True}


# ---------------------------------------------------------------------------
# op CLI wrapper
# ---------------------------------------------------------------------------


def _run_op(args: list[str], timeout: int = 30) -> tuple[int, str, str]:
    """Run `op` with the given args. Returns (returncode, stdout, stderr)."""
    cmd = ["op"] + args
    env = os.environ.copy()
    # Ensure service account token is available; if not in env, the caller
    # must have sourced load-1p-token.ps1 first. We do NOT read Credential
    # Manager here — that's the shell profile's job.
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 1, "", "op CLI not found on PATH"
    except subprocess.TimeoutExpired:
        return 1, "", f"op command timed out after {timeout}s"


def _op_json(args: list[str]) -> Any:
    """Run op with --format json and parse the result. Raises on error."""
    rc, stdout, stderr = _run_op(args + ["--format", "json"])
    if rc != 0:
        raise RuntimeError(stderr.strip() or f"op exited {rc}")
    return json.loads(stdout)


# ---------------------------------------------------------------------------
# Tool schemas
# ---------------------------------------------------------------------------

_TOOLS = [
    {
        "name": "onepassword_get",
        "description": (
            "Retrieve a secret value from 1Password by item title and vault. "
            "Returns the raw secret value — agents MUST redact it in user-facing "
            "output (e.g. [REDACTED length=N]). Use onepassword_fields first if "
            "you don't know the field name."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Exact item title in 1Password, e.g. 'GitHub Personal Access Token'.",
                },
                "vault": {
                    "type": "string",
                    "description": "Vault name: 'api-keys', 'bots', or 'infrastructure'.",
                },
                "field": {
                    "type": "string",
                    "description": "Field name to retrieve. API_CREDENTIAL items usually use 'credential', PASSWORD items use 'password'. Use onepassword_fields to discover.",
                },
            },
            "required": ["title", "vault", "field"],
        },
    },
    {
        "name": "onepassword_list",
        "description": (
            "List all items in a vault. Returns title, category, and id for each. "
            "Does NOT return secret values — safe to display."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "vault": {
                    "type": "string",
                    "description": "Vault name: 'api-keys', 'bots', or 'infrastructure'.",
                },
            },
            "required": ["vault"],
        },
    },
    {
        "name": "onepassword_vaults",
        "description": "List all vaults accessible to the service account. No parameters.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "onepassword_fields",
        "description": (
            "Discover field names for an item without revealing values. "
            "Use this when you don't know which field name to pass to onepassword_get. "
            "Returns field names and types only."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Exact item title in 1Password.",
                },
                "vault": {
                    "type": "string",
                    "description": "Vault name: 'api-keys', 'bots', or 'infrastructure'.",
                },
            },
            "required": ["title", "vault"],
        },
    },
    {
        "name": "onepassword_resolve",
        "description": (
            "Look up a secret by common name (e.g. 'github pat', 'anthropic key', "
            "'cloudflare token'). Resolves the friendly name to the exact 1Password "
            "item title, vault, and field, then retrieves the value. "
            "Returns the raw secret — agents MUST redact in output."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": (
                        "Common name for the secret. Recognized: "
                        "anthropic key, claude key, openai key, deepseek key, mistral key, "
                        "groq key, openrouter key, openrouter admin, huggingface key, hf token, "
                        "nvidia key, gemini key, google ai key, xai key, grok key, elevenlabs key, "
                        "tavily key, context7 key, github pat, github token, github mcp token, "
                        "github dev org pat, cloudflare token, cloudflare key, cloudflare workers, "
                        "cloudflare dns, cloudflare r2, hetzner key, upcloud key, tailscale key, "
                        "pypi token, npm token, gitea token, resend key, discord bot token, "
                        "slack bot token, telegram token, stripe key, bus signing secret, "
                        "hermes gateway token."
                    ),
                },
            },
            "required": ["name"],
        },
    },
]


# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------


class OnePasswordServer:
    """Minimal MCP server exposing 1Password CLI as JSON-RPC 2.0 tools."""

    def __init__(self) -> None:
        self._server_info = {
            "name": "onepassword-mcp",
            "version": "1.0.0",
        }

    # ------------------------------------------------------------------
    # MCP protocol handlers
    # ------------------------------------------------------------------

    def handle_initialize(self, _params: dict[str, Any]) -> dict[str, Any]:
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": self._server_info,
        }

    def handle_tools_list(self, _params: dict[str, Any]) -> dict[str, Any]:
        return {"tools": _TOOLS}

    def handle_tools_call(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        if name == "onepassword_get":
            return self._call_get(args)
        elif name == "onepassword_list":
            return self._call_list(args)
        elif name == "onepassword_vaults":
            return self._call_vaults(args)
        elif name == "onepassword_fields":
            return self._call_fields(args)
        elif name == "onepassword_resolve":
            return self._call_resolve(args)
        else:
            return _error_content(f"Unknown tool: {name!r}")

    # ------------------------------------------------------------------
    # Tool implementations
    # ------------------------------------------------------------------

    def _call_get(self, args: dict[str, Any]) -> dict[str, Any]:
        for param in ("title", "vault", "field"):
            if param not in args:
                return _error_content(f"Missing required parameter: {param!r}")
        title = args["title"]
        vault = args["vault"]
        field = args["field"]
        if vault not in _KNOWN_VAULTS:
            return _error_content(
                f"Vault {vault!r} not accessible. Known vaults: {sorted(_KNOWN_VAULTS)}"
            )
        rc, stdout, stderr = _run_op(
            [
                "item",
                "get",
                title,
                "--vault",
                vault,
                "--fields",
                f"label={field}",
                "--reveal",
            ]
        )
        if rc != 0:
            # Retry without label= prefix (some items use bare field names)
            rc2, stdout2, stderr2 = _run_op(
                [
                    "item",
                    "get",
                    title,
                    "--vault",
                    vault,
                    "--fields",
                    field,
                    "--reveal",
                ]
            )
            if rc2 != 0:
                return _error_content(
                    f"op item get failed: {(stderr2 or stderr).strip()}"
                )
            stdout = stdout2
        value = stdout.strip()
        if not value or value.startswith("[use "):
            return _error_content(
                f"Field {field!r} not found or empty for item {title!r}. "
                "Use onepassword_fields to discover available field names."
            )
        return _ok_content(value)

    def _call_list(self, args: dict[str, Any]) -> dict[str, Any]:
        if "vault" not in args:
            return _error_content("Missing required parameter: 'vault'")
        vault = args["vault"]
        if vault not in _KNOWN_VAULTS:
            return _error_content(
                f"Vault {vault!r} not accessible. Known vaults: {sorted(_KNOWN_VAULTS)}"
            )
        try:
            items = _op_json(["item", "list", "--vault", vault])
        except (RuntimeError, json.JSONDecodeError) as exc:
            return _error_content(str(exc))
        result = [
            {
                "title": item.get("title", ""),
                "category": item.get("category", ""),
                "id": item.get("id", ""),
            }
            for item in items
        ]
        return _ok_content(json.dumps(result, indent=2))

    def _call_vaults(self, _args: dict[str, Any]) -> dict[str, Any]:
        try:
            vaults = _op_json(["vault", "list"])
        except (RuntimeError, json.JSONDecodeError) as exc:
            return _error_content(str(exc))
        result = [{"name": v.get("name", ""), "id": v.get("id", "")} for v in vaults]
        return _ok_content(json.dumps(result, indent=2))

    def _call_fields(self, args: dict[str, Any]) -> dict[str, Any]:
        for param in ("title", "vault"):
            if param not in args:
                return _error_content(f"Missing required parameter: {param!r}")
        title = args["title"]
        vault = args["vault"]
        if vault not in _KNOWN_VAULTS:
            return _error_content(
                f"Vault {vault!r} not accessible. Known vaults: {sorted(_KNOWN_VAULTS)}"
            )
        # Get item details without --reveal to see field names safely
        rc, stdout, stderr = _run_op(["item", "get", title, "--vault", vault])
        if rc != 0:
            return _error_content(f"op item get failed: {stderr.strip()}")
        # Parse the human-readable output to extract field names
        # The output format is:
        #   Fields:
        #     fieldname:  [use 'op item get ... --reveal' to reveal]
        fields: list[dict[str, str]] = []
        in_fields = False
        for line in stdout.splitlines():
            stripped = line.strip()
            if stripped == "Fields:":
                in_fields = True
                continue
            if in_fields:
                if stripped and not stripped.startswith("[use ") and ":" in stripped:
                    # Field line: "fieldname:  [use ...]" or "fieldname:  value"
                    field_name = stripped.split(":")[0].strip()
                    if field_name and field_name not in ("URLs", "Website", "Notes"):
                        fields.append({"name": field_name})
                elif (
                    stripped
                    and ":" not in stripped
                    and not stripped.startswith("[use ")
                ):
                    # Section ended
                    if stripped in ("URLs:", "Notes:", "Tags:", "Files:"):
                        in_fields = False
        return _ok_content(json.dumps(fields, indent=2))

    def _call_resolve(self, args: dict[str, Any]) -> dict[str, Any]:
        if "name" not in args:
            return _error_content("Missing required parameter: 'name'")
        name = args["name"].lower().strip()
        if name not in _RESOLVE_MAP:
            recognized = ", ".join(sorted(_RESOLVE_MAP.keys()))
            return _error_content(
                f"Name {name!r} not recognized. Recognized names: {recognized}"
            )
        title, vault, field = _RESOLVE_MAP[name]
        # Delegate to _call_get
        return self._call_get({"title": title, "vault": vault, "field": field})

    # ------------------------------------------------------------------
    # JSON-RPC 2.0 dispatcher
    # ------------------------------------------------------------------

    def dispatch(self, request: dict[str, Any]) -> dict[str, Any] | None:
        req_id = request.get("id")
        method = request.get("method", "")
        if req_id is None and not method.startswith("initialize"):
            return None
        try:
            params = request.get("params") or {}
            if method == "initialize":
                result = self.handle_initialize(params)
            elif method == "notifications/initialized":
                return None
            elif method == "tools/list":
                result = self.handle_tools_list(params)
            elif method == "tools/call":
                tool_name = params.get("name", "")
                arguments = params.get("arguments") or {}
                result = self.handle_tools_call(tool_name, arguments)
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": _METHOD_NOT_FOUND,
                        "message": f"Method not found: {method!r}",
                    },
                }
        except Exception as exc:  # noqa: BLE001
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": _INTERNAL_ERROR, "message": str(exc)},
            }
        return {"jsonrpc": "2.0", "id": req_id, "result": result}

    # ------------------------------------------------------------------
    # stdio loop
    # ------------------------------------------------------------------

    def run(self, stdin=None, stdout=None) -> None:
        inp = stdin or sys.stdin
        out = stdout or sys.stdout
        for line in inp:
            line = line.strip()
            if not line:
                continue
            try:
                request = json.loads(line)
            except json.JSONDecodeError:
                response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": "Parse error"},
                }
                out.write(json.dumps(response) + "\n")
                out.flush()
                continue
            response = self.dispatch(request)
            if response is not None:
                out.write(json.dumps(response) + "\n")
                out.flush()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    OnePasswordServer().run()


if __name__ == "__main__":
    main()
