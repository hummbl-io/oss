"""Generate a content plan bundle: chain paideia_plan + downstream generators.

Per docs/paideia-9.md §12 next step: "chain paideia_plan + downstream
generators end-to-end." The PAIDEIA plan's `downstream_hints` name four
downstream generators (generate_outline, generate_examples,
generate_assessment, generate_delivery). None of those generators exist yet,
so this bundle does NOT invent them. It:

  1. Wraps a validated PAIDEIA plan (from generate_paideia_plan) into a
     versioned content-plan bundle.
  2. Records each downstream hint with an honest `implemented` flag derived
     from whether the generator module is importable. Today all four are
     `not_implemented` -- the bundle captures the full end-to-end intent and
     marks what is not yet wired, rather than faking it.
  3. Introduces the v0.2 `intent` polarity field on per-axis entries as an
     ADDITIVE optional layer: entries may carry `intent` in
     {"required","deliberate_absent","n_a"}; entries without it default to
     "required" (v0.1 behavior). This primes the v0.2 adoption (Lane 1)
     without breaking v0.1 plans.

CPU-only by design: `build_bundle(plan)` and `validate_bundle(bundle)` take
plain dicts and never touch the network. The CLI can optionally call the
planner via Ollama when invoked with --topic (and no --plan), but the core
logic is fully testable with synthetic plans.

Bundle schema (content-plan-bundle-v1):
{
  "bundle_version": "content-plan-bundle-v1",
  "plan": <validated PAIDEIA plan, per_axis entries may carry "intent">,
  "downstream": {
    "<generator>": {"hint": str, "implemented": bool, "status": str},
    ...
  },
  "intent_polarity": {"<axis>": "required"|"deliberate_absent"|"n_a", ...},
  "_provenance": {timestamp_utc, bundle_version, source, ...}
}

Usage:
    # CPU-only: wrap an existing plan JSON into a bundle
    python generate_content_plan_bundle.py --plan paideia/plans/plan-X.json

    # End-to-end (calls planner via Ollama): plan then bundle
    python generate_content_plan_bundle.py --topic "rate limiters" \\
        --expertise-stage competent --target-solo relational
"""
from __future__ import annotations

import datetime as dt
import importlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _gen_common as gc
import ecosystem_contracts as ec
import generate_paideia_plan as gpp

BUNDLE_VERSION = "content-plan-bundle-v1"
PROMPT_VERSION = "content-plan-bundle-v1"
HERE = Path(__file__).resolve().parent
BUNDLES_DIR = HERE / "paideia" / "bundles"

# The four downstream generators named in paideia_plan_v1/v2 downstream_hints.
# None exist yet (verified by implemented_generators()); the bundle records
# their hints with implemented=False until they land (Lane 4 / executable slice).
KNOWN_DOWNSTREAM = (
    "generate_outline",
    "generate_examples",
    "generate_assessment",
    "generate_delivery",
)

# v0.2 intent polarity values (additive; defaults to "required" for v0.1 plans).
# Canonical source is ecosystem_contracts; re-exported here for convenience.
INTENT_VALUES = ec.PAIDEIA_INTENT_VALUES
DEFAULT_INTENT = ec.PAIDEIA_DEFAULT_INTENT

AXES = ec.PAIDEIA_AXES


def implemented_generators() -> set[str]:
    """Return the subset of KNOWN_DOWNSTREAM that is importable as a module.

    Honest gate: a downstream generator counts as implemented only if its
    module imports. Today this returns an empty set. When Lane 4 lands the
    generators, this flips per-generator without touching the bundle code.
    """
    out: set[str] = set()
    for name in KNOWN_DOWNSTREAM:
        try:
            importlib.import_module(name)
            out.add(name)
        except ModuleNotFoundError:
            continue
    return out


def normalize_plan_intent(plan: dict) -> dict:
    """Add the v0.2 `intent` field to per_axis entries, defaulting to
    "required" where absent (v0.1 behavior). Validates any present `intent`
    value. Returns a new plan dict (does not mutate the input).

    Raises ValueError if a present `intent` is not one of INTENT_VALUES.
    """
    per_axis = plan.get("per_axis", {})
    new_per_axis: dict = {}
    for axis in AXES:
        entry = dict(per_axis.get(axis, {}))
        intent = entry.get("intent", DEFAULT_INTENT)
        if intent not in INTENT_VALUES:
            raise ValueError(
                f"per_axis[{axis}].intent={intent!r} must be one of "
                f"{INTENT_VALUES}")
        entry["intent"] = intent
        new_per_axis[axis] = entry
    new_plan = dict(plan)
    new_plan["per_axis"] = new_per_axis
    return new_plan


def build_bundle(plan: dict, *, source: str = "generator") -> dict:
    """Wrap a validated PAIDEIA plan into a content-plan bundle.

    The plan is first normalized (intent field added) then validated via
    generate_paideia_plan.validate_plan. Downstream entries are built from
    plan.downstream_hints, with `implemented` derived from
    implemented_generators(). intent_polarity is derived from the normalized
    per_axis intent values.
    """
    plan = normalize_plan_intent(plan)
    ok, reason = gpp.validate_plan(plan)
    if not ok:
        raise ValueError(f"invalid PAIDEIA plan: {reason}")

    hints = plan.get("downstream_hints", {}) or {}
    implemented = implemented_generators()
    downstream: dict = {}
    for gen in KNOWN_DOWNSTREAM:
        hint = hints.get(gen, "")
        is_impl = gen in implemented
        downstream[gen] = {
            "hint": hint,
            "implemented": is_impl,
            "status": "implemented" if is_impl else "not_implemented",
        }

    intent_polarity = {a: plan["per_axis"][a]["intent"] for a in AXES}

    return {
        "bundle_version": BUNDLE_VERSION,
        "plan": plan,
        "downstream": downstream,
        "intent_polarity": intent_polarity,
        "_provenance": {
            "timestamp_utc": gc.now_utc_iso(),
            "bundle_version": BUNDLE_VERSION,
            "source": source,
            "common_version": gc.COMMON_VERSION,
        },
    }


def validate_bundle(bundle: dict) -> tuple[bool, str]:
    """Validate a content-plan bundle's shape and inner plan."""
    if not isinstance(bundle, dict):
        return False, "bundle must be a dict"
    if bundle.get("bundle_version") != BUNDLE_VERSION:
        return False, f"bundle_version must be {BUNDLE_VERSION!r}"
    plan = bundle.get("plan")
    if not isinstance(plan, dict):
        return False, "missing plan dict"
    ok, reason = gpp.validate_plan(plan)
    if not ok:
        return False, f"plan invalid: {reason}"
    downstream = bundle.get("downstream")
    if not isinstance(downstream, dict):
        return False, "missing downstream dict"
    for gen in KNOWN_DOWNSTREAM:
        if gen not in downstream:
            return False, f"downstream missing generator {gen}"
        entry = downstream[gen]
        if not isinstance(entry, dict):
            return False, f"downstream[{gen}] must be a dict"
        for field in ("hint", "implemented", "status"):
            if field not in entry:
                return False, f"downstream[{gen}] missing {field}"
        if not isinstance(entry["implemented"], bool):
            return False, f"downstream[{gen}].implemented must be bool"
    ip = bundle.get("intent_polarity")
    if not isinstance(ip, dict):
        return False, "missing intent_polarity dict"
    for axis in AXES:
        if axis not in ip:
            return False, f"intent_polarity missing axis {axis}"
        if ip[axis] not in INTENT_VALUES:
            return False, (f"intent_polarity[{axis}]={ip[axis]!r} must be "
                           f"one of {INTENT_VALUES}")
    return True, ""


def _slugify(s: str, max_len: int = 60) -> str:
    return gpp.slugify(s, max_len=max_len)


def main(argv: list[str] | None = None) -> int:
    p = gc.standard_argparse(__doc__)
    p.add_argument("--plan", default=None,
                   help="path to an existing PAIDEIA plan JSON to bundle "
                        "(CPU-only; no Ollama call).")
    p.add_argument("--topic", default=None,
                   help="topic to plan then bundle (calls the planner via "
                        "Ollama). Required if --plan is not given.")
    p.add_argument("--expertise-stage", default="competent",
                   choices=gpp.EXPERTISE_STAGES)
    p.add_argument("--prior-knowledge", default="")
    p.add_argument("--goals", default="")
    p.add_argument("--delivery-context", default="solo",
                   choices=gpp.DELIVERY_CONTEXTS)
    p.add_argument("--target-solo", default="relational",
                   choices=gpp.SOLO_LEVELS)
    p.add_argument("--instructional-intent", type=lambda s: s.lower() != "false",
                   default=True)
    p.add_argument("--output", default=None,
                   help="write bundle JSON to this path (default: stdout)")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)

    if args.plan:
        plan_path = Path(args.plan)
        if not plan_path.exists():
            print(f"error: plan not found: {plan_path}", file=sys.stderr)
            return 1
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        source = f"plan-file:{plan_path.name}"
        print(f"bundling existing plan: {plan_path}", file=sys.stderr)
    elif args.topic:
        endpoint = gc.load_endpoint(args.endpoint)
        if args.model:
            endpoint = dict(endpoint)
            endpoint["model"] = args.model
        system, user = gpp.build_prompt(
            args.topic, args.expertise_stage, args.prior_knowledge,
            args.goals, args.delivery_context, args.target_solo,
            args.instructional_intent)
        print(f"planning then bundling topic: {args.topic}", file=sys.stderr)
        print(f"endpoint: {endpoint['name']} ({endpoint['model']})",
              file=sys.stderr)
        result = gc.ollama_generate(endpoint, system, user, seed=args.seed,
                                    think=False, timeout=600)
        if not result.ok():
            print(f"ERROR: planner call failed: {result.parse_error}",
                  file=sys.stderr)
            return 1
        plan = result.parsed
        source = "planner+bundle"
    else:
        print("error: provide --plan PATH or --topic TEXT", file=sys.stderr)
        return 2

    try:
        bundle = build_bundle(plan, source=source)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    ok, reason = validate_bundle(bundle)
    if not ok:
        print(f"bundle validation failed: {reason}", file=sys.stderr)
        return 2

    impl = [g for g, e in bundle["downstream"].items() if e["implemented"]]
    not_impl = [g for g, e in bundle["downstream"].items() if not e["implemented"]]
    print(f"downstream implemented={impl} not_implemented={not_impl}",
          file=sys.stderr)
    print(f"intent_polarity defaults: "
          f"{sum(1 for v in bundle['intent_polarity'].values() if v == 'required')}"
          f"/{len(AXES)} required", file=sys.stderr)

    if args.dry_run or not args.output:
        print(json.dumps(bundle, indent=2, ensure_ascii=False))
        if args.dry_run:
            return 0

    if args.output:
        out_path = Path(args.output)
    else:
        slug = _slugify(args.topic or "untitled")
        out_path = BUNDLES_DIR / f"bundle-{dt.datetime.now(dt.UTC).date().isoformat()}-{slug}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(bundle, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    print(f"wrote bundle to {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
