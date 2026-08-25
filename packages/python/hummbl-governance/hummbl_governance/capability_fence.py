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

"""Capability Fence -- Soft sandbox enforcing capability boundaries (ASI-07).

Extends delegation tokens to enforce capability boundaries at runtime.
Provides allow/deny lists, guard wrappers, and audit logging for
agent capability checks.

Usage:
    from hummbl_governance import CapabilityFence, CapabilityDenied

    fence = CapabilityFence(
        allowed=["api:read", "bus:write"],
        denied=["file:write", "shell:execute"],
    )
    fence.check("api:read")    # passes, returns True
    fence.check("file:write")  # raises CapabilityDenied

Stdlib-only. Zero third-party dependencies.
"""

from __future__ import annotations

import json
import logging
import math
import threading
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from fnmatch import fnmatchcase
from typing import Any

from hummbl_governance._types import Caveat, DelegationToken, ResourceSelector
from hummbl_governance.delegation import DelegationTokenManager

logger = logging.getLogger(__name__)


class CapabilityDenied(Exception):
    """Raised when an agent attempts an operation outside its capability fence.

    Attributes:
        capability: The capability that was denied.
        allowed: The set of allowed capabilities.
        denied: The set of denied capabilities.
    """

    def __init__(
        self,
        capability: str,
        allowed: frozenset[str],
        denied: frozenset[str],
        reason: str | None = None,
    ) -> None:
        self.capability = capability
        self.allowed = allowed
        self.denied = denied
        self.reason = reason
        detail = f"; reason={reason}" if reason else ""
        super().__init__(
            f"Capability denied: {capability!r} "
            f"(allowed={sorted(allowed)}, denied={sorted(denied)}{detail})"
        )


@dataclass(frozen=True)
class CapabilityAuditEntry:
    """Record of a capability check."""

    timestamp: str
    capability: str
    decision: str  # "allow" or "deny"
    reason: str


class CapabilityFence:
    """Soft sandbox enforcing capability boundaries via delegation tokens.

    Capability strings use the format "resource:action" (e.g., "api:read",
    "file:write", "shell:execute").

    Resolution logic:
    1. If capability is in denied set -> deny
    2. If allowed set is non-empty and capability is not in it -> deny
    3. Otherwise -> allow

    Thread-safe. All state access is lock-protected.

    Args:
        allowed: Capabilities explicitly allowed. If non-empty, only these
            capabilities are permitted (allowlist mode).
        denied: Capabilities explicitly denied. Always takes precedence
            over allowed.
        audit_log: Optional list to append CapabilityAuditEntry records to.
    """

    def __init__(
        self,
        allowed: list[str] | None = None,
        denied: list[str] | None = None,
        audit_log: list[CapabilityAuditEntry] | None = None,
        *,
        allow_all_if_empty: bool = True,
        _token: DelegationToken | None = None,
        _token_manager: DelegationTokenManager | None = None,
        _expected_issuer: str | None = None,
        _expected_subject: str | None = None,
        _expected_task_id: str | None = None,
        _expected_contract_id: str | None = None,
        _caveat_validator: Callable[[Caveat, Mapping[str, Any]], bool] | None = None,
    ) -> None:
        self._allowed = _normalized_capability_set(allowed, "allowed")
        self._denied = _normalized_capability_set(denied, "denied")
        self._audit_log = audit_log
        self._allow_all_if_empty = allow_all_if_empty
        self._token = _token
        self._token_manager = _token_manager
        self._expected_issuer = _expected_issuer
        self._expected_subject = _expected_subject
        self._expected_task_id = _expected_task_id
        self._expected_contract_id = _expected_contract_id
        self._caveat_validator = _caveat_validator
        self._lock = threading.Lock()

    @property
    def allowed(self) -> frozenset[str]:
        """The set of allowed capabilities."""
        return self._allowed

    @property
    def denied(self) -> frozenset[str]:
        """The set of denied capabilities."""
        return self._denied

    def check(
        self,
        capability: str,
        *,
        resource_type: str | None = None,
        resource_id: str | None = None,
        context: Mapping[str, Any] | None = None,
    ) -> bool:
        """Check if a capability is permitted.

        Args:
            capability: Capability string to check (e.g., "file:write").
            resource_type: Resource type being accessed. Required when a
                token-derived fence contains resource selectors.
            resource_id: Resource identifier being accessed. Required when a
                token-derived fence contains resource selectors.
            context: Runtime values used to satisfy resource constraints and
                delegation-token caveats.

        Returns:
            True if the capability is allowed.

        Raises:
            CapabilityDenied: If the capability is not permitted.
        """
        if type(capability) is not str or not capability:
            raise TypeError("capability must be a non-empty exact string")
        for name, value in (
            ("resource_type", resource_type),
            ("resource_id", resource_id),
        ):
            if value is not None and (type(value) is not str or not value):
                raise TypeError(f"{name} must be a non-empty exact string or None")
        decision, reason = self._resolve(
            capability,
            resource_type=resource_type,
            resource_id=resource_id,
            context=context,
        )
        with self._lock:
            self._audit(capability, decision, reason)
        if decision == "deny":
            raise CapabilityDenied(
                capability,
                self._allowed,
                self._denied,
                reason=reason,
            )
        return True

    def guard(self, fn: Callable[..., Any], capability: str, *args: Any, **kwargs: Any) -> Any:
        """Wrap a function call with a capability check.

        Args:
            fn: Function to call if capability is allowed.
            capability: Capability required to execute the function.
            *args: Positional arguments passed to fn.
            **kwargs: Keyword arguments passed to fn.

        Returns:
            The return value of fn(*args, **kwargs).

        Raises:
            CapabilityDenied: If the capability is not permitted.
        """
        self.check(capability)
        return fn(*args, **kwargs)

    @classmethod
    def from_delegation_token(
        cls,
        token: DelegationToken,
        token_manager: DelegationTokenManager,
        *,
        expected_issuer: str,
        expected_subject: str,
        expected_task_id: str,
        expected_contract_id: str,
        denied: list[str] | None = None,
        audit_log: list[CapabilityAuditEntry] | None = None,
        caveat_validator: Callable[[Caveat, Mapping[str, Any]], bool] | None = None,
    ) -> CapabilityFence:
        """Create a fail-closed fence from an authenticated delegation token.

        The token signature, expiry, issuer, subject, task, and contract are
        checked before construction and again for every capability check.
        Resource selectors and caveats are enforced at check time. A token
        with no granted operations creates a deny-all fence.

        Args:
            token: DelegationToken to authenticate and enforce.
            token_manager: Manager holding the signing key for the token.
            expected_issuer: Issuer authorized to grant the capability.
            expected_subject: Agent expected to exercise the capability.
            expected_task_id: Task to which the token must be bound.
            expected_contract_id: Contract to which the token must be bound.
            denied: Additional denied capabilities.
            audit_log: Optional audit log list.
            caveat_validator: Required when the token has caveats. Called for
                each caveat and runtime context on every capability check.

        Returns:
            A new CapabilityFence instance.

        Raises:
            TypeError: If token_manager is not a DelegationTokenManager.
            ValueError: If the token is invalid or caveats cannot be enforced.
        """
        if type(token_manager) is not DelegationTokenManager:
            raise TypeError("token_manager must be an exact DelegationTokenManager")
        expected_values = {
            "expected_issuer": expected_issuer,
            "expected_subject": expected_subject,
            "expected_task_id": expected_task_id,
            "expected_contract_id": expected_contract_id,
        }
        invalid_expectations = [
            name
            for name, value in expected_values.items()
            if type(value) is not str or not value
        ]
        if invalid_expectations:
            raise ValueError(
                "Delegation token expectations must be non-empty strings: "
                f"{sorted(invalid_expectations)}"
            )

        snapshot, error = token_manager.authenticate_token(
            token,
            expected_task_id=expected_task_id,
            expected_contract_id=expected_contract_id,
            expected_subject=expected_subject,
            expected_issuer=expected_issuer,
        )
        if snapshot is None:
            raise ValueError(f"Delegation token rejected: {error}")
        if snapshot.caveats and caveat_validator is None:
            raise ValueError("Delegation token caveats require a caveat_validator")

        return cls(
            allowed=list(snapshot.ops_allowed),
            denied=denied,
            audit_log=audit_log,
            allow_all_if_empty=False,
            _token=snapshot,
            _token_manager=token_manager,
            _expected_issuer=expected_issuer,
            _expected_subject=expected_subject,
            _expected_task_id=expected_task_id,
            _expected_contract_id=expected_contract_id,
            _caveat_validator=caveat_validator,
        )

    def _resolve(
        self,
        capability: str,
        *,
        resource_type: str | None,
        resource_id: str | None,
        context: Mapping[str, Any] | None,
    ) -> tuple[str, str]:
        """Resolve a capability check to allow/deny with reason.

        Returns:
            Tuple of (decision, reason).
        """
        authenticated_token: DelegationToken | None = None
        if self._token is not None:
            if self._token_manager is None:
                return "deny", "token manager is unavailable"
            authenticated_token, error = self._token_manager.authenticate_token(
                self._token,
                expected_task_id=self._expected_task_id,
                expected_contract_id=self._expected_contract_id,
                expected_subject=self._expected_subject,
                expected_issuer=self._expected_issuer,
            )
            if authenticated_token is None:
                return "deny", f"delegation token is no longer valid: {error}"

        if capability in self._denied:
            return "deny", f"{capability!r} is in denied set"
        if capability not in self._allowed and (
            self._allowed or not self._allow_all_if_empty
        ):
            return "deny", f"{capability!r} is not in allowed set"

        try:
            runtime_context = (
                {} if context is None else _validated_runtime_json(context)
            )
        except (TypeError, ValueError) as exc:
            return "deny", f"context must contain only safe JSON values: {exc}"
        if type(runtime_context) is not dict:
            return "deny", "context must be a plain mapping"
        resource_selectors = (
            authenticated_token.resource_selectors if authenticated_token else ()
        )
        if resource_selectors:
            if resource_type is None or resource_id is None:
                return "deny", "resource_type and resource_id are required"
            try:
                resource_allowed = any(
                    _resource_matches(
                        selector,
                        resource_type=resource_type,
                        resource_id=resource_id,
                        context=runtime_context,
                    )
                    for selector in resource_selectors
                )
            except Exception:
                logger.warning("Resource selector evaluation failed closed", exc_info=True)
                resource_allowed = False
            if not resource_allowed:
                return "deny", f"resource {resource_type!r}:{resource_id!r} is outside token scope"

        caveats = authenticated_token.caveats if authenticated_token else ()
        if caveats:
            if self._caveat_validator is None:
                return "deny", "token caveats cannot be evaluated"
            for caveat in caveats:
                try:
                    satisfied = self._caveat_validator(caveat, runtime_context)
                except Exception:
                    logger.warning(
                        "Caveat validator raised for caveat %s",
                        caveat.caveat_id,
                        exc_info=True,
                    )
                    return "deny", f"caveat {caveat.caveat_id!r} evaluation failed"
                if satisfied is not True:
                    return "deny", f"caveat {caveat.caveat_id!r} is not satisfied"

        return "allow", "permitted"

    def _audit(self, capability: str, decision: str, reason: str) -> None:
        """Record a capability check in the audit log if configured."""
        if self._audit_log is not None:
            entry = CapabilityAuditEntry(
                timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                capability=capability,
                decision=decision,
                reason=reason,
            )
            self._audit_log.append(entry)


def _resource_matches(
    selector: ResourceSelector,
    *,
    resource_type: str,
    resource_id: str,
    context: Mapping[str, Any],
) -> bool:
    """Return whether a concrete resource satisfies a signed selector."""
    if not fnmatchcase(resource_type, selector.resource_type):
        return False
    if not fnmatchcase(resource_id, selector.resource_id):
        return False
    missing = object()
    for key, expected in selector.constraints.items():
        actual = context.get(key, missing)
        if actual is missing or not _plain_json_equal(expected, actual):
            return False
    return True


def _normalized_capability_set(
    values: list[str] | None,
    name: str,
) -> frozenset[str]:
    """Freeze capability configuration after exact-string validation."""
    if values is None:
        return frozenset()
    if type(values) is not list or not all(
        type(value) is str and value for value in values
    ):
        raise TypeError(f"{name} must be a list of non-empty exact strings")
    return frozenset(values)


def _plain_json_equal(expected: Any, actual: Any) -> bool:
    """Compare exact built-in JSON values without invoking custom equality."""
    try:
        expected_json = json.dumps(
            expected,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        actual_json = json.dumps(
            _validated_runtime_json(actual),
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError):
        return False
    return expected_json == actual_json


def _validated_runtime_json(value: Any) -> Any:
    """Snapshot exact built-in JSON values without preserving dynamic behavior."""
    if value is None or type(value) in {str, bool, int}:
        return value
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError("runtime context numbers must be finite")
        return value
    if type(value) is list:
        return [_validated_runtime_json(item) for item in value]
    if type(value) is dict:
        validated: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise TypeError("runtime context keys must be strings")
            validated[key] = _validated_runtime_json(item)
        return validated
    raise TypeError(f"unsupported runtime context type: {type(value).__name__}")
