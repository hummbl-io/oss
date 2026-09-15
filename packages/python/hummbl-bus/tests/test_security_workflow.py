from pathlib import Path

import pytest

# These tests assert on repo-root CI files that exist only in the
# standalone hummbl-bus repository layout. In the oss monorepo the
# package lives under packages/python/hummbl-bus/ and the monorepo's own
# workflows govern CI — the files are absent and these checks skip.
_WORKFLOW = Path(".github/workflows/security-evidence.yml")
_GITLEAKS = Path(".gitleaks.toml")


@pytest.mark.skipif(
    not _WORKFLOW.exists(),
    reason="standalone-repo CI file; not present in monorepo package layout",
)
def test_private_security_workflow_is_self_hosted_and_complete():
    workflow = _WORKFLOW.read_text(encoding="utf-8")
    assert "runs-on: [self-hosted, Linux]" in workflow
    assert "ubuntu-latest" not in workflow
    for control in ("gitleaks", "semgrep", "bandit", "pip-audit", "cyclonedx"):
        assert control in workflow.lower()
    assert "actions/upload-artifact" not in workflow
    assert "persist-credentials: false" in workflow


@pytest.mark.skipif(
    not _GITLEAKS.exists(),
    reason="standalone-repo config; not present in monorepo package layout",
)
def test_gitleaks_allowlist_is_limited_to_reviewed_synthetic_fixtures():
    config = _GITLEAKS.read_text(encoding="utf-8")
    assert "useDefault = true" in config
    assert "tests/test_spool" in config
    assert "tests/test_bus_writer_core" in config
    assert "tests/fixtures/conformance/hmac-v1" in config
    assert "docs/cli/index" in config
    assert "secrets\\.baseline" in config
    assert "src/" not in config
