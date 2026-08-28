"""Smoke test for hummbl-lint-config package import."""

import hummbl_lint_config


def test_package_import():
    """Package imports without error."""
    assert hummbl_lint_config is not None
