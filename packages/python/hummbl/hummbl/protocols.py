"""Domain-specific reasoning protocols.

A protocol defines a structured reasoning pattern: what step types
are required, in what order, and what transitions are valid. Protocols
are composable — a complex reasoning process can chain multiple protocols
together.

The key insight: the autoresearch experiment loop IS a reasoning protocol.
So is code review. HUMMBL makes these patterns explicit, inspectable,
and reusable.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

from hummbl.reasoning import (
    ReasoningTopology,
    ReasoningTrace,
    StepType,
    make_trace,
)


@dataclass
class StepSpec:
    """Specification for a required step in a protocol.

    Attributes:
        type: The cognitive role this step must fill.
        name: Human-readable name for this position in the protocol.
        description: What the agent should do at this step.
        required: Whether the protocol enforces this step.
        metadata_keys: Domain-specific metadata keys expected at this step.
    """

    type: StepType
    name: str
    description: str = ""
    required: bool = True
    metadata_keys: list[str] = field(default_factory=list)


@dataclass
class ReasoningProtocol:
    """Defines a structured reasoning pattern for a specific domain.

    A protocol is a template: it specifies the step types, their order,
    and the valid transitions. It does not execute reasoning — it
    constrains and guides it.

    Attributes:
        name: Protocol identifier.
        description: What this protocol is for.
        step_specs: Ordered list of step specifications.
        topology: The default topology for traces following this protocol.
        domain: The reasoning domain this protocol belongs to.
    """

    name: str
    description: str
    step_specs: list[StepSpec]
    topology: ReasoningTopology = ReasoningTopology.CHAIN
    domain: str = ""

    def create_trace(self, tags: Optional[list[str]] = None) -> ReasoningTrace:
        """Create an empty trace bound to this protocol's domain and topology."""
        return make_trace(
            domain=self.domain or self.name,
            topology=self.topology,
            tags=tags or [],
        )

    def validate_trace(self, trace: ReasoningTrace) -> list[str]:
        """Check whether a trace follows this protocol.

        Returns a list of violations (empty = valid). Only checks
        required steps and their ordering — does not enforce strict
        sequential adjacency, allowing optional steps in between.
        """
        violations = []
        required_specs = [s for s in self.step_specs if s.required]

        # Check that all required step types appear in order
        spec_idx = 0
        for step in trace.steps:
            if spec_idx >= len(required_specs):
                break
            if step.type == required_specs[spec_idx].type:
                spec_idx += 1

        if spec_idx < len(required_specs):
            missing = [s.name for s in required_specs[spec_idx:]]
            violations.append(f"Missing required steps: {', '.join(missing)}")

        # Check metadata keys against the corresponding occurrence of each
        # step type in the protocol, rather than every step of that type.
        # This matters for protocols with repeated step types, e.g. two
        # ACTION steps where only the first requires a commit hash.
        steps_by_type = {step_type: trace.get_steps_by_type(step_type) for step_type in StepType}
        occurrence_by_type: dict[StepType, int] = defaultdict(int)

        for spec in self.step_specs:
            matching_steps = steps_by_type.get(spec.type, [])
            occurrence = occurrence_by_type[spec.type]

            if occurrence >= len(matching_steps):
                continue

            step = matching_steps[occurrence]
            occurrence_by_type[spec.type] += 1

            if not spec.metadata_keys:
                continue

            for key in spec.metadata_keys:
                if key not in step.metadata:
                    violations.append(
                        f"Step '{step.id}' ({spec.name}) missing metadata key '{key}'"
                    )

        return violations

    def describe(self) -> str:
        """Human-readable description of the protocol flow."""
        lines = [f"Protocol: {self.name}", f"  {self.description}", ""]
        for i, spec in enumerate(self.step_specs, 1):
            req = "*" if spec.required else " "
            lines.append(f"  {i}. [{req}] {spec.type.value}: {spec.name}")
            if spec.description:
                lines.append(f"       {spec.description}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Built-in protocols
# ---------------------------------------------------------------------------


class ScientificMethod(ReasoningProtocol):
    """The autoresearch experiment loop as a formal reasoning protocol.

    This is the protocol that the autoresearch pipeline follows:
    1. Form a hypothesis about what change will improve val_bpb
    2. Modify train.py (action)
    3. Run the experiment (action)
    4. Read the results (observation)
    5. Compare to baseline (evaluation)
    6. Keep or discard (decision)
    7. Update strategy for next iteration (reflection)

    This protocol uses CHAIN topology by default because each experiment
    is a linear sequence. The outer loop (many experiments) is captured
    as multiple traces, not as branching within a single trace.
    """

    def __init__(self):
        super().__init__(
            name="scientific_method",
            description=(
                "Hypothesis-driven experimentation loop. "
                "Form a hypothesis, intervene, observe, evaluate, decide."
            ),
            domain="autoresearch",
            topology=ReasoningTopology.CHAIN,
            step_specs=[
                StepSpec(
                    type=StepType.HYPOTHESIS,
                    name="hypothesis",
                    description=(
                        "What change do you expect to improve the metric? "
                        "State the prediction and the reasoning behind it."
                    ),
                    metadata_keys=["predicted_direction"],
                ),
                StepSpec(
                    type=StepType.ACTION,
                    name="modify_code",
                    description=("Modify train.py to implement the hypothesis."),
                    metadata_keys=["commit_hash"],
                ),
                StepSpec(
                    type=StepType.ACTION,
                    name="run_experiment",
                    description=("Run the training script and collect results."),
                ),
                StepSpec(
                    type=StepType.OBSERVATION,
                    name="read_results",
                    description=(
                        "Extract val_bpb, peak_vram_mb, and other metrics from the run log."
                    ),
                    metadata_keys=["val_bpb", "peak_vram_mb"],
                ),
                StepSpec(
                    type=StepType.EVALUATION,
                    name="compare_to_baseline",
                    description=(
                        "Compare this run's val_bpb to the current best. "
                        "Did it improve? By how much?"
                    ),
                    metadata_keys=["baseline_bpb", "delta_bpb"],
                ),
                StepSpec(
                    type=StepType.DECISION,
                    name="keep_or_discard",
                    description=(
                        "Keep the change (advance branch) or discard it "
                        "(git reset). Factor in simplicity criterion."
                    ),
                    metadata_keys=["status"],  # keep / discard / crash
                ),
                StepSpec(
                    type=StepType.REFLECTION,
                    name="update_strategy",
                    description=(
                        "What did this experiment teach you? How should it "
                        "influence the next hypothesis?"
                    ),
                    required=False,  # Not every experiment needs reflection
                ),
            ],
        )


class StructuredToolUse(ReasoningProtocol):
    """Structured reasoning protocol for tool-assisted inquiry.

    This protocol is designed for tasks where an agent must inspect a
    problem, identify uncertainty, choose a tool deliberately, interpret
    the tool result, and either recover or commit to an answer.

    It is intentionally generic so it can cover:
    - geolocation from images
    - code investigation with repository search tools
    - schema inspection and data analysis
    - operational diagnosis and verification

    The key invariant is that tool use must be justified before the call,
    and the result must be evaluated after the call.
    """

    def __init__(self):
        super().__init__(
            name="structured_tool_use",
            description=(
                "Tool-assisted inquiry with explicit pre-tool reasoning, "
                "post-tool evaluation, and recovery or decision."
            ),
            domain="tool_reasoning",
            topology=ReasoningTopology.CHAIN,
            step_specs=[
                StepSpec(
                    type=StepType.OBSERVATION,
                    name="frame_context",
                    description=(
                        "Describe what is directly observed, what evidence "
                        "is already available, and what remains uncertain."
                    ),
                    metadata_keys=["knowns", "unknowns"],
                ),
                StepSpec(
                    type=StepType.HYPOTHESIS,
                    name="working_hypothesis",
                    description=(
                        "State the current best explanation or candidate "
                        "answer and what evidence would confirm or reject it."
                    ),
                    metadata_keys=["candidate", "information_target"],
                ),
                StepSpec(
                    type=StepType.ACTION,
                    name="choose_tool",
                    description=(
                        "Choose the next tool or intervention and justify "
                        "why it is the best way to reduce uncertainty."
                    ),
                    metadata_keys=["tool_name", "why_now", "expected_signal"],
                ),
                StepSpec(
                    type=StepType.OBSERVATION,
                    name="inspect_tool_result",
                    description=(
                        "Record what the tool returned and extract the "
                        "signal relevant to the current hypothesis."
                    ),
                    metadata_keys=["tool_name", "result_summary"],
                ),
                StepSpec(
                    type=StepType.EVALUATION,
                    name="update_belief",
                    description=(
                        "Evaluate whether the tool result supports, weakens, "
                        "or contradicts the working hypothesis."
                    ),
                    metadata_keys=["supports_hypothesis", "next_status"],
                ),
                StepSpec(
                    type=StepType.DECISION,
                    name="recover_or_commit",
                    description=(
                        "Either recover with another targeted action or "
                        "commit to a final answer with explicit evidence."
                    ),
                    metadata_keys=["status"],  # continue / recover / finalize
                ),
                StepSpec(
                    type=StepType.REFLECTION,
                    name="capture_learning",
                    description=(
                        "Record what this run taught about tool choice, "
                        "failure modes, or reusable reasoning patterns."
                    ),
                    required=False,
                ),
            ],
        )


class HypothesisExploration(ReasoningProtocol):
    """Tree-structured hypothesis exploration.

    For problems where multiple competing hypotheses need to be
    evaluated in parallel before committing to one:
    1. Generate multiple hypotheses (branching)
    2. Evaluate each (parallel actions/observations)
    3. Prune unpromising branches
    4. Commit to the best path

    Uses TREE topology — the defining characteristic is branching
    at the hypothesis stage.
    """

    def __init__(self):
        super().__init__(
            name="hypothesis_exploration",
            description=(
                "Generate multiple hypotheses, evaluate in parallel, "
                "prune and commit. Tree-of-thought reasoning."
            ),
            domain="general",
            topology=ReasoningTopology.TREE,
            step_specs=[
                StepSpec(
                    type=StepType.OBSERVATION,
                    name="problem_statement",
                    description="Define the problem and available evidence.",
                ),
                StepSpec(
                    type=StepType.HYPOTHESIS,
                    name="generate_hypotheses",
                    description=(
                        "Generate multiple competing hypotheses. Each becomes a branch in the tree."
                    ),
                ),
                StepSpec(
                    type=StepType.EVALUATION,
                    name="evaluate_branches",
                    description=(
                        "Evaluate each hypothesis branch. Score by "
                        "plausibility, testability, and evidence fit."
                    ),
                ),
                StepSpec(
                    type=StepType.DECISION,
                    name="prune_and_commit",
                    description=(
                        "Prune low-scoring branches. Commit to the "
                        "most promising hypothesis for further action."
                    ),
                    metadata_keys=["selected_hypothesis", "pruned_count"],
                ),
            ],
        )
