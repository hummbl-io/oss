"""Execution plan validation and visualization."""

from __future__ import annotations

from dataclasses import dataclass

from hummbl_cognition.sigil_forge.ir import ExecutionPlan


@dataclass(frozen=True)
class PlanIssue:
    code: str
    message: str
    severity: str = "warning"


class PlanValidator:
    def validate(self, plan: ExecutionPlan) -> tuple[PlanIssue, ...]:
        issues: list[PlanIssue] = []
        node_ids = {node.id for node in plan.nodes}
        for edge in plan.edges:
            if edge.source not in node_ids:
                issues.append(
                    PlanIssue(
                        "missing_source", f"Missing source node: {edge.source}", "error"
                    )
                )
            if edge.target not in node_ids:
                issues.append(
                    PlanIssue(
                        "missing_target", f"Missing target node: {edge.target}", "error"
                    )
                )
        targeted = {edge.target for edge in plan.edges}
        for node in plan.nodes[1:]:
            if node.id not in targeted:
                issues.append(
                    PlanIssue(
                        "unreachable_node", f"Node has no inbound edge: {node.id}"
                    )
                )
        return tuple(issues)


def to_mermaid(plan: ExecutionPlan) -> str:
    lines = ["graph TD"]
    if not plan.nodes:
        return "\n".join(lines)
    labels = {node.id: f"{node.id}[{node.type}]" for node in plan.nodes}
    if not plan.edges:
        lines.extend(f"  {label}" for label in labels.values())
        return "\n".join(lines)
    for edge in plan.edges:
        lines.append(
            f"  {labels.get(edge.source, edge.source)} --> {labels.get(edge.target, edge.target)}"
        )
    return "\n".join(lines)
