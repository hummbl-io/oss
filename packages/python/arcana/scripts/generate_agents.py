"""Generate new ARCANA agent/lens profiles via local Ollama.

Output is a JSON array of lens profiles (id, school, system). Does NOT
automatically merge into lenses.json — produces a staging file the user
reviews and merges manually (or via --merge).

Every generated lens is appended to agents/agents_log.tsv.

Usage:
    python generate_agents.py --theme "political theology and sovereignty" --count 4
    python generate_agents.py --theme "..." --exclude yarvin,gramsci,foucault
    python generate_agents.py --theme "..." --dry-run
    python generate_agents.py --theme "..." --merge lenses.json
    python generate_agents.py --theme "..." --require-primary-texts 2
"""
from __future__ import annotations

import datetime as dt
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _gen_common as gc

PROMPT_VERSION = "agents-v1"
HERE = Path(__file__).resolve().parent
LENSES_PATH = HERE / "lenses.json"
AGENTS_DIR = HERE / "agents"
AGENTS_LOG = AGENTS_DIR / "agents_log.tsv"
LOG_COLUMNS = ["timestamp_utc", "source", "theme", "model", "seed",
               "prompt_version", "agent_id", "school"]

REQUIRED_FIELDS = ("id", "school", "system")
MIN_SYSTEM_CHARS = 300


def existing_lens_ids() -> set[str]:
    """Union of IDs in lenses.json + any staging file — cross-batch dedup."""
    ids: set[str] = set()
    if LENSES_PATH.exists():
        data = json.loads(LENSES_PATH.read_text(encoding="utf-8"))
        ids.update(data.get("lenses", {}).keys())
    if AGENTS_DIR.exists():
        for f in AGENTS_DIR.glob("agents-*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                for lens in data.get("lenses", []):
                    if isinstance(lens, dict) and lens.get("id"):
                        ids.add(lens["id"])
            except (json.JSONDecodeError, OSError):
                continue
    return ids


def id_appears_in_prompt(lens_id: str, system_prompt: str) -> bool:
    """Reject id/content mismatches (e.g. id='bennett' but prompt is about Newman)."""
    p = system_prompt.lower()
    if lens_id.lower() in p:
        return True
    if lens_id.replace("_", " ").lower() in p:
        return True
    parts = [c for c in lens_id.split("_") if len(c) > 3 and not c.isdigit()]
    return any(part.lower() in p for part in parts)


def count_primary_text_signals(system_prompt: str) -> int:
    """Heuristic: parenthesized years, quoted/italicized titles."""
    year_refs = re.findall(r"\((?:c\.?\s*)?\d{3,4}(?:\s*BCE)?\)", system_prompt)
    quoted = re.findall(r"['\"][A-Za-z][^'\"\n]{2,}['\"]", system_prompt)
    italic = re.findall(r"(?<![*_])[*_]([A-Za-z][^*_\n]{2,})[*_](?![*_])",
                        system_prompt)
    return len(year_refs) + len(quoted) + len(italic)


def build_prompt(theme: str, count: int, exclude: list[str]) -> tuple[str, str]:
    system, user_tmpl = gc.load_prompt("agents", "v1")
    exclude_str = ", ".join(exclude) if exclude else "(none)"
    user = user_tmpl.safe_substitute(theme=theme, count=count,
                                     exclude_str=exclude_str)
    return system, user


def validate(lens: dict, existing: set[str]) -> tuple[bool, str]:
    ok, reason = gc.validate_required_string_fields(lens, REQUIRED_FIELDS,
                                                    min_len={"system": MIN_SYSTEM_CHARS})
    if not ok:
        return ok, reason
    if lens["id"] in existing:
        return False, f"duplicate id '{lens['id']}' (already in roster or batch)"
    if not gc.snake_case_ok(lens["id"]):
        return False, f"id '{lens['id']}' is not valid snake_case"
    if not id_appears_in_prompt(lens["id"], lens["system"]):
        return False, (f"id '{lens['id']}' does not appear in system prompt "
                       f"(likely id/content mismatch)")
    return True, ""


def merge_into_lenses_json(new_lenses: list[dict], target: Path,
                           dry_run: bool = False) -> tuple[list[str], list[str]]:
    """Plan and (unless dry_run) apply the merge.

    Returns (added_ids, skipped_ids). When dry_run is True, no write happens
    but the planned diff is still computed so callers can preview.
    """
    data = json.loads(target.read_text(encoding="utf-8"))
    lenses_dict: dict = data.setdefault("lenses", {})
    added_ids: list[str] = []
    skipped_ids: list[str] = []
    for lens in new_lenses:
        lid = lens["id"]
        if lid in lenses_dict:
            skipped_ids.append(lid)
            continue
        lenses_dict[lid] = {"school": lens["school"],
                            "system": lens["system"]}
        added_ids.append(lid)
    if not dry_run:
        target.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                          encoding="utf-8")
    return added_ids, skipped_ids


def main(argv: list[str] | None = None) -> int:
    p = gc.standard_argparse(__doc__)
    p.add_argument("--theme", required=True)
    p.add_argument("--count", type=int, default=4)
    p.add_argument("--exclude", default="",
                   help="comma-separated ids to exclude (in addition to lenses.json)")
    p.add_argument("--merge", default=None,
                   help="also merge into this lenses.json-style file")
    p.add_argument("--require-primary-texts", type=int, default=0, metavar="N",
                   help="reject if fewer than N primary-text signals (years, titles)")
    args = p.parse_args(argv)

    endpoint = gc.load_endpoint(args.endpoint)
    if args.model:
        endpoint = {**endpoint, "model": args.model}
    out_path = Path(args.output) if args.output else \
        AGENTS_DIR / f"agents-{dt.datetime.now(dt.UTC).date().isoformat()}.json"

    existing = existing_lens_ids()
    extra = {e.strip() for e in args.exclude.split(",") if e.strip()}
    excluded = existing | extra

    print(f"theme: {args.theme}", file=sys.stderr)
    print(f"endpoint: {endpoint['name']} ({endpoint['model']})  "
          f"seed: {args.seed}  prompt_version: {PROMPT_VERSION}",
          file=sys.stderr)
    print(f"count: {args.count}  excluded: {len(excluded)}", file=sys.stderr)

    seen_in_batch: set[str] = set()

    def validator(lens: dict) -> tuple[bool, str]:
        ok, reason = validate(lens, excluded | seen_in_batch)
        if ok and args.require_primary_texts > 0:
            signals = count_primary_text_signals(lens["system"])
            if signals < args.require_primary_texts:
                return False, (f"only {signals} primary-text signal(s), "
                               f"need >= {args.require_primary_texts}")
        if ok:
            seen_in_batch.add(lens["id"])
        return ok, reason

    schema_hint = ('lenses list; each item has id (snake_case), school, '
                   f'system prompt (>={MIN_SYSTEM_CHARS} chars) ending '
                   'with the schema sentence')
    accepted, rejected, last_result = gc.run_brainstorm(
        endpoint=endpoint,
        build_prompt=lambda: build_prompt(args.theme, args.count,
                                          sorted(excluded)),
        list_key="lenses",
        item_validator=validator,
        base_seed=args.seed,
        self_review=args.self_review,
        schema_hint=schema_hint,
        timeout=900,
        min_accepted=args.min_accepted,
        max_retries=args.max_retries,
        log_fn=lambda m: print(m, file=sys.stderr))
    if last_result is None or (not last_result.ok() and not accepted):
        print(f"ERROR: {last_result.parse_error if last_result else 'no attempts ran'}",
              file=sys.stderr)
        return 1

    result = last_result  # used downstream for provenance

    print(f"accepted: {len(accepted)}  rejected: {len(rejected)}", file=sys.stderr)
    for lens, reason in rejected:
        lid = lens.get("id", "?") if isinstance(lens, dict) else "?"
        print(f"  reject {lid}: {reason}", file=sys.stderr)

    if args.dry_run:
        print(json.dumps({"lenses": accepted}, indent=2, ensure_ascii=False))
        return 0 if accepted else 1

    if accepted:
        AGENTS_DIR.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps({"lenses": accepted}, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8")
        print(f"wrote {len(accepted)} lens(es) to {out_path}", file=sys.stderr)

        log = gc.TsvLog(AGENTS_LOG, LOG_COLUMNS)
        prov = gc.provenance_row(
            source="generator", theme=args.theme, model=result.model,
            seed=args.seed, prompt_version=PROMPT_VERSION)
        rej_prov = {**prov, "source": "rejected"}
        rows = [{**prov, "agent_id": lens["id"], "school": lens["school"],
                 "reason": ""} for lens in accepted]
        rej_rows = [
            {**rej_prov,
             "agent_id": (lens.get("id", "?") if isinstance(lens, dict) else "?"),
             "school": (lens.get("school", "") if isinstance(lens, dict) else ""),
             "reason": reason[:200]}
            for lens, reason in rejected]
        log.append(rows + rej_rows)
        print(f"logged {len(rows)} accepted + {len(rej_rows)} rejected "
              f"row(s) to {AGENTS_LOG}", file=sys.stderr)

        if args.merge:
            merge_path = Path(args.merge)
            if not merge_path.exists():
                raise SystemExit(f"--merge target not found: {merge_path}")
            added_ids, skipped_ids = merge_into_lenses_json(
                accepted, merge_path, dry_run=args.preview_merge)
            verb = "would merge" if args.preview_merge else "merged"
            print(f"{verb} {len(added_ids)} new lens(es) into {merge_path}",
                  file=sys.stderr)
            for lid in added_ids:
                print(f"  + {lid}", file=sys.stderr)
            for lid in skipped_ids:
                print(f"  = {lid} (already present)", file=sys.stderr)
    return 0 if accepted else 1


if __name__ == "__main__":
    raise SystemExit(main())
