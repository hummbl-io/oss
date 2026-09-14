"""basen-mcp v0.1 — MCP server exposing Base120 + BaseN governance surface.

Extracted from founder-mode (2026-08-09). Canonical home is now the
hummbl-dev-org/mcp-server monorepo at packages/python/basen/.

Architecture
------------
- Stdio JSON-RPC 2.0 server (MCP protocol 2024-11-05).
- Stdlib-only (no `mcp` library — wire protocol implemented from scratch
  per HUMMBL MCP convention).
- Wraps the canonical Base120 registry + `basen_tier.py` classifier +
  `basen_tuple.py` governance record producer.
- Variant parameter (`variant="base120"`) defaults to Base120 and sets up
  the surface for future variants (e.g. Base49, Base12-lite).

Tools (4 parameterized)
-----------------------
- basen_operator_lookup(operator_id, variant)             — Tier 0 read
- basen_family_browse(family, variant)                    — Tier 0 read
- basen_recommend(problem_description, variant, top_k)    — Tier 0 read
- basen_apply(operator_id, input, mode)                   — Tier 1 write (advisory|analytic|empirical)

Resources (URI-addressable, 127 total)
--------------------------------------
- basen://base120/operator/{ID}            — 120 operators
- basen://base120/family/{family}          — 6 families (P/IN/CO/DE/RE/SY)
- basen://base120/manifest                 — 1 catalog manifest

Prompts (3)
-----------
- basen-recon : Apply BaseN to recon a problem
- basen-spec  : Convert intent to spec using BaseN
- basen-audit : Audit artifact with BaseN

Transport
---------
stdio (default per R-05 of SYNTHESIS).
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# MCP protocol primitives (stdlib JSON-RPC 2.0)
# ---------------------------------------------------------------------------

MCP_PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "basen-mcp"
SERVER_VERSION = "0.1.0"

# JSON-RPC 2.0 error codes
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603

# MCP application-level errors
TOOL_NOT_FOUND = -32001
RESOURCE_NOT_FOUND = -32002
PROMPT_NOT_FOUND = -32003


@dataclass
class JsonRpcError(Exception):
    code: int
    message: str
    data: Any = None

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"code": self.code, "message": self.message}
        if self.data is not None:
            out["data"] = self.data
        return out


# ---------------------------------------------------------------------------
# Registry loader
# ---------------------------------------------------------------------------

# Default canonical registry path — bundled in the basen package data directory.
# Operators can override with BASEN_REGISTRY_PATH for deployment-specific registries.
_PACKAGE_ROOT = Path(__file__).resolve().parent
DEFAULT_REGISTRY_JSON = Path(
    os.environ.get(
        "BASEN_REGISTRY_PATH",
        str(_PACKAGE_ROOT / "data" / "base120_registry.json"),
    )
)

# Family code -> human name (matches registry domain field)
_FAMILY_NAMES = {
    "P": "Perspective",
    "IN": "Inversion",
    "CO": "Composition",
    "DE": "Decomposition",
    "RE": "Recursion",
    "SY": "Systems",
}


def _load_registry(variant: str = "base120") -> list[dict[str, Any]]:
    """Load operator records for a variant. Cached in-process at module level."""
    if variant != "base120":
        # TODO: future variant dispatch (base49, base12-lite, etc.)
        raise JsonRpcError(
            INVALID_PARAMS,
            f"unknown variant: {variant!r} (only 'base120' supported in v0.1)",
        )

    if not DEFAULT_REGISTRY_JSON.exists():
        raise JsonRpcError(
            INTERNAL_ERROR,
            f"registry not found at {DEFAULT_REGISTRY_JSON}",
        )

    with DEFAULT_REGISTRY_JSON.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise JsonRpcError(INTERNAL_ERROR, "registry root must be a JSON array")
    return data


# Lazy in-process cache: variant -> list of operator records
_REGISTRY_CACHE: dict[str, list[dict[str, Any]]] = {}


def _registry(variant: str = "base120") -> list[dict[str, Any]]:
    if variant not in _REGISTRY_CACHE:
        _REGISTRY_CACHE[variant] = _load_registry(variant)
    return _REGISTRY_CACHE[variant]


def _operators_by_family(variant: str, family: str) -> list[dict[str, Any]]:
    return [op for op in _registry(variant) if op.get("domain") == family]


def _operator_by_id(variant: str, operator_id: str) -> dict[str, Any] | None:
    for op in _registry(variant):
        if op.get("id") == operator_id:
            return op
    return None


# ---------------------------------------------------------------------------
# Governance record emission (basen_tuple-shaped)
# ---------------------------------------------------------------------------


def _args_hash(args: dict[str, Any]) -> str:
    canonical = json.dumps(args, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# Default tuple log path — CWD-relative. Operators can override with BASEN_TUPLE_LOG.
_TUPLE_LOG_PATH = Path(
    os.environ.get(
        "BASEN_TUPLE_LOG",
        "_state/governance/tuples.jsonl",
    )
)


def _append_tuple_jsonl(record: dict[str, Any]) -> bool:
    """Append a tuple record to the JSONL log (KRINEIA-aligned: append-only).

    Cross-platform: tries the canonical `founder_mode.services.basen_tuple.append_tuple`
    first (POSIX with fcntl); falls back to a stdlib-only msvcrt-based appender on
    Windows. Returns True on successful write, False otherwise.
    """
    try:
        _TUPLE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        return False

    line = json.dumps(record, separators=(",", ":"), sort_keys=True) + "\n"

    # Prefer canonical writer when importable.
    try:
        from basen.basen_tuple import (  # type: ignore
            BaseNTuple,
            append_tuple,
        )
        import uuid as _uuid

        t = BaseNTuple(
            id=record.get("id", str(_uuid.uuid4())[:12]),
            time=record["time"],
            state=record["state"],
            drift=float(record.get("drift", 0.0)),
            agent=record["agent"],
            tool=record["tool"],
            args_hash=record["args_hash"],
            evidence=record.get("evidence", {}),
            tier=record["tier"],
        )
        append_tuple(t, path=str(_TUPLE_LOG_PATH))
        return True
    except (ImportError, ModuleNotFoundError, AttributeError, KeyError):
        pass

    # Cross-platform fallback (Windows or canonical-unavailable).
    try:
        if os.name == "nt":
            import msvcrt

            with open(_TUPLE_LOG_PATH, "a", encoding="utf-8") as f:
                try:
                    msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
                except OSError:
                    pass  # best-effort: append without exclusive lock
                try:
                    f.write(line)
                finally:
                    try:
                        msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
                    except OSError:
                        pass
        else:
            import fcntl

            with open(_TUPLE_LOG_PATH, "a", encoding="utf-8") as f:
                fcntl.flock(f, fcntl.LOCK_EX)
                try:
                    f.write(line)
                finally:
                    fcntl.flock(f, fcntl.LOCK_UN)
        return True
    except OSError:
        return False


def _emit_tuple(
    tool: str,
    args: dict[str, Any],
    tier: int,
    state: str = "ok",
    drift: float = 0.0,
    evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Emit a basen_tuple-shaped governance record alongside a tool response.

    Behavior:
      - Tier 0 reads: build the record + return inline (no persistence).
      - Tier 1+ writes: build, persist via `_append_tuple_jsonl`, return with
        a `persisted: true/false` field.

    KRINEIA invariants enforced: append-only log, no reward-path self-reference
    (this module never reads the log it writes for inference). Disable
    persistence via `BASEN_PERSIST_TUPLES=0`.
    """
    import time
    import uuid as _uuid

    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    rec = {
        "id": str(_uuid.uuid4())[:12],
        "tool": f"basen.{tool}",
        "args_hash": _args_hash(args),
        "tier": tier,
        "state": state,
        "drift": drift,
        "time": ts,
        "agent": os.environ.get("BASEN_MCP_AGENT", "basen-mcp"),
        "evidence": evidence or {},
    }

    if tier == 0:
        # Reads do not emit governance writes — per BaseNTuple tier model.
        return rec

    if os.environ.get("BASEN_PERSIST_TUPLES", "1") != "0":
        rec["persisted"] = _append_tuple_jsonl(rec)
    else:
        rec["persisted"] = False
    return rec


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------


@dataclass
class ToolDefinition:
    name: str
    description: str
    input_schema: dict[str, Any] = field(
        default_factory=lambda: {"type": "object", "properties": {}}
    )

    def to_obj(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema,
        }


MCP_TOOLS: list[ToolDefinition] = [
    ToolDefinition(
        name="basen_operator_lookup",
        description=(
            "Return full operator record by ID (P1-SY20 in base120 variant). "
            "Tier 0 read. Use for direct operator inspection."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "operator_id": {
                    "type": "string",
                    "description": "Operator ID, e.g. 'P1', 'IN10', 'SY20'.",
                },
                "variant": {
                    "type": "string",
                    "description": "BaseN variant. Defaults to 'base120'.",
                    "default": "base120",
                },
            },
            "required": ["operator_id"],
        },
    ),
    ToolDefinition(
        name="basen_family_browse",
        description=(
            "List operators in a family. Tier 0 read. "
            "Families: P (Perspective), IN (Inversion), CO (Composition), "
            "DE (Decomposition), RE (Recursion), SY (Systems)."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "family": {
                    "type": "string",
                    "enum": ["P", "IN", "CO", "DE", "RE", "SY"],
                    "description": "Family code.",
                },
                "variant": {
                    "type": "string",
                    "description": "BaseN variant. Defaults to 'base120'.",
                    "default": "base120",
                },
            },
            "required": ["family"],
        },
    ),
    ToolDefinition(
        name="basen_recommend",
        description=(
            "Recommend operators for a problem description. Tier 0 read. "
            "Returns ranked operator suggestions with rationale. "
            "v0.1: keyword-scoring stub; planned upgrade to embedding-based."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "problem_description": {
                    "type": "string",
                    "description": "Free-text problem statement.",
                },
                "variant": {
                    "type": "string",
                    "description": "BaseN variant. Defaults to 'base120'.",
                    "default": "base120",
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of recommendations to return.",
                    "default": 3,
                    "minimum": 1,
                    "maximum": 20,
                },
            },
            "required": ["problem_description"],
        },
    ),
    ToolDefinition(
        name="basen_apply",
        description=(
            "Apply an operator to an input. Advisory mode is Tier 0/read; analytic "
            "and empirical modes are Tier 1 writes (emit EVIDENCE tuples). "
            "Mode 'advisory' = description only; 'analytic' = structured walk-through; "
            "'empirical' = run with input artifacts."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "operator_id": {
                    "type": "string",
                    "description": "Operator ID, e.g. 'IN2' (Premortem Analysis).",
                },
                "input": {
                    "type": "string",
                    "description": "Input the operator is applied to.",
                },
                "mode": {
                    "type": "string",
                    "enum": ["advisory", "analytic", "empirical"],
                    "description": "Application mode.",
                    "default": "advisory",
                },
                "variant": {
                    "type": "string",
                    "description": "BaseN variant. Defaults to 'base120'.",
                    "default": "base120",
                },
            },
            "required": ["operator_id", "input"],
        },
    ),
]


# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------


def _tool_operator_lookup(args: dict[str, Any]) -> dict[str, Any]:
    op_id = args.get("operator_id")
    variant = args.get("variant", "base120")
    if not isinstance(op_id, str):
        raise JsonRpcError(INVALID_PARAMS, "operator_id must be a string")

    op = _operator_by_id(variant, op_id)
    if op is None:
        raise JsonRpcError(
            INVALID_PARAMS,
            f"operator not found: {op_id!r} in variant {variant!r}",
        )
    return {
        "operator": op,
        "variant": variant,
        "_governance": _emit_tuple("operator_lookup", args, tier=0),
    }


def _tool_family_browse(args: dict[str, Any]) -> dict[str, Any]:
    family = args.get("family")
    variant = args.get("variant", "base120")
    if family not in _FAMILY_NAMES:
        raise JsonRpcError(
            INVALID_PARAMS,
            f"family must be one of {list(_FAMILY_NAMES)}; got {family!r}",
        )
    ops = _operators_by_family(variant, family)
    return {
        "family": family,
        "family_name": _FAMILY_NAMES[family],
        "count": len(ops),
        "operators": ops,
        "variant": variant,
        "_governance": _emit_tuple("family_browse", args, tier=0),
    }


def _score_operator(op: dict[str, Any], keywords: list[str]) -> int:
    """Naive keyword-overlap scoring against name + definition.

    Retained as the fallback path when the embedding recommender is unreachable
    (Ollama down, SSH banned, etc.). Per SYNTHESIS §3.3 the recommend tool
    must be resilient — degraded mode is preferable to error.
    """
    haystack = " ".join(
        [
            str(op.get("name", "")),
            str(op.get("definition", "")),
            str(op.get("domain_name", "")),
        ]
    ).lower()
    return sum(1 for kw in keywords if kw in haystack)


# ---------------------------------------------------------------------------
# Embedding-based recommender (TODO 1, v0.2)
# ---------------------------------------------------------------------------
# Uses local Ollama nomic-embed-text via stdlib urllib. Operator embeddings
# are computed once per registry fingerprint and cached to disk; per-call work
# is one query embedding + 120 cosine similarities.

OLLAMA_EMBED_URL = os.environ.get(
    "BASEN_EMBED_URL", "http://127.0.0.1:11434/api/embeddings"
)
OLLAMA_EMBED_MODEL = os.environ.get("BASEN_EMBED_MODEL", "nomic-embed-text")
OLLAMA_EMBED_TIMEOUT = float(os.environ.get("BASEN_EMBED_TIMEOUT", "5.0"))

# Default embedding cache dir — CWD-relative. Operators can override with BASEN_EMBED_CACHE_DIR.
EMBED_CACHE_DIR = Path(
    os.environ.get(
        "BASEN_EMBED_CACHE_DIR",
        "_state/basen",
    )
)


def _embed_text(text: str) -> list[float] | None:
    """Embed text via local Ollama nomic-embed-text. None on failure."""
    import urllib.error
    import urllib.request

    payload = json.dumps({"model": OLLAMA_EMBED_MODEL, "prompt": text}).encode("utf-8")
    req = urllib.request.Request(
        OLLAMA_EMBED_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=OLLAMA_EMBED_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        embedding = data.get("embedding")
        if isinstance(embedding, list) and embedding:
            return [float(x) for x in embedding]
        return None
    except (urllib.error.URLError, OSError, ValueError, json.JSONDecodeError):
        return None


def _registry_fingerprint(registry: list[dict[str, Any]]) -> str:
    """Deterministic hash of registry contents — invalidates cache on change."""
    payload = json.dumps(
        [(op.get("id"), op.get("name"), op.get("definition")) for op in registry],
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _operator_corpus_text(op: dict[str, Any]) -> str:
    """The text we embed for each operator. Name + family + definition."""
    return " — ".join(
        [
            str(op.get("name", "")),
            str(op.get("domain_name", "")),
            str(op.get("definition", "")),
        ]
    )


def _load_or_compute_operator_embeddings(
    variant: str,
) -> dict[str, list[float]] | None:
    """Load operator embeddings from disk cache, computing on miss.

    Returns None if Ollama is unreachable AND no cache exists (fully degraded).
    Returns the cache if it exists even when Ollama is unreachable.
    """
    registry = _registry(variant)
    fp = _registry_fingerprint(registry)
    cache_path = EMBED_CACHE_DIR / f"embeddings_{variant}_{fp}.json"

    if cache_path.exists():
        try:
            with cache_path.open(encoding="utf-8") as f:
                cached = json.load(f)
            if isinstance(cached, dict) and cached:
                return {k: [float(x) for x in v] for k, v in cached.items()}
        except (OSError, ValueError, json.JSONDecodeError):
            pass  # fall through to recompute

    # Cache miss — try to compute. Probe Ollama with the first operator;
    # if it fails, bail rather than burn 120 timeouts.
    probe = _embed_text(_operator_corpus_text(registry[0]))
    if probe is None:
        return None

    embeddings: dict[str, list[float]] = {registry[0]["id"]: probe}
    for op in registry[1:]:
        emb = _embed_text(_operator_corpus_text(op))
        if emb is None:
            return None  # partial failure — don't cache a partial set
        embeddings[op["id"]] = emb

    try:
        EMBED_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with cache_path.open("w", encoding="utf-8") as f:
            json.dump(embeddings, f)
    except OSError:
        pass  # cache write failure is non-fatal; we still have in-memory data

    return embeddings


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Stdlib cosine similarity in [-1, 1]. Returns 0.0 on degenerate input."""
    import math

    if len(a) != len(b) or not a:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def _recommend_via_embeddings(
    desc: str, variant: str, top_k: int
) -> dict[str, Any] | None:
    """Embedding-cosine recommender. None on Ollama failure (caller falls back)."""
    op_embeddings = _load_or_compute_operator_embeddings(variant)
    if op_embeddings is None:
        return None
    query_emb = _embed_text(desc)
    if query_emb is None:
        return None

    registry = _registry(variant)
    scored: list[tuple[dict[str, Any], float]] = []
    for op in registry:
        emb = op_embeddings.get(op["id"])
        if emb is None:
            continue
        scored.append((op, _cosine_similarity(query_emb, emb)))
    scored.sort(key=lambda x: x[1], reverse=True)
    top = scored[: max(1, top_k)]
    return {
        "recommendations": [
            {
                "operator_id": op.get("id"),
                "name": op.get("name"),
                "family": op.get("domain"),
                "score": round(score, 4),
                "definition": op.get("definition"),
            }
            for op, score in top
        ],
        "method": "embedding-cosine-v0.2",
        "embedding_model": OLLAMA_EMBED_MODEL,
    }


def _tool_recommend(args: dict[str, Any]) -> dict[str, Any]:
    desc = args.get("problem_description")
    variant = args.get("variant", "base120")
    top_k = int(args.get("top_k", 3))
    if not isinstance(desc, str) or not desc.strip():
        raise JsonRpcError(
            INVALID_PARAMS, "problem_description must be a non-empty string"
        )

    # Try embedding-based recommender first (v0.2). Falls back to keyword
    # overlap on Ollama failure to keep the tool responsive in degraded mode.
    emb_result = _recommend_via_embeddings(desc, variant, top_k)
    if emb_result is not None:
        return {
            "problem_description": desc,
            **emb_result,
            "variant": variant,
            "_governance": _emit_tuple("recommend", args, tier=0),
        }

    # Fallback: lowercased keyword tokens (>=4 chars) for naive overlap scoring.
    tokens = [
        t
        for t in "".join(c.lower() if c.isalnum() else " " for c in desc).split()
        if len(t) >= 4
    ]
    scored = [(op, _score_operator(op, tokens)) for op in _registry(variant)]
    scored.sort(key=lambda x: x[1], reverse=True)
    top = scored[: max(1, top_k)]
    return {
        "problem_description": desc,
        "recommendations": [
            {
                "operator_id": op.get("id"),
                "name": op.get("name"),
                "family": op.get("domain"),
                "score": score,
                "definition": op.get("definition"),
            }
            for op, score in top
            if score > 0
        ]
        or [
            # Fallback: surface highest-coverage families if no token matched.
            {
                "operator_id": op.get("id"),
                "name": op.get("name"),
                "family": op.get("domain"),
                "score": 0,
                "definition": op.get("definition"),
                "_note": "no keyword overlap; returning top of registry",
            }
            for op, _ in scored[:top_k]
        ],
        "method": "keyword-overlap-v0.1-fallback",
        "variant": variant,
        "_governance": _emit_tuple("recommend", args, tier=0),
    }


# ---------------------------------------------------------------------------
# Apply modes (TODO 2, v0.2) — advisory | analytic | empirical
# ---------------------------------------------------------------------------

OLLAMA_CHAT_URL = os.environ.get(
    "BASEN_CHAT_URL", "http://127.0.0.1:11434/api/chat"
)
OLLAMA_CHAT_MODEL = os.environ.get("BASEN_CHAT_MODEL", "qwen3.5:9b")
OLLAMA_CHAT_TIMEOUT = float(os.environ.get("BASEN_CHAT_TIMEOUT", "30.0"))

# Per-family analytic templates. Each template encodes the operator's
# characteristic move as a structured walkthrough. No LLM required.
_FAMILY_ANALYTIC_TEMPLATES: dict[str, dict[str, str]] = {
    "P": {
        "question": "From which vantage point does this look different?",
        "method": "Re-frame the input by anchoring or shifting the observer's position.",
        "decision_point": "Which observer position best reveals the load-bearing structure?",
        "expected_output": "A re-framed statement of the input plus the named perspective shift.",
    },
    "IN": {
        "question": "What if the opposite of the stated assumption holds?",
        "method": "Identify the central assumption, then reason from its negation.",
        "decision_point": "Which assumption, if inverted, would most change the conclusion?",
        "expected_output": "A contrasting analysis revealing edges, blind spots, or hidden dependencies.",
    },
    "CO": {
        "question": "Which parts of the input combine into a coherent whole?",
        "method": "Find latent connections; synthesize previously separate elements.",
        "decision_point": "What binding principle holds the composition together?",
        "expected_output": "A composed structure that is more than the sum of its inputs.",
    },
    "DE": {
        "question": "What are the constituent parts of this system?",
        "method": "Partition the input into smaller, separately-analyzable units.",
        "decision_point": "Where are the natural seams that allow clean separation?",
        "expected_output": "An enumerated set of sub-components with their interfaces named.",
    },
    "RE": {
        "question": "What happens if this operation is applied to its own output?",
        "method": "Apply the operation iteratively; treat each output as the next input.",
        "decision_point": "Does the recursion converge, diverge, or produce stable cycles?",
        "expected_output": "A trace of N iterations plus the convergence verdict.",
    },
    "SY": {
        "question": "What is the system-level behavior emerging from these parts?",
        "method": "Map flows, feedback loops, and second-order effects across components.",
        "decision_point": "Where are the leverage points that produce disproportionate change?",
        "expected_output": "A systems map plus identification of high-leverage interventions.",
    },
}


def _apply_advisory(op: dict[str, Any], input_text: str) -> dict[str, Any]:
    """Tier 0 read: describe what applying the operator would entail."""
    return {
        "operator_id": op["id"],
        "name": op["name"],
        "family": op.get("domain"),
        "family_name": op.get("domain_name"),
        "definition": op.get("definition"),
        "advisory": (
            f"Operator {op['id']} ({op['name']}) — family {op.get('domain_name')}. "
            f"Applied to your input, this operator would: {op.get('definition', '').lower().rstrip('.')}."
        ),
        "input_excerpt": input_text[:200],
    }


def _apply_analytic(op: dict[str, Any], input_text: str) -> dict[str, Any]:
    """Tier 1 template: structured walkthrough using per-family template."""
    family = op.get("domain", "")
    template = _FAMILY_ANALYTIC_TEMPLATES.get(
        family,
        {
            "question": f"How does {op['name']} bear on this input?",
            "method": op.get("definition", "(no template registered for this family)"),
            "decision_point": "Identify the most consequential application.",
            "expected_output": "An analysis grounded in the operator's definition.",
        },
    )
    walkthrough = [
        {
            "step": 1,
            "name": "Question",
            "prompt": template["question"],
        },
        {
            "step": 2,
            "name": "Method",
            "prompt": (
                f"Apply {op['name']} ({op.get('definition', '').rstrip('.')}). "
                f"{template['method']}"
            ),
        },
        {
            "step": 3,
            "name": "Decision point",
            "prompt": template["decision_point"],
        },
        {
            "step": 4,
            "name": "Expected output",
            "prompt": template["expected_output"],
        },
    ]
    return {
        "operator_id": op["id"],
        "name": op["name"],
        "family": family,
        "family_name": op.get("domain_name"),
        "input_excerpt": input_text[:200],
        "walkthrough": walkthrough,
        "method": "family-template-v0.2",
    }


def _chat_complete(prompt: str, model: str = "") -> str | None:
    """One-shot Ollama chat completion. None on failure."""
    import urllib.error
    import urllib.request

    payload = json.dumps(
        {
            "model": model or OLLAMA_CHAT_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"think": False},
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        OLLAMA_CHAT_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=OLLAMA_CHAT_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        msg = data.get("message", {}).get("content")
        return msg if isinstance(msg, str) and msg.strip() else None
    except (urllib.error.URLError, OSError, ValueError, json.JSONDecodeError):
        return None


def _apply_empirical(op: dict[str, Any], input_text: str) -> dict[str, Any]:
    """Tier 1 execution: dispatch to local LLM to apply operator to input.

    On Ollama failure, degrades gracefully to analytic mode with a note.
    """
    prompt = (
        f"You are applying the reasoning operator {op['id']} ({op['name']}) "
        f"from the Base120 catalog. Family: {op.get('domain_name')}. "
        f"Definition: {op.get('definition')}.\n\n"
        f"Apply this operator to the following input. Produce a concrete "
        f"analysis showing the operator's characteristic move. Keep your "
        f"response under 250 words.\n\n"
        f"INPUT:\n{input_text}\n\n"
        f"ANALYSIS:"
    )
    completion = _chat_complete(prompt)
    if completion is None:
        # Degrade to analytic + flag
        result = _apply_analytic(op, input_text)
        result["method"] = "empirical-degraded-to-analytic"
        result["_note"] = "Ollama unreachable; returning analytic template instead."
        return result
    return {
        "operator_id": op["id"],
        "name": op["name"],
        "family": op.get("domain"),
        "family_name": op.get("domain_name"),
        "input_excerpt": input_text[:200],
        "analysis": completion,
        "method": "ollama-chat-v0.2",
        "model": OLLAMA_CHAT_MODEL,
    }


def _tool_apply(args: dict[str, Any]) -> dict[str, Any]:
    op_id = args.get("operator_id")
    input_text = args.get("input")
    mode = args.get("mode", "advisory")
    variant = args.get("variant", "base120")
    if not isinstance(op_id, str):
        raise JsonRpcError(INVALID_PARAMS, "operator_id must be a string")
    if not isinstance(input_text, str):
        raise JsonRpcError(INVALID_PARAMS, "input must be a string")
    if mode not in ("advisory", "analytic", "empirical"):
        raise JsonRpcError(
            INVALID_PARAMS,
            f"mode must be one of advisory|analytic|empirical; got {mode!r}",
        )

    op = _operator_by_id(variant, op_id)
    if op is None:
        raise JsonRpcError(INVALID_PARAMS, f"operator not found: {op_id!r}")

    # Mode dispatch. Tier mapping: advisory=0 (read), analytic=1, empirical=1.
    if mode == "advisory":
        body = _apply_advisory(op, input_text)
        tier = 0
    elif mode == "analytic":
        body = _apply_analytic(op, input_text)
        tier = 1
    else:  # empirical
        body = _apply_empirical(op, input_text)
        tier = 1

    return {
        "operator_id": op_id,
        "mode": mode,
        "variant": variant,
        **body,
        "_governance": _emit_tuple("apply", args, tier=tier),
    }


TOOL_HANDLERS = {
    "basen_operator_lookup": _tool_operator_lookup,
    "basen_family_browse": _tool_family_browse,
    "basen_recommend": _tool_recommend,
    "basen_apply": _tool_apply,
}


# ---------------------------------------------------------------------------
# Resources — URI-addressable, dispatched by pattern (not 127 handlers)
# ---------------------------------------------------------------------------


def _resource_list() -> list[dict[str, Any]]:
    """Enumerate all basen://base120/... resources (120 + 6 + 1 = 127)."""
    out: list[dict[str, Any]] = []
    for op in _registry("base120"):
        out.append(
            {
                "uri": f"basen://base120/operator/{op['id']}",
                "name": f"Operator {op['id']}: {op.get('name')}",
                "description": op.get("definition", ""),
                "mimeType": "application/json",
            }
        )
    for family_code, family_name in _FAMILY_NAMES.items():
        out.append(
            {
                "uri": f"basen://base120/family/{family_code}",
                "name": f"Family {family_code}: {family_name}",
                "description": f"All Base120 operators in the {family_name} family.",
                "mimeType": "application/json",
            }
        )
    out.append(
        {
            "uri": "basen://base120/manifest",
            "name": "Base120 catalog manifest",
            "description": "Full catalog of 120 operators + 6 families.",
            "mimeType": "application/json",
        }
    )
    return out


def _resource_read(uri: str) -> dict[str, Any]:
    """Read a basen:// resource by URI pattern."""
    if not uri.startswith("basen://base120/"):
        raise JsonRpcError(RESOURCE_NOT_FOUND, f"unknown resource scheme: {uri!r}")
    tail = uri[len("basen://base120/") :]

    if tail == "manifest":
        regs = _registry("base120")
        manifest = {
            "variant": "base120",
            "version": "v0.1",
            "operator_count": len(regs),
            "families": [
                {
                    "code": code,
                    "name": name,
                    "count": sum(1 for op in regs if op.get("domain") == code),
                }
                for code, name in _FAMILY_NAMES.items()
            ],
        }
        return {
            "contents": [
                {
                    "uri": uri,
                    "mimeType": "application/json",
                    "text": json.dumps(manifest, indent=2),
                }
            ]
        }

    if tail.startswith("operator/"):
        op_id = tail[len("operator/") :]
        op = _operator_by_id("base120", op_id)
        if op is None:
            raise JsonRpcError(RESOURCE_NOT_FOUND, f"operator not found: {op_id!r}")
        return {
            "contents": [
                {
                    "uri": uri,
                    "mimeType": "application/json",
                    "text": json.dumps(op, indent=2),
                }
            ]
        }

    if tail.startswith("family/"):
        family = tail[len("family/") :]
        if family not in _FAMILY_NAMES:
            raise JsonRpcError(RESOURCE_NOT_FOUND, f"family not found: {family!r}")
        ops = _operators_by_family("base120", family)
        body = {
            "family": family,
            "family_name": _FAMILY_NAMES[family],
            "count": len(ops),
            "operators": ops,
        }
        return {
            "contents": [
                {
                    "uri": uri,
                    "mimeType": "application/json",
                    "text": json.dumps(body, indent=2),
                }
            ]
        }

    raise JsonRpcError(RESOURCE_NOT_FOUND, f"unknown resource: {uri!r}")


# ---------------------------------------------------------------------------
# Prompts — 3 reusable BaseN starter prompts
# ---------------------------------------------------------------------------

MCP_PROMPTS: list[dict[str, Any]] = [
    {
        "name": "basen-recon",
        "description": "Apply BaseN to recon a problem.",
        "arguments": [
            {"name": "input", "description": "Problem statement.", "required": True},
        ],
    },
    {
        "name": "basen-spec",
        "description": "Use BaseN to convert intent into a spec.",
        "arguments": [
            {"name": "intent", "description": "Intent statement.", "required": True},
        ],
    },
    {
        "name": "basen-audit",
        "description": "Audit an artifact with BaseN.",
        "arguments": [
            {
                "name": "artifact_path",
                "description": "Path to the artifact under review.",
                "required": True,
            },
        ],
    },
]


def _prompt_get(name: str, args: dict[str, Any]) -> dict[str, Any]:
    if name == "basen-recon":
        text = (
            "Apply BaseN to recon this problem: "
            f"{args.get('input', '<input missing>')}\n\n"
            "Suggested operators: use basen_recommend with the problem description, "
            "then walk the top-3 operators with basen_apply mode=analytic."
        )
    elif name == "basen-spec":
        text = (
            "Use BaseN to convert intent to spec: "
            f"{args.get('intent', '<intent missing>')}\n\n"
            "Suggested operators: P15 Assumption Surfacing, DE8 Work Breakdown, "
            "CO9 Interface Contracts. Use basen_family_browse('DE') for full options."
        )
    elif name == "basen-audit":
        text = (
            "Audit this artifact with BaseN: "
            f"{args.get('artifact_path', '<path missing>')}\n\n"
            "Suggested operators: IN10 Red Teaming, IN12 Failure First Design, "
            "DE13 Failure Mode Analysis. Apply each with basen_apply mode=analytic."
        )
    else:
        raise JsonRpcError(PROMPT_NOT_FOUND, f"prompt not found: {name!r}")

    return {
        "description": next(
            (p["description"] for p in MCP_PROMPTS if p["name"] == name), name
        ),
        "messages": [
            {"role": "user", "content": {"type": "text", "text": text}},
        ],
    }


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------


def handle_request(method: str, params: dict[str, Any]) -> Any:
    """Uniform handler — maps MCP method names to internal handlers."""
    if method == "initialize":
        return {
            "protocolVersion": MCP_PROTOCOL_VERSION,
            "capabilities": {
                "tools": {"listChanged": False},
                "resources": {"listChanged": False, "subscribe": False},
                "prompts": {"listChanged": False},
            },
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
        }
    if method == "notifications/initialized":
        return None  # notification, no response
    if method == "ping":
        return {}
    if method == "tools/list":
        return {"tools": [t.to_obj() for t in MCP_TOOLS]}
    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments") or {}
        if not isinstance(name, str):
            raise JsonRpcError(INVALID_PARAMS, "tools/call: 'name' is required")
        if not isinstance(args, dict):
            raise JsonRpcError(
                INVALID_PARAMS, "tools/call: 'arguments' must be an object"
            )
        handler = TOOL_HANDLERS.get(name)
        if handler is None:
            raise JsonRpcError(TOOL_NOT_FOUND, f"tool not found: {name}")
        result = handler(args)
        return {
            "content": [
                {"type": "text", "text": json.dumps(result, indent=2, default=str)}
            ],
            "isError": False,
        }
    if method == "resources/list":
        return {"resources": _resource_list()}
    if method == "resources/read":
        uri = params.get("uri")
        if not isinstance(uri, str):
            raise JsonRpcError(INVALID_PARAMS, "resources/read: 'uri' is required")
        return _resource_read(uri)
    if method == "prompts/list":
        return {"prompts": MCP_PROMPTS}
    if method == "prompts/get":
        name = params.get("name")
        args = params.get("arguments") or {}
        if not isinstance(name, str):
            raise JsonRpcError(INVALID_PARAMS, "prompts/get: 'name' is required")
        return _prompt_get(name, args)

    raise JsonRpcError(METHOD_NOT_FOUND, f"method not found: {method}")


# ---------------------------------------------------------------------------
# stdio JSON-RPC loop
# ---------------------------------------------------------------------------


def _write_response(obj: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(obj, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def _error_obj(req_id: Any, err: JsonRpcError) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": req_id, "error": err.to_dict()}


def _success_obj(req_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def serve_stdio() -> None:
    """Read newline-delimited JSON-RPC from stdin, write responses to stdout."""
    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue
        req_id: Any = None
        try:
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                raise JsonRpcError(PARSE_ERROR, f"parse error: {e}") from e
            if not isinstance(obj, dict):
                raise JsonRpcError(INVALID_REQUEST, "request must be a JSON object")
            if obj.get("jsonrpc") != "2.0":
                raise JsonRpcError(INVALID_REQUEST, "jsonrpc must be '2.0'")
            method = obj.get("method")
            if not isinstance(method, str) or not method:
                raise JsonRpcError(INVALID_REQUEST, "method must be a non-empty string")
            params = obj.get("params") or {}
            if not isinstance(params, dict):
                raise JsonRpcError(INVALID_PARAMS, "params must be an object")
            req_id = obj.get("id")
            is_notification = "id" not in obj

            try:
                result = handle_request(method, params)
            except JsonRpcError:
                raise
            except Exception as e:  # noqa: BLE001
                raise JsonRpcError(
                    INTERNAL_ERROR, f"internal error: {type(e).__name__}: {e}"
                ) from e

            if is_notification:
                continue
            _write_response(_success_obj(req_id, result))
        except JsonRpcError as err:
            # If we have no id (notification), suppress reply
            _write_response(_error_obj(req_id, err))


if __name__ == "__main__":  # pragma: no cover
    serve_stdio()


def main() -> None:
    """Console entry point for hummbl-mcp-basen."""
    serve_stdio()
