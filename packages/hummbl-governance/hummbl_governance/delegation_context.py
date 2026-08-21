"""Delegation context with immutable depth and scope attenuation.

Raw contexts track depth only and do not establish authority. Token-backed
roots must be created through ``create_context_from_token`` so their scope is
derived from an authenticated delegation token.
"""

from __future__ import annotations

import threading
import time
import uuid
from collections.abc import Sequence
from dataclasses import dataclass, field
from fnmatch import fnmatchcase
from typing import Any

from hummbl_governance._types import DelegationToken
from hummbl_governance.delegation import DelegationTokenManager
from hummbl_governance.errors import HummblError

__all__ = [
    "DelegationContext",
    "DelegationContextManager",
]


@dataclass(frozen=True)
class DelegationContext:
    """Immutable context for a delegation chain with scope attenuation."""

    parent: Any
    max_depth: int = 3
    depth: int = 0
    token_id: str = ""
    operations: tuple[str, ...] = field(default_factory=tuple)
    resources: tuple[str, ...] = field(default_factory=tuple)
    authority_token_id: str | None = field(default=None, init=False)
    created_at: str = field(
        default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    )

    def __post_init__(self) -> None:
        if isinstance(self.parent, DelegationToken):
            raise TypeError(
                "Token-backed roots must be created with "
                "DelegationContextManager.create_context_from_token()"
            )
        if type(self.max_depth) is not int or self.max_depth < 0:
            raise ValueError("max_depth must be a non-negative integer")
        if type(self.depth) is not int or self.depth < 0 or self.depth > self.max_depth:
            raise ValueError("depth must be between zero and max_depth")
        operations = _normalized_scope(self.operations, "operations")
        resources = _normalized_scope(self.resources, "resources")
        if operations or resources:
            raise TypeError(
                "Scoped contexts must be created with "
                "DelegationContextManager.create_trusted_context() or "
                "create_context_from_token()"
            )
        object.__setattr__(self, "operations", operations)
        object.__setattr__(self, "resources", resources)
        if not self.token_id:
            object.__setattr__(self, "token_id", f"dctx-{uuid.uuid4()}")

    def delegate(
        self,
        operations: Sequence[str] | None = None,
        resources: Sequence[str] | None = None,
    ) -> DelegationContext:
        """Create a child whose scope is no broader than this context."""
        if self.authority_token_id is not None or self.operations or self.resources:
            raise PermissionError(
                "Scoped contexts must delegate through "
                "DelegationContextManager.delegate()"
            )
        return _delegate_context(self, operations, resources)

    def depth_exceeded(self, context: DelegationContext) -> bool:
        """Check whether a context exceeds this context's depth ceiling."""
        return context.depth > self.max_depth

    def can_delegate(self) -> bool:
        """Return whether another delegation step is permitted."""
        return self.depth + 1 <= self.max_depth

    def to_dict(self) -> dict[str, Any]:
        """Return a defensive serialization of the immutable context."""
        return {
            "parent": str(self.parent),
            "max_depth": self.max_depth,
            "depth": self.depth,
            "token_id": self.token_id,
            "operations": list(self.operations),
            "resources": list(self.resources),
            "authority_token_id": self.authority_token_id,
            "created_at": self.created_at,
        }


class DelegationContextManager:
    """Track immutable delegation contexts and authenticate token roots."""

    def __init__(self, default_max_depth: int = 3) -> None:
        self._contexts: dict[str, DelegationContext] = {}
        self._authorities: dict[
            str,
            tuple[DelegationToken, DelegationTokenManager],
        ] = {}
        self._trusted_scopes: dict[
            str,
            tuple[tuple[str, ...], tuple[str, ...]],
        ] = {}
        self._default_max_depth = default_max_depth
        self._lock = threading.Lock()

    def create_context(
        self,
        parent: Any,
        max_depth: int | None = None,
    ) -> DelegationContext:
        """Create an unscoped context for backward-compatible depth tracking."""
        ctx = DelegationContext(
            parent=parent,
            max_depth=self._default_max_depth if max_depth is None else max_depth,
        )
        self._register(ctx)
        return ctx

    def create_trusted_context(
        self,
        parent: Any,
        *,
        operations: Sequence[str],
        resources: Sequence[str],
        max_depth: int | None = None,
    ) -> DelegationContext:
        """Create an explicit application-trusted administrative root."""
        if isinstance(parent, DelegationToken):
            raise TypeError("Delegation tokens require create_context_from_token()")
        trusted_operations = _normalized_scope(operations, "operations")
        trusted_resources = _normalized_scope(resources, "resources")
        ctx = DelegationContext(
            parent=parent,
            max_depth=self._default_max_depth if max_depth is None else max_depth,
        )
        _bind_scope(ctx, trusted_operations, trusted_resources)
        self._register(
            ctx,
            trusted_scope=(trusted_operations, trusted_resources),
        )
        return ctx

    def create_context_from_token(
        self,
        token: DelegationToken,
        token_manager: DelegationTokenManager,
        *,
        expected_issuer: str,
        expected_subject: str,
        expected_task_id: str,
        expected_contract_id: str,
        operations: Sequence[str] | None = None,
        resources: Sequence[str] | None = None,
        max_depth: int | None = None,
    ) -> DelegationContext:
        """Create a root whose scope is authenticated and bounded by a token."""
        if type(token_manager) is not DelegationTokenManager:
            raise TypeError("token_manager must be an exact DelegationTokenManager")
        expected_values = (
            expected_issuer,
            expected_subject,
            expected_task_id,
            expected_contract_id,
        )
        if not all(type(value) is str and value for value in expected_values):
            raise ValueError("token expectations must be non-empty strings")

        snapshot, error = token_manager.authenticate_token(
            token,
            expected_issuer=expected_issuer,
            expected_subject=expected_subject,
            expected_task_id=expected_task_id,
            expected_contract_id=expected_contract_id,
        )
        if snapshot is None:
            raise PermissionError(f"Delegation token rejected: {error}")
        if snapshot.caveats:
            raise PermissionError(
                "DelegationContext cannot enforce token caveats; use CapabilityFence"
            )

        parent_operations = tuple(snapshot.ops_allowed)
        parent_resources = _token_resource_patterns(snapshot)
        child_operations = (
            parent_operations
            if operations is None
            else _normalized_scope(operations, "operations")
        )
        child_resources = (
            parent_resources
            if resources is None
            else _normalized_scope(resources, "resources")
        )
        _require_operation_subset(parent_operations, child_operations)
        _require_resource_subset(parent_resources, child_resources)
        ctx = DelegationContext(
            parent=snapshot.token_id,
            max_depth=self._default_max_depth if max_depth is None else max_depth,
        )
        _bind_scope(ctx, child_operations, child_resources)
        _bind_authority_marker(ctx, snapshot.token_id)
        self._register(ctx, authority=(snapshot, token_manager))
        return ctx

    def _register(
        self,
        ctx: DelegationContext,
        *,
        authority: tuple[DelegationToken, DelegationTokenManager] | None = None,
        trusted_scope: tuple[tuple[str, ...], tuple[str, ...]] | None = None,
    ) -> None:
        if authority is not None and trusted_scope is not None:
            raise ValueError("Context cannot have token and trusted-root provenance")
        with self._lock:
            self._contexts[ctx.token_id] = ctx
            if authority is not None:
                self._authorities[ctx.token_id] = authority
            if trusted_scope is not None:
                self._trusted_scopes[ctx.token_id] = trusted_scope

    def get_context(self, token_id: str) -> DelegationContext | None:
        with self._lock:
            return self._contexts.get(token_id)

    def delegate(
        self,
        token_id: str,
        operations: Sequence[str] | None = None,
        resources: Sequence[str] | None = None,
    ) -> DelegationContext:
        """Delegate from an existing immutable context."""
        with self._lock:
            ctx = self._contexts.get(token_id)
            if ctx is None:
                raise KeyError(f"Unknown context: {token_id}")
            authority = self._authorities.get(token_id)
            trusted_scope = self._trusted_scopes.get(token_id)
            if ctx.authority_token_id is not None:
                if authority is None:
                    raise PermissionError(
                        "Token-backed context authority is unavailable"
                    )
                snapshot = _authenticate_context_authority(ctx, *authority)
            elif authority is not None:
                raise PermissionError("Context authority registry is inconsistent")
            elif trusted_scope is not None:
                if trusted_scope != (ctx.operations, ctx.resources):
                    raise PermissionError("Trusted context scope registry is inconsistent")
                snapshot = None
            elif ctx.operations or ctx.resources:
                raise PermissionError("Scoped context provenance is unavailable")
            else:
                snapshot = None
            child = _delegate_context(ctx, operations, resources)
            if snapshot is not None:
                _bind_authority_marker(child, snapshot.token_id)
                self._authorities[child.token_id] = (snapshot, authority[1])
            elif trusted_scope is not None:
                self._trusted_scopes[child.token_id] = (
                    child.operations,
                    child.resources,
                )
            self._contexts[child.token_id] = child
        return child


def _require_operation_subset(parent: Sequence[str], child: Sequence[str]) -> None:
    """Reject a child operation grant that exceeds its parent context."""
    extra = sorted(set(child) - set(parent))
    if extra:
        raise PermissionError(
            f"{HummblError.CAPABILITY_ESCALATION.value}: "
            f"child operations exceed parent scope: {extra}"
        )


def _require_resource_subset(parent: Sequence[str], child: Sequence[str]) -> None:
    """Reject child resource selectors not contained by a parent selector."""
    extra = [
        resource
        for resource in child
        if not any(_resource_pattern_contains(scope, resource) for scope in parent)
    ]
    if extra:
        raise PermissionError(
            f"{HummblError.CAPABILITY_ESCALATION.value}: "
            f"child resources exceed parent scope: {sorted(extra)}"
        )


def _resource_pattern_contains(parent: str, child: str) -> bool:
    """Conservatively determine whether a child resource stays in parent scope."""
    if ".." in child.replace("\\", "/").split("/"):
        return False
    if parent == child or parent in {"*", "**"}:
        return True
    child_has_wildcards = any(char in child for char in "*?[")
    if not child_has_wildcards:
        return fnmatchcase(child, parent)
    if parent.endswith("*") and not any(char in parent[:-1] for char in "*?["):
        return child.startswith(parent[:-1])
    return False


def _normalized_scope(values: Sequence[str], name: str) -> tuple[str, ...]:
    """Return immutable, exact-string scope values."""
    if isinstance(values, (str, bytes)):
        raise TypeError(f"{name} must be a sequence of strings")
    normalized = tuple(values)
    if not all(type(value) is str and value for value in normalized):
        raise TypeError(f"{name} must contain non-empty exact strings")
    return normalized


def _token_resource_patterns(token: DelegationToken) -> tuple[str, ...]:
    """Convert only losslessly representable token selectors to context scope."""
    if not token.resource_selectors:
        return ("*",)
    patterns: list[str] = []
    for selector in token.resource_selectors:
        if selector.resource_type != "*" or selector.constraints:
            raise ValueError(
                "DelegationContext cannot safely represent typed or constrained "
                "resource selectors; enforce this token with CapabilityFence"
            )
        patterns.append(selector.resource_id)
    return tuple(patterns)


def _delegate_context(
    context: DelegationContext,
    operations: Sequence[str] | None,
    resources: Sequence[str] | None,
) -> DelegationContext:
    """Create an attenuated child without assigning authority provenance."""
    new_depth = context.depth + 1
    if new_depth > context.max_depth:
        raise PermissionError(
            f"Delegation chain depth {new_depth} exceeds max_depth {context.max_depth}"
        )
    child_operations = (
        context.operations
        if operations is None
        else _normalized_scope(operations, "operations")
    )
    child_resources = (
        context.resources
        if resources is None
        else _normalized_scope(resources, "resources")
    )
    _require_operation_subset(context.operations, child_operations)
    _require_resource_subset(context.resources, child_resources)
    child = DelegationContext(
        parent=context.token_id,
        max_depth=context.max_depth,
        depth=new_depth,
    )
    _bind_scope(child, child_operations, child_resources)
    return child


def _authenticate_context_authority(
    context: DelegationContext,
    token: DelegationToken,
    manager: DelegationTokenManager,
) -> DelegationToken:
    """Reauthenticate manager-held authority and its current context scope."""
    if type(token) is not DelegationToken or type(manager) is not DelegationTokenManager:
        raise PermissionError("Delegation context authority registry is invalid")
    if token.binding is None:
        raise PermissionError("authenticated authority requires a token binding")
    snapshot, error = manager.authenticate_token(
        token,
        expected_issuer=token.issuer,
        expected_subject=token.subject,
        expected_task_id=token.binding.task_id,
        expected_contract_id=token.binding.contract_id,
    )
    if snapshot is None:
        raise PermissionError(f"Delegation token rejected: {error}")
    if snapshot.caveats:
        raise PermissionError("DelegationContext cannot enforce token caveats")
    _require_operation_subset(snapshot.ops_allowed, context.operations)
    _require_resource_subset(_token_resource_patterns(snapshot), context.resources)
    if context.authority_token_id != snapshot.token_id:
        raise PermissionError("Delegation context authority token does not match")
    return snapshot


def _bind_authority_marker(context: DelegationContext, token_id: str) -> None:
    """Mark manager-backed provenance without retaining signing authority."""
    if type(token_id) is not str or not token_id:
        raise TypeError("authority token ID must be a non-empty exact string")
    object.__setattr__(context, "authority_token_id", token_id)


def _bind_scope(
    context: DelegationContext,
    operations: Sequence[str],
    resources: Sequence[str],
) -> None:
    """Bind manager-validated scope to a newly created unscoped context."""
    if context.operations or context.resources:
        raise PermissionError("Delegation context scope is already bound")
    object.__setattr__(
        context,
        "operations",
        _normalized_scope(operations, "operations"),
    )
    object.__setattr__(
        context,
        "resources",
        _normalized_scope(resources, "resources"),
    )
