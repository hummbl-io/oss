#!/usr/bin/env python3
"""Pre-flight check: validate pyproject.toml license/classifier compatibility.

PEP 639 (https://peps.python.org/pep-0639/) makes license expressions (e.g.
``license = "Apache-2.0"``) the canonical way to declare a project's license.
Newer setuptools (>= 77.0) reject pyproject.toml files that declare BOTH a
SPDX license expression AND a ``License ::`` trove classifier — the two are
mutually exclusive. The failure surfaces at ``pip install -e .`` time, not
at edit time, so it is easy to introduce silently and only discover via CI.

This script scans one or more pyproject.toml files and exits non-zero if it
finds the incompatible combination.

Usage::

    python scripts/validation/check_pep639_license.py            # scan repo root
    python scripts/validation/check_pep639_license.py /path/to/a  # scan a tree
    python scripts/validation/check_pep639_license.py a.toml b.toml  # explicit files

Exit codes:
    0 — all files clean (or no pyproject.toml found)
    1 — one or more files have the PEP 639 conflict
    2 — usage error
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-redef]

LICENSE_CLASSIFIER_PREFIX = "License ::"


def _has_spdx_license_expression(data: dict) -> bool:
    project = data.get("project", {})
    license_field = project.get("license")
    if license_field is None:
        return False
    # SPDX expression: string or {text = "..."} (the table form is legacy but
    # still accepted; only the string form is the PEP 639 expression).
    if isinstance(license_field, str):
        return True
    return False  # table form ({text = "..."}) is not a PEP 639 expression


def _has_license_classifier(data: dict) -> list[str]:
    project = data.get("project", {})
    classifiers = project.get("classifiers", []) or []
    return [c for c in classifiers if isinstance(c, str) and c.startswith(LICENSE_CLASSIFIER_PREFIX)]


def check_file(path: Path) -> list[str]:
    """Return a list of error messages for ``path`` (empty = clean)."""
    errors: list[str] = []
    try:
        with path.open("rb") as fh:
            data = tomllib.load(fh)
    except FileNotFoundError:
        return [f"{path}: file not found"]
    except Exception as exc:  # noqa: BLE001 — report any parse failure
        return [f"{path}: failed to parse: {exc}"]

    has_spdx = _has_spdx_license_expression(data)
    license_classifiers = _has_license_classifier(data)

    if has_spdx and license_classifiers:
        errors.append(
            f"{path}: PEP 639 conflict — `license` is an SPDX expression "
            f"AND `classifiers` contains license trove classifiers: "
            f"{license_classifiers}. Remove the classifier(s); the SPDX "
            f"expression is canonical."
        )
    return errors


def iter_pyproject(roots: list[Path]) -> list[Path]:
    """Yield pyproject.toml files under each root (or the root itself if it
    is a file)."""
    found: list[Path] = []
    for root in roots:
        if root.is_file() and root.name == "pyproject.toml":
            found.append(root)
        elif root.is_dir():
            found.extend(sorted(root.rglob("pyproject.toml")))
    return found


def main(argv: list[str]) -> int:
    args = argv[1:]
    if not args:
        roots = [Path.cwd()]
    else:
        roots = [Path(a).resolve() for a in args]

    files = iter_pyproject(roots)
    if not files:
        print("no pyproject.toml files found", file=sys.stderr)
        return 0

    all_errors: list[str] = []
    for f in files:
        errors = check_file(f)
        if errors:
            all_errors.extend(errors)
            for e in errors:
                print(f"FAIL  {e}", file=sys.stderr)
        else:
            print(f"OK    {f}")

    if all_errors:
        print(
            f"\n{len(all_errors)} PEP 639 conflict(s) found. "
            "Remove the License :: trove classifier(s) when using "
            '`license = "<SPDX>"`.',
            file=sys.stderr,
        )
        return 1

    print(f"\n{len(files)} file(s) clean.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
