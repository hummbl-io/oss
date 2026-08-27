"""Tests for the HUMMBL CalVer release tool.

Covers pure functions (CalVer date formatting, base tag construction, same-day
suffixing, tag validation, SemVer bumping), version-file updates, changelog
generation, bus posting, git helpers, and the main() CLI flow (dry-run paths
and error returns). The publish path (--publish with real git) is not
exercised here to avoid side effects; it is verified manually via dry runs.

Reference: docs/standards/HUMMBL_CALVER_STANDARD.md
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest
from scripts.hummbl_release import (
    PHASE_TAG_RE,
    RELEASE_TAG_RE,
    base_tag,
    bump_semver,
    calver_date,
    generate_changelog,
    get_commits_since,
    get_last_tag,
    main,
    next_available_tag,
    post_bus_status,
    read_pyproject_version,
    update_init_version,
    update_package_json_version,
    update_pyproject_version,
    validate_tag,
)

# ── calver_date ──────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("dt", "expected"),
    [
        (datetime(2026, 8, 11, 3, 30, tzinfo=timezone.utc), "2026.8.11"),
        (datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc), "2026.1.1"),
        (datetime(2026, 12, 31, 23, 59, tzinfo=timezone.utc), "2026.12.31"),
        (datetime(2026, 8, 3, 0, 0, tzinfo=timezone.utc), "2026.8.3"),
    ],
)
def test_calver_date_no_zero_padding(dt, expected):
    """CalVer dates must not zero-pad month or day (per standard §3.1)."""
    assert calver_date(dt) == expected


# ── base_tag ─────────────────────────────────────────────────────────


def test_base_tag_release_format():
    assert base_tag("2026.8.11", phase=None) == "v2026.8.11"


def test_base_tag_phase_gated():
    assert base_tag("2026.8.11", phase=1) == "phase-1.v2026.8.11"


def test_base_tag_phase_negative_one():
    """Phase -1 uses a double hyphen: phase--1 (per standard §3.2)."""
    assert base_tag("2026.8.10", phase=-1) == "phase--1.v2026.8.10"


def test_base_tag_phase_zero():
    assert base_tag("2026.8.11", phase=0) == "phase-0.v2026.8.11"


# ── next_available_tag ───────────────────────────────────────────────


def test_next_available_tag_first_release(monkeypatch):
    """First release of the day has no suffix."""
    monkeypatch.setattr("scripts.hummbl_release.git_tag_exists", lambda t: False)
    assert next_available_tag("v2026.8.11") == "v2026.8.11"


def test_next_available_tag_second_release(monkeypatch):
    """Second release same day gets .2 suffix (per standard §4)."""

    def fake_exists(tag):
        return tag == "v2026.8.11"

    monkeypatch.setattr("scripts.hummbl_release.git_tag_exists", fake_exists)
    assert next_available_tag("v2026.8.11") == "v2026.8.11.2"


def test_next_available_tag_third_release(monkeypatch):
    def fake_exists(tag):
        return tag in ("v2026.8.11", "v2026.8.11.2")

    monkeypatch.setattr("scripts.hummbl_release.git_tag_exists", fake_exists)
    assert next_available_tag("v2026.8.11") == "v2026.8.11.3"


def test_next_available_tag_phase_scoped(monkeypatch):
    """Phase-gated suffixes are independent per phase."""

    def fake_exists(tag):
        return tag == "phase-1.v2026.8.11"

    monkeypatch.setattr("scripts.hummbl_release.git_tag_exists", fake_exists)
    assert next_available_tag("phase-1.v2026.8.11") == "phase-1.v2026.8.11.2"


# ── validate_tag ─────────────────────────────────────────────────────


def test_validate_tag_release_format_accepts_valid():
    validate_tag("v2026.8.11", phase=None)
    validate_tag("v2026.8.11.2", phase=None)


def test_validate_tag_release_format_rejects_zero_padded():
    with pytest.raises(ValueError, match="release format"):
        validate_tag("v2026.08.11", phase=None)


def test_validate_tag_release_format_rejects_no_v_prefix():
    with pytest.raises(ValueError, match="release format"):
        validate_tag("2026.8.11", phase=None)


def test_validate_tag_release_format_rejects_semver():
    with pytest.raises(ValueError, match="release format"):
        validate_tag("v1.0.0", phase=None)


def test_validate_tag_phase_gated_accepts_valid():
    validate_tag("phase-1.v2026.8.11", phase=1)
    validate_tag("phase-0.v2026.8.11", phase=0)
    validate_tag("phase--1.v2026.8.10", phase=-1)
    validate_tag("phase-1.v2026.8.11.2", phase=1)


def test_validate_tag_phase_gated_rejects_zero_padded_phase():
    with pytest.raises(ValueError, match="phase-gated format"):
        validate_tag("phase-01.v2026.8.11", phase=1)


def test_validate_tag_phase_gated_rejects_missing_v():
    with pytest.raises(ValueError, match="phase-gated format"):
        validate_tag("phase-1.2026.8.11", phase=1)


def test_validate_tag_phase_mismatch_rejects():
    """A phase-2 tag must not validate when phase=1 is requested."""
    with pytest.raises(ValueError, match="does not match requested phase"):
        validate_tag("phase-2.v2026.8.11", phase=1)


# ── bump_semver ──────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("current", "part", "expected"),
    [
        ("0.17.0", "major", "1.0.0"),
        ("0.17.0", "minor", "0.18.0"),
        ("0.17.0", "patch", "0.17.1"),
        ("1.2.3", "major", "2.0.0"),
        ("1.2.3", "minor", "1.3.0"),
        ("1.2.3", "patch", "1.2.4"),
    ],
)
def test_bump_semver(current, part, expected):
    assert bump_semver(current, part) == expected


def test_bump_semver_rejects_non_semver():
    with pytest.raises(ValueError, match="not SemVer"):
        bump_semver("1.2", "minor")  # only two segments


def test_bump_semver_rejects_calver_date():
    """A CalVer date like 2026.8.11 is syntactically valid SemVer but must be
    rejected to prevent accidentally bumping a CalVer date misfiled into a
    version field. Use --no-semver for CalVer-only releases.
    """
    with pytest.raises(ValueError, match="CalVer date"):
        bump_semver("2026.8.11", "patch")


def test_bump_semver_rejects_unknown_part():
    with pytest.raises(ValueError, match="Unknown bump part"):
        bump_semver("1.0.0", "pre")


# ── regex sanity ─────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "tag",
    ["v2026.8.11", "v2026.8.11.2", "v2026.12.31", "v2026.1.1.99"],
)
def test_release_tag_regex_matches_valid(tag):
    assert RELEASE_TAG_RE.match(tag)


@pytest.mark.parametrize(
    "tag",
    ["v2026.08.11", "2026.8.11", "v1.0.0", "v2026.8", "v2026.8.11.2.3"],
)
def test_release_tag_regex_rejects_invalid(tag):
    # All rejected: zero-padded month, no v prefix, SemVer, missing day,
    # and two suffix segments (regex allows only one .N suffix).
    assert not RELEASE_TAG_RE.match(tag)


@pytest.mark.parametrize(
    "tag",
    ["phase--1.v2026.8.10", "phase-0.v2026.8.11", "phase-1.v2026.8.11.2", "phase-12.v2026.8.11"],
)
def test_phase_tag_regex_matches_valid(tag):
    assert PHASE_TAG_RE.match(tag)


@pytest.mark.parametrize(
    "tag",
    ["phase-01.v2026.8.11", "phase-1.2026.8.11", "phase-1.v2026.08.11", "phase-.v2026.8.11"],
)
def test_phase_tag_regex_rejects_invalid(tag):
    assert not PHASE_TAG_RE.match(tag)


# ── get_last_tag ─────────────────────────────────────────────────────


def test_get_last_tag_empty_returns_none(monkeypatch):
    monkeypatch.setattr("scripts.hummbl_release.git", lambda *a, **k: "")
    assert get_last_tag("proj", None) is None


def test_get_last_tag_returns_first_calver_match(monkeypatch):
    monkeypatch.setattr(
        "scripts.hummbl_release.git",
        lambda *a, **k: "v2026.8.11\nv2026.8.3\nv2026.7.20",
    )
    assert get_last_tag("proj", None) == "v2026.8.11"


def test_get_last_tag_filters_semver_from_glob(monkeypatch):
    """The 4-digit glob should not match SemVer tags, but if any slip through,
    the regex filter rejects them."""
    monkeypatch.setattr(
        "scripts.hummbl_release.git",
        lambda *a, **k: "v2026.8.11\nv20.0.0",
    )
    assert get_last_tag("proj", None) == "v2026.8.11"


def test_get_last_tag_phase_gated(monkeypatch):
    monkeypatch.setattr(
        "scripts.hummbl_release.git",
        lambda *a, **k: "phase-1.v2026.8.11\nphase-1.v2026.8.3",
    )
    assert get_last_tag("proj", 1) == "phase-1.v2026.8.11"


# ── get_commits_since ────────────────────────────────────────────────


def test_get_commits_since_with_tag(monkeypatch):
    monkeypatch.setattr(
        "scripts.hummbl_release.git",
        lambda *a, **k: "- fix bug (abc123)\n- add feature (def456)",
    )
    commits = get_commits_since("v2026.8.10")
    assert len(commits) == 2
    assert "fix bug" in commits[0]


def test_get_commits_since_empty(monkeypatch):
    monkeypatch.setattr("scripts.hummbl_release.git", lambda *a, **k: "")
    assert get_commits_since("v2026.8.10") == []


def test_get_commits_since_no_tag(monkeypatch):
    monkeypatch.setattr(
        "scripts.hummbl_release.git",
        lambda *a, **k: "- initial (abc123)",
    )
    commits = get_commits_since(None)
    assert len(commits) == 1


# ── generate_changelog ───────────────────────────────────────────────


def test_generate_changelog_with_semver_and_commits():
    cl = generate_changelog("proj", "v2026.8.11", "0.18.0", ["- fix (abc)"], "v2026.8.10", False)
    assert cl.startswith("# proj v2026.8.11")
    assert "Internal SemVer: v0.18.0" in cl
    assert "Full Changelog: v2026.8.10...v2026.8.11" in cl
    assert "## Commits" in cl
    assert "- fix (abc)" in cl


def test_generate_changelog_first_release_no_commits():
    cl = generate_changelog("proj", "v2026.8.11", None, [], None, True)
    assert cl.startswith("# proj v2026.8.11")
    assert "Internal SemVer" not in cl
    assert "First release." in cl
    assert "No new commits since last tag." in cl


def test_generate_changelog_no_semver_with_commits():
    cl = generate_changelog("proj", "v2026.8.11", None, ["- feat (abc)"], "v2026.8.10", False)
    assert "Internal SemVer" not in cl
    assert "## Commits" in cl


# ── post_bus_status ──────────────────────────────────────────────────


def test_post_bus_status_missing_script(monkeypatch, capsys):
    # Point Path.home() to a tmp dir with no bin/bus-global.py
    import scripts.hummbl_release as mod

    monkeypatch.setattr(mod.Path, "home", lambda: Path("/nonexistent-test-path"))
    post_bus_status("proj", "proj", "v2026.8.11", published=True)
    captured = capsys.readouterr()
    assert "bus-global.py not found" in captured.out


def test_post_bus_status_calls_subprocess(monkeypatch):
    import scripts.hummbl_release as mod

    calls = []
    monkeypatch.setattr(mod.Path, "home", lambda: Path("/tmp"))
    # Create a fake bus script
    fake_script = Path("/tmp/bin/bus-global.py")
    fake_script.parent.mkdir(parents=True, exist_ok=True)
    fake_script.write_text("# fake", encoding="utf-8")
    monkeypatch.setattr(
        mod.subprocess,
        "run",
        lambda *a, **k: calls.append((a, k)) or type("R", (), {"returncode": 0})(),
    )
    try:
        post_bus_status("hummbl-governance", "hummbl-governance", "v2026.8.11", published=True)
        assert len(calls) == 1
        # Verify bus_from is passed correctly (not "devin")
        cmd = calls[0][0][0]
        assert "hummbl-governance" in cmd
        assert "devin" not in cmd
    finally:
        fake_script.unlink(missing_ok=True)


# ── version file updates ─────────────────────────────────────────────


def test_update_pyproject_version(tmp_path, monkeypatch):
    import scripts.hummbl_release as mod

    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\nversion = "1.2.2"\n', encoding="utf-8")
    assert update_pyproject_version("1.3.0") is True
    assert 'version = "1.3.0"' in pyproject.read_text(encoding="utf-8")


def test_update_pyproject_version_noop(tmp_path, monkeypatch):
    import scripts.hummbl_release as mod

    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\nversion = "1.2.2"\n', encoding="utf-8")
    # Same version → no change
    assert update_pyproject_version("1.2.2") is False


def test_update_pyproject_version_missing_file(tmp_path, monkeypatch):
    import scripts.hummbl_release as mod

    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    assert update_pyproject_version("1.3.0") is False


def test_update_package_json_version(tmp_path, monkeypatch):
    import scripts.hummbl_release as mod

    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    pkg = tmp_path / "package.json"
    pkg.write_text('{"name": "test", "version": "1.2.2"}', encoding="utf-8")
    assert update_package_json_version("1.3.0") is True
    assert '"version": "1.3.0"' in pkg.read_text(encoding="utf-8")


def test_update_init_version_updates_all(tmp_path, monkeypatch):
    import scripts.hummbl_release as mod

    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    pkg_a = tmp_path / "pkg_a"
    pkg_b = tmp_path / "pkg_b"
    pkg_a.mkdir()
    pkg_b.mkdir()
    (pkg_a / "__init__.py").write_text('__version__ = "1.0.0"\n', encoding="utf-8")
    (pkg_b / "__init__.py").write_text('__version__ = "1.0.0"\n__release_date__ = "2026.1.1"\n', encoding="utf-8")
    updated = update_init_version("1.1.0", "2026.8.11")
    assert len(updated) == 2
    assert '__version__ = "1.1.0"' in (pkg_a / "__init__.py").read_text(encoding="utf-8")
    assert '__release_date__ = "2026.8.11"' in (pkg_b / "__init__.py").read_text(encoding="utf-8")


# ── read_pyproject_version (tomllib) ─────────────────────────────────


def test_read_pyproject_version_tomllib(tmp_path, monkeypatch):
    import scripts.hummbl_release as mod

    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\nname = "test"\nversion = "1.2.2"\n', encoding="utf-8")
    assert read_pyproject_version() == "1.2.2"


def test_read_pyproject_version_missing(tmp_path, monkeypatch):
    import scripts.hummbl_release as mod

    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    assert read_pyproject_version() is None


# ── main() CLI ───────────────────────────────────────────────────────


def test_main_dry_run_first_release(monkeypatch, capsys):
    """Dry run with --first-release prints the tag and returns 0."""
    import scripts.hummbl_release as mod

    monkeypatch.setattr(mod, "git_tag_exists", lambda t: False)
    monkeypatch.setattr(mod, "get_last_tag", lambda *a, **k: None)
    monkeypatch.setattr(mod, "get_commits_since", lambda *a, **k: [])
    monkeypatch.setattr(mod, "read_pyproject_version", lambda: None)
    monkeypatch.setattr(mod, "read_init_version", lambda: None)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "hummbl_release.py",
            "--project",
            "test",
            "--first-release",
            "--date",
            "2026.8.11",
        ],
    )
    rc = main()
    assert rc == 0
    out = capsys.readouterr().out
    assert "v2026.8.11" in out
    assert "dry run" in out


def test_main_rejects_phase_below_negative_one(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["hummbl_release.py", "--project", "test", "--phase", "-2"])
    rc = main()
    assert rc == 2
    out = capsys.readouterr().out
    assert "must be -1 or a non-negative integer" in out


def test_main_rejects_bad_date(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["hummbl_release.py", "--project", "test", "--date", "2026.08.08"])
    rc = main()
    assert rc == 2
    out = capsys.readouterr().out
    assert "no zero-padding" in out


def test_main_rejects_bad_timezone(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["hummbl_release.py", "--project", "test", "--timezone", "Invalid/Zone"])
    rc = main()
    assert rc == 2
    out = capsys.readouterr().out
    assert "unknown timezone" in out


def test_main_no_previous_tags_without_first_release(monkeypatch, capsys):
    import scripts.hummbl_release as mod

    monkeypatch.setattr(mod, "git_tag_exists", lambda t: False)
    monkeypatch.setattr(mod, "get_last_tag", lambda *a, **k: None)
    monkeypatch.setattr(sys, "argv", ["hummbl_release.py", "--project", "test", "--date", "2026.8.11"])
    rc = main()
    assert rc == 0  # dry run returns 0 even when no tags found
    out = capsys.readouterr().out
    assert "No previous tags found" in out


def test_main_bump_rejects_calver_version(monkeypatch, capsys):
    """If pyproject.toml has a CalVer-shaped version, --bump must refuse."""
    import scripts.hummbl_release as mod

    monkeypatch.setattr(mod, "git_tag_exists", lambda t: False)
    monkeypatch.setattr(mod, "get_last_tag", lambda *a, **k: "v2026.8.10")
    monkeypatch.setattr(mod, "get_commits_since", lambda *a, **k: ["- fix (abc)"])
    monkeypatch.setattr(mod, "read_pyproject_version", lambda: "2026.8.11")
    monkeypatch.setattr(mod, "read_init_version", lambda: None)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "hummbl_release.py",
            "--project",
            "test",
            "--bump",
            "minor",
            "--date",
            "2026.8.11",
        ],
    )
    rc = main()
    assert rc == 2
    out = capsys.readouterr().out
    # The CalVer guard in bump_semver raises, caught by main's error handling
    assert "CalVer date" in out or "not SemVer" in out
