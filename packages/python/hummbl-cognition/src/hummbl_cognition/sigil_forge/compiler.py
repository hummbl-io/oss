"""Compiler from Sigil Forge AST to execution plan IR."""

from __future__ import annotations

from dataclasses import replace

from hummbl_cognition.sigil_forge.ir import EdgeSpec, ExecutionPlan, NodeSpec, Program
from hummbl_cognition.sigil_forge.parser import DSLParser


class DSLCompiler:
    """Compile DSL source into a typed execution plan."""

    def __init__(self, parser: DSLParser | None = None) -> None:
        self.parser = parser or DSLParser()

    def compile(self, source: str) -> ExecutionPlan:
        program = self.parser.parse(source)
        nodes: list[NodeSpec] = []
        edges: list[EdgeSpec] = []
        previous: str | None = None
        counter = _NodeCounter()

        def walk(items: tuple[Program, ...]) -> None:
            nonlocal previous
            for item in items:
                if item.kind == "node":
                    node_id = counter.next(item.operator or "node")
                    role = item.params.get("role")
                    params = dict(item.params)
                    node = NodeSpec(
                        id=node_id,
                        type=str(item.operator),
                        params=params,
                        role=str(role) if role is not None else None,
                    )
                    nodes.append(node)
                    if previous is not None:
                        edges.append(EdgeSpec(source=previous, target=node_id))
                    previous = node_id
                elif item.kind == "loop":
                    walk(item.body)
                elif item.kind == "if":
                    walk(item.body)
                    if item.else_body:
                        walk(item.else_body)

        walk(program)
        normalized = tuple(_normalize_node_roles(item) for item in program)
        return ExecutionPlan(nodes=tuple(nodes), edges=tuple(edges), program=normalized, source=source)


class _NodeCounter:
    def __init__(self) -> None:
        self.value = 0

    def next(self, operator: str) -> str:
        self.value += 1
        return f"n{self.value}_{operator}"


def _normalize_node_roles(program: Program) -> Program:
    if program.kind == "node":
        role = program.params.get("role")
        return program if role is None else replace(program, params={**program.params, "role": str(role)})
    return replace(
        program,
        body=tuple(_normalize_node_roles(item) for item in program.body),
        else_body=tuple(_normalize_node_roles(item) for item in program.else_body),
    )
