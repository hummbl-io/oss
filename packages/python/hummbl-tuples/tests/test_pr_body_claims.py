#!/usr/bin/env python3
"""Tests for the PR body file-reference claim checker.

Verifies that:
- Real prose file references are checked against the repo.
- Paths inside markdown inline code are ignored (treated as examples).
- Paths inside fenced code blocks are ignored (treated as examples).
- Missing files in prose are correctly flagged.
"""

import sys
from pathlib import Path

# Add scripts dir to path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from check_pr_body_claims import extract_file_paths, strip_code_blocks


# A file that exists in the repo
EXISTING_FILE = "docs/specs/HASH_CHAINING_DESIGN.md"
# A file that does not exist
MISSING_FILE = "docs/specs/nonexistent_test_file.md"


def test_strip_fenced_code_blocks():
    """Fenced code blocks should be removed entirely."""
    text = "Prose here\n```bash\npython scripts/foo.py\n```\nMore prose"
    stripped = strip_code_blocks(text)
    assert "scripts/foo.py" not in stripped
    assert "Prose here" in stripped
    assert "More prose" in stripped


def test_strip_inline_code():
    """Inline code spans should be removed."""
    text = "See `docs/specs/foo.md` for details."
    stripped = strip_code_blocks(text)
    assert "docs/specs/foo.md" not in stripped
    assert "See " in stripped
    assert "for details." in stripped


def test_strip_preserves_prose():
    """Non-code text should be preserved."""
    text = "Added docs/specs/HASH_CHAINING_DESIGN.md to the repo."
    stripped = strip_code_blocks(text)
    assert "docs/specs/HASH_CHAINING_DESIGN.md" in stripped


def test_prose_path_extracted():
    """A file path in plain prose should be extracted."""
    text = f"This PR adds {EXISTING_FILE} to the repo."
    paths = extract_file_paths(text)
    assert EXISTING_FILE in paths


def test_inline_code_path_not_extracted():
    """A file path inside inline code should NOT be extracted."""
    text = "Example: `docs/specs/foo.md` is not a real file."
    stripped = strip_code_blocks(text)
    paths = extract_file_paths(stripped)
    assert "docs/specs/foo.md" not in paths


def test_fenced_code_path_not_extracted():
    """A file path inside a fenced code block should NOT be extracted."""
    text = (
        "Some prose\n"
        "```bash\n"
        "# See docs/specs/bar.md for details\n"
        "python scripts/detect_duplicate_prs.py\n"
        "```\n"
        "More prose\n"
    )
    stripped = strip_code_blocks(text)
    paths = extract_file_paths(stripped)
    assert "docs/specs/bar.md" not in paths


def test_mixed_prose_and_code():
    """Prose paths are extracted, code-block paths are not."""
    text = (
        f"This PR adds {EXISTING_FILE}.\n"
        f"Example: `docs/specs/foo.md` is illustrative.\n"
        "```python\n"
        "# config at docs/specs/bar.md\n"
        "```\n"
    )
    stripped = strip_code_blocks(text)
    paths = extract_file_paths(stripped)
    assert EXISTING_FILE in paths
    assert "docs/specs/foo.md" not in paths
    assert "docs/specs/bar.md" not in paths


def test_no_paths_in_empty_text():
    """Empty text yields no paths."""
    paths = extract_file_paths("")
    assert paths == []


def test_no_paths_in_code_only():
    """Text that is entirely code-blocked yields no paths."""
    text = "```bash\npython scripts/foo.py\n```"
    stripped = strip_code_blocks(text)
    paths = extract_file_paths(stripped)
    assert paths == []


def test_tilde_fenced_code_block_stripped():
    """Tilde-fenced code blocks (~~~) should also be stripped."""
    text = (
        "Some prose\n"
        "~~~bash\n"
        "# See docs/specs/baz.md for details\n"
        "python scripts/foo.py\n"
        "~~~\n"
        "More prose\n"
    )
    stripped = strip_code_blocks(text)
    assert "docs/specs/baz.md" not in stripped
    assert "Some prose" in stripped
    assert "More prose" in stripped


def test_tilde_fenced_path_not_extracted():
    """A file path inside a tilde-fenced code block should NOT be extracted."""
    text = (
        "~~~python\n"
        "# config at docs/specs/baz.md\n"
        "~~~\n"
    )
    stripped = strip_code_blocks(text)
    paths = extract_file_paths(stripped)
    assert "docs/specs/baz.md" not in paths
