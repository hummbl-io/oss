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

"""Tests for hummbl_governance.capability_fence."""

import threading
from dataclasses import replace

import pytest

from hummbl_governance.capability_fence import (
    CapabilityAuditEntry,
    CapabilityDenied,
    CapabilityFence,
)
from hummbl_governance.delegation import (
    Caveat,
    DelegationTokenManager,
    ResourceSelector,
    TokenBinding,
)


class TestCapabilityDenied:
    """Test CapabilityDenied exception."""

    def test_exception_attributes(self):
        exc = CapabilityDenied("file:write", frozenset(["api:read"]), frozenset(["file:write"]))
        assert exc.capability == "file:write"
        assert "api:read" in exc.allowed
        assert "file:write" in exc.denied

    def test_exception_message(self):
        exc = CapabilityDenied("shell:execute", frozenset(), frozenset(["shell:execute"]))
        assert "shell:execute" in str(exc)

    def test_exception_is_exception(self):
        assert issubclass(CapabilityDenied, Exception)


class TestCapabilityFenceAllowDeny:
    """Test allow/deny resolution logic."""

    def test_allowed_capability_passes(self):
        fence = CapabilityFence(allowed=["api:read", "bus:write"])
        assert fence.check("api:read") is True

    def test_denied_capability_raises(self):
        fence = CapabilityFence(denied=["file:write"])
        try:
            fence.check("file:write")
            assert False, "Should have raised CapabilityDenied"
        except CapabilityDenied as e:
            assert e.capability == "file:write"

    def test_not_in_allowed_raises(self):
        fence = CapabilityFence(allowed=["api:read"])
        try:
            fence.check("file:write")
            assert False, "Should have raised CapabilityDenied"
        except CapabilityDenied:
            pass

    def test_denied_takes_precedence_over_allowed(self):
        fence = CapabilityFence(allowed=["api:read", "file:write"], denied=["file:write"])
        try:
            fence.check("file:write")
            assert False, "Should have raised CapabilityDenied"
        except CapabilityDenied:
            pass

    def test_no_restrictions_allows_all(self):
        fence = CapabilityFence()
        assert fence.check("anything:goes") is True

    def test_empty_allowed_allows_all(self):
        fence = CapabilityFence(allowed=[])
        assert fence.check("anything:goes") is True

    def test_multiple_allowed(self):
        fence = CapabilityFence(allowed=["a:b", "c:d", "e:f"])
        assert fence.check("a:b") is True
        assert fence.check("c:d") is True
        assert fence.check("e:f") is True

    def test_multiple_denied(self):
        fence = CapabilityFence(denied=["a:b", "c:d"])
        try:
            fence.check("a:b")
            assert False
        except CapabilityDenied:
            pass

    def test_dynamic_capability_strings_are_rejected(self):
        class Masquerade(str):
            def __hash__(self):
                return hash("api:read")

            def __eq__(self, other):
                return other == "api:read"

        fence = CapabilityFence(allowed=["api:read"])

        with pytest.raises(TypeError, match="exact string"):
            fence.check(Masquerade("shell:execute"))
        with pytest.raises(TypeError, match="allowed"):
            CapabilityFence(allowed=[Masquerade("shell:execute")])
        try:
            fence.check("c:d")
            assert False
        except CapabilityDenied:
            pass


class TestCapabilityFenceProperties:
    """Test fence property accessors."""

    def test_allowed_property(self):
        fence = CapabilityFence(allowed=["api:read"])
        assert fence.allowed == frozenset(["api:read"])

    def test_denied_property(self):
        fence = CapabilityFence(denied=["file:write"])
        assert fence.denied == frozenset(["file:write"])

    def test_defaults_are_empty(self):
        fence = CapabilityFence()
        assert fence.allowed == frozenset()
        assert fence.denied == frozenset()


class TestCapabilityFenceGuard:
    """Test guard wrapper."""

    def test_guard_executes_on_allowed(self):
        fence = CapabilityFence(allowed=["compute:run"])
        result = fence.guard(lambda x: x * 2, "compute:run", 5)
        assert result == 10

    def test_guard_raises_on_denied(self):
        fence = CapabilityFence(denied=["compute:run"])
        try:
            fence.guard(lambda x: x * 2, "compute:run", 5)
            assert False, "Should have raised CapabilityDenied"
        except CapabilityDenied:
            pass

    def test_guard_passes_kwargs(self):
        fence = CapabilityFence()

        def add(a, b=0):
            return a + b

        result = fence.guard(add, "math:add", 3, b=7)
        assert result == 10

    def test_guard_does_not_call_fn_on_deny(self):
        called = []
        fence = CapabilityFence(denied=["x:y"])

        def side_effect():
            called.append(True)

        try:
            fence.guard(side_effect, "x:y")
        except CapabilityDenied:
            pass
        assert called == []


class TestCapabilityFenceFromToken:
    """Test from_delegation_token factory."""

    def test_creates_fence_from_token(self):
        mgr = DelegationTokenManager(secret=b"test-secret")
        token = mgr.create_token(
            issuer="orchestrator",
            subject="worker",
            ops_allowed=["api:read", "bus:write"],
            binding=TokenBinding(task_id="t1", contract_id="c1"),
        )
        fence = CapabilityFence.from_delegation_token(
            token,
            mgr,
            expected_issuer="orchestrator",
            expected_subject="worker",
            expected_task_id="t1",
            expected_contract_id="c1",
        )
        assert fence.check("api:read") is True
        assert fence.check("bus:write") is True
        try:
            fence.check("file:write")
            assert False
        except CapabilityDenied:
            pass

    def test_from_token_with_denied(self):
        mgr = DelegationTokenManager(secret=b"test-secret")
        token = mgr.create_token(
            issuer="orchestrator",
            subject="worker",
            ops_allowed=["api:read", "bus:write"],
            binding=TokenBinding(task_id="t1", contract_id="c1"),
        )
        fence = CapabilityFence.from_delegation_token(
            token,
            mgr,
            expected_issuer="orchestrator",
            expected_subject="worker",
            expected_task_id="t1",
            expected_contract_id="c1",
            denied=["bus:write"],
        )
        try:
            fence.check("bus:write")
            assert False
        except CapabilityDenied:
            pass

    def test_from_token_with_audit_log(self):
        mgr = DelegationTokenManager(secret=b"test-secret")
        token = mgr.create_token(
            issuer="o", subject="w",
            ops_allowed=["api:read"],
            binding=TokenBinding(task_id="t1", contract_id="c1"),
        )
        log: list[CapabilityAuditEntry] = []
        fence = CapabilityFence.from_delegation_token(
            token,
            mgr,
            expected_issuer="o",
            expected_subject="w",
            expected_task_id="t1",
            expected_contract_id="c1",
            audit_log=log,
        )
        fence.check("api:read")
        assert len(log) == 1

    def test_zero_grant_token_is_deny_all(self):
        mgr = DelegationTokenManager(secret=b"test-secret")
        token = mgr.create_token(
            issuer="o",
            subject="w",
            ops_allowed=[],
            binding=TokenBinding(task_id="t1", contract_id="c1"),
        )
        fence = CapabilityFence.from_delegation_token(
            token,
            mgr,
            expected_issuer="o",
            expected_subject="w",
            expected_task_id="t1",
            expected_contract_id="c1",
        )

        with pytest.raises(CapabilityDenied, match="not in allowed set"):
            fence.check("shell:execute")

    def test_forged_token_is_rejected_before_construction(self):
        mgr = DelegationTokenManager(secret=b"test-secret")
        token = mgr.create_token(
            issuer="o",
            subject="w",
            ops_allowed=["api:read"],
            binding=TokenBinding(task_id="t1", contract_id="c1"),
        )
        forged = replace(token, ops_allowed=("shell:execute",))

        with pytest.raises(ValueError, match="HG_E_TOKEN_INVALID"):
            CapabilityFence.from_delegation_token(
                forged,
                mgr,
                expected_issuer="o",
                expected_subject="w",
                expected_task_id="t1",
                expected_contract_id="c1",
            )

    def test_expired_token_is_rejected_before_construction(self):
        mgr = DelegationTokenManager(secret=b"test-secret")
        token = mgr.create_token(
            issuer="o",
            subject="w",
            ops_allowed=["api:read"],
            binding=TokenBinding(task_id="t1", contract_id="c1"),
            expiry_minutes=-1,
        )

        with pytest.raises(ValueError, match="HG_E_TOKEN_EXPIRED"):
            CapabilityFence.from_delegation_token(
                token,
                mgr,
                expected_issuer="o",
                expected_subject="w",
                expected_task_id="t1",
                expected_contract_id="c1",
            )

    @pytest.mark.parametrize(
        ("expected_issuer", "expected_subject", "expected_task", "expected_contract"),
        [
            ("wrong", "w", "t1", "c1"),
            ("o", "wrong", "t1", "c1"),
            ("o", "w", "wrong", "c1"),
            ("o", "w", "t1", "wrong"),
        ],
    )
    def test_expected_identity_and_binding_are_mandatory(
        self,
        expected_issuer,
        expected_subject,
        expected_task,
        expected_contract,
    ):
        mgr = DelegationTokenManager(secret=b"test-secret")
        token = mgr.create_token(
            issuer="o",
            subject="w",
            ops_allowed=["api:read"],
            binding=TokenBinding(task_id="t1", contract_id="c1"),
        )

        with pytest.raises(ValueError, match="HG_E_BINDING_MISMATCH"):
            CapabilityFence.from_delegation_token(
                token,
                mgr,
                expected_issuer=expected_issuer,
                expected_subject=expected_subject,
                expected_task_id=expected_task,
                expected_contract_id=expected_contract,
            )

    def test_empty_expected_identity_is_rejected(self):
        mgr = DelegationTokenManager(secret=b"test-secret")
        token = mgr.create_token(
            issuer="o",
            subject="w",
            ops_allowed=["api:read"],
            binding=TokenBinding(task_id="t1", contract_id="c1"),
        )

        with pytest.raises(ValueError, match="expected_subject"):
            CapabilityFence.from_delegation_token(
                token,
                mgr,
                expected_issuer="o",
                expected_subject="",
                expected_task_id="t1",
                expected_contract_id="c1",
            )

    def test_dynamic_expected_binding_strings_are_rejected(self):
        class EqualToEverything(str):
            def __eq__(self, other):
                return True

            def __ne__(self, other):
                return False

        mgr = DelegationTokenManager(secret=b"test-secret")
        token = mgr.create_token(
            issuer="other-issuer",
            subject="other-subject",
            ops_allowed=["api:read"],
            binding=TokenBinding(task_id="other-task", contract_id="other-contract"),
        )
        dynamic = EqualToEverything("trusted")

        with pytest.raises(ValueError, match="non-empty strings"):
            CapabilityFence.from_delegation_token(
                token,
                mgr,
                expected_issuer=dynamic,
                expected_subject=dynamic,
                expected_task_id=dynamic,
                expected_contract_id=dynamic,
            )

    def test_resource_selectors_and_constraints_are_enforced(self):
        mgr = DelegationTokenManager(secret=b"test-secret")
        token = mgr.create_token(
            issuer="o",
            subject="w",
            ops_allowed=["database:read"],
            binding=TokenBinding(task_id="t1", contract_id="c1"),
            resource_selectors=[
                ResourceSelector(
                    resource_type="database",
                    resource_id="prod-*",
                    constraints={"tenant": "t1"},
                )
            ],
        )
        fence = CapabilityFence.from_delegation_token(
            token,
            mgr,
            expected_issuer="o",
            expected_subject="w",
            expected_task_id="t1",
            expected_contract_id="c1",
        )

        assert fence.check(
            "database:read",
            resource_type="database",
            resource_id="prod-users",
            context={"tenant": "t1"},
        )
        with pytest.raises(CapabilityDenied, match="outside token scope"):
            fence.check(
                "database:read",
                resource_type="database",
                resource_id="dev-users",
                context={"tenant": "t1"},
            )
        with pytest.raises(CapabilityDenied, match="outside token scope"):
            fence.check(
                "database:read",
                resource_type="database",
                resource_id="prod-users",
                context={"tenant": "other"},
            )
        with pytest.raises(CapabilityDenied, match="resource_type and resource_id"):
            fence.check("database:read")

    def test_caveats_require_and_use_a_fail_closed_validator(self):
        mgr = DelegationTokenManager(secret=b"test-secret")
        token = mgr.create_token(
            issuer="o",
            subject="w",
            ops_allowed=["shell:execute"],
            binding=TokenBinding(task_id="t1", contract_id="c1"),
            caveats=[Caveat("approval", "APPROVAL_REQUIRED", {})],
        )
        expected = {
            "expected_issuer": "o",
            "expected_subject": "w",
            "expected_task_id": "t1",
            "expected_contract_id": "c1",
        }

        with pytest.raises(ValueError, match="require a caveat_validator"):
            CapabilityFence.from_delegation_token(token, mgr, **expected)

        fence = CapabilityFence.from_delegation_token(
            token,
            mgr,
            caveat_validator=lambda caveat, context: (
                caveat.type == "APPROVAL_REQUIRED" and context.get("approved") is True
            ),
            **expected,
        )
        with pytest.raises(CapabilityDenied, match="not satisfied"):
            fence.check("shell:execute", context={"approved": False})
        assert fence.check("shell:execute", context={"approved": True})

        non_boolean_fence = CapabilityFence.from_delegation_token(
            token,
            mgr,
            caveat_validator=lambda caveat, context: "approved",
            **expected,
        )
        with pytest.raises(CapabilityDenied, match="not satisfied"):
            non_boolean_fence.check("shell:execute")

    def test_caveat_validator_exception_denies(self):
        mgr = DelegationTokenManager(secret=b"test-secret")
        token = mgr.create_token(
            issuer="o",
            subject="w",
            ops_allowed=["shell:execute"],
            binding=TokenBinding(task_id="t1", contract_id="c1"),
            caveats=[Caveat("approval", "APPROVAL_REQUIRED", {})],
        )

        def broken_validator(caveat, context):
            raise RuntimeError("validator unavailable")

        fence = CapabilityFence.from_delegation_token(
            token,
            mgr,
            expected_issuer="o",
            expected_subject="w",
            expected_task_id="t1",
            expected_contract_id="c1",
            caveat_validator=broken_validator,
        )
        with pytest.raises(CapabilityDenied, match="evaluation failed"):
            fence.check("shell:execute")

    def test_caveat_context_rejects_dynamic_equality_and_snapshots_plain_values(self):
        class EqualToGranted:
            def __eq__(self, other):
                return other == "granted"

        mgr = DelegationTokenManager(secret=b"test-secret")
        token = mgr.create_token(
            issuer="o",
            subject="w",
            ops_allowed=["shell:execute"],
            binding=TokenBinding(task_id="t1", contract_id="c1"),
            caveats=[Caveat("approval", "APPROVAL_REQUIRED", {})],
        )
        seen_contexts = []

        def approval_validator(caveat, context):
            seen_contexts.append(context)
            return context["approval"] == "granted"

        fence = CapabilityFence.from_delegation_token(
            token,
            mgr,
            expected_issuer="o",
            expected_subject="w",
            expected_task_id="t1",
            expected_contract_id="c1",
            caveat_validator=approval_validator,
        )

        with pytest.raises(CapabilityDenied, match="safe JSON values"):
            fence.check(
                "shell:execute",
                context={"approval": EqualToGranted()},
            )
        assert seen_contexts == []

        plain_context = {"approval": "granted", "evidence": ["reviewed"]}
        assert fence.check("shell:execute", context=plain_context)
        assert seen_contexts == [plain_context]
        assert seen_contexts[0] is not plain_context
        assert seen_contexts[0]["evidence"] is not plain_context["evidence"]

    def test_reentrant_caveat_validator_does_not_deadlock_audit_lock(self):
        mgr = DelegationTokenManager(secret=b"test-secret")
        token = mgr.create_token(
            issuer="o",
            subject="w",
            ops_allowed=["shell:execute"],
            binding=TokenBinding(task_id="t1", contract_id="c1"),
            caveats=[Caveat("approval", "APPROVAL_REQUIRED", {})],
        )
        audit_log = []
        state = {"reentered": False}
        fence: CapabilityFence

        def reentrant_validator(caveat, context):
            if not state["reentered"]:
                state["reentered"] = True
                assert fence.check(
                    "shell:execute",
                    context={"approval": "granted"},
                )
            return context["approval"] == "granted"

        fence = CapabilityFence.from_delegation_token(
            token,
            mgr,
            expected_issuer="o",
            expected_subject="w",
            expected_task_id="t1",
            expected_contract_id="c1",
            caveat_validator=reentrant_validator,
            audit_log=audit_log,
        )
        result = {}

        def run_check():
            result["allowed"] = fence.check(
                "shell:execute",
                context={"approval": "granted"},
            )

        thread = threading.Thread(target=run_check, daemon=True)
        thread.start()
        thread.join(1.0)

        assert not thread.is_alive()
        assert result == {"allowed": True}
        assert [entry.decision for entry in audit_log] == ["allow", "allow"]

    def test_fence_enforces_verified_snapshot_after_external_mutation(self):
        mgr = DelegationTokenManager(secret=b"test-secret")
        constraints = {"tenant": "t1"}
        token = mgr.create_token(
            issuer="o",
            subject="w",
            ops_allowed=["database:read"],
            binding=TokenBinding(task_id="t1", contract_id="c1"),
            resource_selectors=[
                ResourceSelector("database", "prod-*", constraints=constraints)
            ],
        )
        fence = CapabilityFence.from_delegation_token(
            token,
            mgr,
            expected_issuer="o",
            expected_subject="w",
            expected_task_id="t1",
            expected_contract_id="c1",
        )
        constraints["tenant"] = "attacker"

        with pytest.raises(CapabilityDenied, match="outside token scope"):
            fence.check(
                "database:read",
                resource_type="database",
                resource_id="prod-users",
                context={"tenant": "attacker"},
            )
        assert fence.check(
            "database:read",
            resource_type="database",
            resource_id="prod-users",
            context={"tenant": "t1"},
        )

    def test_constraint_comparison_rejects_custom_equality(self):
        class AlwaysEqual:
            def __eq__(self, other):
                return True

        mgr = DelegationTokenManager(secret=b"test-secret")
        token = mgr.create_token(
            issuer="o",
            subject="w",
            ops_allowed=["database:read"],
            binding=TokenBinding(task_id="t1", contract_id="c1"),
            resource_selectors=[
                ResourceSelector(
                    resource_type="database",
                    resource_id="prod-*",
                    constraints={"tenant": "trusted"},
                )
            ],
        )
        fence = CapabilityFence.from_delegation_token(
            token,
            mgr,
            expected_issuer="o",
            expected_subject="w",
            expected_task_id="t1",
            expected_contract_id="c1",
        )

        with pytest.raises(CapabilityDenied, match="safe JSON values"):
            fence.check(
                "database:read",
                resource_type="database",
                resource_id="prod-users",
                context={"tenant": AlwaysEqual()},
            )

    def test_dynamic_signed_constraint_container_is_rejected(self):
        class Shifty(dict):
            pass

        mgr = DelegationTokenManager(secret=b"test-secret")
        with pytest.raises(TypeError, match="unsupported type Shifty"):
            mgr.create_token(
                issuer="o",
                subject="w",
                ops_allowed=["database:read"],
                binding=TokenBinding(task_id="t1", contract_id="c1"),
                resource_selectors=[
                    ResourceSelector(
                        resource_type="database",
                        resource_id="prod-*",
                        constraints=Shifty(tenant="trusted"),
                    )
                ],
            )

    def test_nested_constraint_snapshot_is_detached_and_type_strict(self):
        mgr = DelegationTokenManager(secret=b"test-secret")
        constraints = {"policy": {"version": 1, "enabled": True}}
        token = mgr.create_token(
            issuer="o",
            subject="w",
            ops_allowed=["database:read"],
            binding=TokenBinding(task_id="t1", contract_id="c1"),
            resource_selectors=[
                ResourceSelector("database", "prod-*", constraints=constraints)
            ],
        )
        fence = CapabilityFence.from_delegation_token(
            token,
            mgr,
            expected_issuer="o",
            expected_subject="w",
            expected_task_id="t1",
            expected_contract_id="c1",
        )
        constraints["policy"]["version"] = 2

        assert fence.check(
            "database:read",
            resource_type="database",
            resource_id="prod-users",
            context={"policy": {"version": 1, "enabled": True}},
        )
        with pytest.raises(CapabilityDenied, match="outside token scope"):
            fence.check(
                "database:read",
                resource_type="database",
                resource_id="prod-users",
                context={"policy": {"version": True, "enabled": True}},
            )


class TestAuditLogging:
    """Test audit logging of capability checks."""

    def test_allow_logged(self):
        log: list[CapabilityAuditEntry] = []
        fence = CapabilityFence(allowed=["api:read"], audit_log=log)
        fence.check("api:read")
        assert len(log) == 1
        assert log[0].decision == "allow"
        assert log[0].capability == "api:read"

    def test_deny_logged(self):
        log: list[CapabilityAuditEntry] = []
        fence = CapabilityFence(denied=["file:write"], audit_log=log)
        try:
            fence.check("file:write")
        except CapabilityDenied:
            pass
        assert len(log) == 1
        assert log[0].decision == "deny"

    def test_timestamp_present(self):
        log: list[CapabilityAuditEntry] = []
        fence = CapabilityFence(audit_log=log)
        fence.check("x:y")
        assert log[0].timestamp.endswith("Z")

    def test_no_audit_log_by_default(self):
        # Should not raise even without audit_log
        fence = CapabilityFence(allowed=["x:y"])
        fence.check("x:y")

    def test_multiple_checks_logged(self):
        log: list[CapabilityAuditEntry] = []
        fence = CapabilityFence(audit_log=log)
        fence.check("a:b")
        fence.check("c:d")
        assert len(log) == 2


class TestThreadSafety:
    """Test thread safety of CapabilityFence."""

    def test_concurrent_checks(self):
        log: list[CapabilityAuditEntry] = []
        fence = CapabilityFence(allowed=["api:read"], audit_log=log)
        errors: list[Exception] = []

        def worker():
            try:
                for _ in range(50):
                    fence.check("api:read")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == []
        assert len(log) == 200
