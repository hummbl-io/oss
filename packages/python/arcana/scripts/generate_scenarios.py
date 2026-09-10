"""Generate paradigm scenarios per lens — 3-5 short concrete cases each lens handles well.

Given a lens (or 'all'), asks Ollama to produce paradigm scenarios that would
sharpen the lens's analytic terms. Used for:
- Documenting the roster (each lens gets a concrete footprint in markdown)
- Catching under-specified lens prompts (if the model can't produce a
  plausible scenario, the lens is too abstract)
- Future few-shot prompting material

Output: markdown files lens_docs/<lens_id>.md (overwrites if --force).
Log: scenarios/scenarios_log.tsv.
No merge — purely documentary.

Usage:
    python generate_scenarios.py --lens schmitt
    python generate_scenarios.py --lens all --count 3 --seed 1111
    python generate_scenarios.py --lens schmitt --force   # overwrite existing
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _gen_common as gc

PROMPT_VERSION = "scenarios-v1"
HERE = Path(__file__).resolve().parent
LENSES_PATH = HERE / "lenses.json"
SCENARIOS_DIR = HERE / "scenarios"
LENS_DOCS_DIR = HERE / "lens_docs"
SCENARIOS_LOG = SCENARIOS_DIR / "scenarios_log.tsv"
LOG_COLUMNS = ["timestamp_utc", "source", "theme", "model", "seed",
               "prompt_version", "lens", "scenario_title"]

REQUIRED_FIELDS = ("title", "setup", "what_lens_sees", "what_lens_misses")
MIN_SETUP_CHARS = 80


def load_lens(lens_id: str) -> dict:
    data = json.loads(LENSES_PATH.read_text(encoding="utf-8"))
    lenses = data.get("lenses", {})
    if lens_id not in lenses:
        raise SystemExit(f"lens '{lens_id}' not found. "
                         f"available: {sorted(lenses.keys())}")
    return lenses[lens_id]


def all_lens_ids() -> list[str]:
    data = json.loads(LENSES_PATH.read_text(encoding="utf-8"))
    return list(data.get("lenses", {}).keys())


def build_prompt(lens_id: str, lens_def: dict, count: int) -> tuple[str, str]:
    system, user_tmpl = gc.load_prompt("scenarios", "v1")
    user = user_tmpl.safe_substitute(
        lens_id=lens_id,
        lens_school=lens_def["school"],
        lens_system=lens_def["system"],
        count=count)
    return system, user


def validate(scenario: dict) -> tuple[bool, str]:
    return gc.validate_required_string_fields(
        scenario, REQUIRED_FIELDS, min_len={"setup": MIN_SETUP_CHARS})


def render_markdown(lens_id: str, lens_def: dict, scenarios: list[dict],
                    generated_at: str, model: str, seed: int | None) -> str:
    lines = [f"# `{lens_id}` — {lens_def['school']}", ""]
    lines.append(f"> Generated {generated_at} via generate_scenarios.py "
                 f"(model={model}, seed={seed}, prompt_version={PROMPT_VERSION})")
    lines += ["", "## System prompt", "", "```", lens_def["system"], "```", ""]
    lines += ["## Paradigm scenarios", ""]
    for i, sc in enumerate(scenarios, 1):
        lines.append(f"### {i}. {sc['title']}")
        lines += ["", sc["setup"], ""]
        lines += [f"**What {lens_id} sees:** {sc['what_lens_sees']}", ""]
        lines += [f"**What {lens_id} misses:** {sc['what_lens_misses']}", ""]
    return "\n".join(lines)


def run_one_lens(endpoint: dict, lens_id: str, count: int, force: bool,
                 seed: int | None, self_review: bool,
                 min_accepted: int = 0, max_retries: int = 0,
                 dry_run: bool = False) -> bool:
    lens_def = load_lens(lens_id)
    doc_path = LENS_DOCS_DIR / f"{lens_id}.md"
    if doc_path.exists() and not force and not dry_run:
        print(f"[skip] {lens_id} already has scenarios at {doc_path} "
              f"(use --force to regenerate)", file=sys.stderr)
        return False

    def validator(sc: dict) -> tuple[bool, str]:
        ok, reason = validate(sc)
        if not ok:
            print(f"  [{lens_id}] reject: {reason}", file=sys.stderr)
        return ok, reason

    schema_hint = ('scenarios list; each has title (4-10 words), setup '
                   f'(>={MIN_SETUP_CHARS} chars, 3-5 sentences, '
                   'contemporary-plausible), what_lens_sees (1 sentence), '
                   'what_lens_misses (1 sentence)')
    accepted, rejected, last_result = gc.run_brainstorm(
        endpoint=endpoint,
        build_prompt=lambda: build_prompt(lens_id, lens_def, count),
        list_key="scenarios",
        item_validator=validator,
        base_seed=seed,
        self_review=self_review,
        schema_hint=schema_hint,
        timeout=600,
        min_accepted=min_accepted,
        max_retries=max_retries,
        log_fn=lambda m: print(m, file=sys.stderr))
    if last_result is None or (not last_result.ok() and not accepted):
        print(f"[{lens_id}] FAILED: "
              f"{last_result.parse_error if last_result else 'no attempts'}",
              file=sys.stderr)
        return False
    result = last_result
    if not accepted:
        print(f"[{lens_id}] no valid scenarios", file=sys.stderr)
        if not dry_run:
            # still log the rejections so we can mine reasons later
            log = gc.TsvLog(SCENARIOS_LOG, LOG_COLUMNS)
            prov = gc.provenance_row(
                source="rejected", theme="", model=result.model,
                seed=seed, prompt_version=PROMPT_VERSION)
            rej_rows = [{**prov, "lens": lens_id,
                         "scenario_title": sc.get("title", "?"),
                         "reason": reason[:200]}
                        for sc, reason in rejected]
            if rej_rows:
                log.append(rej_rows)
        return False

    generated_at = gc.now_utc_iso()
    md = render_markdown(lens_id, lens_def, accepted, generated_at,
                        result.model, seed)
    if dry_run:
        print(f"[{lens_id}] [dry-run] would write {len(accepted)} scenarios "
              f"to {doc_path} ({len(rejected)} rejected, no log append)",
              file=sys.stderr)
        return True

    LENS_DOCS_DIR.mkdir(parents=True, exist_ok=True)
    doc_path.write_text(md, encoding="utf-8")

    log = gc.TsvLog(SCENARIOS_LOG, LOG_COLUMNS)
    prov = gc.provenance_row(
        source="generator", theme="", model=result.model,
        seed=seed, prompt_version=PROMPT_VERSION)
    rej_prov = {**prov, "source": "rejected"}
    rows = [{**prov, "lens": lens_id, "scenario_title": sc["title"],
             "reason": ""} for sc in accepted]
    rej_rows = [{**rej_prov, "lens": lens_id,
                 "scenario_title": sc.get("title", "?"),
                 "reason": reason[:200]}
                for sc, reason in rejected]
    log.append(rows + rej_rows)

    print(f"[{lens_id}] wrote {len(accepted)} scenarios to {doc_path}",
          file=sys.stderr)
    return True


def main(argv: list[str] | None = None) -> int:
    p = gc.standard_argparse(__doc__)
    p.add_argument("--lens", required=True,
                   help="lens id or 'all' for every lens in lenses.json")
    p.add_argument("--count", type=int, default=3,
                   help="scenarios per lens (default: 3)")
    p.add_argument("--force", action="store_true",
                   help="overwrite existing lens_docs/<id>.md")
    args = p.parse_args(argv)

    endpoint = gc.load_endpoint(args.endpoint)
    if args.model:
        endpoint = {**endpoint, "model": args.model}
    lens_ids = all_lens_ids() if args.lens == "all" else [args.lens]

    print(f"endpoint: {endpoint['name']} ({endpoint['model']})  "
          f"seed: {args.seed}  prompt_version: {PROMPT_VERSION}",
          file=sys.stderr)
    print(f"lenses: {len(lens_ids)}", file=sys.stderr)

    ok_count = 0
    for i, lid in enumerate(lens_ids, 1):
        print(f"\n[{i}/{len(lens_ids)}] {lid}", file=sys.stderr)
        try:
            if run_one_lens(endpoint, lid, args.count, args.force,
                            args.seed, args.self_review,
                            min_accepted=args.min_accepted,
                            max_retries=args.max_retries,
                            dry_run=args.dry_run):
                ok_count += 1
        except Exception as e:
            print(f"[{lid}] FAILED: {type(e).__name__}: {e}", file=sys.stderr)
    print(f"\ndone: {ok_count}/{len(lens_ids)} lens docs written",
          file=sys.stderr)
    return 0 if ok_count else 1


if __name__ == "__main__":
    raise SystemExit(main())
