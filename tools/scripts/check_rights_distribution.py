#!/usr/bin/env python3
"""Fail-closed rights/distribution invariant check.

Separate from secret scanning (gitleaks) and internal-artifact scanning
(check_boundary_patterns). This check enforces two rights invariants:

1. **Manifest contradiction**: a product admission manifest (product.json
   with schema_version "hummbl.product.v1") must not declare a restrictive
   distribution_policy ("no-new-public-redistribution" or "private-only")
   for embedded content that is already tracked in this public repository
   tree. This catches the PR #138 pattern: declaring
   no-new-public-redistribution for the base120 corpus while the corpus
   files are committed to the public tree.

2. **NOTICE trade-secret regression**: a NOTICE file must not claim
   "trade secret" status for files that are tracked in this public
   repository. This catches the #141 regression: re-introducing
   trade-secret language for corpus files that are already published
   under Apache-2.0.

Exit 0: clean; 1: rights contradiction found; 2: incomplete coverage.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import stat
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

# Distribution policies that restrict public redistribution.
# If content with one of these policies is tracked in the public tree,
# that is a rights contradiction.
RESTRICTIVE_POLICIES = frozenset({
    "no-new-public-redistribution",
    "private-only",
})

# Schema version that identifies a HUMMBL product admission manifest.
PRODUCT_SCHEMA_VERSION = "hummbl.product.v1"

# File extensions that indicate corpus/data content referenced in NOTICE files.
DATA_EXTENSIONS = frozenset({".json", ".yaml", ".yml"})

# Pattern to extract potential file paths from NOTICE text.
# Matches paths ending in data extensions (e.g. base120/data/operators.json).
NOTICE_PATH_PATTERN = re.compile(
    r'[\w./-]+\.(?:json|yaml|yml)',
    re.IGNORECASE,
)

# Trade-secret indicator phrases (case-insensitive).
TRADE_SECRET_PATTERNS = [
    re.compile(r'trade\s+secret', re.IGNORECASE),
    re.compile(r'proprietary\s+(?:and\s+)?confidential', re.IGNORECASE),
    re.compile(r'separate\s+commercial\s+license\s+required', re.IGNORECASE),
]


@dataclass
class RightsResult:
    findings: list[tuple[str, str]] = field(default_factory=list)
    incomplete: list[tuple[str, str]] = field(default_factory=list)
    checked: int = 0

    @property
    def exit_code(self) -> int:
        return 2 if self.incomplete else 1 if self.findings else 0


def root_problem(root: Path) -> str | None:
    """Reject linked roots before filesystem reads or Git inventory."""
    try:
        absolute_root = root.absolute()
        for ancestor in [absolute_root, *absolute_root.parents]:
            root_info = ancestor.lstat()
            if stat.S_ISLNK(root_info.st_mode) or getattr(root_info, "st_file_attributes", 0) & 0x400:
                return "root-link-not-followed"
        if not absolute_root.is_dir():
            return "root-unavailable"
    except OSError:
        return "root-unavailable"
    return None


def git_tracked_files(root: Path) -> set[str] | None:
    """Return the set of tracked file paths, or None on failure."""
    environment = {key: value for key, value in os.environ.items()
                   if not key.upper().startswith("GIT_")}
    try:
        top = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=root,
                             capture_output=True, check=True, timeout=30, env=environment)
        if Path(os.fsdecode(top.stdout.rstrip(b"\r\n"))).resolve() != root.resolve():
            return None
        inventory = subprocess.run(["git", "ls-files", "-z"], cwd=root,
                                   capture_output=True, check=True, timeout=30, env=environment)
        names = set()
        for entry in inventory.stdout.split(b"\0"):
            if entry:
                names.add(os.fsdecode(entry))
        return names
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


def load_manifest(path: Path) -> dict | None:
    """Load and parse a JSON manifest file. Return None on parse failure."""
    try:
        data = json.loads(path.read_bytes().decode("utf-8-sig"))
        return data if isinstance(data, dict) else None
    except (OSError, ValueError, UnicodeDecodeError):
        return None


def check_manifest_contradiction(
    manifest_path: str,
    manifest: dict,
    tracked: set[str],
    result: RightsResult,
) -> None:
    """Check a product manifest for rights/distribution contradictions."""
    schema_version = manifest.get("schema_version")
    if schema_version != PRODUCT_SCHEMA_VERSION:
        return  # Not a HUMMBL product admission manifest; skip.

    result.checked += 1

    rights = manifest.get("rights")
    if not isinstance(rights, dict):
        return

    embedded_content = rights.get("embedded_content")
    if not isinstance(embedded_content, list):
        return

    content_authorities = manifest.get("content_authorities")
    if not isinstance(content_authorities, list):
        content_authorities = []

    # Build content_id -> authority path map.
    authority_paths: dict[str, str] = {}
    for authority in content_authorities:
        if isinstance(authority, dict):
            cid = authority.get("content_id")
            cpath = authority.get("path")
            if isinstance(cid, str) and isinstance(cpath, str):
                authority_paths[cid] = cpath

    for entry in embedded_content:
        if not isinstance(entry, dict):
            continue
        policy = entry.get("distribution_policy")
        if policy not in RESTRICTIVE_POLICIES:
            continue

        content_id = entry.get("content_id", "<unknown>")
        authority_path = authority_paths.get(content_id)

        if authority_path and authority_path in tracked:
            result.findings.append((
                manifest_path,
                (
                    f"rights-contradiction: content_id={content_id} "
                    f"declares distribution_policy={policy} but is tracked "
                    f"in public tree at {authority_path}"
                ),
            ))
        elif authority_path is None:
            # Restrictive policy declared but no content_authorities entry
            # to cross-reference. Flag as incomplete — can't verify.
            result.incomplete.append((
                manifest_path,
                (
                    f"missing-content-authority: content_id={content_id} "
                    f"declares distribution_policy={policy} but no matching "
                    f"content_authorities entry found"
                ),
            ))


def check_notice_trade_secret(
    notice_path: str,
    text: str,
    tracked: set[str],
    result: RightsResult,
) -> None:
    """Check a NOTICE file for trade-secret claims on tracked files."""
    result.checked += 1

    has_trade_secret = any(pattern.search(text) for pattern in TRADE_SECRET_PATTERNS)
    if not has_trade_secret:
        return

    # Extract potential file paths from the NOTICE text and check if
    # any are tracked in the repo.
    referenced_tracked: list[str] = []
    for match in NOTICE_PATH_PATTERN.finditer(text):
        candidate = match.group(0).strip()
        # Normalize: remove leading ./
        candidate = candidate.removeprefix("./")
        if candidate in tracked:
            referenced_tracked.append(candidate)

    if referenced_tracked:
        result.findings.append((
            notice_path,
            (
                f"trade-secret-claim-for-published-files: NOTICE claims trade "
                f"secret status but references tracked files: "
                f"{', '.join(sorted(referenced_tracked))}"
            ),
        ))


def scan(root: Path) -> RightsResult:
    problem = root_problem(root)
    if problem:
        return RightsResult(incomplete=[(".", problem)])

    tracked = git_tracked_files(root)
    if tracked is None:
        return RightsResult(incomplete=[(".", "git-inventory-failed")])
    if not tracked:
        return RightsResult(incomplete=[(".", "empty-tracked-inventory")])

    result = RightsResult()

    for name in sorted(tracked):
        relative = PurePosixPath(name)
        if relative.name == "product.json":
            path = root / name
            manifest = load_manifest(path)
            if manifest is not None:
                check_manifest_contradiction(name, manifest, tracked, result)
            else:
                result.incomplete.append((name, "manifest-parse-failed"))

        if relative.name == "NOTICE":
            path = root / name
            try:
                text = path.read_bytes().decode("utf-8-sig", errors="strict")
            except (OSError, UnicodeDecodeError):
                result.incomplete.append((name, "notice-unreadable"))
                continue
            check_notice_trade_secret(name, text, tracked, result)

    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args(argv)

    result = scan(args.root)

    for name, rule in result.findings:
        print(f"[DENY] {name!a} rule={rule}")
    for name, rule in result.incomplete:
        print(f"[INCOMPLETE] {name!a} rule={rule}")

    state = {0: "CLEAN", 1: "FINDINGS", 2: "INCOMPLETE"}[result.exit_code]
    print(
        f"Rights/distribution check {state}: "
        f"manifests+notices checked={result.checked}; "
        f"findings={len(result.findings)}; "
        f"incomplete={len(result.incomplete)}."
    )
    return result.exit_code


if __name__ == "__main__":
    sys.exit(main())
