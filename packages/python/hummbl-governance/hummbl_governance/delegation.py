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

"""Delegation Token -- HMAC-SHA256 or Ed25519 signed capability tokens for agent delegation.

Implements delegation capability tokens with cryptographic integrity,
expiry, binding to tasks/contracts, and least-privilege enforcement.

Supports two signing methods:
- HMAC-SHA256 (default, stdlib-only, shared-secret trust domain)
- Ed25519 (optional, requires cryptography>=42.0, public-key trust domain)

Usage (HMAC-SHA256):
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

Usage (Ed25519):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    priv = Ed25519PrivateKey.generate()
    mgr = DelegationTokenManager(signing_method="ed25519", private_key=priv)
    token = mgr.create_token(...)
    # Verify with public key:
    valid = token.verify_ed25519_signature(priv.public_key().public_bytes_raw())

Stdlib-only by default. Ed25519 requires the [primitives] extra.
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
            Used when signing_method="hmac_sha256" (default).
        signing_method: Signature scheme — "hmac_sha256" (default) or "ed25519".
        private_key: Ed25519 private key object (required when signing_method="ed25519").
            Must be an Ed25519PrivateKey from the cryptography package.
        public_key: Ed25519 public key bytes (32 bytes). Required for ed25519
            token validation. If None and signing_method="ed25519", validation
            will fail. Can be derived from private_key if the cryptography
            package is available.
    """

    def __init__(
        self,
        secret: bytes | None = None,
        signing_method: str = "hmac_sha256",
        private_key: Any = None,
        public_key: bytes | None = None,
    ):
        self._signing_method = signing_method

        if signing_method == "ed25519":
            if private_key is None:
                raise ValueError(
                    "Ed25519 signing requires a private_key. "
                    "Generate one with Ed25519PrivateKey.generate()."
                )
            self._ed25519_private_key = private_key
            # Derive public key if not provided
            if public_key is None:
                try:
                    from cryptography.hazmat.primitives.serialization import (
                        Encoding,
                        PublicFormat,
                    )
                    public_key = private_key.public_key().public_bytes(
                        encoding=Encoding.Raw,
                        format=PublicFormat.Raw,
                    )
                except ImportError as exc:
                    raise ValueError(
                        "Ed25519 public key derivation requires the "
                        "'cryptography' package. Install with: "
                        "pip install 'hummbl-governance[primitives]'"
                    ) from exc
                except Exception as exc:
                    raise ValueError(
                        f"Failed to derive Ed25519 public key: {exc}. "
                        f"Provide public_key explicitly."
                    ) from exc
            self._ed25519_public_key = public_key
            self._secret = b""  # Not used for ed25519
        elif signing_method == "hmac_sha256":
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
            self._ed25519_private_key = None
            self._ed25519_public_key = None
        else:
            raise ValueError(
                f"Unsupported signing_method: {signing_method}. "
                f"Use 'hmac_sha256' or 'ed25519'."
            )

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
            signing_method=self._signing_method,
        ))

        if self._signing_method == "ed25519":
            sig = _compute_ed25519_signature(token.to_dict(), self._ed25519_private_key)
        else:
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
            signing_method=self._signing_method,
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
            if self._signing_method == "ed25519":
                if not snapshot.verify_ed25519_signature(self._ed25519_public_key):
                    return None, E_TOKEN_INVALID
            else:
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


def _compute_ed25519_signature(data: dict[str, Any], private_key: Any) -> str:
    """Compute Ed25519 signature for token data.

    Requires the cryptography package (install with hummbl-governance[primitives]).
    """
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import (
            Ed25519PrivateKey,
        )
    except ImportError as exc:
        raise ImportError(
            "Ed25519 signing requires the 'cryptography' package. "
            "Install with: pip install hummbl-governance[primitives]"
        ) from exc
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
    sig = private_key.sign(canonical.encode("utf-8"))
    return sig.hex()


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
        signing_method=token.signing_method,
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
