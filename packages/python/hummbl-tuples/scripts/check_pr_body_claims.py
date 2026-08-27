#!/usr/bin/env python3
"""Verify file references in PR bodies against the actual commit.

When a PR body claims a file exists (e.g. a checklist item like
"[x] Design rationale document" referencing ``docs/specs/HASH_CHAINING_DESIGN.md``),
this script checks that the referenced file actually exists in the
current tree. This catches the failure mode where a PR body lists a
deliverable as done but the file was never committed.

Conservative first pass — known limitations:

1. Only checks explicit file paths that appear in the PR body text.
   Does not parse checklist semantics (a "[x]" next to a description
   without a path is not checked).
2. Only checks paths that look like repo-relative file paths
   (contain a ``/`` or a known extension like ``.md``, ``.json``,
   ``.py``, ``.yml``, ``.yaml``, ``.schema.json``).
3. Does not fetch the PR body from GitHub — accepts the body as
   stdin or a ``--body-file`` argument, so it can be used locally
   or in CI via ``gh pr view --json body``.
4. Ignores file paths inside markdown fenced code blocks (``` ... ```)
   and inline-code spans (`` `...` ``). These are treated as examples,
   not real file references.

Usage::

    # From a PR body file
    python scripts/check_pr_body_claims.py --body-file pr_body.md

    # From gh pr view output
    gh pr view <PR_NUMBER> --json body --jq '.body' | python scripts/check_pr_body_claims.py

    # Piped from stdin
    echo "Added docs/specs/FOO.md" | python scripts/check_pr_body_claims.py

Exit codes:
    0 — all referenced files exist, or no file references found
    1 — one or more referenced files do not exist
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Extensions that indicate a repo-relative file path
_FILE_EXTENSIONS = {
    ".md",
    ".json",
    ".py",
    ".yml",
    ".yaml",
    ".txt",
    ".rst",
    ".schema.json",
    ".toml",
    ".cfg",
    ".ini",
    ".sh",
    ".js",
    ".ts",
}

# Pattern: paths that look like repo-relative file references
# Must contain at least one path separator or have a known extension
_PATH_PATTERN = re.compile(
    r'(?:^|[\s`\(\["\'])'  # boundary: start, space, backtick, paren, bracket, quote
    r"((?:[a-zA-Z0-9_.-]+/)+[a-zA-Z0-9_.-]+\.[a-zA-Z0-9]+)"  # path/to/file.ext
    r'(?=[\s`\)\]"\'.,;:!?]|$)',  # boundary: end, space, backtick, paren, bracket, quote, punct
    re.MULTILINE,
)

# Fenced code block: ``` or ~~~ at start of line, until matching fence
_FENCED_CODE_RE = re.compile(
    r"^(?:```|~~~).*?\n(?:```|~~~)",
    re.MULTILINE | re.DOTALL,
)

# Inline code: `...` (single backticks, not triple)
_INLINE_CODE_RE = re.compile(
    r"`[^`\n]+`",
)


def strip_code_blocks(text: str) -> str:
    """Remove fenced code blocks and inline-code spans from markdown text.

    This ensures file paths used as examples (inside code blocks or
    inline code) are not treated as real file references.
    """
    # Remove fenced code blocks first (they may contain inline code)
    text = _FENCED_CODE_RE.sub("", text)
    # Remove inline-code spans
    text = _INLINE_CODE_RE.sub("", text)
    return text


def extract_file_paths(text: str) -> list[str]:
    """Extract candidate file paths from PR body text."""
    candidates: list[str] = []
    for match in _PATH_PATTERN.finditer(text):
        path = match.group(1)
        # Filter: must have a known extension or be under a known repo dir
        ext = Path(path).suffix
        if ext in _FILE_EXTENSIONS or any(
            path.startswith(prefix)
            for prefix in (
                "docs/",
                "schemas/",
                "examples/",
                "scripts/",
                "tests/",
                "hummbl_tuples/",
                "reference_impl/",
                ".github/",
                "conformance/",
                "registry/",
                "research_notes/",
                "adrs/",
                "comparisons/",
            )
        ):
            candidates.append(path)
    return candidates


def check_files_exist(paths: list[str]) -> tuple[list[str], list[str]]:
    """Check which paths exist and which don't.

    Returns (existing, missing).
    """
    existing: list[str] = []
    missing: list[str] = []
    for p in paths:
        full = REPO_ROOT / p
        if full.exists():
            existing.append(p)
        else:
            missing.append(p)
    return existing, missing


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify file references in a PR body exist in the repo."
    )
    parser.add_argument(
        "--body-file",
        type=str,
        default=None,
        help="Path to a file containing the PR body. If omitted, reads stdin.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        default=True,
        help="Exit 1 if any referenced file is missing (default: on).",
    )
    parser.add_argument(
        "--no-strict",
        dest="strict",
        action="store_false",
        help="Warn only, do not fail on missing files.",
    )
    args = parser.parse_args()

    if args.body_file:
        body = Path(args.body_file).read_text(encoding="utf-8")
    else:
        body = sys.stdin.read()

    if not body.strip():
        print("WARN: Empty PR body — no file references to check.")
        return 0

    # Strip code blocks and inline-code spans so example paths are
    # not treated as real file references.
    prose_body = strip_code_blocks(body)
    paths = extract_file_paths(prose_body)
    if not paths:
        print("OK: No explicit file path references found in PR body.")
        print("     (Conservative check — only explicit paths like docs/foo.md are verified.)")
        return 0

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique_paths: list[str] = []
    for p in paths:
        if p not in seen:
            seen.add(p)
            unique_paths.append(p)

    existing, missing = check_files_exist(unique_paths)

    if existing:
        print(f"OK: {len(existing)} referenced file(s) exist:")
        for p in existing:
            print(f"  + {p}")

    if missing:
        print(f"\nFAIL: {len(missing)} referenced file(s) do NOT exist:")
        for p in missing:
            print(f"  - {p}")
        if args.strict:
            print("\nThese files are referenced in the PR body but are not in the repo.")
            print("Either commit the files or remove the references from the PR body.")
            return 1
        else:
            print("\n(warnings only — --no-strict mode)")
            return 0

    print(f"\nOK: All {len(unique_paths)} referenced file(s) verified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
