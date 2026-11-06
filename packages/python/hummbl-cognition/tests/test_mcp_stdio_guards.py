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

"""Protocol guard tests: non-dict JSON-RPC payloads must not kill serve_stdio."""

import io
import json

import pytest

from hummbl_cognition import mcp_cognitive_state, mcp_working_memory

MODULES = [mcp_cognitive_state, mcp_working_memory]


@pytest.mark.parametrize("srv", MODULES, ids=lambda m: m.__name__)
def test_non_dict_payloads_get_invalid_request(srv, monkeypatch, capsys):
    monkeypatch.setattr(
        "sys.stdin",
        io.StringIO(
            '123\n[1, 2]\n{"jsonrpc": "2.0", "id": 7, "method": "initialize"}\n'
        ),
    )
    srv.serve_stdio()
    out = [
        json.loads(line)
        for line in capsys.readouterr().out.splitlines()
        if line.strip()
    ]
    errors = [m for m in out if "error" in m]
    assert len(errors) == 2
    assert all(e["error"]["code"] == -32600 for e in errors)
    assert any(m.get("id") == 7 and "result" in m for m in out)


@pytest.mark.parametrize("srv", MODULES, ids=lambda m: m.__name__)
def test_non_dict_params_normalized(srv, monkeypatch, capsys):
    monkeypatch.setattr(
        "sys.stdin",
        io.StringIO(
            '{"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": [1, 2]}\n'
        ),
    )
    srv.serve_stdio()
    out = [
        json.loads(line)
        for line in capsys.readouterr().out.splitlines()
        if line.strip()
    ]
    assert len(out) == 1
    assert out[0].get("id") == 3
