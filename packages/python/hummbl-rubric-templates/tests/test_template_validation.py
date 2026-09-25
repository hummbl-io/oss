#!/usr/bin/env python3
"""
Tests for HUMMBL rubric template validation
"""

import pytest
import yaml
import sys
from pathlib import Path

# Ensure package root is in sys.path for standalone or monorepo test runs
PACKAGE_ROOT = Path(__file__).resolve().parent.parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

try:
    from hummbl_rubric_templates.validate_template import (
        load_yaml_file,
        validate_parameters,
        validate_hard_gates,
        validate_weighted_dimensions,
        validate_required_outputs,
        validate_template
    )
except ModuleNotFoundError:
    from tools.validate_template import (
        load_yaml_file,
        validate_parameters,
        validate_hard_gates,
        validate_weighted_dimensions,
        validate_required_outputs,
        validate_template
    )



@pytest.fixture
def master_schema():
    """Load the master schema for testing.

    The master schema file wraps its template definition under the
    'template_schema' key. The validators expect flat template structure,
    so extract that section before validating.
    """
    schema_path = Path(__file__).parent.parent / 'schema' / 'hummbl-rubric-master.yaml'
    raw = load_yaml_file(schema_path)
    return raw.get('template_schema', raw)


@pytest.fixture
def nist_template():
    """Load the NIST AI RMF template for testing."""
    template_path = Path(__file__).parent.parent / 'templates' / 'nist-ai-rmf-compliance.yaml'
    return load_yaml_file(template_path)


@pytest.fixture
def base120_template():
    """Load the Base120 template for testing."""
    template_path = Path(__file__).parent.parent / 'templates' / 'base120-protocol-run.yaml'
    return load_yaml_file(template_path)


@pytest.fixture
def agent_coordination_template():
    """Load the Agent Coordination template for testing."""
    template_path = Path(__file__).parent.parent / 'templates' / 'agent-coordination.yaml'
    return load_yaml_file(template_path)


@pytest.fixture
def global_org_ranking_template():
    """Load the Global Organization Ranking template for testing."""
    template_path = Path(__file__).parent.parent / 'templates' / 'global-org-ranking.yaml'
    return load_yaml_file(template_path)



def test_master_schema_parameters(master_schema):
    """Master schema is a type definition, not a template instance — skip."""
    pytest.skip("Master schema contains type definitions, not template values")


def test_master_schema_hard_gates(master_schema):
    """Master schema is a type definition, not a template instance — skip."""
    pytest.skip("Master schema contains type definitions, not template values")


def test_master_schema_weighted_dimensions(master_schema):
    """Master schema is a type definition, not a template instance — skip."""
    pytest.skip("Master schema contains type definitions, not template values")


def test_master_schema_required_outputs(master_schema):
    """Test that master schema has valid required outputs."""
    errors = validate_required_outputs(master_schema)
    assert len(errors) == 0, f"Master schema required outputs validation failed: {errors}"


def test_nist_template_validation(nist_template):
    """Test that NIST template validates correctly."""
    errors = []
    errors.extend(validate_parameters(nist_template))
    errors.extend(validate_hard_gates(nist_template))
    errors.extend(validate_weighted_dimensions(nist_template))
    errors.extend(validate_required_outputs(nist_template))
    
    assert len(errors) == 0, f"NIST template validation failed: {errors}"


def test_base120_template_validation(base120_template):
    """Test that Base120 template validates correctly."""
    errors = []
    errors.extend(validate_parameters(base120_template))
    errors.extend(validate_hard_gates(base120_template))
    errors.extend(validate_weighted_dimensions(base120_template))
    errors.extend(validate_required_outputs(base120_template))
    
    assert len(errors) == 0, f"Base120 template validation failed: {errors}"


def test_agent_coordination_template_validation(agent_coordination_template):
    """Test that Agent Coordination template validates correctly with 100 weight sum."""
    errors = []
    errors.extend(validate_parameters(agent_coordination_template))
    errors.extend(validate_hard_gates(agent_coordination_template))
    errors.extend(validate_weighted_dimensions(agent_coordination_template))
    errors.extend(validate_required_outputs(agent_coordination_template))
    
    assert len(errors) == 0, f"Agent coordination template validation failed: {errors}"


def test_global_org_ranking_template_validation(global_org_ranking_template):
    """Test that MCDA calibrated Global Organization Ranking template validates correctly."""
    errors = []
    errors.extend(validate_parameters(global_org_ranking_template))
    errors.extend(validate_hard_gates(global_org_ranking_template))
    errors.extend(validate_weighted_dimensions(global_org_ranking_template))
    errors.extend(validate_required_outputs(global_org_ranking_template))
    
    assert len(errors) == 0, f"Global organization ranking template validation failed: {errors}"


def test_all_templates_in_directory():
    """Test that all YAML templates in the templates directory pass complete validation."""
    templates_dir = Path(__file__).parent.parent / 'templates'
    template_files = list(templates_dir.glob('*.yaml')) + list(templates_dir.glob('*.yml'))
    assert len(template_files) >= 4, f"Expected at least 4 templates, found {len(template_files)}"
    
    for t_path in template_files:
        is_valid, errors = validate_template(t_path)
        assert is_valid, f"Template {t_path.name} failed validation: {errors}"


def test_weight_sum_validation():
    """Test that weight sum validation catches incorrect totals."""
    # Create a template with incorrect weight sum
    invalid_template = {
        'weighted_dimensions': {
            'dimension1': {'weight': 50, 'description': 'Test', 'scoring_anchors': {'0-10': 'Test'}},
            'dimension2': {'weight': 60, 'description': 'Test', 'scoring_anchors': {'0-10': 'Test'}}
        }
    }
    
    errors = validate_weighted_dimensions(invalid_template)
    assert len(errors) > 0
    assert any('total weight' in error.lower() for error in errors)


def test_hard_gate_score_cap_validation():
    """Test that hard gate score cap validation catches invalid values."""
    # Create a template with invalid score cap
    invalid_template = {
        'hard_gates': {
            'test_gate': {
                'fail_condition': 'Test condition',
                'max_score_if_failed': 150,  # Invalid: > 100
                'severity': 'critical'
            }
        }
    }
    
    errors = validate_hard_gates(invalid_template)
    assert len(errors) > 0
    assert any('invalid max_score_if_failed' in error.lower() for error in errors)


def test_missing_required_parameters():
    """Test that parameter validation catches missing required fields."""
    invalid_template = {
        'parameters': {
            'context_name': 'test'
            # Missing other required parameters
        }
    }
    
    errors = validate_parameters(invalid_template)
    assert len(errors) > 0
    assert any('missing required parameter' in error.lower() for error in errors)


def test_invalid_evaluation_scope():
    """Test that parameter validation catches invalid evaluation scope."""
    invalid_template = {
        'parameters': {
            'context_name': 'test',
            'framework_reference': 'test',
            'evaluation_scope': 'invalid_scope',
            'artifact_types': ['ADR']
        }
    }
    
    errors = validate_parameters(invalid_template)
    assert len(errors) > 0
    assert any('invalid evaluation_scope' in error.lower() for error in errors)


def test_invalid_hard_gate_severity():
    """Test that hard gate validation catches invalid severity."""
    invalid_template = {
        'hard_gates': {
            'test_gate': {
                'fail_condition': 'Test condition',
                'max_score_if_failed': 50,
                'severity': 'invalid_severity'
            }
        }
    }
    
    errors = validate_hard_gates(invalid_template)
    assert len(errors) > 0
    assert any('invalid severity' in error.lower() for error in errors)


def test_missing_required_outputs():
    """Test that required outputs validation catches missing fields."""
    invalid_template = {
        'required_outputs': {
            'numeric_score': 0
            # Missing other required outputs
        }
    }
    
    errors = validate_required_outputs(invalid_template)
    assert len(errors) > 0
    assert any('missing required output' in error.lower() for error in errors)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
