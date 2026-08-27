"""Deterministic execution engine for compiled Sigil Forge programs."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from hummbl_cognition.sigil_forge.compiler import DSLCompiler
from hummbl_cognition.sigil_forge.critique import parse_critique
from hummbl_cognition.sigil_forge.ir import ExecutionPlan, Program
from hummbl_cognition.sigil_forge.policy import CapabilityPolicy
from hummbl_cognition.sigil_forge.preprocessors import (
    InputPreprocessor,
    run_preprocessors,
)
from hummbl_cognition.sigil_forge.receipts import ExecutionReceiptWriter, build_receipt
from hummbl_cognition.sigil_forge.roles import RolePolicy, role_instruction

ModelAdapter = Callable[[str], str]
Retriever = Callable[[str, int], list[str]]
MemoryWriter = Callable[[dict[str, Any]], None]


@dataclass
class RuntimeState:
    """Mutable execution state passed through a prompt graph."""

    user_input: str
    context: list[str] = field(default_factory=list)
    outputs: dict[str, str] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)
    audit: list[dict[str, Any]] = field(default_factory=list)
    last_output: str = ""


class ExecutionEngine:
    """Run Sigil Forge execution plans against pluggable backends.

    The default backend is deterministic and local, which keeps tests and
    governance review independent of third-party model APIs. Production callers
    can inject a model adapter, retriever, and memory writer.
    """

    def __init__(
        self,
        *,
        model: ModelAdapter | None = None,
        retriever: Retriever | None = None,
        memory_writer: MemoryWriter | None = None,
        compiler: DSLCompiler | None = None,
        policy: CapabilityPolicy | None = None,
        receipt_writer: ExecutionReceiptWriter | None = None,
        preprocessors: list[InputPreprocessor] | None = None,
        role_policy: RolePolicy | None = None,
    ) -> None:
        self.model = model or _deterministic_model
        self.retriever = retriever or _empty_retriever
        self.memory_writer = memory_writer
        self.compiler = compiler or DSLCompiler()
        self.policy = policy or CapabilityPolicy()
        self.receipt_writer = receipt_writer
        self.preprocessors = preprocessors or []
        self.role_policy = role_policy or RolePolicy()

    def run(self, source: str, user_input: str) -> RuntimeState:
        plan = self.compiler.compile(source)
        return self.execute(plan, user_input)

    def execute(self, plan: ExecutionPlan, user_input: str) -> RuntimeState:
        self.policy.validate(plan)
        self.role_policy.validate_sequence(
            [str(node.role) for node in plan.nodes if node.role is not None]
        )
        preprocess = run_preprocessors(user_input, self.preprocessors)
        if preprocess.blocked:
            state = RuntimeState(user_input=user_input)
            state.audit.append(
                {
                    "event": "preprocess_blocked",
                    "warnings": [warning.__dict__ for warning in preprocess.warnings],
                }
            )
            return state
        state = RuntimeState(user_input=preprocess.text)
        for warning in preprocess.warnings:
            state.audit.append(
                {"event": "preprocess_warning", "warning": warning.__dict__}
            )
        error: str | None = None
        try:
            for statement in plan.program:
                self._execute_statement(statement, state)
            return state
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            raise
        finally:
            if self.receipt_writer is not None:
                self.receipt_writer.write(
                    build_receipt(
                        plan=plan,
                        audit=state.audit,
                        metrics=state.metrics,
                        outputs=state.outputs,
                        error=error,
                    )
                )

    def _execute_statement(self, statement: Program, state: RuntimeState) -> None:
        if statement.kind == "loop":
            count = int(statement.params["count"])
            for index in range(count):
                state.audit.append(
                    {"event": "loop", "iteration": index + 1, "count": count}
                )
                for child in statement.body:
                    self._execute_statement(child, state)
            return

        if statement.kind == "if":
            if statement.condition is None:
                raise ValueError("IF statement missing condition")
            matched = statement.condition.evaluate(state.metrics)
            branch = statement.body if matched else statement.else_body
            state.audit.append(
                {
                    "event": "condition",
                    "condition": statement.condition.__dict__,
                    "matched": matched,
                }
            )
            for child in branch:
                self._execute_statement(child, state)
            return

        if statement.kind != "node":
            raise ValueError(f"Unsupported statement kind: {statement.kind}")

        operator = statement.operator or ""
        handler = getattr(self, f"_op_{operator}", None)
        if handler is None:
            raise ValueError(f"Unsupported operator: {operator}")
        handler(statement, state)
        state.audit.append(
            {"event": "node", "operator": operator, "params": statement.params}
        )

    def _op_retrieve(self, statement: Program, state: RuntimeState) -> None:
        count = int(statement.params.get("k", 5))
        state.context.extend(self.retriever(state.user_input, count))

    def run_ritual(self, name: str, user_input: str) -> RuntimeState:
        from hummbl_cognition.sigil_forge.rituals import RitualLibrary

        return self.run(RitualLibrary().get(name), user_input)

    def _op_generate(self, statement: Program, state: RuntimeState) -> None:
        prompt = self._build_prompt(statement, state, task="generate")
        output = self.model(prompt)
        state.outputs["generate"] = output
        state.last_output = output

    def _op_critique(self, statement: Program, state: RuntimeState) -> None:
        prompt = self._build_prompt(statement, state, task="critique")
        output = self.model(prompt)
        critique = parse_critique(output)
        state.metrics["score"] = critique.score
        state.metrics["issues"] = len(critique.issues)
        state.metrics["contradictions"] = len(critique.contradictions)
        state.metrics["missing_evidence"] = len(critique.missing_evidence)
        state.outputs["critique"] = json.dumps(critique.to_dict(), sort_keys=True)
        state.last_output = output

    def _op_refine(self, statement: Program, state: RuntimeState) -> None:
        iterations = int(statement.params.get("iter", 1))
        for _ in range(iterations):
            prompt = self._build_prompt(statement, state, task="refine")
            state.last_output = self.model(prompt)
        state.outputs["refine"] = state.last_output

    def _op_format(self, statement: Program, state: RuntimeState) -> None:
        output_type = str(statement.params.get("type", "text"))
        if output_type == "json":
            state.last_output = json.dumps(
                {"output": state.last_output}, sort_keys=True
            )
        state.outputs["final"] = state.last_output

    def _op_store(self, statement: Program, state: RuntimeState) -> None:
        payload = {
            "input": state.user_input,
            "memory": statement.params.get("memory", "session"),
            "output": state.last_output,
            "metrics": dict(state.metrics),
        }
        if self.memory_writer is not None:
            self.memory_writer(payload)
        state.outputs["store"] = "stored"

    def _op_filter(self, statement: Program, state: RuntimeState) -> None:
        threshold = float(statement.params.get("threshold", 0.0))
        state.metrics["accepted"] = float(state.metrics.get("score", 1.0)) >= threshold

    def _op_transform(self, statement: Program, state: RuntimeState) -> None:
        transform_type = str(statement.params.get("type", "rewrite"))
        state.last_output = f"{transform_type}: {state.last_output or state.user_input}"
        state.outputs["transform"] = state.last_output

    def _op_policy_check(self, statement: Program, state: RuntimeState) -> None:
        state.metrics["policy_ok"] = bool(statement.params.get("allow", True))

    def _op_context_reset(self, statement: Program, state: RuntimeState) -> None:
        state.context.clear()
        if statement.params.get("outputs", False):
            state.outputs.clear()
            state.last_output = ""

    def _build_prompt(
        self, statement: Program, state: RuntimeState, *, task: str
    ) -> str:
        role = str(statement.params.get("role", "default"))
        return "\n".join(
            [
                f"Role: {role}",
                f"Instruction: {role_instruction(role)}",
                f"Task: {task}",
                f"Input: {state.user_input}",
                f"Context: {state.context}",
                f"Previous: {state.last_output}",
                f"Params: {statement.params}",
            ]
        )


def _deterministic_model(prompt: str) -> str:
    return prompt.splitlines()[0] + " | deterministic-output"


def _empty_retriever(query: str, count: int) -> list[str]:
    return []
