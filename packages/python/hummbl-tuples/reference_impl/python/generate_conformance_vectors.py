"""
Generate canonical JSON and hashes for cross-language conformance testing.

Output is a JSONL file with one line per test case:
  {"name": "...", "canonical_json": "...", "content_hash": "..."}

The TypeScript conformance test reads this file and verifies byte-identical output.

Run: python reference_impl/python/generate_conformance_vectors.py
"""

import json
import sys
from pathlib import Path

# Add parent dir to path for import
sys.path.insert(0, str(Path(__file__).parent))
from canonical_serialization import canonical_hash, canonical_json


def content_hash(d: dict) -> str:
    """SHA-256 content hash excluding integrity-layer fields."""
    return canonical_hash(d)


# Same test cases as the TypeScript conformance_test.ts
test_cases = [
    {
        "name": "minimal contract tuple",
        "tuple": {
            "tuple_type": "CONTRACT",
            "id": "00000000-0000-0000-0000-000000000001",
            "time": "2026-01-01T00:00:00Z",
            "tuple_data": {
                "contract_id": "ctr-001",
                "scope": "test-scope",
                "constraints": {"max_cost": 100, "max_duration": 3600},
            },
        },
    },
    {
        "name": "tuple with float values",
        "tuple": {
            "tuple_type": "EVIDENCE",
            "id": "00000000-0000-0000-0000-000000000002",
            "time": "2026-01-01T00:00:01Z",
            "tuple_data": {
                "drift": 0.75,
                "confidence": 0.5,
                "agent": "test-agent",
            },
        },
    },
    {
        "name": "tuple with non-ASCII text",
        "tuple": {
            "tuple_type": "SYSTEM",
            "id": "00000000-0000-0000-0000-000000000003",
            "time": "2026-01-01T00:00:02Z",
            "tuple_data": {
                "event": "startup",
                "notes": "café — naïve résumé",
                "agent": "test-agent",
            },
        },
    },
    {
        "name": "tuple with nested objects and arrays",
        "tuple": {
            "tuple_type": "MODEL_SELECTED",
            "id": "00000000-0000-0000-0000-000000000004",
            "time": "2026-01-01T00:00:03Z",
            "tuple_data": {
                "selection_rationale": "best fit",
                "alternatives_considered": ["model-a", "model-b", "model-c"],
                "metadata": {"tier": 1, "tags": ["fast", "cheap"]},
            },
        },
    },
    {
        "name": "tuple with null values (should be omitted)",
        "tuple": {
            "tuple_type": "EVIDENCE",
            "id": "00000000-0000-0000-0000-000000000005",
            "time": "2026-01-01T00:00:04Z",
            "tuple_data": {
                "agent": "test-agent",
                "notes": None,
                "required_field": "present",
            },
        },
    },
    {
        "name": "tuple with integrity fields (should be excluded from hash)",
        "tuple": {
            "tuple_type": "EVIDENCE",
            "id": "00000000-0000-0000-0000-000000000006",
            "time": "2026-01-01T00:00:05Z",
            "tuple_data": {
                "agent": "test-agent",
                "previous_hash": "abc123",
                "args_hash": "def456",
                "signature": "sig789",
            },
        },
    },
]


def main():
    output_path = Path(__file__).parent.parent / "conformance_vectors.jsonl"
    with output_path.open("w", encoding="utf-8") as f:
        for tc in test_cases:
            # Remove None values at top level (Python dict)
            clean_tuple = {}
            for k, v in tc["tuple"].items():
                if v is None:
                    continue
                if isinstance(v, dict):
                    clean_v = {dk: dv for dk, dv in v.items() if dv is not None}
                    clean_tuple[k] = clean_v
                else:
                    clean_tuple[k] = v

            cj = canonical_json(clean_tuple)
            ch = content_hash(clean_tuple)
            result = {"name": tc["name"], "canonical_json": cj, "content_hash": ch}
            f.write(json.dumps(result, ensure_ascii=False) + "\n")
            print(f"PASS: {tc['name']}")
            print(f"  canonical: {cj}")
            print(f"  hash:      {ch}")

    print(f"\nWrote {len(test_cases)} vectors to {output_path}")


if __name__ == "__main__":
    main()
