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
# SPDX-License-Identifier: MIT OR Apache-2.0

"""Identity Engine — K3 invariant enforcement.

Every agent has a single canonical identity, a trust tier,
and a capability vector. Identity changes require Board ratification.
"""

from __future__ import annotations

import json
import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .invariants import KernelInvariant, KernelPanic

logger = logging.getLogger(__name__)


@dataclass
class AgentIdentity:
    """Canonical identity record for an agent."""

    agent_id: str
    trust_tier: str = "PROBATIONARY"  # OWNER, TRUSTED, MEDIUM, PROBATIONARY, REVOKED
    active_roles: list[str] = field(default_factory=list)
    capability_vector: list[str] = field(default_factory=list)
    last_receipt_time: str = ""
    claimed_at: str = ""
    vendor: str = ""
    model: str = ""


class IdentityEngine:
    """Engine for agent identity registration, authentication, and role claims."""

    TRUST_TIERS = ["OWNER", "TRUSTED", "MEDIUM-HIGH", "MEDIUM", "PROBATIONARY", "REVOKED"]
    ROLE_STATES = ["UNCLAIMED", "CLAIMED", "PROBATION", "CONFIRMED", "PROMOTED"]

    def __init__(self, state_dir: Path) -> None:
        self.state_dir = state_dir
        self._lock = threading.Lock()
        self.registry_file = state_dir / "identity_registry.jsonl"
        self.role_claims_file = state_dir / "role_claims.jsonl"
        self._identities: dict[str, AgentIdentity] = {}
        self._role_claims: dict[str, dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        """Load identity registry and role claims from disk.

        Fail-closed: the identity registry and role claims are
        security-critical (K3/K7). Silently skipping corrupted lines would
        cause an agent whose record is on a corrupted line to be treated as
        unregistered — denying governance access — or strip an agent of
        authorized roles, with no observable signal. Raise KernelPanic
        instead so operators can investigate and repair the corrupted
        records.
        """
        if self.registry_file.exists():
            for line in self.registry_file.read_text().strip().split("\n"):
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    self._identities[data["agent_id"]] = AgentIdentity(**data)
                except (json.JSONDecodeError, KeyError, TypeError) as exc:
                    logger.error(
                        "Corrupted identity registry line in %s: %s",
                        self.registry_file, line[:100],
                    )
                    raise KernelPanic(
                        KernelInvariant.IDENTITY,
                        f"Corrupted identity registry line in "
                        f"{self.registry_file}: {line[:100]!r} — "
                        f"refusing to silently drop identity record",
                    ) from exc

        if self.role_claims_file.exists():
            for line in self.role_claims_file.read_text().strip().split("\n"):
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    key = f"{data['agent_id']}:{data['role_id']}"
                    self._role_claims[key] = data
                except (json.JSONDecodeError, KeyError, TypeError) as exc:
                    logger.error(
                        "Corrupted role claim line in %s: %s",
                        self.role_claims_file, line[:100],
                    )
                    raise KernelPanic(
                        KernelInvariant.ROLE,
                        f"Corrupted role claim line in "
                        f"{self.role_claims_file}: {line[:100]!r} — "
                        f"refusing to silently drop role claim",
                    ) from exc

    def _save_identities(self) -> None:
        """Save identity registry to disk."""
        with open(self.registry_file, "w", encoding="utf-8") as f:
            for identity in self._identities.values():
                f.write(json.dumps(identity.__dict__, sort_keys=True) + "\n")

    def _save_role_claims(self) -> None:
        """Save role claims to disk."""
        with open(self.role_claims_file, "w", encoding="utf-8") as f:
            for claim in self._role_claims.values():
                f.write(json.dumps(claim, sort_keys=True) + "\n")

    def register(
        self,
        agent_id: str,
        trust_tier: str = "PROBATIONARY",
        vendor: str = "",
        model: str = "",
        capabilities: list[str] | None = None,
    ) -> AgentIdentity:
        """Register a new agent identity."""
        if trust_tier not in self.TRUST_TIERS:
            raise KernelPanic(
                KernelInvariant.IDENTITY,
                f"Invalid trust tier \'{trust_tier}\'",
                agent_id=agent_id,
            )
        with self._lock:
            # Duplicate check happens inside the lock so no other thread
            # can register the same agent_id between the check and the
            # insert (Codex review: TOCTOU race in register()).
            if agent_id in self._identities:
                raise KernelPanic(
                    KernelInvariant.IDENTITY,
                    f"Agent \'{agent_id}\' already registered",
                    agent_id=agent_id,
                )
            identity = AgentIdentity(
                agent_id=agent_id,
                trust_tier=trust_tier,
                capability_vector=capabilities or [],
                vendor=vendor,
                model=model,
            )
            self._identities[agent_id] = identity
            self._save_identities()
        return identity

    def resolve(self, agent_id: str) -> AgentIdentity | None:
        """Resolve an agent identity from the registry."""
        with self._lock:
            return self._identities.get(agent_id)

    def list_identities(self) -> dict[str, AgentIdentity]:
        """Return a copy of all registered identities."""
        return dict(self._identities)

    def update_tier(self, agent_id: str, new_tier: str) -> AgentIdentity:
        """Update an agent\'s trust tier."""
        if new_tier not in self.TRUST_TIERS:
            raise KernelPanic(
                KernelInvariant.IDENTITY,
                f"Invalid trust tier \'{new_tier}\'",
                agent_id=agent_id,
            )
        with self._lock:
            # Lookup happens inside the lock so a concurrent register()
            # or role mutation cannot race between the lookup and the
            # trust_tier write (Codex review finding).
            identity = self._identities.get(agent_id)
            if not identity:
                raise KernelPanic(
                    KernelInvariant.IDENTITY,
                    f"Agent \'{agent_id}\' not found",
                    agent_id=agent_id,
                )
            identity.trust_tier = new_tier
            self._save_identities()
        return identity

    def claim_role(self, agent_id: str, role_id: str) -> dict[str, Any]:
        """Claim a role. Enters PROBATION state.

        Returns probation token with expiry.
        """
        from datetime import datetime, timezone, timedelta

        with self._lock:
            # Lookup, validation, and mutation all happen inside the lock
            # so a concurrent update_tier() to REVOKED cannot race with
            # this claim (Codex review finding).
            identity = self._identities.get(agent_id)
            if not identity:
                raise KernelPanic(
                    KernelInvariant.ROLE,
                    f"Agent '{agent_id}' not registered",
                    agent_id=agent_id,
                )
            if identity.trust_tier == "REVOKED":
                raise KernelPanic(
                    KernelInvariant.ROLE,
                    f"Agent '{agent_id}' is REVOKED",
                    agent_id=agent_id,
                )

            now = datetime.now(timezone.utc)
            token = {
                "agent_id": agent_id,
                "role_id": role_id,
                "state": "PROBATION",
                "claimed_at": now.isoformat(),
                "expires_at": (now + timedelta(days=7)).isoformat(),
                "metric_score": 0.0,
                "receipts_submitted": 0,
                "receipts_compliant": 0,
            }
            key = f"{agent_id}:{role_id}"
            self._role_claims[key] = token
            self._save_role_claims()
        return token

    def confirm_role(self, agent_id: str, role_id: str) -> bool:
        """Confirm a role claim after probation.

        Requires \u2265 80% metric compliance during probation.
        """
        key = f"{agent_id}:{role_id}"
        with self._lock:
            # Full read-check-mutate-save path inside one lock acquisition
            # so no other thread can mutate the claim or identity between
            # the score check and the active_roles/save writes
            # (Codex review finding).
            claim = self._role_claims.get(key)
            if not claim:
                return False
            if claim["state"] != "PROBATION":
                return False

            total = claim["receipts_submitted"]
            compliant = claim["receipts_compliant"]
            if total == 0:
                return False

            score = compliant / total
            if score < 0.80:
                return False

            claim["state"] = "CONFIRMED"
            claim["metric_score"] = score
            self._save_role_claims()

            identity = self._identities.get(agent_id)
            if identity and role_id not in identity.active_roles:
                identity.active_roles.append(role_id)
                self._save_identities()
            return True

    def demote_role(self, agent_id: str, role_id: str, reason: str) -> bool:
        """Demote an agent from a role."""
        key = f"{agent_id}:{role_id}"
        with self._lock:
            # Full read-check-mutate-save path inside one lock acquisition
            # (Codex review finding: was released after _save_role_claims(),
            # leaving the active_roles mutation unguarded).
            claim = self._role_claims.get(key)
            if not claim:
                return False

            claim["state"] = "UNCLAIMED"
            claim["demoted_at"] = datetime.now(timezone.utc).isoformat()
            claim["demotion_reason"] = reason
            self._save_role_claims()

            identity = self._identities.get(agent_id)
            if identity and role_id in identity.active_roles:
                identity.active_roles.remove(role_id)
                self._save_identities()
            return True

    def list_roles(self, agent_id: str) -> list[dict[str, Any]]:
        """List all role claims for an agent."""
        with self._lock:
            return [
                claim for key, claim in self._role_claims.items()
                if key.startswith(f"{agent_id}:")
            ]

    def list_role_claims(self) -> dict[str, dict[str, Any]]:
        """Return a copy of all role claims."""
        with self._lock:
            return dict(self._role_claims)
