#!/usr/bin/env python3
"""Pre-commit hook: scan staged files for sensitive data.

Scans staged .md/.json/.yaml/.yml/.txt/.py/.ts/.js files for internal
hostnames, Tailscale IPs, public VPS IPs, token patterns, internal ports
in context, password patterns, and SSH key references.

Exits 1 (blocking the commit) if any sensitive patterns are found, unless
bypassed via --allow-sensitive flag or SKIP_SENSITIVE_SCAN=1 env var.

Usage:
    python scripts/scan-sensitive-pre-commit.py [--allow-sensitive]
    SKIP_SENSITIVE_SCAN=1 git commit ...
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

# --- Configuration ---------------------------------------------------------

SCANNABLE_EXTENSIONS = {".md", ".json", ".yaml", ".yml", ".txt", ".py", ".ts", ".js"}

# Patterns that are always sensitive regardless of context.
# Each entry: (label, compiled_regex, raw_pattern-for-display)
SIMPLE_PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    # Internal hostnames
    ("internal hostname 'hummbl-vps'", re.compile(r"\bhummbl-vps\b"), r"hummbl-vps"),
    ("internal hostname 'anvil'", re.compile(r"\banvil\b"), r"anvil"),
    ("internal hostname 'hummbl-runner'", re.compile(r"\bhummbl-runner\b"), r"hummbl-runner"),
    ("internal hostname 'tail093e19'", re.compile(r"\btail093e19\b"), r"tail093e19"),
    ("internal domain 'ts.net'", re.compile(r"\bts\.net\b"), r"ts.net"),
    # Public VPS IP
    ("public VPS IP 5.161.114.121", re.compile(r"\b5\.161\.114\.121\b"), r"5.161.114.121"),
    # Delta public IP range
    ("delta public IP 32.140.210.x", re.compile(r"\b32\.140\.210\.\d{1,3}\b"), r"32.140.210.\d+"),
    # Token patterns
    ("GitHub OAuth token 'gho_'", re.compile(r"\bgho_[A-Za-z0-9]+"), r"gho_..."),
    ("OpenRouter token 'sk-or-v1'", re.compile(r"\bsk-or-v1[A-Za-z0-9_-]*"), r"sk-or-v1..."),
    ("Anthropic token 'sk-ant-'", re.compile(r"\bsk-ant-[A-Za-z0-9_-]+"), r"sk-ant-..."),
    ("DASHBOARD_TOKEN reference", re.compile(r"\bDASHBOARD_TOKEN\b"), r"DASHBOARD_TOKEN"),
    ("BUS_TOKEN reference", re.compile(r"\bBUS_TOKEN\b"), r"BUS_TOKEN"),
    ("CLOUDFLARE_API_TOKEN reference", re.compile(r"\bCLOUDFLARE_API_TOKEN\b"), r"CLOUDFLARE_API_TOKEN"),
    ("bus-bridge-token reference", re.compile(r"\bbus-bridge-token\b"), r"bus-bridge-token"),
    ("bus-sender-tokens reference", re.compile(r"\bbus-sender-tokens\b"), r"bus-sender-tokens"),
    # Password patterns
    ("SITE_PASSWORD= assignment", re.compile(r"\bSITE_PASSWORD="), r"SITE_PASSWORD="),
    ("PASSWORD= assignment", re.compile(r"\bPASSWORD="), r"PASSWORD="),
    # SSH key references
    ("SSH key id_ed25519_fleet", re.compile(r"\bid_ed25519_fleet\b"), r"id_ed25519_fleet"),
]

# Tailscale IPs: 100.x.y.z (CGNAT range used by Tailscale)
TAILSCALE_IP_RE = re.compile(r"\b100\.\d{1,3}\.\d{1,3}\.\d{1,3}\b")

# Internal port numbers -- only flagged when "port" or "bind" appears nearby
# (within 40 chars before or after the number on the same line).
INTERNAL_PORTS = {"18790", "8080", "3030", "2222"}
PORT_CONTEXT_RE = re.compile(r"(?i)(port|bind)")
# Window around the port number to look for context keywords.
PORT_CONTEXT_WINDOW = 40


# --- Helpers ---------------------------------------------------------------


def _git_staged_files() -> list[str]:
    """Return the list of staged file paths from `git diff --cached --name-only`."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        print("scan-sensitive: git not found on PATH", file=sys.stderr)
        return []
    if result.returncode != 0:
        # Not a git repo or git error -- nothing to scan.
        return []
    return [line for line in result.stdout.splitlines() if line.strip()]


def _is_scannable(path: Path) -> bool:
    # Never scan this script itself — its pattern definitions contain the
    # very strings it scans for (hummbl-vps, anvil, token names, etc.).
    if path.name == "scan-sensitive-pre-commit.py":
        return False
    return path.suffix.lower() in SCANNABLE_EXTENSIONS


def _check_port_in_context(line: str, port: str) -> bool:
    """Return True if `port` appears in `line` with 'port' or 'bind' nearby."""
    idx = 0
    while True:
        found = line.find(port, idx)
        if found == -1:
            return False
        start = max(0, found - PORT_CONTEXT_WINDOW)
        end = min(len(line), found + len(port) + PORT_CONTEXT_WINDOW)
        window = line[start:end]
        if PORT_CONTEXT_RE.search(window):
            return True
        idx = found + len(port)
    return False


def _scan_line(line: str) -> list[tuple[str, str]]:
    """Scan a single line; return list of (label, matched_text) findings."""
    findings: list[tuple[str, str]] = []

    # Simple patterns
    for label, regex, _display in SIMPLE_PATTERNS:
        for m in regex.finditer(line):
            findings.append((label, m.group(0)))

    # Tailscale IPs
    for m in TAILSCALE_IP_RE.finditer(line):
        # Avoid double-flagging if this IP was already caught by a specific pattern.
        ip = m.group(0)
        if ip == "5.161.114.121":
            continue  # already flagged by the specific VPS IP pattern
        findings.append(("Tailscale CGNAT IP 100.x.x.x", ip))

    # Internal ports in context
    for port in INTERNAL_PORTS:
        # Use word-boundary search to avoid partial matches inside longer numbers.
        for m in re.finditer(rf"\b{port}\b", line):
            if _check_port_in_context(line, port):
                findings.append((f"internal port {port} (with port/bind context)", m.group(0)))

    return findings


def _scan_file(path: Path) -> list[tuple[int, str, str]]:
    """Scan a file; return list of (line_number, label, matched_text) findings."""
    findings: list[tuple[int, str, str]] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except (OSError, UnicodeDecodeError) as exc:
        print(f"scan-sensitive: could not read {path}: {exc}", file=sys.stderr)
        return findings
    for lineno, line in enumerate(text.splitlines(), start=1):
        for label, matched in _scan_line(line):
            findings.append((lineno, label, matched))
    return findings


# --- Main ------------------------------------------------------------------


def _resolve_targets(argv: list[str]) -> list[str]:
    """Determine which files to scan.

    If explicit file paths are passed (pre-commit framework mode), scan those.
    Otherwise, fall back to `git diff --cached --name-only` (git-hook mode).
    """
    targets = [a for a in argv if not a.startswith("-") and a != ""]
    if targets:
        return targets
    return _git_staged_files()


def main(argv: list[str]) -> int:
    # Bypass via flag or env var.
    if "--allow-sensitive" in argv or os.environ.get("SKIP_SENSITIVE_SCAN") == "1":
        print("scan-sensitive: bypassed (--allow-sensitive / SKIP_SENSITIVE_SCAN=1)")
        return 0

    targets = _resolve_targets(argv)
    if not targets:
        # Nothing staged (or not a git repo) and no files passed -- nothing to scan.
        return 0

    total_findings = 0
    repo_root = Path(os.getcwd())
    for rel in targets:
        path = repo_root / rel
        if not path.is_file():
            continue
        if not _is_scannable(path):
            continue
        file_findings = _scan_file(path)
        if file_findings:
            total_findings += len(file_findings)
            print(f"\n  {rel}")
            for lineno, label, matched in file_findings:
                # Truncate matched text for display.
                display = matched if len(matched) <= 60 else matched[:57] + "..."
                print(f"    line {lineno}: {label} -> {display!r}")

    if total_findings > 0:
        print(
            f"\nscan-sensitive: BLOCKED commit -- {total_findings} sensitive finding(s) "
            f"in staged files.",
            file=sys.stderr,
        )
        print(
            "  If this is intentional, re-run with --allow-sensitive or set "
            "SKIP_SENSITIVE_SCAN=1.",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))