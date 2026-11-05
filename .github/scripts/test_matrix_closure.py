#!/usr/bin/env python3
"""Expand a seed set of package dirs with their reverse-dependency closure.

Reads seed package directory names on stdin (one per line) and the full
tested-package set as argv[1] (whitespace-separated). Prints the seed plus
every package that transitively depends on it, intersected with the
tested set, sorted.

Used by the ci.yml ``revdeps`` job so a change to a foundation package
(e.g. hummbl-governance) also tests its dependents pre-merge (SW-GREEN-4).
The graph is computed live from pyproject ``dependencies`` and
``optional-dependencies``, so it cannot drift from the manifests.
"""

import pathlib
import sys

import tomllib

ROOT = pathlib.Path("packages/python")


def _dep_name(requirement: str) -> str:
    return requirement.split(">")[0].split("=")[0].split("<")[0].split("[")[0].strip()


def _requirements(manifest: dict) -> list[str]:
    project = manifest["project"]
    reqs = list(project.get("dependencies", []))
    for extra in project.get("optional-dependencies", {}).values():
        reqs += extra
    return reqs


def _load_manifests() -> dict[str, dict]:
    return {
        d.name: tomllib.loads((d / "pyproject.toml").read_text(encoding="utf-8"))
        for d in ROOT.iterdir()
        if (d / "pyproject.toml").is_file()
    }


def _reverse_graph(pkgs: dict[str, dict]) -> dict[str, set[str]]:
    name2dir = {p["project"]["name"]: d for d, p in pkgs.items()}
    rev: dict[str, set[str]] = {}
    for d, manifest in pkgs.items():
        for req in _requirements(manifest):
            dep = name2dir.get(_dep_name(req))
            if dep and dep != d:
                rev.setdefault(dep, set()).add(d)
    return rev


def _closure(seed: set[str], rev: dict[str, set[str]]) -> set[str]:
    seen = set(seed)
    stack = list(seed)
    while stack:
        for dep in rev.get(stack.pop(), ()):
            if dep not in seen:
                seen.add(dep)
                stack.append(dep)
    return seen


def main() -> None:
    seed = {line.strip() for line in sys.stdin if line.strip()}
    allowed = set(sys.argv[1].split())
    pkgs = _load_manifests()
    result = _closure(seed, _reverse_graph(pkgs)) & allowed
    sys.stdout.write("\n".join(sorted(result)) + "\n")


if __name__ == "__main__":
    main()
