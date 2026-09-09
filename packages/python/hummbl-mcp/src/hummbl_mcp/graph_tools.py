"""Graphify wrapper — stdlib-only graph query tools.

Reads NetworkX node-link JSON artifacts produced by Graphify and exposes
a curated query surface.  No third-party deps.

Per ADR-008 and RFC-graphify-integration.md §4.4.
"""

from __future__ import annotations

import json
import os
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from hummbl_mcp.protocol import INVALID_PARAMS, JsonRpcError


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_GRAPHS_DIR = Path(
    os.environ.get(
        "HUMMBL_GRAPHS_DIR",
        str(Path(__file__).resolve().parents[1] / "_state" / "graphs"),
    )
)

# Edge confidence ordering (strictest → loosest)
_CONFIDENCE_ORDER = {"EXTRACTED": 0, "INFERRED": 1, "AMBIGUOUS": 2}


# ---------------------------------------------------------------------------
# Internal data model
# ---------------------------------------------------------------------------

@dataclass
class GraphArtifact:
    """In-memory representation of a loaded graph.json."""

    corpus: str
    path: Path
    nodes: list[dict[str, Any]] = field(default_factory=list)
    edges: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    # Indexed lookups (built on load)
    _node_by_id: dict[str, dict[str, Any]] = field(default_factory=dict, repr=False)
    _adj: dict[str, list[tuple[str, dict[str, Any]]]] = field(
        default_factory=dict, repr=False
    )

    def __post_init__(self) -> None:
        self._node_by_id = {n["id"]: n for n in self.nodes}
        self._adj = {}
        for e in self.edges:
            src = str(e.get("source", ""))
            tgt = str(e.get("target", ""))
            if not src or not tgt:
                continue
            self._adj.setdefault(src, []).append((tgt, e))
            # Undirected fallback: index reverse direction too unless explicitly directed
            if not self.metadata.get("directed", False):
                self._adj.setdefault(tgt, []).append((src, e))

    def node(self, node_id: str) -> dict[str, Any] | None:
        return self._node_by_id.get(node_id)

    def neighbors(
        self,
        node_id: str,
        hops: int = 1,
        min_confidence: str = "EXTRACTED",
    ) -> list[dict[str, Any]]:
        """BFS neighbors up to *hops* away, filtered by confidence."""
        if node_id not in self._node_by_id:
            return []

        threshold = _CONFIDENCE_ORDER.get(min_confidence, 0)
        visited: set[str] = {node_id}
        frontier: deque[tuple[str, int]] = deque([(node_id, 0)])
        results: list[dict[str, Any]] = []

        while frontier:
            current, dist = frontier.popleft()
            if dist >= hops:
                continue
            for tgt, edge in self._adj.get(current, []):
                edge_conf = edge.get("confidence", "EXTRACTED")
                if _CONFIDENCE_ORDER.get(edge_conf, 99) > threshold:
                    continue
                if tgt in visited:
                    continue
                visited.add(tgt)
                node = self._node_by_id.get(tgt)
                if node is not None:
                    results.append(
                        {
                            "node": node,
                            "distance": dist + 1,
                            "edge": {
                                "confidence": edge_conf,
                                "relation": edge.get("relation", "unknown"),
                            },
                        }
                    )
                frontier.append((tgt, dist + 1))
        return results

    def shortest_path(
        self,
        source: str,
        target: str,
        max_hops: int = 5,
    ) -> dict[str, Any] | None:
        """BFS shortest path.  Returns nodes + edges with confidence flags."""
        if source not in self._node_by_id or target not in self._node_by_id:
            return None

        # BFS tracking parent edge
        queue: deque[str] = deque([source])
        visited: set[str] = {source}
        parent: dict[str, tuple[str, dict[str, Any]]] = {}

        while queue:
            current = queue.popleft()
            if current == target:
                break
            # Prevent runaway on degenerate graphs
            path_len = 0
            tmp = current
            while tmp in parent:
                tmp, _ = parent[tmp]
                path_len += 1
                if path_len > max_hops:
                    break
            if path_len > max_hops:
                continue

            for tgt, edge in self._adj.get(current, []):
                if tgt in visited:
                    continue
                visited.add(tgt)
                parent[tgt] = (current, edge)
                queue.append(tgt)

        if target not in parent and target != source:
            return None

        # Reconstruct path
        path_nodes: list[dict[str, Any]] = []
        path_edges: list[dict[str, Any]] = []
        cur = target
        while cur in parent:
            prev, edge = parent[cur]
            path_edges.insert(
                0,
                {
                    "source": prev,
                    "target": cur,
                    "confidence": edge.get("confidence", "EXTRACTED"),
                    "relation": edge.get("relation", "unknown"),
                },
            )
            cur = prev
        # Walk forward to collect node objects
        node_ids = [source]
        for e in path_edges:
            node_ids.append(e["target"])
        for nid in node_ids:
            n = self._node_by_id.get(nid)
            if n is not None:
                path_nodes.append(n)

        return {
            "nodes": path_nodes,
            "edges": path_edges,
            "hops": len(path_edges),
            "has_inferred": any(e["confidence"] == "INFERRED" for e in path_edges),
            "has_ambiguous": any(e["confidence"] == "AMBIGUOUS" for e in path_edges),
        }


# ---------------------------------------------------------------------------
# Artifact loader
# ---------------------------------------------------------------------------

def _graphs_dir() -> Path:
    return Path(os.environ.get("HUMMBL_GRAPHS_DIR", str(DEFAULT_GRAPHS_DIR)))


def _latest_artifact(corpus: str) -> Path | None:
    """Resolve latest.json symlink/copy or newest timestamped file."""
    corpus_dir = _graphs_dir() / corpus
    if not corpus_dir.exists():
        return None
    latest = corpus_dir / "latest.json"
    if latest.exists():
        return latest
    # Fallback: newest graph-YYYYMMDD-HHMMSS.json
    candidates = sorted(
        (p for p in corpus_dir.iterdir() if p.name.startswith("graph-") and p.suffix == ".json"),
        key=lambda p: p.name,
        reverse=True,
    )
    return candidates[0] if candidates else None


def _load_artifact(path: Path, corpus: str) -> GraphArtifact:
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise JsonRpcError(
            -32603,
            f"graph.json root must be object, got {type(data).__name__}",
        )
    return GraphArtifact(
        corpus=corpus,
        path=path,
        nodes=data.get("nodes", []),
        edges=data.get("links", data.get("edges", [])),
        metadata=data.get("graph", {}),
    )


# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------

def _get_corpus_param(params: dict[str, Any]) -> str:
    corpus = params.get("corpus")
    if not isinstance(corpus, str) or not corpus:
        raise JsonRpcError(INVALID_PARAMS, "'corpus' is required and must be a non-empty string")
    return corpus


def handle_graph_corpora(_params: dict[str, Any]) -> list[str]:
    """List available corpora (directories in graphs root)."""
    root = _graphs_dir()
    if not root.exists():
        return []
    return sorted(
        p.name for p in root.iterdir() if p.is_dir() and (p / "latest.json").exists() or any(
            c.name.startswith("graph-") and c.suffix == ".json" for c in p.iterdir()
        )
    )


def handle_graph_status(params: dict[str, Any]) -> dict[str, Any]:
    """Return latest build metadata for a corpus."""
    corpus = _get_corpus_param(params)
    artifact = _latest_artifact(corpus)
    if artifact is None:
        return {"available": False, "corpus": corpus}
    return {
        "available": True,
        "corpus": corpus,
        "artifact_path": str(artifact),
        "artifact_name": artifact.name,
        "artifact_mtime_iso": _iso_mtime(artifact),
    }


def _query_single_corpus(corpus: str, query: str, top_k: int) -> list[dict[str, Any]]:
    """Internal helper: query one corpus and tag results with corpus."""
    artifact = _latest_artifact(corpus)
    if artifact is None:
        return []
    graph = _load_artifact(artifact, corpus)
    qlower = query.lower()
    scored: list[tuple[float, dict[str, Any]]] = []
    for node in graph.nodes:
        label = str(node.get("label", node.get("id", "")))
        ntype = str(node.get("type", ""))
        text = f"{label} {ntype}".lower()
        if qlower in text:
            if qlower == label.lower():
                score = 3.0
            elif qlower in label.lower():
                score = 2.0
            else:
                score = 1.0
            tagged_node = dict(node)
            tagged_node["_corpus"] = corpus
            scored.append((score, tagged_node))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [{"node": n, "score": s, "corpus": corpus} for s, n in scored[:top_k]]


def handle_graph_query(params: dict[str, Any]) -> list[dict[str, Any]]:
    """Text query across node labels / types."""
    corpus = _get_corpus_param(params)
    query = params.get("query", "")
    if not isinstance(query, str):
        raise JsonRpcError(INVALID_PARAMS, "'query' must be a string")
    top_k = params.get("top_k", 10)
    if not isinstance(top_k, int) or top_k < 1:
        top_k = 10
    return _query_single_corpus(corpus, query, top_k)


def handle_graph_cross_query(params: dict[str, Any]) -> list[dict[str, Any]]:
    """Text query across multiple corpora (union-at-query-time)."""
    corpora = params.get("corpora")
    if not isinstance(corpora, list) or not corpora:
        raise JsonRpcError(INVALID_PARAMS, "'corpora' is required and must be a list of strings")
    query = params.get("query", "")
    if not isinstance(query, str):
        raise JsonRpcError(INVALID_PARAMS, "'query' must be a string")
    top_k = params.get("top_k", 10)
    if not isinstance(top_k, int) or top_k < 1:
        top_k = 10

    all_results: list[dict[str, Any]] = []
    for corpus in corpora:
        if not isinstance(corpus, str):
            continue
        all_results.extend(_query_single_corpus(corpus, query, top_k))

    # Re-rank by score, corpus-agnostic
    all_results.sort(key=lambda x: x["score"], reverse=True)
    return all_results[:top_k]


def handle_graph_neighbors(params: dict[str, Any]) -> list[dict[str, Any]]:
    """Neighbors of a node, filtered by confidence."""
    corpus = _get_corpus_param(params)
    node_id = params.get("node_id")
    if not isinstance(node_id, str) or not node_id:
        raise JsonRpcError(INVALID_PARAMS, "'node_id' is required")
    hops = params.get("hops", 1)
    if not isinstance(hops, int) or hops < 1:
        hops = 1
    min_confidence = params.get("min_confidence", "EXTRACTED")
    if min_confidence not in _CONFIDENCE_ORDER:
        min_confidence = "EXTRACTED"

    artifact = _latest_artifact(corpus)
    if artifact is None:
        return []

    graph = _load_artifact(artifact, corpus)
    return graph.neighbors(node_id, hops=hops, min_confidence=min_confidence)


def handle_graph_path(params: dict[str, Any]) -> dict[str, Any] | None:
    """Shortest path between two nodes."""
    corpus = _get_corpus_param(params)
    source = params.get("source")
    target = params.get("target")
    if not isinstance(source, str) or not source:
        raise JsonRpcError(INVALID_PARAMS, "'source' is required")
    if not isinstance(target, str) or not target:
        raise JsonRpcError(INVALID_PARAMS, "'target' is required")
    max_hops = params.get("max_hops", 5)
    if not isinstance(max_hops, int) or max_hops < 1:
        max_hops = 5

    artifact = _latest_artifact(corpus)
    if artifact is None:
        return None

    graph = _load_artifact(artifact, corpus)
    return graph.shortest_path(source, target, max_hops=max_hops)


# ---------------------------------------------------------------------------
# Tool definitions (MCP schema)
# ---------------------------------------------------------------------------

def get_tool_definitions() -> list[Any]:
    from hummbl_mcp.protocol import ToolDefinition

    return [
        ToolDefinition(
            name="graph_corpora",
            description="List available graph corpora.",
            input_schema={"type": "object", "properties": {}},
        ),
        ToolDefinition(
            name="graph_status",
            description="Check whether a graph corpus is available and when it was last built.",
            input_schema={
                "type": "object",
                "properties": {
                    "corpus": {
                        "type": "string",
                        "description": "Corpus name (e.g. 'projects', 'bki', 'arcana')",
                    }
                },
                "required": ["corpus"],
            },
        ),
        ToolDefinition(
            name="graph_query",
            description="Search nodes in a corpus by label or type. Returns ranked matches.",
            input_schema={
                "type": "object",
                "properties": {
                    "corpus": {
                        "type": "string",
                        "description": "Corpus name",
                    },
                    "query": {
                        "type": "string",
                        "description": "Text to match against node labels and types",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Maximum results to return (default 10)",
                        "default": 10,
                    },
                },
                "required": ["corpus", "query"],
            },
        ),
        ToolDefinition(
            name="graph_cross_query",
            description="Search nodes across multiple corpora by label or type. Returns ranked, merged results.",
            input_schema={
                "type": "object",
                "properties": {
                    "corpora": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of corpus names to query",
                    },
                    "query": {
                        "type": "string",
                        "description": "Text to match against node labels and types",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Maximum results to return (default 10)",
                        "default": 10,
                    },
                },
                "required": ["corpora", "query"],
            },
        ),
        ToolDefinition(
            name="graph_neighbors",
            description="Find neighbors of a node within a graph corpus, with optional hop and confidence filters.",
            input_schema={
                "type": "object",
                "properties": {
                    "corpus": {"type": "string"},
                    "node_id": {"type": "string", "description": "Node ID to start from"},
                    "hops": {
                        "type": "integer",
                        "description": "BFS depth (default 1)",
                        "default": 1,
                    },
                    "min_confidence": {
                        "type": "string",
                        "enum": ["EXTRACTED", "INFERRED", "AMBIGUOUS"],
                        "description": "Minimum edge confidence to include (default EXTRACTED)",
                        "default": "EXTRACTED",
                    },
                },
                "required": ["corpus", "node_id"],
            },
        ),
        ToolDefinition(
            name="graph_path",
            description="Shortest path between two nodes in a corpus. Flags INFERRED/AMBIGUOUS edges.",
            input_schema={
                "type": "object",
                "properties": {
                    "corpus": {"type": "string"},
                    "source": {"type": "string", "description": "Start node ID"},
                    "target": {"type": "string", "description": "End node ID"},
                    "max_hops": {
                        "type": "integer",
                        "description": "Path length limit (default 5)",
                        "default": 5,
                    },
                },
                "required": ["corpus", "source", "target"],
            },
        ),
    ]


def get_handlers() -> dict[str, Any]:
    return {
        "graph_corpora": handle_graph_corpora,
        "graph_status": handle_graph_status,
        "graph_query": handle_graph_query,
        "graph_cross_query": handle_graph_cross_query,
        "graph_neighbors": handle_graph_neighbors,
        "graph_path": handle_graph_path,
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _iso_mtime(path: Path) -> str:
    import datetime

    mtime = path.stat().st_mtime
    return datetime.datetime.fromtimestamp(mtime, tz=datetime.timezone.utc).isoformat()
