"""Protocol-aware scoring for reasoning traces.

This module turns valid or partially valid reasoning traces into
comparable scorecards. The first scorer is intentionally focused on
the built-in StructuredToolUse protocol so HUMMBL can benchmark:

- pre-tool reasoning quality
- tool discriminativeness
- evidence integration
- recovery behavior
- final artifact quality
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from hummbl.protocols import StructuredToolUse
from hummbl.reasoning import ReasoningStep, ReasoningTrace, StepType


@dataclass
class DimensionScore:
    """One rubric dimension for a scored trace."""

    name: str
    score: int
    max_score: int = 2
    rationale: str = ""
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the dimension score."""
        return {
            "name": self.name,
            "score": self.score,
            "max_score": self.max_score,
            "rationale": self.rationale,
            "evidence": self.evidence,
        }


@dataclass
class TraceScore:
    """Scorecard for one reasoning trace."""

    trace_id: str
    protocol_name: str
    dimensions: dict[str, DimensionScore]
    total_score: int
    max_score: int
    normalized_score: float
    protocol_violations: list[str] = field(default_factory=list)
    outcome: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the full scorecard."""
        return {
            "trace_id": self.trace_id,
            "protocol_name": self.protocol_name,
            "dimensions": {
                name: dimension.to_dict()
                for name, dimension in self.dimensions.items()
            },
            "total_score": self.total_score,
            "max_score": self.max_score,
            "normalized_score": self.normalized_score,
            "protocol_violations": self.protocol_violations,
            "outcome": self.outcome,
            "tags": self.tags,
            "notes": self.notes,
        }


@dataclass
class ToolUseEpisode:
    """One tool-use cycle within a structured tool-use trace."""

    index: int
    context_observation: Optional[ReasoningStep]
    hypothesis: Optional[ReasoningStep]
    action: ReasoningStep
    tool_observation: Optional[ReasoningStep]
    evaluation: Optional[ReasoningStep]
    decision: Optional[ReasoningStep]


class StructuredToolUseScorer:
    """Scores traces against the StructuredToolUse rubric."""

    _GENERIC_SIGNALS = {
        "Additional evidence from the selected tool call.",
        "Evidence that reduces uncertainty.",
    }

    def __init__(self, protocol: Optional[StructuredToolUse] = None):
        self.protocol = protocol or StructuredToolUse()

    def score_trace(self, trace: ReasoningTrace) -> TraceScore:
        """Score a single trace against the structured tool-use rubric."""
        episodes = self._build_episodes(trace)
        violations = self.protocol.validate_trace(trace)

        dimensions = {
            "pre_tool_reasoning": self._score_pre_tool_reasoning(episodes),
            "tool_discriminativeness": self._score_tool_discriminativeness(
                episodes
            ),
            "evidence_integration": self._score_evidence_integration(episodes),
            "recovery_behavior": self._score_recovery_behavior(episodes),
            "final_artifact_quality": self._score_final_artifact_quality(
                trace, episodes
            ),
        }

        total_score = sum(dimension.score for dimension in dimensions.values())
        max_score = sum(dimension.max_score for dimension in dimensions.values())
        notes: list[str] = []

        if violations:
            notes.append("Protocol violations lower confidence in the score.")
        if not any(step.confidence is not None for step in trace.steps):
            notes.append(
                "Trace does not encode explicit step-level confidence yet."
            )

        return TraceScore(
            trace_id=trace.id,
            protocol_name=self.protocol.name,
            dimensions=dimensions,
            total_score=total_score,
            max_score=max_score,
            normalized_score=(total_score / max_score) if max_score else 0.0,
            protocol_violations=violations,
            outcome=trace.outcome,
            tags=list(trace.tags),
            notes=notes,
        )

    def score_traces(self, traces: list[ReasoningTrace]) -> list[TraceScore]:
        """Score a batch of traces."""
        return [self.score_trace(trace) for trace in traces]

    def summary(self, scores: list[TraceScore]) -> dict[str, Any]:
        """Aggregate summary statistics across many trace scorecards."""
        total = len(scores)
        if total == 0:
            return {"total": 0}

        max_total_score = scores[0].max_score if scores else 0
        dimension_names = list(scores[0].dimensions.keys())
        dimension_averages = {
            name: sum(score.dimensions[name].score for score in scores) / total
            for name in dimension_names
        }

        protocol_conformant = sum(
            1 for score in scores if not score.protocol_violations
        )
        finalized = sum(1 for score in scores if score.outcome == "finalize")
        recoveries = sum(
            1
            for score in scores
            if score.dimensions["recovery_behavior"].evidence.get(
                "recovery_triggers", 0
            )
            > 0
        )

        return {
            "total": total,
            "average_total_score": (
                sum(score.total_score for score in scores) / total
            ),
            "average_normalized_score": (
                sum(score.normalized_score for score in scores) / total
            ),
            "max_total_score": max_total_score,
            "dimension_averages": dimension_averages,
            "protocol_conformance_rate": protocol_conformant / total,
            "finalization_rate": finalized / total,
            "recovery_trigger_rate": recoveries / total,
        }

    def _build_episodes(self, trace: ReasoningTrace) -> list[ToolUseEpisode]:
        episodes: list[ToolUseEpisode] = []
        for index, action in enumerate(trace.get_steps_by_type(StepType.ACTION)):
            hypothesis = self._find_ancestor_of_type(
                trace, action, StepType.HYPOTHESIS
            )
            context_observation = (
                self._find_ancestor_of_type(trace, hypothesis, StepType.OBSERVATION)
                if hypothesis is not None
                else self._find_ancestor_of_type(trace, action, StepType.OBSERVATION)
            )
            tool_observation = self._find_direct_child_of_type(
                trace, action, StepType.OBSERVATION
            )
            evaluation = (
                self._find_direct_child_of_type(
                    trace, tool_observation, StepType.EVALUATION
                )
                if tool_observation is not None
                else None
            )
            decision = (
                self._find_direct_child_of_type(
                    trace, evaluation, StepType.DECISION
                )
                if evaluation is not None
                else None
            )
            episodes.append(
                ToolUseEpisode(
                    index=index,
                    context_observation=context_observation,
                    hypothesis=hypothesis,
                    action=action,
                    tool_observation=tool_observation,
                    evaluation=evaluation,
                    decision=decision,
                )
            )
        return episodes

    def _score_pre_tool_reasoning(
        self, episodes: list[ToolUseEpisode]
    ) -> DimensionScore:
        if not episodes:
            return DimensionScore(
                name="pre_tool_reasoning",
                score=0,
                rationale="No tool-use episodes were available to score.",
            )

        item_scores = []
        complete = 0
        partial = 0

        for episode in episodes:
            knowns = self._has_value(
                episode.context_observation, "knowns"
            )
            unknowns = self._has_value(
                episode.context_observation, "unknowns"
            )
            candidate = self._has_value(episode.hypothesis, "candidate")
            tool_name = self._has_value(episode.action, "tool_name")
            why_now = self._has_value(episode.action, "why_now")
            expected_signal = self._has_value(
                episode.action, "expected_signal"
            )

            if all(
                [knowns, unknowns, candidate, tool_name, why_now, expected_signal]
            ):
                score = 2
                complete += 1
            elif tool_name and any([knowns, unknowns, candidate, why_now, expected_signal]):
                score = 1
                partial += 1
            else:
                score = 0
            item_scores.append(score)

        final_score = self._collapse_scores(item_scores)
        return DimensionScore(
            name="pre_tool_reasoning",
            score=final_score,
            rationale=(
                f"{complete}/{len(episodes)} tool calls included explicit knowns, "
                "unknowns, hypothesis, and tool intent."
            ),
            evidence={
                "episodes": len(episodes),
                "complete_calls": complete,
                "partial_calls": partial,
            },
        )

    def _score_tool_discriminativeness(
        self, episodes: list[ToolUseEpisode]
    ) -> DimensionScore:
        if not episodes:
            return DimensionScore(
                name="tool_discriminativeness",
                score=0,
                rationale="No tool-use episodes were available to score.",
            )

        item_scores = []
        strong = 0
        partial = 0

        for episode in episodes:
            tool_name = str(episode.action.metadata.get("tool_name", "")).strip()
            why_now = str(episode.action.metadata.get("why_now", "")).strip()
            expected_signal = str(
                episode.action.metadata.get("expected_signal", "")
            ).strip()
            arguments = episode.action.metadata.get("arguments", {})
            if not isinstance(arguments, dict):
                arguments = {}
            information_target = ""
            if episode.hypothesis is not None:
                information_target = str(
                    episode.hypothesis.metadata.get("information_target", "")
                ).strip()

            specificity = 0
            if tool_name and tool_name != "unknown":
                specificity += 1
            if arguments:
                specificity += 1
            if information_target and information_target.lower() != tool_name.lower():
                specificity += 1
            if expected_signal and expected_signal not in self._GENERIC_SIGNALS:
                specificity += 1
            if why_now and len(why_now) >= 24:
                specificity += 1

            if specificity >= 4:
                score = 2
                strong += 1
            elif specificity >= 2:
                score = 1
                partial += 1
            else:
                score = 0
            item_scores.append(score)

        final_score = self._collapse_scores(item_scores)
        return DimensionScore(
            name="tool_discriminativeness",
            score=final_score,
            rationale=(
                f"{strong}/{len(episodes)} tool calls were strongly targeted "
                "at a specific uncertainty."
            ),
            evidence={
                "episodes": len(episodes),
                "strong_calls": strong,
                "partial_calls": partial,
            },
        )

    def _score_evidence_integration(
        self, episodes: list[ToolUseEpisode]
    ) -> DimensionScore:
        if not episodes:
            return DimensionScore(
                name="evidence_integration",
                score=0,
                rationale="No tool-use episodes were available to score.",
            )

        item_scores = []
        strong = 0
        partial = 0

        for episode in episodes:
            result_summary = self._string_value(
                episode.tool_observation, "result_summary"
            )
            supports = self._normalize_support(episode.evaluation)
            next_status = self._string_value(episode.evaluation, "next_status")
            has_decision = episode.decision is not None

            if result_summary and supports in {"yes", "no"} and next_status and has_decision:
                score = 2
                strong += 1
            elif result_summary and episode.evaluation is not None:
                score = 1
                partial += 1
            else:
                score = 0
            item_scores.append(score)

        final_score = self._collapse_scores(item_scores)
        return DimensionScore(
            name="evidence_integration",
            score=final_score,
            rationale=(
                f"{strong}/{len(episodes)} tool results were explicitly tied "
                "back to a belief update and decision."
            ),
            evidence={
                "episodes": len(episodes),
                "strong_integrations": strong,
                "partial_integrations": partial,
            },
        )

    def _score_recovery_behavior(
        self, episodes: list[ToolUseEpisode]
    ) -> DimensionScore:
        if not episodes:
            return DimensionScore(
                name="recovery_behavior",
                score=0,
                rationale="No tool-use episodes were available to score.",
            )

        triggers = []
        coherent_recoveries = 0
        weak_recoveries = 0

        for index, episode in enumerate(episodes):
            supports = self._normalize_support(episode.evaluation)
            status = self._string_value(episode.decision, "status")
            triggered = supports in {"no", "unclear"} or status == "recover"
            if not triggered:
                continue

            triggers.append(index)
            has_follow_up_action = index < len(episodes) - 1

            if status == "recover" and has_follow_up_action:
                coherent_recoveries += 1
            elif has_follow_up_action or status in {"continue", "unfinished", "recover"}:
                weak_recoveries += 1

        if not triggers:
            has_any_evaluation = any(episode.evaluation is not None for episode in episodes)
            score = 2 if has_any_evaluation else 1
            rationale = (
                "No contradictory or ambiguous tool result required recovery."
                if has_any_evaluation
                else "No recovery trigger was captured, but post-tool evaluation is thin."
            )
        elif coherent_recoveries == len(triggers):
            score = 2
            rationale = (
                f"Recovered coherently after all {len(triggers)} contradictory "
                "or ambiguous tool results."
            )
        elif coherent_recoveries or weak_recoveries:
            score = 1
            rationale = (
                f"Recovery was attempted after {len(triggers)} trigger(s), but "
                "follow-through was incomplete."
            )
        else:
            score = 0
            rationale = (
                f"{len(triggers)} contradictory or ambiguous result(s) were "
                "captured without coherent recovery."
            )

        return DimensionScore(
            name="recovery_behavior",
            score=score,
            rationale=rationale,
            evidence={
                "episodes": len(episodes),
                "recovery_triggers": len(triggers),
                "coherent_recoveries": coherent_recoveries,
                "weak_recoveries": weak_recoveries,
            },
        )

    def _score_final_artifact_quality(
        self,
        trace: ReasoningTrace,
        episodes: list[ToolUseEpisode],
    ) -> DimensionScore:
        final_decision = None
        decisions = trace.get_steps_by_type(StepType.DECISION)
        if decisions:
            final_decision = decisions[-1]

        if final_decision is None:
            return DimensionScore(
                name="final_artifact_quality",
                score=0,
                rationale="Trace does not end in an explicit decision artifact.",
            )

        status = str(final_decision.metadata.get("status", "")).strip()
        final_answer = str(
            final_decision.metadata.get("final_answer", "")
        ).strip()
        evidence_count = sum(
            1
            for episode in episodes
            if self._string_value(episode.tool_observation, "result_summary")
        )
        supported_finalization = any(
            episode.decision is not None
            and episode.decision.id == final_decision.id
            and self._normalize_support(episode.evaluation) in {"yes", "no", "unclear"}
            for episode in episodes
        )

        if status == "finalize" and final_answer and evidence_count > 0 and supported_finalization:
            score = 2
            rationale = "Final decision includes an answer and an evidence-backed evaluation chain."
        elif status == "finalize" and final_answer:
            score = 1
            rationale = "Final answer exists, but the supporting evidence chain is thin."
        else:
            score = 0
            rationale = "Trace does not end in a usable finalized answer."

        return DimensionScore(
            name="final_artifact_quality",
            score=score,
            rationale=rationale,
            evidence={
                "status": status,
                "final_answer_present": bool(final_answer),
                "supporting_tool_results": evidence_count,
            },
        )

    @staticmethod
    def _collapse_scores(item_scores: list[int]) -> int:
        """Collapse per-episode scores into a single 0-2 rubric score."""
        if not item_scores:
            return 0
        average = sum(item_scores) / len(item_scores)
        if average >= 1.5:
            return 2
        if average >= 0.5:
            return 1
        return 0

    @staticmethod
    def _find_ancestor_of_type(
        trace: ReasoningTrace,
        step: Optional[ReasoningStep],
        step_type: StepType,
    ) -> Optional[ReasoningStep]:
        current = step
        while current is not None and current.parent_id is not None:
            parent = trace.get_step(current.parent_id)
            if parent.type == step_type:
                return parent
            current = parent
        return None

    @staticmethod
    def _find_direct_child_of_type(
        trace: ReasoningTrace,
        step: Optional[ReasoningStep],
        step_type: StepType,
    ) -> Optional[ReasoningStep]:
        if step is None:
            return None
        for child_id in step.children_ids:
            child = trace.get_step(child_id)
            if child.type == step_type:
                return child
        return None

    @staticmethod
    def _has_value(step: Optional[ReasoningStep], key: str) -> bool:
        if step is None:
            return False
        value = step.metadata.get(key)
        if value is None:
            return False
        if isinstance(value, str):
            return bool(value.strip())
        if isinstance(value, (list, dict, tuple, set)):
            return bool(value)
        return True

    @staticmethod
    def _string_value(step: Optional[ReasoningStep], key: str) -> str:
        if step is None:
            return ""
        value = step.metadata.get(key, "")
        return str(value).strip()

    def _normalize_support(self, step: Optional[ReasoningStep]) -> str:
        value = self._string_value(step, "supports_hypothesis").lower()
        if value in {"true", "yes", "supported"}:
            return "yes"
        if value in {"false", "no", "contradicted"}:
            return "no"
        if value == "unclear":
            return "unclear"
        return value
