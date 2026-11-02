#!/usr/bin/env python3
"""Unit tests for validate_workflows.py.

This test file is stdlib-only and matches the validator's stdlib-only
constraint. It can be run with:

    python test_validate_workflows.py

When placed next to validate_workflows.py (e.g. tools/scripts/) it loads the
neighbour. When run from the review draft location it can find the checked-out
repo or the WORKFLOW_VALIDATOR_PATH environment variable.
"""

import contextlib
import importlib.util
import io
import os
import re
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


class TestPythonPackageMatrix(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.wdir = self.root / ".github" / "workflows"
        self.wdir.mkdir(parents=True)
        self.package("alpha")
        self.package("beta")
        self.workflow()

    def package(self, name, manifest=True, tests=True):
        package = self.root / "packages" / "python" / name
        package.mkdir(parents=True, exist_ok=True)
        if manifest:
            (package / "pyproject.toml").write_text('[project]\nname = "example"\n')
        if tests:
            (package / "tests").mkdir()

    def workflow(self, packages="alpha, beta", extra=""):
        # Use the real workflow as the supported-layout fixture, not a copy of
        # the validator's expected program. Only the synthetic inventory varies.
        source = Path(validate_workflows.__file__).resolve().parents[2]
        text = (source / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        before, preview = text.split("  test-preview:\n", 1)
        preview = re.sub(r"(?m)^        package: \[[^\n]*\]\n",
                         lambda _: f"        package: [{packages}]\n{extra}", preview, count=1)
        text = before + "  test-preview:\n" + preview
        (self.wdir / "ci.yml").write_bytes(text.encode())

    def issues(self):
        return validate_workflows.validate_python_package_matrix(self.wdir)

    def test_manifest_directory_names_match_preview_and_discovery(self):
        # Distribution names need not equal package directory names. Neither
        # unrelated Node entries nor the dynamic main matrix is a preview list.
        self.workflow("'alpha', \"beta\"")
        self.assertEqual(self.issues(), [])

    def test_main_matrix_cannot_be_narrowed_even_with_complete_preview(self):
        path = self.wdir / "ci.yml"
        text = path.read_text().replace(
            'matrix: ${{ fromJSON(needs.changes.outputs.matrix) }}',
            'matrix:\n        package: [alpha]\n        python-version: ["3.13"]',
        )
        path.write_text(text)
        self.assertTrue(any("main matrix wiring" in issue[1] for issue in self.issues()))

    def test_discovery_output_and_consumer_cannot_be_disconnected(self):
        mutations = [
            ('matrix: ${{ steps.matrix.outputs.json }}', 'matrix: ${{ steps.decoy.outputs.json }}'),
            ('needs: changes', 'needs: decoy'),
            ('fromJSON(needs.changes.outputs.matrix)', 'fromJSON(needs.decoy.outputs.matrix)'),
            ('      - id: matrix\n', '      - id: decoy\n'),
            ('find packages/python -maxdepth', 'find packages/python/alpha -maxdepth'),
            ('PKGS="$ALL"', 'PKGS="alpha"'),
            ('PKGS="$ALL"', "PKGS='$ALL'"),  # Quoting changes expansion semantics.
            ('echo "json=$MATRIX"', 'echo "json=[]"'),
            ('>> "$GITHUB_OUTPUT"', '>> /tmp/unconsumed-output'),
            ('working-directory: packages/python/${{ matrix.package }}',
             'working-directory: packages/python/alpha'),
            ('python-version: ${{ matrix.python-version }}', 'python-version: "3.13"'),
            ('      - id: matrix\n', '      - id: matrix\n        if: false\n'),
            ('  test:\n', '  test:\n    if: false\n'),
        ]
        for old, new in mutations:
            with self.subTest(old=old, new=new):
                self.workflow()
                path = self.wdir / "ci.yml"
                original = path.read_text()
                self.assertIn(old, original)
                path.write_text(original.replace(old, new))
                self.assertTrue(any("main matrix wiring" in issue[1] for issue in self.issues()))

    def test_extra_output_override_is_not_hidden_by_valid_discovery(self):
        path = self.wdir / "ci.yml"
        text = path.read_text().replace(
            '          echo "json=$MATRIX" >> "$GITHUB_OUTPUT"',
            '          echo "json=$MATRIX" >> "$GITHUB_OUTPUT"\n'
            '          echo \'json={"package":["alpha"]}\' >> "$GITHUB_OUTPUT"',
        )
        path.write_text(text)
        self.assertTrue(any("producer commands changed" in issue[1] for issue in self.issues()))

    def test_unused_valid_producer_does_not_satisfy_narrowed_real_producer(self):
        path = self.wdir / "ci.yml"
        text = path.read_text().replace('      - id: matrix\n', '      - id: decoy\n')
        text = text.replace('\n  test:\n', (
            '\n      - id: matrix\n'
            '        env:\n'
            '          EVENT_NAME: ${{ github.event_name }}\n'
            '          BASE_REF: ${{ github.base_ref }}\n'
            '        run: |\n'
            '          echo \'json={"package":["alpha"]}\' >> "$GITHUB_OUTPUT"\n'
            '  test:\n'
        ))
        path.write_text(text)
        self.assertTrue(any("producer commands changed" in issue[1] for issue in self.issues()))

    def test_main_producer_comments_and_outer_indentation_are_supported(self):
        path = self.wdir / "ci.yml"
        text = path.read_text().replace('          set -euo pipefail',
                                        '          # Additional explanation.\n          set -euo pipefail')
        text = text.replace('            git fetch -q origin', '              git fetch -q origin')
        path.write_text(text)
        self.assertEqual(self.issues(), [])

    def test_shell_word_boundaries_cannot_be_erased_by_normalization(self):
        mutations = [
            ('MATRIX=$(jq -nc', 'MATRIX=$ (jq -nc'),
            ('"$PKG_JSON" --argjson', '"$PKG_JSON"--argjson'),
            ("printf '%s\\n' \"$PKGS\" | jq", "printf '%s\\n'\"$PKGS\" | jq"),
        ]
        for old, new in mutations:
            with self.subTest(new=new):
                self.workflow()
                path = self.wdir / "ci.yml"
                text = path.read_text()
                self.assertIn(old, text)
                path.write_text(text.replace(old, new))
                self.assertTrue(any("producer commands changed" in issue[1] for issue in self.issues()))

    def test_unsupported_shell_reformatting_fails_closed(self):
        # This is a narrow physical-command check, not a Bash equivalence parser.
        # Even harmless internal whitespace/continuation changes require review.
        mutations = [
            ('find packages/python', 'find   packages/python'),
            (' \\\n            \'{"python-version"', ' \'{"python-version"'),
            (' \\\n            \'{"python-version"', ' \\\n          # interrupts continuation\n            \'{"python-version"'),
            (' \\\n            \'{"python-version"', ' \\\n\n            \'{"python-version"'),
        ]
        for old, new in mutations:
            with self.subTest(new=new):
                self.workflow()
                path = self.wdir / "ci.yml"
                text = path.read_text()
                self.assertIn(old, text)
                path.write_text(text.replace(old, new))
                self.assertTrue(any("main matrix wiring" in issue[1] for issue in self.issues()))

    def test_yaml_identifiers_conditions_and_defaults_fail_closed(self):
        mutations = [
            ('    needs: changes\n', '    needs: ch anges\n'),
            ('steps.matrix.outputs.json', 'steps.mat rix.outputs.json'),
            ('matrix.package }}', 'matrix.pack age }}'),
            ('  test:\n', '  test:\n    "if": false\n'),
            ('  changes:\n', "  changes:\n    'if': false\n"),
            ('  changes:\n', '  changes:\n    defaults:\n      run:\n        working-directory: packages/python\n'),
            ('jobs:\n', 'defaults:\n  run:\n    working-directory: packages/python\njobs:\n'),
        ]
        for old, new in mutations:
            with self.subTest(new=new):
                self.workflow()
                path = self.wdir / "ci.yml"
                text = path.read_text()
                self.assertIn(old, text)
                path.write_text(text.replace(old, new))
                self.assertTrue(any("main matrix wiring" in issue[1] for issue in self.issues()))

    def test_decoy_directories_cannot_replace_actual_install_and_test_bindings(self):
        path = self.wdir / "ci.yml"
        text = path.read_text().replace(
            '        working-directory: packages/python/${{ matrix.package }}',
            '        "working-directory": packages/python/hummbl-governance', 2,
        )
        decoy = ('      - name: Decoy directory selector\n'
                 '        working-directory: packages/python/${{ matrix.package }}\n'
                 '        run: echo no-tests\n')
        text = text.replace('  test-preview:\n', decoy * 2 + '  test-preview:\n')
        path.write_text(text)
        self.assertTrue(any("main matrix wiring" in issue[1] for issue in self.issues()))

    def test_decoy_python_version_cannot_replace_actual_setup_binding(self):
        path = self.wdir / "ci.yml"
        before, test = path.read_text().split('  test:\n', 1)
        test = test.replace('          python-version: ${{ matrix.python-version }}',
                            '          "python-version": "3.13"', 1)
        test = test.replace('          persist-credentials: false',
                            '          persist-credentials: false\n'
                            '          python-version: ${{ matrix.python-version }}', 1)
        path.write_text(before + '  test:\n' + test)
        self.assertTrue(any("main matrix wiring" in issue[1] for issue in self.issues()))

    def test_later_setup_cannot_override_matrix_version(self):
        setup_sha = '5fda3b95a4ea91299a34e894583c3862153e4b97'
        for key in ('uses', '"uses"', "'uses'"):
            with self.subTest(key=key):
                self.workflow()
                path = self.wdir / "ci.yml"
                text = path.read_text().replace('      - name: Install package and test dependencies\n', (
                    '      - name: Actual setup after decoy\n'
                    f'        {key}: actions/setup-python@{setup_sha}\n'
                    '        with:\n'
                    '          python-version: "3.13"\n'
                    '      - name: Install package and test dependencies\n'
                ), 1)
                path.write_text(text)
                self.assertTrue(any("main matrix wiring" in issue[1] for issue in self.issues()))

    def test_consumer_binding_overrides_and_conditions_fail_closed(self):
        mutations = [
            ('        working-directory: packages/python/${{ matrix.package }}',
             ('        working-directory: packages/python/${{ matrix.package }}\n'
              '        "working-directory": packages/python/hummbl-governance')),
            ('      - name: Run tests\n', '      - name: Run tests\n        "if": false\n'),
            ('      - name: Run tests\n', '      - name: Run tests\n        <<: *overrides\n'),
            ('          python-version: ${{ matrix.python-version }}',
             '          python-version: ${{ matrix.python-version }}\n          "python-version": "3.13"'),
        ]
        for old, new in mutations:
            with self.subTest(new=new):
                self.workflow()
                path = self.wdir / "ci.yml"
                text = path.read_text()
                self.assertIn(old, text)
                path.write_text(text.replace(old, new))
                self.assertTrue(any("main matrix wiring" in issue[1] for issue in self.issues()))

    def test_inventory_is_relative_to_workflows_directory_not_cwd(self):
        with contextlib.chdir(self.root.parent):
            self.assertEqual(self.issues(), [])

    def test_new_manifest_missing_from_preview_fails(self):
        self.package("gamma")
        self.assertIn("preview matrix drift: missing=gamma", self.issues()[0][1])

    def test_removed_package_remaining_in_preview_fails(self):
        self.workflow("alpha, beta, deleted")
        self.assertIn("extra=deleted", self.issues()[0][1])

    def test_manifest_without_tests_cannot_silently_escape_main_matrix(self):
        self.package("gamma", tests=False)
        self.workflow("alpha, beta, gamma")
        self.assertIn("tests-directory discovery drift: missing=gamma", self.issues()[0][1])

    def test_tests_directory_without_manifest_fails(self):
        self.package("orphan", manifest=False)
        self.assertIn("tests-directory discovery drift: extra=orphan", self.issues()[0][1])

    def test_duplicate_preview_package_fails(self):
        self.workflow("alpha, beta, alpha")
        self.assertIn("Duplicate package", self.issues()[0][1])

    def test_unsupported_or_malformed_preview_fails_closed(self):
        for packages in ("", "alpha, beta,", "alpha, ${{ matrix.other }}", "'alpha, beta"):
            with self.subTest(packages=packages):
                self.workflow(packages)
                self.assertTrue(self.issues())
        for extra in ("        exclude: []\n", "        package: [alpha, beta]\n"):
            with self.subTest(extra=extra):
                self.workflow(extra=extra)
                self.assertTrue(self.issues())

    def test_missing_named_preview_is_not_satisfied_by_node_matrix(self):
        path = self.wdir / "ci.yml"
        path.write_text(path.read_text().replace("test-preview:", "other-preview:"))
        self.assertTrue(self.issues())

    def test_missing_ci_or_empty_inventory_fails(self):
        (self.wdir / "ci.yml").unlink()
        self.assertIn("CI workflow not found", self.issues()[0][1])
        self.workflow()
        for package in ("alpha", "beta"):
            (self.root / "packages" / "python" / package / "pyproject.toml").unlink()
        self.assertIn("No Python package manifests", self.issues()[0][1])

    def test_cli_opt_in_turns_matrix_drift_into_failure(self):
        self.package("gamma")
        with patch.object(validate_workflows, "get_environments", return_value=([], None)):
            with patch("sys.argv", ["validate_workflows.py", "--workflows-dir", str(self.wdir),
                                    "--check-python-packages"]):
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(validate_workflows.main(), 1)

    def test_cli_opt_in_rejects_missing_workflows(self):
        with patch("sys.argv", ["validate_workflows.py", "--workflows-dir",
                                str(self.root / "missing"), "--check-python-packages"]):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(validate_workflows.main(), 1)


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
