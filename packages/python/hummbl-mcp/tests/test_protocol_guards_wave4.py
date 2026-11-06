# Copyright 2024-2026 HUMMBL
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

"""Wave-4 protocol guard tests: non-dict JSON-RPC payloads must not crash dispatchers."""

import io
import json
import sys
from contextlib import contextmanager

import pytest

NON_DICT_PAYLOADS = (123, [1, 2], "text")


def _assert_invalid_request(resp):
    assert resp["jsonrpc"] == "2.0"
    assert resp["id"] is None
    assert resp["error"]["code"] == -32600


def _assert_dispatch_guards(handle, *extra_args):
    """Non-dict request -> -32600; valid initialize works; non-dict params safe."""
    for payload in NON_DICT_PAYLOADS:
        _assert_invalid_request(handle(payload, *extra_args))

    init = handle({"jsonrpc": "2.0", "id": 1, "method": "initialize"}, *extra_args)
    assert init["id"] == 1
    assert "result" in init

    call = handle(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": [1, 2],
        },
        *extra_args,
    )
    assert call["id"] == 2


# ---------------------------------------------------------------------------
# Dispatch-style handlers (guard lives inside the request handler)
# ---------------------------------------------------------------------------


def test_mcp_governance_handle_request_guards():
    from hummbl_mcp import mcp_governance

    _assert_dispatch_guards(mcp_governance.handle_request)


def test_mcp_kill_switch_handle_request_guards():
    pytest.importorskip("hummbl_governance")
    from hummbl_mcp import mcp_kill_switch

    _assert_dispatch_guards(mcp_kill_switch.handle_request)


def test_mcp_skills_handle_request_guards():
    from hummbl_mcp import mcp_skills

    _assert_dispatch_guards(mcp_skills.handle_request)


def test_mcp_spark_gateway_handle_request_guards():
    from hummbl_mcp import mcp_spark_gateway

    _assert_dispatch_guards(mcp_spark_gateway.handle_request)


def test_mcp_doctor_handle_request_guards():
    from hummbl_mcp import mcp_doctor

    _assert_dispatch_guards(mcp_doctor.handle_request)


def test_mcp_call_tracer_handle_request_guards():
    from hummbl_mcp import mcp_call_tracer

    _assert_dispatch_guards(mcp_call_tracer._tr_handle_request)


def test_mcp_gateway_handle_request_guards():
    from hummbl_mcp import mcp_gateway

    _assert_dispatch_guards(mcp_gateway._gw_handle_request)


def test_mcp_trust_handle_request_guards():
    from hummbl_mcp import mcp_trust

    # scorer is only touched by tools/call dispatch; None is safe for these paths
    _assert_dispatch_guards(mcp_trust.handle_request, None)


def test_idp_mcp_gateway_handle_request_guards():
    from hummbl_mcp import idp_mcp_gateway

    # gateway=None, idp_enabled=False: tools/call short-circuits before gateway use
    _assert_dispatch_guards(idp_mcp_gateway._idp_handle_request, None, False)


def test_mcp_research_handle_message_guards():
    from hummbl_mcp.mcp_research import ResearchMCPServer

    server = ResearchMCPServer()
    for payload in NON_DICT_PAYLOADS:
        resp = server.handle_message(payload)
        _assert_invalid_request(resp)

    init = server.handle_message({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
    assert init["id"] == 1
    assert "result" in init

    call = server.handle_message(
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": [1, 2]}
    )
    assert call["id"] == 2


# ---------------------------------------------------------------------------
# Inline stdin loops
# ---------------------------------------------------------------------------


def _run_stdin_loop(monkeypatch, serve, payload: str):
    inp = io.StringIO(payload)
    out = io.StringIO()
    monkeypatch.setattr(sys, "stdin", inp)
    monkeypatch.setattr(sys, "stdout", out)
    serve()
    return [json.loads(line) for line in out.getvalue().splitlines() if line.strip()]


def test_mcp_gateway_serve_stdio_guards(monkeypatch):
    from hummbl_mcp import mcp_gateway

    msgs = _run_stdin_loop(
        monkeypatch,
        mcp_gateway.serve_stdio,
        '123\n[1, 2]\n{"jsonrpc": "2.0", "id": 7, "method": "initialize"}\n'
        '{"jsonrpc": "2.0", "id": 8, "method": "tools/call", "params": [1]}\n',
    )
    errors = [m for m in msgs if "error" in m]
    assert len(errors) == 2
    assert all(e["error"]["code"] == -32600 for e in errors)
    assert any(m.get("id") == 7 and "result" in m for m in msgs)
    assert any(m.get("id") == 8 for m in msgs)


@contextmanager
def _import_with_stdout_restore(module_name):
    """Import a module that rebinds sys.stdout at import time, then restore it."""
    prev_stdout = sys.stdout
    prev_stderr = sys.stderr
    try:
        mod = pytest.importorskip(module_name)
    finally:
        sys.stdout = prev_stdout
        sys.stderr = prev_stderr
    yield mod


def test_mcp_ollama_router_main_guards(monkeypatch):
    with _import_with_stdout_restore("hummbl_mcp.mcp_ollama_router") as mod:
        out = io.StringIO()
        monkeypatch.setattr(mod, "original_stdout", out)
        monkeypatch.setattr(
            sys,
            "stdin",
            io.StringIO(
                '123\n[1, 2]\n{"jsonrpc": "2.0", "id": 7, "method": "initialize"}\n'
                '{"jsonrpc": "2.0", "id": 8, "method": "tools/call", "params": [1]}\n'
            ),
        )
        mod.main()
        msgs = [json.loads(line) for line in out.getvalue().splitlines() if line.strip()]

    invalid = [m for m in msgs if m.get("error", {}).get("code") == -32600]
    assert len(invalid) == 2
    assert all(m["id"] is None for m in invalid)
    assert any(m.get("id") == 7 and "result" in m for m in msgs)
    assert any(m.get("id") == 8 for m in msgs)


def test_mcp_git_vault_main_guards(monkeypatch):
    with _import_with_stdout_restore("hummbl_mcp.mcp_git_vault") as mod:
        out = io.StringIO()
        monkeypatch.setattr(mod, "original_stdout", out)
        monkeypatch.setattr(
            sys,
            "stdin",
            io.StringIO(
                '123\n[1, 2]\n{"jsonrpc": "2.0", "id": 7, "method": "initialize"}\n'
                '{"jsonrpc": "2.0", "id": 8, "method": "tools/call", "params": [1]}\n'
            ),
        )
        mod.main()
        msgs = [json.loads(line) for line in out.getvalue().splitlines() if line.strip()]

    invalid = [m for m in msgs if m.get("error", {}).get("code") == -32600]
    assert len(invalid) == 2
    assert all(m["id"] is None for m in invalid)
    assert any(m.get("id") == 7 and "result" in m for m in msgs)
    assert any(m.get("id") == 8 for m in msgs)
