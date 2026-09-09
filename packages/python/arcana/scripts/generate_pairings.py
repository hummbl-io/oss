"""Generate lens pairings — named presets of N lenses that produce productive tension.

Given the current roster in lenses.json, asks Ollama for K pairings, each a
coherent group of N lenses plus an explanation of why they disagree and an
example topic that would sharpen the disagreement.

Output: JSON to pairings/pairings-YYYY-MM-DD.json (staging).
Log:    pairings/pairings_log.tsv (append-only).
Merge:  --merge writes into lenses.json under a top-level 'presets' dict
        keyed by pairing name. Runner picks with `overnight_v0.py --preset NAME`.

Usage:
    python generate_pairings.py --theme "enterprise agent governance" --count 6 --size 3
    python generate_pairings.py --theme "..." --count 4 --seed 909 --merge lenses.json
"""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _gen_common as gc

PROMPT_VERSION = "pairings-v1"
HERE = Path(__file__).resolve().parent
LENSES_PATH = HERE / "lenses.json"
PAIRINGS_DIR = HERE / "pairings"
PAIRINGS_LOG = PAIRINGS_DIR / "pairings_log.tsv"
LOG_COLUMNS = ["timestamp_utc", "source", "theme", "model", "seed",
               "prompt_version", "name", "lenses"]

REQUIRED_FIELDS = ("name", "lenses", "why_tension", "example_topic")


def load_roster() -> list[tuple[str, str]]:
    data = json.loads(LENSES_PATH.read_text(encoding="utf-8"))
    return [(lid, v["school"]) for lid, v in data.get("lenses", {}).items()]


def existing_preset_names() -> set[str]:
    data = json.loads(LENSES_PATH.read_text(encoding="utf-8"))
    return set(data.get("presets", {}).keys())


def build_prompt(theme: str, count: int, size: int,
                 roster: list[tuple[str, str]],
                 excluded_names: set[str]) -> tuple[str, str]:
    system, user_tmpl = gc.load_prompt("pairings", "v1")
    roster_lines = "\n".join(f"- {lid} ({school})" for lid, school in roster)
    excluded_str = ", ".join(sorted(excluded_names)) if excluded_names else "(none)"
    user = user_tmpl.safe_substitute(
        theme=theme, count=count, size=size,
        roster_lines=roster_lines, excluded_str=excluded_str)
    return system, user


def validate(pairing: dict, roster_ids: set[str], existing_names: set[str],
             size: int) -> tuple[bool, str]:
    for field in REQUIRED_FIELDS:
        if field not in pairing:
            return False, f"missing field: {field}"
    name = pairing["name"]
    if not isinstance(name, str) or not gc.snake_case_ok(name):
        return False, f"name '{name}' is not valid snake_case"
    if name in existing_names:
        return False, f"duplicate name '{name}'"
    lenses = pairing["lenses"]
    if not isinstance(lenses, list) or len(lenses) != size:
        got = len(lenses) if isinstance(lenses, list) else "?"
        return False, f"lenses must be exactly {size} items, got {got}"
    if len(set(lenses)) != len(lenses):
        return False, "duplicate lenses within pairing"
    unknown = [lid for lid in lenses if lid not in roster_ids]
    if unknown:
        return False, f"unknown lens ids: {unknown}"
    if not isinstance(pairing["why_tension"], str) or len(pairing["why_tension"]) < 50:
        return False, "why_tension must be >= 50 chars"
    if not isinstance(pairing["example_topic"], str) or len(pairing["example_topic"]) < 10:
        return False, "example_topic must be >= 10 chars"
    return True, ""


def merge_into_lenses_json(pairings: list[dict], target: Path,
                           dry_run: bool = False) -> tuple[list[str], list[str]]:
    data = json.loads(target.read_text(encoding="utf-8"))
    presets = data.setdefault("presets", {})
    added_names: list[str] = []
    skipped_names: list[str] = []
    for pr in pairings:
        name = pr["name"]
        if name in presets:
            skipped_names.append(name)
            continue
        presets[name] = {
            "lenses": list(pr["lenses"]),
            "why_tension": pr["why_tension"],
            "example_topic": pr["example_topic"],
        }
        added_names.append(name)
    if not dry_run:
        target.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                          encoding="utf-8")
    return added_names, skipped_names


def main(argv: list[str] | None = None) -> int:
    p = gc.standard_argparse(__doc__)
    p.add_argument("--theme", required=True)
    p.add_argument("--count", type=int, default=4)
    p.add_argument("--size", type=int, default=3)
    p.add_argument("--merge", default=None,
                   help="merge accepted into this lenses.json-style file under 'presets'")
    args = p.parse_args(argv)

    endpoint = gc.load_endpoint(args.endpoint)
    if args.model:
        endpoint = {**endpoint, "model": args.model}
    out_path = Path(args.output) if args.output else \
        PAIRINGS_DIR / f"pairings-{dt.datetime.now(dt.UTC).date().isoformat()}.json"

    roster = load_roster()
    roster_ids = {lid for lid, _ in roster}
    if len(roster_ids) < args.size:
        raise SystemExit(f"roster has {len(roster_ids)} lenses, "
                         f"need >= {args.size} for pairings of size {args.size}")
    excluded_names = existing_preset_names()

    print(f"theme: {args.theme}", file=sys.stderr)
    print(f"endpoint: {endpoint['name']} ({endpoint['model']})  "
          f"seed: {args.seed}  prompt_version: {PROMPT_VERSION}",
          file=sys.stderr)
    print(f"count: {args.count}  size: {args.size}  "
          f"roster: {len(roster_ids)}  excluded: {len(excluded_names)}",
          file=sys.stderr)

    seen_names: set[str] = set()
    seen_lens_sets: set[frozenset] = set()

    def validator(pr: dict) -> tuple[bool, str]:
        ok, reason = validate(pr, roster_ids,
                              excluded_names | seen_names, args.size)
        if ok:
            lens_set = frozenset(pr["lenses"])
            if lens_set in seen_lens_sets:
                return False, "duplicate lens set (same lenses, different name)"
            seen_lens_sets.add(lens_set)
            seen_names.add(pr["name"])
        return ok, reason

    schema_hint = ('pairings list; each has name (snake_case), lenses '
                   f'array of exactly {args.size} items, why_tension '
                   '>=50 chars, example_topic >=10 chars')
    accepted, rejected, last_result = gc.run_brainstorm(
        endpoint=endpoint,
        build_prompt=lambda: build_prompt(args.theme, args.count, args.size,
                                          roster, excluded_names),
        list_key="pairings",
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
    for pr, reason in rejected:
        pn = pr.get("name", "?") if isinstance(pr, dict) else "?"
        print(f"  reject {pn}: {reason}", file=sys.stderr)

    print(f"accepted: {len(accepted)}  rejected: {len(rejected)}", file=sys.stderr)
    for pr, reason in rejected:
        pn = pr.get("name", "?") if isinstance(pr, dict) else "?"
        print(f"  reject {pn}: {reason}", file=sys.stderr)

    if args.dry_run:
        print(json.dumps({"pairings": accepted}, indent=2, ensure_ascii=False))
        return 0 if accepted else 1

    if accepted:
        PAIRINGS_DIR.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps({"pairings": accepted}, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8")
        print(f"wrote {len(accepted)} pairing(s) to {out_path}", file=sys.stderr)

        log = gc.TsvLog(PAIRINGS_LOG, LOG_COLUMNS)
        prov = gc.provenance_row(
            source="generator", theme=args.theme, model=result.model,
            seed=args.seed, prompt_version=PROMPT_VERSION)
        rej_prov = {**prov, "source": "rejected"}
        rows = [{**prov, "name": pr["name"], "lenses": ",".join(pr["lenses"]),
                 "reason": ""} for pr in accepted]
        def _lenses_field(pr):
            if isinstance(pr, dict) and isinstance(pr.get("lenses"), list):
                return ",".join(str(x) for x in pr["lenses"])
            return ""
        rej_rows = [
            {**rej_prov,
             "name": (pr.get("name", "?") if isinstance(pr, dict) else "?"),
             "lenses": _lenses_field(pr),
             "reason": reason[:200]}
            for pr, reason in rejected]
        log.append(rows + rej_rows)
        print(f"logged {len(rows)} accepted + {len(rej_rows)} rejected "
              f"row(s) to {PAIRINGS_LOG}", file=sys.stderr)

        if args.merge:
            merge_path = Path(args.merge)
            if not merge_path.exists():
                raise SystemExit(f"--merge target not found: {merge_path}")
            added_names, skipped_names = merge_into_lenses_json(
                accepted, merge_path, dry_run=args.preview_merge)
            verb = "would merge" if args.preview_merge else "merged"
            print(f"{verb} {len(added_names)} preset(s) into {merge_path}",
                  file=sys.stderr)
            for name in added_names:
                print(f"  + {name}", file=sys.stderr)
            for name in skipped_names:
                print(f"  = {name} (already present)", file=sys.stderr)
    return 0 if accepted else 1


if __name__ == "__main__":
    raise SystemExit(main())
