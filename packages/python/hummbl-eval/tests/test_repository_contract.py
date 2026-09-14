import json
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]


class RepositoryContractTests(unittest.TestCase):
    def test_canonical_schemas_are_draft_2020_12_and_versioned(self) -> None:
        paths = sorted((ROOT / "schemas").glob("*.schema.json"))
        self.assertGreaterEqual(len(paths), 3)
        for path in paths:
            with self.subTest(schema=path.name):
                value = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(value["$schema"], "https://json-schema.org/draft/2020-12/schema")
                self.assertIn("$id", value)
                self.assertIn("required", value)
                self.assertFalse(value.get("additionalProperties", True))

    def test_project_license_and_policy_are_machine_readable(self) -> None:
        project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        # oss convention: MIT OR Apache-2.0 dual-licensed
        self.assertEqual(project["project"]["license"], {"text": "MIT OR Apache-2.0"})
        self.assertTrue((ROOT / "LICENSE").is_file())


if __name__ == "__main__":
    unittest.main()
