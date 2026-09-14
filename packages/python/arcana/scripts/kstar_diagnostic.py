"""K* / pairwise-similarity diagnostic for ARCANA lens outputs.

Yang et al. (arXiv:2602.03794) define K* as the effective channel count of a
multi-agent system: embed each agent's output, take the Shannon entropy of the
normalized covariance (or Gram) eigenvalues, K* = exp(H). Homogeneous swarms
saturate; 2 diverse agents can match 16 homogeneous ones.

The math (L2-normalize -> Gram -> trace-normalize -> Jacobi eigenvalues ->
exp(Shannon entropy)) is a faithful reproduction of the paper's Eq. 16-18;
2^H (paper) == e^H_natural (here), bit-identical. The only degree of freedom
is Emb(.): the embedding function. Two modes:

  --embed tfidf   (default) word unigram+bigram TF-IDF, L2-normalized.
                  Lexical diversity only. No Ollama, no third-party deps.
                  Report as `kstar_tfidf`. Blind to paraphrase (two texts that
                  say the same thing in different words score as unrelated).

  --embed ollama  nomic-embed-text (768-dim) via Ollama /api/embed.
                  Semantic diversity: catches paraphrase TF-IDF cannot.
                  Requires Ollama running with the model pulled.
                  Report as `kstar_semantic` + `embed_model`.

K* is embedding-model-dependent (Yang et al. App. B.2: r=0.40 NV-Embed-v2 vs
r=0.23 gte-Qwen2). The `embed_model` field makes the choice reproducible.

Modes (input source):
  --topic-dir DIR     one overnight output dir with perspective_*.json
  --outputs-dir DIR   scan outputs/YYYY-MM-DD/slug/ trees
  --lenses-json PATH  measure prompt-space diversity of lenses.json
                      (used when no overnight outputs exist)
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_OUTPUTS = HERE / "outputs"
DEFAULT_LENSES = HERE / "lenses.json"
SHARED_SCHEMA_RE = re.compile(r"\s*Return JSON with keys:.*$", re.I | re.S)
TOKEN_RE = re.compile(r"[a-z0-9]{2,}")


def _as_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(_as_text(x) for x in value if x)
    if isinstance(value, dict):
        return "\n".join(f"{k}: {_as_text(v)}" for k, v in value.items())
    return str(value)


def perspective_text(obj: dict) -> str:
    """Flatten a perspective_*.json object into comparable text."""
    parsed = obj.get("parsed") if isinstance(obj.get("parsed"), dict) else {}
    parts = [
        _as_text(parsed.get("perspective")),
        _as_text(parsed.get("key_claims")),
        _as_text(parsed.get("blind_spots")),
        _as_text(obj.get("content")),
        _as_text(obj.get("raw")),
    ]
    return "\n".join(p for p in parts if p).strip()


def tokenize(text: str) -> list[str]:
    words = TOKEN_RE.findall(text.lower())
    grams = list(words)
    grams.extend(f"{a}_{b}" for a, b in zip(words, words[1:]))
    return grams


def tfidf_matrix(texts: list[str]) -> list[list[float]]:
    docs = [tokenize(t) for t in texts]
    n = len(docs)
    df: Counter[str] = Counter()
    for tokens in docs:
        df.update(set(tokens))
    vocab = sorted(df)
    idf = [math.log((1 + n) / (1 + df[term])) + 1.0 for term in vocab]
    index = {term: i for i, term in enumerate(vocab)}
    matrix: list[list[float]] = []
    for tokens in docs:
        tf = Counter(tokens)
        vec = [0.0] * len(vocab)
        for term, count in tf.items():
            j = index.get(term)
            if j is None:
                continue
            vec[j] = count * idf[j]
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        matrix.append([x / norm for x in vec])
    return matrix


def _l2_normalize(vectors: list[list[float]]) -> list[list[float]]:
    """L2-normalize each vector. Idempotent safety net: Ollama /api/embed
    already returns unit vectors, but /api/embeddings (legacy) does not, and a
    future embed_fn might not. Cheap to keep."""
    out = []
    for vec in vectors:
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        out.append([x / norm for x in vec])
    return out


def ollama_embed(endpoint_url: str, texts: list[str], *,
                 model: str = "nomic-embed-text",
                 timeout: int = 300) -> list[list[float]]:
    """Embed texts via Ollama /api/embed (batch, returns unit-normalized).

    Mirrors the stdlib urllib pattern in ollama_client.py / overnight_v0.py.
    Raises urllib.error.URLError on connection failure; ValueError on a
    malformed response (missing/short `embeddings` list).
    """
    url = endpoint_url.rstrip("/") + "/api/embed"
    payload = {"model": model, "input": texts}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    embeddings = body.get("embeddings")
    if not isinstance(embeddings, list) or len(embeddings) != len(texts):
        raise ValueError(
            f"Ollama /api/embed returned {len(embeddings) if isinstance(embeddings, list) else 'non-list'} "
            f"embeddings for {len(texts)} inputs")
    return [list(map(float, vec)) for vec in embeddings]


def gram_matrix(vectors: list[list[float]]) -> list[list[float]]:
    n = len(vectors)
    gram = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i, n):
            dot = sum(a * b for a, b in zip(vectors[i], vectors[j]))
            gram[i][j] = gram[j][i] = dot
    return gram


def jacobi_eigenvalues(matrix: list[list[float]], *,
                       max_sweeps: int = 64, tol: float = 1e-12) -> list[float]:
    """Eigenvalues of a real symmetric matrix via Jacobi rotations."""
    n = len(matrix)
    a = [row[:] for row in matrix]
    for _ in range(max_sweeps):
        p = q = 0
        max_off = 0.0
        for i in range(n):
            for j in range(i + 1, n):
                val = abs(a[i][j])
                if val > max_off:
                    max_off = val
                    p, q = i, j
        if max_off < tol:
            break
        app, aqq, apq = a[p][p], a[q][q], a[p][q]
        theta = 0.5 * math.atan2(2.0 * apq, aqq - app) if (aqq - app) else (
            math.pi / 4.0)
        c, s = math.cos(theta), math.sin(theta)
        for k in range(n):
            if k == p or k == q:
                continue
            akp, akq = a[k][p], a[k][q]
            a[k][p] = a[p][k] = c * akp - s * akq
            a[k][q] = a[q][k] = s * akp + c * akq
        a[p][p] = c * c * app - 2 * s * c * apq + s * s * aqq
        a[q][q] = s * s * app + 2 * s * c * apq + c * c * aqq
        a[p][q] = a[q][p] = 0.0
    return [a[i][i] for i in range(n)]


def kstar_from_eigenvalues(eigs: list[float], eps: float = 1e-12) -> float:
    clipped = [max(lam, 0.0) for lam in eigs]
    total = sum(clipped)
    if total <= eps:
        return 0.0
    probs = [lam / total for lam in clipped if lam > eps]
    entropy = -sum(p * math.log(p) for p in probs)
    return math.exp(entropy)


def greedy_clusters(gram: list[list[float]], threshold: float) -> int:
    n = len(gram)
    assigned = [False] * n
    clusters = 0
    for i in range(n):
        if assigned[i]:
            continue
        clusters += 1
        assigned[i] = True
        for j in range(i + 1, n):
            if not assigned[j] and gram[i][j] >= threshold:
                assigned[j] = True
    return clusters


def diagnose(named_texts: list[tuple[str, str]], *,
             embed_fn=None, embed_model: str | None = None) -> dict:
    """Compute K* and pairwise stats for a set of named texts.

    embed_fn: optional Callable[[list[str]], list[list[float]]]. If None, fall
    back to TF-IDF (lexical, offline). If provided, must return one raw vector
    per input text, all the same dimensionality. Vectors are L2-normalized
    here regardless (idempotent for /api/embed which already unit-normalizes).

    embed_model: name of the embedding model, recorded in the report for
    reproducibility (K* is embedding-model-dependent per Yang et al. App. B.2).
    Only emitted when embed_fn is provided.
    """
    names = [n for n, t in named_texts]
    texts = [t for _, t in named_texts]
    n = len(texts)
    semantic = embed_fn is not None
    kstar_field = "kstar_semantic" if semantic else "kstar_tfidf"
    base: dict = {
        "embed_method": "ollama" if semantic else "tfidf",
        "method": (
            f"ollama {embed_model or 'embed'} + Jacobi Gram entropy; "
            "semantic K* per Yang et al."
            if semantic else
            "tfidf-unigram-bigram + Jacobi Gram entropy; proxy not paper K*"
        ),
    }
    if semantic:
        base["embed_model"] = embed_model
    if n == 0:
        return {"n": 0, "error": "no texts", **base}
    if n == 1:
        return {
            "n": 1,
            "names": names,
            kstar_field: 1.0,
            "mean_pairwise_cosine": None,
            "median_pairwise_cosine": None,
            "frac_pairs_cosine_ge_0_80": None,
            "clusters_cosine_0_80": 1,
            "empty_texts": 0 if texts[0].strip() else 1,
            **base,
        }
    if semantic:
        vectors = embed_fn(texts)
        if not isinstance(vectors, list) or len(vectors) != n:
            raise ValueError(
                f"embed_fn must return {n} vectors, got "
                f"{len(vectors) if isinstance(vectors, list) else type(vectors).__name__}")
        dim = len(vectors[0]) if vectors and isinstance(vectors[0], list) else 0
        for i, vec in enumerate(vectors):
            if not isinstance(vec, list) or len(vec) != dim or dim == 0:
                raise ValueError(
                    f"embed_fn returned malformed vector at index {i} "
                    f"(dim={dim}, got {len(vec) if isinstance(vec, list) else 'non-list'})")
        vectors = _l2_normalize(vectors)
    else:
        vectors = tfidf_matrix(texts)
    gram = gram_matrix(vectors)
    pairs = [gram[i][j] for i in range(n) for j in range(i + 1, n)]
    pairs_sorted = sorted(pairs)
    mid = len(pairs_sorted) // 2
    median = pairs_sorted[mid] if len(pairs_sorted) % 2 else (
        pairs_sorted[mid - 1] + pairs_sorted[mid]) / 2
    eigs = jacobi_eigenvalues(gram)
    return {
        "n": n,
        "names": names,
        kstar_field: round(kstar_from_eigenvalues(eigs), 4),
        "mean_pairwise_cosine": round(sum(pairs) / len(pairs), 4),
        "median_pairwise_cosine": round(median, 4),
        "frac_pairs_cosine_ge_0_80": round(
            sum(1 for x in pairs if x >= 0.80) / len(pairs), 4),
        "clusters_cosine_0_80": greedy_clusters(gram, 0.80),
        "empty_texts": sum(1 for t in texts if not t.strip()),
        **base,
    }


def load_topic_dir(path: Path) -> list[tuple[str, str]]:
    files = sorted(path.glob("perspective_*.json"))
    out: list[tuple[str, str]] = []
    for f in files:
        data = json.loads(f.read_text(encoding="utf-8"))
        name = data.get("lens") or f.stem.removeprefix("perspective_")
        out.append((str(name), perspective_text(data)))
    return out


def iter_output_topics(outputs_dir: Path) -> list[Path]:
    topics: list[Path] = []
    if not outputs_dir.is_dir():
        return topics
    for date_dir in sorted(outputs_dir.iterdir()):
        if not date_dir.is_dir():
            continue
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_dir.name):
            continue
        for slug_dir in sorted(date_dir.iterdir()):
            if slug_dir.is_dir() and list(slug_dir.glob("perspective_*.json")):
                if slug_dir.name.startswith(("smoke", "test-")):
                    continue
                topics.append(slug_dir)
    return topics


def load_lenses_prompts(path: Path, strip_shared: bool = True) -> list[tuple[str, str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    lenses = data.get("lenses") or {}
    out: list[tuple[str, str]] = []
    for name, spec in lenses.items():
        system = spec.get("system") or ""
        if strip_shared:
            system = SHARED_SCHEMA_RE.sub("", system).strip()
        out.append((name, system))
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    src = p.add_mutually_exclusive_group()
    src.add_argument("--topic-dir", help="one overnight output directory")
    src.add_argument("--outputs-dir", help="scan overnight outputs tree")
    src.add_argument("--lenses-json", help="measure lenses.json prompt diversity")
    p.add_argument("--keep-shared-suffix", action="store_true",
                   help="do not strip the shared Return-JSON schema from lens prompts")
    p.add_argument("--embed", choices=("tfidf", "ollama"), default="tfidf",
                   help="embedding: tfidf (default, lexical, offline) or ollama "
                        "(nomic-embed-text, semantic). See module docstring.")
    p.add_argument("--endpoint", default="http://localhost:11434",
                   help="Ollama base URL (only used with --embed ollama)")
    p.add_argument("--embed-model", default="nomic-embed-text",
                   help="Ollama embedding model (only used with --embed ollama)")
    p.add_argument("--output", default=None, help="write JSON report")
    args = p.parse_args(argv)

    embed_fn = None
    embed_model = None
    if args.embed == "ollama":
        embed_model = args.embed_model
        embed_fn = lambda texts: ollama_embed(  # noqa: E731
            args.endpoint, texts, model=args.embed_model)

    def _kstar(d: dict) -> float | None:
        return d.get("kstar_semantic") if d.get("kstar_semantic") is not None \
            else d.get("kstar_tfidf")

    report: dict
    if args.topic_dir:
        named = load_topic_dir(Path(args.topic_dir))
        report = {
            "mode": "topic-dir",
            "path": str(Path(args.topic_dir).resolve()),
            **diagnose(named, embed_fn=embed_fn, embed_model=embed_model),
        }
    elif args.outputs_dir or (DEFAULT_OUTPUTS.exists() and not args.lenses_json):
        root = Path(args.outputs_dir) if args.outputs_dir else DEFAULT_OUTPUTS
        topics = iter_output_topics(root)
        per_topic = []
        for topic in topics:
            d = diagnose(load_topic_dir(topic),
                         embed_fn=embed_fn, embed_model=embed_model)
            d["path"] = str(topic)
            per_topic.append(d)
        kstars = [_kstar(t) for t in per_topic
                  if t.get("n", 0) >= 2 and _kstar(t) is not None]
        report = {
            "mode": "outputs-dir",
            "path": str(root.resolve()),
            "n_topics": len(per_topic),
            "median_kstar": (
                sorted(kstars)[len(kstars) // 2] if kstars else None),
            "topics": per_topic,
        }
    else:
        lenses_path = Path(args.lenses_json) if args.lenses_json else DEFAULT_LENSES
        named = load_lenses_prompts(
            lenses_path, strip_shared=not args.keep_shared_suffix)
        report = {
            "mode": "lenses-json-prompt-space",
            "path": str(lenses_path.resolve()),
            "note": (
                "Prompt-space proxy only. Overnight perspective_*.json outputs "
                "were not found. Yang et al. treat prompt heterogeneity as a "
                "valid diversity axis, but this is not output K*."
            ),
            **diagnose(named, embed_fn=embed_fn, embed_model=embed_model),
        }

    text = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
        print(f"wrote {args.output}", file=sys.stderr)
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
