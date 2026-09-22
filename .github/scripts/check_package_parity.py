#!/usr/bin/env python3
"""Package inventory and requirements.lock parity check (oss#264).

Checks, run over packages/python/:

1. INVENTORY — every package directory containing pyproject.toml has its
   project name mentioned in docs/architecture/PACKAGES.md.
2. LOCK PRESENCE — every package declaring non-empty
   project.dependencies has a requirements.lock.
3. LOCK FRESHNESS (structural) — for every requirements.lock, the set of
   direct-dependency pins (uv's `# via <pkg> (pyproject.toml)` marker)
   equals the set of declared dependency names, and each pinned version
   satisfies the declared specifier when the specifier is a simple
   comparator (==, >=, <=, >, <, ~=, !=, bare name). Specifiers the
   parser cannot evaluate (environment markers on exotic fields, OR
   unions) degrade to name-presence only — see _satisfies.

This deliberately does NOT re-resolve against a live index: a lock that
pinned numpy==2.5.2 under `numpy>=1.26` remains fresh even when 2.5.3
exists upstream. Freshness here means "in sync with pyproject.toml",
not "newest upstream". That is the drift the repo rule guards against
("when updating runtime dependencies, regenerate its lock file").

Exit code 1 with a per-violation report on failure. Stdlib only.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import tomllib

REPO = Path(__file__).resolve().parents[2]
PKG_ROOT = REPO / "packages" / "python"
PACKAGES_MD = REPO / "docs" / "architecture" / "PACKAGES.md"

_NAME_RE = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)")
_PIN_RE = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)==([^\s\\]+)")
_DIRECT_VIA_RE = re.compile(r"#\s*via\s+\S+\s*\(pyproject\.toml\)")


def canon(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def declared_deps(pyproject: Path) -> dict[str, str]:
    """project.dependencies -> {canonical name: raw specifier string}."""
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    deps = data.get("project", {}).get("dependencies", []) or []
    out: dict[str, str] = {}
    for dep in deps:
        m = _NAME_RE.match(dep)
        if m:
            out[canon(m.group(1))] = dep[m.end(1):].strip()
    return out


def lock_direct_pins(lockfile: Path) -> dict[str, str]:
    """requirements.lock -> {canonical name: pinned version} for pins
    annotated as direct requirements (`# via <pkg> (pyproject.toml)`).

    uv annotates each pin block (the `name==ver` line plus its indented
    `--hash` continuations) with trailing `# via <source>` comments.
    A block whose via list includes `(pyproject.toml)` is a direct dep;
    `# via <other-package>` means transitive. A new block starts at a
    non-indented `name==ver` line. Falls back to treating all pins as
    direct if no via annotations exist at all (e.g. a hand-maintained
    lock).
    """
    pins: dict[str, str] = {}
    annotated = False
    current: tuple[str, str] | None = None
    current_direct = False
    for raw in lockfile.read_text(encoding="utf-8").splitlines():
        indented = raw[:1] in (" ", "\t")
        m = _PIN_RE.match(raw) if not indented else None
        if m:
            if current and current_direct:
                pins[current[0]] = current[1]
            current = (canon(m.group(1)), m.group(2))
            current_direct = False
            continue
        if current and re.search(r"#\s*via\b", raw):
            annotated = True
            if _DIRECT_VIA_RE.search(raw):
                current_direct = True
    if current and current_direct:
        pins[current[0]] = current[1]
    if not annotated:
        return {
            canon(m.group(1)): m.group(2)
            for line in lockfile.read_text(encoding="utf-8").splitlines()
            if line[:1] not in (" ", "\t") and (m := _PIN_RE.match(line))
        }
    return pins


def _ver_tuple(v: str) -> tuple:
    parts = re.split(r"[.\-+_]", v)
    out = []
    for p in parts:
        out.append(int(p) if p.isdigit() else p)
        if not p.isdigit():
            break
    return tuple(out)


def _cmp(a: tuple, b: tuple) -> int:
    n = max(len(a), len(b))
    a += (0,) * (n - len(a))
    b += (0,) * (n - len(b))
    return (a > b) - (a < b)


def _satisfies(pinned: str, spec: str) -> bool | None:
    """True/False if evaluable, None if the spec is beyond this parser."""
    spec = spec.split(";", 1)[0].strip().lstrip("()").strip()
    spec = re.sub(r"^\[[^\]]*\]", "", spec).strip()
    if not spec:
        return True
    if "[" in spec:  # extras without version spec
        return True
    clauses = [c.strip() for c in spec.split(",") if c.strip()]
    pvt = _ver_tuple(pinned)
    for c in clauses:
        m = re.match(r"(===|==|~=|>=|<=|!=|>|<)\s*(.+)", c)
        if not m:
            return None
        op, ver = m.group(1), m.group(2).strip()
        if "*" in ver:
            return None
        vt = _ver_tuple(ver)
        c12 = _cmp(pvt, vt)
        if op == "==" and c12 != 0:
            return False
        if op == "===" and pinned != ver:
            return False
        if op == "!=" and c12 == 0:
            return False
        if op == ">=" and c12 < 0:
            return False
        if op == "<=" and c12 > 0:
            return False
        if op == ">" and c12 <= 0:
            return False
        if op == "<" and c12 >= 0:
            return False
        if op == "~=":
            if c12 < 0:
                return False
            if len(vt) < 2:
                return None
            upper = list(vt[:-1])
            upper[-1] = upper[-1] + 1 if isinstance(upper[-1], int) else 0
            if _cmp(pvt, tuple(upper)) >= 0:
                return False
    return True


def main() -> int:
    failures: list[str] = []
    doc = PACKAGES_MD.read_text(encoding="utf-8") if PACKAGES_MD.is_file() else ""
    dirs = sorted(
        p for p in PKG_ROOT.iterdir()
        if p.is_dir() and (p / "pyproject.toml").is_file()
    )
    for pkg_dir in dirs:
        pp = pkg_dir / "pyproject.toml"
        name = tomllib.loads(pp.read_text(encoding="utf-8"))["project"]["name"]
        rel = pkg_dir.relative_to(REPO).as_posix()

        if f"`{name}`" not in doc:
            failures.append(
                f"INVENTORY: {name} ({rel}) missing from {PACKAGES_MD.relative_to(REPO)}"
            )

        deps = declared_deps(pp)
        lock = pkg_dir / "requirements.lock"
        if deps and not lock.is_file():
            failures.append(
                f"LOCK MISSING: {name} declares {len(deps)} dependencies "
                f"but has no requirements.lock"
            )
            continue
        if not lock.is_file():
            continue

        pins = lock_direct_pins(lock)
        missing = sorted(set(deps) - set(pins))
        extra = sorted(set(pins) - set(deps))
        if missing:
            failures.append(
                f"LOCK STALE: {name} declares {missing} not pinned as direct deps"
            )
        if extra:
            failures.append(
                f"LOCK STALE: {name} lock pins {extra} not declared in pyproject.toml"
            )
        for d in sorted(set(deps) & set(pins)):
            sat = _satisfies(pins[d], deps[d])
            if sat is False:
                failures.append(
                    f"LOCK STALE: {name} {d}=={pins[d]} does not satisfy "
                    f"'{deps[d]}'"
                )
    if failures:
        print(f"package parity check: {len(failures)} violation(s)")
        for f in failures:
            print(f"  {f}")
        return 1
    print(f"package parity check: OK ({len(dirs)} packages)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
