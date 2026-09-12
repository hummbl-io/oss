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

"""Tests for the tied-score flag on base120_select results."""

import json

from base120_mcp_server import Base120Server


def _select(server: Base120Server, problem: str, n: int = 5) -> list[dict]:
    resp = server.handle_tools_call("base120_select", {"problem": problem, "n": n})
    return json.loads(resp["content"][0]["text"])


def test_select_flags_uniform_scores_as_tied():
    # Gibberish problem: every operator scores 0.0 — a null result, not a ranking.
    payload = _select(Base120Server(), "zxcvbnm qwerty", n=5)
    assert len(payload) == 5
    assert all(item["tied"] is True for item in payload)


def test_select_omits_flag_when_scores_discriminate():
    payload = _select(Base120Server(), "root cause why", n=5)
    assert all("tied" not in item for item in payload)
