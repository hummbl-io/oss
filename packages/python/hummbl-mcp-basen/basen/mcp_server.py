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

from .domain120_catalogs import TOOL_NAMES as DOMAIN120_TOOL_NAMES
from .domain120_catalogs import load_catalogs
from .domain120_catalogs import tool_definitions as domain120_tool_definitions
from .domain120_inspection import InspectionError

# A fully validated, explicitly configured snapshot. No import-time file reads.
_DOMAIN120_SERVICE = None


def _configure_domain120() -> None:
    """Select the optional inspection snapshot once at stdio startup."""
    global _DOMAIN120_SERVICE
    _DOMAIN120_SERVICE = None
    manifest = os.environ.get("BASEN_DOMAIN120_MANIFEST")
    digest = os.environ.get("BASEN_DOMAIN120_MANIFEST_SHA256")
    if manifest is None and digest is None:
        return
    if not manifest or not digest:
        raise InspectionError("Both Domain120 configuration variables are required")
    _DOMAIN120_SERVICE = load_catalogs(manifest, digest)


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


def _registry_json_bytes(value: Any) -> bytes:
    """Named Python JSON recipe for content observation, not RFC 8785."""
    def check(item):
        if isinstance(item, dict):
            if any(not isinstance(key, str) for key in item):
                raise ValueError("Non-string JSON key")
            for child in item.values():
                check(child)
        elif isinstance(item, list):
            for child in item:
                check(child)
        elif item is not None and type(item) not in (str, int, float, bool):
            raise ValueError("Non-JSON value")
    check(value)
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("utf-8")


def _unique_registry_json(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate registry JSON key")
        result[key] = value
    return result


def _reject_registry_constant(value):
    raise ValueError("Non-finite registry JSON constant")


@dataclass(frozen=True)
class _RegistrySourceObservation:
    artifact_sha256: str
    normalized_content_sha256: str


class _LoadedRegistry(list):
    """Legacy list interface with an immutable observation of its loaded bytes.

    The list remains mutable for compatibility. Application capture compares its
    current content to this observation before claiming a raw-artifact binding.
    """
    __slots__ = ("_source_observation",)

    def __init__(self, rows, source):
        super().__init__(rows)
        self._source_observation = source

    @property
    def source_observation(self):
        return self._source_observation


def _load_registry(variant: str = "base120") -> list[dict[str, Any]]:
    """Load operator records for a variant. Cached in-process at module level."""
    if variant != "base120":
        # TODO: future variant dispatch (base49, base12-lite, etc.)
        raise JsonRpcError(
            INVALID_PARAMS,
            f"unknown variant: {variant!r} (only 'base120' supported in v0.1)",
        )

    try:
        raw = DEFAULT_REGISTRY_JSON.read_bytes()
        data = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_registry_json,
                          parse_constant=_reject_registry_constant)
        if not isinstance(data, list):
            raise TypeError("Registry root must be an array")
        source = _RegistrySourceObservation(
            hashlib.sha256(raw).hexdigest(),
            hashlib.sha256(_registry_json_bytes(data)).hexdigest())
        return _LoadedRegistry(data, source)
    except (OSError, ValueError, TypeError, RecursionError, OverflowError):
        raise JsonRpcError(INTERNAL_ERROR, "Registry input is unavailable or invalid") from None


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


def _capture_application_operator(variant: str, operator_id: str):
    """Select from one detached content snapshot before any execution effect."""
    if not isinstance(variant, str):
        raise JsonRpcError(INVALID_PARAMS, "variant must be a string")
    rows = _registry(variant)
    source = rows.source_observation if isinstance(rows, _LoadedRegistry) else None
    try:
        if not isinstance(rows, list):
            raise TypeError("Registry must be an array")
        encoded = _registry_json_bytes(rows)
        captured = json.loads(encoded)
        by_id = {}
        for row in captured:
            if not isinstance(row, dict):
                raise TypeError("Registry row must be an object")
            key = row.get("id")
            if not isinstance(key, str) or not key.strip() or key in by_id:
                raise ValueError("Registry IDs must be unique nonempty strings")
            by_id[key] = row
        op = by_id.get(operator_id)
        if op is not None:
            if any(not isinstance(op.get(field), str) for field in ("name", "definition")):
                raise ValueError("Selected record text must be strings")
            if "domain" in op and not isinstance(op["domain"], str):
                raise ValueError("Selected family must be a string")
    except (ValueError, TypeError, RecursionError, OverflowError):
        raise JsonRpcError(INTERNAL_ERROR, "Registry content cannot support application capture") from None
    if op is None:
        raise JsonRpcError(INVALID_PARAMS, f"operator not found: {operator_id!r}")
    content_sha = hashlib.sha256(encoded).hexdigest()
    if source is None:
        binding, artifact_sha = "raw-source-unavailable", None
    elif source.normalized_content_sha256 != content_sha:
        binding, artifact_sha = "cache-content-changed", None
    else:
        binding, artifact_sha = "loaded-bytes-matched", source.artifact_sha256
    observation = {
        "schema": "hummbl.basen.registry-observation.v1",
        "artifact_sha256": artifact_sha,
        "normalized_content_sha256": content_sha,
        "operator_content_sha256": hashlib.sha256(_registry_json_bytes(op)).hexdigest(),
        "artifact_binding": binding,
        "content_hash_format": "utf8-python-json-sorted-compact-ascii-no-nonfinite-v1",
        "registry_version": None,
        "source_authority": "not authenticated",
        "semantic_validation": "not performed",
        "admission": "not assessed",
    }
    return op, observation


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

    Prefer the bundled BaseNTuple writer when importable. A compatibility
    appender is used only when that import is unavailable. Once a writer is
    attempted, never retry through another writer: an error may leave bytes.
    True means the writer returned; it is not independent durability evidence.
    """
    try:
        _TUPLE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        return False

    line = json.dumps(record, separators=(",", ":"), sort_keys=True) + "\n"

    # Import availability is separate from constructing or invoking the writer.
    try:
        from basen.basen_tuple import (  # type: ignore
            BaseNTuple,
            append_tuple,
        )
    except ImportError:
        append_tuple = None

    if append_tuple is not None:
        import uuid as _uuid

        try:
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
        except Exception:  # noqa: BLE001 — a failed write must never select a second appender
            return False
        return True

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
    *,
    report_persistence: bool = False,
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
        if report_persistence:
            rec["persistence_status"] = "not_applicable"
        return rec

    if os.environ.get("BASEN_PERSIST_TUPLES", "1") != "0":
        rec["persisted"] = _append_tuple_jsonl(rec)
        persistence_status = "saved" if rec["persisted"] else "failed"
    else:
        rec["persisted"] = False
        persistence_status = "disabled"
    if report_persistence:
        rec["persistence_status"] = persistence_status
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
            "Uses embeddings with an explicit keyword fallback when embeddings are unavailable. "
            "May contact the configured embedding endpoint and write local cache files."
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

_EMBED_CACHE_SCHEMA = "hummbl.basen.operator-embeddings.v1"


@dataclass(frozen=True, repr=False)
class _EmbeddingInputs:
    # Do not expose the endpoint through repr or persisted cache metadata.
    items: tuple[tuple[str, str], ...]
    model: str
    endpoint: str
    fingerprint: str


def _embedding_inputs(registry: list[dict[str, Any]]) -> _EmbeddingInputs | None:
    """Capture exactly the text and configuration used by this computation."""
    if not isinstance(registry, list) or not registry:
        return None
    model, endpoint = OLLAMA_EMBED_MODEL, OLLAMA_EMBED_URL
    if not isinstance(model, str) or not model or not isinstance(endpoint, str) or not endpoint:
        return None
    items: list[tuple[str, str]] = []
    seen: set[str] = set()
    for op in registry:
        if not isinstance(op, dict):
            return None
        operator_id = op.get("id")
        if not isinstance(operator_id, str) or not operator_id or operator_id in seen:
            return None
        seen.add(operator_id)
        items.append((operator_id, _operator_corpus_text(op)))
    payload = json.dumps({"schema": _EMBED_CACHE_SCHEMA, "model": model,
                          "endpoint": endpoint, "operators": items},
                         sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    fingerprint = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return _EmbeddingInputs(tuple(items), model, endpoint, fingerprint)


def _unique_embedding_json(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate embedding JSON key")
        result[key] = value
    return result


def _embedding_vector(value) -> list[float] | None:
    """Reject coerced, non-finite, empty and zero vectors before using them."""
    import math

    if not isinstance(value, list) or not value:
        return None
    if any(type(item) not in (int, float) for item in value):
        return None
    try:
        vector = [float(item) for item in value]
    except (OverflowError, ValueError):
        return None
    if not all(math.isfinite(item) for item in vector) or not any(vector):
        return None
    return vector


def _embedding_set(value, inputs: _EmbeddingInputs) -> dict[str, list[float]] | None:
    if not isinstance(value, dict) or set(value) != {key for key, _ in inputs.items}:
        return None
    result = {}
    dimension = None
    for key, _ in inputs.items:
        vector = _embedding_vector(value[key])
        if vector is None or (dimension is not None and len(vector) != dimension):
            return None
        dimension = len(vector)
        result[key] = vector
    return result


def _embed_text(text: str, *, model: str | None = None,
                endpoint: str | None = None) -> list[float] | None:
    """Embed through the configured endpoint; safely return None on failure."""
    import http.client
    import urllib.error
    import urllib.request

    try:
        payload = json.dumps({"model": OLLAMA_EMBED_MODEL if model is None else model,
                              "prompt": text}).encode("utf-8")
        req = urllib.request.Request(
            OLLAMA_EMBED_URL if endpoint is None else endpoint,
            data=payload, headers={"Content-Type": "application/json"}, method="POST",
        )
        with urllib.request.urlopen(req, timeout=OLLAMA_EMBED_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"), object_pairs_hook=_unique_embedding_json)
        return _embedding_vector(data.get("embedding")) if isinstance(data, dict) else None
    except (urllib.error.URLError, http.client.HTTPException, OSError,
            ValueError, TypeError, OverflowError, RecursionError):
        return None


def _registry_fingerprint(registry: list[dict[str, Any]]) -> str | None:
    """Computation identity, not a source-authentication or admission digest."""
    inputs = _embedding_inputs(registry)
    return inputs.fingerprint if inputs is not None else None


def _new_embedding_observation() -> dict[str, Any]:
    return {
        "computation_fingerprint": None,
        "configured_model": None,
        "operator_cache_read": "not_attempted",
        "operator_cache_write": "not_attempted",
        "operator_embedding_calls": 0,
        "query_embedding_calls": 0,
        "failure_stage": None,
    }


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
    variant: str, *, inputs: _EmbeddingInputs | None = None,
    observation: dict[str, Any] | None = None,
) -> dict[str, list[float]] | None:
    """Reuse a complete matching vector set, or compute it from captured inputs."""
    if observation is None:
        observation = _new_embedding_observation()
    if inputs is None:
        inputs = _embedding_inputs(_registry(variant))
    if inputs is None:
        return None
    cache_path = EMBED_CACHE_DIR / f"embeddings_v1_{variant}_{inputs.fingerprint}.json"

    try:
        with cache_path.open(encoding="utf-8") as f:
            cached = json.load(f, object_pairs_hook=_unique_embedding_json)
        if (isinstance(cached, dict)
                and set(cached) == {"schema", "fingerprint", "dimension", "embeddings"}
                and cached["schema"] == _EMBED_CACHE_SCHEMA
                and cached["fingerprint"] == inputs.fingerprint
                and type(cached["dimension"]) is int):
            vectors = _embedding_set(cached["embeddings"], inputs)
            if vectors is not None and cached["dimension"] == len(next(iter(vectors.values()))):
                observation["operator_cache_read"] = "hit"
                return vectors
        observation["operator_cache_read"] = "invalid"
    except FileNotFoundError:
        observation["operator_cache_read"] = "miss"
    except OSError:
        observation["operator_cache_read"] = "unavailable"
    except (ValueError, RecursionError):
        observation["operator_cache_read"] = "invalid"

    # Fail on the first invalid result; never persist a partial vector set.
    embeddings: dict[str, list[float]] = {}
    dimension = None
    for operator_id, text in inputs.items:
        observation["operator_embedding_calls"] += 1
        vector = _embedding_vector(_embed_text(text, model=inputs.model, endpoint=inputs.endpoint))
        if vector is None or (dimension is not None and len(vector) != dimension):
            return None
        dimension = len(vector)
        embeddings[operator_id] = vector

    try:
        EMBED_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with cache_path.open("w", encoding="utf-8") as f:
            json.dump({"schema": _EMBED_CACHE_SCHEMA, "fingerprint": inputs.fingerprint,
                       "dimension": dimension, "embeddings": embeddings}, f, allow_nan=False)
        observation["operator_cache_write"] = "write_returned"
    except OSError:
        observation["operator_cache_write"] = "failed"

    return embeddings


def _cosine_similarity(a: list[float], b: list[float]) -> float | None:
    """Stable cosine in [-1, 1]; None for invalid, zero or mismatched vectors."""
    import math

    left, right = _embedding_vector(a), _embedding_vector(b)
    if left is None or right is None or len(left) != len(right):
        return None
    scaled = []
    for vector in (left, right):
        scale = max(abs(item) for item in vector)
        values = [item / scale for item in vector]
        norm = math.sqrt(math.fsum(item * item for item in values))
        scaled.append([item / norm for item in values])
    score = math.fsum(x * y for x, y in zip(*scaled))
    return max(-1.0, min(1.0, score)) if math.isfinite(score) else None


def _recommend_via_embeddings(
    desc: str, variant: str, top_k: int, *,
    registry: list[dict[str, Any]] | None = None,
    observation: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Return None on invalid vectors or computation failure for explicit fallback."""
    import math

    if registry is None:
        registry, _ = _capture_recommendation_registry(variant)
    if observation is None:
        observation = _new_embedding_observation()
    inputs = _embedding_inputs(registry)
    if inputs is None:
        observation["failure_stage"] = "embedding_inputs"
        return None
    observation["computation_fingerprint"] = inputs.fingerprint
    observation["configured_model"] = inputs.model
    op_embeddings = _embedding_set(_load_or_compute_operator_embeddings(
        variant, inputs=inputs, observation=observation), inputs)
    if op_embeddings is None:
        observation["failure_stage"] = "operator_embeddings"
        return None
    observation["query_embedding_calls"] += 1
    query_emb = _embedding_vector(_embed_text(desc, model=inputs.model, endpoint=inputs.endpoint))
    if query_emb is None or len(query_emb) != len(next(iter(op_embeddings.values()))):
        observation["failure_stage"] = "query_embedding"
        return None

    scored: list[tuple[dict[str, Any], float]] = []
    for op in registry:
        score = _cosine_similarity(query_emb, op_embeddings[op["id"]])
        if score is None or not math.isfinite(score):
            observation["failure_stage"] = "similarity"
            return None
        scored.append((op, score))
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
        "embedding_model": inputs.model,
    }


def _capture_recommendation_registry(variant: str):
    """Detach all participating records before cache or embedding effects."""
    if not isinstance(variant, str):
        raise JsonRpcError(INVALID_PARAMS, "variant must be a string")
    rows = _registry(variant)
    source = rows.source_observation if isinstance(rows, _LoadedRegistry) else None
    try:
        if not isinstance(rows, list):
            raise TypeError("Registry must be an array")
        encoded = _registry_json_bytes(rows)
        captured = json.loads(encoded)
        seen = set()
        for row in captured:
            if not isinstance(row, dict):
                raise TypeError("Registry row must be an object")
            key = row.get("id")
            if not isinstance(key, str) or not key.strip() or key in seen:
                raise ValueError("Registry IDs must be unique nonempty strings")
            seen.add(key)
            if any(not isinstance(row.get(field), str) for field in ("name", "definition")):
                raise ValueError("Participating record text must be strings")
            if any(field in row and not isinstance(row[field], str)
                   for field in ("domain", "domain_name")):
                raise ValueError("Participating family text must be strings")
    except (ValueError, TypeError, RecursionError, OverflowError):
        raise JsonRpcError(INTERNAL_ERROR, "Registry content cannot support recommendation capture") from None
    content_sha = hashlib.sha256(encoded).hexdigest()
    if source is None:
        binding, artifact_sha = "raw-source-unavailable", None
    elif source.normalized_content_sha256 != content_sha:
        binding, artifact_sha = "cache-content-changed", None
    else:
        binding, artifact_sha = "loaded-bytes-matched", source.artifact_sha256
    return captured, {
        "artifact_sha256": artifact_sha,
        "normalized_content_sha256": content_sha,
        "artifact_binding": binding,
        "content_hash_format": "utf8-python-json-sorted-compact-ascii-no-nonfinite-v1",
        "registry_version": None,
        "source_authority": "not authenticated",
        "semantic_validation": "not performed",
        "admission": "not assessed",
    }


def _recommendation_result(body, args, registry, registry_observation, embedding_observation):
    by_id = {row["id"]: row for row in registry}
    selection = {
        "schema": "hummbl.basen.recommendation-observation.v1",
        "variant": body["variant"],
        "actual_method": body["method"],
        "fallback_used": body["method"] == "keyword-overlap-v0.1-fallback",
        "registry": registry_observation,
        "selected_operators": [
            {"operator_id": row["operator_id"],
             "operator_content_sha256": hashlib.sha256(
                 _registry_json_bytes(by_id[row["operator_id"]])).hexdigest()}
            for row in body["recommendations"]
        ],
        "embedding": embedding_observation,
    }
    return {
        **body,
        "_selection": selection,
        "_governance": _emit_tuple("recommend", args, tier=0,
                                   evidence={"recommendation": json.loads(_registry_json_bytes(selection))}),
    }


def _tool_recommend(args: dict[str, Any]) -> dict[str, Any]:
    desc = args.get("problem_description")
    variant = args.get("variant", "base120")
    top_k = int(args.get("top_k", 3))
    if not isinstance(desc, str) or not desc.strip():
        raise JsonRpcError(
            INVALID_PARAMS, "problem_description must be a non-empty string"
        )

    registry, registry_observation = _capture_recommendation_registry(variant)
    embedding_observation = _new_embedding_observation()
    # Try embedding-based recommender first (v0.2). Falls back to keyword
    # overlap on Ollama failure to keep the tool responsive in degraded mode.
    emb_result = _recommend_via_embeddings(desc, variant, top_k, registry=registry,
                                          observation=embedding_observation)
    if emb_result is not None:
        return _recommendation_result({
            "problem_description": desc,
            **emb_result,
            "variant": variant,
        }, args, registry, registry_observation, embedding_observation)

    # Fallback: lowercased keyword tokens (>=4 chars) for naive overlap scoring.
    tokens = [
        t
        for t in "".join(c.lower() if c.isalnum() else " " for c in desc).split()
        if len(t) >= 4
    ]
    scored = [(op, _score_operator(op, tokens)) for op in registry]
    scored.sort(key=lambda x: x[1], reverse=True)
    top = scored[: max(1, top_k)]
    return _recommendation_result({
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
    }, args, registry, registry_observation, embedding_observation)


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


def _chat_complete(prompt: str, model: str | None = None, *, endpoint: str | None = None) -> str | None:
    """One-shot Ollama chat completion. None on failure."""
    import http.client
    import urllib.error
    import urllib.request

    try:
        selected_model = OLLAMA_CHAT_MODEL if model is None else model
        selected_endpoint = OLLAMA_CHAT_URL if endpoint is None else endpoint
        if (not isinstance(selected_model, str) or not selected_model.strip()
                or not isinstance(selected_endpoint, str) or not selected_endpoint.strip()):
            return None
        payload = json.dumps(
            {
                "model": selected_model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "options": {"think": False},
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            selected_endpoint,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=OLLAMA_CHAT_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if not isinstance(data, dict) or not isinstance(data.get("message"), dict):
            return None
        msg = data["message"].get("content")
        return msg if isinstance(msg, str) and msg.strip() else None
    except (urllib.error.URLError, http.client.HTTPException, OSError,
            ValueError, TypeError, OverflowError, RecursionError):
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
    model, endpoint = OLLAMA_CHAT_MODEL, OLLAMA_CHAT_URL
    completion = None
    if (isinstance(model, str) and model.strip()
            and isinstance(endpoint, str) and endpoint.strip()):
        completion = _chat_complete(prompt, model=model, endpoint=endpoint)
    if completion is None:
        # Degrade to analytic + flag
        result = _apply_analytic(op, input_text)
        result["method"] = "empirical-degraded-to-analytic"
        result["_note"] = "Usable chat completion unavailable; returning analytic template instead."
        return result
    return {
        "operator_id": op["id"],
        "name": op["name"],
        "family": op.get("domain"),
        "family_name": op.get("domain_name"),
        "input_excerpt": input_text[:200],
        "analysis": completion,
        "method": "ollama-chat-v0.2",
        "model": model,
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

    op, registry_observation = _capture_application_operator(variant, op_id)

    # Mode dispatch. Tier mapping: advisory=0 (read), analytic=1, empirical=1.
    if mode == "advisory":
        body = _apply_advisory(op, input_text)
        tier = 0
        actual_mode, actual_method = "advisory", "operator-description-v0.1"
    elif mode == "analytic":
        body = _apply_analytic(op, input_text)
        tier = 1
        actual_mode, actual_method = "analytic", "family-template-v0.2"
    else:  # empirical
        body = _apply_empirical(op, input_text)
        tier = 1
        if body["method"] == "empirical-degraded-to-analytic":
            actual_mode, actual_method = "analytic", "family-template-v0.2"
        else:
            actual_mode, actual_method = "empirical", "ollama-chat-v0.2"

    application = {
        "variant": variant,
        "operator_id": op_id,
        "requested_mode": mode,
        "actual_mode": actual_mode,
        "actual_method": actual_method,
        "fallback_used": mode != actual_mode,
        "registry": registry_observation,
    }
    if application["fallback_used"]:
        application["fallback_reason"] = "completion_unavailable"
    if actual_mode == "empirical":
        application["configured_model"] = body["model"]

    return {
        "operator_id": op_id,
        "mode": mode,
        "variant": variant,
        **body,
        "_execution": application,
        "_governance": _emit_tuple("apply", args, tier=tier,
                                   evidence={"application": {**application,
                                                             "registry": registry_observation.copy()}},
                                   report_persistence=True),
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
        extra = domain120_tool_definitions() if _DOMAIN120_SERVICE is not None else []
        return {"tools": [t.to_obj() for t in MCP_TOOLS] + extra}
    if method == "tools/call":
        name = params.get("name")
        if isinstance(name, str) and name in DOMAIN120_TOOL_NAMES:
            if _DOMAIN120_SERVICE is None:
                raise JsonRpcError(TOOL_NOT_FOUND, "Domain120 inspection is not configured")
            # Preserve explicitly supplied malformed/falsey values for validation.
            # This scoped branch leaves the existing Base120 handlers unchanged.
            arguments = params.get("arguments", {})
            try:
                result = _DOMAIN120_SERVICE.call(name, arguments)
                serialized = json.dumps(result, indent=2)
            except InspectionError as exc:
                raise JsonRpcError(
                    INVALID_PARAMS,
                    "Domain120 inspection request rejected; use the tool schema and an exact listed catalog identity",
                ) from exc
            except Exception as exc:
                # Never expose private source payloads or exception/path details.
                raise JsonRpcError(INTERNAL_ERROR, "Domain120 inspection failed") from exc
            return {"content": [{"type": "text", "text": serialized}],
                    "isError": False}
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
    try:
        _configure_domain120()
    except Exception:  # noqa: BLE001 — startup errors must not disclose source content
        # Fail before initialization/tool discovery; do not leak source content.
        sys.stderr.write("Domain120 inspection configuration rejected.\n")
        raise SystemExit(2) from None
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
            except Exception as e:
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
