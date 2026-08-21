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

"""Tests for mcp_compliance.py — compliance evidence MCP server."""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

import mcp_compliance  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture()
def empty_audit_dir(tmp_path):
    """Empty governance audit directory."""
    d = tmp_path / "audit"
    d.mkdir()
    return str(d)


@pytest.fixture()
def populated_audit_dir(tmp_path):
    """Audit directory with a few governance JSONL entries."""
    d = tmp_path / "audit"
    d.mkdir()
    entries = [
        {"entry_id": "e1", "timestamp": "2026-01-01T00:00:00Z", "tuple_type": "DCT",
         "agent_id": "claude-code", "action": "read"},
        {"entry_id": "e2", "timestamp": "2026-01-01T00:01:00Z", "tuple_type": "INTENT",
         "agent_id": "codex", "action": "write"},
        {"entry_id": "e3", "timestamp": "2026-01-01T00:02:00Z", "tuple_type": "ATTEST",
         "agent_id": "claude-code", "action": "verify"},
        {"entry_id": "e4", "timestamp": "2026-01-01T00:03:00Z", "tuple_type": "CIRCUIT_BREAKER",
         "agent_id": "system", "action": "trip"},
        {"entry_id": "e5", "timestamp": "2026-01-01T00:04:00Z", "tuple_type": "KILLSWITCH",
         "agent_id": "human", "action": "engage"},
    ]
    logfile = d / "governance-2026-01-01.jsonl"
    with open(logfile, "w") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")
    return str(d)


# ---------------------------------------------------------------------------
# nist_map_controls
# ---------------------------------------------------------------------------
def test_nist_map_controls_empty_dir(empty_audit_dir):
    result = mcp_compliance.handle_tool("nist_map_controls", {"governance_dir": empty_audit_dir})
    assert "nist_csf_2_0" in result
    assert "nist_ai_rmf" in result
    assert result["entries_analyzed"] == 0


def test_nist_map_controls_with_entries(populated_audit_dir):
    result = mcp_compliance.handle_tool("nist_map_controls", {"governance_dir": populated_audit_dir})
    assert result["entries_analyzed"] == 5
    assert "nist_csf_2_0" in result
    assert "coverage_pct" in result["nist_csf_2_0"]


def test_nist_map_controls_coverage_format(populated_audit_dir):
    result = mcp_compliance.handle_tool("nist_map_controls", {"governance_dir": populated_audit_dir})
    csf = result["nist_csf_2_0"]
    assert "coverage" in csf
    assert "/" in csf["coverage"]  # e.g. "5/16"
    assert isinstance(csf["gaps"], list)


def test_nist_map_controls_nonexistent_dir():
    result = mcp_compliance.handle_tool("nist_map_controls", {"governance_dir": "/nonexistent/path"})
    assert result["entries_analyzed"] == 0


# ---------------------------------------------------------------------------
# soc2_assess
# ---------------------------------------------------------------------------
def test_soc2_assess_empty_dir(empty_audit_dir):
    result = mcp_compliance.handle_tool("soc2_assess", {"governance_dir": empty_audit_dir})
    assert "overall_readiness_pct" in result
    assert "trust_service_criteria" in result


def test_soc2_assess_has_five_criteria(empty_audit_dir):
    result = mcp_compliance.handle_tool("soc2_assess", {"governance_dir": empty_audit_dir})
    criteria = result["trust_service_criteria"]
    assert "Security" in criteria
    assert "Availability" in criteria
    assert "Processing Integrity" in criteria
    assert "Confidentiality" in criteria
    assert "Privacy" in criteria


def test_soc2_assess_readiness_label(empty_audit_dir):
    result = mcp_compliance.handle_tool("soc2_assess", {"governance_dir": empty_audit_dir})
    assert result["overall_readiness"] in ("READY", "PARTIAL", "GAP")


def test_soc2_assess_with_entries_higher_coverage(tmp_path):
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    populated_dir = tmp_path / "populated"
    populated_dir.mkdir()
    entries = [
        {"entry_id": f"e{i}", "timestamp": "2026-01-01T00:00:00Z",
         "tuple_type": t, "agent_id": "a", "action": "x"}
        for i, t in enumerate(["DCT", "INTENT", "ATTEST", "CIRCUIT_BREAKER", "KILLSWITCH"])
    ]
    with open(populated_dir / "governance-2026-01-01.jsonl", "w") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")

    empty_result = mcp_compliance.handle_tool("soc2_assess", {"governance_dir": str(empty_dir)})
    populated_result = mcp_compliance.handle_tool("soc2_assess", {"governance_dir": str(populated_dir)})
    assert populated_result["overall_readiness_pct"] >= empty_result["overall_readiness_pct"]


# ---------------------------------------------------------------------------
# iso_crosswalk
# ---------------------------------------------------------------------------
def test_iso_crosswalk_returns_crosswalk_table(empty_audit_dir):
    result = mcp_compliance.handle_tool("iso_crosswalk", {"governance_dir": empty_audit_dir})
    assert "crosswalk" in result
    assert isinstance(result["crosswalk"], list)
    assert len(result["crosswalk"]) > 0


def test_iso_crosswalk_frameworks_listed(empty_audit_dir):
    result = mcp_compliance.handle_tool("iso_crosswalk", {"governance_dir": empty_audit_dir})
    assert "frameworks" in result
    assert "ISO 27001" in result["frameworks"]
    assert "NIST CSF 2.0" in result["frameworks"]


def test_iso_crosswalk_entry_has_expected_keys(empty_audit_dir):
    result = mcp_compliance.handle_tool("iso_crosswalk", {"governance_dir": empty_audit_dir})
    entry = result["crosswalk"][0]
    assert "iso_control" in entry
    assert "description" in entry
    assert "has_evidence" in entry


def test_iso_crosswalk_coverage_structure(empty_audit_dir):
    result = mcp_compliance.handle_tool("iso_crosswalk", {"governance_dir": empty_audit_dir})
    cov = result["coverage"]
    assert "iso_controls_total" in cov
    assert "iso_coverage_pct" in cov
    assert cov["iso_controls_total"] > 0


# ---------------------------------------------------------------------------
# stride_analysis
# ---------------------------------------------------------------------------
def test_stride_analysis_empty_interactions():
    result = mcp_compliance.handle_tool("stride_analysis", {"interactions": []})
    assert "by_severity" in result
    assert "CRITICAL" in result["by_severity"]


def test_stride_analysis_unauthenticated_interaction():
    result = mcp_compliance.handle_tool("stride_analysis", {"interactions": [
        {"source": "agent-a", "target": "database", "data_type": "write",
         "auth_level": "none", "boundary": True, "audited": False, "rate_limited": False},
    ]})
    assert "findings" in result or "by_severity" in result
    # Unauthenticated cross-boundary write should produce findings
    total = sum(result["by_severity"].values())
    assert total > 0


def test_stride_analysis_authenticated_interaction():
    result = mcp_compliance.handle_tool("stride_analysis", {"interactions": [
        {"source": "claude-code", "target": "api", "data_type": "read",
         "auth_level": "hmac", "boundary": False, "audited": True, "rate_limited": True},
    ]})
    assert "by_severity" in result


def test_stride_analysis_multiple_interactions():
    interactions = [
        {"source": f"agent-{i}", "target": "resource", "data_type": "read",
         "auth_level": "token", "boundary": i % 2 == 0, "audited": True, "rate_limited": False}
        for i in range(5)
    ]
    result = mcp_compliance.handle_tool("stride_analysis", {"interactions": interactions})
    assert "by_severity" in result
    assert sum(result["by_severity"].values()) >= 0


def test_stride_analysis_severity_keys():
    result = mcp_compliance.handle_tool("stride_analysis", {"interactions": []})
    assert set(result["by_severity"].keys()) == {"CRITICAL", "HIGH", "MEDIUM", "LOW"}


# ---------------------------------------------------------------------------
# compliance_evidence_export
# ---------------------------------------------------------------------------
def test_compliance_evidence_export_all(empty_audit_dir):
    result = mcp_compliance.handle_tool("compliance_evidence_export", {
        "governance_dir": empty_audit_dir,
        "framework": "all",
    })
    assert "evidence" in result
    assert "total_evidence_items" in result


def test_compliance_evidence_export_soc2_only(empty_audit_dir):
    result = mcp_compliance.handle_tool("compliance_evidence_export", {
        "governance_dir": empty_audit_dir,
        "framework": "soc2",
    })
    assert "soc2" in result["evidence"]
    assert "nist" not in result["evidence"]


def test_compliance_evidence_export_nist_only(empty_audit_dir):
    result = mcp_compliance.handle_tool("compliance_evidence_export", {
        "governance_dir": empty_audit_dir,
        "framework": "nist",
    })
    assert "nist" in result["evidence"]
    assert "soc2" not in result["evidence"]


def test_compliance_evidence_export_owasp(empty_audit_dir):
    result = mcp_compliance.handle_tool("compliance_evidence_export", {
        "governance_dir": empty_audit_dir,
        "framework": "owasp",
    })
    assert "owasp_agentic" in result["evidence"]


def test_compliance_evidence_export_iso(empty_audit_dir):
    result = mcp_compliance.handle_tool("compliance_evidence_export", {
        "governance_dir": empty_audit_dir,
        "framework": "iso",
    })
    assert "iso_crosswalk" in result["evidence"]


# ---------------------------------------------------------------------------
# Unknown tool
# ---------------------------------------------------------------------------
def test_unknown_tool():
    result = mcp_compliance.handle_tool("no_such_tool", {})
    assert "error" in result


# ---------------------------------------------------------------------------
# Protocol-level: subprocess JSON-RPC
# ---------------------------------------------------------------------------
def _rpc_compliance(messages):
    server_path = str(_REPO_ROOT / "mcp_compliance.py")
    env = os.environ.copy()
    env["GOVERNANCE_AUDIT_DIR"] = str(Path(tempfile.mkdtemp()) / "audit")
    os.makedirs(env["GOVERNANCE_AUDIT_DIR"], exist_ok=True)

    proc = subprocess.Popen(
        [sys.executable, server_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        text=True,
    )
    inp = "\n".join(json.dumps(m) for m in messages) + "\n"
    try:
        stdout, _ = proc.communicate(input=inp, timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, _ = proc.communicate()

    responses = []
    for line in stdout.splitlines():
        line = line.strip()
        if line:
            try:
                responses.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return responses


def test_compliance_protocol_initialize():
    responses = _rpc_compliance([
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
    ])
    assert any(r.get("id") == 1 and "result" in r for r in responses)
    r = next(r for r in responses if r.get("id") == 1)
    assert r["result"]["serverInfo"]["name"] == "hummbl-compliance"


def test_compliance_protocol_tools_list():
    responses = _rpc_compliance([
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
    ])
    tools_resp = next(r for r in responses if r.get("id") == 2)
    names = {t["name"] for t in tools_resp["result"]["tools"]}
    assert "nist_map_controls" in names
    assert "soc2_assess" in names
    assert "stride_analysis" in names
