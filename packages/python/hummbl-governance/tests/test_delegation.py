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

"""Tests for hummbl_governance.delegation."""



from hummbl_governance.delegation import (
    Caveat,
    DelegationToken,
    DelegationTokenManager,
    ResourceSelector,
    TokenBinding,
    E_BINDING_MISMATCH,
    E_DCT_VIOLATION,
    E_TOKEN_EXPIRED,
    E_TOKEN_INVALID,
)


class TestDelegationTokenCreation:
    """Test token creation and signing."""

    def test_create_token(self):
        mgr = DelegationTokenManager(secret=b"test-secret")
        token = mgr.create_token(
            issuer="orchestrator",
            subject="worker",
            ops_allowed=["read", "write"],
            binding=TokenBinding(task_id="task-1", contract_id="contract-1"),
        )
        assert token.issuer == "orchestrator"
        assert token.subject == "worker"
        assert "read" in token.ops_allowed
        assert token.signature != ""

    def test_token_has_expiry(self):
        mgr = DelegationTokenManager(secret=b"test-secret")
        token = mgr.create_token(
            issuer="orch", subject="worker",
            ops_allowed=["read"],
            binding=TokenBinding("t1", "c1"),
            expiry_minutes=60,
        )
        assert token.expiry is not None

    def test_token_no_expiry(self):
        mgr = DelegationTokenManager(secret=b"test-secret")
        token = mgr.create_token(
            issuer="orch", subject="worker",
            ops_allowed=["read"],
            binding=TokenBinding("t1", "c1"),
            expiry_minutes=None,
        )
        assert token.expiry is None
        assert not token.is_expired()

    def test_token_with_resources(self):
        mgr = DelegationTokenManager(secret=b"test-secret")
        token = mgr.create_token(
            issuer="orch", subject="worker",
            ops_allowed=["read"],
            binding=TokenBinding("t1", "c1"),
            resource_selectors=[ResourceSelector("database", "db-1")],
        )
        assert len(token.resource_selectors) == 1
        assert token.resource_selectors[0].resource_type == "database"

    def test_token_with_caveats(self):
        mgr = DelegationTokenManager(secret=b"test-secret")
        token = mgr.create_token(
            issuer="orch", subject="worker",
            ops_allowed=["read"],
            binding=TokenBinding("t1", "c1"),
            caveats=[Caveat("c1", "TIME_BOUND", {"max_hours": 2})],
        )
        assert len(token.caveats) == 1


class TestDelegationTokenValidation:
    """Test token validation."""

    def test_valid_token(self):
        mgr = DelegationTokenManager(secret=b"test-secret")
        token = mgr.create_token(
            issuer="orch", subject="worker",
            ops_allowed=["read"],
            binding=TokenBinding("t1", "c1"),
        )
        valid, error = mgr.validate_token(token)
        assert valid is True
        assert error is None

    def test_invalid_signature(self):
        mgr = DelegationTokenManager(secret=b"test-secret")
        token = mgr.create_token(
            issuer="orch", subject="worker",
            ops_allowed=["read"],
            binding=TokenBinding("t1", "c1"),
        )
        # Create tampered token
        tampered = DelegationToken(
            token_id=token.token_id,
            issuer="evil",  # Changed
            subject=token.subject,
            ops_allowed=token.ops_allowed,
            binding=token.binding,
            signature=token.signature,  # Old signature
        )
        valid, error = mgr.validate_token(tampered)
        assert valid is False
        assert error == E_TOKEN_INVALID

    def test_expired_token(self):
        mgr = DelegationTokenManager(secret=b"test-secret")
        token = mgr.create_token(
            issuer="orch", subject="worker",
            ops_allowed=["read"],
            binding=TokenBinding("t1", "c1"),
            expiry_minutes=-1,  # Already expired
        )
        valid, error = mgr.validate_token(token)
        assert valid is False
        assert error == E_TOKEN_EXPIRED

    def test_binding_validation(self):
        mgr = DelegationTokenManager(secret=b"test-secret")
        token = mgr.create_token(
            issuer="orch", subject="worker",
            ops_allowed=["read"],
            binding=TokenBinding("task-1", "contract-1"),
        )
        valid, error = mgr.validate_token(
            token,
            expected_task_id="task-1",
            expected_contract_id="contract-1",
            expected_subject="worker",
        )
        assert valid is True

    def test_binding_mismatch(self):
        mgr = DelegationTokenManager(secret=b"test-secret")
        token = mgr.create_token(
            issuer="orch", subject="worker",
            ops_allowed=["read"],
            binding=TokenBinding("task-1", "contract-1"),
        )
        valid, error = mgr.validate_token(
            token, expected_task_id="wrong-task",
        )
        assert valid is False
        assert error == E_BINDING_MISMATCH

    def test_different_secret_fails(self):
        mgr1 = DelegationTokenManager(secret=b"secret-1")
        mgr2 = DelegationTokenManager(secret=b"secret-2")
        token = mgr1.create_token(
            issuer="orch", subject="worker",
            ops_allowed=["read"],
            binding=TokenBinding("t1", "c1"),
        )
        valid, error = mgr2.validate_token(token)
        assert valid is False
        assert error == E_TOKEN_INVALID


class TestLeastPrivilege:
    """Test least privilege enforcement."""

    def test_allowed_op(self):
        mgr = DelegationTokenManager(secret=b"test-secret")
        token = mgr.create_token(
            issuer="orch", subject="worker",
            ops_allowed=["read", "write"],
            binding=TokenBinding("t1", "c1"),
        )
        allowed, error = mgr.check_least_privilege(token, "read")
        assert allowed is True

    def test_denied_op(self):
        mgr = DelegationTokenManager(secret=b"test-secret")
        token = mgr.create_token(
            issuer="orch", subject="worker",
            ops_allowed=["read"],
            binding=TokenBinding("t1", "c1"),
        )
        allowed, error = mgr.check_least_privilege(token, "write")
        assert allowed is False
        assert error == E_DCT_VIOLATION

    def test_denied_tools_override(self):
        mgr = DelegationTokenManager(secret=b"test-secret")
        token = mgr.create_token(
            issuer="orch", subject="worker",
            ops_allowed=["read", "delete"],
            binding=TokenBinding("t1", "c1"),
        )
        allowed, error = mgr.check_least_privilege(
            token, "delete", denied_tools=["delete"],
        )
        assert allowed is False
        assert error == E_DCT_VIOLATION

    def test_allowed_tools_constraint(self):
        mgr = DelegationTokenManager(secret=b"test-secret")
        token = mgr.create_token(
            issuer="orch", subject="worker",
            ops_allowed=["read", "write"],
            binding=TokenBinding("t1", "c1"),
        )
        allowed, error = mgr.check_least_privilege(
            token, "write", allowed_tools=["read"],
        )
        assert allowed is False

    def test_forged_token_cannot_pass_least_privilege_check(self):
        mgr = DelegationTokenManager(secret=b"test-secret")
        token = mgr.create_token(
            issuer="orch",
            subject="worker",
            ops_allowed=["read"],
            binding=TokenBinding("t1", "c1"),
        )
        forged = DelegationToken(
            token_id=token.token_id,
            issuer=token.issuer,
            subject=token.subject,
            ops_allowed=("shell:execute",),
            binding=token.binding,
            signature=token.signature,
        )

        allowed, error = mgr.check_least_privilege(forged, "shell:execute")

        assert allowed is False
        assert error == E_TOKEN_INVALID

    def test_dynamic_requested_operation_cannot_masquerade_as_allowed(self):
        class Masquerade(str):
            def __hash__(self):
                return hash("read")

            def __eq__(self, other):
                return other == "read"

        mgr = DelegationTokenManager(secret=b"test-secret")
        token = mgr.create_token(
            issuer="orch",
            subject="worker",
            ops_allowed=["read"],
            binding=TokenBinding("t1", "c1"),
        )

        allowed, error = mgr.check_least_privilege(
            token,
            Masquerade("shell:execute"),
        )

        assert allowed is False
        assert error == E_DCT_VIOLATION


def test_dynamic_expected_binding_values_fail_closed():
    class EqualToEverything(str):
        def __eq__(self, other):
            return True

        def __ne__(self, other):
            return False

    mgr = DelegationTokenManager(secret=b"test-secret")
    token = mgr.create_token(
        issuer="other-issuer",
        subject="other-subject",
        ops_allowed=["read"],
        binding=TokenBinding("other-task", "other-contract"),
    )
    dynamic = EqualToEverything("trusted")

    valid, error = mgr.validate_token(
        token,
        expected_issuer=dynamic,
        expected_subject=dynamic,
        expected_task_id=dynamic,
        expected_contract_id=dynamic,
    )

    assert valid is False
    assert error == E_BINDING_MISMATCH


class TestTokenSerialization:
    """Test token round-trip serialization."""

    def test_to_dict_round_trip(self):
        mgr = DelegationTokenManager(secret=b"test-secret")
        token = mgr.create_token(
            issuer="orch", subject="worker",
            ops_allowed=["read"],
            binding=TokenBinding("t1", "c1"),
            resource_selectors=[ResourceSelector("api", "endpoint-1")],
            caveats=[Caveat("cav1", "RATE_LIMIT", {"max_per_hour": 100})],
        )
        d = token.to_dict()
        assert d["issuer"] == "orch"
        assert len(d["resource_selectors"]) == 1
        assert len(d["caveats"]) == 1
        assert d["binding"]["task_id"] == "t1"
