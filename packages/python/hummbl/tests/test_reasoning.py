from hummbl.reasoning import ReasoningTopology, StepType, make_step, make_trace


def test_add_step_links_parent_and_child():
    trace = make_trace("unit-test", topology=ReasoningTopology.CHAIN)
    root = make_step(StepType.HYPOTHESIS, "Root hypothesis")
    trace.add_step(root)

    child = make_step(
        StepType.ACTION,
        "Act on the hypothesis",
        parent_id=root.id,
    )
    trace.add_step(child)

    assert trace.get_step(root.id).children_ids == [child.id]
    assert trace.get_step(child.id).parent_id == root.id


def test_trace_round_trip_json_preserves_structure():
    trace = make_trace("serialization-test")
    first = make_step(StepType.OBSERVATION, "Observed something")
    trace.add_step(first)
    second = make_step(
        StepType.EVALUATION,
        "Interpreted the observation",
        parent_id=first.id,
        metadata={"signal": "strong"},
    )
    trace.add_step(second)
    trace.outcome = "keep"

    restored = trace.from_json(trace.to_json())

    assert restored.id == trace.id
    assert restored.topology == trace.topology
    assert restored.outcome == "keep"
    assert [step.type for step in restored.steps] == [
        StepType.OBSERVATION,
        StepType.EVALUATION,
    ]
    assert restored.get_step(second.id).metadata["signal"] == "strong"


def test_get_path_returns_root_to_target_order():
    trace = make_trace("path-test")
    root = make_step(StepType.HYPOTHESIS, "Start")
    trace.add_step(root)
    middle = make_step(StepType.ACTION, "Middle", parent_id=root.id)
    trace.add_step(middle)
    leaf = make_step(StepType.DECISION, "Finish", parent_id=middle.id)
    trace.add_step(leaf)

    path = trace.get_path(leaf.id)

    assert [step.id for step in path] == [root.id, middle.id, leaf.id]
