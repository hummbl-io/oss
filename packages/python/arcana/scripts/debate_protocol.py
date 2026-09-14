"""Adversarial debate protocol for ARCANA topics.

Implements the Constructive Agent + Adversarial Agent + Hidden Arbiter
protocol: a TopicSpec goes in, a governed verdict ledger comes out.
Reusable infrastructure -- any TopicSpec can run through it.

Phases (per the debate protocol):
  1. formalization      define core terms before substantive debate
  2. constructive       Constructive Agent defends the resolution (blind)
  3. adversarial        Adversarial Agent attacks the resolution (blind)
  4. cross_examination  each side probes the other's weakest assumptions,
                        hidden premises, category errors, unfalsifiable claims
  5. repair             each side may revise; revisions are logged
  6. applied_cases      analyze every required test case
  7. synthesis          state what remains defensible / weakened /
                        domain-limited / unresolved
  8. arbiter_verdict    Hidden Arbiter evaluates each major claim independently

Constructive and adversarial phases are BLIND: each receives only the spec
and the formalized definitions, not the other side's draft. Cross-examination
is the first phase that sees both. This preserves genuine independence, which
a single merged call cannot.

Each phase is one Ollama /api/generate call returning structured JSON. The
Hidden Arbiter emits per-claim verdicts from VERDICT_STATUSES. Output is a
governed verdict ledger with the 17 required fields, written to
outputs/<date>/<slug>/debate/verdict_ledger.json plus per-phase raw responses
and a run log.

Uses _gen_common.ollama_generate + OllamaResult with ollama_fn injection
(mirrors run_brainstorm / score_paideia) so tests mock without a live Ollama.

Usage:
    python debate_protocol.py --spec topics/arcana-metaethics-good-evil-001.json
    python debate_protocol.py --spec ... --endpoint ollama-local --dry-run
    python debate_protocol.py --spec ... --output-dir outputs/2026-09-09/good-evil/debate
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

import _gen_common as gc

HERE = Path(__file__).resolve().parent
OUTPUTS_ROOT = HERE / "outputs"

PROMPT_VERSION = "debate-v1"

# The six verdicts the Hidden Arbiter may emit (per the protocol). Anything
# outside this set is normalized to UNRESOLVED.
VERDICT_STATUSES = (
    "ACCEPTED",
    "REFUTED",
    "CONDITIONAL",
    "DOMAIN_LIMITED",
    "UNRESOLVED",
    "NEEDS_FORMALIZATION",
)

# The 17 required ledger fields, in canonical order. assemble_ledger must
# produce every one of these (None / [] when a phase failed, never missing).
LEDGER_FIELDS = (
    "topic_id",
    "resolution",
    "definitions",
    "assumptions",
    "constructive_claims",
    "adversarial_claims",
    "empirical_evidence",
    "normative_premises",
    "theological_premises",
    "objections",
    "repairs",
    "applied_case_results",
    "domain_of_validity",
    "unresolved_questions",
    "verdict_status",
    "arbiter_reasoning",
    "recommended_follow_up",
)

# Required keys in a TopicSpec JSON.
SPEC_REQUIRED_KEYS = (
    "topic_id",
    "topic",
    "resolution",
    "definitions_required",
    "constructive_mandate",
    "adversarial_mandate",
    "applied_cases",
)

PHASES = (
    "formalization",
    "constructive",
    "adversarial",
    "cross_examination",
    "repair",
    "applied_cases",
    "synthesis",
    "arbiter_verdict",
)


# ------------------------------- spec loading ------------------------------- #

def load_topic_spec(path: Path) -> dict:
    """Load + validate a TopicSpec JSON. Raises SystemExit on structural error."""
    if not path.exists():
        raise SystemExit(f"topic spec not found: {path}")
    spec = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(spec, dict):
        raise SystemExit(f"spec must be a JSON object: {path}")
    for key in SPEC_REQUIRED_KEYS:
        if key not in spec:
            raise SystemExit(f"spec missing required key: {key}")
    if not isinstance(spec["applied_cases"], list) or not spec["applied_cases"]:
        raise SystemExit("spec 'applied_cases' must be a non-empty list")
    return spec


def slugify(s: str, max_len: int = 60) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:max_len] or "untitled"


# ------------------------------- prompt builders ---------------------------- #
# Each returns (system, user). Phases that depend on prior phases receive the
# accumulated `ctx` dict. Prompts ask for JSON with a documented shape so the
# parser can validate.

_SYSTEM_BASE = (
    "You are a rigorous interdisciplinary analyst in a governed debate "
    "protocol. Every output MUST be a single valid JSON object with the exact "
    "keys requested, no prose outside the JSON. Declare domain, claim type, "
    "evidence class, assumptions, scope, uncertainty, consequences if accepted, "
    "and revision conditions for every major claim. Never derive an ought from "
    "an is without exposing the normative premise."
)


def _claim_schema_hint() -> str:
    return (
        'Each claim object: {"id": str, "claim": str, "claim_type": '
        '"empirical|historical|psychological|semantic|normative|metaethical|'
        'metaphysical|theological|pragmatic|narrative", "evidence_class": str, '
        '"assumptions": [str], "scope": str, "uncertainty": str, '
        '"consequences_if_accepted": str, "revision_conditions": str}'
    )


def build_formalization_prompt(spec: dict) -> tuple[str, str]:
    terms = spec["definitions_required"]
    system = _SYSTEM_BASE
    user = (
        f"Topic: {spec['topic']}\n"
        f"Resolution under debate: {spec['resolution']}\n\n"
        f"Phase 1 -- FORMALIZATION. Provide stable, explicit definitions for "
        f"each of these terms before any substantive debate:\n"
        f"{json.dumps(terms, ensure_ascii=False, indent=2)}\n\n"
        f"Return JSON: {{\"definitions\": "
        f"[{{\"term\": str, \"definition\": str, \"contested\": bool}}], "
        f"\"assumptions\": [str]}}"
    )
    return system, user


def build_constructive_prompt(spec: dict, definitions: list) -> tuple[str, str]:
    system = _SYSTEM_BASE + " You are the CONSTRUCTIVE AGENT: defend the resolution."
    user = (
        f"Topic: {spec['topic']}\n"
        f"Resolution: {spec['resolution']}\n"
        f"Formalized definitions: {json.dumps(definitions, ensure_ascii=False)}\n\n"
        f"Constructive mandate:\n{spec['constructive_mandate']}\n\n"
        f"Phase 2 -- CONSTRUCTIVE CASE. Establish the resolution in its strongest "
        f"form. You MUST also identify the strongest limitations and failure modes "
        f"of your own case.\n\n"
        f"Return JSON: {{\"claims\": [claim, ...], "
        f"\"self_identified_limitations\": [str]}}. "
        f"{_claim_schema_hint()}"
    )
    return system, user


def build_adversarial_prompt(spec: dict, definitions: list) -> tuple[str, str]:
    system = _SYSTEM_BASE + " You are the ADVERSARIAL AGENT: attack the resolution."
    user = (
        f"Topic: {spec['topic']}\n"
        f"Resolution: {spec['resolution']}\n"
        f"Formalized definitions: {json.dumps(definitions, ensure_ascii=False)}\n\n"
        f"Adversarial mandate:\n{spec['adversarial_mandate']}\n\n"
        f"Phase 3 -- ADVERSARIAL CASE. Attack the resolution in its strongest "
        f"form. You are NOT required to endorse any particular theology. Probe "
        f"whether calling Good and Evil mental models improperly reduces moral "
        f"reality to cognition, whether revisability weakens condemnation of "
        f"atrocities, and whether the framework confuses uncertainty about moral "
        f"knowledge with uncertainty about moral truth.\n\n"
        f"Return JSON: {{\"claims\": [claim, ...], "
        f"\"strongest_objection\": str}}. "
        f"{_claim_schema_hint()}"
    )
    return system, user


def build_cross_examination_prompt(spec: dict, constructive: dict,
                                   adversarial: dict) -> tuple[str, str]:
    system = _SYSTEM_BASE + " You are the CROSS-EXAMINATION phase."
    user = (
        f"Resolution: {spec['resolution']}\n\n"
        f"Constructive claims: {json.dumps(constructive.get('claims', []), ensure_ascii=False)}\n\n"
        f"Adversarial claims: {json.dumps(adversarial.get('claims', []), ensure_ascii=False)}\n\n"
        f"Phase 4 -- CROSS-EXAMINATION. For each side, identify: the strongest "
        f"opposing claim against it, its weakest assumption, hidden premises, "
        f"category errors, and any unfalsifiable claims.\n\n"
        f"Return JSON: {{\"objections\": "
        f"[{{\"target\": \"constructive|adversarial\", \"strongest_opposing_claim\": str, "
        f"\"weakest_assumption\": str, \"hidden_premises\": [str], "
        f"\"category_errors\": [str], \"unfalsifiable_claims\": [str]}}]}}"
    )
    return system, user


def build_repair_prompt(spec: dict, constructive: dict, adversarial: dict,
                        objections: list) -> tuple[str, str]:
    system = _SYSTEM_BASE + " You are the REPAIR phase."
    user = (
        f"Resolution: {spec['resolution']}\n\n"
        f"Constructive claims: {json.dumps(constructive.get('claims', []), ensure_ascii=False)}\n\n"
        f"Adversarial claims: {json.dumps(adversarial.get('claims', []), ensure_ascii=False)}\n\n"
        f"Cross-examination objections: {json.dumps(objections, ensure_ascii=False)}\n\n"
        f"Phase 5 -- REPAIR. Each side may revise its position in response to "
        f"the cross-examination. Revisions MUST be logged with what changed and why.\n\n"
        f"Return JSON: {{\"repairs\": "
        f"[{{\"side\": \"constructive|adversarial\", \"revised_claims\": [claim], "
        f"\"what_changed\": str, \"why\": str}}]}}. "
        f"{_claim_schema_hint()}"
    )
    return system, user


def build_applied_cases_prompt(spec: dict, repairs: list) -> tuple[str, str]:
    system = _SYSTEM_BASE + " You are the APPLIED CASES phase."
    cases = spec["applied_cases"]
    user = (
        f"Resolution: {spec['resolution']}\n"
        f"Repaired positions: {json.dumps(repairs, ensure_ascii=False)}\n\n"
        f"Phase 6 -- APPLIED CASES. Analyze EVERY one of these required test "
        f"cases and give an explicit judgment for each:\n"
        f"{json.dumps(cases, ensure_ascii=False, indent=2)}\n\n"
        f"Return JSON: {{\"applied_case_results\": "
        f"[{{\"case_id\": str, \"case\": str, \"judgment\": str, "
        f"\"moral_model_used\": str, \"uncertainty\": str}}]}}"
    )
    return system, user


def build_synthesis_prompt(spec: dict, applied_cases: dict) -> tuple[str, str]:
    system = _SYSTEM_BASE + " You are the SYNTHESIS phase."
    user = (
        f"Resolution: {spec['resolution']}\n"
        f"Applied case results: {json.dumps(applied_cases, ensure_ascii=False)}\n\n"
        f"Phase 7 -- SYNTHESIS. State what remains defensible, what is weakened, "
        f"what is domain-limited, and what is unresolved. Do NOT force artificial "
        f"closure -- preserve unresolved questions.\n\n"
        f"Return JSON: {{\"defensible\": [str], \"weakened\": [str], "
        f"\"domain_of_validity\": [str], \"unresolved_questions\": [str]}}"
    )
    return system, user


def build_arbiter_prompt(spec: dict, synthesis: dict,
                         all_claims: list) -> tuple[str, str]:
    system = (
        _SYSTEM_BASE + " You are the HIDDEN ARBITER. Evaluate claims "
        "INDIVIDUALLY -- do not declare a single debate winner. Each claim gets "
        "one verdict from: " + ", ".join(VERDICT_STATUSES) + ". "
        "Use the FULL verdict range: CONDITIONAL, DOMAIN_LIMITED, and "
        "NEEDS_FORMALIZATION are often the most accurate verdicts for contested "
        "claims -- defaulting to only ACCEPTED/REFUTED is a failure mode. A "
        "balanced arbiter normally emits a MIX of verdicts, not a unanimous block."
    )
    user = (
        f"Resolution: {spec['resolution']}\n"
        f"Synthesis: {json.dumps(synthesis, ensure_ascii=False)}\n\n"
        f"Claims to verdict (each evaluated independently):\n"
        f"{json.dumps(all_claims, ensure_ascii=False, indent=2)}\n\n"
        f"Phase 8 -- ARBITER VERDICT. For each claim, emit a verdict, the "
        f"reasoning, the domain of validity, and any recommended follow-up.\n\n"
        f"Return JSON: {{\"verdicts\": "
        f"[{{\"claim_id\": str, \"verdict\": "
        f"\"{'|'.join(VERDICT_STATUSES)}\", \"reasoning\": str, "
        f"\"domain_of_validity\": str}}], \"arbiter_reasoning\": str, "
        f"\"recommended_follow_up\": [str]}}"
    )
    return system, user


# ------------------------------- phase runner ------------------------------- #

def _run_phase(name: str, endpoint: dict, system: str, user: str,
               ollama_fn, log, seed: int | None = None,
               timeout: int = 900) -> gc.OllamaResult:
    log(f"[phase:{name} @ {endpoint['name']}] starting...")
    result = ollama_fn(endpoint, system, user, seed=seed, think=False,
                       timeout=timeout)
    if result.ok():
        log(f"[phase:{name}] done in {result.elapsed_s}s "
            f"({result.completion_tokens} tok)")
    else:
        log(f"[phase:{name}] FAILED: {result.parse_error}")
    return result


def _parsed(result: gc.OllamaResult) -> dict:
    """Return the parsed dict, or an error envelope on parse failure."""
    if not result.ok() or not isinstance(result.parsed, dict):
        return {"_error": result.parse_error or "no parsed JSON",
                "_raw": result.raw[:500] if result.raw else ""}
    return result.parsed


def _as_list(value) -> list:
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def _claims_by_type(claims: list, claim_type: str) -> list:
    return [c for c in claims
            if isinstance(c, dict) and c.get("claim_type") == claim_type]


def _normalize_verdict(v: str) -> str:
    if isinstance(v, str):
        upper = v.strip().upper().replace(" ", "_")
        if upper in VERDICT_STATUSES:
            return upper
    return "UNRESOLVED"


# Verdicts that represent genuine intermediate judgment, not binary
# accept/refute. Their absence (with enough claims) signals the arbiter
# defaulted to a binary mode -- the failure mode this check catches.
_INTERMEDIATE_VERDICTS = ("CONDITIONAL", "DOMAIN_LIMITED", "NEEDS_FORMALIZATION")


def verdict_distribution(verdicts: list) -> dict:
    """Count verdicts by status. Accepts either normalized verdict dicts
    (with a 'verdict' key) or bare status strings."""
    counts: dict[str, int] = {}
    for v in verdicts:
        status = v["verdict"] if isinstance(v, dict) else v
        counts[status] = counts.get(status, 0) + 1
    return counts


def flag_lopsided_verdicts(verdicts: list, log) -> list[str]:
    """Warn when the arbiter's verdict distribution is suspiciously one-sided.

    Returns the warnings (also logged). Does NOT mutate the verdicts -- the
    arbiter's actual output is preserved; the operator sees the warning and
    can rerun with a different seed or larger model.

    Two failure modes flagged:
    1. Unanimous: n >= 3 and all verdicts identical (arbiter failed to
       discriminate between claims at all).
    2. Binary-only: n >= 4 and no intermediate verdicts used -- the arbiter
       ignored CONDITIONAL/DOMAIN_LIMITED/NEEDS_FORMALIZATION and defaulted
       to accept/refute.
    """
    n = len(verdicts)
    warnings: list[str] = []
    if n == 0:
        return warnings
    counts = verdict_distribution(verdicts)
    if n >= 3 and len(counts) == 1:
        only = next(iter(counts))
        warnings.append(
            f"arbiter-balance WARNING: all {n} verdicts are {only} -- arbiter "
            f"did not discriminate between claims; consider a larger model or "
            f"different seed.")
    if n >= 4 and not any(s in counts for s in _INTERMEDIATE_VERDICTS):
        warnings.append(
            f"arbiter-balance WARNING: {n} verdicts and none are "
            f"CONDITIONAL/DOMAIN_LIMITED/NEEDS_FORMALIZATION -- arbiter "
            f"defaulted to binary accept/refute; the full verdict range was "
            f"not used.")
    for w in warnings:
        log(w)
    return warnings


# ------------------------------- orchestration ------------------------------ #

def run_debate(spec: dict, endpoint: dict, *,
               ollama_fn=None, log=print, output_dir: Path | None = None,
               seed: int | None = None, write_artifacts: bool = True
               ) -> dict:
    """Run all 8 debate phases and assemble the verdict ledger.

    ollama_fn: dependency-injection for tests; production leaves None to use
    gc.ollama_generate.
    """
    if ollama_fn is None:
        ollama_fn = gc.ollama_generate

    slug = slugify(spec["topic"])
    today = dt.datetime.now(dt.UTC).date().isoformat()
    out_dir = output_dir or OUTPUTS_ROOT / today / slug / "debate"
    if write_artifacts:
        out_dir.mkdir(parents=True, exist_ok=True)

    raw_results: dict[str, gc.OllamaResult] = {}
    parsed: dict[str, dict] = {}

    def _phase(name: str, system: str, user: str) -> dict:
        result = _run_phase(name, endpoint, system, user, ollama_fn, log,
                            seed=seed)
        raw_results[name] = result
        p = _parsed(result)
        parsed[name] = p
        if write_artifacts and result.raw:
            (out_dir / f"phase_{name}.json").write_text(
                json.dumps({"parsed": p, "raw": result.raw,
                            "elapsed_s": result.elapsed_s,
                            "parse_error": result.parse_error},
                           indent=2, ensure_ascii=False), encoding="utf-8")
        return p

    # 1. formalization
    formal = _phase("formalization", *build_formalization_prompt(spec))
    definitions = _as_list(formal.get("definitions")) if "_error" not in formal else []

    # 2. constructive (blind) + 3. adversarial (blind)
    constructive = _phase("constructive",
                          *build_constructive_prompt(spec, definitions))
    adversarial = _phase("adversarial",
                         *build_adversarial_prompt(spec, definitions))

    # 4. cross-examination (sees both)
    crossx = _phase("cross_examination",
                    *build_cross_examination_prompt(spec, constructive, adversarial))
    objections = _as_list(crossx.get("objections")) if "_error" not in crossx else []

    # 5. repair
    repair = _phase("repair",
                    *build_repair_prompt(spec, constructive, adversarial, objections))
    repairs = _as_list(repair.get("repairs")) if "_error" not in repair else []

    # 6. applied cases
    applied = _phase("applied_cases",
                     *build_applied_cases_prompt(spec, repairs))
    applied_results = (_as_list(applied.get("applied_case_results"))
                       if "_error" not in applied else [])

    # 7. synthesis
    synthesis = _phase("synthesis",
                       *build_synthesis_prompt(spec, applied))
    domain = (_as_list(synthesis.get("domain_of_validity"))
              if "_error" not in synthesis else [])
    unresolved = (_as_list(synthesis.get("unresolved_questions"))
                  if "_error" not in synthesis else [])

    # 8. arbiter verdict (sees everything)
    all_claims = (_as_list(constructive.get("claims"))
                  + _as_list(adversarial.get("claims")))
    arbiter = _phase("arbiter_verdict",
                     *build_arbiter_prompt(spec, synthesis, all_claims))
    verdicts = (_as_list(arbiter.get("verdicts"))
                if "_error" not in arbiter else [])
    for v in verdicts:
        if isinstance(v, dict):
            v["verdict"] = _normalize_verdict(v.get("verdict"))
    balance_warnings = flag_lopsided_verdicts(verdicts, log)

    ledger = assemble_ledger(
        spec=spec,
        formalization=formal,
        constructive=constructive,
        adversarial=adversarial,
        cross_examination=crossx,
        repair=repair,
        applied_cases=applied,
        synthesis=synthesis,
        arbiter=arbiter,
    )
    ledger["_provenance"] = {
        "generated_at": gc.now_utc_iso(),
        "model": endpoint.get("model"),
        "endpoint": endpoint.get("name"),
        "prompt_version": PROMPT_VERSION,
        "seed": seed,
        "phases_run": list(parsed.keys()),
        "phase_errors": {n: p["_error"] for n, p in parsed.items()
                         if "_error" in p},
        "verdict_distribution": verdict_distribution(verdicts),
        "arbiter_balance_warnings": balance_warnings,
    }

    if write_artifacts:
        (out_dir / "verdict_ledger.json").write_text(
            json.dumps(ledger, indent=2, ensure_ascii=False), encoding="utf-8")
        log(f"done. ledger in {out_dir / 'verdict_ledger.json'}")
    return ledger


def assemble_ledger(*, spec: dict, formalization: dict, constructive: dict,
                    adversarial: dict, cross_examination: dict, repair: dict,
                    applied_cases: dict, synthesis: dict, arbiter: dict) -> dict:
    """Build the 17-field governed verdict ledger from phase outputs.

    Every LEDGER_FIELDS key is present (None / [] on phase failure, never
    missing). Claim-type separation routes empirical/normative/theological
    claims to their dedicated fields while preserving the full claim lists.
    """
    def _claims(phase: dict) -> list:
        return _as_list(phase.get("claims")) if "_error" not in phase else []

    def _field(phase: dict, key: str, default=None):
        return phase.get(key, default if default is not None else []) \
            if "_error" not in phase else (default if default is not None else [])

    constructive_claims = _claims(constructive)
    adversarial_claims = _claims(adversarial)
    all_claims = constructive_claims + adversarial_claims

    # Repair-phase revised claims also count toward type separation.
    repair_claims = []
    for r in _as_list(repair.get("repairs")):
        if isinstance(r, dict):
            repair_claims.extend(_as_list(r.get("revised_claims")))
    combined_for_typing = all_claims + repair_claims

    definitions = _as_list(formalization.get("definitions"))
    assumptions = (_as_list(formalization.get("assumptions"))
                   + [c.get("assumptions") for c in all_claims
                      if isinstance(c, dict) and c.get("assumptions")])
    # flatten nested assumption lists
    flat_assumptions = []
    for a in assumptions:
        if isinstance(a, list):
            flat_assumptions.extend(a)
        elif isinstance(a, str):
            flat_assumptions.append(a)

    return {
        "topic_id": spec["topic_id"],
        "resolution": spec["resolution"],
        "definitions": definitions,
        "assumptions": flat_assumptions,
        "constructive_claims": constructive_claims,
        "adversarial_claims": adversarial_claims,
        "empirical_evidence": _claims_by_type(combined_for_typing, "empirical"),
        "normative_premises": _claims_by_type(combined_for_typing, "normative"),
        "theological_premises": _claims_by_type(combined_for_typing, "theological"),
        "objections": _as_list(cross_examination.get("objections")),
        "repairs": _as_list(repair.get("repairs")),
        "applied_case_results": _as_list(applied_cases.get("applied_case_results")),
        "domain_of_validity": _as_list(synthesis.get("domain_of_validity")),
        "unresolved_questions": _as_list(synthesis.get("unresolved_questions")),
        "verdict_status": _as_list(arbiter.get("verdicts")),
        "arbiter_reasoning": arbiter.get("arbiter_reasoning"),
        "recommended_follow_up": _as_list(arbiter.get("recommended_follow_up")),
    }


# ------------------------------- rendering ---------------------------------- #

def render_ledger_markdown(ledger: dict) -> str:
    """Human-readable rendering of a verdict ledger."""
    L = ledger
    lines = [
        f"# Verdict Ledger: {L.get('topic_id', '?')}",
        "",
        f"**Resolution:** {L.get('resolution', '?')}",
        "",
    ]
    defs = L.get("definitions") or []
    if defs:
        lines += ["## Definitions", ""]
        for d in defs:
            if isinstance(d, dict):
                tag = " _(contested)_" if d.get("contested") else ""
                lines += [f"**{d.get('term', '?')}**{tag}: {d.get('definition', '')}"]
        lines.append("")

    def _claim_block(title, claims):
        if not claims:
            return
        lines.extend(["## " + title, ""])
        for c in claims:
            if isinstance(c, dict):
                lines.extend([f"### {c.get('id', '?')} — {c.get('claim_type', '?')}",
                              c.get("claim", ""),
                              f"- **Scope:** {c.get('scope', '')}",
                              f"- **Uncertainty:** {c.get('uncertainty', '')}",
                              ""])

    _claim_block("Constructive Claims", L.get("constructive_claims"))
    _claim_block("Adversarial Claims", L.get("adversarial_claims"))

    verdicts = L.get("verdict_status") or []
    if verdicts:
        lines += ["## Arbiter Verdicts", ""]
        for v in verdicts:
            if isinstance(v, dict):
                lines += [f"- **{v.get('claim_id', '?')}**: "
                          f"{v.get('verdict', '?')} — {v.get('reasoning', '')}"]
        lines.append("")
    if L.get("arbiter_reasoning"):
        lines += ["## Arbiter Reasoning", "", L["arbiter_reasoning"], ""]
    if L.get("recommended_follow_up"):
        lines += ["## Recommended Follow-Up", ""]
        lines += [f"- {f}" for f in L["recommended_follow_up"]]
        lines.append("")
    if L.get("unresolved_questions"):
        lines += ["## Unresolved Questions", ""]
        lines += [f"- {q}" for q in L["unresolved_questions"]]
        lines.append("")
    prov = L.get("_provenance") or {}
    if prov:
        lines += ["---", "",
                  f"*Generated {prov.get('generated_at')} "
                  f"via arcana/scripts/debate_protocol.py "
                  f"(prompt {prov.get('prompt_version')}, "
                  f"model {prov.get('model')})*"]
    return "\n".join(lines)


# ------------------------------- CLI ---------------------------------------- #

def _make_logger(log_path: Path | None = None):
    def log(msg: str) -> None:
        stamp = dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        line = f"{stamp}  {msg}"
        print(line, flush=True)
        if log_path is not None:
            with log_path.open("a", encoding="utf-8") as f:
                f.write(line + "\n")
    return log


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--spec", required=True, metavar="PATH",
                   help="TopicSpec JSON file")
    p.add_argument("--endpoint", default=None,
                   help="endpoint name (default: first enabled)")
    p.add_argument("--model", default=None, help="override endpoint model")
    p.add_argument("--output-dir", default=None,
                   help="override output dir (default: outputs/<date>/<slug>/debate)")
    p.add_argument("--seed", type=int, default=None,
                   help="deterministic seed passed to Ollama options.seed")
    p.add_argument("--dry-run", action="store_true",
                   help="load spec + endpoint, print plan, exit before any Ollama call")
    args = p.parse_args(argv)

    spec = load_topic_spec(Path(args.spec))
    endpoint = gc.load_endpoint(args.endpoint)
    if args.model:
        endpoint = {**endpoint, "model": args.model}

    slug = slugify(spec["topic"])
    today = dt.datetime.now(dt.UTC).date().isoformat()
    out_dir = (Path(args.output_dir) if args.output_dir
               else OUTPUTS_ROOT / today / slug / "debate")

    if args.dry_run:
        print(f"spec: {args.spec}")
        print(f"topic_id: {spec['topic_id']}")
        print(f"topic: {spec['topic']}")
        print(f"endpoint: {endpoint['name']} ({endpoint['model']})")
        print(f"output_dir: {out_dir}")
        print(f"phases: {', '.join(PHASES)}")
        print(f"applied_cases: {len(spec['applied_cases'])}")
        return 0

    out_dir.mkdir(parents=True, exist_ok=True)
    log = _make_logger(out_dir / "debate.log")
    log(f"spec: {args.spec}")
    log(f"topic_id: {spec['topic_id']}")
    log(f"endpoint: {endpoint['name']} ({endpoint['model']})")
    log(f"output: {out_dir}")

    ledger = run_debate(spec, endpoint, log=log, output_dir=out_dir,
                        seed=args.seed, write_artifacts=True)

    md = render_ledger_markdown(ledger)
    (out_dir / "verdict_ledger.md").write_text(md, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
