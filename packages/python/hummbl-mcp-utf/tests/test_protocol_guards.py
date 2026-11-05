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

"""Protocol guard tests: non-dict params must not crash the stdio loop."""

import io
import json
import sys

import utf_mcp_server as srv


def _run(payload: str) -> list[dict]:
    inp = io.StringIO(payload)
    out = io.StringIO()
    old_stdin, old_stdout = sys.stdin, sys.stdout
    sys.stdin, sys.stdout = inp, out
    try:
        srv.main()
    finally:
        sys.stdin, sys.stdout = old_stdin, old_stdout
    return [json.loads(line) for line in out.getvalue().splitlines() if line.strip()]


def test_non_dict_payloads_skipped_and_initialize_works():
    msgs = _run(
        '123\n[1, 2]\n{"jsonrpc": "2.0", "id": 7, "method": "initialize"}\n'
    )
    assert any(m.get("id") == 7 and "result" in m for m in msgs)


def test_non_dict_params_does_not_crash():
    msgs = _run(
        '{"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": [1, 2]}\n'
    )
    assert len(msgs) == 1
    assert msgs[0].get("id") == 3
