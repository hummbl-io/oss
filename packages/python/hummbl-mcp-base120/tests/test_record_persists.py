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

"""base120_record must persist the tuple to the ledger, not just return it.

The verb promises a durable artifact; a response object alone does not
prove the append happened. These tests assert the side effect.
"""

import json
from pathlib import Path
from unittest.mock import patch

import base120_mcp_server
from base120.ledger import Ledger
from base120_mcp_server import Base120Server


def _record(server: Base120Server, **overrides) -> dict:
    args = {
        "code": "IN3",
        "problem": "p",
        "recommendation": "r",
        "confidence": 0.5,
    }
    args.update(overrides)
    resp = server.handle_tools_call("base120_record", args)
    return json.loads(resp["content"][0]["text"])


def test_record_appends_to_ledger(tmp_path):
    ledger_file = tmp_path / "ledger.jsonl"
    server = Base120Server()
    with patch.object(
        base120_mcp_server, "Ledger", return_value=Ledger(ledger_file)
    ):
        out = _record(server)
    assert out["persisted"] is True
    assert out["ledger_path"] == str(ledger_file)
    lines = ledger_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["id"] == "IN3"
    assert entry["state"] == "r"  # tuple.state is the recommendation text
    assert entry["drift"] == 0.5


def test_record_reports_not_persisted_on_write_failure():
    server = Base120Server()
    with patch.object(base120_mcp_server, "Ledger") as mock_ledger:
        mock_ledger.return_value.append.side_effect = OSError("read-only fs")
        mock_ledger.return_value.path = Path("/nonexistent/ledger.jsonl")
        out = _record(server)
    # The call still returns the minted tuple; persistence is reported.
    assert out["persisted"] is False
    assert out["tuple"]["id"] == "IN3"


def test_record_missing_param_still_errors():
    server = Base120Server()
    resp = server.handle_tools_call(
        "base120_record", {"code": "IN3", "problem": "p"})
    assert resp.get("isError") is True or "Missing" in resp["content"][0]["text"]
