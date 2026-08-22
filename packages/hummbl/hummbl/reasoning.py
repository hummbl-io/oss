"""Core reasoning engine — data structures and trace management.

The fundamental abstraction: reasoning is a sequence of typed steps
organized in a topology (chain, tree, or graph). Each step has a type
that constrains what it does, and traces capture the full history of
a reasoning process for inspection, replay, and learning.
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ReasoningTopology(Enum):
    """How reasoning steps relate to each other.

    CHAIN: Linear progression. Each step follows the previous.
           Good for well-defined procedures (scientific method, checklists).

    TREE:  Branching exploration. A step can spawn multiple children,
           which are evaluated and pruned. Good for hypothesis generation,
           search, and decision-making under uncertainty.

    GRAPH: Networked reasoning. Steps can reference any prior step,
           forming cycles and cross-links. Good for iterative refinement,
           combining insights across branches, and meta-reasoning.
    """
    CHAIN = "chain"
    TREE = "tree"
    GRAPH = "graph"


class StepType(Enum):
    """The cognitive role of a reasoning step.

    These map to the fundamental operations of structured thinking:

    HYPOTHESIS:  A claim to be tested. "I think X will happen because Y."
    ACTION:      An intervention in the world. "Modify code." "Run experiment."
    OBSERVATION: Raw data from the world. "val_bpb was 0.82." "Test failed."
    EVALUATION:  Judgment about observations. "This is better than baseline."
    DECISION:    A commitment to act. "Keep this change." "Discard and revert."
    REFLECTION:  Meta-reasoning about the process itself. "My hypotheses
                 about depth have been wrong — I should try width instead."
    """
    HYPOTHESIS = "hypothesis"
    ACTION = "action"
    OBSERVATION = "observation"
    EVALUATION = "evaluation"
    DECISION = "decision"
    REFLECTION = "reflection"


@dataclass
class ReasoningStep:
    """A single step in a reasoning trace.

    Each step has a type that constrains its role, content that describes
    what it does, and structural links (parent/children) that define its
    position in the trace topology.

    Attributes:
        id: Unique identifier for this step.
        type: The cognitive role of this step (hypothesis, action, etc.).
        content: Human-readable description of what this step does/claims.
        parent_id: ID of the step that spawned this one (None for roots).
        children_ids: IDs of steps that branch from this one.
        metadata: Domain-specific data (metrics, file paths, config values).
        timestamp: Unix timestamp when this step was created.
        confidence: Optional confidence score [0.0, 1.0] for this step.
    """
    id: str
    type: StepType
    content: str
    parent_id: Optional[str] = None
    children_ids: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    confidence: Optional[float] = None

    def to_dict(self) -> dict:
        """Serialize to a plain dictionary."""
        return {
            "id": self.id,
            "type": self.type.value,
            "content": self.content,
            "parent_id": self.parent_id,
            "children_ids": self.children_ids,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "confidence": self.confidence,
        }

    @classmethod
    def from_dict(cls, data: dict) -> ReasoningStep:
        """Deserialize from a plain dictionary."""
        return cls(
            id=data["id"],
            type=StepType(data["type"]),
            content=data["content"],
            parent_id=data.get("parent_id"),
            children_ids=data.get("children_ids", []),
            metadata=data.get("metadata", {}),
            timestamp=data.get("timestamp", 0.0),
            confidence=data.get("confidence"),
        )


@dataclass
class ReasoningTrace:
    """A complete reasoning trace — the full record of a reasoning process.

    A trace captures the topology, all steps, and the outcome of a
    reasoning episode. Traces are the primary unit of inspection and
    learning in HUMMBL.

    Attributes:
        id: Unique identifier for this trace.
        topology: How steps are organized (chain, tree, graph).
        steps: Ordered list of all reasoning steps.
        outcome: Final result — "keep", "discard", "crash", or free-form.
        domain: The reasoning domain ("autoresearch", "peptide_qa", etc.).
        created_at: Unix timestamp when the trace was started.
        tags: Free-form tags for filtering and grouping traces.
    """
    id: str
    topology: ReasoningTopology
    steps: list[ReasoningStep] = field(default_factory=list)
    outcome: Optional[str] = None
    domain: str = ""
    created_at: float = field(default_factory=time.time)
    tags: list[str] = field(default_factory=list)

    # -- Step index for fast lookups --
    _step_index: dict[str, int] = field(
        default_factory=dict, init=False, repr=False
    )

    def __post_init__(self):
        """Build the step index after initialization."""
        self._rebuild_index()

    def _rebuild_index(self):
        """Rebuild the step-id-to-position index."""
        self._step_index = {step.id: i for i, step in enumerate(self.steps)}

    # -- Core operations --

    def add_step(self, step: ReasoningStep) -> None:
        """Add a step to the trace, maintaining structural integrity.

        If the step has a parent_id, the parent's children_ids list is
        updated automatically.

        Raises:
            ValueError: If a step with this ID already exists.
            KeyError: If the parent_id references a nonexistent step.
        """
        if step.id in self._step_index:
            raise ValueError(f"Step '{step.id}' already exists in trace")

        if step.parent_id is not None:
            if step.parent_id not in self._step_index:
                raise KeyError(
                    f"Parent step '{step.parent_id}' not found in trace"
                )
            parent = self.steps[self._step_index[step.parent_id]]
            if step.id not in parent.children_ids:
                parent.children_ids.append(step.id)

        self._step_index[step.id] = len(self.steps)
        self.steps.append(step)

    def get_step(self, step_id: str) -> ReasoningStep:
        """Retrieve a step by ID.

        Raises:
            KeyError: If no step with this ID exists.
        """
        if step_id not in self._step_index:
            raise KeyError(f"Step '{step_id}' not found in trace")
        return self.steps[self._step_index[step_id]]

    def get_path(self, step_id: str) -> list[ReasoningStep]:
        """Get the full path from root to the given step.

        Walks parent_id links backward to reconstruct the reasoning
        chain that led to this step. Useful for understanding how
        a particular conclusion was reached.

        Returns:
            List of steps from root to the target step (inclusive).

        Raises:
            KeyError: If step_id is not found in the trace.
        """
        path = []
        current_id: Optional[str] = step_id

        while current_id is not None:
            step = self.get_step(current_id)
            path.append(step)
            current_id = step.parent_id

        path.reverse()
        return path

    def get_steps_by_type(self, step_type: StepType) -> list[ReasoningStep]:
        """Return all steps of a given type, in trace order."""
        return [s for s in self.steps if s.type == step_type]

    def get_root_steps(self) -> list[ReasoningStep]:
        """Return all root steps (steps with no parent)."""
        return [s for s in self.steps if s.parent_id is None]

    def get_leaf_steps(self) -> list[ReasoningStep]:
        """Return all leaf steps (steps with no children)."""
        return [s for s in self.steps if not s.children_ids]

    # -- Serialization --

    def to_json(self, indent: int = 2) -> str:
        """Serialize the full trace to JSON."""
        data = {
            "id": self.id,
            "topology": self.topology.value,
            "steps": [s.to_dict() for s in self.steps],
            "outcome": self.outcome,
            "domain": self.domain,
            "created_at": self.created_at,
            "tags": self.tags,
        }
        return json.dumps(data, indent=indent)

    @classmethod
    def from_json(cls, raw: str) -> ReasoningTrace:
        """Deserialize a trace from JSON.

        Rebuilds the full trace including step index.
        """
        data = json.loads(raw)
        steps = [ReasoningStep.from_dict(s) for s in data.get("steps", [])]
        trace = cls(
            id=data["id"],
            topology=ReasoningTopology(data["topology"]),
            steps=[],  # Will add via add_step for integrity checks
            outcome=data.get("outcome"),
            domain=data.get("domain", ""),
            created_at=data.get("created_at", 0.0),
            tags=data.get("tags", []),
        )
        # Bypass add_step validation during deserialization —
        # the data is already structurally consistent.
        trace.steps = steps
        trace._rebuild_index()
        return trace


# -- Factory helpers --

def make_step(
    step_type: StepType,
    content: str,
    parent_id: Optional[str] = None,
    metadata: Optional[dict] = None,
    confidence: Optional[float] = None,
) -> ReasoningStep:
    """Convenience factory for creating a reasoning step with a UUID."""
    return ReasoningStep(
        id=str(uuid.uuid4())[:8],
        type=step_type,
        content=content,
        parent_id=parent_id,
        metadata=metadata or {},
        confidence=confidence,
    )


def make_trace(
    domain: str,
    topology: ReasoningTopology = ReasoningTopology.CHAIN,
    tags: Optional[list[str]] = None,
) -> ReasoningTrace:
    """Convenience factory for creating an empty reasoning trace with a UUID."""
    return ReasoningTrace(
        id=str(uuid.uuid4())[:8],
        topology=topology,
        domain=domain,
        tags=tags or [],
    )
