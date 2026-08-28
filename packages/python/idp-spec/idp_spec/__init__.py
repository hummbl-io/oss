"""HUMMBL Intelligent Delegation Profile (IDP) — Reference Implementation.

IDP is a deterministic, cryptography-backed specification for safe, verifiable
delegation in multi-agent systems. This package provides the reference
Python implementation of the six-tuple IDP framework:

    DCTX -> CONTRACT -> EVIDENCE -> ATTEST -> DCT -> GOVERNANCE_BUS

Usage::

    from idp_spec import DelegationCapabilityToken, DelegationContext, GovernanceBus

    # 1. Create a capability token
    binding = TokenBinding(task_id="task-001", contract_id="contract-001")
    dct = create_token(
        issuer="scheduler",
        subject="briefing_service",
        ops_allowed=["generate", "write_briefing"],
        binding=binding,
        secret=b"my-secure-key",
    )

    # 2. Validate token
    valid, _ = validate_token(dct, secret=b"my-secure-key", binding=binding)
    assert valid

    # 3. Create context & log to governance bus
    dctx = DelegationContext(
        intent_id="intent-001",
        task_id="task-001",
        delegator_id="scheduler",
        delegatee_id="briefing_service",
        contract_id="contract-001",
    )
    bus = GovernanceBus(base_dir=Path("./_state/governance"))
    bus.append(
        intent_id=dctx.intent_id,
        task_id=dctx.task_id,
        tuple_type="DCT",
        tuple_data={"token_id": dct.token_id},
        contract_id=dctx.contract_id,
        capability_token_id=dct.token_id,
    )

Feature flag: ``ENABLE_IDP=true`` activates full enforcement.
Default: disabled (backward compatible pass-through).
"""

__version__ = "0.1.0"

# Re-export core types
from idp_spec.delegation_token import (
    Caveat,
    DelegationCapabilityToken,
    DelegationTokenManager,
    ResourceSelector,
    TokenBinding,
    create_token,
    validate_token,
)
from idp_spec.delegation_context import (
    DelegationBudget,
    DelegationContext,
    DelegationContextManager,
)
from idp_spec.governance_bus import (
    GovernanceBus,
    GovernanceEntry,
)

__all__ = [
    # delegation_token
    "Caveat",
    "DelegationCapabilityToken",
    "DelegationTokenManager",
    "ResourceSelector",
    "TokenBinding",
    "create_token",
    "validate_token",
    # delegation_context
    "DelegationBudget",
    "DelegationContext",
    "DelegationContextManager",
    # governance_bus
    "GovernanceBus",
    "GovernanceEntry",
]
