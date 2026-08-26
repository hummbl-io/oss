#!/usr/bin/env python3
"""
HUMMBL Rubric Template Validator

Validates rubric templates against the master schema to ensure:
- YAML syntax validity
- Required field presence
- Weight sum validation
- Scoring anchor completeness
- Hard gate configuration validity
"""

import sys
import yaml
from pathlib import Path
from typing import Dict, Any, List, Tuple


def load_yaml_file(file_path: Path) -> Dict[str, Any]:
    """Load and parse a YAML file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"ERROR: Invalid YAML in {file_path}: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"ERROR: File not found: {file_path}")
        sys.exit(1)


def validate_parameters(template: Dict[str, Any]) -> List[str]:
    """Validate template parameters."""
    errors = []
    
    if 'parameters' not in template:
        errors.append("Missing 'parameters' section")
        return errors
    
    params = template['parameters']
    required_params = [
        'context_name',
        'framework_reference',
        'evaluation_scope',
        'artifact_types'
    ]
    
    for param in required_params:
        if param not in params:
            errors.append(f"Missing required parameter: {param}")
    
    # Validate evaluation_scope enum
    valid_scopes = ['single_document', 'multi_phase', 'fleet_wide', 'cross_repo']
    if 'evaluation_scope' in params and params['evaluation_scope'] not in valid_scopes:
        errors.append(f"Invalid evaluation_scope: {params['evaluation_scope']}. Must be one of {valid_scopes}")
    
    return errors


def validate_hard_gates(template: Dict[str, Any]) -> List[str]:
    """Validate hard gate configuration."""
    errors = []
    
    if 'hard_gates' not in template:
        errors.append("Missing 'hard_gates' section")
        return errors
    
    gates = template['hard_gates']
    required_gate_fields = ['fail_condition', 'max_score_if_failed', 'severity']
    valid_severities = ['critical', 'high', 'medium', 'low']
    
    for gate_name, gate_config in gates.items():
        for field in required_gate_fields:
            if field not in gate_config:
                errors.append(f"Hard gate '{gate_name}' missing required field: {field}")
        
        if 'severity' in gate_config and gate_config['severity'] not in valid_severities:
            errors.append(f"Hard gate '{gate_name}' has invalid severity: {gate_config['severity']}")
        
        if 'max_score_if_failed' in gate_config:
            max_score = gate_config['max_score_if_failed']
            if not isinstance(max_score, int) or max_score < 0 or max_score > 100:
                errors.append(f"Hard gate '{gate_name}' has invalid max_score_if_failed: {max_score}")
    
    return errors


def validate_weighted_dimensions(template: Dict[str, Any]) -> List[str]:
    """Validate weighted dimension configuration."""
    errors = []
    
    if 'weighted_dimensions' not in template:
        errors.append("Missing 'weighted_dimensions' section")
        return errors
    
    dimensions = template['weighted_dimensions']
    required_dim_fields = ['weight', 'description', 'scoring_anchors']
    
    total_weight = 0
    
    for dim_name, dim_config in dimensions.items():
        for field in required_dim_fields:
            if field not in dim_config:
                errors.append(f"Dimension '{dim_name}' missing required field: {field}")
        
        if 'weight' in dim_config:
            weight = dim_config['weight']
            if not isinstance(weight, int) or weight < 0 or weight > 100:
                errors.append(f"Dimension '{dim_name}' has invalid weight: {weight}")
            else:
                total_weight += weight
        
        if 'scoring_anchors' in dim_config:
            anchors = dim_config['scoring_anchors']
            if not isinstance(anchors, dict) or len(anchors) == 0:
                errors.append(f"Dimension '{dim_name}' has invalid scoring_anchors: must be non-empty dict")
    
    if total_weight != 100:
        errors.append(f"Total weight sum is {total_weight}, must equal 100")
    
    return errors


def validate_required_outputs(template: Dict[str, Any]) -> List[str]:
    """Validate required outputs configuration."""
    errors = []
    
    if 'required_outputs' not in template:
        errors.append("Missing 'required_outputs' section")
        return errors
    
    outputs = template['required_outputs']
    required_outputs = [
        'numeric_score',
        'hard_gate_status',
        'weighted_breakdown',
        'top_3_strengths',
        'top_3_weaknesses',
        'score_caps_triggered',
        'next_validation_test',
        'limitations'
    ]
    
    for output in required_outputs:
        if output not in outputs:
            errors.append(f"Missing required output: {output}")
    
    return errors


def validate_template(file_path: Path) -> Tuple[bool, List[str]]:
    """Validate a template file against the master schema."""
    print(f"Validating {file_path}...")
    
    template = load_yaml_file(file_path)
    all_errors = []
    
    # Validate each section
    all_errors.extend(validate_parameters(template))
    all_errors.extend(validate_hard_gates(template))
    all_errors.extend(validate_weighted_dimensions(template))
    all_errors.extend(validate_required_outputs(template))
    
    return len(all_errors) == 0, all_errors


def main():
    """Main validation function."""
    if len(sys.argv) < 2:
        print("Usage: python validate-template.py <template_file.yaml>")
        print("   or: python validate-template.py --all")
        sys.exit(1)
    
    repo_root = Path(__file__).parent.parent
    templates_dir = repo_root / 'templates'
    
    if sys.argv[1] == '--all':
        # Validate all templates
        template_files = list(templates_dir.glob('*.yaml'))
        if not template_files:
            print(f"No template files found in {templates_dir}")
            sys.exit(1)
        
        all_valid = True
        for template_file in template_files:
            is_valid, errors = validate_template(template_file)
            if not is_valid:
                all_valid = False
                print(f"  VALIDATION FAILED:")
                for error in errors:
                    print(f"    - {error}")
            else:
                print(f"  VALIDATION PASSED")
        
        if all_valid:
            print("\nAll templates validated successfully!")
            sys.exit(0)
        else:
            print("\nSome templates failed validation")
            sys.exit(1)
    else:
        # Validate single template
        template_file = Path(sys.argv[1])
        if not template_file.exists():
            print(f"ERROR: Template file not found: {template_file}")
            sys.exit(1)
        
        is_valid, errors = validate_template(template_file)
        
        if not is_valid:
            print("VALIDATION FAILED:")
            for error in errors:
                print(f"  - {error}")
            sys.exit(1)
        else:
            print("VALIDATION PASSED")
            sys.exit(0)


if __name__ == '__main__':
    main()
