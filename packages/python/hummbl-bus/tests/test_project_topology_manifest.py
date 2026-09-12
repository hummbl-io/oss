"""Stdlib conformance checks for the project topology manifest example."""

import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
SCHEMA = ROOT / "docs" / "architecture" / "project-topology-manifest.v1.schema.json"
EXAMPLE = ROOT / "docs" / "architecture" / "project-topology-manifest.hummbl-bus.example.json"


def test_topology_schema_and_example_are_valid_json() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    example = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    assert schema["$schema"].endswith("/draft/2020-12/schema")
    assert schema["properties"]["schema"]["const"] == example["schema"]


def test_hummbl_bus_example_declares_one_writer_and_unique_sidecars() -> None:
    example = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    cell = example["cell"]
    assert cell["canonical_writer"]
    assert len(cell["message_types"]) == len(set(cell["message_types"]))
    names = [sidecar["name"] for sidecar in example["sidecars"]]
    assert len(names) == len(set(names))
    assert example["status"] == "proposed"
    assert example["evidence"]["deployment_verified"] is False
