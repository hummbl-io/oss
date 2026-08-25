#!/usr/bin/env python3
"""Portable conformance test runner for HUMMBL tuples.

Loads test vectors from conformance/test_vectors.jsonl and validates each
against the corresponding schema in schemas/. Reports pass/fail per vector.

This is repo-agnostic — downstream implementations can copy this script
and the test_vectors.jsonl file to self-verify.

Stdlib-only. Exit 0 if all vectors match expected results, 1 otherwise.

Usage:
    python conformance/run_conformance.py
    python conformance/run_conformance.py --verbose
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# This script is designed to be portable. It assumes:
# - schemas/ directory with *.schema.json files
# - conformance/test_vectors.jsonl with test vectors
# When copying to a downstream repo, adjust REPO_ROOT accordingly.

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMAS_DIR = REPO_ROOT / "schemas"
VECTORS_FILE = Path(__file__).resolve().parent / "test_vectors.jsonl"


def _load_vectors() -> list[dict[str, Any]]:
    """Load test vectors from JSONL file."""
    vectors = []
    with VECTORS_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                vectors.append(json.loads(line))
    return vectors


def _load_schema(tuple_type: str) -> dict[str, Any] | None:
    """Find and load the schema for a given tuple_type."""
    for p in SCHEMAS_DIR.glob("*.schema.json"):
        with p.open("r", encoding="utf-8") as f:
            schema = json.load(f)
        props = schema.get("properties", {})
        tt = props.get("tuple_type", {})
        if isinstance(tt, dict) and tt.get("const") == tuple_type:
            return schema
    return None


def _validate_basic(tuple: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    """Basic validation — checks required fields, const, enum, additionalProperties.

    This is a minimal validator. For full validation, use the repo's
    reference_impl/validate_examples.py.
    """
    violations: list[str] = []

    # Check required fields
    required = schema.get("required", [])
    for field in required:
        if field not in tuple:
            violations.append("required")

    # Check tuple_type const
    props = schema.get("properties", {})
    tt_schema = props.get("tuple_type", {})
    if isinstance(tt_schema, dict) and "const" in tt_schema:
        if tuple.get("tuple_type") != tt_schema["const"]:
            violations.append("const")

    # Check additionalProperties
    if schema.get("additionalProperties") is False:
        allowed = set(props.keys())
        for key in tuple:
            if key not in allowed:
                violations.append("additionalProperties")
                break

    # Check enum values
    for field_name, field_schema in props.items():
        if isinstance(field_schema, dict) and "enum" in field_schema:
            val = tuple.get(field_name)
            if val is not None and val not in field_schema["enum"]:
                violations.append("enum")
                break

    # Check minimum
    for field_name, field_schema in props.items():
        if isinstance(field_schema, dict) and "minimum" in field_schema:
            val = tuple.get(field_name)
            if isinstance(val, (int, float)) and val < field_schema["minimum"]:
                violations.append("minimum")
                break

    return violations


def run_conformance(verbose: bool = False) -> tuple[int, int, int]:
    """Run conformance tests. Returns (passed, failed, total)."""
    vectors = _load_vectors()
    passed = 0
    failed = 0

    for vector in vectors:
        vector_id = vector["vector_id"]
        tuple_type = vector["tuple_type"]
        input_tuple = vector["input"]
        expected = vector["expected_result"]
        expected_violations = set(vector.get("expected_violations", []))
        description = vector.get("description", "")

        schema = _load_schema(tuple_type)
        if schema is None:
            if verbose:
                print(f"  [SKIP] {vector_id}: no schema found for tuple_type={tuple_type}")
            continue

        actual_violations = set(_validate_basic(input_tuple, schema))
        actual_result = "valid" if len(actual_violations) == 0 else "invalid"

        if actual_result == expected:
            # For invalid results, also check that expected violations are detected
            if expected == "invalid" and expected_violations:
                if not expected_violations.issubset(actual_violations):
                    if verbose:
                        print(f"  [FAIL] {vector_id}: expected violations {expected_violations} not subset of {actual_violations}")
                    failed += 1
                    continue
            passed += 1
            if verbose:
                print(f"  [PASS] {vector_id}: {description}")
        else:
            failed += 1
            if verbose:
                print(f"  [FAIL] {vector_id}: expected={expected} actual={actual_result} violations={actual_violations}")
                print(f"         {description}")

    return passed, failed, len(vectors)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verbose", action="store_true", help="Print per-vector results")
    args = parser.parse_args(argv)

    passed, failed, total = run_conformance(verbose=args.verbose)
    print(f"Conformance: {passed}/{total} passed, {failed} failed")
    return 1 if failed > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
