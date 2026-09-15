"""Propose prompt version bumps from gap_analysis output.

Reads gap report (JSON), looks up current prompt version, proposes edits,
and writes a trial prompt file. Does NOT overwrite the canonical prompt.

Pure stdlib. No Ollama.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ecosystem_contracts as ec

HERE = Path(__file__).resolve().parent
PROMPTS_DIR = HERE / "prompts"
PAIDEIA_PLAN_PROMPT = PROMPTS_DIR / "paideia_plan_v1.txt"


@dataclass
class PromptEdit:
    axis: str
    original_snippet: str
    proposed_snippet: str
    rationale: str
    confidence: float


# ---- Edit library: axis → (regex pattern, replacement template) -----------

EDIT_PATTERNS = {
    "M": (
        r"(M MODALITY: representational channels \(verbal, visual, symbolic, embodied, auditory\)\..*?Mayer 2009; Paivio 1986\.)",
        r"\1 NOTE: The plan MUST include at least one non-verbal channel (visual diagram, code block, or audio cue) to score M≥2."
    ),
    "D": (
        r"(D DEPTH: intellectual operation demanded, scored via SOLO structure\. Biggs and Collis 1982\.)",
        r"\1 NOTE: Target SOLO level must be explicitly named (unistructural/multistructural/relational/extended_abstract). Content scoring below target indicates insufficient cognitive demand."
    ),
    "E": (
        r"(E ENGAGEMENT: overt learner activity mode \(Passive 0 / Active 1 / Constructive 2-3 / Interactive 4\)\. Chi and Wylie 2014\.)",
        r"\1 NOTE: Constructive activities (write, design, build, justify) MUST be explicitly called out in the content outline to score E≥2."
    ),
    "V": (
        r"(V MOTIVATION: autonomy, competence, relatedness afforded\. Ryan and Deci 2000\.)",
        r"\1 NOTE: Include at least one choice-point or self-directed exploration task to satisfy autonomy. Mastery progression must be visible to satisfy competence."
    ),
    "C": (
        r"(C METACOGNITION: prompts for planning, monitoring, reflection\. Flavell 1979; Zimmerman 2000\.)",
        r"\1 NOTE: Embed 2+ explicit self-monitoring prompts (e.g., 'Predict before reading', 'Check your understanding', 'What would you do differently?')."
    ),
    "L": (
        r"(L LOAD: extraneous vs germane load vs learner expertise\. Sweller 2011; Kalyuga 2007\.)",
        r"\1 NOTE: Justify load_budget choice with learner expertise. Novice → low extraneous; expert → higher intrinsic acceptable."
    ),
    "S": (
        r"(S SCAFFOLD: novice to expert fade schedule\. Dreyfus 1980; Vygotsky 1978\.)",
        r"\1 NOTE: Scaffold must be explicit: state what support is provided initially and when it is removed. Fade schedule must be traceable in the content structure."
    ),
    "P": (
        r"(P PRACTICE: retrieval, spacing, interleaving, feedback\. Roediger and Karpicke 2006\.)",
        r"\1 NOTE: Include at least one retrieval exercise with an answer key or feedback mechanism. Space practice across at least two content sections."
    ),
    "A": (
        r"(A AUTHENTICITY: situated, whole-task realism\. Brown et al\. 1989\.)",
        r"\1 NOTE: Anchor content to a realistic scenario, case study, or production context. Abstract-only treatments score A≤1."
    ),
    "Em": (
        r"(Em EMOTION: affective intensity as a vehicle for content\..*?Tyng, Amin, Saad and Malik 2017\.)",
        r"\1 NOTE: For technical reference content target Em 0-1 with intent deliberate_absent; for persuasive or narrative content where affect is load-bearing, target Em≥3 with intent required. Valence is descriptive, not scored."
    ),
}


def load_gap_report(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def compute_prompt_version(current_path: Path) -> str:
    """Parse vN from filename and return v(N+1)."""
    name = current_path.name
    m = re.search(r"_v(\d+)\.txt$", name)
    if not m:
        return "v2"
    return f"v{int(m.group(1)) + 1}"


def propose_edits(gap_report: dict) -> list[PromptEdit]:
    edits: list[PromptEdit] = []
    axis_results = gap_report.get("axis_gaps", [])
    prompt_text = PAIDEIA_PLAN_PROMPT.read_text(encoding="utf-8")

    for result in axis_results:
        axis = result["axis"]
        mean_gap = result["mean_gap"]
        confidence = result["confidence"]

        # Only propose edits for gaps we can actually fix with prompt changes
        if result["root_cause"] not in ("prompt_weakness", "detector_limitation"):
            continue
        if abs(mean_gap) < 0.5:
            continue

        pattern, replacement = EDIT_PATTERNS.get(axis, (None, None))
        if pattern is None:
            continue

        match = re.search(pattern, prompt_text)
        if not match:
            continue

        original = match.group(0)
        proposed = re.sub(pattern, replacement, original)

        edits.append(PromptEdit(
            axis=axis,
            original_snippet=original[:120] + ("..." if len(original) > 120 else ""),
            proposed_snippet=proposed[:120] + ("..." if len(proposed) > 120 else ""),
            rationale=(
                f"Mean gap {mean_gap:.1f} on {axis} ({ec.PAIDEIA_AXIS_NAMES[axis]}). "
                f"Root cause: {result['root_cause']}. "
                f"Adding explicit constraint to prompt should raise scores."
            ),
            confidence=confidence,
        ))

    return edits


def generate_trial_prompt(
    current_path: Path,
    edits: list[PromptEdit],
    dry_run: bool = True,
) -> Path | None:
    """Write a trial prompt file with proposed edits applied."""
    prompt_text = current_path.read_text(encoding="utf-8")
    new_version = compute_prompt_version(current_path)
    new_name = re.sub(r"_v\d+\.txt$", f"_{new_version}.txt", current_path.name)
    trial_path = PROMPTS_DIR / new_name

    applied = 0
    for edit in edits:
        pattern, replacement = EDIT_PATTERNS.get(edit.axis, (None, None))
        if pattern is None:
            continue
        new_text, count = re.subn(pattern, replacement, prompt_text, count=1)
        if count:
            prompt_text = new_text
            applied += 1

    if applied == 0:
        return None

    if not dry_run:
        trial_path.write_text(prompt_text, encoding="utf-8")
        print(f"wrote trial prompt: {trial_path}", file=sys.stderr)
    return trial_path


def render_proposal(edits: list[PromptEdit], trial_path: Path | None, dry_run: bool) -> str:
    lines = ["# Prompt Refinement Proposal", ""]
    lines.append(f"- **Trial prompt:** {trial_path or '(none generated — no applicable edits)'}")
    lines.append(f"- **Dry run:** {dry_run}")
    lines.append(f"- **Edits proposed:** {len(edits)}")
    lines.append("")

    for i, edit in enumerate(edits, 1):
        lines.append(f"## Edit {i}: {edit.axis} — {ec.PAIDEIA_AXIS_NAMES[edit.axis]}")
        lines.append(f"- **Confidence:** {edit.confidence}")
        lines.append(f"- **Original:** {edit.original_snippet}")
        lines.append(f"- **Proposed:** {edit.proposed_snippet}")
        lines.append(f"- **Rationale:** {edit.rationale}")
        lines.append("")

    if trial_path and not dry_run:
        lines.append("## Next Steps")
        lines.append(f"1. Backtest new prompt on last 5 topics: `python generate_paideia_plan.py --prompt-version {trial_path.name}`")
        lines.append("2. Compare PAIDEIA signatures to baseline")
        lines.append("3. If mean gap closes by ≥ 0.3, promote to canonical")
        lines.append("")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--gap-report", type=Path, required=True,
                   help="JSON output from gap_analysis.py")
    p.add_argument("--prompt", type=Path, default=PAIDEIA_PLAN_PROMPT)
    p.add_argument("--dry-run", action="store_true", default=True,
                   help="preview edits without writing trial prompt (default)")
    p.add_argument("--apply", action="store_true",
                   help="write the trial prompt file (overrides --dry-run)")
    p.add_argument("--output", type=Path, default=None)
    args = p.parse_args(argv)

    dry_run = not args.apply
    gap_report = load_gap_report(args.gap_report)
    edits = propose_edits(gap_report)
    trial_path = generate_trial_prompt(args.prompt, edits, dry_run=dry_run)

    report = render_proposal(edits, trial_path, dry_run)

    if args.output:
        args.output.write_text(report + "\n", encoding="utf-8")
        print(f"wrote refinement proposal to {args.output}", file=sys.stderr)
    else:
        print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
