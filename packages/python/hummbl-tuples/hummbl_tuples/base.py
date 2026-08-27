from __future__ import annotations

import dataclasses
import hashlib
import json
import uuid
from dataclasses import dataclass, field, fields
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Type, TypeVar

T = TypeVar("T", bound="TypedTuple")


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _short_id() -> str:
    return str(uuid.uuid4())[:12]


def _sha256_hex(payload: str) -> str:
    """SHA-256 hex digest of a UTF-8 encoded string."""
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True, kw_only=True)
class TypedTuple:
    """Base class for all HUMMBL Typed Tuples (Layer 1).

    Layer 1 (universal): tuple_type, id, time, tuple_data
    Subclasses add Layer 2 (governance), Layer 3 (domain), Layer 4 (integrity).

    Tuples are immutable (frozen) and include a deterministic SHA-256 hash
    of their content for cryptographic integrity and chaining.
    """

    tuple_type: str
    id: str = field(default_factory=_short_id)
    time: str = field(default_factory=_utc_now)

    # -- serialisation helpers ------------------------------------------------

    @classmethod
    def _envelope_fields(cls) -> tuple[str, ...]:
        """Field names that belong in the top-level envelope."""
        return ("tuple_type", "id", "time")

    @classmethod
    def _data_fields(cls) -> tuple[str, ...]:
        """Field names that belong inside ``tuple_data``."""
        envelope = set(cls._envelope_fields())
        return tuple(f.name for f in fields(cls) if f.name not in envelope)

    def to_dict(self) -> Dict[str, Any]:
        """Produce the canonical envelope + tuple_data dict."""
        envelope: Dict[str, Any] = {}
        for name in self._envelope_fields():
            val = getattr(self, name)
            if val is not None:
                envelope[name] = val
        data: Dict[str, Any] = {}
        for name in self._data_fields():
            val = getattr(self, name)
            if val is not None:
                data[name] = val
        envelope["tuple_data"] = data
        return envelope

    def to_json(self) -> str:
        """Deterministic JSON representation for hashing.

        Canonical serialization per CANONICAL_SERIALIZATION_v1.md:
        - Compact separators (no whitespace)
        - Keys sorted by UTF-8 code point order
        - Non-ASCII emitted as raw UTF-8 (ensure_ascii=False)
        """
        return json.dumps(self.to_dict(), separators=(",", ":"), sort_keys=True, ensure_ascii=False)

    @property
    def hash(self) -> str:
        """SHA-256 hash of the tuple content.

        Per CANONICAL_SERIALIZATION_v1.md §5: excludes integrity-layer fields
        (previous_hash, args_hash, signature) so the hash is stable regardless
        of chaining state. Uses canonical serialization (compact, sorted, UTF-8).
        """
        d = self.to_dict()
        # Exclude integrity-layer fields from hash computation so that
        # the hash is stable regardless of chaining state.
        d.pop("previous_hash", None)
        d.pop("args_hash", None)
        d.pop("signature", None)
        stable_json = json.dumps(d, separators=(",", ":"), sort_keys=True, ensure_ascii=False)
        return _sha256_hex(stable_json)

    def with_chain(self, previous_hash: str | None) -> "TypedTuple":
        """Return a new tuple with ``previous_hash`` set to link it into a chain.

        This is an optional Layer 4 integrity operation. The returned tuple
        is a new frozen instance (the original is unchanged). If
        ``previous_hash`` is None, the chain link is cleared.

        Raises TypeError if the tuple class does not support ``previous_hash``.
        """
        if not hasattr(type(self), "previous_hash"):
            raise TypeError(
                f"{type(self).__name__} does not support hash chaining (no previous_hash field)"
            )
        updates: Dict[str, Any] = {}
        for f in fields(self):
            updates[f.name] = getattr(self, f.name)
        updates["previous_hash"] = previous_hash
        return type(self)(**updates)

    def verify_chain(self, predecessor_hash: str | None) -> bool:
        """Verify that ``self.previous_hash`` matches the given predecessor hash.

        Returns True if:
        - previous_hash is set and matches predecessor_hash, or
        - previous_hash is None and predecessor_hash is None (unchained)

        Returns False if the hashes don't match.
        Raises TypeError if the tuple class does not support previous_hash.
        """
        if not hasattr(type(self), "previous_hash"):
            raise TypeError(
                f"{type(self).__name__} does not support hash chaining (no previous_hash field)"
            )
        return getattr(self, "previous_hash") == predecessor_hash

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Create a tuple from an envelope + tuple_data dictionary.

        Accepts the canonical schema shape (top-level envelope keys plus a
        nested ``tuple_data`` object) and flattens it into keyword arguments
        for the dataclass constructor.

        Raises ValueError with field-level detail if input is invalid.
        """
        if not isinstance(data, dict):
            raise ValueError(f"{cls.__name__}.from_dict() expected dict, got {type(data).__name__}")
        flat: Dict[str, Any] = {}
        envelope_names = set(cls._envelope_fields())
        for key, value in data.items():
            if key == "tuple_data" and isinstance(value, dict):
                flat.update(value)
            elif key in envelope_names:
                flat[key] = value
        # Only pass keys that correspond to declared fields.
        valid = {f.name for f in fields(cls)}
        kwargs = {k: v for k, v in flat.items() if k in valid}
        # Check for required fields without defaults.
        for f in fields(cls):
            if f.default is f.default_factory is dataclasses.MISSING and f.name not in kwargs:
                raise ValueError(f"{cls.__name__}.from_dict(): missing required field '{f.name}'")
        return cls(**kwargs)


# ---------------------------------------------------------------------------
# Domain-specific envelope base classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True, kw_only=True)
class IDPTuple(TypedTuple):
    """Base for IDP governance tuples (Layer 1 + 2 + 3/IDP).

    Layer 2 (governance): state, drift, tier, agent, tool
    Layer 3 (IDP): intent_id, task_id
    Layer 4 (integrity): signature
    """

    # Layer 2 — Governance (VERUM-aligned)
    state: str = "ok"
    drift: float = 0.0
    tier: int = 1
    agent: str = ""
    tool: str = ""

    # Layer 3 — IDP domain
    intent_id: str = ""
    task_id: str = ""

    # Layer 4 — Integrity
    signature: Optional[str] = None
    previous_hash: Optional[str] = None

    @classmethod
    def _envelope_fields(cls) -> tuple[str, ...]:
        return (
            "tuple_type",
            "id",
            "time",
            "state",
            "drift",
            "tier",
            "agent",
            "tool",
            "intent_id",
            "task_id",
            "signature",
            "previous_hash",
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class BaseNTuple(TypedTuple):
    """Base for BaseN experiment tuples (Layer 1 + 3/BaseN).

    Layer 3 (BaseN): problem_id, run_id, control_mode
    No Layer 2 — research tuples are not governed.
    """

    problem_id: str = ""
    run_id: str = ""
    control_mode: str = ""

    @classmethod
    def _envelope_fields(cls) -> tuple[str, ...]:
        return ("tuple_type", "id", "time", "problem_id", "run_id", "control_mode")


@dataclass(frozen=True, slots=True, kw_only=True)
class NodezeroTuple(TypedTuple):
    """Base for Nodezero experiment-control tuples (Layer 1 + 3/Nodezero).

    Layer 3 (Nodezero): run_id
    """

    run_id: str = ""

    @classmethod
    def _envelope_fields(cls) -> tuple[str, ...]:
        return ("tuple_type", "id", "time", "run_id")


@dataclass(frozen=True, slots=True, kw_only=True)
class NodezeroExperimentTuple(NodezeroTuple):
    """Nodezero tuple that also carries a problem_id."""

    problem_id: str = ""

    @classmethod
    def _envelope_fields(cls) -> tuple[str, ...]:
        return ("tuple_type", "id", "time", "problem_id", "run_id")
