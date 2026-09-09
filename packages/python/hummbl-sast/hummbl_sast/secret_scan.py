"""Regex-based secret-pattern scanner using the Python standard library.

Modified by HUMMBL on 2026-09-08: narrow the scanner's scope description.


Scans files for leaked credentials: API keys, tokens, private keys, passwords,
database connection strings, and other sensitive patterns.

No third-party dependencies. Uses only re, os, pathlib.
"""

from __future__ import annotations

import os
import pathlib
import re
from dataclasses import dataclass
from typing import Sequence


@dataclass
class SecretFinding:
    """A single secret scanning finding."""
    rule_id: str
    severity: str  # HIGH, MEDIUM
    message: str
    file: str
    line: int
    col: int
    match: str  # The matched text (redacted in output)
    redacted: str  # Match with secret value masked

    def __str__(self) -> str:
        return f"[{self.severity}] {self.rule_id} — {self.message} @ {self.file}:{self.line}"


def _redact(text: str, visible: int = 4) -> str:
    """Redact a secret, showing only first `visible` chars."""
    if len(text) <= visible:
        return "***"
    return text[:visible] + "***"


# --- Secret patterns ---
# Each entry: (rule_id, severity, message, regex, group_index_for_secret)
# Patterns are ordered by specificity — most specific first.

_SECRET_RULES: list[tuple[str, str, str, re.Pattern, int]] = [
    # Private keys (PEM format)
    (
        "SEC001", "HIGH",
        "Private key (PEM) detected",
        re.compile(
            r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY-----",
            re.MULTILINE,
        ),
        0,
    ),
    # AWS Access Key ID
    (
        "SEC002", "HIGH",
        "AWS Access Key ID detected",
        re.compile(r"\b(AKIA[0-9A-Z]{16})\b"),
        1,
    ),
    # AWS Secret Access Key (40 chars, base64-ish after known prefix patterns)
    (
        "SEC003", "HIGH",
        "AWS Secret Access Key pattern detected",
        re.compile(r"(?:aws_secret|secret_access_key|aws_secret_access_key)\s*[=:]\s*['\"]?([A-Za-z0-9/+=]{40})['\"]?", re.I),
        1,
    ),
    # GitHub tokens
    (
        "SEC004", "HIGH",
        "GitHub token detected",
        re.compile(r"\b(gh[pousr]_[A-Za-z0-9]{36,})\b"),
        1,
    ),
    # GitHub classic tokens (older format)
    (
        "SEC005", "HIGH",
        "GitHub classic token detected",
        re.compile(r"\b(gho_[A-Za-z0-9]{36})\b"),
        1,
    ),
    # GitLab tokens
    (
        "SEC006", "HIGH",
        "GitLab token detected",
        re.compile(r"\b(glpat-[A-Za-z0-9_-]{20})\b"),
        1,
    ),
    # Slack tokens
    (
        "SEC007", "HIGH",
        "Slack token detected",
        re.compile(r"\b(xox[baprs]-[A-Za-z0-9-]{10,})\b"),
        1,
    ),
    # Stripe keys
    (
        "SEC008", "HIGH",
        "Stripe secret key detected",
        re.compile(r"\b(sk_live_[A-Za-z0-9]{24,})\b"),
        1,
    ),
    (
        "SEC009", "MEDIUM",
        "Stripe restricted key detected",
        re.compile(r"\b(rk_live_[A-Za-z0-9]{24,})\b"),
        1,
    ),
    # Google API keys
    (
        "SEC010", "HIGH",
        "Google API key detected",
        re.compile(r"\b(AIza[0-9A-Za-z_-]{35})\b"),
        1,
    ),
    # OpenAI API keys
    (
        "SEC011", "HIGH",
        "OpenAI API key detected",
        re.compile(r"\b(sk-[A-Za-z0-9]{20}T3BlbkFJ[A-Za-z0-9]{20})\b"),
        1,
    ),
    # OpenAI new-format keys (sk-proj-...)
    (
        "SEC012", "HIGH",
        "OpenAI project API key detected",
        re.compile(r"\b(sk-proj-[A-Za-z0-9_-]{40,})\b"),
        1,
    ),
    # Anthropic API keys
    (
        "SEC013", "HIGH",
        "Anthropic API key detected",
        re.compile(r"\b(sk-ant-[A-Za-z0-9_-]{40,})\b"),
        1,
    ),
    # Generic API key assignments
    (
        "SEC020", "MEDIUM",
        "Hardcoded API key in assignment",
        re.compile(r"(?:api[_-]?key|apikey)\s*[=:]\s*['\"]([A-Za-z0-9_-]{20,})['\"]", re.I),
        1,
    ),
    # Generic secret/token assignments
    (
        "SEC021", "MEDIUM",
        "Hardcoded secret/token in assignment",
        re.compile(r"(?:secret|token|auth[_-]?token|access[_-]?token)\s*[=:]\s*['\"]([A-Za-z0-9_./+=-]{16,})['\"]", re.I),
        1,
    ),
    # Password assignments
    (
        "SEC022", "MEDIUM",
        "Hardcoded password in assignment",
        re.compile(r"""(?:password|passwd|pwd)\s*[=:]\s*['"]([^'"\s]{4,})['"]""", re.I),
        1,
    ),
    # Database connection strings with credentials
    (
        "SEC030", "HIGH",
        "Database connection string with credentials detected",
        re.compile(r"(?:postgres|postgresql|mysql|mongodb|redis)://[^:]+:([^@]+)@", re.I),
        1,
    ),
    # JWT tokens
    (
        "SEC040", "MEDIUM",
        "JWT token detected",
        re.compile(r"\b(eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+)\b"),
        1,
    ),
    # Generic high-entropy strings (base64, 32+ chars, looks like a key)
    (
        "SEC050", "LOW",
        "High-entropy string — possible secret",
        re.compile(r"['\"]([A-Za-z0-9+/]{32,}={0,2})['\"]"),
        1,
    ),
    # .env file patterns
    (
        "SEC060", "MEDIUM",
        "Credential in .env-style file",
        re.compile(r"^(?:export\s+)?([A-Z_]+(?:KEY|TOKEN|SECRET|PASSWORD|PASS|PWD|CREDENTIAL)[A-Z_]*)\s*=\s*(.+)$", re.I | re.MULTILINE),
        2,
    ),
    # Tailscale auth keys
    (
        "SEC070", "HIGH",
        "Tailscale auth key detected",
        re.compile(r"\b(tskey-(?:auth|node|ephemeral)-[A-Za-z0-9]+)\b"),
        1,
    ),
    # Cloudflare API tokens
    (
        "SEC071", "HIGH",
        "Cloudflare API token detected",
        re.compile(r"\b([A-Za-z0-9_-]{40})\b.*cloudflare", re.I),
        1,
    ),
    # DigitalOcean tokens
    (
        "SEC072", "HIGH",
        "DigitalOcean token detected",
        re.compile(r"\b(dop_v1_[A-Za-z0-9]{64})\b"),
        1,
    ),
    # Heroku API keys
    (
        "SEC073", "HIGH",
        "Heroku API key detected",
        re.compile(r"(?:heroku[_-]?api[_-]?key|HEROKU_API_KEY)\s*[=:]\s*['\"]?([A-Za-z0-9]{32,})['\"]?", re.I),
        1,
    ),
    # Twilio Account SID + Auth Token
    (
        "SEC074", "HIGH",
        "Twilio Account SID detected",
        re.compile(r"\b(AC[a-z0-9]{32})\b"),
        1,
    ),
]

# File extensions to scan
_SCANABLE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rb", ".php",
    ".c", ".cpp", ".h", ".hpp", ".cs", ".rs", ".swift", ".kt",
    ".yml", ".yaml", ".json", ".toml", ".ini", ".cfg", ".conf", ".env",
    ".sh", ".bash", ".zsh", ".ps1", ".bat", ".cmd",
    ".xml", ".html", ".css", ".sql", ".graphql", ".gql",
    ".md", ".rst", ".txt",  # docs can leak secrets too
    ".dockerfile", ".tf", ".hcl",
}

# Files that should always be scanned (no extension)
_ALWAYS_SCAN_FILES = {
    "dockerfile", "dockerfile.dev", "dockerfile.prod",
    ".env", ".env.local", ".env.production", ".env.development",
    ".gitignore",  # check for leaked secrets in comments
}

# Directories to never scan
_EXCLUDE_DIRS = {
    ".git", ".venv", "venv", "__pycache__", "node_modules",
    ".mypy_cache", ".pytest_cache", ".ruff_cache",
    "dist", "build", ".tox", ".eggs", "egg-info",
    ".cache", "vendor", "third_party",
}


def _is_scanable(path: pathlib.Path) -> bool:
    """Check if a file should be scanned."""
    name = path.name.lower()
    if name in _ALWAYS_SCAN_FILES:
        return True
    if name.startswith(".env"):
        return True
    return path.suffix.lower() in _SCANABLE_EXTENSIONS


def _redact_match(match_text: str, group_idx: int, full_match: str) -> str:
    """Redact the secret portion of a match."""
    if group_idx == 0:
        return _redact(full_match)
    # Try to extract the specific group
    # We re-run the regex to get group positions
    return full_match  # Will be redacted by caller


def scan_file(filepath: str | pathlib.Path) -> list[SecretFinding]:
    """Scan a single file for secrets.

    Args:
        filepath: Path to scan.

    Returns:
        List of secret findings.
    """
    filepath = pathlib.Path(filepath)
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except OSError:
        return []

    findings: list[SecretFinding] = []
    lines = content.splitlines()

    for rule_id, severity, message, pattern, group_idx in _SECRET_RULES:
        for match in pattern.finditer(content):
            # Calculate line number from match position
            pos = match.start()
            line_num = content[:pos].count("\n") + 1
            col = pos - (content.rfind("\n", 0, pos) + 1) if pos > 0 else pos

            # Get the secret value for redaction
            try:
                secret_val = match.group(group_idx) if group_idx > 0 else match.group(0)
            except (IndexError, re.error):
                secret_val = match.group(0)

            redacted = _redact(secret_val)

            # Get the full line for context
            line_text = lines[line_num - 1].strip() if line_num <= len(lines) else ""

            findings.append(SecretFinding(
                rule_id=rule_id,
                severity=severity,
                message=message,
                file=str(filepath),
                line=line_num,
                col=col,
                match=line_text,  # Don't store the actual secret
                redacted=redacted,
            ))

    # Deduplicate (same file, line, rule)
    seen: set[tuple[str, int, str]] = set()
    unique: list[SecretFinding] = []
    for f in findings:
        key = (f.rule_id, f.line, f.file)
        if key not in seen:
            seen.add(key)
            unique.append(f)

    return unique


def scan_directory(
    root: str | pathlib.Path,
    exclude_dirs: Sequence[str] = (),
    exclude_patterns: Sequence[str] = (),
    max_file_size: int = 1_000_000,  # 1MB
) -> list[SecretFinding]:
    """Scan all files in a directory tree for secrets.

    Args:
        root: Root directory to scan.
        exclude_dirs: Additional directory names to skip.
        exclude_patterns: Regex patterns to skip matching file paths.
        max_file_size: Skip files larger than this (bytes).

    Returns:
        List of findings sorted by file then line.
    """
    root = pathlib.Path(root)
    all_excludes = _EXCLUDE_DIRS | set(exclude_dirs)
    compiled_excludes = [re.compile(p) for p in exclude_patterns]

    findings: list[SecretFinding] = []

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in all_excludes]

        for fname in filenames:
            fpath = pathlib.Path(dirpath) / fname
            if not _is_scanable(fpath):
                continue

            # Skip large files
            try:
                if fpath.stat().st_size > max_file_size:
                    continue
            except OSError:
                continue

            relpath = str(fpath.relative_to(root))
            if any(p.search(relpath) for p in compiled_excludes):
                continue

            findings.extend(scan_file(fpath))

    findings.sort(key=lambda f: (f.file, f.line))
    return findings


def summarize(findings: list[SecretFinding]) -> dict:
    """Produce a summary of secret findings by severity."""
    by_sev: dict[str, int] = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    by_rule: dict[str, int] = {}
    for f in findings:
        by_sev[f.severity] = by_sev.get(f.severity, 0) + 1
        by_rule[f.rule_id] = by_rule.get(f.rule_id, 0) + 1

    return {
        "total": len(findings),
        "by_severity": by_sev,
        "by_rule": dict(sorted(by_rule.items(), key=lambda x: -x[1])),
    }


def format_report(findings: list[SecretFinding], root: str = "") -> str:
    """Format findings as a human-readable report."""
    summary = summarize(findings)
    lines = [
        f"Secret Scan Report — {root or '.'}",
        "=" * 60,
        f"Total findings: {summary['total']}",
        f"  HIGH:   {summary['by_severity']['HIGH']}",
        f"  MEDIUM: {summary['by_severity']['MEDIUM']}",
        f"  LOW:    {summary['by_severity']['LOW']}",
        "",
    ]

    for sev in ["HIGH", "MEDIUM", "LOW"]:
        sev_findings = [f for f in findings if f.severity == sev]
        if not sev_findings:
            continue
        lines.append(f"--- {sev} ({len(sev_findings)}) ---")
        for f in sev_findings:
            loc = f.file
            if root:
                try:
                    loc = str(pathlib.Path(f.file).relative_to(root))
                except ValueError:
                    pass
            lines.append(f"  {f.rule_id} — {f.message}")
            lines.append(f"    {loc}:{f.line}  (secret: {f.redacted})")
            lines.append("")

    return "\n".join(lines)
