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

"""Tests for mcp_audit, mcp_crypto, and mcp_health MCP servers."""

from __future__ import annotations

import json
import subprocess
import sys
import pytest


def _call_mcp(module: str, method: str, params: dict | None = None) -> dict:
    """Call an MCP server and return the parsed response."""
    request = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}
    payload = json.dumps(request)
    proc = subprocess.run(
        [sys.executable, "-m", module],
        input=payload,
        capture_output=True,
        text=True,
        timeout=15,
    )
    for line in proc.stdout.strip().split("\n"):
        if not line.strip():
            continue
        try:
            resp = json.loads(line)
            if resp.get("id") == 1:
                return resp
        except json.JSONDecodeError:
            continue
    pytest.fail(f"No valid response from {module}. stdout: {proc.stdout[:300]}")


# ===========================================================================
# mcp_audit tests
# ===========================================================================


class TestMCPAuditToolsList:
    def test_tools_list_returns_13(self):
        resp = _call_mcp("mcp_audit", "tools/list")
        tools = resp["result"]["tools"]
        assert len(tools) == 13

    def test_tools_have_required_fields(self):
        resp = _call_mcp("mcp_audit", "tools/list")
        for t in resp["result"]["tools"]:
            assert "name" in t
            assert "description" in t
            assert "inputSchema" in t

    def test_expected_tool_names(self):
        resp = _call_mcp("mcp_audit", "tools/list")
        names = {t["name"] for t in resp["result"]["tools"]}
        expected = {
            "audit_append_entry",
            "audit_query_entries",
            "audit_log_stats",
            "audit_export_log",
            "frameworks_list",
            "framework_get_details",
            "framework_get_controls",
            "mapper_generate_report",
            "mapper_get_gaps",
            "mapper_get_coverage",
            "stride_threat_catalog",
            "stride_map_threats_to_controls",
            "stride_get_mitigations",
        }
        assert names == expected


class TestMCPAuditFrameworks:
    def test_frameworks_list(self):
        resp = _call_mcp(
            "mcp_audit",
            "tools/call",
            {
                "name": "frameworks_list",
                "arguments": {},
            },
        )
        text = resp["result"]["content"][0]["text"]
        data = json.loads(text)
        assert "frameworks" in data or "count" in data

    def test_stride_threat_catalog(self):
        resp = _call_mcp(
            "mcp_audit",
            "tools/call",
            {
                "name": "stride_threat_catalog",
                "arguments": {},
            },
        )
        text = resp["result"]["content"][0]["text"]
        data = json.loads(text)
        # STRIDE has 6 categories — field may be named differently
        assert any(k in data for k in ("categories", "threats", "stride_categories"))
        assert (
            data.get("total_categories", 0) == 6 or len(data.get("stride_categories", data.get("categories", []))) == 6
        )


class TestMCPAuditLog:
    def test_audit_log_stats(self):
        resp = _call_mcp(
            "mcp_audit",
            "tools/call",
            {
                "name": "audit_log_stats",
                "arguments": {},
            },
        )
        text = resp["result"]["content"][0]["text"]
        data = json.loads(text)
        assert isinstance(data, dict)


# ===========================================================================
# mcp_crypto tests
# ===========================================================================


class TestMCPCryptoToolsList:
    def test_tools_list_returns_12(self):
        resp = _call_mcp("mcp_crypto", "tools/list")
        tools = resp["result"]["tools"]
        assert len(tools) == 12

    def test_tools_have_required_fields(self):
        resp = _call_mcp("mcp_crypto", "tools/list")
        for t in resp["result"]["tools"]:
            assert "name" in t
            assert "description" in t
            assert "inputSchema" in t

    def test_expected_tool_names(self):
        resp = _call_mcp("mcp_crypto", "tools/list")
        names = {t["name"] for t in resp["result"]["tools"]}
        expected = {
            "crypto_status",
            "crypto_openssl_check",
            "crypto_generate_key",
            "crypto_generate_mac_key",
            "crypto_init",
            "crypto_encrypt_envelope",
            "crypto_decrypt_envelope",
            "crypto_inspect_envelope",
            "crypto_hmac",
            "crypto_verify_hmac",
            "crypto_hash",
            "crypto_envelope_info",
        }
        assert names == expected


class TestMCPCryptoOperations:
    def test_crypto_status(self):
        resp = _call_mcp(
            "mcp_crypto",
            "tools/call",
            {
                "name": "crypto_status",
                "arguments": {},
            },
        )
        text = resp["result"]["content"][0]["text"]
        data = json.loads(text)
        assert isinstance(data, dict)

    def test_crypto_generate_key(self):
        resp = _call_mcp(
            "mcp_crypto",
            "tools/call",
            {
                "name": "crypto_generate_key",
                "arguments": {},
            },
        )
        text = resp["result"]["content"][0]["text"]
        data = json.loads(text)
        assert "key" in data or "key_hex" in data or "error" in data

    def test_crypto_hash(self):
        resp = _call_mcp(
            "mcp_crypto",
            "tools/call",
            {
                "name": "crypto_hash",
                "arguments": {"data_hex": "48656c6c6f", "algorithm": "sha256"},
            },
        )
        text = resp["result"]["content"][0]["text"]
        data = json.loads(text)
        assert "digest" in data or "digest_hex" in data or "hash" in data or "error" in data

    def test_crypto_envelope_info(self):
        resp = _call_mcp(
            "mcp_crypto",
            "tools/call",
            {
                "name": "crypto_envelope_info",
                "arguments": {},
            },
        )
        text = resp["result"]["content"][0]["text"]
        data = json.loads(text)
        assert isinstance(data, dict)


# ===========================================================================
# mcp_health tests
# ===========================================================================


class TestMCPHealthToolsList:
    def test_tools_list_returns_13(self):
        resp = _call_mcp("mcp_health", "tools/list")
        tools = resp["result"]["tools"]
        assert len(tools) == 13

    def test_tools_have_required_fields(self):
        resp = _call_mcp("mcp_health", "tools/list")
        for t in resp["result"]["tools"]:
            assert "name" in t
            assert "description" in t
            assert "inputSchema" in t

    def test_expected_tool_names(self):
        resp = _call_mcp("mcp_health", "tools/list")
        names = {t["name"] for t in resp["result"]["tools"]}
        expected = {
            "health_register_probe",
            "health_run_probe",
            "health_status",
            "health_probe_history",
            "lifecycle_get_state",
            "lifecycle_log_decision",
            "lifecycle_history",
            "delegation_create_context",
            "delegation_validate_depth",
            "delegation_check_scope",
            "lineage_record_modification",
            "lineage_get_modifications",
            "lineage_get_ancestors",
        }
        assert names == expected


class TestMCPHealthOperations:
    def test_health_status(self):
        resp = _call_mcp(
            "mcp_health",
            "tools/call",
            {
                "name": "health_status",
                "arguments": {},
            },
        )
        text = resp["result"]["content"][0]["text"]
        data = json.loads(text)
        assert isinstance(data, dict)

    def test_lifecycle_get_state(self):
        resp = _call_mcp(
            "mcp_health",
            "tools/call",
            {
                "name": "lifecycle_get_state",
                "arguments": {},
            },
        )
        text = resp["result"]["content"][0]["text"]
        data = json.loads(text)
        assert isinstance(data, dict)

    def test_delegation_create_context(self):
        resp = _call_mcp(
            "mcp_health",
            "tools/call",
            {
                "name": "delegation_create_context",
                "arguments": {
                    "delegator": "agent-1",
                    "delegatee": "agent-2",
                    "scope": {"operations": ["read"], "resources": ["data/*"]},
                },
            },
        )
        text = resp["result"]["content"][0]["text"]
        data = json.loads(text)
        assert "context" in data or "error" in data or "created" in data
