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

"""Tests for hummbl_governance.dsar_handler (P55 DSARHandler)."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from hummbl_governance.dsar_handler import DSARHandler

@pytest.fixture
def store_dir(tmp_path):
    return tmp_path

@pytest.fixture
def mock_gate_store(store_dir):
    gate_file = store_dir / "gates.jsonl"
    with open(gate_file, "w") as f:
        f.write('{"gate_id": "g1", "data_subject_id": "subj-1", "status": "approved"}\n')
        f.write('{"gate_id": "g2", "data_subject_id": "subj-2", "status": "denied"}\n')
    return gate_file

@pytest.fixture
def mock_contestation_store(store_dir):
    c_file = store_dir / "contestations.jsonl"
    with open(c_file, "w") as f:
        f.write('{"contestation_id": "c1", "data_subject_id": "subj-1"}\n')
    return c_file

@pytest.fixture
def handler(store_dir, mock_gate_store, mock_contestation_store):
    store_file = store_dir / "dsars.jsonl"
    return DSARHandler(
        storage_path=store_file,
        gate_store_path=mock_gate_store,
        contestation_store_path=mock_contestation_store,
    )

def test_receive_creates_received_record(handler):
    record = handler.receive("subj-1", "ref-1")
    assert record.status == "received"
    assert record.data_subject_id == "subj-1"
    assert record.requester_ref == "ref-1"

def test_receive_sets_30_day_deadline(handler):
    record = handler.receive("subj-1", "ref")
    sub = datetime.strptime(record.timestamp_received, "%Y-%m-%dT%H:%M:%SZ")
    dead = datetime.strptime(record.deadline_iso, "%Y-%m-%dT%H:%M:%SZ")
    assert (dead - sub).days == 30

def test_compile_response_writes_json_file(handler, store_dir):
    record = handler.receive("subj-1", "ref")
    out_file = store_dir / "response.json"
    
    updated = handler.compile_response(record.dsar_id, out_file)
    assert updated.status == "in_review"
    assert out_file.exists()
    
    with open(out_file) as f:
        data = json.load(f)
    assert data["dsar_id"] == record.dsar_id

def test_compile_response_searches_gate_store(handler, store_dir):
    record = handler.receive("subj-1", "ref")
    out_file = store_dir / "resp.json"
    handler.compile_response(record.dsar_id, out_file)
    
    with open(out_file) as f:
        data = json.load(f)
        
    records = {r["source"]: r["entries"] for r in data["records"]}
    assert len(records["gate_receipts"]) == 1
    assert records["gate_receipts"][0]["gate_id"] == "g1"

def test_compile_response_searches_contestation_store(handler, store_dir):
    record = handler.receive("subj-1", "ref")
    out_file = store_dir / "resp.json"
    handler.compile_response(record.dsar_id, out_file)
    
    with open(out_file) as f:
        data = json.load(f)
        
    records = {r["source"]: r["entries"] for r in data["records"]}
    assert len(records["contestation_records"]) == 1
    assert records["contestation_records"][0]["contestation_id"] == "c1"

def test_compile_response_art15_structure(handler, store_dir):
    record = handler.receive("subj-1", "ref")
    out_file = store_dir / "resp.json"
    handler.compile_response(record.dsar_id, out_file)
    
    with open(out_file) as f:
        data = json.load(f)
        
    assert "art15_disclosure" in data
    assert "confirmation_of_processing" in data["art15_disclosure"]
    assert "purposes" in data["art15_disclosure"]
    assert "categories" in data["art15_disclosure"]
    assert "recipients" in data["art15_disclosure"]

def test_extend_adds_60_days(handler):
    record = handler.receive("s", "r")
    updated = handler.extend(record.dsar_id, "Complex request")
    
    sub = datetime.strptime(updated.timestamp_received, "%Y-%m-%dT%H:%M:%SZ")
    dead = datetime.strptime(updated.deadline_iso, "%Y-%m-%dT%H:%M:%SZ")
    assert (dead - sub).days == 90
    assert updated.extended is True

def test_extend_only_once_allowed(handler):
    record = handler.receive("s", "r")
    handler.extend(record.dsar_id, "Reason 1")
    with pytest.raises(ValueError, match="already extended"):
        handler.extend(record.dsar_id, "Reason 2")

def test_close_complete_sets_status(handler):
    record = handler.receive("s", "r")
    updated = handler.close(record.dsar_id, "complete")
    assert updated.status == "complete"
    assert updated.timestamp_completed is not None

def test_close_refused_sets_status(handler):
    record = handler.receive("s", "r")
    updated = handler.close(record.dsar_id, "refused")
    assert updated.status == "refused"

def test_list_overdue_returns_past_deadline(handler):
    record = handler.receive("s", "r")
    record.deadline_iso = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    overdue = handler.list_overdue()
    assert len(overdue) == 1

def test_list_overdue_excludes_complete(handler):
    record = handler.receive("s", "r")
    record.deadline_iso = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    handler.close(record.dsar_id, "complete")
    
    assert len(handler.list_overdue()) == 0

def test_generate_ai_act_notice_contains_dsar_id(handler):
    record = handler.receive("s", "r")
    notice = handler.generate_ai_act_notice(record.dsar_id)
    assert record.dsar_id in notice

def test_generate_ai_act_notice_mentions_ai_act(handler):
    record = handler.receive("s", "r")
    notice = handler.generate_ai_act_notice(record.dsar_id)
    assert "AI Act" in notice

def test_boundary_note_in_compiled_response(handler, store_dir):
    record = handler.receive("s", "r")
    out_file = store_dir / "resp.json"
    handler.compile_response(record.dsar_id, out_file)
    
    with open(out_file) as f:
        data = json.load(f)
    assert "boundary_note" in data
    assert "HUMMBL is not a supervisory authority" in data["boundary_note"]

def test_get_unknown_dsar_raises(handler):
    with pytest.raises(KeyError):
        handler.get("unknown")

def test_store_survives_reload(handler, store_dir):
    record = handler.receive("s", "r")
    handler.close(record.dsar_id, "complete")
    
    store_file = store_dir / "dsars.jsonl"
    handler2 = DSARHandler(storage_path=store_file)
    reloaded = handler2.get(record.dsar_id)
    assert reloaded.status == "complete"
