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

from hummbl_governance.eal import evaluate_validation


def test_eal_validates_code_quality_success():
    contract = {
        "contract_id": "c1",
        "contract_hash": "h1",
        "action_space": ["act1"],
    }
    receipt = {
        "receipt_id": "r1",
        "contract_id": "c1",
        "contract_hash": "h1",
        "signature": {"status": "valid"},
        "evidence": [{}],
        "receipt_hash": "rh1",
        "actions": [{"action_id": "act1"}],
        "min_arbiter_score": 80.0,
        "actual_arbiter_score": 85.0,
    }
    report = evaluate_validation(contract, receipt)
    assert report["classification"] == "VALID"
    assert "E_OK_VALID" in report["reason_codes"]


def test_eal_validates_code_quality_failure():
    contract = {
        "contract_id": "c1",
        "contract_hash": "h1",
        "action_space": ["act1"],
    }
    receipt = {
        "receipt_id": "r1",
        "contract_id": "c1",
        "contract_hash": "h1",
        "signature": {"status": "valid"},
        "evidence": [{}],
        "receipt_hash": "rh1",
        "actions": [{"action_id": "act1"}],
        "min_arbiter_score": 80.0,
        "actual_arbiter_score": 75.0,
    }
    report = evaluate_validation(contract, receipt)
    assert report["classification"] == "INVALID"
    assert "E_CODE_QUALITY_FAIL" in report["reason_codes"]


def test_eal_handles_missing_quality_metadata():
    contract = {
        "contract_id": "c1",
        "contract_hash": "h1",
        "action_space": ["act1"],
    }
    receipt = {
        "receipt_id": "r1",
        "contract_id": "c1",
        "contract_hash": "h1",
        "signature": {"status": "valid"},
        "evidence": [{}],
        "receipt_hash": "rh1",
        "actions": [{"action_id": "act1"}],
    }
    report = evaluate_validation(contract, receipt)
    assert report["classification"] == "VALID"


def test_eal_rejects_non_numeric_quality_metadata():
    contract = {
        "contract_id": "c1",
        "contract_hash": "h1",
        "action_space": ["act1"],
    }
    receipt = {
        "receipt_id": "r1",
        "contract_id": "c1",
        "contract_hash": "h1",
        "signature": {"status": "valid"},
        "evidence": [{}],
        "receipt_hash": "rh1",
        "actions": [{"action_id": "act1"}],
        "min_arbiter_score": "80.0",
        "actual_arbiter_score": 85.0,
    }
    report = evaluate_validation(contract, receipt)
    assert report["classification"] == "INDETERMINATE"
    assert report["primary_reason_code"] == "E_INPUT_MALFORMED"
