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

"""Tests for hummbl_governance.dpia_generator (P58 DPIAGenerator)."""

import json
from pathlib import Path

import pytest
from hummbl_governance.dpia_generator import DPIAGenerator

@pytest.fixture
def tmp_store(tmp_path):
    return tmp_path

@pytest.fixture
def mock_review_gate_store(tmp_store):
    gate_file = tmp_store / "gates.jsonl"
    with open(gate_file, "w") as f:
        f.write('{"gate_id": "g1", "solely_automated": true, "decision_summary": "test"}\n')
        f.write('{"gate_id": "g2", "solely_automated": false, "decision_summary": "test"}\n')
    return gate_file

@pytest.fixture
def generator(mock_review_gate_store):
    return DPIAGenerator(review_gate_store=mock_review_gate_store)

@pytest.fixture
def empty_generator(tmp_store):
    return DPIAGenerator()

def test_generate_has_four_sections(empty_generator):
    doc = empty_generator.generate(
        system_name="TestSystem",
        system_description="Test Description",
        processing_purposes=["Testing"],
        data_categories=["Email"],
    )
    assert len(doc.sections) == 4

def test_section_titles_match_art35_7(empty_generator):
    doc = empty_generator.generate(
        system_name="TestSystem",
        system_description="Test Description",
        processing_purposes=["Testing"],
        data_categories=["Email"],
    )
    titles = [s.title for s in doc.sections]
    assert "Systematic Description of Processing" in titles
    assert "Necessity and Proportionality Assessment" in titles
    assert "Risk Assessment" in titles
    assert "Measures Envisaged" in titles

def test_boundary_disclaimer_present(empty_generator):
    doc = empty_generator.generate(
        system_name="TestSystem",
        system_description="Test",
        processing_purposes=["Test"],
        data_categories=["Test"],
    )
    assert doc.boundary_disclaimer == empty_generator.BOUNDARY_DISCLAIMER

def test_receipt_hmac_present(empty_generator):
    doc = empty_generator.generate(
        system_name="TestSystem",
        system_description="Test",
        processing_purposes=["Test"],
        data_categories=["Test"],
    )
    assert doc.receipt_hmac
    assert len(doc.receipt_hmac) == 64

def test_fria_addendum_present_when_requested(empty_generator):
    doc = empty_generator.generate(
        system_name="TestSystem",
        system_description="Test",
        processing_purposes=["Test"],
        data_categories=["Test"],
        include_fria=True,
    )
    assert doc.fria_addendum is not None
    assert "AI Act Art. 27" in doc.fria_addendum

def test_fria_addendum_absent_when_not_requested(empty_generator):
    doc = empty_generator.generate(
        system_name="TestSystem",
        system_description="Test",
        processing_purposes=["Test"],
        data_categories=["Test"],
        include_fria=False,
    )
    assert doc.fria_addendum is None

def test_detect_triggers_returns_list(empty_generator):
    triggers = empty_generator.detect_art35_triggers()
    assert isinstance(triggers, list)

def test_detect_triggers_solely_automated_from_gate_store(generator):
    triggers = generator.detect_art35_triggers()
    assert len(triggers) > 0
    assert any("solely_automated_decisions" in t for t in triggers)

def test_art35_trigger_in_document_when_detected(generator):
    doc = generator.generate(
        system_name="TestSystem",
        system_description="Test",
        processing_purposes=["Test"],
        data_categories=["Test"],
    )
    assert len(doc.art35_triggers) > 0
    assert any("solely_automated_decisions" in t for t in doc.art35_triggers)

def test_export_markdown_writes_file(empty_generator, tmp_store):
    doc = empty_generator.generate(
        system_name="TestSystem",
        system_description="Test",
        processing_purposes=["Test"],
        data_categories=["Test"],
        include_fria=True
    )
    out_file = tmp_store / "dpia.md"
    empty_generator.export(doc, out_file, format="markdown")
    assert out_file.exists()
    
    content = out_file.read_text(encoding="utf-8")
    assert "DPIA — TestSystem" in content
    assert "FRIA Addendum" in content

def test_export_json_writes_valid_json(empty_generator, tmp_store):
    doc = empty_generator.generate(
        system_name="TestSystem",
        system_description="Test",
        processing_purposes=["Test"],
        data_categories=["Test"],
    )
    out_file = tmp_store / "dpia.json"
    empty_generator.export(doc, out_file, format="json")
    assert out_file.exists()
    
    with open(out_file) as f:
        data = json.load(f)
    assert data["dpia_id"] == doc.dpia_id
    assert len(data["sections"]) == 4

def test_generate_with_no_primitives_works(empty_generator):
    doc = empty_generator.generate(
        system_name="Sys",
        system_description="Desc",
        processing_purposes=["P"],
        data_categories=["D"],
    )
    assert doc.dpia_id is not None
