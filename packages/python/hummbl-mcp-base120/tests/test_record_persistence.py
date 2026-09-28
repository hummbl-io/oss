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

"""Tests for base120_record ledger persistence."""

import json

import base120_mcp_server
from base120.ledger import Ledger
from base120_mcp_server import Base120Server


def test_record_appends_tuple_to_ledger(tmp_path, monkeypatch):
    ledger_file = tmp_path / "ledger.jsonl"
    monkeypatch.setattr(base120_mcp_server, "Ledger", lambda: Ledger(ledger_file))

    resp = Base120Server().handle_tools_call(
        "base120_record",
        {
            "code": "P6",
            "problem": "verify ledger persistence",
            "recommendation": "append the tuple",
            "confidence": 0.9,
        },
    )
    payload = json.loads(resp["content"][0]["text"])

    assert payload["persisted"] is True
    assert payload["ledger_path"] == str(ledger_file)
    entries = Ledger(ledger_file).project()
    assert len(entries) == 1
    assert entries[0].id == "P6"
