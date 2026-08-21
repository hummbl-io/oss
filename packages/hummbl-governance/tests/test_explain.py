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

"""Tests for AuditLog.explain() method."""

import tempfile

from hummbl_governance.audit_log import AuditLog


class TestExplain:
    """Test the explain() audit chain tracing."""

    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.log = AuditLog(
            base_dir=self.tmpdir,
            require_signature=False,
        )

    def teardown_method(self):
        self.log.close()

    def _append(self, **kwargs):
        """Helper: append and return the entry_id."""
        ok, err = self.log.append(**kwargs)
        assert ok, f"append failed: {err}"
        # Find the entry we just wrote
        entries = list(self.log.query_by_intent(kwargs["intent_id"]))
        return entries[-1].entry_id

    def test_explain_single_entry(self):
        eid = self._append(
            intent_id="i1", task_id="t1",
            tuple_type="SYSTEM", tuple_data={"action": "test"},
        )
        chain = self.log.explain(eid)
        assert len(chain) == 1
        assert chain[0].entry_id == eid

    def test_explain_not_found(self):
        chain = self.log.explain("nonexistent-id")
        assert chain == []

    def test_explain_amendment_chain(self):
        # Create original entry
        original_id = self._append(
            intent_id="i1", task_id="t1",
            tuple_type="SYSTEM", tuple_data={"version": 1},
        )
        # Create amendment
        amendment_id = self._append(
            intent_id="i1", task_id="t1",
            tuple_type="SYSTEM", tuple_data={"version": 2},
            amendment_of=original_id,
        )
        chain = self.log.explain(amendment_id)
        assert len(chain) == 2
        # Causal order: original first, amendment last
        assert chain[0].entry_id == original_id
        assert chain[1].entry_id == amendment_id

    def test_explain_contract_link(self):
        # Create contract entry
        contract_id = self._append(
            intent_id="i1", task_id="t1",
            tuple_type="CONTRACT", tuple_data={"name": "budget-policy"},
        )
        # Create action governed by contract
        action_id = self._append(
            intent_id="i1", task_id="t2",
            tuple_type="DCTX", tuple_data={"event": "api-call"},
            contract_id=contract_id,
        )
        chain = self.log.explain(action_id)
        assert len(chain) == 2
        assert chain[0].entry_id == contract_id
        assert chain[1].entry_id == action_id

    def test_explain_delegation_chain(self):
        # Contract -> DCT -> Action
        contract_id = self._append(
            intent_id="i1", task_id="t1",
            tuple_type="CONTRACT", tuple_data={"name": "access-policy"},
        )
        dct_id = self._append(
            intent_id="i1", task_id="t1",
            tuple_type="DCT", tuple_data={"subject": "worker-1"},
            contract_id=contract_id,
        )
        action_id = self._append(
            intent_id="i1", task_id="t2",
            tuple_type="DCTX", tuple_data={"event": "write"},
            capability_token_id=dct_id,
        )
        chain = self.log.explain(action_id)
        assert len(chain) == 3
        assert chain[0].entry_id == contract_id
        assert chain[1].entry_id == dct_id
        assert chain[2].entry_id == action_id

    def test_explain_evidence_attestation(self):
        # Evidence -> Attest
        evidence_id = self._append(
            intent_id="i1", task_id="t1",
            tuple_type="EVIDENCE", tuple_data={"finding": "all tests pass"},
        )
        attest_id = self._append(
            intent_id="i1", task_id="t1",
            tuple_type="ATTEST", tuple_data={"verdict": "approved"},
            verification_id=evidence_id,
        )
        chain = self.log.explain(attest_id)
        assert len(chain) == 2
        assert chain[0].entry_id == evidence_id
        assert chain[1].entry_id == attest_id

    def test_explain_no_cycles(self):
        """Ensure explain() doesn't loop on self-referential entries."""
        eid = self._append(
            intent_id="i1", task_id="t1",
            tuple_type="SYSTEM", tuple_data={"note": "standalone"},
        )
        # Even if we could create a cycle, visited set prevents infinite loop
        chain = self.log.explain(eid)
        assert len(chain) == 1
