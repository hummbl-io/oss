"""SYNTHESIS runtime -- cross-module workflow orchestration.

First executable workflow: ``paideia-review``.

    article.md + plan.json
      -> PAIDEIA score (score_paideia)
      -> target vs actual per-axis gap (overnight_v0 plan load + inline delta)
      -> root-cause attribution (gap_analysis.attribute_root_cause)
      -> prompt edit proposal (prompt_refiner.propose_edits / render_proposal)
      -> SYNTHESIS receipt bundle (JSON) + Markdown summary

This is a *different* workflow from the release gate in ``RELEASE/gate.py``
(which composes article -> PAIDEIA -> LINGUA -> NOMOS -> EVIDENCE -> RELEASE).
SYNTHESIS debuts here as the cross-module workflow entry point; the
paideia-review workflow is the first of potentially several. It composes
existing runnable sibling functions and does not duplicate the release-gate
chain.

Single-article in v0.1 of this runtime. Root-cause attribution
(gap_analysis.attribute_root_cause) with sample_size=1 still proposes
prompt edits for axes where target>=3 and actual<=1.5 (the prompt_weakness
branch fires before the sample-size guard, confidence 0.55); axes with
other gap patterns return "insufficient_data" and no edit. Batch mode
(multiple articles sharing one plan, raising confidence and sample size)
is a later PR in this arc.

Pure stdlib. No Ollama. use_llm=False on the PAIDEIA score.
"""
from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
for path in (ROOT, SCRIPTS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import ecosystem_contracts as ec  # noqa: E402
import gap_analysis as ga  # noqa: E402
import overnight_v0 as ov  # noqa: E402
import prompt_refiner as pr  # noqa: E402
import score_paideia as paideia  # noqa: E402

SCHEMA_VERSION = "synthesis-paideia-review-v0.1"
WORKFLOW_NAME = "paideia-review"
DEFAULT_PROMPT = SCRIPTS / "prompts" / "paideia_plan_v2.txt"


def now_utc_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def artifact_receipt(path: Path, text: str) -> dict[str, object]:
    data = text.encode("utf-8")
    return {
        "path": str(path),
        "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data),
        "lines": text.count("\n") + (0 if text.endswith("\n") else 1),
    }


def _axis_gaps(target: dict, actual: dict) -> list[dict[str, object]]:
    """Per-axis target-vs-actual gap with root-cause attribution.

    Only axes present in BOTH target and actual are compared (v0.1 plans
    loaded via overnight_v0.load_paideia_plan have Em filled to 0, so all 10
    axes are comparable for v0.2 scores).
    """
    out: list[dict[str, object]] = []
    for axis in ec.PAIDEIA_AXES:
        t = target.get(axis)
        a = actual.get(axis)
        if t is None or a is None:
            continue
        gap = float(t) - float(a)
        cause, fix, conf = ga.attribute_root_cause(
            axis, gap, sample_size=1,
            plan_targets=[float(t)], actual_scores=[float(a)],
        )
        out.append({
            "axis": axis,
            "axis_name": ec.PAIDEIA_AXIS_NAMES[axis],
            "target": t,
            "actual": a,
            "gap": gap,
            # mean_gap over a single sample == the gap itself; prompt_refiner
            # .propose_edits reads "mean_gap", so emit it for compatibility.
            "mean_gap": gap,
            "root_cause": cause,
            "proposed_fix": fix,
            "confidence": round(conf, 2),
        })
    return out


def build_paideia_review_bundle(
    article_path: Path,
    plan_path: Path,
    *,
    prompt_path: Path | None = None,
    instructional_intent: bool = True,
) -> dict[str, object]:
    """Run the paideia-review workflow and return a receipt bundle."""
    if not article_path.exists():
        raise FileNotFoundError(article_path)
    if not plan_path.exists():
        raise FileNotFoundError(plan_path)
    text = article_path.read_text(encoding="utf-8")
    article = artifact_receipt(article_path, text)

    plan = ov.load_paideia_plan(plan_path)  # version-aware (fills Em for v0.1)
    target = plan["target_vector"]
    plan_receipt = {
        "path": str(plan_path),
        "paideia_version": plan.get("prompt_version", "unknown"),
        "target_vector": target,
        "instructional_intent": plan.get("instructional_intent", True),
    }

    score = paideia.score_content(
        text, instructional_intent=instructional_intent, use_llm=False)

    axis_gaps = _axis_gaps(target, score["vector"])
    gap_report = {"axis_gaps": axis_gaps}
    edits = pr.propose_edits(gap_report)
    proposal_md = pr.render_proposal(edits, None, dry_run=True)

    prompt_used = prompt_path or DEFAULT_PROMPT
    return {
        "schema_version": SCHEMA_VERSION,
        "workflow": WORKFLOW_NAME,
        "generated_at": now_utc_iso(),
        "inputs": {
            "article": article,
            "plan": plan_receipt,
            "prompt": str(prompt_used),
        },
        "paideia_score": {
            "signature": score["signature"],
            "prompt_version": score["prompt_version"],
            "vector": score["vector"],
            "comparable_vector": score["comparable_vector"],
            "hard_axes_status": score["hard_axes_status"],
        },
        "gaps": {
            "axis_gaps": axis_gaps,
            "axes_underperforming": [
                g["axis"] for g in axis_gaps if g["gap"] > 0],
            "axes_exceeding": [
                g["axis"] for g in axis_gaps if g["gap"] < 0],
        },
        "edits": [dataclasses.asdict(e) for e in edits],
        "proposal_markdown": proposal_md,
    }


def render_summary(bundle: dict[str, object]) -> str:
    article = bundle["inputs"]["article"]
    plan = bundle["inputs"]["plan"]
    score = bundle["paideia_score"]
    gaps = bundle["gaps"]
    lines = [
        "# SYNTHESIS Paideia-Review Summary",
        "",
        f"- Workflow: `{bundle['workflow']}`",
        f"- Schema: `{bundle['schema_version']}`",
        f"- Generated: `{bundle['generated_at']}`",
        f"- Article: `{article['path']}` (sha256 `{article['sha256'][:12]}...`)",
        f"- Plan: `{plan['path']}` (paideia `{plan['paideia_version']}`)",
        f"- PAIDEIA signature: `{score['signature']}`",
        f"- PAIDEIA version: `{score['prompt_version']}`",
        f"- Comparable vector: `{str(score['comparable_vector']).lower()}`",
        f"- Hard axes status: `{score['hard_axes_status']}`",
        f"- Axes underperforming: `{', '.join(gaps['axes_underperforming']) or '(none)'}`",
        f"- Axes exceeding: `{', '.join(gaps['axes_exceeding']) or '(none)'}`",
        f"- Prompt edits proposed: `{len(bundle['edits'])}`",
    ]
    if bundle["edits"]:
        lines.extend(["", "## Proposed prompt edits", ""])
        for e in bundle["edits"]:
            lines.append(f"- **{e['axis']}** ({e['confidence']:.2f}): {e['rationale']}")
    else:
        lines.extend(["",
                      "No prompt edits proposed. Single-article attribution "
                      "returns 'insufficient_data' (confidence < 0.5); batch "
                      "mode (>=2 scored articles sharing one plan) is needed "
                      "for confident root-cause attribution."])
    return "\n".join(lines).strip() + "\n"


def write_outputs(bundle: dict[str, object], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "synthesis_paideia_review.json"
    md_path = output_dir / "synthesis_paideia_review.md"
    json_path.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n",
                         encoding="utf-8")
    md_path.write_text(render_summary(bundle), encoding="utf-8")
    return json_path, md_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--article", required=True,
                        help="article markdown/text artifact to review")
    parser.add_argument("--plan", required=True,
                        help="PAIDEIA plan JSON (target_vector) for the article's topic")
    parser.add_argument("--prompt", default=None,
                        help="prompt file the plan was generated against (default: paideia_plan_v2.txt)")
    parser.add_argument("--output-dir", default=None,
                        help="write JSON and Markdown receipts to this directory")
    parser.add_argument("--instructional-intent", type=lambda s: s.lower() != "false",
                        default=True)
    args = parser.parse_args(argv)

    bundle = build_paideia_review_bundle(
        Path(args.article), Path(args.plan),
        prompt_path=Path(args.prompt) if args.prompt else None,
        instructional_intent=args.instructional_intent,
    )
    if args.output_dir:
        json_path, md_path = write_outputs(bundle, Path(args.output_dir))
        print(f"wrote {json_path}")
        print(f"wrote {md_path}")
    else:
        print(json.dumps(bundle, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
