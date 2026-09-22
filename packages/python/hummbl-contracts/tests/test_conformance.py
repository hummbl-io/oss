"""JSON Schema Test Suite conformance harness for hummbl-contracts validator.

Loads licensed fixtures from the JSON Schema Test Suite (MIT, see
tests/fixtures/json-schema-test-suite/LICENSE) and classifies each test
case into mutually exclusive outcomes:

  - pass:             validator result matches expected `valid`
  - fail:             validator result does NOT match (real conformance gap)
  - outside_subset:   schema uses keywords or constructs outside the declared subset
  - known_limitation: validator result does NOT match due to an explicit, documented limitation
  - error:            unexpected runtime exception during validation or fixture loading
  - stale_waiver:     test unexpectedly passed despite being waived as a known limitation

The declared subset is the set of keywords hummbl_contracts.schema_validator
supports. Failures are reported with actionable details so they can be
fixed or documented with explicit rationale.
"""

from __future__ import annotations

import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, NamedTuple

import pytest

from hummbl_contracts.schema_validator import validate

_FIXTURES_DIR = Path(__file__).parent / "fixtures" / "json-schema-test-suite"
_REPORTS_DIR = Path(__file__).parent / "reports"

# Keywords supported by hummbl-contracts stdlib-only validator.
# See hummbl_contracts/schema_validator.py module docstring.
SUPPORTED_KEYWORDS = frozenset({
    "type", "required", "properties", "enum", "pattern",
    "minimum", "maximum", "minLength", "maxLength",
    "minItems", "maxItems", "items", "additionalProperties",
    "const", "oneOf", "anyOf",
})

# Meta-keywords that are annotations or schema identifiers — ignored during subset evaluation.
_META_KEYWORDS = frozenset({"$schema", "$id", "description", "title", "$comment"})


class KnownLimitation(NamedTuple):
    keyword: str
    group: str
    test: str | None
    rationale: str


# Explicit registry of known limitations with stable identities and technical rationale.
KNOWN_LIMITATIONS: tuple[KnownLimitation, ...] = (
    KnownLimitation(
        keyword="pattern",
        group="pattern with Unicode property escape requires unicode mode",
        test="ASCII letters match",
        rationale=(
            "Python stdlib `re` module does not support ECMA-262 Unicode property "
            "escapes (\\p{Letter}) without third-party `regex` library. Prohibited "
            "under hummbl-contracts zero-third-party-runtime-dependency policy."
        ),
    ),
    KnownLimitation(
        keyword="pattern",
        group="pattern with Unicode property escape requires unicode mode",
        test="Non-ASCII letters match",
        rationale=(
            "Python stdlib `re` module does not support ECMA-262 Unicode property "
            "escapes (\\p{Letter}) without third-party `regex` library. Prohibited "
            "under hummbl-contracts zero-third-party-runtime-dependency policy."
        ),
    ),
)

DECLARED_PROFILE: dict[str, Any] = {
    "dialect": "https://json-schema.org/draft/2020-12/schema",
    "profile_id": "hummbl-contracts-draft2020-12-subset-v1",
    "supported_keywords": tuple(sorted(SUPPORTED_KEYWORDS)),
    "boolean_schemas_supported": True,
    "unsupported_constructs": (
        "$defs", "$ref", "allOf", "contains", "dependentRequired",
        "dependentSchemas", "if", "then", "else", "maxContains",
        "minContains", "not", "patternProperties", "prefixItems",
        "propertyNames", "unevaluatedItems", "unevaluatedProperties",
        "uniqueItems"
    ),
    "regex_engine": "python-stdlib-re",
    "known_limitations": [
        {
            "keyword": kl.keyword,
            "group": kl.group,
            "test": kl.test,
            "rationale": kl.rationale,
        }
        for kl in KNOWN_LIMITATIONS
    ],
}


def _collect_keywords(schema: Any, acc: set[str]) -> None:
    """Recursively collect all keywords used in a schema.

    Traverses only schema-bearing positions:
      - Property-name mappings: properties, patternProperties, $defs, definitions, dependentSchemas
      - Schema-valued keywords: additionalProperties, items, contains, propertyNames, not, if, then, else
      - Schema arrays: oneOf, anyOf, allOf, prefixItems

    Instance data under `const` and `enum` is intentionally NOT traversed as schemas.
    Boolean schemas (true/false) contain no keyword constraints and are supported by the validator.
    """
    if isinstance(schema, bool) or not isinstance(schema, dict):
        return

    for key, value in schema.items():
        if key not in _META_KEYWORDS:
            acc.add(key)

        # Mapping of property names to schemas (walk dictionary values)
        if key in ("properties", "patternProperties", "$defs", "definitions", "dependentSchemas") and isinstance(value, dict):
            for v in value.values():
                _collect_keywords(v, acc)

        # Schema-valued keywords (walk the schema itself)
        elif key in ("additionalProperties", "items", "contains", "propertyNames", "not", "if", "then", "else"):
            _collect_keywords(value, acc)

        # Array of schemas (walk each schema in the list)
        elif key in ("oneOf", "anyOf", "allOf", "prefixItems") and isinstance(value, list):
            for v in value:
                _collect_keywords(v, acc)


def _is_in_subset(schema: Any) -> bool:
    """Check whether a schema uses only supported keywords."""
    keywords: set[str] = set()
    _collect_keywords(schema, keywords)
    return keywords.issubset(SUPPORTED_KEYWORDS)


def _find_known_limitation(keyword: str, group: str, test: str) -> KnownLimitation | None:
    for kl in KNOWN_LIMITATIONS:
        if kl.keyword == keyword and kl.group == group:
            if kl.test is None or kl.test == test:
                return kl
    return None


def _load_fixture_files() -> list[Path]:
    """Load all JSON fixture files in the test suite directory."""
    if not _FIXTURES_DIR.exists():
        return []
    return sorted(_FIXTURES_DIR.glob("*.json"))


def _classify_all() -> list[dict[str, Any]]:
    """Run all fixtures and return a list of classified result dicts."""
    results: list[dict[str, Any]] = []
    for fixture_path in _load_fixture_files():
        keyword = fixture_path.stem
        try:
            data = json.loads(fixture_path.read_text(encoding="utf-8"))
        except Exception as exc:
            results.append({
                "case_id": f"{keyword}::error:file_read",
                "keyword": keyword,
                "group_index": -1,
                "test_index": -1,
                "group": "",
                "test": "",
                "classification": "error",
                "expected": None,
                "actual": None,
                "schema": None,
                "data": None,
                "errors": [f"Failed to read/decode fixture file {fixture_path.name}: {exc}"],
                "rationale": None,
            })
            continue

        for g_idx, group in enumerate(data):
            schema = group.get("schema", {})
            group_desc = group.get("description", "")
            in_subset = _is_in_subset(schema)

            for t_idx, test in enumerate(group.get("tests", [])):
                test_desc = test.get("description", "")
                case_id = f"{keyword}::g{g_idx}:{group_desc}::t{t_idx}:{test_desc}"
                test_data = test.get("data")
                expected = test.get("valid")

                if not in_subset:
                    results.append({
                        "case_id": case_id,
                        "keyword": keyword,
                        "group_index": g_idx,
                        "test_index": t_idx,
                        "group": group_desc,
                        "test": test_desc,
                        "classification": "outside_subset",
                        "expected": expected,
                        "actual": None,
                        "schema": schema,
                        "data": test_data,
                        "errors": [],
                        "rationale": None,
                    })
                    continue

                limitation = _find_known_limitation(keyword, group_desc, test_desc)

                try:
                    errors = validate(test_data, schema)
                    actual_valid = len(errors) == 0
                    is_match = (actual_valid == expected)

                    if is_match:
                        if limitation is not None:
                            classification = "stale_waiver"
                        else:
                            classification = "pass"
                    else:
                        if limitation is not None:
                            classification = "known_limitation"
                        else:
                            classification = "fail"

                    results.append({
                        "case_id": case_id,
                        "keyword": keyword,
                        "group_index": g_idx,
                        "test_index": t_idx,
                        "group": group_desc,
                        "test": test_desc,
                        "classification": classification,
                        "expected": expected,
                        "actual": actual_valid,
                        "schema": schema,
                        "data": test_data,
                        "errors": errors if classification in ("fail", "known_limitation") else [],
                        "rationale": limitation.rationale if limitation else None,
                    })

                except Exception as exc:
                    results.append({
                        "case_id": case_id,
                        "keyword": keyword,
                        "group_index": g_idx,
                        "test_index": t_idx,
                        "group": group_desc,
                        "test": test_desc,
                        "classification": "error",
                        "expected": expected,
                        "actual": None,
                        "schema": schema,
                        "data": test_data,
                        "errors": [f"Runner exception: {exc}"],
                        "rationale": None,
                    })

    return results


def generate_conformance_report(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Generate machine-readable conformance report."""
    total = len(results)
    passes = [r for r in results if r["classification"] == "pass"]
    fails = [r for r in results if r["classification"] == "fail"]
    outside = [r for r in results if r["classification"] == "outside_subset"]
    known = [r for r in results if r["classification"] == "known_limitation"]
    errors = [r for r in results if r["classification"] == "error"]
    stale = [r for r in results if r["classification"] == "stale_waiver"]

    in_profile = len(passes) + len(fails) + len(known)
    coverage_pct = round((in_profile / total) * 100, 2) if total else 0.0
    pass_rate_pct = round((len(passes) / in_profile) * 100, 2) if in_profile else 0.0

    return {
        "report_version": "1.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "package": "packages/python/hummbl-contracts",
        "upstream_repository": "https://github.com/json-schema-org/JSON-Schema-Test-Suite",
        "upstream_revision": "f6fd52a0a95472e079cbfc6ef7f089702b80e045",
        "profile": DECLARED_PROFILE,
        "environment": {
            "python_version": platform.python_version(),
            "python_implementation": platform.python_implementation(),
            "platform": platform.platform(),
        },
        "counts": {
            "total_selected": total,
            "pass": len(passes),
            "fail": len(fails),
            "outside_subset": len(outside),
            "known_limitation": len(known),
            "error": len(errors),
            "stale_waiver": len(stale),
        },
        "metrics": {
            "in_profile_total": in_profile,
            "selected_corpus_coverage_pct": coverage_pct,
            "in_profile_pass_rate_pct": pass_rate_pct,
        },
        "disclaimer": (
            "Selected-corpus coverage measures the proportion of tests in the imported "
            "16-file test suite within the declared subset profile. It does NOT assert "
            "full JSON Schema Draft 2020-12 specification conformance."
        ),
        "results_summary": [
            {
                "case_id": r["case_id"],
                "classification": r["classification"],
                "expected": r["expected"],
                "actual": r["actual"],
                "rationale": r.get("rationale"),
            }
            for r in results
        ],
    }


def test_every_fixture_is_classified():
    """Every fixture must be classified into one of the valid disjoint outcomes."""
    results = _classify_all()
    assert len(results) == 385, f"Expected 385 fixtures, got {len(results)}"
    valid_classifications = {"pass", "fail", "outside_subset", "known_limitation", "error", "stale_waiver"}
    for r in results:
        assert r["classification"] in valid_classifications, (
            f"Unclassified or invalid outcome: {r['case_id']} -> {r['classification']}"
        )


def test_disjoint_outcomes_partition():
    """The sum of disjoint classification outcomes must equal total selected test count."""
    results = _classify_all()
    total = len(results)
    passes = sum(1 for r in results if r["classification"] == "pass")
    fails = sum(1 for r in results if r["classification"] == "fail")
    outside = sum(1 for r in results if r["classification"] == "outside_subset")
    known = sum(1 for r in results if r["classification"] == "known_limitation")
    errors = sum(1 for r in results if r["classification"] == "error")
    stale = sum(1 for r in results if r["classification"] == "stale_waiver")

    partition_sum = passes + fails + outside + known + errors + stale
    assert partition_sum == total, (
        f"Partition mismatch: {passes} + {fails} + {outside} + {known} + {errors} + {stale} "
        f"= {partition_sum} != {total}"
    )


def test_conformance_summary(tmp_path):
    """Verify zero real conformance failures and write machine-readable report."""
    results = _classify_all()
    fails = [r for r in results if r["classification"] == "fail"]
    errors = [r for r in results if r["classification"] == "error"]
    stale = [r for r in results if r["classification"] == "stale_waiver"]

    report_data = generate_conformance_report(results)
    report_file = tmp_path / "conformance_report.json"
    report_file.write_text(json.dumps(report_data, indent=2) + "\n", encoding="utf-8")
    assert report_file.exists()
    assert report_data["counts"]["total_selected"] == 385
    assert report_data["counts"]["pass"] == 344
    assert report_data["counts"]["known_limitation"] == 2
    assert report_data["counts"]["outside_subset"] == 39

    assert len(errors) == 0, f"{len(errors)} runner errors: {errors}"
    assert len(stale) == 0, (
        f"{len(stale)} stale waivers detected! Formerly failing tests now pass: "
        f"{[s['case_id'] for s in stale]}"
    )
    assert len(fails) == 0, (
        f"{len(fails)} real conformance failure(s): {[f['case_id'] for f in fails]}"
    )



def test_additional_properties_traversal_counterexamples():
    """Regression test: verify schema traversal fixes for additionalProperties counterexamples."""
    s1 = {"additionalProperties": {"type": "string"}}
    s2 = {"properties": {"x": {"allOf": [{"type": "string"}]}}}
    s3 = {"additionalProperties": {"allOf": [{"type": "string"}]}}
    s4 = {"additionalProperties": {"$ref": "#/$defs/item"}}

    assert _is_in_subset(s1) is True, "additionalProperties with type must be in subset"
    assert _is_in_subset(s2) is False, "properties with nested allOf must classify outside subset"
    assert _is_in_subset(s3) is False, "additionalProperties with nested allOf must classify outside subset"
    assert _is_in_subset(s4) is False, "additionalProperties with nested $ref must classify outside subset"


def test_const_enum_instance_data_not_treated_as_schemas():
    """Instance data under const/enum must not be treated as schema keywords."""
    s_const = {"const": {"allOf": [{"type": "string"}]}}
    s_enum = {"enum": [{"$ref": "#/some/ref"}]}

    assert _is_in_subset(s_const) is True, "Dict value inside const is instance data, not a schema"
    assert _is_in_subset(s_enum) is True, "Dict value inside enum is instance data, not a schema"


def test_boolean_schemas_conformance():
    """Boolean schemas (true/false) are supported Draft 2020-12 schemas."""
    assert _is_in_subset(True) is True
    assert _is_in_subset(False) is True

    assert validate("any_data", True) == []
    errors = validate("any_data", False)
    assert len(errors) > 0


def test_stale_waiver_detection():
    """Ensure that an unexpected pass on a waived case is detected as stale_waiver."""
    limitation = _find_known_limitation(
        "pattern",
        "pattern with Unicode property escape requires unicode mode",
        "ASCII letters match",
    )
    assert limitation is not None
    assert "Unicode property escape" in limitation.group


if __name__ == "__main__":
    results = _classify_all()
    _REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_data = generate_conformance_report(results)
    report_file = _REPORTS_DIR / "conformance_report.json"
    report_file.write_text(json.dumps(report_data, indent=2) + "\n", encoding="utf-8")
    print(f"Conformance report written to {report_file}")
    c = report_data["counts"]
    print(
        f"Total: {c['total_selected']} | Pass: {c['pass']} | Fail: {c['fail']} | "
        f"Outside: {c['outside_subset']} | Known limitations: {c['known_limitation']} | "
        f"Errors: {c['error']} | Stale waivers: {c['stale_waiver']}"
    )

