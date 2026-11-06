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

"""Protocol guard tests: non-dict JSON-RPC payloads must not crash handle_request."""

import signal_mcp_server as srv


def test_non_dict_requests_get_invalid_request():
    for payload in (123, [1, 2], "text"):
        res = srv.handle_request(payload)
        assert res["jsonrpc"] == "2.0"
        assert res["id"] is None
        assert res["error"]["code"] == -32600


def test_initialize_still_works():
    res = srv.handle_request({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
    assert res["id"] == 1
    assert "result" in res


def test_non_dict_params_does_not_crash():
    res = srv.handle_request(
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": [1, 2]}
    )
    assert res["id"] == 2
