"""JSON Schema Test Suite conformance harness for hummbl-contracts validator.

Loads licensed fixtures from the JSON Schema Test Suite (MIT, see
tests/fixtures/json-schema-test-suite/LICENSE) and classifies each test
case as:

  - pass:   validator result matches the expected `valid` field
  - fail:   validator result does NOT match (real conformance gap)
  - outside: schema uses keywords outside the declared subset

The declared subset is the set of keywords hummbl_contracts.schema_validator
supports (see its module docstring). Failures are reported with actionable
details — the test description, schema, data, expected, and actual — so they
can be fixed or documented as known limitations. This is not an inflated
conformance claim; it is an honest accounting.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from hummbl_contracts.schema_validator import validate

_FIXTURES_DIR = Path(__file__).parent / "fixtures" / "json-schema-test-suite"

# Keywords the hummbl-contracts validator supports.
# See hummbl_contracts/schema_validator.py module docstring.
SUPPORTED_KEYWORDS = frozenset({
    "type", "required", "properties", "enum", "pattern",
    "minimum", "maximum", "minLength", "maxLength",
    "minItems", "maxItems", "items", "additionalProperties",
    "const", "oneOf", "anyOf",
})

# Meta-keywords that are not validation keywords — ignored, not treated
# as unsupported.
_META_KEYWORDS = frozenset({"$schema", "description", "title", "$comment"})

# Known limitations of the stdlib-only validator. These are real JSON Schema
# requirements that Python's `re` module cannot satisfy without the `regex`
# library (which would violate the stdlib-only constraint). Each entry is
# (keyword, group_description) — matching the test suite's fields.
_KNOWN_LIMITATIONS = frozenset({
    ("pattern", "pattern with Unicode property escape requires unicode mode"),
})


def _collect_keywords(schema: Any, acc: set[str]) -> None:
    """Recursively collect all keywords used in a schema."""
    if isinstance(schema, bool):
        return  # boolean schemas are not in our subset
    if not isinstance(schema, dict):
        return
    for key, value in schema.items():
        if key not in _META_KEYWORDS:
            acc.add(key)
        # Recurse into nested schemas
        if key in ("properties", "additionalProperties") and isinstance(value, dict):
            for v in value.values():
                _collect_keywords(v, acc)
        elif key in ("items",) and isinstance(value, dict):
            _collect_keywords(value, acc)
        elif key in ("oneOf", "anyOf") and isinstance(value, list):
            for v in value:
                _collect_keywords(v, acc)


def _is_in_subset(schema: Any) -> bool:
    """Check whether a schema uses only supported keywords."""
    keywords: set[str] = set()
    _collect_keywords(schema, keywords)
    return keywords.issubset(SUPPORTED_KEYWORDS)


def _load_fixture_files() -> list[Path]:
    """Load all JSON fixture files in the test suite directory."""
    if not _FIXTURES_DIR.exists():
        return []
    return sorted(_FIXTURES_DIR.glob("*.json"))


def _classify_all() -> list[dict[str, Any]]:
    """Run all fixtures and return a list of result dicts."""
    results: list[dict[str, Any]] = []
    for fixture_path in _load_fixture_files():
        keyword = fixture_path.stem
        data = json.loads(fixture_path.read_text(encoding="utf-8"))
        for group in data:
            schema = group.get("schema", {})
            in_subset = _is_in_subset(schema)
            for test in group.get("tests", []):
                test_data = test["data"]
                expected = test["valid"]
                if not in_subset:
                    results.append({
                        "keyword": keyword,
                        "group": group.get("description", ""),
                        "test": test.get("description", ""),
                        "classification": "outside",
                        "expected": expected,
                        "actual": None,
                        "schema": schema,
                        "data": test_data,
                    })
                    continue
                errors = validate(test_data, schema)
                actual_valid = len(errors) == 0
                classification = "pass" if actual_valid == expected else "fail"
                results.append({
                    "keyword": keyword,
                    "group": group.get("description", ""),
                    "test": test.get("description", ""),
                    "classification": classification,
                    "expected": expected,
                    "actual": actual_valid,
                    "schema": schema,
                    "data": test_data,
                    "errors": errors if classification == "fail" else [],
                })
    return results


def test_every_fixture_is_classified():
    """Every fixture must be classified as pass, fail, or outside."""
    results = _classify_all()
    assert len(results) > 0, "no fixtures loaded — check fixtures directory"
    valid_classifications = {"pass", "fail", "outside"}
    for r in results:
        assert r["classification"] in valid_classifications, (
            f"unclassified: {r['keyword']}/{r['test']}"
        )


def test_conformance_summary():
    """Print a conformance summary and fail on any in-subset failures.

    Failures are real conformance gaps where the validator disagrees with
    the JSON Schema Test Suite on a schema that uses only supported keywords.
    Each failure is printed with actionable details.
    """
    results = _classify_all()
    passes = [r for r in results if r["classification"] == "pass"]
    fails = [r for r in results if r["classification"] == "fail"]
    outside = [r for r in results if r["classification"] == "outside"]

    total = len(results)
    print(f"\n{'='*60}")
    print(f"JSON Schema Test Suite Conformance Summary")
    print(f"{'='*60}")
    print(f"Total fixtures:  {total}")
    print(f"  Pass:          {len(passes)}")
    print(f"  Fail:          {len(fails)}")
    print(f"  Outside subset: {len(outside)}")
    print(f"  Coverage:      {len(passes) + len(fails)}/{total} "
          f"({(len(passes) + len(fails)) / total * 100:.1f}%) in subset")
    print(f"{'='*60}")

    if fails:
        print(f"\n--- CONFORMANCE FAILURES ({len(fails)}) ---")
        for r in fails:
            print(f"\n  [{r['keyword']}] {r['group']} > {r['test']}")
            print(f"    expected valid={r['expected']}, got valid={r['actual']}")
            print(f"    errors: {r.get('errors', [])}")
            print(f"    schema: {json.dumps(r['schema'])}")
            print(f"    data:   {json.dumps(r['data'])}")

    if outside:
        print(f"\n--- OUTSIDE SUBSET ({len(outside)}) ---")
        outside_keywords: set[str] = set()
        for r in outside:
            kw: set[str] = set()
            _collect_keywords(r["schema"], kw)
            outside_keywords.update(kw - SUPPORTED_KEYWORDS)
        print(f"  Unsupported keywords found: {sorted(outside_keywords)}")

    # Separate known limitations from real failures
    real_fails = [r for r in fails
                  if (r["keyword"], r["group"]) not in _KNOWN_LIMITATIONS]
    known = [r for r in fails
             if (r["keyword"], r["group"]) in _KNOWN_LIMITATIONS]

    if known:
        print(f"\n--- KNOWN LIMITATIONS ({len(known)}) ---")
        print("  These require features Python's `re` module does not support")
        print("  (Unicode property escapes). Fixing would require the `regex`")
        print("  library, violating the stdlib-only constraint.")
        for r in known:
            print(f"    [{r['keyword']}] {r['group']} > {r['test']}")

    # Fail only on REAL conformance failures (not known limitations)
    assert len(real_fails) == 0, (
        f"{len(real_fails)} real conformance failure(s) — see output above. "
        f"Each failure is a case where the validator disagrees with the "
        f"JSON Schema Test Suite on a schema using only supported keywords. "
        f"Fix the validator or add to _KNOWN_LIMITATIONS with justification."
    )
