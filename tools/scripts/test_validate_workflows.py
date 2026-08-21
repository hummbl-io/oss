#!/usr/bin/env python3
"""Unit tests for validate_workflows.py.

This test file is stdlib-only and matches the validator's stdlib-only
constraint. It can be run with:

    python test_validate_workflows.py

When placed next to validate_workflows.py (e.g. tools/scripts/) it loads the
neighbour. When run from the review draft location it can find the checked-out
repo or the WORKFLOW_VALIDATOR_PATH environment variable.
"""

import importlib.util
import os
import sys
import tempfile
import textwrap
import types
import unittest
from pathlib import Path
from unittest.mock import patch


def _load_validator():
    here = Path(__file__).resolve().parent

    env = os.environ.get("WORKFLOW_VALIDATOR_PATH")
    if env:
        candidate = Path(env)
        if candidate.exists():
            spec = importlib.util.spec_from_file_location("validate_workflows", candidate)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod

    candidate = here / "validate_workflows.py"
    if candidate.exists():
        spec = importlib.util.spec_from_file_location("validate_workflows", candidate)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    candidate = here / "hummbl-oss-work" / "tools" / "scripts" / "validate_workflows.py"
    if candidate.exists():
        spec = importlib.util.spec_from_file_location("validate_workflows", candidate)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    raise FileNotFoundError(
        "Could not find validate_workflows.py. "
        "Place this test in the same directory as validate_workflows.py "
        "or set WORKFLOW_VALIDATOR_PATH to the validator file."
    )


validate_workflows = _load_validator()


class TestValidateFile(unittest.TestCase):
    """Tests for the validate_file() function."""

    VALID_SHA = "11d5960a326750d5838078e36cf38b85af677262"
    OTHER_SHA = "a26af69be951a213d495a4c3e4e4022e16d87065"

    @staticmethod
    def _write(path, content, newline="\n"):
        data = content.encode("utf-8")
        if newline != "\n":
            data = data.replace(b"\n", newline.encode("utf-8"))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def _validate(self, content, envs=None, name="test.yml", newline="\n"):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / ".github" / "workflows" / name
            self._write(p, content, newline)
            return validate_workflows.validate_file(p, envs)

    def _fails(self, issues):
        return [i for i in issues if i[0] == "FAIL"]

    def _warns(self, issues):
        return [i for i in issues if i[0] == "WARN"]

    def test_sha_pinned_workflow_passes(self):
        content = textwrap.dedent(f"""
        name: Test

        "on":
          push:

        jobs:
          build:
            runs-on: ubuntu-latest
            environment: pypi
            steps:
              - uses: actions/checkout@{self.VALID_SHA}
              - uses: actions/setup-python@{self.OTHER_SHA}
        """).lstrip()
        issues = self._validate(content, envs=["pypi"])
        self.assertEqual(issues, [])

    def test_tag_ref_violates_sha_pin(self):
        content = textwrap.dedent("""
        name: Test

        "on":
          push:

        jobs:
          build:
            steps:
              - uses: actions/checkout@v4
        """).lstrip()
        issues = self._validate(content)
        fails = self._fails(issues)
        self.assertEqual(len(fails), 1)
        self.assertIn("SHA-pin violation", fails[0][1])
        self.assertIn("actions/checkout@v4", fails[0][1])
        self.assertIsNotNone(fails[0][2])

    def test_branch_ref_violates_sha_pin(self):
        for ref in ("main", "stable", "latest", "master"):
            with self.subTest(ref=ref):
                content = (
                    f'"on":\n'
                    f'  push:\n\n'
                    f'jobs:\n'
                    f'  build:\n'
                    f'    steps:\n'
                    f'      - uses: actions/checkout@{ref}\n'
                )
                issues = self._validate(content)
                fails = self._fails(issues)
                self.assertEqual(len(fails), 1, f"expected FAIL for @{ref}")
                self.assertIn(f"actions/checkout@{ref}", fails[0][1])

    def test_local_workflow_not_flagged(self):
        content = textwrap.dedent("""
        name: Test

        "on":
          push:

        jobs:
          build:
            steps:
              - uses: ./.github/workflows/check.yml
        """).lstrip()
        issues = self._validate(content)
        self.assertEqual(self._fails(issues), [])

    def test_sha_with_inline_comment_passes(self):
        content = textwrap.dedent(f"""
        name: Test

        "on":
          push:

        jobs:
          build:
            steps:
              - uses: actions/checkout@{self.VALID_SHA}  # v4.2.2
        """).lstrip()
        issues = self._validate(content)
        self.assertEqual(self._fails(issues), [])

    def test_quoted_action_name_passes(self):
        content = textwrap.dedent(f"""
        name: Test

        "on":
          push:

        jobs:
          build:
            steps:
              - uses: "actions/checkout@{self.VALID_SHA}"
              - uses: 'actions/setup-python@{self.OTHER_SHA}'
        """).lstrip()
        issues = self._validate(content)
        self.assertEqual(self._fails(issues), [])

    def test_non_ascii_em_dash_fails(self):
        content = textwrap.dedent(f"""
        name: Test

        "on":
          push:

        # This comment has an em\u2014dash
        jobs:
          build:
            steps:
              - uses: actions/checkout@{self.VALID_SHA}
        """).lstrip()
        issues = self._validate(content)
        fails = self._fails(issues)
        self.assertEqual(len(fails), 1)
        self.assertIn("U+2014", fails[0][1])
        self.assertIn("EM DASH", fails[0][1])

    def test_non_ascii_smart_quote_fails(self):
        content = textwrap.dedent(f"""
        name: Test

        "on":
          push:

        jobs:
          build:
            steps:
              - name: Build \u201cdocs\u201d
              - uses: actions/checkout@{self.VALID_SHA}
        """).lstrip()
        issues = self._validate(content)
        fails = self._fails(issues)
        self.assertEqual(len(fails), 1)
        self.assertIn("U+201C", fails[0][1])

    def test_crlf_fails(self):
        content = textwrap.dedent("""
        name: Test

        "on":
          push:
        """).lstrip()
        issues = self._validate(content, newline="\r\n")
        fails = self._fails(issues)
        self.assertEqual(len(fails), 1)
        self.assertIn("CRLF", fails[0][1])
        self.assertIsNone(fails[0][2])

    def test_mixed_line_endings_fails(self):
        content = "name: test\n\"on\":\n  push:\r\n"
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "test.yml"
            p.write_bytes(content.encode("utf-8"))
            issues = validate_workflows.validate_file(p, None)
        fails = self._fails(issues)
        self.assertTrue(any("CRLF" in i[1] for i in fails))

    def test_lf_only_passes(self):
        content = textwrap.dedent(f"""
        name: Test

        "on":
          push:

        jobs:
          build:
            steps:
              - uses: actions/checkout@{self.VALID_SHA}
        """).lstrip()
        issues = self._validate(content)
        self.assertEqual(issues, [])

    def test_unquoted_on_warns(self):
        content = textwrap.dedent(f"""
        name: Test

        on:
          push:

        jobs:
          build:
            steps:
              - uses: actions/checkout@{self.VALID_SHA}
        """).lstrip()
        issues = self._validate(content)
        warns = self._warns(issues)
        self.assertEqual(len(warns), 1)
        self.assertIn("Unquoted 'on:' key", warns[0][1])

    def test_quoted_on_does_not_warn(self):
        content = textwrap.dedent(f"""
        name: Test

        "on":
          push:

        jobs:
          build:
            steps:
              - uses: actions/checkout@{self.VALID_SHA}
        """).lstrip()
        issues = self._validate(content)
        self.assertEqual(self._warns(issues), [])

    def test_environment_exists_passes(self):
        content = textwrap.dedent(f"""
        name: Test

        "on":
          push:

        jobs:
          build:
            environment: pypi
            steps:
              - uses: actions/checkout@{self.VALID_SHA}
        """).lstrip()
        issues = self._validate(content, envs=["pypi"])
        self.assertEqual(issues, [])

    def test_environment_missing_warns(self):
        content = textwrap.dedent(f"""
        name: Test

        "on":
          push:

        jobs:
          build:
            environment: npm
            steps:
              - uses: actions/checkout@{self.VALID_SHA}
        """).lstrip()
        issues = self._validate(content, envs=["pypi"])
        warns = self._warns(issues)
        self.assertEqual(len(warns), 1)
        self.assertIn("npm", warns[0][1])
        self.assertIn("does not exist", warns[0][1])

    def test_environment_check_skipped_when_gh_unavailable(self):
        content = textwrap.dedent(f"""
        name: Test

        "on":
          push:

        jobs:
          build:
            environment: npm
            steps:
              - uses: actions/checkout@{self.VALID_SHA}
        """).lstrip()
        issues = self._validate(content, envs=None)
        self.assertEqual(issues, [])

    def test_empty_file_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "empty.yml"
            p.write_bytes(b"")
            issues = validate_workflows.validate_file(p, None)
        self.assertEqual(issues, [])

    def test_no_uses_directives_passes(self):
        content = textwrap.dedent("""
        name: Test

        "on":
          push:

        jobs:
          build:
            runs-on: ubuntu-latest
            steps:
              - run: echo hi
        """).lstrip()
        issues = self._validate(content)
        self.assertEqual(issues, [])

    def test_nested_action_path_pinned_sha_is_accepted(self):
        # PR #1 (MONOREPO-DESIGN.md 4.5) uses gradle/actions/setup-gradle@<sha>.
        # This is a valid SHA-pinned action with a sub-path.
        content = textwrap.dedent("""
        name: Test

        "on":
          push:

        jobs:
          build:
            steps:
              - uses: gradle/actions/setup-gradle@ed408507eac070d1f99cc633dbcf757c94c7933a
        """).lstrip()
        issues = self._validate(content)
        self.assertEqual(self._fails(issues), [])

    def test_sha_with_comment_two_spaces(self):
        # Matches the DeterminateSystems examples in PR #1.
        content = textwrap.dedent("""
        name: Test

        "on":
          push:

        jobs:
          build:
            steps:
              - uses: DeterminateSystems/nix-installer-action@ef8a148080ab6020fd15196c2084a2eea5ff2d25  # v22
        """).lstrip()
        issues = self._validate(content)
        self.assertEqual(self._fails(issues), [])


class TestGetEnvironments(unittest.TestCase):
    """Tests for the gh api environment lookup."""

    def _run(self, mock_run):
        with patch.object(validate_workflows.subprocess, "run", mock_run):
            return validate_workflows.get_environments("hummbl-io/oss")

    def test_gh_not_found(self):
        def mock_run(*args, **kwargs):
            raise FileNotFoundError()
        envs, err = self._run(mock_run)
        self.assertEqual(envs, [])
        self.assertEqual(err, "gh CLI not found")

    def test_gh_timeout(self):
        def mock_run(*args, **kwargs):
            raise validate_workflows.subprocess.TimeoutExpired("gh", 15)
        envs, err = self._run(mock_run)
        self.assertEqual(envs, [])
        self.assertEqual(err, "gh api timed out")

    def test_gh_api_failure(self):
        def mock_run(*args, **kwargs):
            return types.SimpleNamespace(returncode=1, stdout="", stderr="auth failed")
        envs, err = self._run(mock_run)
        self.assertEqual(envs, [])
        self.assertEqual(err, "auth failed")

    def test_gh_api_success(self):
        def mock_run(*args, **kwargs):
            return types.SimpleNamespace(returncode=0, stdout="pypi\nnpm\n\n", stderr="")
        envs, err = self._run(mock_run)
        self.assertEqual(envs, ["pypi", "npm"])
        self.assertIsNone(err)

    def test_gh_api_empty(self):
        def mock_run(*args, **kwargs):
            return types.SimpleNamespace(returncode=0, stdout="", stderr="")
        envs, err = self._run(mock_run)
        self.assertEqual(envs, [])
        self.assertIsNone(err)


class TestMain(unittest.TestCase):
    """Tests for the main() entry point and CLI behaviour."""

    VALID_SHA = "11d5960a326750d5838078e36cf38b85af677262"

    @staticmethod
    def _write_workflow(tmp, content, name="test.yml", newline="\n"):
        wdir = Path(tmp) / ".github" / "workflows"
        wdir.mkdir(parents=True, exist_ok=True)
        p = wdir / name
        data = content.encode("utf-8")
        if newline != "\n":
            data = data.replace(b"\n", newline.encode("utf-8"))
        p.write_bytes(data)

    def _main(self, tmp, envs=(), env_error=None, repo="hummbl-io/oss"):
        if env_error is None:
            return_value = (list(envs), None)
        else:
            return_value = ([], env_error)
        with patch.object(validate_workflows, "get_environments", return_value=return_value):
            wdir = Path(tmp) / ".github" / "workflows"
            with patch("sys.argv", ["validate_workflows.py", "--workflows-dir", str(wdir), "--repo", repo]):
                return validate_workflows.main()

    def test_main_no_workflows_dir_returns_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            wdir = Path(tmp) / "missing"
            with patch("sys.argv", ["validate_workflows.py", "--workflows-dir", str(wdir)]):
                with patch.object(validate_workflows, "get_environments", return_value=(["pypi"], None)):
                    self.assertEqual(validate_workflows.main(), 0)

    def test_main_empty_workflows_dir_returns_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            wdir = Path(tmp) / ".github" / "workflows"
            wdir.mkdir(parents=True, exist_ok=True)
            with patch("sys.argv", ["validate_workflows.py", "--workflows-dir", str(wdir)]):
                with patch.object(validate_workflows, "get_environments", return_value=(["pypi"], None)):
                    self.assertEqual(validate_workflows.main(), 0)

    def test_main_failing_workflow_returns_one(self):
        content = textwrap.dedent("""
        name: Test

        "on":
          push:

        jobs:
          build:
            steps:
              - uses: actions/checkout@v4
        """).lstrip()
        with tempfile.TemporaryDirectory() as tmp:
            self._write_workflow(tmp, content)
            self.assertEqual(self._main(tmp), 1)

    def test_main_warnings_only_returns_zero(self):
        content = textwrap.dedent(f"""
        name: Test

        on:
          push:

        jobs:
          build:
            environment: npm
            steps:
              - uses: actions/checkout@{self.VALID_SHA}
        """).lstrip()
        with tempfile.TemporaryDirectory() as tmp:
            self._write_workflow(tmp, content)
            self.assertEqual(self._main(tmp, envs=["pypi"]), 0)

    def test_main_gh_missing_still_returns_one_for_sha_violation(self):
        content = textwrap.dedent("""
        name: Test

        "on":
          push:

        jobs:
          build:
            steps:
              - uses: actions/checkout@v4
        """).lstrip()
        with tempfile.TemporaryDirectory() as tmp:
            self._write_workflow(tmp, content)
            self.assertEqual(self._main(tmp, env_error="gh CLI not found"), 1)

    def test_main_gh_missing_skips_environment_check(self):
        content = textwrap.dedent(f"""
        name: Test

        "on":
          push:

        jobs:
          build:
            environment: npm
            steps:
              - uses: actions/checkout@{self.VALID_SHA}
        """).lstrip()
        with tempfile.TemporaryDirectory() as tmp:
            self._write_workflow(tmp, content)
            self.assertEqual(self._main(tmp, env_error="gh CLI not found"), 0)


class TestContributingExamples(unittest.TestCase):
    """Validate that the right/wrong examples in CONTRIBUTING.md do what they claim."""

    def test_contributing_wrong_sha_example_is_rejected(self):
        content = "- uses: actions/checkout@v4\n"
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "wrong.yml"
            p.write_bytes(content.encode("utf-8"))
            issues = validate_workflows.validate_file(p, None)
        fails = [i for i in issues if i[0] == "FAIL"]
        self.assertEqual(len(fails), 1)
        self.assertIn("actions/checkout@v4", fails[0][1])

    def test_contributing_right_sha_example_is_accepted(self):
        content = "- uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262\n"
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "right.yml"
            p.write_bytes(content.encode("utf-8"))
            issues = validate_workflows.validate_file(p, None)
        self.assertEqual(issues, [])

    def test_contributing_wrong_on_example_warns(self):
        content = 'on:\n  push:\n    tags: ["python/*/v*"]\n'
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "wrong.yml"
            p.write_bytes(content.encode("utf-8"))
            issues = validate_workflows.validate_file(p, None)
        warns = [i for i in issues if i[0] == "WARN"]
        self.assertEqual(len(warns), 1)
        self.assertIn("Unquoted 'on:' key", warns[0][1])

    def test_contributing_right_on_example_is_accepted(self):
        content = '"on":\n  push:\n    tags: ["python/*/v*"]\n'
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "right.yml"
            p.write_bytes(content.encode("utf-8"))
            issues = validate_workflows.validate_file(p, None)
        self.assertEqual(issues, [])


if __name__ == "__main__":
    unittest.main()