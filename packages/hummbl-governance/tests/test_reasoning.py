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

import json
import tempfile
from pathlib import Path

from hummbl_governance.reasoning import ReasoningEngine


def test_reasoning_engine_loads_models():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tf:
        models = [
            {
                "code": "DE1",
                "name": "5 Whys",
                "transformation": "Decomposition",
                "definition": "Deep root cause analysis",
            },
            {
                "code": "S1",
                "name": "Systems Thinking",
                "transformation": "Systems",
                "definition": "Feedback loops",
            },
        ]
        json.dump(models, tf)
        tf_path = Path(tf.name)

    try:
        engine = ReasoningEngine(models_path=tf_path)
        assert len(engine.models) == 2
        assert engine.get_model("DE1").name == "5 Whys"
    finally:
        tf_path.unlink()


def test_generate_system_prompt():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tf:
        models = [
            {
                "code": "DE1",
                "name": "5 Whys",
                "transformation": "Decomposition",
                "definition": "Deep root cause analysis",
            },
            {
                "code": "P1",
                "name": "First Principles",
                "transformation": "Perspective",
                "definition": "Reducing to axioms",
            },
        ]
        json.dump(models, tf)
        tf_path = Path(tf.name)

    try:
        engine = ReasoningEngine(models_path=tf_path)
        prompt = engine.generate_system_prompt("DE1", depth=3)
        assert "DE1" in prompt
        assert "why_5" in prompt

        prompt_p1 = engine.generate_system_prompt("P1")
        assert "axioms" in prompt_p1
    finally:
        tf_path.unlink()


def test_parse_llm_output():
    engine = ReasoningEngine()
    output = """
    ```json
    {
        "analysis": {"step1": "test"},
        "recommendation": "Do it",
        "confidence": 0.9
    }
    ```
    """
    result = engine.parse_llm_output("DE1", output)
    assert result.confidence == 0.9
    assert result.recommendation == "Do it"
    assert result.analysis["step1"] == "test"


def test_parse_invalid_output_graceful():
    engine = ReasoningEngine()
    result = engine.parse_llm_output("DE1", "not json")
    assert result.confidence == 0.0
    assert "error" in result.analysis


def _make_engine(*codes_and_names) -> "ReasoningEngine":
    """Helper: build an engine with given (code, name) model pairs."""
    import tempfile
    models = [
        {
            "code": code,
            "name": name,
            "transformation": "Test",
            "definition": f"Test definition for {code}",
        }
        for code, name in codes_and_names
    ]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tf:
        json.dump(models, tf)
        tf_path = Path(tf.name)
    engine = ReasoningEngine(models_path=tf_path)
    tf_path.unlink()
    return engine


def test_generate_system_prompt_unknown_code_raises():
    engine = _make_engine(("DE1", "5 Whys"))
    try:
        engine.generate_system_prompt("UNKNOWN")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "UNKNOWN" in str(e)


def test_generate_system_prompt_in2_branch():
    engine = _make_engine(("IN2", "Pre-Mortem"))
    prompt = engine.generate_system_prompt("IN2")
    assert "ALREADY" in prompt or "failed" in prompt.lower()


def test_generate_system_prompt_s1_branch():
    engine = _make_engine(("S1", "Systems Thinking"))
    prompt = engine.generate_system_prompt("S1")
    assert "feedback" in prompt.lower() or "loops" in prompt.lower()


def test_generate_system_prompt_re1_branch():
    engine = _make_engine(("RE1", "Recursion"))
    prompt = engine.generate_system_prompt("RE1")
    assert "recursive" in prompt.lower() or "base_case" in prompt


def test_parse_llm_output_unknown_code_raises():
    engine = _make_engine(("DE1", "5 Whys"))
    try:
        engine.parse_llm_output("UNKNOWN", '{"analysis": {}, "recommendation": "x", "confidence": 0.5}')
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "UNKNOWN" in str(e)


def test_parse_llm_output_no_json_fence():
    engine = _make_engine(("DE1", "5 Whys"))
    output = '{"analysis": {"step": "ok"}, "recommendation": "Do it", "confidence": 0.7}'
    result = engine.parse_llm_output("DE1", output)
    assert result.confidence == 0.7
    assert result.model == "DE1"


def test_reasoning_engine_missing_file():
    engine = ReasoningEngine(models_path=Path("/nonexistent/path/models.json"))
    assert len(engine.models) == 0
    assert engine.get_model("DE1") is None


def test_reasoning_engine_corrupt_json_file(tmp_path):
    corrupt = tmp_path / "models.json"
    corrupt.write_text("not valid json")
    engine = ReasoningEngine(models_path=corrupt)
    assert len(engine.models) == 0


def test_apply_result_metadata_default():
    from hummbl_governance.reasoning import ApplyResult
    result = ApplyResult(
        model="DE1",
        name="5 Whys",
        analysis={"x": 1},
        recommendation="ok",
        confidence=0.8,
    )
    assert result.metadata == {}


def test_get_model_returns_none_for_unknown():
    engine = _make_engine(("DE1", "5 Whys"))
    assert engine.get_model("NOTHERE") is None
