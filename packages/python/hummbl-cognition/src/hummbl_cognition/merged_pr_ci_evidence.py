"""Merged-PR CI evidence extractor for release-gate reviews.

Extracts CI/check evidence for merged PRs and maps that evidence into
release-gate fields. This closes the gap where release-gate reviews
fall back to PR-body or commit-message CI claims when GitHub Actions
workflow-run lookup returns no runs for selected merge SHAs.

Evidence tiers:
  - connector_verified: CI status extracted from GitHub Actions or
    check suites API
  - declared_in_pr: CI status claimed in PR body but not independently
    verified
  - declared_in_commit: CI status claimed in commit message but not
    independently verified
  - missing: no CI evidence found
  - inconclusive: evidence found but status/conclusion is ambiguous

Design:
  - Pure stdlib (subprocess, json, dataclasses, pathlib)
  - Uses `gh` CLI for API access (consistent with github_adapter.py)
  - No side effects — read-only extraction and mapping
  - Machine-readable output suitable for 4 PM Transformation Trace review

Reference: issue #1113
"""

from __future__ import annotations

import json
import logging
import subprocess
from dataclasses import dataclass, field
from typing import Any

__all__ = [
    "CIEvidence",
    "MergedPREvidence",
    "EvidenceTier",
    "extract_ci_evidence",
    "extract_batch",
]

logger = logging.getLogger(__name__)


class EvidenceTier(str):
    """Evidence quality tier for CI status."""

    CONNECTOR_VERIFIED = "connector_verified"
    DECLARED_IN_PR = "declared_in_pr"
    DECLARED_IN_COMMIT = "declared_in_commit"
    MISSING = "missing"
    INCONCLUSIVE = "inconclusive"


@dataclass
class CIEvidence:
    """CI evidence for a single workflow run or check suite."""

    source: str  # "workflow_run" or "check_suite"
    workflow_name: str = ""
    run_url: str = ""
    status: str = ""  # queued, in_progress, completed
    conclusion: str = ""  # success, failure, cancelled, skipped, action_required
    head_sha: str = ""
    started_at: str = ""
    completed_at: str = ""
    lookup_method: str = ""  # how this evidence was found

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "workflow_name": self.workflow_name,
            "run_url": self.run_url,
            "status": self.status,
            "conclusion": self.conclusion,
            "head_sha": self.head_sha,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "lookup_method": self.lookup_method,
        }


@dataclass
class MergedPREvidence:
    """Full CI evidence record for a merged PR."""

    repo: str
    pr_number: int
    merge_commit_sha: str = ""
    head_sha: str = ""
    branch_name: str = ""
    evidence_tier: str = EvidenceTier.MISSING
    ci_evidence: list[CIEvidence] = field(default_factory=list)
    ci_status: str = ""  # mapped release-gate field
    deployment_status: str = ""
    rollback_or_migration_risk: str = ""
    required_human_approval: bool = False
    release_recommendation: str = ""  # go, no-go, conditional
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "repo": self.repo,
            "pr_number": self.pr_number,
            "merge_commit_sha": self.merge_commit_sha,
            "head_sha": self.head_sha,
            "branch_name": self.branch_name,
            "evidence_tier": self.evidence_tier,
            "ci_evidence": [e.to_dict() for e in self.ci_evidence],
            "ci_status": self.ci_status,
            "deployment_status": self.deployment_status,
            "rollback_or_migration_risk": self.rollback_or_migration_risk,
            "required_human_approval": self.required_human_approval,
            "release_recommendation": self.release_recommendation,
            "errors": self.errors,
        }


def _run_gh(
    args: list[str],
    timeout: int = 30,
    errors: list[str] | None = None,
) -> dict[str, Any] | list[Any] | str | None:
    """Run a gh CLI command and return parsed JSON, or None on failure.

    Logs errors at WARNING level (not DEBUG) so auth failures, rate limits,
    and transient API errors are visible in operator review.
    """
    try:
        proc = subprocess.run(
            ["gh"] + args,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if proc.returncode != 0:
            message = (
                f"gh command failed (exit {proc.returncode}): "
                f"gh {' '.join(args[:3])} — {proc.stderr.strip()[:200]}"
            )
            logger.warning(message)
            if errors is not None:
                errors.append(message)
            return None
        return json.loads(proc.stdout)
    except subprocess.TimeoutExpired:
        message = f"gh command timed out after {timeout}s: gh {' '.join(args[:3])}"
        logger.warning(message)
        if errors is not None:
            errors.append(message)
        return None
    except json.JSONDecodeError as e:
        message = f"gh command returned invalid JSON: {e} — output: {proc.stdout[:200]}"
        logger.warning(message)
        if errors is not None:
            errors.append(message)
        return None
    except Exception as e:
        message = f"gh command error: {type(e).__name__} — {e}"
        logger.warning(message)
        if errors is not None:
            errors.append(message)
        return None


def _get_pr_info(
    repo: str, pr_number: int, errors: list[str] | None = None
) -> dict[str, Any] | None:
    """Fetch PR metadata including merge commit SHA and head SHA."""
    result = _run_gh(
        [
            "pr",
            "view",
            str(pr_number),
            "--repo",
            repo,
            "--json",
            "number,mergeCommit,headRefOid,baseRefName,headRefName,body,state",
        ],
        errors=errors,
    )
    if result and isinstance(result, dict):
        return result
    return None


def _get_workflow_runs_for_sha(
    repo: str, sha: str, errors: list[str] | None = None
) -> list[dict[str, Any]]:
    """Fetch workflow runs for a specific commit SHA."""
    result = _run_gh(
        [
            "run",
            "list",
            "--repo",
            repo,
            "--commit",
            sha,
            "--limit",
            "20",
            "--json",
            "conclusion,status,workflowName,url,headSha,startedAt,updatedAt,databaseId",
        ],
        errors=errors,
    )
    if result and isinstance(result, list):
        return result
    return []


def _get_check_suites_for_sha(
    repo: str,
    sha: str,
    errors: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Fetch check suites for a specific commit SHA via GitHub API.

    Note: `gh api --paginate` can emit multiple JSON objects when pagination
    spans multiple pages. We handle this by parsing the raw stdout as
    concatenated JSON objects.
    """
    try:
        proc = subprocess.run(
            ["gh", "api", f"repos/{repo}/commits/{sha}/check-suites", "--paginate"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if proc.returncode != 0:
            message = f"check-suites API call failed: {proc.stderr.strip()[:200]}"
            logger.warning(message)
            if errors is not None:
                errors.append(message)
            return []
        # gh --paginate may emit multiple JSON objects concatenated.
        # Parse them by splitting on "}\n{" boundaries and re-wrapping.
        raw = proc.stdout.strip()
        if not raw:
            return []
        # Try single-object parse first
        try:
            result = json.loads(raw)
            if isinstance(result, dict):
                return result.get("check_suites", [])
        except json.JSONDecodeError:
            pass
        # Multiple concatenated objects — wrap in a JSON array
        wrapped = "[" + raw.replace("}\n{", "},{").replace("}\r\n{", "},{") + "]"
        try:
            results = json.loads(wrapped)
            suites: list[dict[str, Any]] = []
            for r in results:
                if isinstance(r, dict):
                    suites.extend(r.get("check_suites", []))
            return suites
        except json.JSONDecodeError as e:
            message = f"check-suites pagination parse failed: {e}"
            logger.warning(message)
            if errors is not None:
                errors.append(message)
            return []
    except subprocess.TimeoutExpired:
        message = "check-suites API call timed out"
        logger.warning(message)
        if errors is not None:
            errors.append(message)
        return []
    except Exception as e:
        message = f"check-suites API error: {e}"
        logger.warning(message)
        if errors is not None:
            errors.append(message)
        return []


def _get_check_runs_for_ref(repo: str, ref: str) -> list[dict[str, Any]]:
    """Fetch check runs for a specific ref via GitHub API.

    Handles `--paginate` concatenated JSON objects.
    """
    try:
        proc = subprocess.run(
            ["gh", "api", f"repos/{repo}/commits/{ref}/check-runs", "--paginate"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if proc.returncode != 0:
            logger.warning("check-runs API call failed: %s", proc.stderr.strip()[:200])
            return []
        raw = proc.stdout.strip()
        if not raw:
            return []
        try:
            result = json.loads(raw)
            if isinstance(result, dict):
                return result.get("check_runs", [])
        except json.JSONDecodeError:
            pass
        wrapped = "[" + raw.replace("}\n{", "},{").replace("}\r\n{", "},{") + "]"
        try:
            results = json.loads(wrapped)
            runs: list[dict[str, Any]] = []
            for r in results:
                if isinstance(r, dict):
                    runs.extend(r.get("check_runs", []))
            return runs
        except json.JSONDecodeError as e:
            logger.warning("check-runs pagination parse failed: %s", e)
            return []
    except subprocess.TimeoutExpired:
        logger.warning("check-runs API call timed out")
        return []
    except Exception as e:
        logger.warning("check-runs API error: %s", e)
        return []


def _get_commit_message(repo: str, sha: str, errors: list[str] | None = None) -> str:
    """Fetch the commit message for a specific SHA via gh API."""
    result = _run_gh(
        [
            "api",
            f"repos/{repo}/commits/{sha}",
        ],
        errors=errors,
    )
    if isinstance(result, dict):
        commit = result.get("commit", {})
        if isinstance(commit, dict):
            message = commit.get("message", "")
            if isinstance(message, str):
                return message
    return ""


def _determine_evidence_tier(
    workflow_runs: list[dict[str, Any]],
    check_suites: list[dict[str, Any]],
    pr_body: str,
    commit_message: str = "",
) -> str:
    """Determine the evidence quality tier based on what was found."""
    has_workflow_runs = len(workflow_runs) > 0
    has_check_suites = len(check_suites) > 0

    if has_workflow_runs or has_check_suites:
        # Check if all runs have a definitive conclusion
        all_completed = all(
            r.get("status") == "completed" for r in workflow_runs
        ) and all(s.get("status") == "completed" for s in check_suites)
        if all_completed:
            return EvidenceTier.CONNECTOR_VERIFIED
        return EvidenceTier.INCONCLUSIVE

    # No connector evidence — check if PR body declares CI status
    if pr_body and any(
        marker in pr_body.lower()
        for marker in (
            "ci pass",
            "ci green",
            "tests pass",
            "all checks pass",
            "ci: pass",
        )
    ):
        return EvidenceTier.DECLARED_IN_PR

    # No connector evidence — check if commit message declares CI status
    if commit_message and any(
        marker in commit_message.lower()
        for marker in (
            "ci pass",
            "ci green",
            "tests pass",
            "all checks pass",
            "ci: pass",
        )
    ):
        return EvidenceTier.DECLARED_IN_COMMIT

    return EvidenceTier.MISSING


def _determine_ci_status(
    workflow_runs: list[dict[str, Any]],
    check_suites: list[dict[str, Any]],
) -> str:
    """Map CI evidence to a release-gate ci_status value."""
    if not workflow_runs and not check_suites:
        return "missing"

    all_conclusions: list[str] = []
    for r in workflow_runs:
        c = r.get("conclusion", "")
        if c:
            all_conclusions.append(c)
    for s in check_suites:
        c = s.get("conclusion", "")
        if c:
            all_conclusions.append(c)

    if not all_conclusions:
        return "inconclusive"

    if all(c == "success" for c in all_conclusions):
        return "green"
    if any(c in ("failure", "cancelled") for c in all_conclusions):
        return "red"
    if any(c == "skipped" for c in all_conclusions):
        return "skipped"
    return "inconclusive"


def _determine_release_recommendation(
    evidence_tier: str,
    ci_status: str,
) -> tuple[str, bool]:
    """Determine release recommendation and whether human approval is needed.

    Returns (recommendation, required_human_approval).
    """
    if ci_status == "red":
        return ("no-go", False)
    if ci_status == "missing" or evidence_tier == EvidenceTier.MISSING:
        return ("conditional", True)
    if evidence_tier == EvidenceTier.INCONCLUSIVE:
        return ("conditional", True)
    if evidence_tier == EvidenceTier.DECLARED_IN_PR:
        return ("conditional", True)
    if evidence_tier == EvidenceTier.DECLARED_IN_COMMIT:
        return ("conditional", True)
    if ci_status == "green" and evidence_tier == EvidenceTier.CONNECTOR_VERIFIED:
        return ("go", False)
    if ci_status == "skipped":
        return ("conditional", True)
    return ("conditional", True)


def extract_ci_evidence(
    repo: str,
    pr_number: int,
) -> MergedPREvidence:
    """Extract CI evidence for a merged PR.

    Args:
        repo: Repository in "owner/repo" format.
        pr_number: PR number to extract evidence for.

    Returns:
        MergedPREvidence with CI evidence, evidence tier, and mapped
        release-gate fields.
    """
    evidence = MergedPREvidence(repo=repo, pr_number=pr_number)

    # Step 1: Fetch PR metadata
    pr_info = _get_pr_info(repo, pr_number, evidence.errors)
    if not pr_info:
        evidence.errors.append(f"Could not fetch PR #{pr_number} from {repo}")
        evidence.evidence_tier = EvidenceTier.MISSING
        evidence.ci_status = "missing"
        evidence.release_recommendation, evidence.required_human_approval = (
            _determine_release_recommendation(
                evidence.evidence_tier, evidence.ci_status
            )
        )
        return evidence

    # Extract merge commit SHA and head SHA
    merge_commit = pr_info.get("mergeCommit", {})
    if isinstance(merge_commit, dict):
        evidence.merge_commit_sha = merge_commit.get("oid", "")
    evidence.head_sha = pr_info.get("headRefOid", "")
    evidence.branch_name = pr_info.get("headRefName", "")
    pr_body = pr_info.get("body", "") or ""
    pr_state = pr_info.get("state", "")

    # Verify PR is actually merged — if not, don't treat it as merged evidence
    if pr_state != "MERGED":
        evidence.errors.append(
            f"PR #{pr_number} state is '{pr_state}', not 'MERGED' — "
            f"evidence extraction is only valid for merged PRs"
        )
        evidence.evidence_tier = EvidenceTier.MISSING
        evidence.ci_status = "missing"
        evidence.release_recommendation, evidence.required_human_approval = (
            _determine_release_recommendation(
                evidence.evidence_tier, evidence.ci_status
            )
        )
        return evidence

    # Step 2: Fetch workflow runs for the merge commit SHA
    sha_to_check = evidence.merge_commit_sha or evidence.head_sha
    workflow_runs: list[dict[str, Any]] = []
    if sha_to_check:
        workflow_runs = _get_workflow_runs_for_sha(repo, sha_to_check, evidence.errors)
        for run in workflow_runs:
            evidence.ci_evidence.append(
                CIEvidence(
                    source="workflow_run",
                    workflow_name=run.get("workflowName", ""),
                    run_url=run.get("url", ""),
                    status=run.get("status", ""),
                    conclusion=run.get("conclusion", ""),
                    head_sha=run.get("headSha", ""),
                    started_at=run.get("startedAt", ""),
                    completed_at=run.get("updatedAt", ""),
                    lookup_method=f"gh run list --commit {sha_to_check}",
                )
            )

    # Step 3: Fetch check suites for the merge commit SHA
    check_suites: list[dict[str, Any]] = []
    if sha_to_check:
        check_suites = _get_check_suites_for_sha(repo, sha_to_check, evidence.errors)
        for suite in check_suites:
            evidence.ci_evidence.append(
                CIEvidence(
                    source="check_suite",
                    workflow_name=suite.get("app", {}).get("name", ""),
                    run_url=suite.get("html_url", ""),
                    status=suite.get("status", ""),
                    conclusion=suite.get("conclusion", ""),
                    head_sha=suite.get("head_sha", ""),
                    started_at=suite.get("created_at", ""),
                    completed_at=suite.get("updated_at", ""),
                    lookup_method=f"gh api repos/{repo}/commits/{sha_to_check}/check-suites",
                )
            )

    # Step 4: Determine evidence tier
    # Fetch commit message to check for declared_in_commit tier
    commit_message = ""
    if evidence.merge_commit_sha:
        commit_message = _get_commit_message(
            repo, evidence.merge_commit_sha, evidence.errors
        )
    evidence.evidence_tier = _determine_evidence_tier(
        workflow_runs, check_suites, pr_body, commit_message
    )

    # Step 5: Map to release-gate fields
    evidence.ci_status = _determine_ci_status(workflow_runs, check_suites)
    evidence.release_recommendation, evidence.required_human_approval = (
        _determine_release_recommendation(evidence.evidence_tier, evidence.ci_status)
    )

    # Step 6: Deployment status (conservative — only green CI means deployed)
    if evidence.ci_status == "green":
        evidence.deployment_status = "ci_verified"
    elif evidence.ci_status == "red":
        evidence.deployment_status = "blocked"
    else:
        evidence.deployment_status = "unverified"

    # Step 7: Rollback/migration risk (conservative)
    if evidence.ci_status == "red":
        evidence.rollback_or_migration_risk = "high"
    elif evidence.evidence_tier in (EvidenceTier.MISSING, EvidenceTier.INCONCLUSIVE):
        evidence.rollback_or_migration_risk = "unknown"
    else:
        evidence.rollback_or_migration_risk = "low"

    return evidence


def extract_batch(
    repo: str,
    pr_numbers: list[int],
) -> list[dict[str, Any]]:
    """Extract CI evidence for a batch of merged PRs.

    Args:
        repo: Repository in "owner/repo" format.
        pr_numbers: List of PR numbers to extract evidence for.

    Returns:
        List of MergedPREvidence dicts, suitable for the 4 PM
        Transformation Trace review.
    """
    results: list[dict[str, Any]] = []
    for pr_number in pr_numbers:
        evidence = extract_ci_evidence(repo, pr_number)
        results.append(evidence.to_dict())
    return results
