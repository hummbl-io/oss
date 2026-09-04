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

"""Agent Registry Primitive (P44) — append-only JSONL tracking for fleet agents.

Two-axis taxonomy: ``status`` (lifecycle) orthogonal to ``sender_class``
(autonomy classification). Closes the roster-drift gap surfaced by WS-6:
``ROSTER.md`` and ``agent-roster.md`` become generated artifacts (WS-2/WS-3),
and drift is detected by comparing registry state against the markdown rosters.

Builds on two existing primitives:
    * ``model_registry.py``  — append-only JSONL record-store pattern.
    * ``canon_registry.py``  — lifecycle-transition + operator-approval gate.

Status axis (lifecycle):
    candidate_pending -> active_bootstrap -> active
    active -> active_aip (research lane)
    active -> dormant (outage); dormant -> active (recovery, K10)
    any -> retired (terminal)
    any -> superseded (terminal; requires ``superseded_by``)

Sender-class axis (autonomy, orthogonal to status):
    autonomous_llm            — devin, codex, hermes, pi, ...
    simulation_gated_service  — purple/red/blue-team (code modules)
    non_sender                — candidates (agy, deepseek), retired, superseded

Usage:
    from hummbl_governance.kernel.agent_registry import AgentRegistry, AgentStatus

    reg = AgentRegistry()
    reg.register(
        agent_id="pi",
        display_name="Pi CLI (compound-engineering plugin host)",
        status=AgentStatus.ACTIVE,
        sender_class="autonomous_llm",
        trust_class="medium_high",
        role="Ops/remediation executor, research-ingest surface",
        default_model="nvidia/nemotron-3-ultra-550b-a55b",
        guardrail_path="rules/pi-guardrails.md",
        profile_path="agents/pi.md",
        hosts=["anvil", "hummbl_vps"],
    )

    agents = reg.list_agents()
    active = reg.find(status=AgentStatus.ACTIVE)
    pi = reg.get("pi")
    drift = reg.detect_roster_drift(roster_path="ROSTER.md")
"""

from __future__ import annotations

import json
import logging
import os
import re
import tempfile
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from .invariants import KernelInvariant, KernelPanic
from hummbl_governance.schema_validator import SchemaValidator, ValidationError

logger = logging.getLogger(__name__)

SCHEMA_VERSION = "1.0.0"
_SCHEMA_PATH = Path(__file__).parent.parent / "data" / "agent_registry.schema.json"
_SCHEMA_CACHE: dict[str, Any] | None = None


class AgentStatus(str, Enum):
    """Lifecycle status axis (sequential promotion + terminal states)."""

    CANDIDATE_PENDING = "candidate_pending"
    ACTIVE_BOOTSTRAP = "active_bootstrap"
    ACTIVE = "active"
    ACTIVE_AIP = "active_aip"
    DORMANT = "dormant"
    RETIRED = "retired"
    SUPERSEDED = "superseded"


class SenderClass(str, Enum):
    """Autonomy classification axis, orthogonal to status."""

    AUTONOMOUS_LLM = "autonomous_llm"
    SIMULATION_GATED_SERVICE = "simulation_gated_service"
    NON_SENDER = "non_sender"


# Forward promotion transitions (sequential, single destination per source).
_FORWARD_TRANSITIONS: dict[str, str] = {
    AgentStatus.CANDIDATE_PENDING.value: AgentStatus.ACTIVE_BOOTSTRAP.value,
    AgentStatus.ACTIVE_BOOTSTRAP.value: AgentStatus.ACTIVE.value,
}

# Non-sequential transitions allowed from ACTIVE-family states.
# Multi-map: a source state may transition to more than one destination
# (e.g. active -> active_aip OR active -> dormant). A plain dict would
# silently collapse duplicate keys, losing transitions.
_ACTIVE_TRANSITIONS: dict[str, frozenset[str]] = {
    AgentStatus.ACTIVE.value: frozenset({
        AgentStatus.ACTIVE_AIP.value,
        AgentStatus.DORMANT.value,
    }),
    AgentStatus.ACTIVE_AIP.value: frozenset({
        AgentStatus.ACTIVE.value,
        AgentStatus.DORMANT.value,
    }),
    AgentStatus.DORMANT.value: frozenset({AgentStatus.ACTIVE.value}),
}

# Terminal states — no forward transition out.
_TERMINAL = {AgentStatus.RETIRED.value, AgentStatus.SUPERSEDED.value}

# Statuses that require operator approval to enter (D5 NO_AUTO_PROMOTION).
_PROMOTION_GATE = {
    AgentStatus.ACTIVE_BOOTSTRAP.value,
    AgentStatus.ACTIVE.value,
    AgentStatus.ACTIVE_AIP.value,
}


@dataclass
class AgentEntry:
    """A single agent registration record."""

    schema_version: str
    agent_id: str
    timestamp: str
    display_name: str
    status: str
    sender_class: str
    trust_class: str
    role: str
    default_model: str = ""
    guardrail_path: str = ""
    profile_path: str = ""
    hosts: list[str] = field(default_factory=list)
    mesh_scope: str = ""
    promoted_at: str = ""
    superseded_by: str = ""
    parent_id: str = ""
    notes: str = ""
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> AgentEntry:
        # Tolerate missing optional fields by filtering to known keys.
        known = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in d.items() if k in known}
        return cls(**filtered)


def _load_schema() -> dict[str, Any]:
    global _SCHEMA_CACHE
    if _SCHEMA_CACHE is None:
        with open(_SCHEMA_PATH, encoding="utf-8") as f:
            _SCHEMA_CACHE = json.load(f)
    return _SCHEMA_CACHE


def validate_agent_entry(entry: dict[str, Any]) -> None:
    """Validate an agent entry dict against the JSON schema.

    Raises:
        ValidationError: If the entry does not conform to the schema.
    """
    schema = _load_schema()
    errors = SchemaValidator.validate(entry, schema)
    if errors:
        raise ValidationError(
            f"Agent registry schema validation failed: {'; '.join(errors)}"
        )


def validate_transition(current: str, proposed: str) -> None:
    """Validate that a status transition is allowed.

    Raises:
        ValueError: If the transition is not valid.
    """
    if current == proposed:
        raise ValueError(
            f"Agent transition rejected: current and proposed are both '{current}'"
        )

    if current in _TERMINAL:
        raise ValueError(
            f"Agent transition rejected: '{current}' is terminal "
            f"(retired/superseded have no forward transition)"
        )

    if proposed in _TERMINAL:
        # Retirement/supersession allowed from any non-terminal state.
        return

    # Forward (sequential) transitions take precedence — a state in both
    # maps follows its single forward destination.
    forward = _FORWARD_TRANSITIONS.get(current)
    if forward is not None:
        if proposed == forward:
            return
        raise ValueError(
            f"Agent transition rejected: '{current}' -> '{proposed}' "
            f"(expected '{current}' -> '{forward}')"
        )

    allowed = _ACTIVE_TRANSITIONS.get(current)
    if allowed is None:
        raise ValueError(
            f"Agent transition rejected: no forward transition from '{current}'"
        )
    if proposed not in allowed:
        raise ValueError(
            f"Agent transition rejected: '{current}' -> '{proposed}' "
            f"(allowed from '{current}': {sorted(allowed)})"
        )


def validate_promotion_gate(
    current: str, proposed: str, operator_approval: bool, approver_id: str
) -> None:
    """Enforce D5 (NO_AUTO_PROMOTION) for status promotions.

    Promotions into active_bootstrap, active, or active_aip require explicit
    operator approval with a non-empty approver_id.

    Raises:
        ValueError: If the promotion gate is not satisfied.
    """
    if proposed not in _PROMOTION_GATE:
        return
    if not operator_approval:
        raise ValueError(
            f"Agent promotion rejected: D5 (NO_AUTO_PROMOTION) violation — "
            f"operator_approval must be True for '{current}' -> '{proposed}'"
        )
    if not approver_id or not isinstance(approver_id, str):
        raise ValueError(
            "Agent promotion rejected: approver_id must be a non-empty string"
        )


def validate_supersession(entry: AgentEntry) -> None:
    """Validate that superseded entries declare a successor.

    Raises:
        ValueError: If status is superseded but superseded_by is empty.
    """
    if entry.status == AgentStatus.SUPERSEDED.value and not entry.superseded_by:
        raise ValueError(
            f"Agent entry '{entry.agent_id}' is superseded but "
            f"superseded_by is empty"
        )


class AgentRegistry:
    """Append-only agent registry backed by JSONL.

    Each register() call appends one line. ``get()`` returns the latest record
    for an agent_id (the registry is append-only, so history is preserved).
    """

    def __init__(self, registry_path: str | None = None) -> None:
        using_default = registry_path is None
        if registry_path is None:
            registry_path = str(default_registry_path())
        self.registry_path = Path(registry_path)
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        seed = package_seed_registry_path()
        if using_default and not self.registry_path.exists() and seed.exists():
            tmp_fd, tmp_name = tempfile.mkstemp(
                dir=self.registry_path.parent, suffix=".tmp"
            )
            try:
                with os.fdopen(tmp_fd, "wb") as tmp_f:
                    tmp_f.write(seed.read_bytes())
                os.replace(tmp_name, self.registry_path)
            except FileExistsError:
                if Path(tmp_name).exists():
                    os.unlink(tmp_name)
            except OSError:
                if Path(tmp_name).exists():
                    os.unlink(tmp_name)
                raise

    def register(self, **kwargs: Any) -> AgentEntry:
        """Register a new agent entry. Returns the entry.

        Validates against schema and supersession rules before appending.

        Raises:
            ValidationError: If schema validation fails.
            ValueError: If supersession validation fails.
        """
        if "schema_version" not in kwargs:
            kwargs["schema_version"] = SCHEMA_VERSION
        if "timestamp" not in kwargs:
            kwargs["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        # Coerce enum values to strings for schema validation.
        if isinstance(kwargs.get("status"), AgentStatus):
            kwargs["status"] = kwargs["status"].value
        if isinstance(kwargs.get("sender_class"), SenderClass):
            kwargs["sender_class"] = kwargs["sender_class"].value
        entry = AgentEntry(**kwargs)
        validate_agent_entry(entry.to_dict())
        validate_supersession(entry)
        with open(self.registry_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")
        return entry

    def list_agents(self) -> list[AgentEntry]:
        """Return all registered agent records (full history).

        Fail-closed: corrupted lines raise KernelPanic (K11 INTEGRITY) rather
        than being silently dropped, matching model_registry.py convention.
        """
        entries: list[AgentEntry] = []
        if not self.registry_path.exists():
            return entries
        with open(self.registry_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(AgentEntry.from_dict(json.loads(line)))
                except (json.JSONDecodeError, TypeError) as exc:
                    logger.error(
                        "Corrupted agent registry line in %s: %s",
                        self.registry_path, line[:100],
                    )
                    raise KernelPanic(
                        KernelInvariant.INTEGRITY,
                        f"Corrupted agent registry line in "
                        f"{self.registry_path}: {line[:100]!r} — "
                        f"refusing to silently drop agent entry",
                    ) from exc
        return entries

    def latest(self) -> dict[str, AgentEntry]:
        """Return a dict of agent_id -> latest entry (deduplicates history)."""
        result: dict[str, AgentEntry] = {}
        for entry in self.list_agents():
            existing = result.get(entry.agent_id)
            if existing is None or entry.timestamp >= existing.timestamp:
                result[entry.agent_id] = entry
        return result

    def find(
        self,
        status: AgentStatus | str | None = None,
        sender_class: SenderClass | str | None = None,
        trust_class: str | None = None,
        host: str | None = None,
        tag: str | None = None,
    ) -> list[AgentEntry]:
        """Find agents matching criteria (against latest entries only)."""
        status_val = status.value if isinstance(status, AgentStatus) else status
        sc_val = (
            sender_class.value if isinstance(sender_class, SenderClass) else sender_class
        )
        results: list[AgentEntry] = []
        for entry in self.latest().values():
            if status_val is not None and entry.status != status_val:
                continue
            if sc_val is not None and entry.sender_class != sc_val:
                continue
            if trust_class is not None and entry.trust_class != trust_class:
                continue
            if host is not None and host not in entry.hosts:
                continue
            if tag is not None and tag not in entry.tags:
                continue
            results.append(entry)
        return results

    def get(self, agent_id: str) -> AgentEntry | None:
        """Get the latest entry for an agent_id."""
        return self.latest().get(agent_id)

    def lineage(self, agent_id: str) -> list[AgentEntry]:
        """Trace lineage from an agent back to ancestors via parent_id."""
        entries = self.latest()
        chain: list[AgentEntry] = []
        current = entries.get(agent_id)
        while current is not None:
            chain.append(current)
            current = (
                entries.get(current.parent_id) if current.parent_id else None
            )
        return list(reversed(chain))

    def promote(
        self,
        agent_id: str,
        proposed: AgentStatus | str,
        operator_approval: bool,
        approver_id: str,
        **overrides: Any,
    ) -> AgentEntry:
        """Promote an agent to a new status with operator approval (D5).

        Validates the transition, the promotion gate, then appends a new
        entry with the proposed status and a promoted_at timestamp.

        Raises:
            ValueError: If the agent is not found, the transition is invalid,
                or the promotion gate is not satisfied.
            ValidationError: If schema validation fails on the new entry.
        """
        current = self.get(agent_id)
        if current is None:
            raise ValueError(f"Agent promotion rejected: '{agent_id}' not found")

        proposed_val = (
            proposed.value if isinstance(proposed, AgentStatus) else proposed
        )
        validate_transition(current.status, proposed_val)
        validate_promotion_gate(
            current.status, proposed_val, operator_approval, approver_id
        )

        new_entry = current.to_dict()
        new_entry["status"] = proposed_val
        new_entry["timestamp"] = time.strftime(
            "%Y-%m-%dT%H:%M:%SZ", time.gmtime()
        )
        new_entry["promoted_at"] = new_entry["timestamp"]
        if proposed_val == AgentStatus.SUPERSEDED.value and "superseded_by" in overrides:
            new_entry["superseded_by"] = overrides.pop("superseded_by")
        new_entry.update(overrides)
        # Re-register as a fresh entry (register() validates + appends).
        return self.register(**new_entry)

    def stats(self) -> dict[str, Any]:
        """Return registry statistics against latest entries."""
        latest = self.latest()
        if not latest:
            return {"count": 0}
        by_status: dict[str, int] = {}
        by_sender_class: dict[str, int] = {}
        for e in latest.values():
            by_status[e.status] = by_status.get(e.status, 0) + 1
            by_sender_class[e.sender_class] = (
                by_sender_class.get(e.sender_class, 0) + 1
            )
        return {
            "count": len(latest),
            "by_status": by_status,
            "by_sender_class": by_sender_class,
            "latest": max(latest.values(), key=lambda e: e.timestamp).agent_id,
        }

    # ------------------------------------------------------------------
    # Drift detection — compare registry state against a markdown roster.
    # ------------------------------------------------------------------

    # Matches the first column agent_id in a markdown table row like:
    #   | `pi` | Pi CLI ... | MEDIUM-HIGH | Active | ... |
    _ROSTER_ROW_RE = re.compile(
        r"^\s*\|\s*`([a-z][a-z0-9-]*)`\s*\|", re.MULTILINE
    )

    def detect_roster_drift(
        self, roster_path: str | Path
    ) -> list[dict[str, Any]]:
        """Detect drift between the registry and a markdown roster file.

        Returns a list of drift findings, each with keys:
            - ``kind``: "missing_in_registry" | "missing_in_roster" |
              "status_mismatch"
            - ``agent_id``: the affected agent_id
            - ``detail``: human-readable explanation

        The roster is parsed for agent_ids in backtick-wrapped table cells.
        Registry status is compared against a heuristic mapping of roster
        status text (Active, DORMANT, RETIRED, SUPERSEDED, Candidate).
        Agents present in one surface but not the other are reported.
        """
        roster_path = Path(roster_path)
        if not roster_path.exists():
            raise FileNotFoundError(f"Roster file not found: {roster_path}")

        roster_ids = self._extract_roster_agent_ids(roster_path)
        registry_latest = self.latest()
        registry_ids = set(registry_latest.keys())

        findings: list[dict[str, Any]] = []

        for agent_id in sorted(roster_ids - registry_ids):
            findings.append({
                "kind": "missing_in_registry",
                "agent_id": agent_id,
                "detail": (
                    f"Agent '{agent_id}' appears in roster {roster_path.name} "
                    f"but has no entry in the agent registry"
                ),
            })

        for agent_id in sorted(registry_ids - roster_ids):
            entry = registry_latest[agent_id]
            # Retired/superseded agents may legitimately be absent from the
            # active roster; only flag non-terminal agents as missing.
            if entry.status in _TERMINAL:
                continue
            findings.append({
                "kind": "missing_in_roster",
                "agent_id": agent_id,
                "detail": (
                    f"Agent '{agent_id}' is in the registry (status={entry.status}) "
                    f"but not in roster {roster_path.name}"
                ),
            })

        # Status mismatch: compare registry status against roster status text.
        roster_statuses = self._extract_roster_statuses(roster_path)
        for agent_id, roster_status in roster_statuses.items():
            entry = registry_latest.get(agent_id)
            if entry is None:
                continue
            expected = _roster_status_to_enum(roster_status)
            if expected is None:
                continue
            if entry.status != expected.value:
                findings.append({
                    "kind": "status_mismatch",
                    "agent_id": agent_id,
                    "detail": (
                        f"Registry status '{entry.status}' != roster status "
                        f"'{roster_status}' for '{agent_id}'"
                    ),
                })

        return findings

    def _extract_roster_agent_ids(self, roster_path: Path) -> set[str]:
        text = roster_path.read_text(encoding="utf-8")
        ids: set[str] = set()
        for match in self._ROSTER_ROW_RE.finditer(text):
            ids.add(match.group(1))
        return ids

    def _extract_roster_statuses(
        self, roster_path: Path
    ) -> dict[str, str]:
        """Extract agent_id -> raw status text from roster table rows.

        Parses markdown table rows with the canonical 5-column shape:
            | `agent_id` | display | trust | status | ... |
        The status column is the 4th column.
        """
        text = roster_path.read_text(encoding="utf-8")
        statuses: dict[str, str] = {}
        for line in text.splitlines():
            line = line.strip()
            if not line.startswith("|"):
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) < 4:
                continue
            id_match = re.match(r"`([a-z][a-z0-9-]*)`", cells[0])
            if not id_match:
                continue
            statuses[id_match.group(1)] = cells[3]
        return statuses

    # ------------------------------------------------------------------
    # Importer — bootstrap the registry from .agents/ frontmatter.
    # ------------------------------------------------------------------

    def import_from_agents_dir(
        self,
        agents_dir: str | Path,
        status_map: dict[str, tuple[str, str]] | None = None,
        dry_run: bool = False,
    ) -> list[AgentEntry]:
        """Import agent definitions from a ``.agents/agents/`` directory.

        Each ``*.md`` file is parsed for YAML frontmatter (``name``,
        ``description``, ``model``, ``tier``, ``persona``). The ``name``
        becomes the ``agent_id``; ``description`` becomes ``display_name``.

        Args:
            agents_dir: Path to the directory containing agent ``.md`` files.
            status_map: Optional mapping of agent_id ->
                (status, sender_class) to override defaults. Agents not in
                the map default to (candidate_pending, non_sender).
            dry_run: If True, validate entries but do not append to the
                registry. Returns the entries that would have been registered.

        Returns:
            List of AgentEntry objects registered (or that would be, if
            dry_run).
        """
        agents_dir = Path(agents_dir)
        if not agents_dir.is_dir():
            raise FileNotFoundError(f"Agents directory not found: {agents_dir}")

        status_map = status_map or {}
        entries: list[AgentEntry] = []

        for md_path in sorted(agents_dir.glob("*.md")):
            frontmatter = _parse_frontmatter(md_path)
            if not frontmatter or "name" not in frontmatter:
                continue
            agent_id = frontmatter["name"].strip().lower()
            if not re.match(r"^[a-z][a-z0-9-]*$", agent_id):
                continue  # skip non-canonical names

            status, sender_class = status_map.get(
                agent_id, (AgentStatus.CANDIDATE_PENDING.value, SenderClass.NON_SENDER.value)
            )
            display = frontmatter.get("description", agent_id).strip()
            entry_kwargs: dict[str, Any] = {
                "agent_id": agent_id,
                "display_name": display,
                "status": status,
                "sender_class": sender_class,
                "trust_class": _tier_to_trust(frontmatter.get("tier", "")),
                "role": display,
                "default_model": frontmatter.get("model", ""),
                "profile_path": str(md_path.relative_to(agents_dir)).replace("\\", "/"),
                "tags": [],
            }
            if "persona" in frontmatter:
                entry_kwargs["tags"] = [frontmatter["persona"]]

            if dry_run:
                entry = AgentEntry(
                    schema_version=SCHEMA_VERSION,
                    timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    **entry_kwargs,
                )
                validate_agent_entry(entry.to_dict())
                entries.append(entry)
            else:
                entries.append(self.register(**entry_kwargs))

        return entries


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

def _parse_frontmatter(path: Path) -> dict[str, str]:
    """Parse a simple YAML frontmatter block (key: value lines)."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    block = text[3:end].strip()
    result: dict[str, str] = {}
    for line in block.splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        key, _, value = line.partition(":")
        result[key.strip()] = value.strip().strip('"').strip("'")
    return result


def _tier_to_trust(tier: str) -> str:
    """Map a frontmatter ``tier`` value to a trust_class."""
    tier = tier.strip().lower()
    mapping = {
        "operational": "medium_high",
        "emerging": "probationary",
        "trusted": "trusted",
        "owner": "owner",
        "system": "trusted",
        "high": "trusted",
        "medium": "medium",
        "low": "low",
        "probationary": "probationary",
    }
    return mapping.get(tier, "probationary")


def _roster_status_to_enum(roster_status: str) -> AgentStatus | None:
    """Map a roster status cell text to an AgentStatus enum value.

    Returns None if the text does not match a known status (skip mismatch
    check for unrecognized text).
    """
    s = roster_status.strip().lower()
    if "superseded" in s:
        return AgentStatus.SUPERSEDED
    if "retired" in s:
        return AgentStatus.RETIRED
    if "dormant" in s:
        return AgentStatus.DORMANT
    if "candidate" in s or "pending" in s or "probationary" in s:
        return AgentStatus.CANDIDATE_PENDING
    if "bootstrap" in s:
        return AgentStatus.ACTIVE_BOOTSTRAP
    if "aip" in s:
        return AgentStatus.ACTIVE_AIP
    if s.startswith("active"):
        return AgentStatus.ACTIVE
    return None


def package_seed_registry_path() -> Path:
    """Return the package seed registry path (shipped with the package)."""
    here = Path(__file__).parent.parent
    return here / "data" / "registry" / "agents.jsonl"


def default_registry_path() -> Path:
    """Return the user-state default registry path for runtime writes."""
    configured = os.environ.get("HUMMBL_AGENT_REGISTRY_PATH")
    if configured:
        return Path(configured).expanduser()

    state_dir = os.environ.get("HUMMBL_KERNEL_STATE_DIR")
    if state_dir:
        return Path(state_dir).expanduser() / "agent_registry" / "agents.jsonl"

    state_root = os.environ.get("XDG_STATE_HOME") or os.environ.get("LOCALAPPDATA")
    if state_root:
        return (
            Path(state_root).expanduser()
            / "hummbl-governance"
            / "agent_registry"
            / "agents.jsonl"
        )

    return Path.home() / ".local" / "state" / "hummbl-governance" / "agent_registry" / "agents.jsonl"


__all__ = [
    "AgentEntry",
    "AgentStatus",
    "AgentRegistry",
    "SenderClass",
    "validate_agent_entry",
    "validate_transition",
    "validate_promotion_gate",
    "validate_supersession",
    "package_seed_registry_path",
    "default_registry_path",
    "SCHEMA_VERSION",
]
