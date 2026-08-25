# Copyright 2024-2026 HUMMBL, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

"""Base120 Reasoning Kernel.

Provides the core logic for applying mental models to problem statements.
Part of the zero-dependency hummbl-governance kernel.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class Base120Model:
    """A Base120 mental model definition."""

    code: str
    name: str
    transformation: str
    definition: str


@dataclass(frozen=True, slots=True)
class ApplyResult:
    """The result of applying a model to a problem."""

    model: str
    name: str
    analysis: dict[str, Any]
    recommendation: str
    confidence: float
    metadata: dict[str, Any] = field(default_factory=dict)


class ReasoningEngine:
    """Core logic for the Reasoning primitive."""

    def __init__(self, models_path: Path | None = None):
        if models_path is None:
            models_path = Path(__file__).parent / "data" / "base120_models.json"
        
        self.models_path = models_path
        self.models: dict[str, Base120Model] = {}
        self._load_models()

    def _load_models(self) -> None:
        """Load model definitions from JSON."""
        try:
            if not self.models_path.exists():
                return

            with open(self.models_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    model = Base120Model(
                        code=item["code"],
                        name=item["name"],
                        transformation=item["transformation"],
                        definition=item["definition"],
                    )
                    self.models[model.code] = model
        except Exception as e:
            logger.error(f"Failed to load Base120 models: {e}")

    def get_model(self, code: str) -> Base120Model | None:
        """Get a model by its code."""
        return self.models.get(code)

    def generate_system_prompt(self, code: str, depth: int = 1) -> str:
        """Generate a specialized system prompt for the given model."""
        model = self.get_model(code)
        if not model:
            raise ValueError(f"Unknown model code: {code}")

        prompt = [
            f"You are a specialized reasoning engine implementing the Base120 mental model {model.code}: {model.name}.",
            f"Definition: {model.definition}",
            f"Transformation: {model.transformation}",
            "",
            "Your objective is to apply this model to the provided"
            f" problem statement with a reasoning depth of {depth}.",
            "",
            "Constraints:",
            "1. Focus strictly on the logic of this specific mental model.",
            "2. Provide evidence-based analysis where possible.",
            "3. Identify gaps in information or contradictions.",
            "4. Return your output EXCLUSIVELY in valid JSON format.",
            "",
            "The JSON output must contain these top-level keys:",
            '- "analysis": A structured object containing the step-by-step reasoning.',
            '- "recommendation": A clear, actionable suggestion based on the analysis.',
            '- "confidence": A float between 0.0 and 1.0 reflecting your certainty.',
            "",
        ]

        if model.code == "DE1":
            prompt.append(
                "For DE1 (5 Whys), the 'analysis' object should contain"
                f" 'why_1' through 'why_{max(3, 2 + depth)}' as keys."
            )
        elif model.code == "IN2":
            prompt.append(
                "For IN2, assume the project or decision has ALREADY"
                " FAILED. The 'analysis' should identify the failure causes."
            )
        elif model.code == "P1":
            prompt.append(
                "For P1, reduce the problem to its most fundamental"
                " truths. List 'axioms' and 'derived_conclusions'."
            )
        elif model.code == "S1":
            prompt.append(
                "For S1, analyze the feedback loops and emergent behaviors."
                " Identify 'positive_feedback' and 'balancing_loops'."
            )
        elif model.code == "RE1":
            prompt.append(
                "For RE1, identify patterns that repeat across scales."
                " Analyze 'base_case' and 'recursive_step'."
            )

        return "\n".join(prompt)

    def parse_llm_output(self, code: str, output: str) -> ApplyResult:
        """Parse raw LLM output into structured ApplyResult."""
        model = self.get_model(code)
        if not model:
            raise ValueError(f"Unknown model code: {code}")

        try:
            clean_output = output.strip()
            if clean_output.startswith("```json"):
                clean_output = clean_output[7:]
            if clean_output.endswith("```"):
                clean_output = clean_output[:-3]
            clean_output = clean_output.strip()

            data = json.loads(clean_output)
            
            return ApplyResult(
                model=model.code,
                name=model.name,
                analysis=data.get("analysis", {}),
                recommendation=data.get("recommendation", "No recommendation provided."),
                confidence=float(data.get("confidence", 0.5)),
                metadata={"raw_length": len(output)}
            )
        except Exception:
            return ApplyResult(
                model=model.code,
                name=model.name,
                analysis={"error": "Failed to parse LLM output", "raw": output},
                recommendation="Error: See analysis for details.",
                confidence=0.0
            )
