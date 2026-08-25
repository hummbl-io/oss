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

"""Tests for ContractNetManager."""

from hummbl_governance.contract_net import (
    Bid,
    ContractNetManager,
    ContractPhase,
)


class TestAnnouncement:
    def test_announce_returns_id(self):
        mgr = ContractNetManager()
        ann_id = mgr.announce("orch", "task-1")
        assert ann_id
        assert mgr.get_phase(ann_id) == ContractPhase.BIDDING

    def test_announce_with_requirements(self):
        mgr = ContractNetManager()
        ann_id = mgr.announce("orch", "task-1", requirements={"skill": "ocr"})
        ann = mgr.get_announcement(ann_id)
        assert ann.requirements == {"skill": "ocr"}

    def test_list_active(self):
        mgr = ContractNetManager()
        mgr.announce("orch", "task-1")
        mgr.announce("orch", "task-2")
        assert len(mgr.list_active()) == 2


class TestBidding:
    def test_submit_bid(self):
        mgr = ContractNetManager()
        ann_id = mgr.announce("orch", "task-1")
        ok = mgr.submit_bid(ann_id, Bid(bidder="w1", cost=1.0))
        assert ok

    def test_submit_bid_unknown_announcement(self):
        mgr = ContractNetManager()
        ok = mgr.submit_bid("nonexistent", Bid(bidder="w1"))
        assert not ok

    def test_multiple_bids(self):
        mgr = ContractNetManager()
        ann_id = mgr.announce("orch", "task-1")
        mgr.submit_bid(ann_id, Bid(bidder="w1", cost=1.0))
        mgr.submit_bid(ann_id, Bid(bidder="w2", cost=0.5))
        mgr.submit_bid(ann_id, Bid(bidder="w3", cost=2.0))
        ann = mgr.get_announcement(ann_id)
        assert len(ann.bids) == 3

    def test_bid_after_evaluation_rejected(self):
        mgr = ContractNetManager()
        ann_id = mgr.announce("orch", "task-1")
        mgr.submit_bid(ann_id, Bid(bidder="w1", cost=1.0))
        mgr.evaluate(ann_id)
        ok = mgr.submit_bid(ann_id, Bid(bidder="late", cost=0.1))
        assert not ok


class TestEvaluation:
    def test_lowest_cost(self):
        mgr = ContractNetManager(default_strategy="lowest_cost")
        ann_id = mgr.announce("orch", "task-1")
        mgr.submit_bid(ann_id, Bid(bidder="w1", cost=5.0))
        mgr.submit_bid(ann_id, Bid(bidder="w2", cost=1.0))
        mgr.submit_bid(ann_id, Bid(bidder="w3", cost=3.0))
        winner = mgr.evaluate(ann_id)
        assert winner.bidder == "w2"
        assert mgr.get_phase(ann_id) == ContractPhase.AWARDED

    def test_highest_capability(self):
        mgr = ContractNetManager()
        ann_id = mgr.announce("orch", "task-1")
        mgr.submit_bid(ann_id, Bid(bidder="w1", capability=0.5))
        mgr.submit_bid(ann_id, Bid(bidder="w2", capability=0.9))
        winner = mgr.evaluate(ann_id, strategy="highest_capability")
        assert winner.bidder == "w2"

    def test_best_ratio(self):
        mgr = ContractNetManager()
        ann_id = mgr.announce("orch", "task-1")
        mgr.submit_bid(ann_id, Bid(bidder="w1", cost=10.0, capability=0.5))  # ratio=20
        mgr.submit_bid(ann_id, Bid(bidder="w2", cost=2.0, capability=0.8))   # ratio=2.5
        winner = mgr.evaluate(ann_id, strategy="best_ratio")
        assert winner.bidder == "w2"

    def test_no_bids_returns_none(self):
        mgr = ContractNetManager()
        ann_id = mgr.announce("orch", "task-1")
        winner = mgr.evaluate(ann_id)
        assert winner is None
        assert mgr.get_phase(ann_id) == ContractPhase.FAILED

    def test_unknown_strategy_raises(self):
        mgr = ContractNetManager()
        ann_id = mgr.announce("orch", "task-1")
        mgr.submit_bid(ann_id, Bid(bidder="w1"))
        try:
            mgr.evaluate(ann_id, strategy="nonexistent")
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

    def test_unknown_announcement_raises(self):
        mgr = ContractNetManager()
        try:
            mgr.evaluate("nonexistent")
            assert False, "Should have raised KeyError"
        except KeyError:
            pass


class TestLifecycle:
    def test_complete(self):
        mgr = ContractNetManager()
        ann_id = mgr.announce("orch", "task-1")
        mgr.submit_bid(ann_id, Bid(bidder="w1"))
        mgr.evaluate(ann_id)
        mgr.complete(ann_id)
        assert mgr.get_phase(ann_id) == ContractPhase.COMPLETE

    def test_fail(self):
        mgr = ContractNetManager()
        ann_id = mgr.announce("orch", "task-1")
        mgr.fail(ann_id)
        assert mgr.get_phase(ann_id) == ContractPhase.FAILED

    def test_summary(self):
        mgr = ContractNetManager()
        mgr.announce("orch", "task-1")
        mgr.announce("orch", "task-2")
        summary = mgr.summary()
        assert summary.get("bidding", 0) == 2


class TestBidProperties:
    def test_cost_capability_ratio(self):
        bid = Bid(bidder="w1", cost=10.0, capability=0.5)
        assert bid.cost_capability_ratio == 20.0

    def test_zero_capability_ratio(self):
        bid = Bid(bidder="w1", cost=10.0, capability=0.0)
        assert bid.cost_capability_ratio == float("inf")

    def test_expired_announcement(self):
        mgr = ContractNetManager()
        ann_id = mgr.announce("orch", "task-1", deadline_seconds=0.0)
        ok = mgr.submit_bid(ann_id, Bid(bidder="w1"))
        assert not ok
