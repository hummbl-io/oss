#!/usr/bin/env python3
"""Generate and check the repository script lifecycle contract document.

Emits ``docs/architecture/SCRIPT-CONTRACTS.md`` — an inventory of every
executable script and console entrypoint with its owner, invocation contract,
source-of-truth, test/smoke path, and lifecycle class
(maintain / connect / productize / deprecate / retire-candidate).

``--check`` regenerates the document in memory and fails when:
  - the committed document has drifted from generated output, or
  - a script file exists on disk with no contract row, or
  - a contract row names a file that no longer exists.

Stdlib-only, matching the repository convention.
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs" / "architecture" / "SCRIPT-CONTRACTS.md"

CLASSES = ("maintain", "connect", "productize", "deprecate", "retire-candidate")

# ---------------------------------------------------------------------------
# Group defaults: owner / classification / test convention per directory.
# Per-script entries in OVERRIDES replace individual fields.
# ---------------------------------------------------------------------------

GROUPS: dict[str, dict] = {
    ".github/scripts": {
        "owner": "oss-maintainers",
        "class": "maintain",
        "test": "executed by .github/workflows on every PR",
        "boundary": "CI invocation surface — stdlib only, no network beyond platform APIs",
    },
    "tools/scripts": {
        "owner": "oss-maintainers",
        "class": "maintain",
        "test": "co-located test_*.py where present, else --help smoke",
        "boundary": "monorepo tooling — public-safe, boundary-checked by boundary-check.yml",
    },
    "tools": {
        "owner": "oss-maintainers",
        "class": "maintain",
        "test": "co-located test file",
        "boundary": "public position/asset validation only — no source-of-truth authority",
    },
    "tools/assessor-v0": {
        "owner": "oss-maintainers",
        "class": "productize",
        "test": "tools/assessor-v0/verify.py --help; pack fixtures in assessor_readme.md",
        "boundary": "candidate product pack — CONTRACT x DCT x EVIDENCE verifier",
    },
    "packages/python/arcana/scripts": {
        "owner": "arcana maintainers",
        "class": "maintain",
        "test": "arcana package test suite",
        "boundary": "research/content generation tooling — output reviewed before publication",
    },
    "packages/python/base120/scripts": {
        "owner": "base120 maintainers",
        "class": "maintain",
        "test": "base120 package test suite",
        "boundary": "registry/extraction helpers for the Base120 package",
    },
    "packages/python/hummbl-bus/scripts": {
        "owner": "hummbl-bus maintainers",
        "class": "maintain",
        "test": "hummbl-bus package test suite",
        "boundary": "release helpers for the hummbl-bus package",
    },
    "packages/python/hummbl-eval/scripts": {
        "owner": "hummbl-eval maintainers",
        "class": "maintain",
        "test": "hummbl-eval package test suite",
        "boundary": "evaluation runners and validators",
    },
    "packages/python/hummbl-governance/scripts": {
        "owner": "hummbl-governance maintainers",
        "class": "maintain",
        "test": "hummbl-governance package test suite or --help smoke",
        "boundary": "governance ops tooling — must not embed secrets or host-internal paths",
    },
    "packages/python/hummbl-tuples/scripts": {
        "owner": "hummbl-tuples maintainers",
        "class": "maintain",
        "test": "hummbl-tuples package test suite",
        "boundary": "schema/fixture generation and validation helpers",
    },
}

# Per-script overrides and explicit lifecycle notes.
OVERRIDES: dict[str, dict] = {
    "tools/scripts/pypi_download_tracker.py": {
        "class": "connect",
        "notes": "feeds adoption signals; integration point for product admission (oss#215)",
    },
    "tools/validate_ai_positions.py": {
        "boundary": "validates public position-document structure only; not source truth",
    },
    "tools/data/pypi-downloads.csv": {
        "class": "maintain",
        "owner": "oss-maintainers",
        "notes": "append-only data sink written by pypi_download_tracker.py + workflow",
    },
    "tools/scripts/script_contracts.py": {
        "test": "self-check via --check in boundary-check/CI",
        "notes": "this contract's own generator/enforcer",
    },
    # One-shot remediation scripts — executed for a specific gap, now stale
    # candidates for retirement rather than ongoing maintenance.
    **{
        f"packages/python/hummbl-governance/scripts/{n}": {
            "class": "retire-candidate",
            "notes": "one-shot gap remediation script; retain for audit trail",
        }
        for n in [
            "gap2-generate-agent-keys.py",
            "gap5-audit-ci-pinning.py",
            "gap5-generate-sbom.py",
            "gap6-merkle-anchor.py",
            "gap7-branch-protection-audit.py",
            "gap7-enable-branch-protection.py",
        ]
    },
    "packages/python/hummbl-governance/scripts/sync-gitea-to-github.sh": {
        "class": "deprecate",
        "notes": "superseded by GitHub-native sync; retained until replacement documented",
    },
    "packages/python/hummbl-tuples/scripts/migrate_to_v2.py": {
        "class": "retire-candidate",
        "notes": "one-shot schema migration; re-run is meaningless post-v2",
    },
    "packages/python/hummbl-tuples/scripts/migrate_tuples.py": {
        "class": "retire-candidate",
        "notes": "one-shot data migration; re-run is meaningless post-migration",
    },
}

TEST_FILE_RE = re.compile(r"^(test_|.*_test\.)")
SCRIPT_SUFFIXES = (".py", ".mjs", ".sh", ".js")


@dataclass(frozen=True)
class Contract:
    path: str
    purpose: str
    owner: str
    invocation: str
    sot: str
    test: str
    cls: str
    notes: str


def _docstring(path: Path) -> str:
    try:
        if path.suffix != ".py":
            return ""
        tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
        doc = ast.get_docstring(tree) or ""
        return doc.split("\n", 1)[0].strip().rstrip(".")
    except (SyntaxError, OSError):
        return ""


def _group_for(rel: str) -> dict:
    best: dict = {}
    best_len = -1
    for prefix, g in GROUPS.items():
        if rel.startswith(prefix + "/") and len(prefix) > best_len:
            best, best_len = g, len(prefix)
    return best


def _invocation(rel: str) -> str:
    if rel.endswith(".py"):
        return f"python {rel}"
    if rel.endswith((".mjs", ".js")):
        return f"node {rel}"
    if rel.endswith(".sh"):
        return f"bash {rel}"
    return f"./{rel}"


def collect_scripts() -> list[str]:
    """Every executable script file under contract scope (test files excluded)."""
    out: list[str] = []
    roots = [
        ROOT / ".github" / "scripts",
        ROOT / "tools",
        *sorted(ROOT.glob("packages/*/*/scripts")),
    ]
    for root in roots:
        if not root.is_dir():
            continue
        for f in sorted(root.rglob("*")):
            if not f.is_file():
                continue
            if TEST_FILE_RE.match(f.name):
                continue
            if f.suffix not in SCRIPT_SUFFIXES and not (f.stat().st_mode & 0o111):
                continue
            if f.name == "__init__.py":
                continue
            out.append(f.relative_to(ROOT).as_posix())
    return sorted(out)


def collect_entrypoints() -> list[tuple[str, str, str]]:
    """(package, script-name, entry) for every [project.scripts] entry."""
    out = []
    for pp in sorted(ROOT.glob("packages/*/*/pyproject.toml")):
        try:
            data = tomllib.loads(pp.read_text(encoding="utf-8"))
        except Exception:
            continue
        pkg = data.get("project", {}).get("name", pp.parent.name)
        for name, entry in sorted(data.get("project", {}).get("scripts", {}).items()):
            out.append((pkg, name, entry))
    return out


def build_contracts() -> list[Contract]:
    contracts = []
    for rel in collect_scripts():
        g = _group_for(rel)
        ov = OVERRIDES.get(rel, {})
        p = ROOT / rel
        contracts.append(
            Contract(
                path=rel,
                purpose=ov.get("purpose") or _docstring(p) or "(no module docstring)",
                owner=ov.get("owner", g.get("owner", "oss-maintainers")),
                invocation=ov.get("invocation", _invocation(rel)),
                sot=ov.get("sot", f"git:{rel}"),
                test=ov.get("test", g.get("test", "not recorded")),
                cls=ov.get("class", g.get("class", "maintain")),
                notes=ov.get("notes", ""),
            )
        )
    return contracts


def _esc(s: str) -> str:
    return s.replace("|", "\\|")


def render(contracts: list[Contract], entrypoints: list[tuple[str, str, str]]) -> str:
    lines = [
        "# Script Lifecycle & Integration Contracts",
        "",
        "<!-- GENERATED FILE — regenerate with `python tools/scripts/script_contracts.py`.",
        "     Verify with `--check`; do not edit by hand. -->",
        "",
        "Every executable script in the monorepo carries a lifecycle contract:",
        "owner, invocation contract, source-of-truth, test or smoke path, and a",
        "lifecycle class (`maintain`, `connect`, `productize`, `deprecate`,",
        "`retire-candidate`). New scripts fail `script_contracts.py --check`",
        "until they are covered here — that is the contract enforcement.",
        "",
        "## Repository scripts",
        "",
        "| Script | Class | Owner | Invocation | Test / smoke | Purpose | Notes |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for c in contracts:
        lines.append(
            f"| `{c.path}` | {c.cls} | {c.owner} | `{c.invocation}` | "
            f"{_esc(c.test)} | {_esc(c.purpose)} | {_esc(c.notes)} |"
        )
    lines += [
        "",
        "## Package console entrypoints",
        "",
        "Published `[project.scripts]` surface — the contract is the package's",
        "pyproject entry and its package test suite; version/source-of-truth is",
        "the package version at `packages/*/pyproject.toml`.",
        "",
        "| Package | Script | Entrypoint |",
        "| --- | --- | --- |",
    ]
    for pkg, name, entry in entrypoints:
        lines.append(f"| {pkg} | `{name}` | `{entry}` |")
    lines += [
        "",
        "## Workflow callers",
        "",
        "Scripts invoked by GitHub Actions (from `.github/workflows/*.yml`):",
        "",
        "- `boundary-check.yml` -> `tools/scripts/check_boundary_patterns.py`,",
        "  `tools/scripts/check_rights_distribution.py`",
        "- `ci.yml` -> `.github/scripts/check_license_consistency.py`,",
        "  `.github/scripts/lock_build_env.py`,",
        "  `packages/python/hummbl-governance/scripts/check_public_count_claims.py`,",
        "  `tools/scripts/validate_product_manifests.mjs`",
        "- `publish-pypi.yml` -> `.github/scripts/lock_build_env.py` (hash-locked",
        "  build env; failure aborts the publish before artifacts ship)",
        "- `pypi-download-tracker.yml` -> `tools/scripts/pypi_download_tracker.py`",
        "  (appends `tools/data/pypi-downloads.csv`)",
        "- `validate-workflows.yml` -> `tools/scripts/validate_workflows.py`",
        "",
        "Failure behavior: all workflow-called scripts exit nonzero on invariant",
        "violation; none mutate repository state except the download tracker,",
        "whose CSV append is committed by the workflow itself.",
        "",
        "## Integration opportunities",
        "",
        "- `pypi_download_tracker.py` -> adoption-signal feed for product",
        "  admission decisions (oss#215).",
        "- `gap5-generate-sbom.py` + `lock_build_env.py` -> provenance/SBOM",
        "  evidence chain alongside publish-pypi attestations.",
        "- `assessor-v0` -> productize candidate: verifier contract already",
        "  documented in `tools/assessor-v0/WHAT_THIS_PROVES.md`.",
        "- `coverage_ratchet.py` / `validate_coverage_matrices.py` -> CI gate",
        "  candidates once evidence-matrix format stabilizes.",
        "",
        "## Deprecation register",
        "",
        "Scripts marked `retire-candidate` or `deprecate` are retained for",
        "audit trail; they are not wired into new automation and should not be",
        "referenced by new documentation.",
        "",
    ]
    return "\n".join(lines)


def check() -> int:
    contracts = build_contracts()
    entrypoints = collect_entrypoints()

    # Coverage both directions.
    on_disk = set(collect_scripts())
    in_doc = {c.path for c in contracts}
    missing = on_disk - in_doc
    stale = in_doc - on_disk
    problems = [f"uncovered script: {p}" for p in sorted(missing)]
    problems += [f"contract names missing file: {p}" for p in sorted(stale)]
    # Overrides must name real files too.
    for k in OVERRIDES:
        if k.endswith(".csv"):
            continue
        if not (ROOT / k).exists():
            problems.append(f"override names missing file: {k}")

    expected = render(contracts, entrypoints)
    if not DOC.exists():
        problems.append(f"{DOC.relative_to(ROOT)} does not exist — run the generator")
    elif DOC.read_text(encoding="utf-8") != expected:
        problems.append(f"{DOC.relative_to(ROOT)} is stale — run the generator")

    for p in problems:
        print(f"FAIL {p}")
    if problems:
        return 1
    print(f"script contracts: OK ({len(contracts)} scripts, {len(entrypoints)} entrypoints)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="verify doc freshness and coverage")
    args = ap.parse_args()
    if args.check:
        return check()
    out = render(build_contracts(), collect_entrypoints())
    DOC.parent.mkdir(parents=True, exist_ok=True)
    DOC.write_text(out, encoding="utf-8", newline="\n")
    print(f"wrote {DOC.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
