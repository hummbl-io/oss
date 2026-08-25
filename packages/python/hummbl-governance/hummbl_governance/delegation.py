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

"""Delegation Token -- HMAC-SHA256 signed capability tokens for agent delegation.

Implements delegation capability tokens with cryptographic integrity,
expiry, binding to tasks/contracts, and least-privilege enforcement.

Usage:
    from hummbl_governance import DelegationToken, DelegationTokenManager
    from hummbl_governance.delegation import TokenBinding

    mgr = DelegationTokenManager(secret=b"my-secret")
    token = mgr.create_token(
        issuer="orchestrator",
        subject="worker-agent",
        ops_allowed=["read_data", "write_results"],
        binding=TokenBinding(task_id="task-1", contract_id="contract-1"),
    )

    valid, error = mgr.validate_token(token)

Stdlib-only. Zero third-party dependencies.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import math
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from hummbl_governance._types import (
    Caveat,
    DelegationToken,
    ResourceSelector,
    TokenBinding,
)
from hummbl_governance.errors import HummblError

logger = logging.getLogger(__name__)


# Error code shorthands — resolved from the unified HummblError enum.
E_TOKEN_INVALID = HummblError.TOKEN_INVALID.value
E_TOKEN_EXPIRED = HummblError.TOKEN_EXPIRED.value
E_BINDING_MISMATCH = HummblError.BINDING_MISMATCH.value
E_DCT_VIOLATION = HummblError.DCT_VIOLATION.value


class DelegationTokenManager:
    """Manager for creating and validating delegation tokens.

    Args:
        secret: HMAC secret bytes. If None, reads from HUMMBL_SIGNING_SECRET
            or DCT_SECRET env vars, or generates an ephemeral key.
    """

    def __init__(self, secret: bytes | None = None):
        if secret is None:
            for var in ("HUMMBL_SIGNING_SECRET", "DCT_SECRET"):
                secret_str = os.environ.get(var)
                if secret_str:
                    secret = secret_str.encode("utf-8")
                    break
            if secret is None:
                logger.warning(
                    "No signing secret configured, using ephemeral key. "
                    "Tokens will be invalid after process restart."
                )
                secret = os.urandom(32)
        self._secret = secret

    def create_token(
        self,
        issuer: str,
        subject: str,
        ops_allowed: list[str],
        binding: TokenBinding,
        resource_selectors: list[ResourceSelector] | None = None,
        caveats: list[Caveat] | None = None,
        expiry_minutes: int | None = 120,
    ) -> DelegationToken:
        """Create a new signed delegation token.

        Args:
            issuer: Agent granting the capability.
            subject: Agent receiving the capability.
            ops_allowed: Permitted operations.
            binding: Task/contract binding.
            resource_selectors: Accessible resources (default: all).
            caveats: Constraints on use.
            expiry_minutes: Minutes until expiry (None = no expiry).

        Returns:
            Signed DelegationToken.
        """
        if type(issuer) is not str or not issuer:
            raise TypeError("issuer must be a non-empty exact string")
        if type(subject) is not str or not subject:
            raise TypeError("subject must be a non-empty exact string")
        if type(ops_allowed) is not list or not all(
            type(operation) is str and operation for operation in ops_allowed
        ):
            raise TypeError("ops_allowed must be a list of non-empty exact strings")
        if type(binding) is not TokenBinding:
            raise TypeError("binding must be an exact TokenBinding")
        if resource_selectors is not None and type(resource_selectors) is not list:
            raise TypeError("resource_selectors must be a list or None")
        if caveats is not None and type(caveats) is not list:
            raise TypeError("caveats must be a list or None")
        expiry = None
        if expiry_minutes is not None:
            expiry_dt = datetime.now(timezone.utc) + timedelta(minutes=expiry_minutes)
            expiry = expiry_dt.isoformat().replace("+00:00", "Z")

        token = _normalized_token_snapshot(DelegationToken(
            token_id=str(uuid.uuid4()),
            issuer=issuer,
            subject=subject,
            resource_selectors=tuple(resource_selectors or []),
            ops_allowed=tuple(ops_allowed),
            caveats=tuple(caveats or []),
            expiry=expiry,
            binding=binding,
            signature="",
        ))

        sig = _compute_signature(token.to_dict(), self._secret)

        return DelegationToken(
            token_id=token.token_id,
            issuer=token.issuer,
            subject=token.subject,
            resource_selectors=token.resource_selectors,
            ops_allowed=token.ops_allowed,
            caveats=token.caveats,
            expiry=token.expiry,
            binding=token.binding,
            signature=sig,
        )

    def issue(
        self,
        issuer: str,
        subject: str,
        operations: list[str],
        resources: list[str],
        *,
        expiry_minutes: int | None = 120,
        task_id: str = "default",
        contract_id: str = "default",
    ) -> DelegationToken:
        """Convenience alias for create_token with a simpler signature.

        Accepts ``operations`` and ``resources`` as plain lists and
        constructs the required TokenBinding and ResourceSelector objects
        internally. Matches the code examples shown on hummbl.io.

        Args:
            issuer: Agent granting the capability.
            subject: Agent receiving the capability.
            operations: Permitted operations (e.g. ["read", "summarize"]).
            resources: Accessible resource patterns (e.g. ["docs/*"]).
            expiry_minutes: Minutes until expiry (None = no expiry).
            task_id: Task binding ID (default "default").
            contract_id: Contract binding ID (default "default").

        Returns:
            Signed DelegationToken.
        """
        binding = TokenBinding(task_id=task_id, contract_id=contract_id)
        selectors = [
            ResourceSelector(resource_type="*", resource_id=r) for r in resources
        ]
        return self.create_token(
            issuer=issuer,
            subject=subject,
            ops_allowed=operations,
            binding=binding,
            resource_selectors=selectors,
            expiry_minutes=expiry_minutes,
        )

    def validate_token(
        self,
        token: DelegationToken,
        expected_task_id: str | None = None,
        expected_contract_id: str | None = None,
        expected_subject: str | None = None,
        expected_issuer: str | None = None,
    ) -> tuple[bool, str | None]:
        """Validate a delegation token.

        Returns:
            Tuple of (is_valid, error_code).
        """
        snapshot, error = self.authenticate_token(
            token,
            expected_task_id=expected_task_id,
            expected_contract_id=expected_contract_id,
            expected_subject=expected_subject,
            expected_issuer=expected_issuer,
        )
        return snapshot is not None, error

    def authenticate_token(
        self,
        token: DelegationToken,
        expected_task_id: str | None = None,
        expected_contract_id: str | None = None,
        expected_subject: str | None = None,
        expected_issuer: str | None = None,
    ) -> tuple[DelegationToken | None, str | None]:
        """Return a verified, detached token snapshot or fail closed.

        Normalization rejects container subclasses and non-JSON values before
        signature verification. Callers must enforce the returned snapshot,
        not the caller-owned token, to avoid verification/use races.
        """
        expected_values = (
            expected_task_id,
            expected_contract_id,
            expected_subject,
            expected_issuer,
        )
        if any(
            value is not None and (type(value) is not str or not value)
            for value in expected_values
        ):
            return None, E_BINDING_MISMATCH
        try:
            snapshot = _normalized_token_snapshot(token)
            if not snapshot.verify_signature(self._secret):
                return None, E_TOKEN_INVALID
            if snapshot.is_expired():
                return None, E_TOKEN_EXPIRED
            if expected_issuer is not None and snapshot.issuer != expected_issuer:
                return None, E_BINDING_MISMATCH
            if (
                expected_task_id is not None
                or expected_contract_id is not None
                or expected_subject is not None
            ):
                valid, error = self._validate_binding(
                    snapshot,
                    expected_task_id,
                    expected_contract_id,
                    expected_subject,
                )
                if not valid:
                    return None, error
        except Exception:
            logger.warning("Delegation token authentication failed closed", exc_info=True)
            return None, E_TOKEN_INVALID
        return snapshot, None

    @staticmethod
    def _validate_binding(
        token: DelegationToken,
        expected_task_id: str | None,
        expected_contract_id: str | None,
        expected_subject: str | None,
    ) -> tuple[bool, str | None]:
        """Validate token binding against expected values."""
        task_id = (
            expected_task_id
            if expected_task_id is not None
            else (token.binding.task_id if token.binding else "")
        )
        contract_id = (
            expected_contract_id
            if expected_contract_id is not None
            else (token.binding.contract_id if token.binding else "")
        )
        subject = expected_subject if expected_subject is not None else token.subject
        if not token.validate_binding(task_id, contract_id, subject):
            return False, E_BINDING_MISMATCH
        return True, None

    def check_least_privilege(
        self,
        token: DelegationToken,
        requested_op: str,
        allowed_tools: list[str] | None = None,
        denied_tools: list[str] | None = None,
    ) -> tuple[bool, str | None]:
        """Check if requested operation complies with least privilege.

        Returns:
            Tuple of (is_allowed, error_code).
        """
        if type(requested_op) is not str or not requested_op:
            return False, E_DCT_VIOLATION
        for tools in (allowed_tools, denied_tools):
            if tools is not None and (
                type(tools) is not list
                or not all(type(tool) is str and tool for tool in tools)
            ):
                return False, E_DCT_VIOLATION
        snapshot, error = self.authenticate_token(token)
        if snapshot is None:
            return False, error
        if requested_op not in snapshot.ops_allowed:
            return False, E_DCT_VIOLATION
        if allowed_tools is not None and requested_op not in allowed_tools:
            return False, E_DCT_VIOLATION
        if denied_tools is not None and requested_op in denied_tools:
            return False, E_DCT_VIOLATION
        return True, None


def _compute_signature(data: dict[str, Any], secret: bytes) -> str:
    """Compute HMAC-SHA256 signature for token data."""
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hmac.new(secret, canonical.encode("utf-8"), hashlib.sha256).hexdigest()


def _normalized_token_snapshot(token: DelegationToken) -> DelegationToken:
    """Copy a token into exact built-in types before it crosses the trust boundary."""
    if type(token) is not DelegationToken:
        raise TypeError("token must be an exact DelegationToken")
    for name in ("token_id", "issuer", "subject", "signature"):
        if type(getattr(token, name)) is not str:
            raise TypeError(f"{name} must be a string")
    if token.expiry is not None and type(token.expiry) is not str:
        raise TypeError("expiry must be a string or None")
    if type(token.ops_allowed) is not tuple or not all(
        type(operation) is str for operation in token.ops_allowed
    ):
        raise TypeError("ops_allowed must be a tuple of strings")
    if type(token.resource_selectors) is not tuple:
        raise TypeError("resource_selectors must be a tuple")
    if type(token.caveats) is not tuple:
        raise TypeError("caveats must be a tuple")

    binding = token.binding
    if binding is not None:
        if type(binding) is not TokenBinding:
            raise TypeError("binding must be an exact TokenBinding")
        if type(binding.task_id) is not str or type(binding.contract_id) is not str:
            raise TypeError("binding values must be strings")
        binding = TokenBinding(binding.task_id, binding.contract_id)

    selectors: list[ResourceSelector] = []
    for selector in token.resource_selectors:
        if type(selector) is not ResourceSelector:
            raise TypeError("resource selector must be an exact ResourceSelector")
        if type(selector.resource_type) is not str or type(selector.resource_id) is not str:
            raise TypeError("resource selector identifiers must be strings")
        constraints = _copy_plain_json(selector.constraints, "resource selector constraints")
        if type(constraints) is not dict:
            raise TypeError("resource selector constraints must be a dictionary")
        selectors.append(
            ResourceSelector(
                resource_type=selector.resource_type,
                resource_id=selector.resource_id,
                constraints=constraints,
            )
        )

    caveats: list[Caveat] = []
    for caveat in token.caveats:
        if type(caveat) is not Caveat:
            raise TypeError("caveat must be an exact Caveat")
        if type(caveat.caveat_id) is not str or type(caveat.type) is not str:
            raise TypeError("caveat identifiers must be strings")
        parameters = _copy_plain_json(caveat.parameters, "caveat parameters")
        if type(parameters) is not dict:
            raise TypeError("caveat parameters must be a dictionary")
        caveats.append(Caveat(caveat.caveat_id, caveat.type, parameters))

    return DelegationToken(
        token_id=token.token_id,
        issuer=token.issuer,
        subject=token.subject,
        resource_selectors=tuple(selectors),
        ops_allowed=tuple(token.ops_allowed),
        caveats=tuple(caveats),
        expiry=token.expiry,
        binding=binding,
        signature=token.signature,
    )


def _copy_plain_json(value: Any, path: str) -> Any:
    """Return a detached exact-type JSON value, rejecting dynamic subclasses."""
    if value is None or type(value) in {str, bool, int}:
        return value
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError(f"{path} contains a non-finite float")
        return value
    if type(value) is list:
        return [_copy_plain_json(item, f"{path}[]") for item in value]
    if type(value) is dict:
        copied: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise TypeError(f"{path} contains a non-string key")
            copied[key] = _copy_plain_json(item, f"{path}.{key}")
        return copied
    raise TypeError(f"{path} contains unsupported type {type(value).__name__}")
