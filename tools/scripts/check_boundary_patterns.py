#!/usr/bin/env python3
"""Scan tracked worktree files for public/private boundary patterns.

Exit 0: checked text is clean; 1: findings; 2: incomplete coverage (even
with findings). This is a heuristic boundary check, not secret or rights
clearance. Binary assets and unsupported encodings require separate review.
Git history and untracked files are outside this check's explicit scope.
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

# Internal artifact file-name patterns (case-insensitive).
# These match the naming conventions used in private repos for
# handoffs, AARs, receipts, session transcripts, and fleet inventory.
DENYFILE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"^HANDOFF[-_]", re.I), "internal handoff document"),
    (re.compile(r"^HANDOFF(?:\.[^.]+)?$", re.I), "internal handoff document"),
    (re.compile(r"^AAR[-_]", re.I), "After Action Review (belongs in private repo)"),
    (re.compile(r"^RECEIPT[-_]", re.I), "internal receipt artifact"),
    (re.compile(r"^SESSION[-_]?(TRANSCRIPT|LOG)", re.I), "session transcript/log"),
    (re.compile(r"^FLEET[-_]?INVENTORY", re.I), "fleet inventory file"),
    (re.compile(r"^AUDIT[-_]?\d", re.I), "internal audit file (dated audit belongs in private repo)"),
    (re.compile(r"^BACKCHANNEL", re.I), "backchannel log"),
    (re.compile(r"^RETIRED[-_]", re.I), "retired/internal retirement index"),
    (re.compile(r"^INTERNAL[-_]", re.I), "internal-only file"),
]

# Directories that indicate internal artifact collections.
DENYDIR_NAMES = {
    "handoffs", "receipts", "backchannel", "session-transcripts",
    "fleet-inventory", "audit-matrices", "internal-infra",
}

# File extensions to scan for content-based checks (fleet topology files).
SCAN_EXTENSIONS = {".json", ".yaml", ".yml"}

# Tailscale CGNAT range (RFC 6598, /10 prefix).
CGNAT_IP_PATTERN = re.compile(
    r"\b100\.(6[4-9]|[7-9][0-9]|1[01][0-9]|12[0-7])\.\d{1,3}\.\d{1,3}\b"
)

# Documentation placeholder IP already adopted as convention across this
# repo's docs/tests (first address of the CGNAT block). Not a leak.
ALLOWED_EXAMPLE_IPS = {"100.64.0.1"}


# These exact public implementation filenames use governance domain terms.
# Exceptions affect naming only: their contents are still checked.
PUBLIC_DOMAIN_PATHS = {
    "packages/python/hummbl-governance/docs/ecosystem/schemas/receipt_bundle.schema.json",
    "packages/python/hummbl-governance/hummbl_governance/data/receipt_integrity_monitor.schema.json",
    "packages/python/hummbl-governance/hummbl_governance/kernel/receipt_engine.py",
    "packages/python/hummbl-governance/hummbl_governance/kernel/receipt_integrity_monitor.py",
    "packages/python/hummbl-tuples/schemas/extensions/multi_actor/handoff_event.schema.json",
}
WINDOWS_HOME_PATH = re.compile(r"(?i)[A-Z]:[/\\]+Users[/\\]+[A-Za-z0-9._-]+")
POSIX_HOME_PATH = re.compile(
    r"(?i)(?:~/projects[/\\]PROJECTS|/(?:Users|home)/[A-Za-z0-9._-]+/[A-Za-z0-9._-]+)"
)
URL_SPAN = re.compile(r"https?://[^\s<>\"'`)\]|]+", re.I)
PRIVATE_STATUS = re.compile(
    r"^\s*(?:[-*]\s+)?(?:status|visibility|classification)\s*:\s*"
    r"[^\n]*\b(?:private|internal(?:[- ]only)?|confidential)\b", re.I
)
STATUS_PLACEHOLDER = re.compile(
    r"\((?:public|private|internal|confidential)(?:\|(?:public|private|internal|confidential))+\)",
    re.I,
)
BINARY_SUFFIXES = {
    ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".bmp",
    ".zip", ".gz", ".tar", ".7z", ".xz", ".bz2", ".whl",
    ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".exe", ".dll", ".so", ".a", ".o", ".pyc", ".bin", ".woff", ".woff2",
    ".mp3", ".mp4", ".wav", ".mov", ".sqlite", ".db",
}
DOCUMENT_SUFFIXES = {".md", ".mdx", ".rst", ".txt", ".adoc"}


@dataclass
class Result:
    findings: list[tuple[str, str]] = field(default_factory=list)
    incomplete: list[tuple[str, str]] = field(default_factory=list)
    checked: int = 0

    @property
    def exit_code(self) -> int:
        return 2 if self.incomplete else 1 if self.findings else 0


def status_lines(text: str):
    """Actual Markdown declarations only, excluding blockquotes/code examples."""
    fence = None
    for number, line in enumerate(text.splitlines(), 1):
        stripped = line.lstrip()
        if stripped.startswith(">"):
            continue
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if marker:
            token = marker.group(1)
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
            continue
        if fence or line.startswith(("    ", "\t")):
            continue
        # Markdown heading and emphasis may decorate the field and its value.
        declaration = re.sub(r"^\s*#{1,6}\s+", "", line)
        declaration = declaration.replace("*", "").replace("_", "")
        if PRIVATE_STATUS.search(STATUS_PLACEHOLDER.sub("", declaration)):
            yield number


def inspect_text(name: str, text: str, result: Result) -> None:
    suffix = PurePosixPath(name).suffix.lower()
    if suffix in SCAN_EXTENSIONS and "git_host" in text and text.count('"name"') > 20:
        result.findings.append((name, "fleet-topology"))
    if suffix in DOCUMENT_SUFFIXES:
        for number in status_lines(text):
            result.findings.append((name, f"private-status:line={number}"))
    for number, line in enumerate(text.splitlines(), 1):
        # URLs can contain /users/ legitimately; do not suppress other spans.
        non_url = URL_SPAN.sub("", line)
        if WINDOWS_HOME_PATH.search(non_url) or POSIX_HOME_PATH.search(non_url):
            result.findings.append((name, f"home-path:line={number}"))
        if any(m.group(0) not in ALLOWED_EXAMPLE_IPS for m in CGNAT_IP_PATTERN.finditer(line)):
            result.findings.append((name, f"internal-ip:line={number}"))


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


def scan_paths(root: Path, names: list[str]) -> Result:
    problem = root_problem(root)
    if problem:
        return Result(incomplete=[(".", problem)])
    result = Result()
    root = root.resolve(strict=True)
    for name in sorted(set(names)):
        relative = PurePosixPath(name)
        if not relative.parts or relative.is_absolute() or ".." in relative.parts or "\\" in name or ":" in name:
            result.incomplete.append((name, "outside-root"))
            continue
        path = root.joinpath(*relative.parts)
        try:
            current = root
            linked = False
            for part in relative.parts:
                current = current / part
                info = current.lstat()
                if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
                    linked = True
                    break
            if linked:
                result.incomplete.append((name, "link-not-followed"))
                continue
            if not path.resolve(strict=True).is_relative_to(root):
                result.incomplete.append((name, "outside-root"))
                continue
            if not stat.S_ISREG(info.st_mode):
                result.incomplete.append((name, "unsupported-file-type"))
                continue
            if name not in PUBLIC_DOMAIN_PATHS:
                for pattern, _ in DENYFILE_PATTERNS:
                    if pattern.search(relative.name):
                        result.findings.append((name, "internal-artifact-name"))
                        break
            if any(part.lower() in DENYDIR_NAMES for part in relative.parts[:-1]):
                result.findings.append((name, "internal-artifact-directory"))
            if relative.suffix.lower() in BINARY_SUFFIXES:
                result.incomplete.append((name, "binary-content-review-required"))
                continue
            data = path.read_bytes()
            if b"\x00" in data:
                result.incomplete.append((name, "binary-content-review-required"))
                continue
            text = data.decode("utf-8-sig", errors="strict")
        except UnicodeDecodeError:
            result.incomplete.append((name, "unsupported-encoding-review-required"))
            continue
        except (OSError, ValueError):
            result.incomplete.append((name, "unreadable-file"))
            continue
        if any(ord(char) < 32 and char not in "\n\r\t\f" for char in text):
            result.incomplete.append((name, "binary-content-review-required"))
            continue
        result.checked += 1
        inspect_text(name, text, result)
    return result


def scan(root: Path) -> Result:
    problem = root_problem(root)
    if problem:
        return Result(incomplete=[(".", problem)])
    # Ambient Git routing must not redirect inventory to another index/repo.
    environment = {key: value for key, value in os.environ.items()
                   if not key.upper().startswith("GIT_")}
    try:
        top = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=root,
                             capture_output=True, check=True, timeout=30, env=environment)
        if Path(os.fsdecode(top.stdout.rstrip(b"\r\n"))).resolve() != root.resolve():
            return Result(incomplete=[(".", "repository-root-required")])
        inventory = subprocess.run(["git", "ls-files", "--stage", "-z"], cwd=root,
                                   capture_output=True, check=True, timeout=30, env=environment)
        names = []
        inventory_gaps = []
        for entry in inventory.stdout.split(b"\0"):
            if not entry:
                continue
            metadata, raw_name = entry.split(b"\t", 1)
            mode, _, stage = metadata.split()
            name = os.fsdecode(raw_name)
            if stage != b"0":
                inventory_gaps.append((name, "unmerged-index-entry"))
            elif mode == b"120000":
                inventory_gaps.append((name, "tracked-link-not-followed"))
            elif mode != b"100644" and mode != b"100755":
                inventory_gaps.append((name, "unsupported-index-mode"))
            else:
                names.append(name)
    except (OSError, ValueError, subprocess.SubprocessError):
        return Result(incomplete=[(".", "git-inventory-failed")])
    if not names and not inventory_gaps:
        return Result(incomplete=[(".", "empty-tracked-inventory")])
    result = scan_paths(root, names)
    result.incomplete.extend(inventory_gaps)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--files-from", type=Path,
                        help="JSON array of root-relative paths, including proposed/untracked export files")
    args = parser.parse_args(argv)
    scope = "tracked worktree"
    if args.files_from is None:
        result = scan(args.root)
    else:
        scope = "explicit manifest"
        try:
            names = json.loads(args.files_from.read_text(encoding="utf-8-sig"))
            if not isinstance(names, list) or not names or not all(
                isinstance(name, str) and name and "\x00" not in name for name in names
            ):
                raise ValueError("invalid manifest")
            result = scan_paths(args.root, names)
        except (OSError, ValueError):
            result = Result(incomplete=[(".", "invalid-or-unreadable-manifest")])
    for name, rule in result.findings:
        print(f"[DENY] {ascii(name)} rule={rule}")
    for name, rule in result.incomplete:
        print(f"[INCOMPLETE] {ascii(name)} rule={rule}")
    state = {0: "CLEAN", 1: "FINDINGS", 2: "INCOMPLETE"}[result.exit_code]
    print(f"Boundary check {state}: {scope} text checked={result.checked}; "
          f"findings={len(result.findings)}; incomplete={len(result.incomplete)}. "
          + ("History and untracked files not scanned." if args.files_from is None
           else "History and files outside manifest not scanned."))
    return result.exit_code


if __name__ == "__main__":
    sys.exit(main())
