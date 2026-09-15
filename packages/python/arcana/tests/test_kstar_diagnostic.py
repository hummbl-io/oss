"""CPU-only tests for kstar_diagnostic.py. No Ollama."""
from __future__ import annotations

import json
import math
from pathlib import Path

import kstar_diagnostic as ks


def test_kstar_identical_texts_near_one():
    named = [("a", "alpha beta gamma delta"),
             ("b", "alpha beta gamma delta"),
             ("c", "alpha beta gamma delta")]
    report = ks.diagnose(named)
    assert report["n"] == 3
    assert report["kstar_tfidf"] == 1.0
    assert report["mean_pairwise_cosine"] == 1.0
    assert report["clusters_cosine_0_80"] == 1


def test_kstar_disjoint_vocab_near_n():
    named = [
        ("a", "apple banana cherry date elderberry fig grape"),
        ("b", "neutron proton electron quark gluon photon boson"),
        ("c", "sonnet stanza meter rhyme iamb pentameter volta"),
    ]
    report = ks.diagnose(named)
    assert report["n"] == 3
    assert report["kstar_tfidf"] >= 2.5
    assert report["mean_pairwise_cosine"] < 0.15
    assert report["clusters_cosine_0_80"] == 3


def test_kstar_from_identity_eigenvalues():
    assert abs(ks.kstar_from_eigenvalues([1.0, 1.0, 1.0]) - 3.0) < 1e-9


def test_kstar_from_rank_one_eigenvalues():
    assert abs(ks.kstar_from_eigenvalues([4.0, 0.0, 0.0, 0.0]) - 1.0) < 1e-9


def test_jacobi_identity():
    ident = [[1.0 if i == j else 0.0 for j in range(3)] for i in range(3)]
    eigs = sorted(ks.jacobi_eigenvalues(ident))
    assert all(abs(e - 1.0) < 1e-8 for e in eigs)


def test_perspective_text_prefers_parsed_fields():
    obj = {
        "lens": "schmitt",
        "parsed": {
            "perspective": "friend enemy",
            "key_claims": ["claim a", "claim b"],
            "blind_spots": "misses economy",
        },
        "raw": "should not dominate",
    }
    text = ks.perspective_text(obj)
    assert "friend enemy" in text
    assert "claim a" in text
    assert "misses economy" in text


def test_load_topic_dir(tmp_path: Path):
    payload = {
        "lens": "yarvin",
        "parsed": {
            "perspective": "sovereign decides",
            "key_claims": ["c1"],
            "blind_spots": "ignores consent",
        },
    }
    (tmp_path / "perspective_yarvin.json").write_text(
        json.dumps(payload), encoding="utf-8")
    named = ks.load_topic_dir(tmp_path)
    assert named[0][0] == "yarvin"
    assert "sovereign decides" in named[0][1]


def test_load_lenses_prompts_strips_shared_suffix(tmp_path: Path):
    data = {
        "lenses": {
            "a": {"system": "Unique apple frame. Return JSON with keys: perspective, key_claims."},
            "b": {"system": "Unique neutron frame. Return JSON with keys: perspective, key_claims."},
        }
    }
    path = tmp_path / "lenses.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    stripped = dict(ks.load_lenses_prompts(path, strip_shared=True))
    kept = dict(ks.load_lenses_prompts(path, strip_shared=False))
    assert "Return JSON" not in stripped["a"]
    assert "Unique apple" in stripped["a"]
    assert "Return JSON" in kept["a"]


def test_diagnose_empty():
    report = ks.diagnose([])
    assert report["n"] == 0


# ---- semantic embedding mode (--embed ollama path, mocked) --------------- #

def _embed_orthogonal(texts):
    """Mock embed_fn: map each text to a distinct orthonormal axis."""
    dim = len(texts)
    return [[1.0 if i == j else 0.0 for j in range(dim)] for i in range(dim)]


def test_diagnose_embed_fn_semantic_mode():
    named = [("a", "apple"), ("b", "neutron"), ("c", "sonnet")]
    report = ks.diagnose(named, embed_fn=_embed_orthogonal,
                         embed_model="nomic-embed-text")
    assert report["embed_method"] == "ollama"
    assert report["embed_model"] == "nomic-embed-text"
    assert "kstar_semantic" in report
    assert "kstar_tfidf" not in report
    # 3 orthonormal vectors -> Gram = I -> eigs all 1 -> K* = 3.0
    assert abs(report["kstar_semantic"] - 3.0) < 1e-3
    assert report["mean_pairwise_cosine"] == 0.0
    assert report["clusters_cosine_0_80"] == 3


def test_diagnose_semantic_collapse_paraphrase():
    """Headline proof: two paraphrases with DISJOINT vocab merge under semantic
    embedding (K*~1, 1 cluster) but stay separate under TF-IDF (2 clusters).
    This is the exact failure the TF-IDF proxy cannot catch."""
    named = [("a", "the sovereign decides the exception"),
             ("b", "the ruler determines the emergency")]
    # Mock a semantic embedder that (correctly) sees these as near-identical.
    near_identical = [[1.0, 0.0], [0.999, 0.0447]]  # cos ~ 0.999
    report_sem = ks.diagnose(named, embed_fn=lambda t: near_identical,
                             embed_model="nomic-embed-text")
    assert report_sem["kstar_semantic"] < 1.05
    assert report_sem["clusters_cosine_0_80"] == 1
    # Same texts under TF-IDF: zero shared tokens -> orthogonal -> 2 clusters.
    report_lex = ks.diagnose(named)
    assert report_lex["embed_method"] == "tfidf"
    assert report_lex["kstar_tfidf"] >= 1.9
    assert report_lex["clusters_cosine_0_80"] == 2


def test_diagnose_tfidf_default_embed_method():
    report = ks.diagnose([("a", "alpha beta"), ("b", "gamma delta")])
    assert report["embed_method"] == "tfidf"
    assert "kstar_tfidf" in report
    assert "kstar_semantic" not in report
    assert "embed_model" not in report


def test_diagnose_malformed_embed_fn_raises():
    named = [("a", "x"), ("b", "y"), ("c", "z")]
    # Wrong count: 3 texts, 2 vectors.
    try:
        ks.diagnose(named, embed_fn=lambda t: [[1.0, 0.0], [0.0, 1.0]])
        raise AssertionError("should raise on wrong vector count")
    except ValueError as e:
        assert "embed_fn" in str(e) or "vectors" in str(e)
    # Ragged dimensions.
    try:
        ks.diagnose(named, embed_fn=lambda t: [[1.0, 0.0], [0.0, 1.0, 0.0], [1.0, 0.0]])
        raise AssertionError("should raise on ragged dims")
    except ValueError as e:
        assert "malformed" in str(e) or "dim" in str(e)
