"""Doctor command — verify hummbl-gitops environment health.

Checks:
1. CLI is on PATH
2. Pre-push hook is installed in target repo
3. State directory is writable
4. gh CLI is authenticated
5. Git is available
6. Python version is 3.11+
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class DoctorResult:
    """Result of a doctor check."""

    checks: list[tuple[str, bool, str]] = field(default_factory=list)

    @property
    def all_passed(self) -> bool:
        return all(passed for _, passed, _ in self.checks)

    def summary(self) -> str:
        lines = ["hummbl-gitops doctor"]
        for name, passed, message in self.checks:
            status = "OK" if passed else "FAIL"
            lines.append(f"  {status} {name}: {message}")
        lines.append(f"\n  Overall: {'HEALTHY' if self.all_passed else 'UNHEALTHY'}")
        return "\n".join(lines)


def run_doctor(repo_path: Optional[Path] = None) -> DoctorResult:
    """Run environment health checks.

    Args:
        repo_path: Path to a target repo to check for hook installation.
                   If None, skips the hook check.

    Returns:
        DoctorResult with per-check status.
    """
    result = DoctorResult()

    # 1. CLI on PATH
    cli_path = shutil.which("hummbl-gitops")
    if cli_path:
        result.checks.append(("cli_on_path", True, cli_path))
    else:
        result.checks.append(("cli_on_path", False, "hummbl-gitops not found on PATH"))

    # 2. Pre-push hook installed
    if repo_path is not None:
        hook_path = Path(repo_path) / ".git" / "hooks" / "pre-push"
        if hook_path.exists():
            result.checks.append(("pre_push_hook", True, str(hook_path)))
        else:
            result.checks.append(("pre_push_hook", False, f"not found at {hook_path}"))
    else:
        result.checks.append(("pre_push_hook", True, "skipped (no repo specified)"))

    # 3. State directory writable
    state_dir = os.environ.get("HUMMBL_GITOPS_STATE_DIR")
    if state_dir:
        state_path = Path(state_dir)
    else:
        state_path = Path.home() / ".local" / "share" / "hummbl-gitops"

    try:
        state_path.mkdir(parents=True, exist_ok=True)
        test_file = state_path / ".doctor-write-test"
        test_file.write_text("ok")
        test_file.unlink()
        result.checks.append(("state_dir_writable", True, str(state_path)))
    except (PermissionError, OSError) as e:
        result.checks.append(("state_dir_writable", False, f"{state_path}: {e}"))

    # 4. gh CLI authenticated
    gh_path = shutil.which("gh")
    if gh_path:
        auth_check = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if auth_check.returncode == 0:
            result.checks.append(("gh_authenticated", True, gh_path))
        else:
            result.checks.append((
                "gh_authenticated",
                False,
                f"gh found but not authenticated: {auth_check.stderr.strip()}",
            ))
    else:
        result.checks.append(("gh_authenticated", False, "gh CLI not found on PATH"))

    # 5. Git available
    git_path = shutil.which("git")
    if git_path:
        result.checks.append(("git_available", True, git_path))
    else:
        result.checks.append(("git_available", False, "git not found on PATH"))

    # 6. Python version
    if sys.version_info >= (3, 11):
        result.checks.append((
            "python_version",
            True,
            f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        ))
    else:
        result.checks.append((
            "python_version",
            False,
            f"{sys.version_info.major}.{sys.version_info.minor} (requires 3.11+)",
        ))

    return result
