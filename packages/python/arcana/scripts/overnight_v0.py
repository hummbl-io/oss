"""Minimal overnight ARCANA runner.

Self-contained: no imports from the broken pipeline/ layout. Pure stdlib.

Topic goes in, perspectives come out. Each lens gets one Ollama call. After all
perspectives complete, the synthesist gets one more call. Everything written to
outputs/YYYY-MM-DD/<slug>/ as JSON + Markdown, with a run log.

Usage:
    python overnight_v0.py --topic "Google's new Enterprise Agent Platform"
    python overnight_v0.py --topic "..." --lenses yarvin,foucault,aurelius
    python overnight_v0.py --topic "..." --synth-input claims
    python overnight_v0.py --topic "..." --dry-run
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import _gen_common as gc
import ecosystem_contracts as ec

HERE = Path(__file__).resolve().parent
LENSES_PATH = HERE / "lenses.json"
OUTPUTS_ROOT = HERE / "outputs"

PAIDEIA_AXES = ec.PAIDEIA_AXES
SYNTH_INPUT_FULL = "full"
SYNTH_INPUT_CLAIMS = "claims"
SYNTH_INPUT_MODES = (SYNTH_INPUT_FULL, SYNTH_INPUT_CLAIMS)


def load_paideia_plan(path: Path) -> dict:
    """Validate + return a PAIDEIA plan JSON. Raises on structural error.

    Version-aware: accepts v0.1 plans (9-axis target_vector, no Em) and
    fills Em=0 so the v0.2 10-axis pipeline can consume them. v0.2 plans
    (10-axis) are returned as-is. (docs/paideia-9-v0.2-draft.md: v0.1
    plans/scores kept as-is; re-scoring is opt-in.)
    """
    if not path.exists():
        raise SystemExit(f"paideia plan not found: {path}")
    plan = json.loads(path.read_text(encoding="utf-8"))
    if "target_vector" not in plan:
        raise SystemExit(f"plan {path} missing target_vector")
    tv = plan["target_vector"]
    for a in PAIDEIA_AXES:
        if a not in tv:
            if a == "Em" and set(tv) == set(ec.PAIDEIA_AXES_V0_1):
                # v0.1 plan: fill Em default so v0.2 pipeline can run.
                tv["Em"] = 0
                plan.setdefault("per_axis", {})["Em"] = {
                    "target": 0, "referent": "artifact",
                    "rationale": "v0.1 plan; Em not specified, defaulted to 0",
                    "citation": "n/a"}
                continue
            raise SystemExit(f"plan {path} target_vector missing axis {a}")
    return plan


def paideia_signature(vec: dict) -> str:
    return ec.paideia_signature(vec)


def paideia_delta(target: dict, actual: dict) -> dict:
    """Compute per-axis delta + a summary. Positive delta = actual > target."""
    delta = {a: actual.get(a, 0) - target.get(a, 0) for a in PAIDEIA_AXES}
    return {
        "target_signature": paideia_signature(target),
        "actual_signature": paideia_signature(actual),
        "per_axis_delta": delta,
        "axes_met_or_exceeded": [a for a, d in delta.items() if d >= 0],
        "axes_missed": [a for a, d in delta.items() if d < 0],
        "worst_miss": min(delta.items(), key=lambda kv: kv[1]),
    }


def slugify(s: str, max_len: int = 60) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:max_len] or "untitled"


def load_config() -> tuple[dict, list[dict]]:
    lenses = json.loads(LENSES_PATH.read_text(encoding="utf-8"))
    endpoints = gc.load_endpoints()
    endpoints = [e for e in endpoints if e.get("enabled", True)]
    if not endpoints:
        raise SystemExit("no endpoints enabled")
    return lenses, endpoints


def ollama_generate(endpoint: dict, system: str, user: str,
                    timeout: int = 600) -> dict:
    url = endpoint["url"].rstrip("/") + "/api/generate"
    payload = {
        "model": endpoint["model"],
        "prompt": user,
        "system": system,
        "stream": False,
        "format": "json",
        "think": False,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data,
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    elapsed = time.time() - t0
    raw = body.get("response", "") or body.get("thinking", "")
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"WARN: LLM response JSON parse failed: {e}", file=sys.stderr)
        parsed = {"_raw": raw, "_parse_error": True}
    return {
        "elapsed_s": round(elapsed, 2),
        "prompt_tokens": body.get("prompt_eval_count", 0),
        "completion_tokens": body.get("eval_count", 0),
        "model": endpoint["model"],
        "endpoint": endpoint["name"],
        "parsed": parsed,
    }


def dispatch_lenses(lens_names: list[str], endpoints: list[dict]) -> list[tuple[str, dict]]:
    """Round-robin assign each lens to an endpoint."""
    assignments = []
    for i, name in enumerate(lens_names):
        ep = endpoints[i % len(endpoints)]
        assignments.append((name, ep))
    return assignments


def run_lens(lens_name: str, lens_def: dict, topic: str, endpoint: dict,
             log) -> dict:
    user_prompt = (
        f"Topic under analysis: {topic}\n\n"
        f"Analyze this topic through your assigned lens. Output must be a valid "
        f"JSON object. Be specific; cite the lens's own terminology."
    )
    log(f"[{lens_name} @ {endpoint['name']}] starting...")
    try:
        result = ollama_generate(endpoint, lens_def["system"], user_prompt)
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        log(f"[{lens_name}] FAILED: {type(e).__name__}: {e}")
        return {"lens": lens_name, "error": f"{type(e).__name__}: {e}"}
    log(f"[{lens_name}] done in {result['elapsed_s']}s "
        f"({result['completion_tokens']} tok)")
    return {
        "lens": lens_name,
        "school": lens_def["school"],
        **result,
    }


def _resolve_synthesist(lenses: dict, name: str) -> dict:
    """Return the synthesist config for `name`. Handles legacy layout."""
    synthesists = lenses.get("synthesists", {})
    if name in synthesists:
        return synthesists[name]
    if name == "default" and "synthesist" in lenses:
        return lenses["synthesist"]
    raise SystemExit(f"synthesist '{name}' not found. "
                     f"available: {sorted(synthesists.keys())}")


def format_perspective_for_synthesist(perspective: dict,
                                      synth_input: str = SYNTH_INPUT_FULL) -> str | None:
    """Render one lens result for the synthesist prompt.

    `full` (default): the entire parsed JSON, including the perspective essay.
    `claims`: key_claims + blind_spots only. Interaction-tax ablation — lenses
    still write independently; the synthesist does not read full drafts.
    """
    if synth_input not in SYNTH_INPUT_MODES:
        raise ValueError(f"synth_input must be one of {SYNTH_INPUT_MODES}")
    parsed = perspective.get("parsed")
    if not isinstance(parsed, dict):
        return None
    payload = parsed if synth_input == SYNTH_INPUT_FULL else {
        "key_claims": parsed.get("key_claims"),
        "blind_spots": parsed.get("blind_spots"),
    }
    lens = perspective.get("lens", "?")
    school = perspective.get("school", "?")
    return (
        f"### {lens} ({school})\n"
        f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )


def format_perspectives_blob(perspectives: list[dict],
                             synth_input: str = SYNTH_INPUT_FULL) -> str:
    chunks = [
        blob for p in perspectives
        if (blob := format_perspective_for_synthesist(p, synth_input))
    ]
    return "\n\n".join(chunks)


def _try_one_synthesist(lenses: dict, topic: str, perspectives: list[dict],
                        endpoint: dict, log, synthesist_name: str,
                        timeout: int = 900,
                        synth_input: str = SYNTH_INPUT_FULL) -> dict:
    synth = _resolve_synthesist(lenses, synthesist_name)
    perspectives_blob = format_perspectives_blob(perspectives, synth_input)
    user_prompt = (
        f"Topic: {topic}\n\n"
        f"Below are perspectives from {len(perspectives)} lenses "
        f"(synth-input={synth_input}). "
        f"Synthesize per the schema in your system prompt.\n\n"
        f"{perspectives_blob}"
    )
    log(f"[synthesist:{synthesist_name} @ {endpoint['name']} "
        f"synth_input={synth_input}] starting...")
    try:
        result = ollama_generate(endpoint, synth["system"], user_prompt,
                                 timeout=timeout)
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        log(f"[synthesist:{synthesist_name}] FAILED: {type(e).__name__}: {e}")
        return {"error": f"{type(e).__name__}: {e}",
                "lens": f"synthesist:{synthesist_name}"}
    log(f"[synthesist:{synthesist_name}] done in {result['elapsed_s']}s "
        f"({result['completion_tokens']} tok)")
    return {"lens": f"synthesist:{synthesist_name}", **result}


def run_synthesis(lenses: dict, topic: str, perspectives: list[dict],
                  endpoint: dict, log, synthesist_name: str = "default",
                  fallback_synthesist: str | None = None,
                  synth_input: str = SYNTH_INPUT_FULL) -> dict:
    """Run synthesis with optional fallback on error.

    If the primary synthesist returns an error (timeout, network, parse), and
    `fallback_synthesist` is set and different, retry with that synthesist.
    The fallback is usually 'minimalist' — produces shorter output, finishes
    well under timeout ceilings.
    """
    primary = _try_one_synthesist(lenses, topic, perspectives, endpoint, log,
                                  synthesist_name, synth_input=synth_input)
    if "error" not in primary or not fallback_synthesist \
            or fallback_synthesist == synthesist_name:
        return primary
    log(f"primary synthesist failed — retrying with fallback '{fallback_synthesist}'")
    fallback = _try_one_synthesist(lenses, topic, perspectives, endpoint, log,
                                   fallback_synthesist, synth_input=synth_input)
    if "error" not in fallback:
        fallback["_primary_failed"] = primary.get("error")
    return fallback


def _as_text(x) -> str:
    """Coerce an LLM field (which may come back as list/dict/other) to a string.

    Models occasionally return list-of-paragraphs where the schema asked for a
    string, or dict-with-keys where a string was expected. Coerce rather than
    crash in render_markdown — the join would fail otherwise.
    """
    if isinstance(x, str):
        return x
    if isinstance(x, list):
        return "\n\n".join(_as_text(item) for item in x)
    if isinstance(x, dict):
        return "\n".join(f"- **{k}**: {_as_text(v)}" for k, v in x.items())
    return str(x) if x is not None else ""


def _as_items(x) -> list[str]:
    """Coerce an LLM 'list of strings' field that might be a dict or string."""
    if isinstance(x, list):
        return [_as_text(item) for item in x if item not in (None, "")]
    if isinstance(x, str):
        return [x] if x.strip() else []
    if isinstance(x, dict):
        return [f"**{k}**: {_as_text(v)}" for k, v in x.items()]
    return []


def render_markdown(topic: str, perspectives: list[dict], synthesis: dict) -> str:
    s = synthesis.get("parsed", {}) if isinstance(synthesis.get("parsed"), dict) else {}
    title = _as_text(s.get("title") or topic) or topic
    lines = [f"# {title}", "", f"**Topic:** {topic}", ""]
    summary = _as_text(s.get("summary"))
    if summary:
        lines += ["## Summary", "", summary, ""]
    convergences = _as_items(s.get("convergences"))
    if convergences:
        lines += ["## Convergences", ""]
        lines += [f"- {c}" for c in convergences]
        lines.append("")
    divergences = _as_items(s.get("divergences"))
    if divergences:
        lines += ["## Divergences", ""]
        lines += [f"- {d}" for d in divergences]
        lines.append("")
    synth_essay = _as_text(s.get("synthesis"))
    if synth_essay:
        lines += ["## Synthesis", "", synth_essay, ""]
    live_questions = _as_items(s.get("live_questions"))
    if live_questions:
        lines += ["## Live Questions", ""]
        lines += [f"- {q}" for q in live_questions]
        lines.append("")
    lines += ["## Perspectives", ""]
    for p in perspectives:
        pp = p.get("parsed", {})
        lines += [f"### {p['lens']} ({p.get('school','?')})", ""]
        if isinstance(pp, dict):
            persp = _as_text(pp.get("perspective"))
            if persp:
                lines += [persp, ""]
            key_claims = _as_items(pp.get("key_claims"))
            if key_claims:
                lines += ["**Key claims:**"]
                lines += [f"- {c}" for c in key_claims]
                lines.append("")
            blind_spots = _as_text(pp.get("blind_spots"))
            if blind_spots:
                lines += [f"**Blind spots:** {blind_spots}", ""]
        else:
            lines += [f"(unparseable: {pp})", ""]
    lines += ["---", "",
              (f"*Generated {dt.datetime.now(dt.UTC).isoformat()}Z "
              f"via arcana/scripts/overnight_v0.py*")]
    return "\n".join(lines)


def _make_logger(log_path: Path):
    def log(msg: str) -> None:
        stamp = dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        line = f"{stamp}  {msg}"
        print(line, flush=True)
        with log_path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    return log


def resynth_only(out_dir: Path, config: dict, endpoints: list[dict],
                 synthesist_name: str = "default",
                 fallback_synthesist: str | None = None,
                 synth_input: str = SYNTH_INPUT_FULL) -> Path:
    """Regenerate synthesis.json + article.md from existing perspective_*.json.

    Use when synthesis failed (timeout, error) but perspectives landed.
    Preserves the expensive lens-dispatch work; only redoes the synthesist call.
    Overwrites existing synthesis.json and article.md if present.
    """
    if not out_dir.is_dir():
        raise SystemExit(f"out_dir does not exist: {out_dir}")
    perspective_files = sorted(out_dir.glob("perspective_*.json"))
    if not perspective_files:
        raise SystemExit(f"no perspective_*.json files in {out_dir}")
    perspectives = [json.loads(p.read_text(encoding="utf-8"))
                    for p in perspective_files]

    # Extract topic from run.log
    topic = out_dir.name
    log_path = out_dir / "run.log"
    if log_path.exists():
        for line in log_path.read_text(encoding="utf-8").splitlines():
            if "topic:" in line:
                topic = line.split("topic:", 1)[1].strip()
                break

    log = _make_logger(log_path)
    log(f"resynth-only: {len(perspectives)} perspectives, "
        f"synthesist={synthesist_name}, fallback={fallback_synthesist}, "
        f"synth_input={synth_input}")

    synth_endpoint = endpoints[0]
    synthesis = run_synthesis(config, topic, perspectives, synth_endpoint,
                              log, synthesist_name=synthesist_name,
                              fallback_synthesist=fallback_synthesist,
                              synth_input=synth_input)
    (out_dir / "synthesis.json").write_text(
        json.dumps(synthesis, indent=2, ensure_ascii=False), encoding="utf-8")

    md = render_markdown(topic, perspectives, synthesis)
    (out_dir / "article.md").write_text(md, encoding="utf-8")
    log(f"resynth done. artifacts in {out_dir}")
    return out_dir


def run_one_topic(topic: str, config: dict, endpoints: list[dict],
                  lens_names: list[str], output_dir: Path | None = None,
                  dry_run: bool = False,
                  synthesist_name: str = "default",
                  fallback_synthesist: str | None = None,
                  synth_input: str = SYNTH_INPUT_FULL) -> Path | None:
    """Run the full pipeline for a single topic. Returns output dir or None if skipped."""
    today = dt.datetime.now(dt.UTC).date().isoformat()
    slug = slugify(topic)
    out_dir = output_dir or OUTPUTS_ROOT / today / slug
    # Resumability: skip if synthesis already exists
    if (out_dir / "synthesis.json").exists():
        print(f"[skip] {slug} already has synthesis.json", flush=True)
        return None
    out_dir.mkdir(parents=True, exist_ok=True)

    assignments = dispatch_lenses(lens_names, endpoints)
    log_path = out_dir / "run.log"
    log = _make_logger(log_path)

    log(f"topic: {topic}")
    log(f"lenses: {lens_names}")
    log(f"synth_input: {synth_input}")
    log(f"endpoints: {[e['name'] for e in endpoints]}")
    log(f"output: {out_dir}")

    if dry_run:
        log("dry-run - exiting before any Ollama calls")
        for name, ep in assignments:
            log(f"  plan: {name} -> {ep['name']} ({ep['model']})")
        return out_dir

    perspectives: list[dict] = []
    for name, ep in assignments:
        lens_def = config["lenses"][name]
        result = run_lens(name, lens_def, topic, ep, log)
        perspectives.append(result)
        (out_dir / f"perspective_{name}.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    log(f"all perspectives complete, starting synthesis "
        f"(style={synthesist_name}, synth_input={synth_input})")
    synth_endpoint = endpoints[0]
    synthesis = run_synthesis(config, topic, perspectives, synth_endpoint,
                              log, synthesist_name=synthesist_name,
                              fallback_synthesist=fallback_synthesist,
                              synth_input=synth_input)
    (out_dir / "synthesis.json").write_text(
        json.dumps(synthesis, indent=2, ensure_ascii=False), encoding="utf-8")

    md = render_markdown(topic, perspectives, synthesis)
    (out_dir / "article.md").write_text(md, encoding="utf-8")
    log(f"done. artifacts in {out_dir}")
    return out_dir


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--topic", help="single topic to run")
    src.add_argument("--topics-file",
                     help="path to file with one topic per line; "
                          "already-completed topics are skipped")
    src.add_argument("--resynth", metavar="DIR",
                     help="regenerate synthesis.json + article.md from existing "
                          "perspective_*.json in DIR; skips lens dispatch. Use when "
                          "synthesis failed but perspectives landed.")
    p.add_argument("--lenses", default="all",
                   help="comma-separated lens names or 'all' (default). "
                        "Ignored if --preset is given.")
    p.add_argument("--preset", default=None,
                   help="named preset from lenses.json 'presets' dict. "
                        "Overrides --lenses.")
    p.add_argument("--output-dir", default=None,
                   help="override output dir (single-topic only)")
    p.add_argument("--synthesist", default="default",
                   help="named synthesist from lenses.json 'synthesists' dict "
                        "(default: 'default' = original convergence/divergence)")
    p.add_argument("--fallback-synthesist", default=None,
                   help="retry with this synthesist if primary errors/times out. "
                        "'minimalist' is a good default — produces shorter output, "
                        "finishes well under ceiling. Unused if primary succeeds.")
    p.add_argument("--synth-input", choices=SYNTH_INPUT_MODES,
                   default=SYNTH_INPUT_FULL,
                   help="what the synthesist reads: full parsed JSON (default) "
                        "or key_claims+blind_spots only (interaction-tax ablation).")
    p.add_argument("--plan", default=None, metavar="PATH",
                   help="PAIDEIA plan JSON from generate_paideia_plan. Used as "
                        "target contract: plan signature logged, actual score "
                        "computed after run, delta written to paideia_delta.json")
    p.add_argument("--dry-run", action="store_true",
                   help="print plan and exit")
    args = p.parse_args(argv)

    paideia_plan = load_paideia_plan(Path(args.plan)) if args.plan else None

    config, endpoints = load_config()

    # --resynth: short-circuit to resynth-only mode; no lens work
    if args.resynth:
        out_dir = Path(args.resynth).resolve()
        resynth_only(out_dir, config, endpoints,
                     synthesist_name=args.synthesist,
                     fallback_synthesist=args.fallback_synthesist,
                     synth_input=args.synth_input)
        return 0

    all_lens_names = list(config["lenses"].keys())
    if args.preset:
        presets = config.get("presets", {})
        if args.preset not in presets:
            raise SystemExit(f"unknown preset '{args.preset}'. "
                             f"available: {sorted(presets.keys())}")
        lens_names = list(presets[args.preset]["lenses"])
        unknown = [n for n in lens_names if n not in config["lenses"]]
        if unknown:
            raise SystemExit(f"preset '{args.preset}' references unknown "
                             f"lenses: {unknown}")
    elif args.lenses == "all":
        lens_names = all_lens_names
    else:
        lens_names = [n.strip() for n in args.lenses.split(",") if n.strip()]
        unknown = [n for n in lens_names if n not in config["lenses"]]
        if unknown:
            raise SystemExit(f"unknown lenses: {unknown}. "
                             f"available: {all_lens_names}")

    if args.topics_file:
        if args.output_dir:
            raise SystemExit("--output-dir is incompatible with --topics-file")
        topics_path = Path(args.topics_file)
        if not topics_path.exists():
            raise SystemExit(f"topics file not found: {topics_path}")
        topics = [t.strip() for t in topics_path.read_text(encoding="utf-8").splitlines()
                  if t.strip() and not t.strip().startswith("#")]
        if not topics:
            raise SystemExit(f"no topics in {topics_path}")
        for topic in topics:
            run_one_topic(topic, config, endpoints, lens_names,
                          synthesist_name=args.synthesist,
                          fallback_synthesist=args.fallback_synthesist,
                          synth_input=args.synth_input)
        return 0

    if not args.topic:
        raise SystemExit("--topic required (or --topics-file / --resynth)")

    out_dir = run_one_topic(
        args.topic, config, endpoints, lens_names,
        output_dir=Path(args.output_dir) if args.output_dir else None,
        dry_run=args.dry_run,
        synthesist_name=args.synthesist,
        fallback_synthesist=args.fallback_synthesist,
        synth_input=args.synth_input)

    if paideia_plan and out_dir:
        # Score actual output against plan target
        from score_paideia import score_content
        article_text = (out_dir / "article.md").read_text(encoding="utf-8")
        score_result = score_content(article_text)
        actual_vector = score_result["vector"]
        target_vector = paideia_plan["target_vector"]
        delta = paideia_delta(target_vector, actual_vector)
        delta_path = out_dir / "paideia_delta.json"
        delta_path.write_text(
            json.dumps(delta, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8")
        print(f"paideia delta written to {delta_path}", flush=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
