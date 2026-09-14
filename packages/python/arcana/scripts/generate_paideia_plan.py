"""Generate a PAIDEIA-9 content plan for a topic + consumer profile.

PAIDEIA-9 is a 9-axis evidence-grounded framework for multi-modal content
design. See docs/paideia-9.md for full spec.

This generator takes:
- topic (what to teach/explain/explore)
- consumer_profile (expertise_stage, prior_knowledge, goals, context)
- delivery_context (solo | cohort | agent-mediated)
- target_outcome (SOLO level + retention horizon)
- instructional_intent (true/false; non-instructional artifacts partially-score)

and produces:
- target_vector [M, D, E, V, C, L, S, P, A] on 0-4 scale
- constraints (load_budget, modality_budget)
- downstream_hints for the other generators in the family
- evidence_trace (per-axis citation)
- referent specification per axis (artifact | reader_state | reader_demand)

Output: JSON to paideia/plans/plan-YYYY-MM-DD-<slug>.json (staging).
Log:    paideia/paideia_log.tsv (append-only, tracked).

Usage:
    python generate_paideia_plan.py --topic "rate limiters" \\
        --expertise-stage competent --target-solo relational \\
        --delivery-context solo
    python generate_paideia_plan.py --topic "..." --dry-run
    python generate_paideia_plan.py --topic "..." --self-review
"""
from __future__ import annotations

import datetime as dt
import json
import re
import sys
from pathlib import Path

# Import shared library
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _gen_common as gc
import ecosystem_contracts as ec

PROMPT_VERSION = "paideia-plan-v2"
HERE = Path(__file__).resolve().parent
PAIDEIA_DIR = HERE / "paideia"
PLANS_DIR = PAIDEIA_DIR / "plans"
PAIDEIA_LOG = PAIDEIA_DIR / "paideia_log.tsv"

LOG_COLUMNS = [
    "timestamp_utc", "source", "topic", "expertise_stage", "delivery_context",
    "target_solo", "instructional_intent", "model", "seed",
    "prompt_version", "target_vector",
]

EXPERTISE_STAGES = ("novice", "advanced_beginner", "competent", "proficient", "expert")
SOLO_LEVELS = ("prestructural", "unistructural", "multistructural",
               "relational", "extended_abstract")
DELIVERY_CONTEXTS = ("solo", "cohort", "agent-mediated")

AXES = ec.PAIDEIA_AXES
AXIS_NAMES = ec.PAIDEIA_AXIS_NAMES
PAIDEIA_REFERENTS = ec.PAIDEIA_REFERENTS


def build_prompt(topic: str, expertise_stage: str, prior_knowledge: str,
                 goals: str, delivery_context: str, target_solo: str,
                 instructional_intent: bool) -> tuple[str, str]:
    system, user_tmpl = gc.load_prompt("paideia_plan", "v2")
    user = user_tmpl.safe_substitute(
        topic=topic,
        expertise_stage=expertise_stage,
        prior_knowledge=prior_knowledge or "(not specified)",
        goals=goals or "(not specified)",
        delivery_context=delivery_context,
        target_solo=target_solo,
        instructional_intent=str(instructional_intent).lower())
    return system, user


def validate_plan(plan: dict) -> tuple[bool, str]:
    ok, reason = gc.validate_required_string_fields(
        plan, ("content_type_warning",))
    if not ok and "content_type_warning" not in plan:
        return False, reason
    if "target_vector" not in plan or not isinstance(plan["target_vector"], dict):
        return False, "missing target_vector dict"
    tv = plan["target_vector"]
    for axis in AXES:
        if axis not in tv:
            return False, f"target_vector missing axis {axis}"
        v = tv[axis]
        if not isinstance(v, int) or v < 0 or v > 4:
            return False, f"target_vector[{axis}]={v} must be integer 0..4"
    if "per_axis" not in plan or not isinstance(plan["per_axis"], dict):
        return False, "missing per_axis dict"
    for axis in AXES:
        if axis not in plan["per_axis"]:
            return False, f"per_axis missing axis {axis}"
        entry = plan["per_axis"][axis]
        for field in ("target", "referent", "rationale", "citation"):
            if field not in entry:
                return False, f"per_axis[{axis}] missing {field}"
        if entry["referent"] not in PAIDEIA_REFERENTS:
            return False, (f"per_axis[{axis}].referent must be one of "
                           f"{'|'.join(PAIDEIA_REFERENTS)}")
        # v0.2 additive: optional intent polarity field (Proposal C). Absent
        # means "required" (v0.1 behavior); present must be a valid value.
        if "intent" in entry and entry["intent"] not in ec.PAIDEIA_INTENT_VALUES:
            return False, (f"per_axis[{axis}].intent={entry['intent']!r} must "
                           f"be one of {'|'.join(ec.PAIDEIA_INTENT_VALUES)}")
    if "constraints" not in plan or not isinstance(plan["constraints"], dict):
        return False, "missing constraints"
    return True, ""


def slugify(s: str, max_len: int = 60) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:max_len] or "untitled"


def main(argv: list[str] | None = None) -> int:
    p = gc.standard_argparse(__doc__)
    p.add_argument("--topic", required=True)
    p.add_argument("--expertise-stage", default="competent",
                   choices=EXPERTISE_STAGES)
    p.add_argument("--prior-knowledge", default="")
    p.add_argument("--goals", default="")
    p.add_argument("--delivery-context", default="solo",
                   choices=DELIVERY_CONTEXTS)
    p.add_argument("--target-solo", default="relational",
                   choices=SOLO_LEVELS)
    p.add_argument("--instructional-intent", type=lambda s: s.lower() != "false",
                   default=True,
                   help="set to 'false' for non-instructional artifacts (poetry, "
                        "entertainment) — triggers content_type_warning")
    args = p.parse_args(argv)

    endpoint = gc.load_endpoint(args.endpoint)
    system, user = build_prompt(
        args.topic, args.expertise_stage, args.prior_knowledge, args.goals,
        args.delivery_context, args.target_solo, args.instructional_intent)

    print(f"topic: {args.topic}", file=sys.stderr)
    print(f"expertise: {args.expertise_stage}  delivery: {args.delivery_context}  "
          f"target_solo: {args.target_solo}  intent: {args.instructional_intent}",
          file=sys.stderr)
    print(f"endpoint: {endpoint['name']} ({args.model or endpoint['model']})  "
          f"seed: {args.seed}  prompt_version: {PROMPT_VERSION}",
          file=sys.stderr)

    if args.model:
        endpoint = dict(endpoint)
        endpoint["model"] = args.model

    result = gc.ollama_generate(endpoint, system, user, seed=args.seed,
                                think=False, timeout=600)
    if not result.ok():
        print(f"ERROR: ollama call failed: {result.parse_error}", file=sys.stderr)
        if result.raw:
            print(f"raw response (first 400 chars): {result.raw[:400]}",
                  file=sys.stderr)
        return 1

    plan = result.parsed

    if args.self_review:
        print("running self-review pass...", file=sys.stderr)
        schema_hint = ("PAIDEIA-9 plan with target_vector (M,D,E,V,C,L,S,P,A "
                       "all 0-4 integers), per_axis entries with target/referent/"
                       "rationale/citation, constraints, downstream_hints.")
        review = gc.self_review(endpoint, plan, schema_hint, seed=args.seed)
        if review.ok():
            plan = review.parsed
        else:
            print(f"  self-review failed: {review.parse_error} — using original",
                  file=sys.stderr)

    ok, reason = validate_plan(plan) if isinstance(plan, dict) else (False, "not a dict")
    if not ok:
        print(f"validation failed: {reason}", file=sys.stderr)
        print(json.dumps(plan, indent=2, ensure_ascii=False)[:800], file=sys.stderr)
        return 2

    vector_str = "-".join(str(plan["target_vector"][a]) for a in AXES)
    print(f"target_vector (M-D-E-V-C-L-S-P-A): {vector_str}", file=sys.stderr)
    print(f"elapsed: {result.elapsed_s}s, tokens in/out: "
          f"{result.prompt_tokens}/{result.completion_tokens}", file=sys.stderr)

    # Attach provenance
    plan["_provenance"] = {
        "topic": args.topic,
        "expertise_stage": args.expertise_stage,
        "delivery_context": args.delivery_context,
        "target_solo": args.target_solo,
        "prompt_version": PROMPT_VERSION,
        "common_version": gc.COMMON_VERSION,
        "model": result.model,
        "endpoint": result.endpoint_name,
        "seed": args.seed,
        "self_review": args.self_review,
        "timestamp_utc": gc.now_utc_iso(),
    }

    if args.dry_run:
        print(json.dumps(plan, indent=2, ensure_ascii=False))
        return 0

    slug = slugify(args.topic)
    out_path = Path(args.output) if args.output else \
        PLANS_DIR / f"plan-{dt.datetime.now(dt.UTC).date().isoformat()}-{slug}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote plan to {out_path}", file=sys.stderr)

    log = gc.TsvLog(PAIDEIA_LOG, LOG_COLUMNS)
    log.append([{
        **gc.provenance_row(
            source="generator", theme=args.topic,
            model=result.model, seed=args.seed,
            prompt_version=PROMPT_VERSION),
        "topic": args.topic,
        "expertise_stage": args.expertise_stage,
        "delivery_context": args.delivery_context,
        "target_solo": args.target_solo,
        "instructional_intent": str(args.instructional_intent).lower(),
        "target_vector": vector_str,
    }])
    print(f"logged to {PAIDEIA_LOG}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
