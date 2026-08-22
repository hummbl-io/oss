from hummbl.protocols import ScientificMethod, StructuredToolUse
from hummbl.reasoning import StepType, make_step


def test_scientific_method_accepts_valid_trace():
    protocol = ScientificMethod()
    trace = protocol.create_trace()

    trace.add_step(
        make_step(
            StepType.HYPOTHESIS,
            "Depth should help",
            metadata={"predicted_direction": "down"},
        )
    )
    previous_id = trace.steps[-1].id
    trace.add_step(
        make_step(
            StepType.ACTION,
            "Modify model depth",
            parent_id=previous_id,
            metadata={"commit_hash": "abc123"},
        )
    )
    previous_id = trace.steps[-1].id
    trace.add_step(
        make_step(
            StepType.ACTION,
            "Run experiment",
            parent_id=previous_id,
        )
    )
    previous_id = trace.steps[-1].id
    trace.add_step(
        make_step(
            StepType.OBSERVATION,
            "Observe results",
            parent_id=previous_id,
            metadata={"val_bpb": 0.81, "peak_vram_mb": 6100},
        )
    )
    previous_id = trace.steps[-1].id
    trace.add_step(
        make_step(
            StepType.EVALUATION,
            "Compare with baseline",
            parent_id=previous_id,
            metadata={"baseline_bpb": 0.82, "delta_bpb": -0.01},
        )
    )
    previous_id = trace.steps[-1].id
    trace.add_step(
        make_step(
            StepType.DECISION,
            "Keep the change",
            parent_id=previous_id,
            metadata={"status": "keep"},
        )
    )

    assert protocol.validate_trace(trace) == []


def test_structured_tool_use_requires_metadata_and_sequence():
    protocol = StructuredToolUse()
    trace = protocol.create_trace()

    trace.add_step(
        make_step(
            StepType.OBSERVATION,
            "Knowns and unknowns",
            metadata={"knowns": ["repo loaded"], "unknowns": ["root cause"]},
        )
    )
    previous_id = trace.steps[-1].id
    trace.add_step(
        make_step(
            StepType.HYPOTHESIS,
            "The config is wrong",
            parent_id=previous_id,
            metadata={
                "candidate": "bad config",
                "information_target": "config source",
            },
        )
    )
    previous_id = trace.steps[-1].id
    trace.add_step(
        make_step(
            StepType.ACTION,
            "Search config files",
            parent_id=previous_id,
            metadata={
                "tool_name": "rg",
                "why_now": "reduce uncertainty",
                "expected_signal": "config override",
            },
        )
    )
    previous_id = trace.steps[-1].id
    trace.add_step(
        make_step(
            StepType.OBSERVATION,
            "Tool result",
            parent_id=previous_id,
            metadata={"tool_name": "rg", "result_summary": "override found"},
        )
    )
    previous_id = trace.steps[-1].id
    trace.add_step(
        make_step(
            StepType.EVALUATION,
            "Hypothesis supported",
            parent_id=previous_id,
            metadata={"supports_hypothesis": True, "next_status": "finalize"},
        )
    )
    previous_id = trace.steps[-1].id
    trace.add_step(
        make_step(
            StepType.DECISION,
            "Finalize answer",
            parent_id=previous_id,
            metadata={"status": "finalize"},
        )
    )

    assert protocol.validate_trace(trace) == []


def test_structured_tool_use_reports_missing_required_metadata():
    protocol = StructuredToolUse()
    trace = protocol.create_trace()
    trace.add_step(make_step(StepType.OBSERVATION, "Only context"))

    violations = protocol.validate_trace(trace)

    assert violations
    assert any("Missing required steps" in violation for violation in violations)
