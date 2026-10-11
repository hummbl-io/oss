#!/usr/bin/env python3
"""Enforce package/doc parity and requirements.lock freshness (issue #264).

Two gates:

1. Doc parity -- every directory under ``packages/python/`` containing a
   ``pyproject.toml`` must be listed in the Python package tables of
   ``docs/architecture/PACKAGES.md``. Only the tables under
   ``## 1. PyPI (Python)`` count: the name-collision table above that
   section and the ``### Excluded`` subsection inside it list packages
   that are explicitly not ours, so they cannot satisfy the gate.

2. Lock freshness -- every package with a non-empty
   ``[project.dependencies]`` must carry ``requirements.lock`` produced by
   ``uv pip compile pyproject.toml --output-file requirements.lock``.
   Freshness is proven the same way ``lock_build_env.py`` proves
   ``requirements-build.lock`` freshness: an ``# inputs-sha256:`` line in
   the lock records the digest of the pyproject inputs it was compiled
   from (``requires-python`` + ``dependencies``). ``check`` recomputes the
   digest from the current pyproject; a missing or mismatched line means
   the lock is absent, foreign, or stale. A package with no dependencies
   needs no lock, but a lock that is present is verified like any other.

Modes
-----
``check`` stdlib only; doc parity + lock presence/digest verification.
          Runs in CI -- no network, no uv.
``lock``  regenerate ``requirements.lock`` with uv and stamp the inputs
          digest. Needs ``uv`` on PATH. Bare ``lock`` targets every package
          that declares dependencies or already has a lock; named targets
          are regenerated as given.

Usage
-----
    python .github/scripts/package_parity.py check
    python .github/scripts/package_parity.py check hummbl-cognition
    python .github/scripts/package_parity.py lock
    python .github/scripts/package_parity.py lock hummbl-cognition
"""

from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGES_DIR_REL = Path("packages") / "python"
PACKAGES_DOC_REL = Path("docs") / "architecture" / "PACKAGES.md"
LOCK_NAME = "requirements.lock"
INPUTS_HASH_PREFIX = "# inputs-sha256: "

PYTHON_SECTION_RE = re.compile(r"^## .*PyPI \(Python\)")
DIST_NAME_RE = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)")
PIN_RE = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)\s*(==|@)")


def normalize(name: str) -> str:
    """PEP 503-style normalization for comparing package names."""
    return re.sub(r"[-_.]+", "-", name).lower()


def package_dirs(root: Path, names: list[str] | None) -> list[Path]:
    packages_dir = root / PACKAGES_DIR_REL
    if names:
        dirs = [packages_dir / n for n in names]
        missing = [d for d in dirs if not (d / "pyproject.toml").is_file()]
        if missing:
            sys.exit(f"no pyproject.toml in: {', '.join(str(m) for m in missing)}")
        return dirs
    if not packages_dir.is_dir():
        sys.exit(f"no packages directory at {packages_dir}")
    return sorted(d for d in packages_dir.iterdir() if (d / "pyproject.toml").is_file())


def project_table(pkg_dir: Path) -> dict:
    data = tomllib.loads((pkg_dir / "pyproject.toml").read_text(encoding="utf-8"))
    return data.get("project", {})


def package_name(pkg_dir: Path) -> str:
    """The installable name a docs table would list; falls back to dir name."""
    return str(project_table(pkg_dir).get("name") or pkg_dir.name)


def doc_package_names(doc_path: Path) -> set[str]:
    """Normalized first-column names from the '## N. PyPI (Python)' tables."""
    text = doc_path.read_text(encoding="utf-8")
    names: set[str] = set()
    in_scope = False
    excluded = False
    for line in text.splitlines():
        if line.startswith("## "):
            in_scope = bool(PYTHON_SECTION_RE.match(line))
            excluded = False
            continue
        if not in_scope:
            continue
        if line.startswith("### "):
            excluded = line.lstrip("# ").startswith("Excluded")
            continue
        if excluded or not line.startswith("|"):
            continue
        cells = line.split("|")
        if len(cells) < 2:
            continue
        cell = cells[1].strip()
        if cell.startswith("`") and cell.endswith("`") and len(cell) > 2:
            names.add(normalize(cell[1:-1]))
    return names


def lock_inputs(pkg_dir: Path) -> tuple[str, list[str]]:
    """The pyproject inputs the lock must have been compiled from."""
    project = project_table(pkg_dir)
    requires_python = str(project.get("requires-python") or "").strip()
    deps = sorted(d.strip() for d in project.get("dependencies", []) if d.strip())
    return requires_python, deps


def inputs_digest(requires_python: str, deps: list[str]) -> str:
    canonical = f"requires-python: {requires_python}\n" + "".join(
        f"dependency: {d}\n" for d in deps
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def read_lock_digest(lock_path: Path) -> str | None:
    if not lock_path.is_file():
        return None
    for line in lock_path.read_text(encoding="utf-8").splitlines():
        if line.startswith(INPUTS_HASH_PREFIX):
            return line[len(INPUTS_HASH_PREFIX) :].strip()
    return None


def check_lock(pkg_dir: Path) -> str | None:
    """Error string if the lock is missing, unstamped, or stale, else None."""
    requires_python, deps = lock_inputs(pkg_dir)
    lock_path = pkg_dir / LOCK_NAME
    if not lock_path.is_file():
        if deps:
            return (
                f"{pkg_dir.name}: declares dependencies but has no {LOCK_NAME}; "
                f"run: python .github/scripts/package_parity.py lock {pkg_dir.name}"
            )
        return None
    recorded = read_lock_digest(lock_path)
    if recorded is None:
        return (
            f"{pkg_dir.name}: {LOCK_NAME} has no {INPUTS_HASH_PREFIX.strip()} line; "
            f"run: python .github/scripts/package_parity.py lock {pkg_dir.name}"
        )
    if recorded != inputs_digest(requires_python, deps):
        return (
            f"{pkg_dir.name}: {LOCK_NAME} is stale (pyproject inputs changed); "
            f"run: python .github/scripts/package_parity.py lock {pkg_dir.name}"
        )
    text = lock_path.read_text(encoding="utf-8")
    pins = {normalize(m.group(1)) for line in text.splitlines() if (m := PIN_RE.match(line))}
    for dep in deps:
        dist = DIST_NAME_RE.match(dep)
        if dist and normalize(dist.group(1)) not in pins:
            return (
                f"{pkg_dir.name}: declares {dep!r} but {LOCK_NAME} pins no "
                f"{dist.group(1)}== release; "
                f"run: python .github/scripts/package_parity.py lock {pkg_dir.name}"
            )
    return None


def check_doc_parity(pkg_dirs: list[Path], doc_path: Path) -> list[str]:
    if not doc_path.is_file():
        return [f"{doc_path}: package inventory doc missing"]
    documented = doc_package_names(doc_path)
    if not documented:
        return [
            f"{doc_path}: found no package tables under a '## <n>. PyPI (Python)' heading"
        ]
    errors = []
    for d in pkg_dirs:
        name = package_name(d)
        if normalize(name) not in documented:
            errors.append(
                f"{d.name}: package {name!r} is not listed in {PACKAGES_DOC_REL}"
            )
    return errors


def run_check(root: Path, names: list[str]) -> int:
    dirs = package_dirs(root, names or None)
    errors = check_doc_parity(dirs, root / PACKAGES_DOC_REL)
    errors.extend(e for e in (check_lock(d) for d in dirs) if e)
    for e in errors:
        print(f"ERROR: {e}", file=sys.stderr)
    print(f"checked {len(dirs)} package(s): {len(dirs) - len(errors)} ok, {len(errors)} failing")
    return 1 if errors else 0


def lock_targets(root: Path, names: list[str]) -> list[Path]:
    if names:
        return package_dirs(root, names)
    dirs = package_dirs(root, None)
    return [d for d in dirs if lock_inputs(d)[1] or (d / LOCK_NAME).is_file()]


def write_lock(pkg_dir: Path) -> Path:
    uv = shutil.which("uv")
    if not uv:
        sys.exit("uv is required for `lock` mode (https://docs.astral.sh/uv/)")
    lock_path = pkg_dir / LOCK_NAME
    # Preserve the file's existing flavor: hashed locks stay hashed, plain
    # locks stay plain, and the command uv echoes into the header keeps
    # matching what AGENTS.md documents.
    hashed = lock_path.is_file() and "--hash=sha256:" in lock_path.read_text(
        encoding="utf-8"
    )
    cmd = [uv, "pip", "compile", "pyproject.toml"]
    if hashed:
        cmd.append("--generate-hashes")
    cmd += ["--output-file", LOCK_NAME]
    result = subprocess.run(cmd, cwd=pkg_dir, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        sys.exit(f"uv pip compile failed for {pkg_dir.name}:\n{result.stderr}")
    requires_python, deps = lock_inputs(pkg_dir)
    body = lock_path.read_bytes()
    if not body.endswith(b"\n"):
        body += b"\n"
    body += f"{INPUTS_HASH_PREFIX}{inputs_digest(requires_python, deps)}\n".encode("utf-8")
    lock_path.write_bytes(body)
    return lock_path


def run_lock(root: Path, names: list[str]) -> int:
    for d in lock_targets(root, names):
        path = write_lock(d)
        print(f"wrote {path.relative_to(root)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("mode", choices=("check", "lock"))
    parser.add_argument(
        "packages",
        nargs="*",
        help="package directory names under packages/python/ (default: all for "
        "check, all dependency-bearing or already-locked packages for lock)",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=REPO_ROOT,
        help="repository root (default: the checkout containing this script)",
    )
    args = parser.parse_args(argv)
    if args.mode == "lock":
        return run_lock(args.root, args.packages)
    return run_check(args.root, args.packages)


if __name__ == "__main__":
    sys.exit(main())
