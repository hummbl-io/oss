"""Retriever adapters for Sigil Forge."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Protocol


class Queryable(Protocol):
    def query(self, text: str, limit: int = 5) -> object:
        ...


@dataclass(frozen=True)
class StaticRetriever:
    """Deterministic retriever for tests and local examples."""

    documents: tuple[str, ...]

    def __call__(self, query: str, count: int) -> list[str]:
        lowered = query.lower()
        matches = [doc for doc in self.documents if lowered in doc.lower()]
        return (matches or list(self.documents))[:count]


@dataclass(frozen=True)
class OpenBrainSigilRetriever:
    """Adapter for Open Brain style query clients."""

    client: Queryable

    def __call__(self, query: str, count: int) -> list[str]:
        result = self.client.query(query, limit=count)
        if isinstance(result, str):
            return [result]
        if isinstance(result, dict):
            return _extract_strings(result.values())[:count]
        if isinstance(result, Iterable):
            return _extract_strings(result)[:count]
        return [str(result)]


def _extract_strings(items: Iterable[object]) -> list[str]:
    values: list[str] = []
    for item in items:
        if isinstance(item, str):
            values.append(item)
        elif isinstance(item, dict):
            for key in ("content", "text", "summary", "title"):
                value = item.get(key)
                if value:
                    values.append(str(value))
                    break
        else:
            values.append(str(item))
    return values
