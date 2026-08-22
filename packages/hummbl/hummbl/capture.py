"""Reasoning trace capture from autoresearch experiment data.

Converts the artifacts of an autoresearch run — results.tsv and
strategy notes — into structured HUMMBL reasoning traces. This is
the bridge between "an agent did stuff" and "we have an inspectable
record of how it reasoned."

This module demonstrates a core HUMMBL principle: reasoning traces
should be derivable from existing artifacts, not require agents to
use a special API during execution. Capture after the fact, then
use the traces for analysis and learning.
"""

from __future__ import annotations

import csv
import json
import logging
import re
from pathlib import Path
from typing import Any, Optional

from hummbl.reasoning import (
    ReasoningStep,
    ReasoningTopology,
    ReasoningTrace,
    StepType,
    make_step,
    make_trace,
)

logger = logging.getLogger(__name__)


class AutoresearchCapture:
    """Captures reasoning traces from autoresearch experiment loops.

    Each row in results.tsv represents one experiment cycle:
    hypothesis (description) -> action (code change via commit) ->
    observation (val_bpb, memory) -> decision (keep/discard/crash).

    The capture reconstructs these steps and links them into traces.
    """

    def capture_from_results_tsv(
        self, path: str | Path
    ) -> list[ReasoningTrace]:
        """Convert results.tsv history into structured reasoning traces.

        Each row becomes one trace with the following steps:
        1. HYPOTHESIS — inferred from the description column
        2. ACTION — the code change (commit hash as metadata)
        3. OBSERVATION — val_bpb and memory usage
        4. EVALUATION — comparison to the running best
        5. DECISION — keep, discard, or crash

        Args:
            path: Path to the results.tsv file.

        Returns:
            List of ReasoningTrace objects, one per experiment row.
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"results.tsv not found: {path}")

        traces: list[ReasoningTrace] = []
        best_bpb: Optional[float] = None

        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row_num, row in enumerate(reader):
                trace = self._row_to_trace(row, row_num, best_bpb)
                traces.append(trace)

                # Track the running best for evaluation context
                val_bpb = self._parse_float(row.get("val_bpb", "0"))
                status = row.get("status", "").strip()
                if status == "keep" and val_bpb > 0:
                    if best_bpb is None or val_bpb < best_bpb:
                        best_bpb = val_bpb

        return traces

    def _row_to_trace(
        self,
        row: dict,
        experiment_num: int,
        best_bpb: Optional[float],
    ) -> ReasoningTrace:
        """Convert a single results.tsv row into a reasoning trace."""
        commit = row.get("commit", "unknown").strip()
        val_bpb = self._parse_float(row.get("val_bpb", "0"))
        memory_gb = self._parse_float(row.get("memory_gb", "0"))
        status = row.get("status", "unknown").strip()
        description = row.get("description", "").strip()

        trace = make_trace(
            domain="autoresearch",
            topology=ReasoningTopology.CHAIN,
            tags=[f"experiment_{experiment_num}", status],
        )

        # Step 1: HYPOTHESIS — what did the researcher expect?
        hypothesis = make_step(
            StepType.HYPOTHESIS,
            content=f"Experiment {experiment_num}: {description}",
            metadata={"experiment_num": experiment_num},
        )
        trace.add_step(hypothesis)

        # Step 2: ACTION — the code change
        action = make_step(
            StepType.ACTION,
            content=f"Modified train.py and committed as {commit}",
            parent_id=hypothesis.id,
            metadata={"commit_hash": commit},
        )
        trace.add_step(action)

        # Step 3: OBSERVATION — what happened?
        if status == "crash":
            obs_content = f"Experiment crashed (commit {commit})"
        else:
            obs_content = (
                f"val_bpb={val_bpb:.6f}, peak_vram={memory_gb:.1f} GB"
            )
        observation = make_step(
            StepType.OBSERVATION,
            content=obs_content,
            parent_id=action.id,
            metadata={
                "val_bpb": val_bpb,
                "peak_vram_gb": memory_gb,
                "crashed": status == "crash",
            },
        )
        trace.add_step(observation)

        # Step 4: EVALUATION — how does it compare?
        if status == "crash":
            eval_content = "Cannot evaluate — experiment crashed"
            delta = None
        elif best_bpb is not None and val_bpb > 0:
            delta = val_bpb - best_bpb
            direction = "better" if delta < 0 else "worse"
            eval_content = (
                f"Delta from best: {delta:+.6f} ({direction}). "
                f"Best was {best_bpb:.6f}, this is {val_bpb:.6f}."
            )
        else:
            eval_content = (
                f"Baseline establishment: val_bpb={val_bpb:.6f}"
            )
            delta = None

        evaluation = make_step(
            StepType.EVALUATION,
            content=eval_content,
            parent_id=observation.id,
            metadata={
                "baseline_bpb": best_bpb,
                "delta_bpb": delta,
            },
        )
        trace.add_step(evaluation)

        # Step 5: DECISION — keep, discard, or crash
        decision = make_step(
            StepType.DECISION,
            content=f"Decision: {status}",
            parent_id=evaluation.id,
            metadata={"status": status},
        )
        trace.add_step(decision)

        trace.outcome = status
        return trace

    def capture_from_strategy_md(
        self, path: str | Path
    ) -> ReasoningTrace:
        """Extract meta-reasoning from strategy.md or program.md.

        Strategy documents contain reflection-level reasoning:
        what categories of experiments to try, what has been learned,
        what to prioritize. This captures that as a single REFLECTION
        trace.

        Args:
            path: Path to strategy.md or program.md.

        Returns:
            A single ReasoningTrace capturing the strategic reasoning.
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Strategy file not found: {path}")

        content = path.read_text(encoding="utf-8")
        trace = make_trace(
            domain="autoresearch",
            topology=ReasoningTopology.CHAIN,
            tags=["meta", "strategy"],
        )

        # Extract section headers as individual reflection steps
        sections = self._extract_sections(content)

        parent_id = None
        for heading, body in sections:
            step = make_step(
                StepType.REFLECTION,
                content=f"{heading}\n{body.strip()}" if body.strip() else heading,
                parent_id=parent_id,
                metadata={"section": heading},
            )
            trace.add_step(step)
            parent_id = step.id

        trace.outcome = "strategy_captured"
        return trace

    def summary(self, traces: list[ReasoningTrace]) -> dict:
        """Compute summary statistics from a set of experiment traces.

        Returns:
            Dictionary with counts, best result, keep/discard/crash rates.
        """
        total = len(traces)
        if total == 0:
            return {"total": 0}

        outcomes = [t.outcome for t in traces]
        keeps = outcomes.count("keep")
        discards = outcomes.count("discard")
        crashes = outcomes.count("crash")

        # Find best val_bpb across all traces
        best_bpb = None
        for trace in traces:
            for step in trace.get_steps_by_type(StepType.OBSERVATION):
                bpb = step.metadata.get("val_bpb", 0)
                if bpb > 0 and (best_bpb is None or bpb < best_bpb):
                    best_bpb = bpb

        return {
            "total": total,
            "keeps": keeps,
            "discards": discards,
            "crashes": crashes,
            "keep_rate": keeps / total if total > 0 else 0,
            "best_val_bpb": best_bpb,
        }

    # -- Helpers --

    @staticmethod
    def _parse_float(value: str) -> float:
        """Safely parse a float, returning 0.0 on failure."""
        try:
            return float(value.strip())
        except (ValueError, AttributeError) as exc:
            logger.warning("Could not parse metric value %r: %s", value, exc)
            return 0.0

    @staticmethod
    def _extract_sections(markdown: str) -> list[tuple[str, str]]:
        """Extract (heading, body) pairs from markdown text."""
        sections: list[tuple[str, str]] = []
        lines = markdown.split("\n")
        current_heading = ""
        current_body: list[str] = []

        for line in lines:
            if line.startswith("#"):
                if current_heading:
                    sections.append(
                        (current_heading, "\n".join(current_body))
                    )
                current_heading = line.lstrip("#").strip()
                current_body = []
            else:
                current_body.append(line)

        if current_heading:
            sections.append((current_heading, "\n".join(current_body)))

        return sections


class ToolUseCapture:
    """Captures structured tool-use traces from transcript-style messages.

    This class converts assistant conversations with explicit thinking,
    tool calls, tool responses, and final answers into HUMMBL traces
    aligned with the StructuredToolUse protocol.
    """

    _THINK_RE = re.compile(
        r"<think>\s*(.*?)\s*</think>", re.IGNORECASE | re.DOTALL
    )
    _TOOL_CALL_RE = re.compile(
        r"<tool_call>\s*(.*?)\s*</tool_call>", re.IGNORECASE | re.DOTALL
    )
    _TOOL_RESPONSE_RE = re.compile(
        r"<tool_response>\s*(.*?)\s*</tool_response>",
        re.IGNORECASE | re.DOTALL,
    )
    _ANSWER_RE = re.compile(
        r"<answer>\s*(.*?)\s*</answer>", re.IGNORECASE | re.DOTALL
    )

    def capture_from_messages(
        self,
        messages: list[dict[str, Any]],
        *,
        system_prompt: str = "",
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> ReasoningTrace:
        """Capture a tool-use trace from generic transcript messages.

        Supported message shapes:
        - {"role": "...", "content": "..."}
        - {"from": "...", "value": "..."}

        The capture logic expects assistant messages to contain some
        combination of:
        - <think>...</think>
        - <tool_call>...</tool_call>
        - <answer>...</answer>

        User or tool messages may include:
        - <tool_response>...</tool_response>
        """
        normalized = self._normalize_messages(messages)
        trace = make_trace(
            domain="tool_reasoning",
            topology=ReasoningTopology.CHAIN,
            tags=(tags or []) + ["structured_tool_use"],
        )

        parent_id: Optional[str] = None
        if system_prompt or metadata:
            context = make_step(
                StepType.REFLECTION,
                content="Capture context for structured tool-use transcript",
                metadata={
                    "system_prompt": system_prompt,
                    **(metadata or {}),
                },
            )
            trace.add_step(context)
            parent_id = context.id

        pending_actions: list[dict[str, Any]] = []
        pending_result: Optional[dict[str, Any]] = None

        for message in normalized:
            role = message["role"]
            content = message["content"]

            if role in {"assistant", "model"}:
                thought = self._extract_text_blocks(self._THINK_RE, content)
                answer = self._extract_text_blocks(self._ANSWER_RE, content)
                tool_calls = self._extract_tool_calls(content)

                if pending_result is not None:
                    eval_step, decision_step = self._build_post_tool_steps(
                        thought=thought or answer,
                        answer=answer,
                        tool_calls=tool_calls,
                        pending_result=pending_result,
                        parent_id=pending_result["step_id"],
                    )
                    trace.add_step(eval_step)
                    trace.add_step(decision_step)
                    parent_id = decision_step.id
                    if answer:
                        trace.outcome = "finalize"
                    pending_result = None

                if tool_calls:
                    for call in tool_calls:
                        observation, hypothesis, action = (
                            self._build_pre_tool_steps(
                                thought=thought,
                                tool_call=call,
                                parent_id=parent_id,
                            )
                        )
                        trace.add_step(observation)
                        trace.add_step(hypothesis)
                        trace.add_step(action)
                        parent_id = action.id
                        pending_actions.append(
                            {
                                "step_id": action.id,
                                "tool_name": call["name"],
                                "tool_args": call["arguments"],
                                "thought": thought,
                                "candidate": hypothesis.metadata["candidate"],
                            }
                        )
                elif answer and trace.outcome != "finalize":
                    # Final answer with no unresolved tool result.
                    observation, hypothesis = self._build_answer_context_steps(
                        thought=thought or answer,
                        parent_id=parent_id,
                    )
                    trace.add_step(observation)
                    trace.add_step(hypothesis)
                    evaluation = make_step(
                        StepType.EVALUATION,
                        content=self._shorten(thought or answer),
                        parent_id=hypothesis.id,
                        metadata={
                            "supports_hypothesis": "yes",
                            "next_status": "finalize",
                        },
                    )
                    trace.add_step(evaluation)
                    decision = make_step(
                        StepType.DECISION,
                        content="Decision: finalize",
                        parent_id=evaluation.id,
                        metadata={
                            "status": "finalize",
                            "final_answer": self._shorten(answer),
                        },
                    )
                    trace.add_step(decision)
                    parent_id = decision.id
                    trace.outcome = "finalize"

            elif role in {"user", "human", "tool"}:
                tool_response = self._extract_text_blocks(
                    self._TOOL_RESPONSE_RE, content
                )
                if tool_response and pending_actions:
                    action_ctx = pending_actions.pop(0)
                    obs = make_step(
                        StepType.OBSERVATION,
                        content=f"Tool result from {action_ctx['tool_name']}: "
                        f"{self._shorten(tool_response)}",
                        parent_id=action_ctx["step_id"],
                        metadata=self._build_observation_metadata(
                            thought=action_ctx["thought"],
                            tool_name=action_ctx["tool_name"],
                            result_summary=tool_response,
                        ),
                    )
                    trace.add_step(obs)
                    parent_id = obs.id
                    pending_result = {
                        "step_id": obs.id,
                        "tool_name": action_ctx["tool_name"],
                        "tool_args": action_ctx["tool_args"],
                        "tool_response": tool_response,
                        "thought": action_ctx["thought"],
                        "candidate": action_ctx["candidate"],
                    }

        if pending_result is not None:
            evaluation = make_step(
                StepType.EVALUATION,
                content="Run ended before post-tool evaluation was captured",
                parent_id=pending_result["step_id"],
                metadata={
                    "supports_hypothesis": "unclear",
                    "next_status": "unfinished",
                },
            )
            trace.add_step(evaluation)
            decision = make_step(
                StepType.DECISION,
                content="Decision: unfinished",
                parent_id=evaluation.id,
                metadata={"status": "unfinished"},
            )
            trace.add_step(decision)
            parent_id = decision.id
            trace.outcome = "unfinished"

        if not trace.get_steps_by_type(StepType.ACTION):
            raise ValueError("No tool calls found in transcript")

        if trace.outcome is None:
            trace.outcome = "captured"

        return trace

    def capture_from_spotagenticcot_row(
        self, row: dict[str, Any]
    ) -> ReasoningTrace:
        """Capture a trace from a SpotAgenticCoT dataset row."""
        row_id = str(row.get("id", "unknown"))
        images = row.get("images", []) or []
        return self.capture_from_messages(
            row.get("conversations", []) or [],
            system_prompt=str(row.get("system", "")),
            tags=["spotagenticcot", row_id],
            metadata={
                "source": "spotagenticcot",
                "row_id": row_id,
                "image_count": len(images),
            },
        )

    def summary(self, traces: list[ReasoningTrace]) -> dict[str, Any]:
        """Compute basic summary statistics for tool-use traces."""
        total = len(traces)
        if total == 0:
            return {"total": 0}

        tool_calls = 0
        recoveries = 0
        finalizations = 0
        unfinished = 0

        for trace in traces:
            tool_calls += len(trace.get_steps_by_type(StepType.ACTION))
            for step in trace.get_steps_by_type(StepType.DECISION):
                status = step.metadata.get("status")
                if status == "recover":
                    recoveries += 1
                elif status == "finalize":
                    finalizations += 1
                elif status == "unfinished":
                    unfinished += 1

        return {
            "total": total,
            "tool_calls": tool_calls,
            "recoveries": recoveries,
            "finalizations": finalizations,
            "unfinished": unfinished,
            "avg_tool_calls_per_trace": tool_calls / total,
        }

    def _build_pre_tool_steps(
        self,
        *,
        thought: str,
        tool_call: dict[str, Any],
        parent_id: Optional[str],
    ) -> tuple[ReasoningStep, ReasoningStep, ReasoningStep]:
        tool_name = tool_call["name"]
        arguments = tool_call["arguments"]

        observation = make_step(
            StepType.OBSERVATION,
            content=self._shorten(thought or f"Preparing to call {tool_name}"),
            parent_id=parent_id,
            metadata=self._build_observation_metadata(
                thought=thought,
                tool_name=tool_name,
                result_summary="",
            ),
        )
        hypothesis = make_step(
            StepType.HYPOTHESIS,
            content=self._shorten(self._extract_candidate(thought)),
            parent_id=observation.id,
            metadata={
                "candidate": self._extract_candidate(thought),
                "information_target": self._extract_information_target(
                    tool_name, arguments
                ),
            },
        )
        action = make_step(
            StepType.ACTION,
            content=f"Call tool '{tool_name}' with arguments {arguments}",
            parent_id=hypothesis.id,
            metadata={
                "tool_name": tool_name,
                "why_now": self._extract_why_now(thought),
                "expected_signal": self._infer_expected_signal(
                    tool_name, arguments
                ),
                "arguments": arguments,
            },
        )
        return observation, hypothesis, action

    def _build_post_tool_steps(
        self,
        *,
        thought: str,
        answer: str,
        tool_calls: list[dict[str, Any]],
        pending_result: dict[str, Any],
        parent_id: str,
    ) -> tuple[ReasoningStep, ReasoningStep]:
        status = self._infer_decision_status(
            thought=thought or answer,
            answer=answer,
            tool_calls=tool_calls,
        )
        evaluation = make_step(
            StepType.EVALUATION,
            content=self._shorten(thought or answer or pending_result["tool_response"]),
            parent_id=parent_id,
            metadata={
                "supports_hypothesis": self._infer_support(thought or answer),
                "next_status": status,
            },
        )
        decision = make_step(
            StepType.DECISION,
            content=f"Decision: {status}",
            parent_id=evaluation.id,
            metadata={
                "status": status,
                "final_answer": self._shorten(answer) if answer else "",
            },
        )
        return evaluation, decision

    def _build_answer_context_steps(
        self, *, thought: str, parent_id: Optional[str]
    ) -> tuple[ReasoningStep, ReasoningStep]:
        observation = make_step(
            StepType.OBSERVATION,
            content=self._shorten(thought),
            parent_id=parent_id,
            metadata=self._build_observation_metadata(
                thought=thought,
                tool_name="",
                result_summary="",
            ),
        )
        hypothesis = make_step(
            StepType.HYPOTHESIS,
            content=self._shorten(self._extract_candidate(thought)),
            parent_id=observation.id,
            metadata={
                "candidate": self._extract_candidate(thought),
                "information_target": "",
            },
        )
        return observation, hypothesis

    @staticmethod
    def _normalize_messages(
        messages: list[dict[str, Any]],
    ) -> list[dict[str, str]]:
        normalized = []
        for msg in messages:
            role = str(msg.get("role", msg.get("from", ""))).strip().lower()
            content = str(msg.get("content", msg.get("value", "")))
            if role and content:
                normalized.append({"role": role, "content": content})
        return normalized

    @classmethod
    def _extract_text_blocks(cls, pattern: re.Pattern, content: str) -> str:
        matches = [m.strip() for m in pattern.findall(content) if m.strip()]
        return "\n".join(matches)

    @classmethod
    def _extract_tool_calls(cls, content: str) -> list[dict[str, Any]]:
        calls = []
        for raw in cls._TOOL_CALL_RE.findall(content):
            raw = raw.strip()
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                parsed = {
                    "name": cls._extract_string_field(raw, "name"),
                    "arguments": {},
                    "raw": raw,
                }
            name = str(parsed.get("name", "unknown")).strip() or "unknown"
            arguments = parsed.get("arguments", {})
            if not isinstance(arguments, dict):
                arguments = {"value": arguments}
            calls.append(
                {
                    "name": name,
                    "arguments": arguments,
                    "raw": raw,
                }
            )
        return calls

    @staticmethod
    def _extract_string_field(raw: str, field: str) -> str:
        match = re.search(
            rf'"{re.escape(field)}"\s*:\s*"([^"]+)"', raw, re.IGNORECASE
        )
        return match.group(1) if match else ""

    def _build_observation_metadata(
        self,
        *,
        thought: str,
        tool_name: str,
        result_summary: str,
    ) -> dict[str, Any]:
        return {
            "knowns": self._extract_knowns(thought),
            "unknowns": self._extract_unknowns(thought),
            "tool_name": tool_name,
            "result_summary": self._shorten(result_summary, limit=240),
        }

    def _extract_knowns(self, thought: str) -> str:
        cleaned = self._strip_tags(thought)
        if not cleaned:
            return ""
        sentences = self._split_sentences(cleaned)
        return " ".join(sentences[:2]) if sentences else cleaned

    def _extract_unknowns(self, thought: str) -> str:
        cleaned = self._strip_tags(thought)
        if not cleaned:
            return ""
        markers = [
            "need",
            "uncertain",
            "unclear",
            "still",
            "missing",
            "not visible",
            "not confirmed",
        ]
        matches = [
            s for s in self._split_sentences(cleaned)
            if any(marker in s.lower() for marker in markers)
        ]
        return " ".join(matches) if matches else "Not explicitly separated."

    def _extract_candidate(self, thought: str) -> str:
        cleaned = self._strip_tags(thought)
        if not cleaned:
            return ""
        for marker in ("location hypothesis", "hypothesis"):
            match = re.search(
                rf"{marker}\s*[:\-]?\s*(.+)",
                cleaned,
                re.IGNORECASE | re.DOTALL,
            )
            if match:
                return self._shorten(match.group(1))
        sentences = self._split_sentences(cleaned)
        return self._shorten(sentences[0]) if sentences else self._shorten(cleaned)

    def _extract_information_target(
        self, tool_name: str, arguments: dict[str, Any]
    ) -> str:
        for key in ("query", "address", "path", "bbox_2d"):
            if key in arguments:
                return self._shorten(str(arguments[key]))
        return tool_name

    def _extract_why_now(self, thought: str) -> str:
        return self._shorten(self._strip_tags(thought), limit=280)

    @staticmethod
    def _infer_expected_signal(
        tool_name: str, arguments: dict[str, Any]
    ) -> str:
        lowered = tool_name.lower()
        if "zoom" in lowered or "crop" in lowered:
            return "Higher-resolution local evidence from a discriminative region."
        if "search" in lowered or "geocode" in lowered or "lookup" in lowered:
            return "External verification or exact identifying details."
        if "open" in lowered or "read" in lowered:
            return "Direct source evidence from the referenced file or artifact."
        if arguments:
            return "Additional evidence from the selected tool call."
        return "Evidence that reduces uncertainty."

    @staticmethod
    def _infer_support(text: str) -> str:
        lowered = text.lower()
        negative_markers = [
            "wrong",
            "incorrect",
            "didn't",
            "did not",
            "not the correct",
            "contradict",
        ]
        positive_markers = [
            "confirm",
            "confirmed",
            "aligns",
            "matches",
            "perfect",
            "great",
            "supports",
        ]
        if any(marker in lowered for marker in negative_markers):
            return "no"
        if any(marker in lowered for marker in positive_markers):
            return "yes"
        return "unclear"

    def _infer_decision_status(
        self,
        *,
        thought: str,
        answer: str,
        tool_calls: list[dict[str, Any]],
    ) -> str:
        if answer:
            return "finalize"
        lowered = thought.lower()
        if tool_calls:
            recovery_markers = (
                "wrong",
                "incorrect",
                "contradict",
                "doesn't match",
                "does not match",
                "unexpected",
                "override",
                "re-check",
                "recheck",
                "inspect",
                "before finalizing",
                "before finalising",
                "let me try",
                "instead",
                "try a more specific",
            )
            if any(marker in lowered for marker in recovery_markers):
                return "recover"
        if tool_calls:
            return "continue"
        return "captured"

    @staticmethod
    def _strip_tags(text: str) -> str:
        return re.sub(r"<[^>]+>", " ", text).strip()

    @staticmethod
    def _split_sentences(text: str) -> list[str]:
        return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]

    @staticmethod
    def _shorten(text: str, limit: int = 180) -> str:
        compact = re.sub(r"\s+", " ", text).strip()
        if len(compact) <= limit:
            return compact
        return compact[: limit - 3].rstrip() + "..."
