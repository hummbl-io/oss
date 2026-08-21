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

"""Tests for hummbl_governance.compliance_mapper."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path


from hummbl_governance.compliance_mapper import (
    ComplianceMapper,
    ComplianceReport,
    main,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _today_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _days_ago_str(n: int) -> str:
    dt = datetime.now(timezone.utc) - timedelta(days=n)
    return dt.strftime("%Y-%m-%d")


def _write_governance_file(directory: Path, date_str: str, entries: list[dict]) -> Path:
    """Write a governance JSONL file with the given entries."""
    fp = directory / f"governance-{date_str}.jsonl"
    with open(fp, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")
    return fp


def _dct_entry(entry_id: str = "e1", signed: bool = True) -> dict:
    return {
        "entry_id": entry_id,
        "timestamp": "2026-03-23T10:00:00Z",
        "task_id": "t1",
        "intent_id": "i1",
        "signature": "sig123" if signed else None,
        "tuple_type": "DCT",
        "tuple_data": {
            "issuer": "system",
            "subject": "agent-1",
            "resource_selectors": ["res:*"],
            "ops_allowed": ["read"],
        },
    }


def _dctx_entry(entry_id: str = "e2") -> dict:
    return {
        "entry_id": entry_id,
        "timestamp": "2026-03-23T10:01:00Z",
        "task_id": "t1",
        "intent_id": "i1",
        "signature": "sig456",
        "tuple_type": "DCTX",
        "tuple_data": {
            "delegator": "agent-1",
            "delegatee": "agent-2",
            "event": "task_delegated",
        },
    }


def _intent_entry(entry_id: str = "e3") -> dict:
    return {
        "entry_id": entry_id,
        "timestamp": "2026-03-23T10:02:00Z",
        "task_id": "t2",
        "intent_id": "i2",
        "signature": "sig789",
        "tuple_type": "INTENT",
        "tuple_data": {
            "agent": "claude",
            "objective": "generate briefing",
            "phase": "SPECIFICATION",
        },
    }


def _contract_entry(entry_id: str = "e4") -> dict:
    return {
        "entry_id": entry_id,
        "timestamp": "2026-03-23T10:03:00Z",
        "task_id": "t3",
        "intent_id": "i3",
        "signature": None,
        "tuple_type": "CONTRACT",
        "tuple_data": {
            "delegator": "system",
            "delegatee": "agent-1",
            "event": "contract_created",
        },
    }


def _circuit_breaker_entry(entry_id: str = "e5") -> dict:
    return {
        "entry_id": entry_id,
        "timestamp": "2026-03-23T10:04:00Z",
        "task_id": "t4",
        "intent_id": "i4",
        "signature": "sigabc",
        "tuple_type": "CIRCUIT_BREAKER",
        "tuple_data": {
            "state": "OPEN",
            "adapter": "github",
        },
    }


def _killswitch_entry(entry_id: str = "e6") -> dict:
    return {
        "entry_id": entry_id,
        "timestamp": "2026-03-23T10:05:00Z",
        "task_id": "t5",
        "intent_id": "i5",
        "signature": "sigdef",
        "tuple_type": "KILLSWITCH",
        "tuple_data": {
            "state": "HALT_ALL",
            "adapter": None,
        },
    }


# ---------------------------------------------------------------------------
# TestComplianceReport
# ---------------------------------------------------------------------------

class TestComplianceReport:
    def test_creation(self):
        report = ComplianceReport(
            generated_at="2026-03-23T10:00:00Z",
            framework="SOC2",
        )
        assert report.generated_at == "2026-03-23T10:00:00Z"
        assert report.framework == "SOC2"
        assert report.controls == {}

    def test_to_json_roundtrip(self):
        report = ComplianceReport(
            generated_at="2026-03-23T10:00:00Z",
            framework="GDPR",
            controls={"Art.30": [{"entry_id": "e1"}]},
        )
        json_str = report.to_json()
        parsed = json.loads(json_str)
        assert parsed["framework"] == "GDPR"
        assert parsed["generated_at"] == "2026-03-23T10:00:00Z"
        assert len(parsed["controls"]["Art.30"]) == 1
        assert parsed["controls"]["Art.30"][0]["entry_id"] == "e1"

    def test_empty_controls(self):
        report = ComplianceReport(
            generated_at="2026-03-23T10:00:00Z",
            framework="SOC2",
            controls={"CC6.1": [], "CC7.2": []},
        )
        parsed = json.loads(report.to_json())
        assert parsed["controls"]["CC6.1"] == []
        assert parsed["controls"]["CC7.2"] == []

    def test_to_json_sorted_keys(self):
        report = ComplianceReport(
            generated_at="2026-03-23T10:00:00Z",
            framework="SOC2",
            controls={"z_control": [], "a_control": []},
        )
        json_str = report.to_json()
        # Keys should be sorted
        assert json_str.index('"controls"') < json_str.index('"framework"')
        assert json_str.index('"framework"') < json_str.index('"generated_at"')


# ---------------------------------------------------------------------------
# TestComplianceMapperSOC2
# ---------------------------------------------------------------------------

class TestComplianceMapperSOC2:
    def test_generates_report(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_dct_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_soc2_report(days=7)
        assert report.framework == "SOC2"
        assert "CC6.1" in report.controls
        assert "CC7.2" in report.controls
        assert "CC6.3" in report.controls

    def test_dct_maps_to_cc61(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_dct_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_soc2_report(days=7)
        assert len(report.controls["CC6.1"]) == 1
        evidence = report.controls["CC6.1"][0]
        assert evidence["issuer"] == "system"
        assert evidence["subject"] == "agent-1"
        assert evidence["resources"] == ["res:*"]
        assert evidence["ops"] == ["read"]

    def test_dct_maps_to_cc63(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_dct_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_soc2_report(days=7)
        assert len(report.controls["CC6.3"]) == 1
        evidence = report.controls["CC6.3"][0]
        assert evidence["subject"] == "agent-1"
        assert evidence["issuer"] == "system"

    def test_signed_maps_to_cc72(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_dct_entry(signed=True)])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_soc2_report(days=7)
        assert len(report.controls["CC7.2"]) == 1

    def test_unsigned_skips_cc72(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_dct_entry(signed=False)])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_soc2_report(days=7)
        assert len(report.controls["CC7.2"]) == 0

    def test_date_filter_excludes_old(self, tmp_path):
        _write_governance_file(tmp_path, _days_ago_str(30), [_dct_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_soc2_report(days=7)
        assert len(report.controls["CC6.1"]) == 0

    def test_date_filter_includes_recent(self, tmp_path):
        _write_governance_file(tmp_path, _days_ago_str(3), [_dct_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_soc2_report(days=7)
        assert len(report.controls["CC6.1"]) == 1


# ---------------------------------------------------------------------------
# TestComplianceMapperGDPR
# ---------------------------------------------------------------------------

class TestComplianceMapperGDPR:
    def test_dctx_maps_to_art30(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_dctx_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_gdpr_report(days=30)
        assert len(report.controls["Art.30"]) == 1
        evidence = report.controls["Art.30"][0]
        assert evidence["tuple_type"] == "DCTX"
        assert evidence["delegator"] == "agent-1"

    def test_contract_maps_to_art30(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_contract_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_gdpr_report(days=30)
        assert len(report.controls["Art.30"]) == 1

    def test_signed_maps_to_art32(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_dctx_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_gdpr_report(days=30)
        # dctx_entry has signature="sig456"
        assert len(report.controls["Art.32"]) == 1
        evidence = report.controls["Art.32"][0]
        assert evidence["tuple_type"] == "DCTX"

    def test_unsigned_skips_art32(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_contract_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_gdpr_report(days=30)
        # contract_entry has signature=None
        assert len(report.controls["Art.32"]) == 0

    def test_gdpr_all_controls_initialized(self, tmp_path):
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_gdpr_report(days=30)
        assert set(report.controls.keys()) == {"Art.5", "Art.6", "Art.25", "Art.28", "Art.30", "Art.32"}

    def test_intent_maps_to_art5(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_intent_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_gdpr_report(days=30)
        assert len(report.controls["Art.5"]) == 1
        assert report.controls["Art.5"][0]["objective"] == "generate briefing"

    def test_contract_maps_to_art6(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_contract_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_gdpr_report(days=30)
        assert len(report.controls["Art.6"]) == 1

    def test_dct_maps_to_art25(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_dct_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_gdpr_report(days=30)
        assert len(report.controls["Art.25"]) == 1
        assert "ops_allowed" in report.controls["Art.25"][0]

    def test_dctx_maps_to_art28(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_dctx_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_gdpr_report(days=30)
        assert len(report.controls["Art.28"]) == 1
        assert report.controls["Art.28"][0]["delegator"] == "agent-1"


# ---------------------------------------------------------------------------
# TestComplianceMapperOWASP
# ---------------------------------------------------------------------------

class TestComplianceMapperOWASP:
    def test_all_10_controls_initialized(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_owasp_report(days=7)
        expected = {f"ASI{str(i).zfill(2)}" for i in range(1, 11)}
        assert set(report.controls.keys()) == expected

    def test_intent_maps_to_asi01(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_intent_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_owasp_report(days=7)
        assert len(report.controls["ASI01"]) == 1
        evidence = report.controls["ASI01"][0]
        assert evidence["agent"] == "claude"
        assert evidence["objective"] == "generate briefing"
        assert evidence["phase"] == "SPECIFICATION"

    def test_dct_maps_to_asi03(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_dct_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_owasp_report(days=7)
        assert len(report.controls["ASI03"]) == 1
        evidence = report.controls["ASI03"][0]
        assert evidence["issuer"] == "system"
        assert evidence["subject"] == "agent-1"

    def test_signed_maps_to_asi04(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_dct_entry(signed=True)])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_owasp_report(days=7)
        assert len(report.controls["ASI04"]) == 1

    def test_unsigned_skips_asi04(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_dct_entry(signed=False)])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_owasp_report(days=7)
        assert len(report.controls["ASI04"]) == 0

    def test_dctx_maps_to_asi07(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_dctx_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_owasp_report(days=7)
        assert len(report.controls["ASI07"]) == 1
        evidence = report.controls["ASI07"][0]
        assert evidence["delegator"] == "agent-1"
        assert evidence["delegatee"] == "agent-2"

    def test_circuit_breaker_maps_to_asi08(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_circuit_breaker_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_owasp_report(days=7)
        assert len(report.controls["ASI08"]) == 1
        evidence = report.controls["ASI08"][0]
        assert evidence["tuple_type"] == "CIRCUIT_BREAKER"
        assert evidence["state"] == "OPEN"

    def test_killswitch_maps_to_asi08(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_killswitch_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_owasp_report(days=7)
        assert len(report.controls["ASI08"]) == 1
        evidence = report.controls["ASI08"][0]
        assert evidence["tuple_type"] == "KILLSWITCH"
        assert evidence["state"] == "HALT_ALL"


# ---------------------------------------------------------------------------
# TestParseRobustness
# ---------------------------------------------------------------------------

class TestParseRobustness:
    def test_malformed_jsonl_line_skipped(self, tmp_path):
        fp = tmp_path / f"governance-{_today_str()}.jsonl"
        with open(fp, "w") as f:
            f.write("NOT VALID JSON\n")
            f.write(json.dumps(_dct_entry()) + "\n")
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_soc2_report(days=7)
        assert len(report.controls["CC6.1"]) == 1

    def test_bad_filename_skipped(self, tmp_path):
        fp = tmp_path / "governance-not-a-date.jsonl"
        with open(fp, "w") as f:
            f.write(json.dumps(_dct_entry()) + "\n")
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_soc2_report(days=7)
        assert len(report.controls["CC6.1"]) == 0

    def test_empty_governance_dir(self, tmp_path):
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_soc2_report(days=7)
        assert report.controls["CC6.1"] == []


# ---------------------------------------------------------------------------
# TestDefaultDir
# ---------------------------------------------------------------------------

class TestDefaultDir:
    def test_default_governance_dir(self):
        mapper = ComplianceMapper()
        assert mapper.governance_dir == Path("governance")

    def test_custom_governance_dir(self, tmp_path):
        mapper = ComplianceMapper(governance_dir=tmp_path)
        assert mapper.governance_dir == tmp_path

    def test_string_governance_dir(self, tmp_path):
        mapper = ComplianceMapper(governance_dir=str(tmp_path))
        assert mapper.governance_dir == tmp_path


# ---------------------------------------------------------------------------
# TestCLI
# ---------------------------------------------------------------------------

class TestCLI:
    def test_framework_soc2(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_dct_entry()])
        rc = main(["--framework", "soc2", "--dir", str(tmp_path)])
        assert rc == 0

    def test_framework_gdpr(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_dctx_entry()])
        rc = main(["--framework", "gdpr", "--dir", str(tmp_path)])
        assert rc == 0

    def test_framework_owasp(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_intent_entry()])
        rc = main(["--framework", "owasp", "--dir", str(tmp_path)])
        assert rc == 0

    def test_output_file(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_dct_entry()])
        output_path = tmp_path / "report.json"
        rc = main(["--dir", str(tmp_path), "--output", str(output_path)])
        assert rc == 0
        assert output_path.exists()
        parsed = json.loads(output_path.read_text())
        assert parsed["framework"] == "SOC2"

    def test_days_arg(self, tmp_path):
        _write_governance_file(tmp_path, _days_ago_str(10), [_dct_entry()])
        # days=5 should exclude 10-day-old file
        output_path = tmp_path / "report.json"
        rc = main(["--dir", str(tmp_path), "--days", "5", "--output", str(output_path)])
        assert rc == 0
        parsed = json.loads(output_path.read_text())
        assert len(parsed["controls"]["CC6.1"]) == 0

    def test_framework_nist_rmf(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_intent_entry()])
        rc = main(["--framework", "nist-rmf", "--dir", str(tmp_path)])
        assert rc == 0

    def test_framework_eu_ai_act(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_killswitch_entry()])
        rc = main(["--framework", "eu-ai-act", "--dir", str(tmp_path)])
        assert rc == 0


# ---------------------------------------------------------------------------
# Fixtures shared between NIST/EU tests
# ---------------------------------------------------------------------------

def _attest_entry(entry_id: str = "e7") -> dict:
    return {
        "entry_id": entry_id,
        "timestamp": "2026-03-23T11:00:00Z",
        "task_id": "t6",
        "intent_id": "i6",
        "signature": "sigattest",
        "tuple_type": "ATTEST",
        "tuple_data": {
            "claim": "output validated",
            "outcome": "PASS",
        },
    }


def _cost_governor_entry(entry_id: str = "e8") -> dict:
    return {
        "entry_id": entry_id,
        "timestamp": "2026-03-23T11:01:00Z",
        "task_id": "t7",
        "intent_id": "i7",
        "signature": None,
        "tuple_type": "COST_GOVERNOR",
        "tuple_data": {
            "agent": "claude",
            "decision": "ALLOW",
            "spend": 0.05,
            "budget": 10.0,
        },
    }


# ---------------------------------------------------------------------------
# TestComplianceMapperNISTRMF
# ---------------------------------------------------------------------------

class TestComplianceMapperNISTRMF:
    def test_all_controls_initialized(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_nist_rmf_report(days=30)
        assert report.framework == "NIST_AI_RMF"
        expected = {
            "GOVERN-1.1", "GOVERN-1.7",
            "MAP-1.1", "MAP-2.2",
            "MEASURE-2.5", "MEASURE-2.8",
            "MANAGE-1.3", "MANAGE-2.4",
        }
        assert set(report.controls.keys()) == expected

    def test_intent_maps_to_govern_1_1(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_intent_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_nist_rmf_report(days=30)
        assert len(report.controls["GOVERN-1.1"]) == 1
        evidence = report.controls["GOVERN-1.1"][0]
        assert evidence["agent"] == "claude"
        assert evidence["objective"] == "generate briefing"
        assert evidence["phase"] == "SPECIFICATION"

    def test_circuit_breaker_maps_to_govern_1_7(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_circuit_breaker_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_nist_rmf_report(days=30)
        assert len(report.controls["GOVERN-1.7"]) == 1
        evidence = report.controls["GOVERN-1.7"][0]
        assert evidence["tuple_type"] == "CIRCUIT_BREAKER"
        assert evidence["state"] == "OPEN"

    def test_killswitch_maps_to_govern_1_7_and_manage_1_3(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_killswitch_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_nist_rmf_report(days=30)
        assert len(report.controls["GOVERN-1.7"]) == 1
        assert len(report.controls["MANAGE-1.3"]) == 1
        evidence = report.controls["MANAGE-1.3"][0]
        assert evidence["tuple_type"] == "KILLSWITCH"
        assert evidence["state"] == "HALT_ALL"

    def test_circuit_breaker_maps_to_manage_2_4(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_circuit_breaker_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_nist_rmf_report(days=30)
        assert len(report.controls["MANAGE-2.4"]) == 1

    def test_dct_maps_to_map_1_1(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_dct_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_nist_rmf_report(days=30)
        assert len(report.controls["MAP-1.1"]) == 1
        evidence = report.controls["MAP-1.1"][0]
        assert evidence["tuple_type"] == "DCT"
        assert evidence["delegator"] == "system"
        assert evidence["delegatee"] == "agent-1"

    def test_dctx_maps_to_map_1_1(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_dctx_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_nist_rmf_report(days=30)
        assert len(report.controls["MAP-1.1"]) == 1
        evidence = report.controls["MAP-1.1"][0]
        assert evidence["tuple_type"] == "DCTX"
        assert evidence["delegator"] == "agent-1"

    def test_contract_maps_to_map_1_1(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_contract_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_nist_rmf_report(days=30)
        assert len(report.controls["MAP-1.1"]) == 1

    def test_attest_maps_to_map_2_2(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_attest_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_nist_rmf_report(days=30)
        assert len(report.controls["MAP-2.2"]) == 1
        evidence = report.controls["MAP-2.2"][0]
        assert evidence["tuple_type"] == "ATTEST"
        assert evidence["claim"] == "output validated"
        assert evidence["outcome"] == "PASS"

    def test_signed_maps_to_measure_2_5(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_dct_entry(signed=True)])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_nist_rmf_report(days=30)
        assert len(report.controls["MEASURE-2.5"]) == 1

    def test_unsigned_skips_measure_2_5(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_dct_entry(signed=False)])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_nist_rmf_report(days=30)
        assert len(report.controls["MEASURE-2.5"]) == 0

    def test_cost_governor_maps_to_measure_2_8(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_cost_governor_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_nist_rmf_report(days=30)
        assert len(report.controls["MEASURE-2.8"]) == 1
        evidence = report.controls["MEASURE-2.8"][0]
        assert evidence["agent"] == "claude"
        assert evidence["decision"] == "ALLOW"
        assert evidence["spend"] == 0.05
        assert evidence["budget"] == 10.0

    def test_empty_dir_all_controls_empty(self, tmp_path):
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_nist_rmf_report(days=30)
        for control_items in report.controls.values():
            assert control_items == []

    def test_multiple_entries_accumulate(self, tmp_path):
        _write_governance_file(
            tmp_path, _today_str(),
            [_intent_entry("e1"), _intent_entry("e2"), _circuit_breaker_entry("e3")],
        )
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_nist_rmf_report(days=30)
        assert len(report.controls["GOVERN-1.1"]) == 2
        assert len(report.controls["GOVERN-1.7"]) == 1

    def test_report_to_json_roundtrip(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_intent_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_nist_rmf_report(days=30)
        parsed = json.loads(report.to_json())
        assert parsed["framework"] == "NIST_AI_RMF"
        assert len(parsed["controls"]["GOVERN-1.1"]) == 1

    def test_date_filter_excludes_old(self, tmp_path):
        _write_governance_file(tmp_path, _days_ago_str(60), [_intent_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_nist_rmf_report(days=30)
        assert len(report.controls["GOVERN-1.1"]) == 0

    def test_date_filter_includes_recent(self, tmp_path):
        _write_governance_file(tmp_path, _days_ago_str(15), [_intent_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_nist_rmf_report(days=30)
        assert len(report.controls["GOVERN-1.1"]) == 1


# ---------------------------------------------------------------------------
# TestComplianceMapperEUAIAct
# ---------------------------------------------------------------------------

class TestComplianceMapperEUAIAct:
    def test_all_controls_initialized(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_eu_ai_act_report(days=30)
        assert report.framework == "EU_AI_ACT"
        expected = {"Art.9", "Art.10", "Art.11", "Art.12", "Art.13", "Art.14", "Art.15", "Art.16", "Art.17", "Art.19"}
        assert set(report.controls.keys()) == expected

    def test_circuit_breaker_maps_to_art9(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_circuit_breaker_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_eu_ai_act_report(days=30)
        assert len(report.controls["Art.9"]) == 1
        evidence = report.controls["Art.9"][0]
        assert evidence["tuple_type"] == "CIRCUIT_BREAKER"
        assert evidence["state"] == "OPEN"
        assert evidence["adapter"] == "github"

    def test_killswitch_maps_to_art9(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_killswitch_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_eu_ai_act_report(days=30)
        assert len(report.controls["Art.9"]) == 1
        evidence = report.controls["Art.9"][0]
        assert evidence["tuple_type"] == "KILLSWITCH"

    def test_attest_maps_to_art10(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_attest_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_eu_ai_act_report(days=30)
        assert len(report.controls["Art.10"]) == 1
        evidence = report.controls["Art.10"][0]
        assert evidence["claim"] == "output validated"
        assert evidence["outcome"] == "PASS"

    def test_signed_maps_to_art12(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_dct_entry(signed=True)])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_eu_ai_act_report(days=30)
        assert len(report.controls["Art.12"]) == 1

    def test_unsigned_skips_art12(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_dct_entry(signed=False)])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_eu_ai_act_report(days=30)
        assert len(report.controls["Art.12"]) == 0

    def test_intent_maps_to_art13(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_intent_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_eu_ai_act_report(days=30)
        assert len(report.controls["Art.13"]) == 1
        evidence = report.controls["Art.13"][0]
        assert evidence["agent"] == "claude"
        assert evidence["objective"] == "generate briefing"

    def test_killswitch_maps_to_art14(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_killswitch_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_eu_ai_act_report(days=30)
        assert len(report.controls["Art.14"]) == 1
        evidence = report.controls["Art.14"][0]
        assert evidence["state"] == "HALT_ALL"
        assert evidence["human_initiated"] is True

    def test_killswitch_disengaged_not_human_initiated(self, tmp_path):
        entry = {
            "entry_id": "e_dis",
            "timestamp": "2026-03-23T10:05:00Z",
            "task_id": "t5",
            "intent_id": "i5",
            "signature": "sigdis",
            "tuple_type": "KILLSWITCH",
            "tuple_data": {"state": "DISENGAGED", "adapter": None},
        }
        _write_governance_file(tmp_path, _today_str(), [entry])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_eu_ai_act_report(days=30)
        assert len(report.controls["Art.14"]) == 1
        assert report.controls["Art.14"][0]["human_initiated"] is False

    def test_killswitch_emergency_is_human_initiated(self, tmp_path):
        entry = {
            "entry_id": "e_emerg",
            "timestamp": "2026-03-23T10:06:00Z",
            "task_id": "t6",
            "intent_id": "i6",
            "signature": "sigemerg",
            "tuple_type": "KILLSWITCH",
            "tuple_data": {"state": "EMERGENCY", "adapter": None},
        }
        _write_governance_file(tmp_path, _today_str(), [entry])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_eu_ai_act_report(days=30)
        assert report.controls["Art.14"][0]["human_initiated"] is True

    def test_dctx_maps_to_art17(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_dctx_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_eu_ai_act_report(days=30)
        assert len(report.controls["Art.17"]) == 1
        evidence = report.controls["Art.17"][0]
        assert evidence["delegator"] == "agent-1"
        assert evidence["delegatee"] == "agent-2"
        assert evidence["event"] == "task_delegated"

    def test_non_dctx_skips_art17(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_dct_entry(), _intent_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_eu_ai_act_report(days=30)
        assert len(report.controls["Art.17"]) == 0

    def test_empty_dir_all_controls_empty(self, tmp_path):
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_eu_ai_act_report(days=30)
        for control_items in report.controls.values():
            assert control_items == []

    def test_multiple_entries_accumulate(self, tmp_path):
        _write_governance_file(
            tmp_path, _today_str(),
            [_killswitch_entry("e1"), _killswitch_entry("e2"), _dctx_entry("e3")],
        )
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_eu_ai_act_report(days=30)
        assert len(report.controls["Art.9"]) == 2
        assert len(report.controls["Art.14"]) == 2
        assert len(report.controls["Art.17"]) == 1

    def test_report_to_json_roundtrip(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_killswitch_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_eu_ai_act_report(days=30)
        parsed = json.loads(report.to_json())
        assert parsed["framework"] == "EU_AI_ACT"
        assert len(parsed["controls"]["Art.9"]) == 1
        assert len(parsed["controls"]["Art.14"]) == 1

    def test_date_filter_excludes_old(self, tmp_path):
        _write_governance_file(tmp_path, _days_ago_str(60), [_killswitch_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_eu_ai_act_report(days=30)
        assert len(report.controls["Art.9"]) == 0

    def test_date_filter_includes_recent(self, tmp_path):
        _write_governance_file(tmp_path, _days_ago_str(15), [_killswitch_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_eu_ai_act_report(days=30)
        assert len(report.controls["Art.9"]) == 1

    def test_contract_maps_to_art11(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_contract_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_eu_ai_act_report(days=30)
        assert len(report.controls["Art.11"]) == 1

    def test_killswitch_maps_to_art15(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_killswitch_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_eu_ai_act_report(days=30)
        assert len(report.controls["Art.15"]) >= 1

    def test_dctx_maps_to_art16(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_dctx_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_eu_ai_act_report(days=30)
        assert len(report.controls["Art.16"]) >= 1

    def test_signed_maps_to_art19(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_dct_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_eu_ai_act_report(days=30)
        assert len(report.controls["Art.19"]) >= 1
        assert report.controls["Art.19"][0].get("auto_generated") is True


# ---------------------------------------------------------------------------
# TestComplianceMapperISO27001
# ---------------------------------------------------------------------------


class TestComplianceMapperISO27001:
    def test_iso27001_all_controls_initialized(self, tmp_path):
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_iso27001_report(days=30)
        assert report.framework == "ISO27001"
        assert set(report.controls.keys()) == {"A.5", "A.6", "A.7", "A.8", "A.9", "A.12"}

    def test_iso27001_intent_maps_to_a5(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_intent_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_iso27001_report(days=30)
        assert len(report.controls["A.5"]) == 1
        assert report.controls["A.5"][0]["objective"] == "generate briefing"

    def test_iso27001_dctx_maps_to_a6(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_dctx_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_iso27001_report(days=30)
        assert len(report.controls["A.6"]) == 1
        assert report.controls["A.6"][0]["delegator"] == "agent-1"

    def test_iso27001_dct_maps_to_a7_and_a8_and_a9(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_dct_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_iso27001_report(days=30)
        assert len(report.controls["A.7"]) == 1
        assert len(report.controls["A.8"]) == 1
        assert len(report.controls["A.9"]) == 1
        assert report.controls["A.9"][0]["ops_allowed"] == ["read"]

    def test_iso27001_signed_maps_to_a12(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_dct_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_iso27001_report(days=30)
        assert len(report.controls["A.12"]) >= 1

    def test_iso27001_contract_maps_to_a7_and_a8(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_contract_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_iso27001_report(days=30)
        assert len(report.controls["A.7"]) == 1

    def test_iso27001_attest_maps_to_a8(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_attest_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_iso27001_report(days=30)
        assert len(report.controls["A.8"]) == 1

    def test_iso27001_cli(self, tmp_path):
        rc = main(["--framework", "iso27001", "--dir", str(tmp_path)])
        assert rc == 0

    def test_iso27001_empty_dir(self, tmp_path):
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_iso27001_report(days=30)
        for ctrl in report.controls.values():
            assert ctrl == []

    def test_iso27001_report_to_json_roundtrip(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_dct_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_iso27001_report(days=30)
        parsed = json.loads(report.to_json())
        assert parsed["framework"] == "ISO27001"
        assert len(parsed["controls"]["A.9"]) == 1


# ---------------------------------------------------------------------------
# TestComplianceMapperISO42001
# ---------------------------------------------------------------------------


class TestComplianceMapperISO42001:
    def test_iso42001_all_controls_initialized(self, tmp_path):
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_iso42001_report(days=30)
        assert report.framework == "ISO42001"
        assert set(report.controls.keys()) == {
            "A.2", "A.3", "A.4", "A.5", "A.6",
            "A.7", "A.8", "A.9", "A.10",
        }

    def test_iso42001_intent_maps_to_a2(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_intent_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_iso42001_report(days=30)
        assert len(report.controls["A.2"]) == 1
        assert report.controls["A.2"][0]["objective"] == "generate briefing"

    def test_iso42001_dctx_maps_to_a3_and_a10(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_dctx_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_iso42001_report(days=30)
        assert len(report.controls["A.3"]) == 1
        assert report.controls["A.3"][0]["delegator"] == "agent-1"
        assert len(report.controls["A.10"]) == 1

    def test_iso42001_dct_maps_to_a4_a7_a9(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_dct_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_iso42001_report(days=30)
        assert len(report.controls["A.4"]) == 1
        assert len(report.controls["A.7"]) == 1
        assert len(report.controls["A.9"]) == 1
        assert report.controls["A.9"][0]["ops_allowed"] == ["read"]

    def test_iso42001_attest_maps_to_a4_and_a5(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_attest_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_iso42001_report(days=30)
        assert len(report.controls["A.4"]) == 1
        assert len(report.controls["A.5"]) == 1

    def test_iso42001_contract_maps_to_a6(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_contract_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_iso42001_report(days=30)
        assert len(report.controls["A.6"]) == 1

    def test_iso42001_signed_maps_to_a8(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_dct_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_iso42001_report(days=30)
        assert len(report.controls["A.8"]) >= 1

    def test_iso42001_cli(self, tmp_path):
        rc = main(["--framework", "iso42001", "--dir", str(tmp_path)])
        assert rc == 0

    def test_iso42001_empty_dir(self, tmp_path):
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_iso42001_report(days=30)
        for ctrl in report.controls.values():
            assert ctrl == []

    def test_iso42001_report_to_json_roundtrip(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_dct_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_iso42001_report(days=30)
        parsed = json.loads(report.to_json())
        assert parsed["framework"] == "ISO42001"
        assert len(parsed["controls"]["A.9"]) == 1


# ---------------------------------------------------------------------------
# TestComplianceMapperNISTCSF
# ---------------------------------------------------------------------------


class TestComplianceMapperNISTCSF:
    def test_nist_csf_all_controls_initialized(self, tmp_path):
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_nist_csf_report(days=30)
        assert report.framework == "NIST_CSF"
        assert set(report.controls.keys()) == {"GOVERN", "IDENTIFY", "PROTECT", "DETECT", "RESPOND", "RECOVER"}

    def test_nist_csf_intent_maps_to_govern(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_intent_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_nist_csf_report(days=30)
        assert len(report.controls["GOVERN"]) == 1

    def test_nist_csf_dctx_maps_to_govern(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_dctx_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_nist_csf_report(days=30)
        assert len(report.controls["GOVERN"]) == 1

    def test_nist_csf_dct_maps_to_identify_and_protect(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_dct_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_nist_csf_report(days=30)
        assert len(report.controls["IDENTIFY"]) == 1
        assert len(report.controls["PROTECT"]) == 1

    def test_nist_csf_killswitch_maps_to_protect(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_killswitch_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_nist_csf_report(days=30)
        assert len(report.controls["PROTECT"]) >= 1

    def test_nist_csf_killswitch_emergency_maps_to_respond(self, tmp_path):
        entry = _killswitch_entry()
        entry["tuple_data"]["state"] = "EMERGENCY"
        _write_governance_file(tmp_path, _today_str(), [entry])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_nist_csf_report(days=30)
        assert len(report.controls["RESPOND"]) >= 1

    def test_nist_csf_circuit_breaker_maps_to_detect(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_circuit_breaker_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_nist_csf_report(days=30)
        assert len(report.controls["DETECT"]) >= 1

    def test_nist_csf_circuit_breaker_open_maps_to_respond(self, tmp_path):
        entry = _circuit_breaker_entry()
        entry["tuple_data"]["state"] = "OPEN"
        _write_governance_file(tmp_path, _today_str(), [entry])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_nist_csf_report(days=30)
        assert len(report.controls["RESPOND"]) >= 1

    def test_nist_csf_circuit_breaker_half_open_maps_to_recover(self, tmp_path):
        entry = _circuit_breaker_entry()
        entry["tuple_data"]["state"] = "HALF_OPEN"
        _write_governance_file(tmp_path, _today_str(), [entry])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_nist_csf_report(days=30)
        assert len(report.controls["RECOVER"]) >= 1

    def test_nist_csf_cost_governor_maps_to_recover(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_cost_governor_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_nist_csf_report(days=30)
        assert len(report.controls["RECOVER"]) >= 1

    def test_nist_csf_cli(self, tmp_path):
        rc = main(["--framework", "nist-csf", "--dir", str(tmp_path)])
        assert rc == 0

    def test_nist_csf_empty_dir(self, tmp_path):
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_nist_csf_report(days=30)
        for ctrl in report.controls.values():
            assert ctrl == []

    def test_nist_csf_report_to_json_roundtrip(self, tmp_path):
        _write_governance_file(tmp_path, _today_str(), [_intent_entry(), _killswitch_entry()])
        mapper = ComplianceMapper(governance_dir=tmp_path)
        report = mapper.generate_nist_csf_report(days=30)
        parsed = json.loads(report.to_json())
        assert parsed["framework"] == "NIST_CSF"
        assert len(parsed["controls"]["GOVERN"]) == 1
