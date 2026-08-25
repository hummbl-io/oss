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

"""Agent Identity Registry -- Configurable agent identity, aliases, and trust tiers.

Provides a generic agent registry for multi-agent systems. Agents have
canonical names, display names, trust tiers, and status. Aliases map
variant identifiers to canonical names.

Usage:
    from hummbl_governance import AgentRegistry

    registry = AgentRegistry()
    registry.register_agent("orchestrator", display="Orchestrator", trust="high")
    registry.register_agent("worker", display="Worker", trust="medium")
    registry.add_alias("worker-1", "worker")
    registry.add_alias("worker-2", "worker")

    canonical = registry.canonicalize("worker-1")  # -> "worker"
    tier = registry.get_trust_tier("worker-1")      # -> "medium"

Stdlib-only. Zero third-party dependencies.
"""

from __future__ import annotations

import threading
from enum import Enum
from typing import Any


class TrustTier(Enum):
    """Normalized trust tiers for agent identities.

    Ordered from most to least privileged:
        OWNER > SYSTEM > HIGH > MEDIUM > LOW
    """

    OWNER = "owner"
    SYSTEM = "system"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

    @classmethod
    def from_str(cls, value: str) -> "TrustTier":
        """Parse a trust tier string (case-insensitive)."""
        try:
            return cls(value.lower().strip())
        except ValueError as exc:
            raise ValueError(
                f"Invalid trust tier {value!r}. "
                f"Expected one of: {', '.join(t.value for t in cls)}"
            ) from exc


class AgentRegistry:
    """Configurable agent identity registry.

    Manages canonical agent identities, aliases, autonomous services,
    deprecated identities, and retired agents.

    Args:
        agents: Initial dict of canonical agents.
            Format: {"name": {"display": "...", "trust": "...", "status": "..."}}
        aliases: Initial dict of alias -> canonical name mappings.
        services: Initial set of autonomous service names.
        deprecated: Initial set of deprecated/junk identity names.
        retired: Initial dict of retired agent -> reason mappings.
    """

    def __init__(
        self,
        agents: dict[str, dict[str, str]] | None = None,
        aliases: dict[str, str] | None = None,
        services: set[str] | None = None,
        deprecated: set[str] | None = None,
        retired: dict[str, str] | None = None,
    ):
        self._agents: dict[str, dict[str, str]] = dict(agents) if agents else {}
        self._aliases: dict[str, str] = dict(aliases) if aliases else {}
        self._services: set[str] = set(services) if services else set()
        self._deprecated: set[str] = set(deprecated) if deprecated else set()
        self._retired: dict[str, str] = dict(retired) if retired else {}
        self._lock = threading.Lock()

    def register_agent(
        self,
        name: str,
        display: str | None = None,
        trust: str | TrustTier = "medium",
        status: str = "active",
    ) -> None:
        """Register a canonical agent identity.

        Args:
            name: Canonical agent name (lowercase recommended).
            display: Human-readable display name (defaults to name.title()).
            trust: Trust tier (e.g., "owner", "high", "medium", "low", "system").
                Invalid values raise ValueError.
            status: Agent status (e.g., "active", "probation", "suspended").
        """
        if isinstance(trust, str):
            trust = TrustTier.from_str(trust)
        elif not isinstance(trust, TrustTier):
            raise TypeError(
                f"trust must be a string or TrustTier, got {type(trust).__name__}"
            )
        with self._lock:
            self._agents[name] = {
                "display": display or name.title(),
                "trust": trust.value,
                "status": status,
            }

    def unregister_agent(self, name: str) -> None:
        """Remove a canonical agent identity."""
        with self._lock:
            self._agents.pop(name, None)

    def add_alias(self, alias: str, canonical: str) -> None:
        """Map an alias to a canonical agent name.

        Raises:
            ValueError: If the alias would create a cycle.
        """
        with self._lock:
            # Check for direct cycle: alias pointing to itself
            if alias == canonical:
                raise ValueError(f"Alias cannot point to itself: {alias!r}")
            # Check for indirect cycle: would following aliases loop back?
            visited = {alias}
            current = canonical
            while current in self._aliases:
                current = self._aliases[current]
                if current in visited:
                    raise ValueError(
                        f"Alias cycle detected: adding {alias!r} -> {canonical!r} "
                        f"would create a loop"
                    )
                visited.add(current)
            self._aliases[alias] = canonical

    def remove_alias(self, alias: str) -> None:
        """Remove an alias mapping."""
        with self._lock:
            self._aliases.pop(alias, None)

    def add_service(self, name: str) -> None:
        """Register an autonomous service as a valid sender."""
        with self._lock:
            self._services.add(name)

    def remove_service(self, name: str) -> None:
        """Unregister an autonomous service."""
        with self._lock:
            self._services.discard(name)

    def add_deprecated(self, name: str) -> None:
        """Mark an identity as deprecated/junk."""
        with self._lock:
            self._deprecated.add(name)

    def retire_agent(self, name: str, reason: str) -> None:
        """Retire an agent with a reason."""
        with self._lock:
            self._retired[name] = reason

    def canonicalize(self, sender: str) -> str:
        """Map a sender to its canonical identity.

        Resolution order:
        1. Direct alias match (exact, then case-insensitive)
        2. Base name (before parenthetical) alias match
        3. Autonomous service match
        4. Canonical agent match
        5. Returns original sender if unknown

        Alias resolution is bounded to 50 steps to prevent infinite loops.
        """
        sender = sender.strip()
        if not sender:
            return sender

        # Base name (strip parenthetical)
        base = sender.split("(", 1)[0].strip() if "(" in sender else sender
        candidates = [sender, base] if base != sender else [sender]

        with self._lock:
            # 1. Alias lookup (with cycle guard)
            result = self._lookup_alias(candidates)
            if result is not None:
                return result

            # 2. Set membership lookup (services, then agents)
            result = self._lookup_in_set(candidates, self._services)
            if result is not None:
                return result
            result = self._lookup_in_set(candidates, self._agents)
            if result is not None:
                return result

        return sender

    @staticmethod
    def _lookup_in_set(candidates: list[str], registry: dict | set) -> str | None:
        """Find the first candidate present in a registry (exact or case-insensitive)."""
        for name in candidates:
            if name in registry:
                return name
            if name.lower() in registry:
                return name.lower()
        return None

    def _lookup_alias(self, candidates: list[str]) -> str | None:
        """Find the first candidate that matches an alias (exact or case-insensitive).

        Follows alias chains up to 50 steps to prevent infinite loops.
        """
        for name in candidates:
            current = name
            steps = 0
            while steps < 50:
                # Direct match
                if current in self._aliases:
                    current = self._aliases[current]
                    steps += 1
                    continue
                # Case-insensitive match
                current_lower = current.lower()
                if current_lower in self._aliases:
                    current = self._aliases[current_lower]
                    steps += 1
                    continue
                # Search all aliases for case-insensitive match
                found = None
                for alias_key, canonical in self._aliases.items():
                    if alias_key.lower() == current_lower:
                        found = canonical
                        break
                if found is not None:
                    current = found
                    steps += 1
                    continue
                # No alias match — if current is a known agent/service, return it
                if current in self._agents or current in self._services:
                    return current
                # No match for this candidate — try next candidate
                break
            else:
                # Step limit exceeded — break potential cycle, try next candidate
                continue
        return None

    def is_valid_sender(self, sender: str) -> bool:
        """Check if a sender is a known identity."""
        sender = sender.strip()
        with self._lock:
            if (
                sender in self._agents
                or sender in self._aliases
                or sender in self._services
            ):
                return True
        canonical = self.canonicalize(sender)
        # canonicalize returns None for unknown senders — guard against
        # the fallthrough where None != sender evaluates to True.
        if canonical is None:
            return False
        return canonical != sender


    def is_deprecated(self, sender: str) -> bool:
        """Check if a sender is a known deprecated/junk identity."""
        return sender.strip() in self._deprecated

    def get_trust_tier(self, sender: str) -> str:
        """Get trust tier for a sender. Returns 'unknown' for unrecognized."""
        canonical = self.canonicalize(sender)
        if canonical in self._agents:
            return self._agents[canonical]["trust"]
        if canonical in self._services:
            return "system"
        return "unknown"

    def get_status(self, sender: str) -> str:
        """Return registry status for a sender."""
        canonical = self.canonicalize(sender)
        if canonical in self._agents:
            return self._agents[canonical]["status"]
        if canonical in self._services:
            return "active"
        stripped = sender.strip()
        if canonical in self._retired or stripped in self._retired:
            return "retired"
        if self.is_deprecated(sender):
            return "deprecated"
        return "unknown"

    def get_known_senders(self) -> set[str]:
        """Return the set of all known sender identifiers."""
        known = set(self._agents)
        known.update(self._aliases)
        known.update(self._services)
        known.update(self._retired)
        return known

    def get_agents(self) -> dict[str, dict[str, str]]:
        """Return a copy of the canonical agents dict."""
        return dict(self._agents)

    def get_aliases(self) -> dict[str, str]:
        """Return a copy of the aliases dict."""
        return dict(self._aliases)

    def to_dict(self) -> dict[str, Any]:
        """Serialize registry to dictionary."""
        return {
            "agents": dict(self._agents),
            "aliases": dict(self._aliases),
            "services": sorted(self._services),
            "deprecated": sorted(self._deprecated),
            "retired": dict(self._retired),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AgentRegistry:
        """Deserialize registry from dictionary."""
        return cls(
            agents=data.get("agents"),
            aliases=data.get("aliases"),
            services=set(data.get("services", [])),
            deprecated=set(data.get("deprecated", [])),
            retired=data.get("retired"),
        )
