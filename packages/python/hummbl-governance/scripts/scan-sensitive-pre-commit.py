#!/usr/bin/env python3
"""Pre-commit hook + standalone vetting tool: scan for sensitive data.

Scans .md/.json/.yaml/.yml/.txt/.py/.ts/.js files for internal hostnames,
Tailscale IPs, public IPs, token patterns, passwords, SSH keys, PII, PHI,
internal paths, and personal references.

Modes:
    python scripts/scan-sensitive-pre-commit.py              # Pre-commit: scan staged files
    python scripts/scan-sensitive-pre-commit.py --diff       # Scan uncommitted diff
    python scripts/scan-sensitive-pre-commit.py --branch REF # Scan current branch vs REF
    python scripts/scan-sensitive-pre-commit.py --file PATH  # Scan specific file(s)
    python scripts/scan-sensitive-pre-commit.py --all        # Scan all git-tracked files
    python scripts/scan-sensitive-pre-commit.py --staged     # Explicit staged mode (default)

Severity levels:
    CRITICAL - Tokens, passwords, private keys, SSN (always blocks)
    HIGH     - Internal IPs, paths, Tailscale domains, PHI (blocks by default)
    MEDIUM   - Fleet hostnames, personal domains, email addresses (warns)
    LOW      - Full names, personal references (info only)

Exit codes:
    0 - No findings, or only LOW/MEDIUM with --allow-warnings
    1 - CRITICAL or HIGH findings present (blocks commit)
    2 - Invalid arguments

Bypass:
    --allow-sensitive    Bypass all checks (use sparingly, document reason)
    --allow-warnings     Allow MEDIUM/LOW through (still block CRITICAL/HIGH)
    SKIP_SENSITIVE_SCAN=1  Environment bypass (equivalent to --allow-sensitive)

Allowlist:
    A .vet-allowlist file in the repo root can pre-approve specific patterns.
    Format: one glob per line matching file paths to exempt.
    Lines starting with # are comments.
    Example: docs/REPO_STATUS_DECISION_*.md

Config:
    A .vet-config.json file in the repo root can customize pattern behavior:
    {
      "disable_patterns": ["full name 'Reuben Paul Bowlby'"],
      "severity_overrides": {"fleet hostname 'anvil'": "LOW"},
      "custom_patterns": [
        {"severity": "HIGH", "category": "custom", "label": "project codename",
         "pattern": "\\bPROJECT_X\\b"}
      ]
    }
    - disable_patterns: skip patterns by exact label
    - severity_overrides: change a pattern's severity (e.g., MEDIUM -> LOW)
    - custom_patterns: add project-specific patterns
"""
from __future__ import annotations

import fnmatch
import json
import os
import re
import subprocess
import sys
from pathlib import Path

# --- Severity levels -------------------------------------------------------

CRITICAL = "CRITICAL"
HIGH = "HIGH"
MEDIUM = "MEDIUM"
LOW = "LOW"

# Exit codes
EXIT_CLEAN = 0
EXIT_BLOCKED = 1
EXIT_BAD_ARGS = 2

# --- Configuration ---------------------------------------------------------

SCANNABLE_EXTENSIONS = {".md", ".json", ".yaml", ".yml", ".txt", ".py", ".ts", ".js"}

# Allowlist file name (in repo root)
ALLOWLIST_FILE = ".vet-allowlist"

# Config file name (in repo root)
CONFIG_FILE = ".vet-config.json"

# Default config structure:
# {
#   "disable_patterns": ["full name 'Reuben Paul Bowlby'", "personal domain 'rpbx.net'"],
#   "severity_overrides": {"fleet hostname 'anvil'": "LOW"},
#   "custom_patterns": [
#     {"severity": "HIGH", "category": "custom", "label": "internal project codename",
#      "pattern": "\\bPROJECT_X\\b"}
#   ]
# }
DEFAULT_CONFIG: dict = {
    "disable_patterns": [],
    "severity_overrides": {},
    "custom_patterns": [],
}

# --- Pattern registry ------------------------------------------------------
# Each entry: (severity, category, label, compiled_regex)
# CRITICAL: Always block — real secrets that must never be committed.
# HIGH: Block by default — infrastructure details that aid attackers.
# MEDIUM: Warn — fleet hostnames, personal domains, emails. May be intentional.
# LOW: Info only — full names, personal references. Usually fine in docs.

PatternDef = tuple[str, str, str, re.Pattern[str]]

PATTERNS: list[PatternDef] = [
    # --- CRITICAL: Tokens, passwords, keys ---
    (CRITICAL, "token", "GitHub OAuth token 'gho_'",
     re.compile(r"\bgho_[A-Za-z0-9]+")),
    (CRITICAL, "token", "OpenRouter token 'sk-or-v1'",
     re.compile(r"\bsk-or-v1[A-Za-z0-9_-]*")),
    (CRITICAL, "token", "Anthropic token 'sk-ant-'",
     re.compile(r"\bsk-ant-[A-Za-z0-9_-]+")),
    (CRITICAL, "token", "OpenAI token 'sk-proj-'",
     re.compile(r"\bsk-proj-[A-Za-z0-9_-]+")),
    (CRITICAL, "token", "DASHBOARD_TOKEN reference",
     re.compile(r"\bDASHBOARD_TOKEN\b")),
    (CRITICAL, "token", "BUS_TOKEN reference",
     re.compile(r"\bBUS_TOKEN\b")),
    (CRITICAL, "token", "CLOUDFLARE_API_TOKEN= assignment",
     re.compile(r"\bCLOUDFLARE_API_TOKEN\s*=\s*\S")),
    (CRITICAL, "token", "bus-bridge-token reference",
     re.compile(r"\bbus-bridge-token\b")),
    (CRITICAL, "token", "bus-sender-tokens reference",
     re.compile(r"\bbus-sender-tokens\b")),
    (CRITICAL, "password", "SITE_PASSWORD= assignment",
     re.compile(r"\bSITE_PASSWORD=")),
    (CRITICAL, "password", "PASSWORD= assignment",
     re.compile(r"\bPASSWORD=")),
    (CRITICAL, "key", "SSH private key block",
     re.compile(r"-----BEGIN (RSA |EC |OPENSSH |ED25519 )?PRIVATE KEY-----")),
    (CRITICAL, "key", "SSH key id_ed25519_fleet",
     re.compile(r"\bid_ed25519_fleet\b")),
    (CRITICAL, "pii", "Social Security Number",
     re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),

    # --- HIGH: Infrastructure details ---
    (HIGH, "hostname", "internal hostname 'hummbl-vps'",
     re.compile(r"\bhummbl-vps\b")),
    (HIGH, "hostname", "internal hostname 'hummbl-runner'",
     re.compile(r"\bhummbl-runner\b")),
    (HIGH, "hostname", "internal hostname 'tail093e19'",
     re.compile(r"\btail093e19\b")),
    (HIGH, "domain", "internal Tailscale domain 'ts.net'",
     re.compile(r"\bts\.net\b")),
    (HIGH, "ip", "public VPS IP 5.161.114.121",
     re.compile(r"\b5\.161\.114\.121\b")),
    (HIGH, "ip", "delta public IP 32.140.210.x",
     re.compile(r"\b32\.140\.210\.\d{1,3}\b")),
    (HIGH, "path", "internal Windows user path 'C:\\Users\\reuben'",
     re.compile(r"C:\\Users\\reuben", re.IGNORECASE)),
    (HIGH, "path", "internal Unix path '/home/reuben'",
     re.compile(r"/home/reuben")),
    (HIGH, "path", "internal path '/opt/hummbl'",
     re.compile(r"/opt/hummbl")),
    (HIGH, "path", "internal bus cache path '.cache/bus'",
     re.compile(r"\.cache/bus")),
    (HIGH, "path", "internal coordination path '_state/coordination'",
     re.compile(r"_state/coordination")),
    (HIGH, "path", "internal loop-ledger path 'loop-ledger/'",
     re.compile(r"loop-ledger/")),
    (HIGH, "phi", "medical record number 'MRN:'",
     re.compile(r"\bMRN[:\s]?\d{4,}\b", re.IGNORECASE)),

    # --- MEDIUM: Fleet hostnames, personal domains, emails ---
    # Ambiguous hostnames (common English words) are only flagged in
    # hostname-like contexts: host=, machine=, on <name>, <name> session,
    # <name>'s, <name> is/has/was, from <name>, to <name>, @<name>
    # Distinctive hostnames are always flagged.
    (MEDIUM, "hostname", "fleet hostname 'anvil'",
     re.compile(r"(?:host=anvil|machine=anvil|\bon\s+anvil\b|anvil\'s\b|anvil\s+(?:is|has|was|session|started|resumed|completed|froze)|from\s+anvil|to\s+anvil|@anvil|devin-anvil|codex-anvil)", re.IGNORECASE)),
    (MEDIUM, "hostname", "fleet hostname 'delta'",
     re.compile(r"(?:host=delta|machine=delta|\bon\s+delta\b|delta\'s\b|delta\s+(?:has|was|session|started|resumed|completed|froze)|from\s+delta|to\s+delta|@delta|devin-delta|codex-delta)", re.IGNORECASE)),
    (MEDIUM, "hostname", "fleet hostname 'huxley'",
     re.compile(r"(?:host=huxley|machine=huxley|\bon\s+huxley\b|huxley\'s\b|huxley\s+(?:is|has|was|session|started|resumed|completed|froze)|from\s+huxley|to\s+huxley|@huxley|devin-huxley|codex-huxley|\(Huxley\))", re.IGNORECASE)),
    (MEDIUM, "hostname", "fleet hostname 'slate'",
     re.compile(r"(?:host=slate|machine=slate|\bon\s+slate\b|slate\'s\b|slate\s+(?:is|has|was|session|started|resumed|completed|froze)|from\s+slate|to\s+slate|@slate|devin-slate|codex-slate)", re.IGNORECASE)),
    (MEDIUM, "hostname", "fleet hostname 'nodezero'",
     re.compile(r"\bnodezero\b")),
    (MEDIUM, "hostname", "fleet hostname 'beachhead'",
     re.compile(r"\bbeachhead\b")),
    (MEDIUM, "domain", "personal domain 'rpbx.net'",
     re.compile(r"\brpbx\.net\b")),
    (MEDIUM, "pii", "email address",
     re.compile(r"\b[A-Za-z0-9._%+-]+@(?!example\.(com|net|org|edu)\b)[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
    (MEDIUM, "pii", "US phone number",
     re.compile(r"\b\d{3}[-.]\d{3}[-.]\d{4}\b")),

    # --- LOW: Personal references ---
    (LOW, "pii", "full name 'Reuben Paul Bowlby'",
     re.compile(r"Reuben\s+Paul\s+Bowlby")),
    (LOW, "pii", "full name 'Reuben Bowlby'",
     re.compile(r"Reuben\s+Bowlby")),
    (LOW, "pii", "full name 'Paul Verderber'",
     re.compile(r"Paul\s+Verderber")),
]

# Tailscale IPs: 100.x.y.z (CGNAT range used by Tailscale)
TAILSCALE_IP_RE = re.compile(r"\b100\.\d{1,3}\.\d{1,3}\.\d{1,3}\b")

# Internal port numbers -- only flagged when "port" or "bind" appears nearby.
INTERNAL_PORTS = {"18790", "8080", "3030", "2222"}
PORT_CONTEXT_RE = re.compile(r"(?i)(port|bind)")
PORT_CONTEXT_WINDOW = 40

# Severity order for display
_SEVERITY_ORDER = {CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3}


# --- Helpers ---------------------------------------------------------------


def _load_config(repo_root: Path) -> dict:
    """Load .vet-config.json from repo root, merged with defaults."""
    config = dict(DEFAULT_CONFIG)
    config_path = repo_root / CONFIG_FILE
    if not config_path.is_file():
        return config
    try:
        user_config = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"scan-sensitive: could not load {CONFIG_FILE}: {exc}", file=sys.stderr)
        return config
    # Merge: user values extend/override defaults
    for key in DEFAULT_CONFIG:
        if key in user_config:
            config[key] = user_config[key]
    return config


def _build_active_patterns(config: dict) -> list[PatternDef]:
    """Build the active pattern list, applying config overrides.

    - disable_patterns: remove patterns by label
    - severity_overrides: change a pattern's severity
    - custom_patterns: add new patterns
    """
    disabled = set(config.get("disable_patterns", []))
    overrides = config.get("severity_overrides", {})
    customs = config.get("custom_patterns", [])

    active: list[PatternDef] = []
    for severity, category, label, regex in PATTERNS:
        if label in disabled:
            continue
        if label in overrides:
            severity = overrides[label]
        active.append((severity, category, label, regex))

    # Add custom patterns
    for cp in customs:
        try:
            sev = cp.get("severity", MEDIUM)
            cat = cp.get("category", "custom")
            lbl = cp.get("label", "custom pattern")
            pat = re.compile(cp["pattern"])
            active.append((sev, cat, lbl, pat))
        except (KeyError, re.error) as exc:
            print(f"scan-sensitive: invalid custom pattern: {exc}", file=sys.stderr)

    return active


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
        return []
    return [line for line in result.stdout.splitlines() if line.strip()]


def _git_diff_files(ref: str) -> list[str]:
    """Return files changed in the working tree vs ref (unstaged + staged)."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", ref],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return []
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line.strip()]


def _git_branch_files(base_ref: str) -> list[str]:
    """Return files changed on current branch vs base_ref."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", f"{base_ref}...HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return []
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line.strip()]


def _is_scannable(path: Path) -> bool:
    # Never scan this script itself — its pattern definitions contain the
    # very strings it scans for.
    if path.name == "scan-sensitive-pre-commit.py":
        return False
    # Don't scan the allowlist file.
    if path.name == ALLOWLIST_FILE:
        return False
    return path.suffix.lower() in SCANNABLE_EXTENSIONS


def _load_allowlist(repo_root: Path) -> list[str]:
    """Load glob patterns from .vet-allowlist file, if it exists."""
    allowlist_path = repo_root / ALLOWLIST_FILE
    if not allowlist_path.is_file():
        return []
    try:
        text = allowlist_path.read_text(encoding="utf-8")
    except OSError:
        return []
    patterns = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        patterns.append(line)
    return patterns


def _is_allowlisted(rel_path: str, allowlist: list[str]) -> bool:
    """Check if a file path matches any allowlist glob pattern."""
    for pattern in allowlist:
        if fnmatch.fnmatch(rel_path, pattern):
            return True
    return False


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


# --- Scanning --------------------------------------------------------------


def scan_line(line: str, patterns: list[PatternDef] | None = None) -> list[tuple[str, str, str, str]]:
    """Scan a single line; return list of (severity, category, label, matched_text).

    If patterns is provided, use those instead of the global PATTERNS list
    (for config-driven pattern selection). Tailscale IPs and internal ports
    are always checked.
    """
    findings: list[tuple[str, str, str, str]] = []
    active = patterns if patterns is not None else PATTERNS

    for severity, category, label, regex in active:
        for m in regex.finditer(line):
            findings.append((severity, category, label, m.group(0)))

    # Tailscale IPs (always checked — not part of the configurable pattern list)
    for m in TAILSCALE_IP_RE.finditer(line):
        ip = m.group(0)
        if ip == "5.161.114.121":
            continue  # already flagged by the specific VPS IP pattern
        findings.append((HIGH, "ip", "Tailscale CGNAT IP 100.x.x.x", ip))

    # Internal ports in context (always checked)
    for port in INTERNAL_PORTS:
        for m in re.finditer(rf"\b{port}\b", line):
            if _check_port_in_context(line, port):
                findings.append((
                    HIGH, "port",
                    f"internal port {port} (with port/bind context)",
                    m.group(0),
                ))

    return findings


def scan_file(path: Path, patterns: list[PatternDef] | None = None) -> list[tuple[int, str, str, str, str]]:
    """Scan a file; return list of (line_number, severity, category, label, matched_text)."""
    findings: list[tuple[int, str, str, str, str]] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except (OSError, UnicodeDecodeError) as exc:
        print(f"scan-sensitive: could not read {path}: {exc}", file=sys.stderr)
        return findings
    for lineno, line in enumerate(text.splitlines(), start=1):
        for severity, category, label, matched in scan_line(line, patterns):
            findings.append((lineno, severity, category, label, matched))
    return findings


def scan_text(text: str, patterns: list[PatternDef] | None = None) -> list[tuple[int, str, str, str, str]]:
    """Scan arbitrary text; return list of (line_number, severity, category, label, matched_text)."""
    findings: list[tuple[int, str, str, str, str]] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        for severity, category, label, matched in scan_line(line, patterns):
            findings.append((lineno, severity, category, label, matched))
    return findings


# --- Reporting -------------------------------------------------------------


def _format_findings(
    rel: str,
    file_findings: list[tuple[int, str, str, str, str]],
) -> list[str]:
    """Format findings for a single file into output lines."""
    lines = [f"\n  {rel}"]
    # Sort by severity (CRITICAL first), then by line number
    sorted_findings = sorted(
        file_findings,
        key=lambda f: (_SEVERITY_ORDER.get(f[1], 9), f[0]),
    )
    for lineno, severity, _category, label, matched in sorted_findings:
        display = matched if len(matched) <= 60 else matched[:57] + "..."
        lines.append(f"    [{severity}] line {lineno}: {label} -> {display!r}")
    return lines


def _summarize_findings(
    all_findings: list[tuple[str, int, str, str, str, str]],
) -> dict[str, int]:
    """Count findings by severity. all_findings: (file, lineno, severity, category, label, matched)."""
    counts = {CRITICAL: 0, HIGH: 0, MEDIUM: 0, LOW: 0}
    for _file, _lineno, severity, _cat, _label, _matched in all_findings:
        counts[severity] = counts.get(severity, 0) + 1
    return counts


# --- Main ------------------------------------------------------------------


def _parse_args(argv: list[str]) -> tuple[str, list[str], bool, bool]:
    """Parse command-line arguments.

    Returns (mode, extra_args, allow_sensitive, allow_warnings).
    mode is one of: 'staged', 'diff', 'branch', 'file'
    """
    mode = "staged"
    allow_sensitive = False
    allow_warnings = False
    extra: list[str] = []

    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--allow-sensitive":
            allow_sensitive = True
        elif arg == "--allow-warnings":
            allow_warnings = True
        elif arg == "--staged":
            mode = "staged"
        elif arg == "--diff":
            mode = "diff"
        elif arg == "--branch":
            mode = "branch"
            if i + 1 < len(argv) and not argv[i + 1].startswith("-"):
                extra.append(argv[i + 1])
                i += 1
            else:
                extra.append("origin/main")
        elif arg == "--file":
            mode = "file"
        elif arg == "--all":
            mode = "all"
        elif arg == "--help" or arg == "-h":
            print(__doc__)
            sys.exit(EXIT_CLEAN)
        elif arg.startswith("-"):
            print(f"scan-sensitive: unknown flag '{arg}'", file=sys.stderr)
            sys.exit(EXIT_BAD_ARGS)
        else:
            extra.append(arg)
        i += 1

    return mode, extra, allow_sensitive, allow_warnings


def _git_all_tracked_files() -> list[str]:
    """Return all git-tracked files with scannable extensions."""
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return []
    if result.returncode != 0:
        return []
    files = []
    for line in result.stdout.splitlines():
        path = line.strip()
        if not path:
            continue
        if Path(path).suffix.lower() in SCANNABLE_EXTENSIONS:
            files.append(path)
    return files


def _resolve_targets(mode: str, extra: list[str]) -> list[str]:
    """Determine which files to scan based on mode."""
    if mode == "file":
        return [a for a in extra if a]
    if mode == "diff":
        return _git_diff_files("HEAD")
    if mode == "branch":
        ref = extra[0] if extra else "origin/main"
        return _git_branch_files(ref)
    if mode == "all":
        return _git_all_tracked_files()
    # Default: staged
    if extra:
        # Pre-commit framework mode: explicit file paths passed
        return extra
    return _git_staged_files()


def main(argv: list[str]) -> int:
    mode, extra, allow_sensitive, allow_warnings = _parse_args(argv)

    # Full bypass
    if allow_sensitive or os.environ.get("SKIP_SENSITIVE_SCAN") == "1":
        print("scan-sensitive: bypassed (--allow-sensitive / SKIP_SENSITIVE_SCAN=1)")
        return EXIT_CLEAN

    targets = _resolve_targets(mode, extra)
    if not targets:
        if mode != "staged":
            print(f"scan-sensitive: no files to scan in {mode} mode")
        return EXIT_CLEAN

    repo_root = Path(os.getcwd())
    allowlist = _load_allowlist(repo_root)
    config = _load_config(repo_root)
    active_patterns = _build_active_patterns(config)

    all_findings: list[tuple[str, int, str, str, str, str]] = []
    output_lines: list[str] = []

    for rel in targets:
        # Skip allowlisted files
        if _is_allowlisted(rel, allowlist):
            continue
        path = repo_root / rel
        if not path.is_file():
            continue
        if not _is_scannable(path):
            continue
        file_findings = scan_file(path, active_patterns)
        if file_findings:
            for lineno, severity, category, label, matched in file_findings:
                all_findings.append((rel, lineno, severity, category, label, matched))
            output_lines.extend(_format_findings(rel, file_findings))

    if not all_findings:
        if mode != "staged":
            print("scan-sensitive: CLEAN — no sensitive findings.")
        return EXIT_CLEAN

    # Print findings
    for line in output_lines:
        print(line)

    counts = _summarize_findings(all_findings)
    total = len(all_findings)

    # Determine if we block
    blocking = counts[CRITICAL] + counts[HIGH]
    warnings = counts[MEDIUM] + counts[LOW]

    if blocking > 0:
        print(
            f"\nscan-sensitive: BLOCKED — {total} finding(s) "
            f"({counts[CRITICAL]} CRITICAL, {counts[HIGH]} HIGH, "
            f"{counts[MEDIUM]} MEDIUM, {counts[LOW]} LOW).",
            file=sys.stderr,
        )
        print(
            "  CRITICAL/HIGH findings must be resolved or explicitly bypassed.",
            file=sys.stderr,
        )
        print(
            "  Use --allow-sensitive to bypass (document reason in commit message),",
            file=sys.stderr,
        )
        print(
            "  or add file paths to .vet-allowlist to exempt them.",
            file=sys.stderr,
        )
        return EXIT_BLOCKED

    if warnings > 0 and not allow_warnings:
        print(
            f"\nscan-sensitive: BLOCKED — {total} finding(s) "
            f"({counts[CRITICAL]} CRITICAL, {counts[HIGH]} HIGH, "
            f"{counts[MEDIUM]} MEDIUM, {counts[LOW]} LOW).",
            file=sys.stderr,
        )
        print(
            "  MEDIUM/LOW findings are warnings. Review and either:",
            file=sys.stderr,
        )
        print(
            "  (1) redact the content, (2) add to .vet-allowlist, or",
            file=sys.stderr,
        )
        print(
            "  (3) re-run with --allow-warnings to proceed.",
            file=sys.stderr,
        )
        return EXIT_BLOCKED

    if warnings > 0 and allow_warnings:
        print(
            f"\nscan-sensitive: WARNINGS ALLOWED — {total} finding(s) "
            f"({counts[MEDIUM]} MEDIUM, {counts[LOW]} LOW). "
            f"No CRITICAL/HIGH findings.",
        )
        return EXIT_CLEAN

    return EXIT_CLEAN


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
