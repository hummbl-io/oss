#!/usr/bin/env python3
"""HUMMBL CalVer Release Tool.

Generates CalVer tags and creates releases for HUMMBL projects.
Supports two formats per HUMMBL_CALVER_STANDARD.md:

  - Release format:      vYYYY.M.D[.N]
  - Phase-gated format:  phase-{N}.vYYYY.M.D[.N]

Adapted from Hermes Agent's release.py (Nous Research, MIT).
Reference: docs/standards/HUMMBL_CALVER_STANDARD.md

Usage:
    # Dry run — preview the tag and changelog
    python scripts/hummbl_release.py --project my-project

    # Create the release (with internal SemVer bump)
    python scripts/hummbl_release.py --project my-project --bump minor --publish

    # Phase-gated release
    python scripts/hummbl_release.py --project governed-counterpart --phase 1 --publish

    # Belated release (override the CalVer date)
    python scripts/hummbl_release.py --project my-project --date 2026.8.8 --publish

    # First release (no previous tag)
    python scripts/hummbl_release.py --project my-project --first-release --publish

    # CalVer only, no internal SemVer
    python scripts/hummbl_release.py --project my-project --no-semver --publish
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# CalVer date format: YYYY.M.D (no zero-padding on month/day).
_STRICT_DATE_RE = re.compile(r"^\d{4}\.(1[0-2]|[1-9])\.(3[0-1]|[1-2][0-9]|[1-9])$")
# No-zero-pad month/day segments: 1-12 and 1-31 without leading zeros.
_MONTH = r"(?:1[0-2]|[1-9])"
_DAY = r"(?:3[0-1]|[1-2][0-9]|[1-9])"
# Full release tag: vYYYY.M.D[.N] — rejects zero-padded month/day.
RELEASE_TAG_RE = re.compile(rf"^v(\d{{4}})\.{_MONTH}\.{_DAY}(?:\.(\d+))?$")
# Full phase-gated tag: phase-{N}.vYYYY.M.D[.N] — rejects zero-padded phase.
PHASE_TAG_RE = re.compile(
    rf"^phase-(-1|0|[1-9][0-9]*)\.v(\d{{4}})\.{_MONTH}\.{_DAY}(?:\.(\d+))?$"
)


# ──────────────────────────────────────────────────────────────────────
# Git helpers
# ──────────────────────────────────────────────────────────────────────

def git(*args: str, check: bool = True) -> str:
    """Run a git command in REPO_ROOT and return stdout."""
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), *args],
        capture_output=True,
        text=True,
    )
    if check and result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def git_tag_exists(tag: str) -> bool:
    return bool(git("tag", "--list", tag, check=False))


def get_last_tag(project: str, phase: int | None, tag_prefix: str | None = None) -> str | None:
    """Get the most recent CalVer tag for this project (and phase if gated).

    Uses a 4-digit year glob (v20[0-9][0-9].*) to avoid matching SemVer tags
    like v20.0.0. If tag_prefix is given, it's prepended to scope to a
    specific project in multi-project repos.
    """
    if phase is not None:
        glob = f"phase-{phase}.v20[0-9][0-9].*"
    else:
        glob = "v20[0-9][0-9].*"
    if tag_prefix:
        glob = f"{tag_prefix}-{glob}" if phase is None else f"{tag_prefix}-{glob}"
    tags = git("tag", "--list", glob, "--sort=-v:refname", check=False)
    if not tags:
        return None
    # Filter results through the regex to reject any non-CalVer tags that
    # matched the glob (defensive — the glob is already specific).
    candidates = tags.split("\n")
    regex = PHASE_TAG_RE if phase is not None else RELEASE_TAG_RE
    for tag in candidates:
        if regex.match(tag):
            return tag
    return None


# ──────────────────────────────────────────────────────────────────────
# CalVer tag generation
# ──────────────────────────────────────────────────────────────────────

def calver_date(now: datetime) -> str:
    """Format a datetime as YYYY.M.D (no zero-padding)."""
    return f"{now.year}.{now.month}.{now.day}"


def base_tag(date: str, phase: int | None) -> str:
    """Build the base tag (no same-day suffix) for the given date and phase."""
    if phase is not None:
        return f"phase-{phase}.v{date}"
    return f"v{date}"


def next_available_tag(base: str) -> str:
    """Return the next available tag, suffixing same-day releases from .2."""
    if not git_tag_exists(base):
        return base
    suffix = 2
    while git_tag_exists(f"{base}.{suffix}"):
        suffix += 1
    return f"{base}.{suffix}"


def validate_tag(tag: str, phase: int | None) -> None:
    """Reject tags that don't match the mandated format and requested phase."""
    if phase is not None:
        m = PHASE_TAG_RE.match(tag)
        if not m:
            raise ValueError(f"Tag {tag!r} does not match phase-gated format")
        if int(m.group(1)) != phase:
            raise ValueError(
                f"Tag {tag!r} phase {m.group(1)} does not match requested phase {phase}"
            )
    else:
        if not RELEASE_TAG_RE.match(tag):
            raise ValueError(f"Tag {tag!r} does not match release format")


# ──────────────────────────────────────────────────────────────────────
# SemVer helpers (optional, for projects that carry internal SemVer)
# ──────────────────────────────────────────────────────────────────────

SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
# CalVer dates (YYYY.M.D) are structurally valid SemVer (major.minor.patch).
# Reject them in bump_semver to prevent accidentally bumping a CalVer date
# that was misfiled into a version field.
_CALVER_SHAPED = re.compile(r"^(20\d{2})\.([1-9]|1[0-2])\.([1-9]|[12]\d|3[01])$")


def bump_semver(current: str, part: str) -> str:
    if _CALVER_SHAPED.match(current):
        raise ValueError(
            f"Current version {current!r} looks like a CalVer date, not SemVer. "
            "Use --no-semver for CalVer-only releases."
        )
    m = SEMVER_RE.match(current)
    if not m:
        raise ValueError(f"Current version {current!r} is not SemVer")
    major, minor, patch = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if part == "major":
        return f"{major + 1}.0.0"
    if part == "minor":
        return f"{major}.{minor + 1}.0"
    if part == "patch":
        return f"{major}.{minor}.{patch + 1}"
    raise ValueError(f"Unknown bump part: {part}")


def read_pyproject_version() -> str | None:
    pyproject = REPO_ROOT / "pyproject.toml"
    if not pyproject.exists():
        return None
    try:
        import tomllib
        with pyproject.open("rb") as f:
            data = tomllib.load(f)
        return data.get("project", {}).get("version")
    except Exception:
        # Fallback: regex for non-standard pyproject layouts.
        text = pyproject.read_text(encoding="utf-8")
        m = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
        return m.group(1) if m else None


def update_pyproject_version(new_version: str) -> bool:
    pyproject = REPO_ROOT / "pyproject.toml"
    if not pyproject.exists():
        return False
    text = pyproject.read_text(encoding="utf-8")
    updated = re.sub(
        r'^version\s*=\s*"[^"]+"',
        f'version = "{new_version}"',
        text,
        flags=re.MULTILINE,
    )
    if updated == text:
        return False
    pyproject.write_text(updated, encoding="utf-8")
    return True


def update_init_version(new_version: str, calver: str) -> list[Path]:
    """Update __version__ and __release_date__ in all __init__.py files.

    Looks for modules with `__version__ = "..."` and optionally
    `__release_date__ = "..."`. Returns list of files that were updated.
    """
    updated: list[Path] = []
    for init_file in REPO_ROOT.rglob("__init__.py"):
        if "site-packages" in str(init_file) or ".venv" in str(init_file):
            continue
        text = init_file.read_text(encoding="utf-8")
        original = text
        if "__version__" not in text:
            continue
        text = re.sub(
            r'__version__\s*=\s*"[^"]+"',
            f'__version__ = "{new_version}"',
            text,
        )
        text = re.sub(
            r'__release_date__\s*=\s*"[^"]+"',
            f'__release_date__ = "{calver}"',
            text,
        )
        if text != original:
            init_file.write_text(text, encoding="utf-8")
            updated.append(init_file)
    return updated


def read_init_version() -> str | None:
    """Read __version__ from the first __init__.py that has one."""
    for init_file in REPO_ROOT.rglob("__init__.py"):
        if "site-packages" in str(init_file) or ".venv" in str(init_file):
            continue
        text = init_file.read_text(encoding="utf-8")
        m = re.search(r'__version__\s*=\s*"([^"]+)"', text)
        if m:
            return m.group(1)
    return None


def update_package_json_version(new_version: str) -> bool:
    """Update version in package.json (npm/JS projects)."""
    pkg = REPO_ROOT / "package.json"
    if not pkg.exists():
        return False
    text = pkg.read_text(encoding="utf-8")
    updated = re.sub(
        r'"version"\s*:\s*"[^"]+"',
        f'"version": "{new_version}"',
        text,
        count=1,
    )
    if updated == text:
        return False
    pkg.write_text(updated, encoding="utf-8")
    return True


# ──────────────────────────────────────────────────────────────────────
# Changelog generation
# ──────────────────────────────────────────────────────────────────────

def get_commits_since(tag: str | None, max_commits: int = 50) -> list[str]:
    if tag:
        spec = f"{tag}..HEAD"
    else:
        spec = "HEAD"
    out = git("log", "--pretty=format:- %s (%h)", f"-{max_commits}", spec, check=False)
    if not out:
        return []
    return out.split("\n")


def generate_changelog(
    project: str,
    tag_name: str,
    semver: str | None,
    commits: list[str],
    prev_tag: str | None,
    first_release: bool,
) -> str:
    lines = [f"# {project} {tag_name}"]
    lines.append("")
    if semver:
        lines.append(f"Internal SemVer: v{semver}")
        lines.append("")
    if first_release or not prev_tag:
        lines.append("First release.")
    else:
        lines.append(f"Full Changelog: {prev_tag}...{tag_name}")
    lines.append("")
    if commits:
        lines.append("## Commits")
        lines.append("")
        lines.extend(commits)
    else:
        lines.append("No new commits since last tag.")
    lines.append("")
    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────────
# Bus posting
# ──────────────────────────────────────────────────────────────────────

def post_bus_status(bus_from: str, project: str, tag_name: str, published: bool) -> None:
    """Post a STATUS to the coordination bus. Best-effort, never fatal."""
    bus_script = Path.home() / "bin" / "bus-global.py"
    if not bus_script.exists():
        print("  (bus-global.py not found — skipping bus post)")
        return
    status = "published" if published else "prepared (dry run)"
    msg = f"Release {project} {tag_name} {status}"
    try:
        subprocess.run(
            ["python", str(bus_script), "post", bus_from, "all", "STATUS", msg],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except Exception as exc:
        print(f"  (bus post skipped: {exc})")


# ──────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="HUMMBL CalVer release tool (see HUMMBL_CALVER_STANDARD.md)",
    )
    parser.add_argument("--project", required=True, help="Project name (for changelog title and bus)")
    parser.add_argument("--phase", type=int, default=None,
                        help="Phase number for phase-gated format (-1, 0, 1, 2, ...). "
                             "Omit for release format.")
    parser.add_argument("--bump", choices=["major", "minor", "patch"], default=None,
                        help="Bump internal SemVer (requires pyproject.toml, __init__.py, or package.json).")
    parser.add_argument("--no-semver", action="store_true",
                        help="Skip internal SemVer — use CalVer as the only version.")
    parser.add_argument("--date", default=None,
                        help="Override CalVer date (format: YYYY.M.D). For belated releases.")
    parser.add_argument("--timezone", default="UTC",
                        help="IANA timezone for date computation (default: UTC).")
    parser.add_argument("--first-release", action="store_true",
                        help="Mark as first release (no previous tag expected).")
    parser.add_argument("--publish", action="store_true",
                        help="Actually create the tag and release (otherwise dry run).")
    parser.add_argument("--push", action="store_true",
                        help="Push the tag to origin after creating it.")
    parser.add_argument("--gh-release", action="store_true",
                        help="Create a GitHub release after tagging (requires gh CLI).")
    parser.add_argument("--bus", action="store_true",
                        help="Post STATUS to coordination bus (also on dry run).")
    parser.add_argument("--bus-from", default=None,
                        help="Bus sender identity (default: --project value).")
    parser.add_argument("--tag-prefix", default=None,
                        help="Prefix to scope tag lookup in multi-project repos.")
    parser.add_argument("--max-commits", type=int, default=50,
                        help="Max commits in changelog for first release (default: 50).")
    args = parser.parse_args()

    # Validate phase early (W5: phase < -1 is invalid).
    if args.phase is not None and args.phase < -1:
        print(f"Error: --phase must be -1 or a non-negative integer, got {args.phase}")
        return 2

    # Determine CalVer date.
    if args.date:
        if not _STRICT_DATE_RE.match(args.date):
            print(f"Error: --date must be YYYY.M.D (no zero-padding), got {args.date!r}")
            print("       Example: 2026.8.8 (not 2026.08.08)")
            return 2
        calver = args.date
    else:
        # ponytail: timezone support adds a dependency; UTC is the default
        # and the only zone most projects need. Use zoneinfo if a non-UTC
        # zone is requested (stdlib in 3.11+).
        if args.timezone == "UTC":
            now = datetime.now(timezone.utc)
        else:
            try:
                from zoneinfo import ZoneInfo
                now = datetime.now(ZoneInfo(args.timezone))
            except KeyError:
                print(f"Error: unknown timezone {args.timezone!r}. Use an IANA zone name.")
                return 2
        calver = calver_date(now)

    # Build the tag.
    base = base_tag(calver, args.phase)
    tag_name = next_available_tag(base)
    if tag_name != base:
        print(f"Note: Tag {base} already exists, using {tag_name}")

    validate_tag(tag_name, args.phase)

    # Determine previous tag.
    prev_tag = get_last_tag(args.project, args.phase, args.tag_prefix)
    # W10: --first-release with existing tags — ignore prev_tag for changelog.
    if args.first_release and prev_tag:
        print(f"Note: --first-release passed but tags exist (latest: {prev_tag}). "
              "Treating as first release for changelog.")
        prev_tag = None
    if not prev_tag and not args.first_release:
        print("No previous tags found. Use --first-release for the initial release.")
        print(f"Would create tag: {tag_name}")
        if not args.publish:
            return 0
        return 1

    # Collect commits.
    commits = get_commits_since(prev_tag, max_commits=args.max_commits)
    if not commits and prev_tag:
        print("No new commits since last tag.")
        if not args.publish:
            return 0

    # Optional SemVer bump.
    new_semver = None
    if not args.no_semver and args.bump:
        current = read_pyproject_version() or read_init_version()
        if not current:
            print("Error: --bump requires a version field in pyproject.toml, __init__.py, or package.json")
            return 2
        try:
            new_semver = bump_semver(current, args.bump)
        except ValueError as exc:
            print(f"Error: {exc}")
            return 2
    elif not args.no_semver:
        new_semver = read_pyproject_version() or read_init_version()

    # Generate changelog.
    changelog = generate_changelog(
        args.project, tag_name, new_semver, commits, prev_tag, args.first_release,
    )

    # Print summary.
    print(f"\n  Project:       {args.project}")
    print(f"  CalVer tag:    {tag_name}")
    if new_semver:
        print(f"  Internal SemVer: v{new_semver}")
    print(f"  Previous tag:  {prev_tag or '(none — first release)'}")
    print(f"\n{changelog}")

    bus_from = args.bus_from or args.project

    if not args.publish:
        print("\n(dry run — pass --publish to create the tag)")
        if args.bus:
            post_bus_status(bus_from, args.project, tag_name, published=False)
        return 0

    # ── Publish path ────────────────────────────────────────────────
    # Update version files if SemVer bump requested. Stage ONLY the files
    # we modified (B2: never git add -A — avoids sweeping unrelated changes).
    files_to_stage: list[str] = []
    if new_semver and args.bump:
        if update_pyproject_version(new_semver):
            print(f"  ✓ Updated pyproject.toml to v{new_semver}")
            files_to_stage.append("pyproject.toml")
        init_files = update_init_version(new_semver, calver)
        for f in init_files:
            print(f"  ✓ Updated {f.relative_to(REPO_ROOT)} to v{new_semver} ({calver})")
            files_to_stage.append(str(f.relative_to(REPO_ROOT)))
        if update_package_json_version(new_semver):
            print(f"  ✓ Updated package.json to v{new_semver}")
            files_to_stage.append("package.json")
        if files_to_stage:
            for f in files_to_stage:
                git("add", f)
            git("commit", "-m", f"chore: bump version to v{new_semver} ({calver})")

    # Create annotated tag.
    tag_msg = f"{args.project} {tag_name}\n\nCalVer release"
    tag_result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "tag", "-a", tag_name, "-m", tag_msg],
        capture_output=True, text=True,
    )
    if tag_result.returncode != 0:
        print(f"  ✗ Failed to create tag {tag_name}: {tag_result.stderr.strip()}")
        return 1
    print(f"  ✓ Created tag {tag_name}")

    # Push (N2: push only the new tag, not all tags).
    if args.push:
        push_result = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "push", "origin", "HEAD",
             f"refs/tags/{tag_name}"],
            capture_output=True, text=True,
        )
        if push_result.returncode != 0:
            print(f"  ✗ Failed to push: {push_result.stderr.strip()}")
            print(f"    Retry manually: git push origin HEAD refs/tags/{tag_name}")
        else:
            print(f"  ✓ Pushed {tag_name} to origin")

    # GitHub release (W4: handle missing gh CLI gracefully).
    if args.gh_release:
        try:
            gh_result = subprocess.run(
                ["gh", "release", "create", tag_name,
                 "--title", f"{args.project} {tag_name}",
                 "--notes", changelog],
                capture_output=True, text=True,
            )
            if gh_result.returncode != 0:
                print(f"  ✗ Failed to create GitHub release: {gh_result.stderr.strip()}")
                print(f"    Tag {tag_name} exists — create the release manually.")
            else:
                print(f"  ✓ Created GitHub release for {tag_name}")
        except FileNotFoundError:
            print(f"  ✗ gh CLI not found — tag {tag_name} created, create the release manually.")

    post_bus_status(bus_from, args.project, tag_name, published=True)
    print(f"\n  ✓ Release {tag_name} published.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except FileNotFoundError as exc:
        if "git" in str(exc).lower():
            print("Error: git not found on PATH. Install git to use this tool.")
            sys.exit(2)
        raise
