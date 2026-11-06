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

"""Protocol guard tests: non-dict JSON-RPC payloads must not kill run()."""

import io
import json

from base120_mcp_server import Base120Server


def _run(payload: str) -> list[dict]:
    inp = io.StringIO(payload)
    out = io.StringIO()
    Base120Server().run(stdin=inp, stdout=out)
    return [json.loads(line) for line in out.getvalue().splitlines() if line.strip()]


def test_non_dict_payloads_get_invalid_request():
    msgs = _run('123\n[1, 2]\n{"jsonrpc": "2.0", "id": 7, "method": "initialize"}\n')
    errors = [m for m in msgs if "error" in m]
    assert len(errors) == 2
    assert all(e["error"]["code"] == -32600 for e in errors)
    assert any(m.get("id") == 7 and "result" in m for m in msgs)


def test_non_dict_params_and_method_normalized():
    msgs = _run(
        '{"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": [1, 2]}\n'
        '{"jsonrpc": "2.0", "id": 4, "method": 5}\n'
    )
    assert len(msgs) == 2
    assert all(m.get("id") in (3, 4) for m in msgs)
