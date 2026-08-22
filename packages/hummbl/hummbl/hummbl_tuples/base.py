from __future__ import annotations
import hashlib
import json
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Type, TypeVar

T = TypeVar("T", bound="TypedTuple")

@dataclass(frozen=True, slots=True, kw_only=True)
class TypedTuple:
    """Base class for all HUMMBL Typed Tuples.
    
    Tuples are immutable (frozen) and include a deterministic SHA-256 hash
    of their content for cryptographic integrity and chaining.
    """
    tuple_type: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    version: str = "v1"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert tuple to a dictionary, ensuring all values are serializable."""
        return asdict(self)

    def to_json(self) -> str:
        """Deterministic JSON representation for hashing."""
        return json.dumps(self.to_dict(), sort_keys=True)

    @property
    def hash(self) -> str:
        """SHA-256 hash of the tuple content."""
        return hashlib.sha256(self.to_json().encode("utf-8")).hexdigest()

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Create a tuple from a dictionary."""
        return cls(**data)
