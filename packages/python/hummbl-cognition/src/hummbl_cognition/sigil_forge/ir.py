"""Typed intermediate representation for Sigil Forge programs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

ControlKind = Literal["node", "loop", "if"]


@dataclass(frozen=True)
class Condition:
    """A simple metric comparison used by IF blocks."""

    metric: str
    operator: str
    value: float | str | bool

    def evaluate(self, metrics: dict[str, Any]) -> bool:
        observed = metrics.get(self.metric)
        expected = self.value

        if self.operator in {"<", "<=", ">", ">="}:
            try:
                left = float(observed)
                right = float(expected)
            except (TypeError, ValueError):
                return False
            if self.operator == "<":
                return left < right
            if self.operator == "<=":
                return left <= right
            if self.operator == ">":
                return left > right
            return left >= right

        if self.operator == "==":
            return observed == expected
        if self.operator == "!=":
            return observed != expected
        raise ValueError(f"Unsupported condition operator: {self.operator}")


@dataclass(frozen=True)
class NodeSpec:
    """One executable operator in a compiled prompt program."""

    id: str
    type: str
    params: dict[str, Any] = field(default_factory=dict)
    role: str | None = None


@dataclass(frozen=True)
class EdgeSpec:
    """Directed data-flow edge between two nodes."""

    source: str
    target: str


@dataclass(frozen=True)
class Program:
    """Parsed AST node.

    The AST preserves control-flow structure. The compiler flattens concrete
    nodes into an execution plan while retaining loop and condition metadata.
    """

    kind: ControlKind
    operator: str | None = None
    params: dict[str, Any] = field(default_factory=dict)
    body: tuple["Program", ...] = ()
    else_body: tuple["Program", ...] = ()
    condition: Condition | None = None


@dataclass(frozen=True)
class ExecutionPlan:
    """Compiled representation consumed by the execution engine."""

    nodes: tuple[NodeSpec, ...]
    edges: tuple[EdgeSpec, ...]
    program: tuple[Program, ...]
    source: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "edges": [edge.__dict__ for edge in self.edges],
            "nodes": [
                {
                    "id": node.id,
                    "params": node.params,
                    "role": node.role,
                    "type": node.type,
                }
                for node in self.nodes
            ],
            "source": self.source,
        }
