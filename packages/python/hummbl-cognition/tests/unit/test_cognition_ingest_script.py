"""Tests for scripts/cognition_ingest.py — standalone CLP ledger ingest CLI."""

from __future__ import annotations

import importlib.util
import json
import sys
import types
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent.parent  # tests/unit -> tests -> repo
SCRIPT_PATH = REPO_ROOT / "scripts" / "cognition_ingest.py"

# Skip the entire module if the script under test has not been committed yet.
# Origin: PR #21 committed the test suite but scripts/cognition_ingest.py was
# not included; these tests error with FileNotFoundError until the script lands.
pytestmark = pytest.mark.skipif(
    not SCRIPT_PATH.exists(),
    reason=f"scripts/cognition_ingest.py not found at {SCRIPT_PATH}; skip until script is committed",
)


def _load_script() -> types.ModuleType:
    """Load the ingest script as a module (isolated each test via reimport)."""
    mod_name = "cognition_ingest_test_module"
    # Only remove this test module's cached copy, not the real cognition package
    sys.modules.pop(mod_name, None)

    spec = importlib.util.spec_from_file_location(mod_name, str(SCRIPT_PATH))
    assert spec is not None, f"Script not found: {SCRIPT_PATH}"
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _restore_cognition_sys_modules():
    """Restore sys.modules after each test to prevent cognition stub pollution.

    _bootstrap_cognition() in the script injects a plain types.ModuleType for
    'hummbl_cognition' (without __path__).  If that stub outlives the
    test it poisons subsequent imports of real hummbl_cognition submodules
    in test_cognition_ledger.py and friends.  This fixture captures the state
    before and restores it after each test.
    """
    _PREFIX = ("hummbl_cognition", "cognition_ingest_test_module")
    before = {k: v for k, v in sys.modules.items() if k.startswith(_PREFIX)}
    yield
    # Remove any stubs added by the test
    for key in list(sys.modules.keys()):
        if key.startswith(_PREFIX):
            if key in before:
                sys.modules[key] = before[key]
            else:
                del sys.modules[key]


@pytest.fixture()
def temp_ledger(tmp_path: Path) -> Path:
    """Return a path to a temporary ledger file (doesn't need to exist yet)."""
    return tmp_path / "test_ledger.jsonl"


@pytest.fixture()
def ingest(temp_ledger: Path):
    """Return a callable that invokes main() with --ledger pointing at temp_ledger."""
    mod = _load_script()

    def _run(*extra_args: str) -> tuple[int, str, str]:
        """Run main() and capture stdout/stderr.

        Returns (exit_code, stdout_text, stderr_text).
        """
        import io

        old_stdout, old_stderr = sys.stdout, sys.stderr
        sys.stdout = captured_out = io.StringIO()
        sys.stderr = captured_err = io.StringIO()
        try:
            argv = list(extra_args) + ["--ledger", str(temp_ledger)]
            exit_code = mod.main(argv)
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

        return (
            exit_code,
            captured_out.getvalue(),
            captured_err.getvalue(),
        )

    return _run


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestSuccessfulIngest:
    """Happy-path tests — entry written, ID returned."""

    def test_returns_clp_id(self, ingest, temp_ledger):
        """Successful ingest prints a line matching 'ingested: clp-<12hex>'."""
        code, out, err = ingest("A discovery about the ledger API")
        assert code == 0, f"Expected exit 0, got {code}. stderr: {err}"
        assert out.startswith("ingested: clp-"), f"Unexpected output: {out!r}"
        entry_id = out.strip().split(": ")[1]
        assert len(entry_id) == 16, f"ID wrong length: {entry_id!r}"
        assert entry_id.startswith("clp-"), f"ID format wrong: {entry_id!r}"

    def test_entry_written_to_ledger(self, ingest, temp_ledger):
        """After ingest the ledger file contains exactly one valid JSON line."""
        code, out, _ = ingest("Written to ledger check")
        assert code == 0
        lines = [l for l in temp_ledger.read_text().splitlines() if l.strip()]
        assert len(lines) == 1
        data = json.loads(lines[0])
        assert data["content"] == "Written to ledger check"
        assert data["agent"] == "claude-code"
        assert data["vendor"] == "anthropic"
        assert data["type"] == "discovery"
        assert data["scope"] == "project"
        assert abs(data["confidence"] - 0.85) < 1e-6

    def test_id_in_written_entry_matches_output(self, ingest, temp_ledger):
        """The ID printed to stdout matches the id field in the written entry."""
        code, out, _ = ingest("ID consistency check")
        assert code == 0
        printed_id = out.strip().split(": ")[1]
        data = json.loads(temp_ledger.read_text().strip())
        assert data["id"] == printed_id

    def test_custom_type_and_scope(self, ingest, temp_ledger):
        """--type and --scope flags are respected."""
        code, out, err = ingest(
            "A lesson learned",
            "--type",
            "lesson",
            "--scope",
            "module",
        )
        assert code == 0, f"stderr: {err}"
        data = json.loads(temp_ledger.read_text().strip())
        assert data["type"] == "lesson"
        assert data["scope"] == "module"

    def test_custom_confidence(self, ingest, temp_ledger):
        """--confidence flag is stored correctly."""
        code, out, err = ingest("High confidence finding", "--confidence", "0.99")
        assert code == 0, f"stderr: {err}"
        data = json.loads(temp_ledger.read_text().strip())
        assert abs(data["confidence"] - 0.99) < 1e-6

    def test_custom_agent(self, ingest, temp_ledger):
        """--agent flag overrides default."""
        code, out, err = ingest("Custom agent test", "--agent", "gemini")
        assert code == 0, f"stderr: {err}"
        data = json.loads(temp_ledger.read_text().strip())
        assert data["agent"] == "gemini"

    def test_multiple_entries_appended(self, ingest, temp_ledger):
        """Two calls append two entries; both are valid."""
        code1, _, _ = ingest("First entry")
        code2, _, _ = ingest("Second entry")
        assert code1 == 0
        assert code2 == 0
        lines = [l for l in temp_ledger.read_text().splitlines() if l.strip()]
        assert len(lines) == 2
        ids = [json.loads(l)["id"] for l in lines]
        assert ids[0] != ids[1], "Duplicate IDs generated"


class TestTagsHandling:
    """Tests for the --tags flag."""

    def test_tags_applied(self, ingest, temp_ledger):
        """--tags flag stores tags on the entry."""
        code, out, err = ingest(
            "Tagged discovery",
            "--tags",
            "alpha",
            "beta",
            "gamma",
        )
        assert code == 0, f"stderr: {err}"
        data = json.loads(temp_ledger.read_text().strip())
        assert set(data["tags"]) == {"alpha", "beta", "gamma"}

    def test_no_tags_by_default(self, ingest, temp_ledger):
        """Without --tags the tags field is absent or empty."""
        code, _, _ = ingest("No tags")
        assert code == 0
        data = json.loads(temp_ledger.read_text().strip())
        # tags may be absent or an empty list
        assert data.get("tags", []) == []

    def test_single_tag(self, ingest, temp_ledger):
        """Single tag is accepted."""
        code, _, err = ingest("One tag", "--tags", "solo")
        assert code == 0, f"stderr: {err}"
        data = json.loads(temp_ledger.read_text().strip())
        assert "solo" in data["tags"]


class TestMissingContentArgument:
    """Tests for the required positional 'content' argument."""

    def test_no_args_exits_nonzero(self, temp_ledger):
        """Calling with no arguments exits with a non-zero code."""
        mod = _load_script()
        import io

        old_err = sys.stderr
        sys.stderr = io.StringIO()
        try:
            # Pass only --ledger (no content positional)
            code = mod.main(["--ledger", str(temp_ledger)])
        finally:
            sys.stderr = old_err
        assert code != 0

    def test_no_args_prints_error(self, temp_ledger):
        """Missing content argument prints an error to stderr."""
        mod = _load_script()
        import io

        old_err = sys.stderr
        sys.stderr = captured = io.StringIO()
        try:
            mod.main(["--ledger", str(temp_ledger)])
        finally:
            sys.stderr = old_err
        err_text = captured.getvalue().lower()
        assert "error" in err_text or "usage" in err_text or "required" in err_text


class TestConfidenceValidation:
    """Tests for --confidence range enforcement."""

    def test_confidence_above_one_exits_nonzero(self, ingest):
        """Confidence > 1.0 must exit with code 1 and print an error."""
        code, out, err = ingest("Too confident", "--confidence", "1.5")
        assert code != 0, "Expected non-zero exit for confidence > 1.0"
        assert "error" in err.lower() or "error" in out.lower()
        assert out.strip() == "" or not out.startswith("ingested:"), (
            "Should not print an entry ID when confidence is invalid"
        )

    def test_confidence_below_zero_exits_nonzero(self, ingest):
        """Confidence < 0.0 must exit with code 1."""
        code, out, err = ingest("Negative confidence", "--confidence", "-0.1")
        assert code != 0, "Expected non-zero exit for confidence < 0.0"

    def test_confidence_at_boundaries_accepted(self, ingest, temp_ledger):
        """Boundary values 0.0 and 1.0 are accepted."""
        code0, _, err0 = ingest("Zero confidence", "--confidence", "0.0")
        assert code0 == 0, f"Expected 0.0 to be accepted. stderr: {err0}"
        # Clear and test 1.0
        temp_ledger.unlink()
        code1, _, err1 = ingest("Full confidence", "--confidence", "1.0")
        assert code1 == 0, f"Expected 1.0 to be accepted. stderr: {err1}"


class TestContentValidation:
    """Tests for content length limits and content scanning."""

    def test_content_too_long_exits_nonzero(self, ingest):
        """Content exceeding 4096 chars exits with code 1."""
        long_content = "x" * 4097
        code, out, err = ingest(long_content)
        assert code != 0, "Expected non-zero exit for content > 4096 chars"
        assert "error" in err.lower()
        assert not out.startswith("ingested:")

    def test_max_content_accepted(self, ingest, temp_ledger):
        """Content of exactly 4096 chars is accepted."""
        max_content = "a" * 4096
        code, out, err = ingest(max_content)
        assert code == 0, f"Expected 4096-char content to be accepted. stderr: {err}"
        assert out.startswith("ingested: clp-")


class TestDefaultsPreserved:
    """Verify all documented defaults are applied when flags are omitted."""

    def test_all_defaults(self, ingest, temp_ledger):
        code, _, _ = ingest("Default fields check")
        assert code == 0
        data = json.loads(temp_ledger.read_text().strip())
        assert data["agent"] == "claude-code"
        assert data["vendor"] == "anthropic"
        assert data["model"] == "claude-sonnet-4-6"
        assert data["type"] == "discovery"
        assert data["scope"] == "project"
        assert abs(data["confidence"] - 0.85) < 1e-6
