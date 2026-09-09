"""Generate alternative synthesist prompts.

The synthesist is the agent that takes N per-lens perspectives and produces
a synthesis. The default prompt asks for convergences/divergences/questions.
This generator produces alternative synthesis styles (tension-surfacer,
convergence-mapper, dialectical, socratic, artistic, etc.) so the same raw
perspectives can be re-synthesized multiple ways without rerunning the lenses.

Output: JSON to synthesists/synthesists-YYYY-MM-DD.json (staging).
Log:    synthesists/synthesists_log.tsv (append-only, tracked).
Merge:  --merge writes into lenses.json under 'synthesists' dict.

Usage:
    python generate_synthesis_variants.py --styles tension,convergence,socratic
    python generate_synthesis_variants.py --styles all --seed 1010 --merge lenses.json
"""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _gen_common as gc

PROMPT_VERSION = "synthesis-variants-v1"
HERE = Path(__file__).resolve().parent
LENSES_PATH = HERE / "lenses.json"
SYNTH_DIR = HERE / "synthesists"
SYNTH_LOG = SYNTH_DIR / "synthesists_log.tsv"
LOG_COLUMNS = ["timestamp_utc", "source", "theme", "model", "seed",
               "prompt_version", "id", "description"]

STYLE_DESCRIPTIONS = {
    "tension":      "Surfaces divergences sharpest. Where the lenses disagree on the same facts, the synthesist names the disagreement in each lens's own terms and refuses to smooth it.",
    "convergence":  "Maps only what the lenses agree on, explicitly excluding divergences. Produces a minimal shared picture.",
    "dialectical":  "Treats each pair of lenses as thesis/antithesis. Produces one sublated synthesis per pair, then integrates.",
    "socratic":     "Produces questions, not claims. Each perspective becomes a question that exposes the topic's presuppositions.",
    "artistic":     "Writes the synthesis as a short prose piece (500-800 words) with a title, cadence, and figurative framing, not a structured report.",
    "minimalist":   "One paragraph. The fewest sentences that preserve the lenses' irreducible disagreements and their shared blind spots.",
    "adversarial":  "Steelmans the lens the others would dismiss most. Finishes with why the others might nevertheless be right.",
}

REQUIRED_FIELDS = ("id", "description", "system")
MIN_SYSTEM_CHARS = 200


def existing_synth_ids() -> set[str]:
    data = json.loads(LENSES_PATH.read_text(encoding="utf-8"))
    ids = set(data.get("synthesists", {}).keys())
    if SYNTH_DIR.exists():
        for f in SYNTH_DIR.glob("synthesists-*.json"):
            try:
                d = json.loads(f.read_text(encoding="utf-8"))
                for s in d.get("synthesists", []):
                    if isinstance(s, dict) and s.get("id"):
                        ids.add(s["id"])
            except (json.JSONDecodeError, OSError) as e:
                print(f"WARN: skipping corrupt {f}: {e}", file=sys.stderr)
                continue
    return ids


def build_prompt(styles: list[str], excluded: set[str]) -> tuple[str, str]:
    system, user_tmpl = gc.load_prompt("synthesis_variants", "v1")
    style_block = "\n".join(f"- {s}: {STYLE_DESCRIPTIONS[s]}" for s in styles)
    excluded_str = ", ".join(sorted(excluded)) if excluded else "(none)"
    user = user_tmpl.safe_substitute(style_block=style_block,
                                     excluded_str=excluded_str)
    return system, user


def validate(synth: dict, existing: set[str]) -> tuple[bool, str]:
    ok, reason = gc.validate_required_string_fields(synth, REQUIRED_FIELDS,
                                                    min_len={"system": MIN_SYSTEM_CHARS})
    if not ok:
        return ok, reason
    sid = synth["id"]
    if not gc.snake_case_ok(sid):
        return False, f"id '{sid}' not valid snake_case"
    if sid in existing:
        return False, f"duplicate id '{sid}'"
    if "Return JSON" not in synth["system"]:
        return False, "system prompt missing 'Return JSON with keys: ...' clause"
    return True, ""


def merge_into_lenses_json(synths: list[dict], target: Path,
                           dry_run: bool = False) -> tuple[list[str], list[str]]:
    data = json.loads(target.read_text(encoding="utf-8"))
    synthesists = data.setdefault("synthesists", {})
    # Auto-promote the legacy top-level 'synthesist' key to synthesists.default.
    if "synthesist" in data and "default" not in synthesists:
        synthesists["default"] = {
            "description": "Original synthesist: convergence, divergence, "
                           "and live-questions mapper.",
            "system": data["synthesist"]["system"],
        }
    added_ids: list[str] = []
    skipped_ids: list[str] = []
    for s in synths:
        sid = s["id"]
        if sid in synthesists:
            skipped_ids.append(sid)
            continue
        synthesists[sid] = {"description": s["description"],
                            "system": s["system"]}
        added_ids.append(sid)
    if not dry_run:
        target.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                          encoding="utf-8")
    return added_ids, skipped_ids


def main(argv: list[str] | None = None) -> int:
    p = gc.standard_argparse(__doc__)
    p.add_argument("--styles", default="tension,convergence,socratic,minimalist",
                   help=f"comma-separated style names or 'all'. "
                        f"Available: {','.join(STYLE_DESCRIPTIONS.keys())}")
    p.add_argument("--merge", default=None,
                   help="merge accepted into this lenses.json-style file")
    args = p.parse_args(argv)

    endpoint = gc.load_endpoint(args.endpoint)
    if args.model:
        endpoint = {**endpoint, "model": args.model}
    if args.styles == "all":
        styles = list(STYLE_DESCRIPTIONS.keys())
    else:
        styles = [s.strip() for s in args.styles.split(",") if s.strip()]
        unknown = [s for s in styles if s not in STYLE_DESCRIPTIONS]
        if unknown:
            raise SystemExit(f"unknown styles: {unknown}. "
                             f"available: {list(STYLE_DESCRIPTIONS.keys())}")
    out_path = Path(args.output) if args.output else \
        SYNTH_DIR / f"synthesists-{dt.datetime.now(dt.UTC).date().isoformat()}.json"

    excluded = existing_synth_ids()
    print(f"styles: {styles}", file=sys.stderr)
    print(f"endpoint: {endpoint['name']} ({endpoint['model']})  "
          f"seed: {args.seed}  prompt_version: {PROMPT_VERSION}",
          file=sys.stderr)
    print(f"excluded: {sorted(excluded)}", file=sys.stderr)

    seen: set[str] = set()

    def validator(s: dict) -> tuple[bool, str]:
        ok, reason = validate(s, excluded | seen)
        if ok:
            seen.add(s["id"])
        return ok, reason

    schema_hint = ('synthesists list; each has id (snake_case), '
                   f'description, system (>={MIN_SYSTEM_CHARS} chars) '
                   'ending with the schema sentence')
    accepted, rejected, last_result = gc.run_brainstorm(
        endpoint=endpoint,
        build_prompt=lambda: build_prompt(styles, excluded),
        list_key="synthesists",
        item_validator=validator,
        base_seed=args.seed,
        self_review=args.self_review,
        schema_hint=schema_hint,
        timeout=900,
        min_accepted=args.min_accepted,
        max_retries=args.max_retries,
        log_fn=lambda m: print(m, file=sys.stderr))
    if last_result is None or (not last_result.ok() and not accepted):
        print(f"ERROR: {last_result.parse_error if last_result else 'no attempts'}",
              file=sys.stderr)
        return 1
    result = last_result

    print(f"accepted: {len(accepted)}  rejected: {len(rejected)}", file=sys.stderr)
    for s, reason in rejected:
        sid = s.get("id", "?") if isinstance(s, dict) else "?"
        print(f"  reject {sid}: {reason}", file=sys.stderr)

    if args.dry_run:
        print(json.dumps({"synthesists": accepted}, indent=2, ensure_ascii=False))
        return 0 if accepted else 1

    if accepted:
        SYNTH_DIR.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps({"synthesists": accepted}, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8")
        print(f"wrote {len(accepted)} synthesist(s) to {out_path}", file=sys.stderr)

        log = gc.TsvLog(SYNTH_LOG, LOG_COLUMNS)
        prov = gc.provenance_row(
            source="generator", theme="", model=result.model,
            seed=args.seed, prompt_version=PROMPT_VERSION)
        rej_prov = {**prov, "source": "rejected"}
        rows = [{**prov, "id": s["id"], "description": s["description"],
                 "reason": ""} for s in accepted]
        rej_rows = [
            {**rej_prov,
             "id": (s.get("id", "?") if isinstance(s, dict) else "?"),
             "description": (s.get("description", "") if isinstance(s, dict) else ""),
             "reason": reason[:200]}
            for s, reason in rejected]
        log.append(rows + rej_rows)
        print(f"logged {len(rows)} accepted + {len(rej_rows)} rejected "
              f"row(s) to {SYNTH_LOG}", file=sys.stderr)

        if args.merge:
            merge_path = Path(args.merge)
            if not merge_path.exists():
                raise SystemExit(f"--merge target not found: {merge_path}")
            added_ids, skipped_ids = merge_into_lenses_json(
                accepted, merge_path, dry_run=args.preview_merge)
            verb = "would merge" if args.preview_merge else "merged"
            print(f"{verb} {len(added_ids)} synthesist(s) into {merge_path}",
                  file=sys.stderr)
            for sid in added_ids:
                print(f"  + {sid}", file=sys.stderr)
            for sid in skipped_ids:
                print(f"  = {sid} (already present)", file=sys.stderr)
    return 0 if accepted else 1


if __name__ == "__main__":
    raise SystemExit(main())
