import pytest

from hummbl.reasoning import ReasoningStep, ReasoningTrace, StepType, make_step, make_trace


@pytest.mark.parametrize(
    "confidence",
    [-0.01, 1.01, float("nan"), float("inf"), -float("inf"), True, False, "0.5", [], 10**400],
)
def test_invalid_confidence_rejected_at_construction_and_load(confidence):
    with pytest.raises(ValueError, match="confidence"):
        make_step(StepType.HYPOTHESIS, "claim", confidence=confidence)
    with pytest.raises(ValueError, match="confidence"):
        ReasoningStep.from_dict(
            {"id": "s", "type": "hypothesis", "content": "claim", "confidence": confidence}
        )


@pytest.mark.parametrize("confidence", [None, 0, 0.0, 0.5, 1, 1.0])
def test_confidence_boundaries_survive_trace_roundtrip(confidence):
    trace = make_trace("example")
    trace.add_step(make_step(StepType.HYPOTHESIS, "claim", confidence=confidence))
    restored = ReasoningTrace.from_json(trace.to_json())
    assert restored.steps[0].confidence == confidence


@pytest.mark.parametrize("confidence", [float("nan"), -1, 2, True, "0.5", 10**400])
def test_mutation_cannot_serialize_invalid_confidence(confidence):
    step = make_step(StepType.HYPOTHESIS, "claim", confidence=0.5)
    trace = make_trace("example")
    trace.add_step(step)
    step.confidence = confidence
    with pytest.raises(ValueError, match="confidence"):
        step.to_dict()
    with pytest.raises(ValueError, match="confidence"):
        trace.to_json()
