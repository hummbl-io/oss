"""Semantic graph validation for the Phase 1 relation registry."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from .records import Record, Relation


class SemanticError(ValueError):
    """A structurally valid object violates domain semantics."""


ACYCLIC_RELATIONS = {
    "hummbl:contains",
    "hummbl:authorized_by",
    "hummbl:supersedes",
    "hummbl:strictly_precedes",
}


def _has_cycle(edges: Iterable[tuple[str, str]]) -> bool:
    adjacency: dict[str, list[str]] = defaultdict(list)
    for source, target in edges:
        adjacency[source].append(target)
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        for target in adjacency[node]:
            if visit(target):
                return True
        visiting.remove(node)
        visited.add(node)
        return False

    return any(visit(node) for node in tuple(adjacency))


def validate_graph(records: Iterable[Record], relations: Iterable[Relation]) -> None:
    """Validate endpoint, epistemic, and relation-specific cycle invariants."""

    record_list = list(records)
    record_map = {record.record_id: record for record in record_list}
    relation_list = list(relations)
    if len(record_map) != len(record_list):
        raise SemanticError("duplicate record identity")
    seen_relations: set[str] = set()
    for relation in relation_list:
        if relation.relation_id in seen_relations:
            raise SemanticError("duplicate relation identity")
        seen_relations.add(relation.relation_id)
        try:
            source = record_map[relation.source_record_id]
            target = record_map[relation.target_record_id]
        except KeyError as exc:
            raise SemanticError("relation endpoint does not exist") from exc
        if relation.relation_type == "hummbl:supports":
            if source.record_type != "hummbl:Evidence" or target.record_type != "hummbl:Claim":
                raise SemanticError(
                    "supports requires Evidence -> Claim; receipts are not evidence"
                )

    for relation_type in ACYCLIC_RELATIONS:
        edges = (
            (item.source_record_id, item.target_record_id)
            for item in relation_list
            if item.relation_type == relation_type
        )
        if _has_cycle(edges):
            raise SemanticError(f"{relation_type} relation must be acyclic")
