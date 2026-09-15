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

"""Tests for hummbl_governance.contestation_handler (P54 ContestationHandler)."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from hummbl_governance.contestation_handler import ContestationHandler

class MockCapabilityFence:
    def __init__(self):
        self.restricted = []
        self.unrestricted = []

    def restrict(self, agent_id: str, denied_capabilities: list[str]):
        self.restricted.append((agent_id, denied_capabilities))

    def unrestrict(self, agent_id: str):
        self.unrestricted.append(agent_id)


@pytest.fixture
def tmp_store(tmp_path):
    return tmp_path / "contestations.jsonl"


@pytest.fixture
def fence():
    return MockCapabilityFence()


@pytest.fixture
def handler(tmp_store, fence):
    return ContestationHandler(storage_path=tmp_store, capability_fence=fence)


def test_submit_creates_open_record(handler):
    record = handler.submit("gate-123", "subj-1", "I disagree")
    assert record.status == "open"
    assert record.original_gate_id == "gate-123"
    assert record.data_subject_id == "subj-1"


def test_submit_sets_30_day_deadline(handler):
    record = handler.submit("gate-123", "subj-1", "I disagree")
    submitted = datetime.strptime(record.timestamp_submitted, "%Y-%m-%dT%H:%M:%SZ")
    deadline = datetime.strptime(record.deadline_iso, "%Y-%m-%dT%H:%M:%SZ")
    delta = deadline - submitted
    assert delta.days == 30


def test_submit_records_grounds(handler):
    record = handler.submit("gate-123", "subj-1", "This is wrong")
    assert record.grounds == "This is wrong"


def test_begin_review_transitions_to_under_review(handler):
    record = handler.submit("gate-1", "subj-1", "grounds")
    updated = handler.begin_review(record.contestation_id, "reviewer-1")
    assert updated.status == "under_review"
    assert updated.resolver_id == "reviewer-1"


def test_resolve_upheld_sets_outcome(handler):
    record = handler.submit("gate-1", "subj-1", "grounds")
    updated = handler.resolve(record.contestation_id, "upheld", "resolver-1")
    assert updated.status == "resolved"
    assert updated.outcome == "upheld"


def test_resolve_overturned_sets_outcome(handler, fence):
    record = handler.submit("gate-1", "subj-1", "grounds")
    assert fence.restricted == [("gate-1", ["execute_decision"])]
    
    updated = handler.resolve(record.contestation_id, "overturned", "resolver-1")
    assert updated.status == "resolved"
    assert updated.outcome == "overturned"
    assert "gate-1" in fence.unrestricted


def test_resolve_withdrawn_sets_outcome(handler):
    record = handler.submit("gate-1", "subj-1", "grounds")
    updated = handler.resolve(record.contestation_id, "withdrawn", "resolver-1")
    assert updated.status == "withdrawn"
    assert updated.outcome == "withdrawn"


def test_resolve_sets_timestamp_resolved(handler):
    record = handler.submit("gate-1", "subj-1", "grounds")
    updated = handler.resolve(record.contestation_id, "upheld", "resolver-1")
    assert updated.timestamp_resolved is not None


def test_resolve_sets_resolver_id(handler):
    record = handler.submit("gate-1", "subj-1", "grounds")
    updated = handler.resolve(record.contestation_id, "upheld", "resolver-99")
    assert updated.resolver_id == "resolver-99"


def test_list_open_returns_open_and_under_review(handler):
    r1 = handler.submit("gate-1", "subj-1", "g1")
    r2 = handler.submit("gate-2", "subj-2", "g2")
    handler.begin_review(r2.contestation_id, "rev-1")
    
    opens = handler.list_open()
    assert len(opens) == 2


def test_list_open_excludes_resolved(handler):
    r1 = handler.submit("gate-1", "subj-1", "g1")
    handler.resolve(r1.contestation_id, "upheld", "rev")
    assert len(handler.list_open()) == 0


def test_list_overdue_returns_past_deadline_unresolved(handler):
    r1 = handler.submit("gate-1", "subj-1", "g1")
    # Manually backdate deadline to force overdue
    r1.deadline_iso = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    overdue = handler.list_overdue()
    assert len(overdue) == 1
    assert overdue[0].contestation_id == r1.contestation_id


def test_list_overdue_excludes_resolved(handler):
    r1 = handler.submit("gate-1", "subj-1", "g1")
    r1.deadline_iso = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    handler.resolve(r1.contestation_id, "upheld", "rev")
    assert len(handler.list_overdue()) == 0


def test_list_by_subject_filters_correctly(handler):
    handler.submit("g1", "subj-A", "1")
    handler.submit("g2", "subj-A", "2")
    handler.submit("g3", "subj-B", "3")
    assert len(handler.list_by_subject("subj-A")) == 2
    assert len(handler.list_by_subject("subj-B")) == 1


def test_get_returns_record(handler):
    r1 = handler.submit("g1", "s1", "g")
    assert handler.get(r1.contestation_id).contestation_id == r1.contestation_id


def test_get_unknown_raises_key_error(handler):
    with pytest.raises(KeyError):
        handler.get("unknown")


def test_record_persisted_to_jsonl(handler, tmp_store):
    handler.submit("g1", "s1", "g")
    lines = tmp_store.read_text().strip().split("\n")
    assert len(lines) == 1
    assert "g1" in lines[0]


def test_record_survives_reload(handler, tmp_store):
    r1 = handler.submit("g1", "s1", "g")
    handler.resolve(r1.contestation_id, "upheld", "rev")
    
    handler2 = ContestationHandler(storage_path=tmp_store)
    reloaded = handler2.get(r1.contestation_id)
    assert reloaded.status == "resolved"


def test_hmac_present(handler):
    r1 = handler.submit("g1", "s1", "g")
    assert r1.receipt_hmac is not None
    assert len(r1.receipt_hmac) == 64


def test_invalid_outcome_raises_value_error(handler):
    r1 = handler.submit("g1", "s1", "g")
    with pytest.raises(ValueError):
        handler.resolve(r1.contestation_id, "bogus", "rev")


def test_submit_without_capability_fence_still_works(tmp_store):
    handler_no_fence = ContestationHandler(storage_path=tmp_store, capability_fence=None)
    r1 = handler_no_fence.submit("g1", "s1", "g")
    assert r1.status == "open"
    handler_no_fence.resolve(r1.contestation_id, "overturned", "rev")
