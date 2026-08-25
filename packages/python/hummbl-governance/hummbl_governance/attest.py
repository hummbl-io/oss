"""MCP Attestation — verify MCP server identity and policy compliance.

This module provides the Attest class for verifying that an MCP server
is running an expected policy (allowlist, blocklist, capability fence).

Stdlib-only. No third-party dependencies.

Example:
    from hummbl_governance.attest import Attest, ALLOWLIST

    attest = Attest()
    result = attest.verify(
        server="hummbl-mcp-server",
        policy=ALLOWLIST,
        allowed_tools=["base120_get", "base120_list"],
    )
    if result.ok:
        print("Server attested")
    else:
        print(f"Attestation failed: {result.reason}")
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from typing import Any

__all__ = [
    "Attest",
    "AttestResult",
    "ALLOWLIST",
    "BLOCKLIST",
    "CAPABILITY_FENCE",
]

# Policy type constants
ALLOWLIST = "allowlist"
BLOCKLIST = "blocklist"
CAPABILITY_FENCE = "capability_fence"


@dataclass(frozen=True)
class AttestResult:
    """Result of an attestation verification."""

    ok: bool
    server: str
    policy: str
    reason: str = ""
    timestamp: str = ""
    nonce: str = ""
    hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "server": self.server,
            "policy": self.policy,
            "reason": self.reason,
            "timestamp": self.timestamp,
            "nonce": self.nonce,
            "hash": self.hash,
        }


class Attest:
    """Verify MCP server identity and policy compliance.

    Provides a simple attestation mechanism: given a server name and a
    policy (allowlist, blocklist, or capability fence), verify that the
    server's declared tools/resources match the expected policy.

    This is a lightweight, stdlib-only attestation. It does not perform
    cryptographic verification of remote server identity (that requires
    TLS/mTLS). It verifies that the server's declared capabilities match
    the expected policy.
    """

    def __init__(self, *, challenge_timeout_seconds: int = 30) -> None:
        """Initialize the attestation verifier.

        Args:
            challenge_timeout_seconds: Max seconds for a challenge-response
                cycle (default 30).
        """
        self._timeout = challenge_timeout_seconds

    def verify(
        self,
        server: str,
        policy: str,
        *,
        allowed_tools: list[str] | None = None,
        blocked_tools: list[str] | None = None,
        declared_tools: list[str] | None = None,
        nonce: str | None = None,
    ) -> AttestResult:
        """Verify that a server's declared tools match the expected policy.

        Args:
            server: Server name or identifier.
            policy: Policy type (ALLOWLIST, BLOCKLIST, or CAPABILITY_FENCE).
            allowed_tools: Tools the server is allowed to expose (for ALLOWLIST).
            blocked_tools: Tools the server must not expose (for BLOCKLIST).
            declared_tools: Tools the server actually declares.
            nonce: Optional nonce for challenge-response (auto-generated if None).

        Returns:
            AttestResult with ok=True if policy is satisfied, False otherwise.
        """
        ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        n = nonce or hashlib.sha256(f"{server}:{ts}".encode()).hexdigest()[:16]
        declared = declared_tools or []

        # Build the policy hash for the attestation record
        policy_data = {
            "server": server,
            "policy": policy,
            "allowed_tools": allowed_tools or [],
            "blocked_tools": blocked_tools or [],
            "declared_tools": declared,
            "nonce": n,
            "timestamp": ts,
        }
        policy_hash = hashlib.sha256(
            json.dumps(policy_data, sort_keys=True).encode()
        ).hexdigest()

        def _check_allowed_scope(
            allowed: set[str],
            *,
            empty_reason: str,
            violation_prefix: str,
        ) -> AttestResult | None:
            if not allowed:
                return AttestResult(
                    ok=False,
                    server=server,
                    policy=policy,
                    reason=empty_reason,
                    timestamp=ts,
                    nonce=n,
                    hash=policy_hash,
                )
            violations = set(declared) - allowed
            if violations:
                return AttestResult(
                    ok=False,
                    server=server,
                    policy=policy,
                    reason=f"{violation_prefix}: {sorted(violations)}",
                    timestamp=ts,
                    nonce=n,
                    hash=policy_hash,
                )
            return None

        if policy == ALLOWLIST:
            result = _check_allowed_scope(
                set(allowed_tools or []),
                empty_reason="ALLOWLIST policy requires allowed_tools",
                violation_prefix="Tools not in allowlist",
            )
            if result is not None:
                return result
            return AttestResult(
                ok=True,
                server=server,
                policy=policy,
                timestamp=ts,
                nonce=n,
                hash=policy_hash,
            )

        elif policy == BLOCKLIST:
            blocked = set(blocked_tools or [])
            declared_set = set(declared)
            violations = declared_set & blocked
            if violations:
                return AttestResult(
                    ok=False,
                    server=server,
                    policy=policy,
                    reason=f"Blocked tools exposed: {sorted(violations)}",
                    timestamp=ts,
                    nonce=n,
                    hash=policy_hash,
                )
            return AttestResult(
                ok=True,
                server=server,
                policy=policy,
                timestamp=ts,
                nonce=n,
                hash=policy_hash,
            )

        elif policy == CAPABILITY_FENCE:
            result = _check_allowed_scope(
                set(allowed_tools or []),
                empty_reason="CAPABILITY_FENCE policy requires allowed_tools",
                violation_prefix="Tools outside capability fence",
            )
            if result is not None:
                return result
            return AttestResult(
                ok=True,
                server=server,
                policy=policy,
                timestamp=ts,
                nonce=n,
                hash=policy_hash,
            )

        else:
            return AttestResult(
                ok=False,
                server=server,
                policy=policy,
                reason=f"Unknown policy type: {policy}",
                timestamp=ts,
                nonce=n,
                hash=policy_hash,
            )
