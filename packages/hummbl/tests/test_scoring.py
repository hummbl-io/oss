from hummbl import StepType, StructuredToolUseScorer, ToolUseCapture
from hummbl.reasoning import make_step, make_trace


def test_structured_tool_use_scorer_scores_recovery_trace_high():
    capture = ToolUseCapture()
    scorer = StructuredToolUseScorer()

    messages = [
        {"role": "user", "content": "Find why FEATURE_X is active."},
        {
            "role": "assistant",
            "content": (
                "<think>I know FEATURE_X is active in production. "
                "I still need the config source, so I will search the "
                "repository for the flag definition.</think>"
                "<tool_call>"
                '{"name":"repo_search","arguments":{"query":"FEATURE_X"}}'
                "</tool_call>"
            ),
        },
        {
            "role": "user",
            "content": (
                "<tool_response>"
                '{"matches":["config.py: FEATURE_X = False"]}'
                "</tool_response>"
            ),
        },
        {
            "role": "assistant",
            "content": (
                "<think>The result contradicts my assumption about the "
                "effective value. I should inspect the runtime override "
                "before finalizing.</think>"
                "<tool_call>"
                '{"name":"open_file","arguments":{"path":"env.py"}}'
                "</tool_call>"
            ),
        },
        {
            "role": "user",
            "content": (
                "<tool_response>"
                '{"content":"FEATURE_X = True"}'
                "</tool_response>"
            ),
        },
        {
            "role": "assistant",
            "content": (
                "<think>The override explains the behavior and confirms "
                "the root cause.</think>"
                "<answer>FEATURE_X is overridden in env.py.</answer>"
            ),
        },
    ]

    trace = capture.capture_from_messages(messages)
    score = scorer.score_trace(trace)

    assert score.protocol_violations == []
    assert score.total_score == 10
    assert score.dimensions["pre_tool_reasoning"].score == 2
    assert score.dimensions["tool_discriminativeness"].score == 2
    assert score.dimensions["evidence_integration"].score == 2
    assert score.dimensions["recovery_behavior"].score == 2
    assert score.dimensions["final_artifact_quality"].score == 2


def test_structured_tool_use_scorer_penalizes_weak_trace():
    scorer = StructuredToolUseScorer()
    trace = make_trace("tool_reasoning")

    observation = make_step(StepType.OBSERVATION, "Looking for the answer.")
    trace.add_step(observation)
    action = make_step(
        StepType.ACTION,
        "Search the repository",
        parent_id=observation.id,
        metadata={"tool_name": "repo_search"},
    )
    trace.add_step(action)
    tool_result = make_step(
        StepType.OBSERVATION,
        "Tool output pasted without interpretation.",
        parent_id=action.id,
        metadata={"tool_name": "repo_search"},
    )
    trace.add_step(tool_result)
    decision = make_step(
        StepType.DECISION,
        "Finalize answer",
        parent_id=tool_result.id,
        metadata={
            "status": "finalize",
            "final_answer": "It is probably in config.py.",
        },
    )
    trace.add_step(decision)
    trace.outcome = "finalize"

    score = scorer.score_trace(trace)

    assert score.protocol_violations
    assert score.dimensions["pre_tool_reasoning"].score == 0
    assert score.dimensions["tool_discriminativeness"].score == 0
    assert score.dimensions["evidence_integration"].score == 0
    assert score.dimensions["recovery_behavior"].score == 1
    assert score.dimensions["final_artifact_quality"].score == 1
    assert score.total_score == 2


def test_structured_tool_use_scorer_summary_aggregates_scores():
    capture = ToolUseCapture()
    scorer = StructuredToolUseScorer()

    strong_trace = capture.capture_from_messages(
        [
            {"role": "user", "content": "Find why FEATURE_X is active."},
            {
                "role": "assistant",
                "content": (
                    "<think>I know FEATURE_X is active in production. "
                    "I still need the config source, so I will search the "
                    "repository for the flag definition.</think>"
                    "<tool_call>"
                    '{"name":"repo_search","arguments":{"query":"FEATURE_X"}}'
                    "</tool_call>"
                ),
            },
            {
                "role": "user",
                "content": (
                    "<tool_response>"
                    '{"matches":["config.py: FEATURE_X = False"]}'
                    "</tool_response>"
                ),
            },
            {
                "role": "assistant",
                "content": (
                    "<think>The result contradicts my assumption about the "
                    "effective value. I should inspect the runtime override "
                    "before finalizing.</think>"
                    "<tool_call>"
                    '{"name":"open_file","arguments":{"path":"env.py"}}'
                    "</tool_call>"
                ),
            },
            {
                "role": "user",
                "content": (
                    "<tool_response>"
                    '{"content":"FEATURE_X = True"}'
                    "</tool_response>"
                ),
            },
            {
                "role": "assistant",
                "content": (
                    "<think>The override explains the behavior and confirms "
                    "the root cause.</think>"
                    "<answer>FEATURE_X is overridden in env.py.</answer>"
                ),
            },
        ]
    )

    weak_trace = make_trace("tool_reasoning")
    weak_observation = make_step(
        StepType.OBSERVATION,
        "Looking for the answer.",
    )
    weak_trace.add_step(weak_observation)
    weak_action = make_step(
        StepType.ACTION,
        "Search the repository",
        parent_id=weak_observation.id,
        metadata={"tool_name": "repo_search"},
    )
    weak_trace.add_step(weak_action)
    weak_result = make_step(
        StepType.OBSERVATION,
        "Tool output pasted without interpretation.",
        parent_id=weak_action.id,
        metadata={"tool_name": "repo_search"},
    )
    weak_trace.add_step(weak_result)
    weak_decision = make_step(
        StepType.DECISION,
        "Finalize answer",
        parent_id=weak_result.id,
        metadata={
            "status": "finalize",
            "final_answer": "It is probably in config.py.",
        },
    )
    weak_trace.add_step(weak_decision)
    weak_trace.outcome = "finalize"

    summary = scorer.summary(
        scorer.score_traces([strong_trace, weak_trace])
    )

    assert summary["total"] == 2
    assert summary["max_total_score"] == 10
    assert summary["average_total_score"] == 6.0
    assert summary["protocol_conformance_rate"] == 0.5
    assert summary["finalization_rate"] == 1.0
    assert summary["recovery_trigger_rate"] == 0.5
    assert summary["dimension_averages"]["pre_tool_reasoning"] == 1.0
