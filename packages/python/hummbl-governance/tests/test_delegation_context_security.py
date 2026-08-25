"""Adversarial tests for monotonic delegation-context scope."""

import copy
import pickle
from dataclasses import FrozenInstanceError, asdict
from datetime import datetime, timedelta

import pytest

from hummbl_governance.delegation import (
    Caveat,
    DelegationTokenManager,
    ResourceSelector,
    TokenBinding,
)
from hummbl_governance.delegation_context import (
    DelegationContext,
    DelegationContextManager,
)


def test_child_can_only_narrow_operations_and_resources():
    manager = DelegationContextManager()
    parent = manager.create_trusted_context(
        parent="root-token",
        operations=["read", "write"],
        resources=["docs/*"],
    )

    child = manager.delegate(
        parent.token_id,
        operations=["read"],
        resources=["docs/public/*"],
    )

    assert child.operations == ("read",)
    assert child.resources == ("docs/public/*",)


def test_child_cannot_add_operation():
    manager = DelegationContextManager()
    parent = manager.create_trusted_context(
        parent="root-token",
        operations=["read"],
        resources=["docs/*"],
    )

    with pytest.raises(PermissionError, match="HG_E_CAPABILITY_ESCALATION"):
        manager.delegate(parent.token_id, operations=["read", "shell:execute"])


def test_child_cannot_expand_resource_scope():
    manager = DelegationContextManager()
    parent = manager.create_trusted_context(
        parent="root-token",
        operations=["read"],
        resources=["docs/*"],
    )

    with pytest.raises(PermissionError, match="HG_E_CAPABILITY_ESCALATION"):
        manager.delegate(parent.token_id, resources=["*"])


def test_child_resource_scope_rejects_parent_traversal():
    manager = DelegationContextManager()
    parent = manager.create_trusted_context(
        parent="root-token",
        operations=["read"],
        resources=["docs/*"],
    )

    with pytest.raises(PermissionError, match="HG_E_CAPABILITY_ESCALATION"):
        manager.delegate(parent.token_id, resources=["docs/../secrets/*"])


def test_grandchild_cannot_regain_scope_dropped_by_child():
    manager = DelegationContextManager()
    parent = manager.create_trusted_context(
        parent="root-token",
        operations=["read", "write"],
        resources=["docs/*"],
    )
    child = manager.delegate(
        parent.token_id,
        operations=["read"],
        resources=["docs/public/*"],
    )

    with pytest.raises(PermissionError, match="HG_E_CAPABILITY_ESCALATION"):
        manager.delegate(
            child.token_id,
            operations=["write"],
            resources=["docs/*"],
        )


def test_zero_grant_context_cannot_delegate_capabilities():
    parent = DelegationContext(parent="root-token")

    with pytest.raises(PermissionError, match="HG_E_CAPABILITY_ESCALATION"):
        parent.delegate(operations=["shell:execute"], resources=["*"])


def test_manager_applies_requested_child_scope():
    manager = DelegationContextManager()
    parent = manager.create_trusted_context(
        parent="root-token",
        operations=["read"],
        resources=["docs/*"],
    )

    child = manager.delegate(
        parent.token_id,
        operations=["read"],
        resources=["docs/public/*"],
    )

    assert manager.get_context(child.token_id) is child
    assert child.operations == ("read",)
    assert child.resources == ("docs/public/*",)


def test_context_scope_and_depth_are_immutable_and_serialization_is_defensive():
    manager = DelegationContextManager()
    parent = manager.create_trusted_context(
        parent="trusted-admin",
        operations=["read", "write"],
        resources=["docs/*"],
    )
    child = manager.delegate(
        parent.token_id,
        operations=["read"],
        resources=["docs/public/*"],
    )

    with pytest.raises(FrozenInstanceError):
        child.max_depth = 100
    with pytest.raises(FrozenInstanceError):
        child.operations = ("read", "shell:execute")
    with pytest.raises(AttributeError):
        child.resources.append("*")

    serialized = child.to_dict()
    serialized["operations"].append("shell:execute")
    serialized["resources"].append("*")
    assert child.operations == ("read",)
    assert child.resources == ("docs/public/*",)


def test_token_parent_cannot_seed_an_unauthenticated_root():
    token_manager = DelegationTokenManager(secret=b"trusted-secret")
    token = token_manager.issue(
        issuer="orchestrator",
        subject="worker",
        operations=["read"],
        resources=["public/*"],
        task_id="task-1",
        contract_id="contract-1",
    )

    with pytest.raises(TypeError, match="create_context_from_token"):
        DelegationContext(
            parent=token,
            operations=["shell:execute"],
            resources=["*"],
        )
    with pytest.raises(TypeError, match="create_context_from_token"):
        DelegationContextManager().create_context(parent=token)


def test_authenticated_token_root_derives_and_only_narrows_scope():
    token_manager = DelegationTokenManager(secret=b"trusted-secret")
    token = token_manager.issue(
        issuer="orchestrator",
        subject="worker",
        operations=["read", "summarize"],
        resources=["public/*"],
        task_id="task-1",
        contract_id="contract-1",
    )
    context_manager = DelegationContextManager()
    expected = {
        "expected_issuer": "orchestrator",
        "expected_subject": "worker",
        "expected_task_id": "task-1",
        "expected_contract_id": "contract-1",
    }

    root = context_manager.create_context_from_token(
        token,
        token_manager,
        operations=["read"],
        resources=["public/reports/*"],
        **expected,
    )
    assert root.operations == ("read",)
    assert root.resources == ("public/reports/*",)
    assert root.authority_token_id == token.token_id

    with pytest.raises(PermissionError, match="HG_E_CAPABILITY_ESCALATION"):
        context_manager.create_context_from_token(
            token,
            token_manager,
            operations=["shell:execute"],
            **expected,
        )
    with pytest.raises(PermissionError, match="HG_E_CAPABILITY_ESCALATION"):
        context_manager.create_context_from_token(
            token,
            token_manager,
            resources=["*"],
            **expected,
        )


def test_token_root_rejects_wrong_verifier_and_lossy_resource_conversion():
    issuer_manager = DelegationTokenManager(secret=b"trusted-secret")
    wrong_manager = DelegationTokenManager(secret=b"wrong-secret")
    token = issuer_manager.create_token(
        issuer="orchestrator",
        subject="worker",
        ops_allowed=["database:read"],
        binding=TokenBinding("task-1", "contract-1"),
        resource_selectors=[
            ResourceSelector("database", "prod-*", {"tenant": "trusted"})
        ],
    )
    context_manager = DelegationContextManager()
    expected = {
        "expected_issuer": "orchestrator",
        "expected_subject": "worker",
        "expected_task_id": "task-1",
        "expected_contract_id": "contract-1",
    }

    with pytest.raises(PermissionError, match="HG_E_TOKEN_INVALID"):
        context_manager.create_context_from_token(
            token,
            wrong_manager,
            **expected,
        )
    with pytest.raises(ValueError, match="cannot safely represent"):
        context_manager.create_context_from_token(
            token,
            issuer_manager,
            **expected,
        )


def test_token_authority_marker_cannot_be_forged_through_constructor():
    with pytest.raises(TypeError, match="authority_token_id"):
        DelegationContext(
            parent="restricted-token-id",
            operations=["shell:execute"],
            resources=["*"],
            authority_token_id="restricted-token-id",
        )

    with pytest.raises(TypeError, match="Scoped contexts must be created"):
        DelegationContext(
            parent="untrusted",
            operations=["admin:*"],
            resources=["*"],
        )

    raw = DelegationContext(parent="untrusted")
    assert raw.authority_token_id is None
    assert raw.operations == ()
    assert raw.resources == ()
    assert raw.to_dict()["authority_token_id"] is None
    with pytest.raises(PermissionError, match="HG_E_CAPABILITY_ESCALATION"):
        raw.delegate(operations=["admin:*"], resources=["*"])


def test_trusted_scope_delegation_requires_manager_held_provenance():
    manager = DelegationContextManager()
    root = manager.create_trusted_context(
        parent="trusted-root",
        operations=["read"],
        resources=["docs/*"],
    )

    with pytest.raises(PermissionError, match="must delegate through"):
        root.delegate()

    object.__setattr__(root, "operations", ("admin:*",))
    with pytest.raises(PermissionError, match="scope registry is inconsistent"):
        manager.delegate(root.token_id)


def test_token_backed_context_reauthenticates_expiry_on_every_delegation(
    monkeypatch: pytest.MonkeyPatch,
):
    import hummbl_governance._types as types_module

    token_manager = DelegationTokenManager(secret=b"trusted-secret")
    token = token_manager.issue(
        issuer="orchestrator",
        subject="worker",
        operations=["read"],
        resources=["public/*"],
        task_id="task-1",
        contract_id="contract-1",
    )
    context_manager = DelegationContextManager()
    root = context_manager.create_context_from_token(
        token,
        token_manager,
        expected_issuer="orchestrator",
        expected_subject="worker",
        expected_task_id="task-1",
        expected_contract_id="contract-1",
    )

    class FutureDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime.now(tz) + timedelta(days=1)

    monkeypatch.setattr(types_module, "datetime", FutureDateTime)

    with pytest.raises(PermissionError, match="HG_E_TOKEN_EXPIRED"):
        context_manager.delegate(root.token_id)


def test_token_backed_context_rejects_unrepresentable_caveats():
    token_manager = DelegationTokenManager(secret=b"trusted-secret")
    token = token_manager.create_token(
        issuer="orchestrator",
        subject="worker",
        ops_allowed=["read"],
        binding=TokenBinding("task-1", "contract-1"),
        caveats=[Caveat("approval", "APPROVAL_REQUIRED", {})],
    )

    with pytest.raises(PermissionError, match="cannot enforce token caveats"):
        DelegationContextManager().create_context_from_token(
            token,
            token_manager,
            expected_issuer="orchestrator",
            expected_subject="worker",
            expected_task_id="task-1",
            expected_contract_id="contract-1",
        )


def test_public_context_cannot_serialize_or_reach_signing_secret():
    secret = b"unique-context-signing-secret"
    token_manager = DelegationTokenManager(secret=secret)
    token = token_manager.issue(
        issuer="orchestrator",
        subject="worker",
        operations=["read"],
        resources=["public/*"],
        task_id="task-1",
        contract_id="contract-1",
    )
    root = DelegationContextManager().create_context_from_token(
        token,
        token_manager,
        expected_issuer="orchestrator",
        expected_subject="worker",
        expected_task_id="task-1",
        expected_contract_id="contract-1",
    )

    serialized = asdict(root)
    cloned = copy.deepcopy(root)
    pickled = pickle.dumps(root)

    assert "_authority_manager" not in serialized
    assert "_authority_token" not in serialized
    assert not hasattr(root, "_authority_manager")
    assert not hasattr(root, "_authority_token")
    assert cloned.authority_token_id == token.token_id
    assert secret not in pickled
    with pytest.raises(PermissionError, match="must delegate through"):
        root.delegate()
