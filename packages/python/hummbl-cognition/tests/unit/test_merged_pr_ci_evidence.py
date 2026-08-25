from __future__ import annotations

from hummbl_cognition import merged_pr_ci_evidence as ci


def test_extract_ci_evidence_fails_closed_for_open_pr(monkeypatch):
    monkeypatch.setattr(
        ci,
        "_get_pr_info",
        lambda repo, pr_number, errors=None: {
            "state": "OPEN",
            "mergeCommit": None,
            "headRefOid": "abc",
            "headRefName": "branch",
            "body": "CI green",
        },
    )

    evidence = ci.extract_ci_evidence("owner/repo", 1)

    assert evidence.evidence_tier == ci.EvidenceTier.MISSING
    assert evidence.ci_status == "missing"
    assert evidence.release_recommendation == "conditional"
    assert evidence.errors


def test_declared_in_commit_tier_when_connector_evidence_missing():
    tier = ci._determine_evidence_tier([], [], "", "CI: pass")

    assert tier == ci.EvidenceTier.DECLARED_IN_COMMIT


def test_run_gh_records_errors_for_failed_command(monkeypatch):
    class Proc:
        returncode = 1
        stdout = ""
        stderr = "rate limit"

    monkeypatch.setattr(ci.subprocess, "run", lambda *args, **kwargs: Proc())
    errors: list[str] = []

    result = ci._run_gh(["api", "x"], errors=errors)

    assert result is None
    assert errors
    assert "rate limit" in errors[0]