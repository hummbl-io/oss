"""Capability gate for Sigil Forge execution plans."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum

from hummbl_cognition.sigil_forge.ir import ExecutionPlan, Program


class PolicyViolationError(PermissionError):
    """Raised when a DSL program exceeds its allowed authority."""


PolicyViolation = PolicyViolationError


class RiskLevel(IntEnum):
    """Execution risk level for DSL actions."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

    @classmethod
    def from_value(cls, value: object) -> "RiskLevel":
        if isinstance(value, RiskLevel):
            return value
        if isinstance(value, int):
            return cls(value)
        return cls[str(value).upper()]


@dataclass(frozen=True)
class ActionSpec:
    """Risk metadata for a DSL operator or action."""

    name: str
    risk: RiskLevel
    description: str
    requires_approval: bool = False


OPERATOR_ACTIONS = {
    "context_reset": ActionSpec(
        "context_reset",
        RiskLevel.MEDIUM,
        "Drops context and can alter continuity assumptions.",
    ),
    "critique": ActionSpec("critique", RiskLevel.LOW, "Evaluates generated output."),
    "filter": ActionSpec("filter", RiskLevel.LOW, "Computes a selection metric."),
    "format": ActionSpec("format", RiskLevel.LOW, "Formats the current output."),
    "generate": ActionSpec("generate", RiskLevel.LOW, "Calls a model adapter."),
    "policy_check": ActionSpec(
        "policy_check", RiskLevel.LOW, "Records a local policy metric."
    ),
    "refine": ActionSpec(
        "refine", RiskLevel.LOW, "Calls a model adapter to refine output."
    ),
    "retrieve": ActionSpec(
        "retrieve",
        RiskLevel.MEDIUM,
        "Pulls contextual data into the prompt.",
    ),
    "store": ActionSpec(
        "store",
        RiskLevel.HIGH,
        "Writes runtime output to memory.",
        requires_approval=True,
    ),
    "transform": ActionSpec("transform", RiskLevel.LOW, "Transforms local text."),
}


@dataclass(frozen=True)
class CapabilityPolicy:
    """Preflight policy for compiled DSL programs."""

    allowed_operators: frozenset[str] = frozenset(
        {
            "context_reset",
            "critique",
            "filter",
            "format",
            "generate",
            "policy_check",
            "refine",
            "retrieve",
            "store",
            "transform",
        }
    )
    allowed_roles: frozenset[str] = frozenset(
        {
            "critic",
            "default",
            "librarian",
            "machine",
            "operative",
            "oracle",
            "synthesizer",
        }
    )
    allowed_memory_targets: frozenset[str] = frozenset({"session"})
    max_loop_count: int = 3
    max_model_calls: int = 12
    max_risk_without_approval: RiskLevel = RiskLevel.MEDIUM
    approved_actions: frozenset[str] = frozenset()
    allow_memory_write: bool = False
    allow_retrieval: bool = True
    extra: dict[str, str] = field(default_factory=dict)

    @classmethod
    def permissive(cls) -> "CapabilityPolicy":
        return cls(
            allowed_memory_targets=frozenset({"session", "long_term"}),
            max_loop_count=10,
            max_model_calls=64,
            max_risk_without_approval=RiskLevel.HIGH,
            approved_actions=frozenset({"store"}),
            allow_memory_write=True,
            allow_retrieval=True,
        )

    def validate(self, plan: ExecutionPlan) -> None:
        estimated_calls = 0
        for node in plan.nodes:
            if node.type not in self.allowed_operators:
                raise PolicyViolation(f"Operator not allowed: {node.type}")
            self._validate_action_risk(node.type)
            if node.type == "retrieve" and not self.allow_retrieval:
                raise PolicyViolation("Retrieval is not allowed by policy")
            if node.type == "store":
                if not self.allow_memory_write:
                    raise PolicyViolation("Memory writes are not allowed by policy")
                memory = str(node.params.get("memory", "session"))
                if memory not in self.allowed_memory_targets:
                    raise PolicyViolation(f"Memory target not allowed: {memory}")
            role = node.params.get("role")
            if role is not None and str(role) not in self.allowed_roles:
                raise PolicyViolation(f"Role not allowed: {role}")
            estimated_calls += _estimated_model_calls(node.type, node.params)

        self._validate_control(plan.program)
        if estimated_calls > self.max_model_calls:
            raise PolicyViolation(
                f"Estimated model calls {estimated_calls} exceeds policy limit {self.max_model_calls}"
            )

    def _validate_control(self, program: tuple[Program, ...]) -> None:
        for statement in program:
            if statement.kind == "loop":
                count = int(statement.params["count"])
                if count > self.max_loop_count:
                    raise PolicyViolation(
                        f"Loop count {count} exceeds policy limit {self.max_loop_count}"
                    )
                self._validate_control(statement.body)
            elif statement.kind == "if":
                self._validate_control(statement.body)
                self._validate_control(statement.else_body)

    def _validate_action_risk(self, operator: str) -> None:
        action = OPERATOR_ACTIONS.get(
            operator, ActionSpec(operator, RiskLevel.HIGH, "Unknown action")
        )
        if (
            action.risk > self.max_risk_without_approval
            and action.name not in self.approved_actions
        ):
            raise PolicyViolation(
                f"Action {action.name} risk {action.risk.name} exceeds "
                f"unapproved limit {self.max_risk_without_approval.name}"
            )
        if action.requires_approval and action.name not in self.approved_actions:
            raise PolicyViolation(f"Action requires approval: {action.name}")


def _estimated_model_calls(operator: str, params: dict[str, object]) -> int:
    if operator in {"generate", "critique"}:
        return 1
    if operator == "refine":
        return int(params.get("iter", 1))
    return 0
