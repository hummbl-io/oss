from __future__ import annotations

from dataclasses import dataclass
from dataclasses import fields as dc_fields
from typing import Any, Dict, Optional, Type, TypeVar

from .base import TypedTuple

T = TypeVar("T", bound="TraceArtifact")


@dataclass(frozen=True, slots=True, kw_only=True)
class TraceArtifact(TypedTuple):
    """Base for trace artifact records (pretraining / posttraining).

    Trace artifacts use a different envelope than governance tuples:
    artifact_type, lifecycle_stage, trace_source, trace_visibility,
    governance_status, payload (instead of tuple_data).
    """

    artifact_type: str = "reasoning_trace"
    lifecycle_stage: str = ""
    trace_source: str = ""
    trace_visibility: str = ""
    governance_status: str = ""

    @classmethod
    def _envelope_fields(cls) -> tuple[str, ...]:
        # Traces use artifact_type instead of tuple_type in their envelope,
        # but Layer 1 id and time are still present.
        return (
            "tuple_type",
            "id",
            "time",
            "artifact_type",
            "lifecycle_stage",
            "trace_source",
            "trace_visibility",
            "governance_status",
        )

    def to_dict(self) -> Dict[str, Any]:
        """Produce the canonical envelope + payload dict."""
        envelope: Dict[str, Any] = {}
        # Layer 1: id and time
        envelope["id"] = self.id
        envelope["time"] = self.time
        # Trace-specific envelope (artifact_type replaces tuple_type)
        trace_envelope = (
            "artifact_type",
            "lifecycle_stage",
            "trace_source",
            "trace_visibility",
            "governance_status",
        )
        for name in trace_envelope:
            val = getattr(self, name)
            if val is not None:
                envelope[name] = val
        data: Dict[str, Any] = {}
        for name in self._data_fields():
            val = getattr(self, name)
            if val is not None:
                data[name] = val
        envelope["payload"] = data
        return envelope

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        flat: Dict[str, Any] = {}
        envelope_names = set(cls._envelope_fields())
        for key, value in data.items():
            if key == "payload" and isinstance(value, dict):
                flat.update(value)
            elif key in envelope_names:
                flat[key] = value
        valid = {f.name for f in dc_fields(cls)}
        return cls(**{k: v for k, v in flat.items() if k in valid})


@dataclass(frozen=True, slots=True, kw_only=True)
class PretrainingTrace(TraceArtifact):
    """A reasoning trace artifact from the pretraining lifecycle stage.

    Schema: pretraining_trace.schema.json
    Required payload: objective, corpus_role
    """

    lifecycle_stage: str = "pretraining"
    objective: str = ""
    corpus_role: str = ""
    generator: Optional[str] = None
    filtering_notes: Optional[str] = None
    provenance_uri: Optional[str] = None
    safety_notes: Optional[str] = None
    # tuple_type not used for trace artifacts; artifact_type is used instead
    tuple_type: str = "PRETRAINING_TRACE"


@dataclass(frozen=True, slots=True, kw_only=True)
class PosttrainingTrace(TraceArtifact):
    """A reasoning trace artifact from a posttraining lifecycle stage.

    Schema: posttraining_trace.schema.json
    Required payload: objective, trace_role
    """

    objective: str = ""
    trace_role: str = ""
    judge: Optional[str] = None
    selected: Optional[bool] = None
    score: Optional[float] = None
    selection_rationale: Optional[str] = None
    tuple_type: str = "POSTTRAINING_TRACE"
