"""Public documentation regressions with synthetic negative fixtures."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from validate_ai_positions import DEFAULT_PACKAGE, POSITIONS, TOPICS, validate


class PositionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.package = Path(self.tmp.name)
        self.write(
            "sources.json",
            [
                {
                    "id": "S1",
                    "title": "Example publication",
                    "kind": "primary",
                    "urls": ["https://example.org/paper"],
                    "accessed_on": "2026-01-01",
                    "observation": "Attributed result",
                    "limitation": "Not independently replicated",
                }
            ],
        )
        self.write(
            "claims.json",
            {
                "schema_version": "1.0",
                "status": "proposed_canonical_baseline",
                "claims": [
                    {
                        "id": f"C{n}",
                        "position_id": position,
                        "claim": "Example bounded statement",
                        "evidence_class": "attribution",
                        "disposition": "attributed",
                        "limitation": "Selected evidence",
                        "revision_trigger": "New evidence",
                        "source_ids": ["S1"],
                        "topics": sorted(TOPICS),
                        "as_of": "2026-01-01",
                    }
                    for n, position in enumerate(sorted(POSITIONS))
                ],
            },
        )
        self.write(
            "economics.json",
            {
                "status": "illustrative_not_observed",
                "assumptions": {
                    "collection_fraction": 0.1,
                    "labor_rate_per_hour": 50,
                    "target_margin": 0.2,
                },
                "scenarios": [
                    {
                        "name": "Example",
                        "price": 1000,
                        "variable_cost": 100,
                        "labor_hours": 10,
                        "expected_contribution": 300,
                        "expected_max_hours": 12,
                    }
                ],
            },
        )
        (self.package / "README.md").write_text(
            "\n".join(f"## {p} — Example" for p in sorted(POSITIONS)), encoding="utf-8"
        )

    def write(self, name, value):
        (self.package / name).write_text(json.dumps(value, indent=2), encoding="utf-8")

    def mutate(self, name, change):
        value = json.loads((self.package / name).read_text())
        change(value)
        self.write(name, value)

    def defect(self, prefix):
        self.assertTrue(
            any(e.startswith(prefix) for e in validate(self.package)), prefix
        )

    def test_public_package(self):
        self.assertEqual(validate(DEFAULT_PACKAGE), [])

    def test_synthetic_baseline(self):
        self.assertEqual(validate(self.package), [])

    def test_unresolved_reference(self):
        self.mutate(
            "claims.json", lambda v: v["claims"][0].update(source_ids=["absent"])
        )
        self.defect("REFERENCE")

    def test_duplicate_reference(self):
        self.mutate(
            "claims.json", lambda v: v["claims"][0].update(source_ids=["S1", "S1"])
        )
        self.defect("REFERENCE")

    def test_duplicate_identity(self):
        self.mutate("sources.json", lambda v: v.append(v[0]))
        self.defect("IDENTITY")

    def test_missing_topic(self):
        self.mutate(
            "claims.json", lambda v: [c.update(topics=["RSI"]) for c in v["claims"]]
        )
        self.defect("COVERAGE")

    def test_missing_position(self):
        self.mutate("claims.json", lambda v: v["claims"].pop())
        self.defect("COVERAGE")

    def test_unreviewed_promotion(self):
        self.mutate("claims.json", lambda v: v.update(status="adopted"))
        self.defect("STATUS")

    def test_future_access(self):
        self.mutate("sources.json", lambda v: v[0].update(accessed_on="9999-01-01"))
        self.defect("DATE")

    def test_malformed_url(self):
        self.mutate("sources.json", lambda v: v[0].update(urls=["https://[broken"]))
        self.defect("URL")

    def test_no_public_citation(self):
        self.mutate("sources.json", lambda v: v[0].update(urls=[]))
        self.defect("URL")

    def test_missing_limitation(self):
        self.mutate("sources.json", lambda v: v[0].update(limitation=""))
        self.defect("SOURCE")

    def test_invalid_json(self):
        (self.package / "claims.json").write_text("{")
        self.defect("JSON")

    def test_malformed_claim_fields(self):
        self.mutate(
            "claims.json",
            lambda v: v["claims"][0].update(
                disposition=[], position_id={}, topics=[{}], source_ids=[None]
            ),
        )
        self.defect("CLAIM")

    def test_empty_scenarios(self):
        self.mutate("economics.json", lambda v: v.update(scenarios=[]))
        self.defect("SHAPE")

    def test_false_profit(self):
        self.mutate(
            "economics.json",
            lambda v: v["scenarios"][0].update(expected_contribution=9999),
        )
        self.defect("ECONOMICS")

    def test_boolean_is_not_price(self):
        self.mutate("economics.json", lambda v: v["scenarios"][0].update(price=True))
        self.defect("ECONOMICS")

    def test_duplicate_scenario(self):
        self.mutate(
            "economics.json", lambda v: v["scenarios"].append(v["scenarios"][0])
        )
        self.defect("ECONOMICS")

    def test_missing_link(self):
        with (self.package / "README.md").open("a") as f:
            f.write("\n[missing](absent.md)\n")
        self.defect("LINK")

    def test_missing_anchor(self):
        with (self.package / "README.md").open("a") as f:
            f.write("\n[missing](#absent)\n")
        self.defect("ANCHOR")

    def test_invalid_markdown_url(self):
        with (self.package / "README.md").open("a") as f:
            f.write("\n[bad](https://[broken)\n")
        self.defect("LINK")

    def test_inline_example_not_link(self):
        with (self.package / "README.md").open("a") as f:
            f.write("\n`[example](absent.md)`\n")
        self.assertEqual(validate(self.package), [])

    def test_metadata_assignment(self):
        self.write("extra.json", {"hostname": "example-machine"})
        self.defect("PUBLIC")

    def test_synthetic_user_path(self):
        components = ("", "home", "example", "notes")
        self.write("extra.json", {"location": "/".join(components)})
        self.defect("PUBLIC")

    def test_technical_words_allowed(self):
        with (self.package / "README.md").open("a") as f:
            f.write("\nAn operator composes functions; a host serves models.\n")
        self.assertEqual(validate(self.package), [])


if __name__ == "__main__":
    unittest.main()
