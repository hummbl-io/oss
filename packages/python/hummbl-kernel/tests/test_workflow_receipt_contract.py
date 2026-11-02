import asyncio
import json
from unittest.mock import Mock

import pytest

from hummbl_kernel.kernel import MissionModeKernel


@pytest.mark.parametrize(
    "workflow",
    [
        None,
        "not a workflow",
        "workflow_id: example\nworkflow: []",
        "[]",
        "null",
        "{}",
        '{"workflow_id":"w","workflow":[]}',
        '{"workflow_id":"w","workflow":[null]}',
        '{"workflow_id":"w","workflow":[{"step":"s","agent":"a"},null]}',
        '{"workflow_id":"w","workflow":[{"step":"s","agent":42}]}',
        '{"workflow_id":" ","workflow":[{"step":"s","agent":"a"}]}',
        '{"workflow_id":"w","workflow":[{"step":" ","agent":"a"}]}',
        '{"workflow_id":"w","workflow":[{"step":"s","agent":" "}]}',
        '{"workflow_id":"w","workflow":[{"step":"s"}]}',
        '{"workflow_id":"w","mission":null,"workflow":[{"step":"s","agent":"a"}]}',
        '{"workflow_id":"w","compliance_framework":"unknown",'
        '"workflow":[{"step":"s","agent":"a"}]}',
    ],
)
def test_malformed_workflow_creates_no_receipt_or_trail(workflow, monkeypatch):
    kernel = MissionModeKernel()
    create_trail = Mock(wraps=kernel.create_audit_trail)
    generate_receipt = Mock(wraps=kernel.generate_receipt)
    monkeypatch.setattr(kernel, "create_audit_trail", create_trail)
    monkeypatch.setattr(kernel, "generate_receipt", generate_receipt)
    with pytest.raises(ValueError):
        asyncio.run(kernel.execute_workflow(workflow, {}))
    assert not kernel.audit_trails
    create_trail.assert_not_called()
    generate_receipt.assert_not_called()


@pytest.mark.parametrize("inputs", [None, [], "input"])
def test_non_object_inputs_rejected_before_audit(inputs):
    kernel = MissionModeKernel()
    workflow = {"workflow_id": "example", "workflow": [{"step": "s1", "agent": "a"}]}
    with pytest.raises(ValueError, match="inputs"):
        asyncio.run(kernel.execute_workflow(json.dumps(workflow), inputs))
    assert not kernel.audit_trails


def test_simulation_cannot_claim_execution_or_supplied_evidence(monkeypatch):
    monkeypatch.setenv("MISSION_MODE_SIGNING_KEY", "local-test-signing-key")
    kernel = MissionModeKernel()
    workflow = {
        "workflow_id": "example",
        "workflow": [
            {
                "step": "s1",
                "agent": "nonexistent-agent",
                "outputs": {"evidence_refs": ["unverified"]},
            }
        ],
    }
    receipt = asyncio.run(kernel.execute_workflow(" \n" + json.dumps(workflow), {}))
    assert receipt.final_status == "simulated"
    assert receipt.evidence_refs == []
    events = kernel.audit_trails[receipt.audit_trail_ref]["events"]
    assert [event["event_type"] for event in events] == [
        "simulation.initialized",
        "step.simulated",
    ]
    assert all(event["evidence_refs"] == [] for event in events)
    assert events[-1]["payload"]["step"]["outputs"]["evidence_refs"] == ["unverified"]
    assert kernel.audit_trails[receipt.audit_trail_ref]["status"] == "finalized"
