from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.check_codeql_sarif import summarize_sarif


class CheckCodeQLSarifTests(unittest.TestCase):
    def test_clean_sarif_has_no_findings(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "python.sarif").write_text(
                json.dumps({"runs": [{"results": []}]}),
                encoding="utf-8",
            )

            file_count, rule_counts = summarize_sarif(Path(directory))

        self.assertEqual(file_count, 1)
        self.assertEqual(rule_counts, {})

    def test_findings_are_counted_by_rule_without_messages(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "python.sarif").write_text(
                json.dumps(
                    {
                        "runs": [
                            {
                                "results": [
                                    {"ruleId": "py/example-a", "message": {"text": "hidden"}},
                                    {"ruleId": "py/example-a", "message": {"text": "hidden"}},
                                    {"ruleId": "py/example-b", "message": {"text": "hidden"}},
                                ]
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            file_count, rule_counts = summarize_sarif(Path(directory))

        self.assertEqual(file_count, 1)
        self.assertEqual(rule_counts, {"py/example-a": 2, "py/example-b": 1})

    def test_missing_sarif_is_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(FileNotFoundError):
                summarize_sarif(Path(directory))


if __name__ == "__main__":
    unittest.main()
