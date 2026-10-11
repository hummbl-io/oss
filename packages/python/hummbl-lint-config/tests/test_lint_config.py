"""Tests for hummbl_lint_config package."""

from __future__ import annotations

import unittest
from pathlib import Path

import hummbl_lint_config


class TestLintConfig(unittest.TestCase):
    def test_get_ruff_config_path(self) -> None:
        path = hummbl_lint_config.get_ruff_config_path()
        self.assertIsInstance(path, Path)
        self.assertTrue(path.exists())
        self.assertEqual(path.name, "ruff.toml")

    def test_get_ruff_config_text(self) -> None:
        text = hummbl_lint_config.get_ruff_config_text()
        self.assertIn("target-version", text)
        self.assertIn("py311", text)
        self.assertIn("[lint]", text)


if __name__ == "__main__":
    unittest.main()
