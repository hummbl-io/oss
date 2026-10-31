#!/usr/bin/env python3
"""Claim-integrity checks for the public surface.

Two mechanical guards that bind public claims to repository state:

1. stdlib-scope -- the repo advertises "zero third-party runtime dependencies
   (stdlib only in production code)". That holds only if every package's
   runtime ``dependencies`` list contains nothing beyond (a) intra-repo
   first-party packages and (b) an explicit allowlist of documented
   third-party exceptions. A new third-party runtime dependency must be added
   here deliberately rather than slip in silently.

2. runner-badge -- a README "Tested on" badge is a public claim; it must not
   name an operating system that no workflow actually runs on.

Stdlib only. Read-only. Exit 1 on any violation.
"""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGES_DIR = REPO_ROOT / "packages" / "python"
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"
GOVERNANCE_README = PACKAGES_DIR / "hummbl-governance" / "README.md"

# The only packages permitted to declare third-party runtime dependencies and
# the exact third-party base names permitted. This is the machine-enforced copy
# of the exceptions documented in AGENTS.md "Conventions".
RUNTIME_DEP_ALLOWLIST: dict[str, set[str]] = {
    "governed-compression": {"numpy"},
    "hummbl-free-models": {"pyyaml"},
    "hummbl-rubric-templates": {"pyyaml"},
}


def _dep_base(spec: str) -> str:
    """Return the lowercase base distribution name from a PEP 508 requirement."""
    name = str(spec).strip()
    for sep in (">=", "<=", "==", "!=", "~=", ">", "<", "=", ";", "[", " ", "@"):
        idx = name.find(sep)
        if idx != -1:
            name = name[:idx]
    return name.strip().lower()


def _load_packages() -> list[tuple[str, str, list[str]]]:
    """Return (dir_name, declared_name, raw_deps) for each package."""
    loaded: list[tuple[str, str, list[str]]] = []
    for pyproject in sorted(PACKAGES_DIR.glob("*/pyproject.toml")):
        pkg_dir = pyproject.parent.name
        try:
            data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError) as exc:
            print(f"claim-integrity: cannot parse {pyproject}: {exc}", file=sys.stderr)
            continue
        project = data.get("project", {}) or {}
        name = str(project.get("name", pkg_dir)).strip().lower()
        deps = [str(d) for d in (project.get("dependencies", []) or [])]
        loaded.append((pkg_dir, name, deps))
    return loaded


def check_stdlib_scope() -> list[str]:
    loaded = _load_packages()
    first_party = {name for _dir, name, _deps in loaded}
    problems: list[str] = []
    for pkg_dir, _name, deps in loaded:
        allowed = RUNTIME_DEP_ALLOWLIST.get(pkg_dir, set())
        for spec in deps:
            base = _dep_base(spec)
            if base in first_party:
                continue  # intra-repo first-party dependency
            if base in allowed:
                continue  # documented third-party exception
            problems.append(
                f"{pkg_dir}: unexpected third-party runtime dependency {base!r} "
                f"(declared as {spec!r}); add it to RUNTIME_DEP_ALLOWLIST in "
                f".github/scripts/check_claim_integrity.py and document it in "
                f"AGENTS.md, or remove it"
            )
    return problems


def _workflow_os_set() -> set[str]:
    oses: set[str] = set()
    for wf in sorted(WORKFLOWS_DIR.glob("*.yml")):
        try:
            text = wf.read_text(encoding="utf-8")
        except OSError:
            continue
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped.startswith("runs-on:"):
                continue
            value = stripped.split("runs-on:", 1)[1].lower()
            for token in ("ubuntu", "macos", "windows"):
                if token in value:
                    oses.add(token)
    return oses


def check_runner_claims() -> list[str]:
    problems: list[str] = []
    if not GOVERNANCE_README.exists():
        return problems
    oses = _workflow_os_set()
    for line in GOVERNANCE_README.read_text(encoding="utf-8").splitlines():
        if "Tested%20on" not in line and "Tested on" not in line:
            continue
        decoded = (
            line.replace("%20", " ").replace("%2B", "+").replace("%C2%B7", "\u00b7").lower()
        )
        if "macos" in decoded and "macos" not in oses:
            problems.append(
                "hummbl-governance README 'Tested on' badge claims macOS, "
                "but no workflow runs on a macOS runner"
            )
        if "windows" in decoded and "windows" not in oses:
            problems.append(
                "hummbl-governance README 'Tested on' badge claims Windows, "
                "but no workflow runs on a Windows runner"
            )
    return problems


def main() -> int:
    problems = check_stdlib_scope() + check_runner_claims()
    if problems:
        print("claim-integrity: FAIL")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("claim-integrity: OK (stdlib scope + runner badge)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
