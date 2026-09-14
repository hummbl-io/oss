"""Score existing content on PAIDEIA-9 axes (skeleton).

Takes a content artifact (markdown file or raw text) and produces a PAIDEIA-9
score vector + per-axis rationale. Per docs/paideia-9.md §9, per-axis detection
difficulty varies: M/C/P are EASY (heuristic/regex), E/S/A are MEDIUM, D/V/L
are HARD (require LLM judgment with rubric).

v0.1 status: heuristic detectors for M, C, P. Stubs for the rest that return
a placeholder score + "detector_not_implemented" note. LLM-based detectors
for D/V/L land in v0.2.

Usage:
    python score_paideia.py --content article.md
    python score_paideia.py --content article.md --instructional-intent false
    python score_paideia.py --content article.md --use-llm --allow-uncalibrated
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _gen_common as gc
import ecosystem_contracts as ec

PROMPT_VERSION = "paideia-score-v0.2"
AXES = list(ec.PAIDEIA_AXES)

# ---- EASY detectors (heuristic) --------------------------------------- #

def detect_modality(text: str) -> tuple[int, str]:
    """M: count distinct representational channels present."""
    channels = 0
    details = []
    if len(text) > 100:
        channels += 1
        details.append("verbal")
    if re.search(r"!\[.*?\]\(|<img ", text):
        channels += 1
        details.append("visual")
    if re.search(r"```[\w+]*\n|    [a-zA-Z]+\s*[=(]", text):
        channels += 1
        details.append("symbolic/code")
    if re.search(r"<audio|\.mp3|\.wav|\.ogg", text, re.IGNORECASE):
        channels += 1
        details.append("auditory")
    if re.search(r"<video|\.mp4|\.webm|\.mov", text, re.IGNORECASE):
        channels += 1
        details.append("video")
    if re.search(r"\$[^$]+\$|\\\(|\\\[", text):
        channels += 1
        details.append("math-symbolic")
    # map channel count -> 0..4 (cap at 4 channels)
    score = min(channels, 4)
    return score, f"channels: {', '.join(details) or 'none'}"


def detect_metacognition(text: str) -> tuple[int, str]:
    """C: count explicit prompts for self-monitoring/reflection."""
    prompts = [
        r"\bpredict\b", r"\breflect\b", r"\bwhy (do|did|would)\b",
        r"\bwhat if\b", r"\bcheck your\b", r"\bself-check\b",
        r"\bask yourself\b", r"\btry to explain\b",
        r"\bbefore reading\b", r"\bpause and\b", r"\bconsider\b",
    ]
    hits = 0
    for pat in prompts:
        hits += len(re.findall(pat, text, re.IGNORECASE))
    # Map hit count to 0..4
    if hits == 0:
        score = 0
    elif hits <= 1:
        score = 1
    elif hits <= 3:
        score = 2
    elif hits <= 6:
        score = 3
    else:
        score = 4
    return score, f"metacognitive prompts detected: {hits}"


def detect_practice(text: str) -> tuple[int, str]:
    """P: detect retrieval, spacing, interleaving, feedback structures."""
    signals = {}
    signals["exercises"] = len(re.findall(
        r"\bexercise\b|\bpractice\b|\bproblem set\b|\bquiz\b|\btry it\b",
        text, re.IGNORECASE))
    signals["questions"] = text.count("?")
    signals["feedback_cues"] = len(re.findall(
        r"\banswer:\b|\bsolution:\b|\bcorrect:\b|\bcheck answer\b",
        text, re.IGNORECASE))
    total = signals["exercises"] + signals["feedback_cues"]
    if signals["exercises"] == 0 and signals["feedback_cues"] == 0:
        score = 0
    elif total <= 2:
        score = 1
    elif total <= 5:
        score = 2
    elif total <= 10:
        score = 3
    else:
        score = 4
    return score, f"practice signals: {signals}"


# ---- MEDIUM/HARD detectors (stubs, v0.2) ------------------------------- #

def detect_depth(text: str) -> tuple[int, str]:
    return 2, "STUB: defaults to SOLO multistructural until LLM detector lands (v0.2)"


def detect_engagement(text: str) -> tuple[int, str]:
    # Simple heuristic: count interactive/active affordances
    interactive = len(re.findall(r"\[ \]|<input |<form|<button", text))
    constructive = len(re.findall(r"\bwrite|\bcreate|\bdesign|\bbuild\b", text, re.IGNORECASE))
    if interactive:
        score = 4
        note = f"interactive affordances: {interactive}"
    elif constructive >= 3:
        score = 3
        note = f"constructive prompts: {constructive}"
    elif constructive >= 1:
        score = 2
        note = f"constructive-lite: {constructive}"
    else:
        score = 1
        note = "passive default"
    return score, note


def detect_motivation(text: str) -> tuple[int, str]:
    return 2, "STUB: defaults to moderate until SDT-language detector lands (v0.2)"


def detect_load(text: str) -> tuple[int, str]:
    return 2, "STUB: defaults to moderate until expertise-aware detector lands (v0.2)"


def detect_scaffold(text: str) -> tuple[int, str]:
    worked = len(re.findall(r"\bexample\b|\bfor instance\b|\bworked example\b", text, re.IGNORECASE))
    if worked >= 3:
        score = 3
    elif worked >= 1:
        score = 2
    else:
        score = 1
    return score, f"worked-example markers: {worked}"


def detect_authenticity(text: str) -> tuple[int, str]:
    # Heuristic: mentions of "real", "production", "industry", "case study"
    markers = len(re.findall(
        r"\bproduction\b|\bindustry\b|\bcase study\b|\breal-world\b|\bin practice\b",
        text, re.IGNORECASE))
    if markers >= 3:
        score = 3
    elif markers >= 1:
        score = 2
    else:
        score = 1
    return score, f"authenticity markers: {markers}"


# v0.2 EMOTION (Em) detector. Affect-word density heuristic anchored to a
# small lexicon (Tyng et al. 2017). MEDIUM difficulty like E/S/A: a real
# detector lands in v0.2 alongside the LLM ensemble for D/V/L. Valence
# (pos/neg/mixed) is reported in the note but not scored -- intensity only,
# per docs/paideia-9-v0.2-draft.md Proposal A.
_AFFECT_POS = (
    "hope", "joy", "wonder", "awe", "love", "pride", "gratitude", "delight",
    "thrill", "aspiration", "triumph", "beauty", "sublime", "exhilarat",
)
_AFFECT_NEG = (
    "fear", "dread", "horror", "rage", "anger", "grief", "sorrow", "despair",
    "anguish", "shame", "disgust", "anxiety", "terror", "melancholy",
    "lament", "elegy",
)


def detect_emotion(text: str) -> tuple[int, str]:
    """Em: affect-word density as a proxy for emotional intensity (0-4).

    Heuristic, not semantic: counts positive and negative affect lexemes.
    Valence is reported in the note (pos/neg/mixed) but the score is intensity
    only. A flat technical reference scores 0; a piece where affect is the
    content (elegy, rage, awe) scores 4. Anchor: Tyng et al. 2017.
    """
    pos = sum(len(re.findall(rf"\b{w}", text, re.IGNORECASE)) for w in _AFFECT_POS)
    neg = sum(len(re.findall(rf"\b{w}", text, re.IGNORECASE)) for w in _AFFECT_NEG)
    total = pos + neg
    if total == 0:
        score = 0
        valence = "flat"
    elif total <= 2:
        score = 1
        valence = "pos" if pos > neg else ("neg" if neg > pos else "mixed")
    elif total <= 5:
        score = 2
        valence = "pos" if pos > neg else ("neg" if neg > pos else "mixed")
    elif total <= 9:
        score = 3
        valence = "pos" if pos > neg else ("neg" if neg > pos else "mixed")
    else:
        score = 4
        valence = "pos" if pos > neg else ("neg" if neg > pos else "mixed")
    return score, f"affect hits: pos={pos} neg={neg} valence={valence}"


DETECTORS = {
    "M": detect_modality,
    "D": detect_depth,
    "E": detect_engagement,
    "V": detect_motivation,
    "C": detect_metacognition,
    "L": detect_load,
    "S": detect_scaffold,
    "P": detect_practice,
    "A": detect_authenticity,
    "Em": detect_emotion,
}

DIFFICULTY = {
    "M": "EASY",
    "D": "HARD (stub)",
    "E": "MEDIUM",
    "V": "HARD (stub)",
    "C": "EASY",
    "L": "HARD (stub)",
    "S": "MEDIUM",
    "P": "EASY",
    "A": "MEDIUM",
    "Em": "MEDIUM",
}


UNCALIBRATED_MSG = (
    "use_llm=True requires --allow-uncalibrated (or allow_uncalibrated=True). "
    "HARD axes D/V/L have no human calibration set. DOCTRINE Q2 / Rulers: "
    "do not treat an uncalibrated LLM 9-vector as a PAIDEIA score."
)


def score_content(text: str, instructional_intent: bool = True,
                  *,
                  use_llm: bool = False,
                  allow_uncalibrated: bool = False,
                  endpoint: dict | None = None,
                  ollama_fn=None,
                  n_runs: int = 3,
                  seed: int | None = None) -> dict:
    """Score content on PAIDEIA-9 axes.

    Default (use_llm=False): all 9 axes use heuristic/stub detectors. M, C, P
    are calibrated; D, V, L return stub values; E, S, A are simple regex
    counts. This is the v0.1 path and is CPU-only. The returned vector is
    NOT comparable across artifacts while HARD axes are stubs.

    use_llm=True: D, V, L are scored via paideia_detectors_llm with N-run
    ensemble against the given endpoint. Requires endpoint dict (or callers
    can pass ollama_fn for tests) AND allow_uncalibrated=True until a human
    bias-estimation set exists. Bumps prompt_version to v0.2-llm.
    """
    if use_llm and not allow_uncalibrated:
        raise ValueError(UNCALIBRATED_MSG)

    per_axis: dict = {}
    for axis in AXES:
        score, note = DETECTORS[axis](text)
        per_axis[axis] = {
            "score": score,
            "detector": DIFFICULTY[axis],
            "note": note,
            "referent": "artifact",
        }

    if use_llm:
        # Override D/V/L with LLM ensemble scores.
        import paideia_detectors_llm as pdl
        if endpoint is None and ollama_fn is None:
            raise ValueError("use_llm=True requires endpoint or ollama_fn")
        hard = pdl.detect_hard_axes(
            text, endpoint=endpoint or {"name": "fake", "model": "fake",
                                        "url": ""},
            ollama_fn=ollama_fn, n_runs=n_runs, seed=seed)
        for axis, (score, note) in hard.items():
            per_axis[axis] = {
                "score": score,
                "detector": "LLM ensemble",
                "note": note,
                "referent": "artifact",
            }

    vector = {a: per_axis[a]["score"] for a in AXES}
    hard_status = "uncalibrated_llm" if use_llm else "stub"
    result = {
        "instructional_intent": instructional_intent,
        "vector": vector,
        "per_axis": per_axis,
        "signature": ec.paideia_signature(vector),
        "comparable_vector": False,
        "calibrated": False,
        "hard_axes_status": hard_status,
        "prompt_version": (
            "paideia-score-v0.2-llm" if use_llm else PROMPT_VERSION),
        "note": (
            "v0.2 LLM ensemble for D/V/L is UNCALIBRATED; not a comparable "
            "PAIDEIA-10 vector. M/C/P heuristics; E/S/A/Em regex."
            if use_llm else
            "v0.2 skeleton: M/C/P are calibrated heuristics; "
            "D/V/L are stubs; Em is affect-density. Signature is not a "
            "comparable 10-vector."),
    }
    if not instructional_intent:
        result["content_type_warning"] = (
            "non-instructional content — L, S, P scores advisory not deficient")
    return result


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--content", required=True,
                   help="path to markdown/text file to score")
    p.add_argument("--instructional-intent", type=lambda s: s.lower() != "false",
                   default=True)
    p.add_argument("--output", default=None,
                   help="write score JSON to this path (default: stdout)")
    p.add_argument("--use-llm", action="store_true",
                   help="use LLM ensemble detectors for HARD axes (D/V/L) "
                        "instead of v0.1 stubs. Requires Ollama endpoint AND "
                        "--allow-uncalibrated until a human calibration set exists.")
    p.add_argument("--allow-uncalibrated", action="store_true",
                   help="required with --use-llm. Marks D/V/L as uncalibrated; "
                        "the 9-vector is not comparable across artifacts.")
    p.add_argument("--endpoint", default=None,
                   help="endpoint name (only used with --use-llm)")
    p.add_argument("--n-runs", type=int, default=3,
                   help="LLM ensemble size per axis (default 3); "
                        "ignored unless --use-llm")
    p.add_argument("--seed", type=int, default=None)
    args = p.parse_args(argv)

    content_path = Path(args.content)
    if not content_path.exists():
        print(f"error: content not found: {content_path}", file=sys.stderr)
        return 1
    text = content_path.read_text(encoding="utf-8")

    if args.use_llm and not args.allow_uncalibrated:
        print(f"error: {UNCALIBRATED_MSG}", file=sys.stderr)
        return 2

    endpoint = None
    if args.use_llm:
        endpoint = gc.load_endpoint(args.endpoint)
        print(f"LLM detectors: D, V, L via {endpoint['name']} "
              f"({endpoint['model']}), n_runs={args.n_runs} "
              f"(UNCALIBRATED)",
              file=sys.stderr)

    result = score_content(
        text, args.instructional_intent,
        use_llm=args.use_llm, allow_uncalibrated=args.allow_uncalibrated,
        endpoint=endpoint,
        n_runs=args.n_runs, seed=args.seed)
    result["_source"] = str(content_path)
    result["_scored_at"] = gc.now_utc_iso()

    if args.output:
        Path(args.output).write_text(
            json.dumps(result, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8")
        print(f"wrote score to {args.output}", file=sys.stderr)
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"signature: {result['signature']}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
