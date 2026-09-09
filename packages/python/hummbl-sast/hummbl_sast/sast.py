"""AST-based static analysis heuristics using the Python standard library.

Modified by HUMMBL on 2026-09-08: narrow the scanner's scope description.

Uses the ast module to parse Python source and detect security anti-patterns.
No third-party runtime dependencies. Flags selected patterns involving:

  - Code injection (eval, exec, compile)
  - Shell injection (subprocess with shell=True, os.system)
  - Path traversal (urllib with dynamic URLs, file:// scheme)
  - Deserialization (pickle, yaml.load, marshal)
  - Weak crypto (md5, sha1 for security)
  - Hardcoded credentials
  - Binding to all interfaces
  - Assert in production code
  - Disabled SSL verification
  - Tempfile race conditions
"""

from __future__ import annotations

import ast
import hashlib
import os
import pathlib
import re
from dataclasses import dataclass, field
from typing import Sequence


@dataclass
class Finding:
    """A single SAST finding."""
    rule_id: str
    severity: str  # HIGH, MEDIUM, LOW
    confidence: str  # HIGH, MEDIUM, LOW
    message: str
    file: str
    line: int
    col: int = 0
    code_snippet: str = ""
    cwe: str = ""

    def __str__(self) -> str:
        loc = f"{self.file}:{self.line}"
        if self.col:
            loc += f":{self.col}"
        return f"[{self.severity}] {self.rule_id} — {self.message} @ {loc}"


# --- Rule definitions ---

# Each rule is (rule_id, severity, confidence, message, cwe, checker)
# Checkers are functions(ast_node, source_lines) -> list[Finding]

_DANGEROUS_CALLS = {
    # (module, attr) -> (rule_id, severity, message, cwe)
    ("eval", None): ("S001", "HIGH", "Use of eval() — code injection risk", "CWE-94"),
    ("exec", None): ("S002", "HIGH", "Use of exec() — code injection risk", "CWE-94"),
    ("compile", None): ("S003", "MEDIUM", "Use of compile() — dynamic code execution", "CWE-94"),
    ("os", "system"): ("S004", "HIGH", "os.system() — shell injection risk", "CWE-78"),
    ("os", "popen"): ("S005", "HIGH", "os.popen() — shell injection risk", "CWE-78"),
    ("subprocess", "call"): ("S006", "MEDIUM", "subprocess.call() — check for shell=True", "CWE-78"),
    ("subprocess", "run"): ("S007", "MEDIUM", "subprocess.run() — check for shell=True", "CWE-78"),
    ("subprocess", "Popen"): ("S008", "MEDIUM", "subprocess.Popen() — check for shell=True", "CWE-78"),
    ("subprocess", "check_output"): ("S009", "MEDIUM", "subprocess.check_output() — check for shell=True", "CWE-78"),
    ("pickle", "loads"): ("S010", "HIGH", "pickle.loads() — deserialization risk", "CWE-502"),
    ("pickle", "load"): ("S011", "HIGH", "pickle.load() — deserialization risk", "CWE-502"),
    ("cPickle", "loads"): ("S012", "HIGH", "cPickle.loads() — deserialization risk", "CWE-502"),
    ("marshal", "loads"): ("S013", "MEDIUM", "marshal.loads() — deserialization risk", "CWE-502"),
    ("yaml", "load"): ("S014", "HIGH", "yaml.load() without SafeLoader — deserialization risk", "CWE-502"),
    ("urllib.request", "urlopen"): ("S015", "MEDIUM", "urllib.request.urlopen() — audit URL scheme (file:// risk)", "CWE-939"),
    ("urllib", "urlopen"): ("S016", "MEDIUM", "urllib.urlopen() — audit URL scheme (file:// risk)", "CWE-939"),
    ("hashlib", "md5"): ("S017", "MEDIUM", "hashlib.md5() — weak hash for security purposes", "CWE-327"),
    ("hashlib", "sha1"): ("S018", "MEDIUM", "hashlib.sha1() — weak hash for security purposes", "CWE-327"),
    ("random", "random"): ("S019", "LOW", "random.random() — not cryptographically secure", "CWE-330"),
    ("random", "randint"): ("S020", "LOW", "random.randint() — not cryptographically secure", "CWE-330"),
    ("random", "choice"): ("S021", "LOW", "random.choice() — not cryptographically secure", "CWE-330"),
    ("shelve", "open"): ("S022", "MEDIUM", "shelve.open() — pickle-based deserialization risk", "CWE-502"),
    ("tempfile", "mktemp"): ("S023", "MEDIUM", "tempfile.mktemp() — race condition risk", "CWE-377"),
    ("ctypes", "CDLL"): ("S024", "MEDIUM", "ctypes.CDLL() — native code loading risk", "CWE-114"),
}

# Hardcoded password/secret patterns
_SECRET_PATTERNS = [
    (re.compile(r"(?:password|passwd|pwd|secret|token|api_key|apikey|private_key)\s*=\s*['\"]([^'\"]{3,})['\"]", re.I), "S030", "HIGH", "Hardcoded credential in assignment", "CWE-798"),
    (re.compile(r"""(?:password|passwd|pwd)\s*=\s*['"]([^'"\s]{4,})['"]""", re.I), "S032", "MEDIUM", "Hardcoded password in assignment", "CWE-798"),
    (re.compile(r"(?:password|passwd|pwd|secret|token|api_key|apikey)\s*=\s*([A-Za-z0-9_]{8,})", re.I), "S031", "MEDIUM", "Potential hardcoded credential", "CWE-798"),
]

# SSL verification disable patterns
_SSL_DISABLE = {
    ("ssl", "CERT_NONE"): ("S040", "HIGH", "SSL verification disabled (CERT_NONE)", "CWE-295"),
}


class SASTVisitor(ast.NodeVisitor):
    """Walks an AST tree and collects security findings."""

    def __init__(self, filepath: str, source_lines: list[str]):
        self.filepath = filepath
        self.source_lines = source_lines
        self.findings: list[Finding] = []

    def _snippet(self, lineno: int) -> str:
        if 0 < lineno <= len(self.source_lines):
            return self.source_lines[lineno - 1].strip()
        return ""

    def _add(self, rule_id: str, severity: str, confidence: str,
             message: str, node: ast.AST, cwe: str = "") -> None:
        self.findings.append(Finding(
            rule_id=rule_id, severity=severity, confidence=confidence,
            message=message, file=self.filepath, line=getattr(node, "lineno", 0),
            col=getattr(node, "col_offset", 0),
            code_snippet=self._snippet(getattr(node, "lineno", 0)),
            cwe=cwe,
        ))

    def _resolve_call(self, node: ast.Call) -> tuple[str | None, str | None]:
        """Resolve a call node to (module, attribute) or (name, None)."""
        func = node.func
        if isinstance(func, ast.Name):
            return (func.id, None)
        if isinstance(func, ast.Attribute):
            if isinstance(func.value, ast.Name):
                return (func.value.id, func.attr)
            # Handle nested: urllib.request.urlopen
            if isinstance(func.value, ast.Attribute):
                if isinstance(func.value.value, ast.Name):
                    return (f"{func.value.value.id}.{func.value.attr}", func.attr)
        return (None, None)

    def visit_Call(self, node: ast.Call) -> None:
        mod, attr = self._resolve_call(node)

        # Check dangerous calls table
        key = (mod, attr)
        if key in _DANGEROUS_CALLS:
            rule_id, sev, msg, cwe = _DANGEROUS_CALLS[key]
            confidence = "HIGH"

            # Special case: subprocess with shell=False is fine
            if mod == "subprocess" and attr in ("call", "run", "Popen", "check_output"):
                shell_arg = None
                for kw in node.keywords:
                    if kw.arg == "shell":
                        shell_arg = kw.value
                # Check positional shell arg (usually 2nd after cmd)
                if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
                    shell_arg = node.args[1]

                if shell_arg is not None:
                    if isinstance(shell_arg, ast.Constant) and shell_arg.value is False:
                        self.generic_visit(node)
                        return
                    if isinstance(shell_arg, ast.Constant) and shell_arg.value is True:
                        self._add(rule_id, "HIGH", "HIGH",
                                  f"{msg} with shell=True — shell injection risk", node, cwe)
                        self.generic_visit(node)
                        return
                # No shell arg — medium risk
                confidence = "MEDIUM"

            # Special case: yaml.load with SafeLoader is fine
            if mod == "yaml" and attr == "load":
                for kw in node.keywords:
                    if kw.arg == "Loader":
                        if isinstance(kw.value, ast.Name) and "Safe" in kw.value.id:
                            self.generic_visit(node)
                            return
                        if isinstance(kw.value, ast.Attribute) and "Safe" in kw.value.attr:
                            self.generic_visit(node)
                            return

            self._add(rule_id, sev, confidence, msg, node, cwe)

        # Check SSL disable
        for (smod, sattr), (rule_id, sev, msg, cwe) in _SSL_DISABLE.items():
            if mod == smod and attr == sattr:
                self._add(rule_id, sev, "HIGH", msg, node, cwe)

        self.generic_visit(node)

    def visit_Assert(self, node: ast.Assert) -> None:
        self._add("S050", "LOW", "MEDIUM",
                  "assert statement — removed in optimized mode, not for validation", node, "CWE-617")
        self.generic_visit(node)

    def visit_Compare(self, node: ast.Compare) -> None:
        # Detect: assert x == y pattern is handled by visit_Assert
        # Detect: 0.0.0.0 binding
        for comparator in [node.left] + node.comparators:
            if isinstance(comparator, ast.Constant) and comparator.value == "0.0.0.0":
                self._add("S041", "MEDIUM", "MEDIUM",
                          "Binding to 0.0.0.0 — all interfaces", node, "CWE-605")
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        # Check for hardcoded credentials via regex on source
        if node.lineno and node.lineno <= len(self.source_lines):
            line = self.source_lines[node.lineno - 1]
            for pattern, rule_id, sev, msg, cwe in _SECRET_PATTERNS:
                if pattern.search(line):
                    self._add(rule_id, sev, "HIGH", msg, node, cwe)
        # Check for binding to 0.0.0.0
        for child in ast.walk(node):
            if isinstance(child, ast.Constant) and child.value == "0.0.0.0":
                self._add("S041", "MEDIUM", "MEDIUM",
                          "Binding to 0.0.0.0 — all interfaces", node, "CWE-605")
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        # Flag import of telnetlib (deprecated, insecure)
        for alias in node.names:
            if alias.name == "telnetlib":
                self._add("S060", "MEDIUM", "HIGH",
                          "telnetlib import — deprecated, no encryption", node, "CWE-319")
            if alias.name == "ftplib":
                self._add("S061", "LOW", "HIGH",
                          "ftplib import — no encryption by default", node, "CWE-319")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module == "telnetlib":
            self._add("S060", "MEDIUM", "HIGH",
                      "telnetlib import — deprecated, no encryption", node, "CWE-319")
        if node.module == "ftplib":
            self._add("S061", "LOW", "HIGH",
                      "ftplib import — no encryption by default", node, "CWE-319")
        self.generic_visit(node)


def scan_file(filepath: str | pathlib.Path) -> list[Finding]:
    """Scan a single Python file for security issues.

    Args:
        filepath: Path to a .py file.

    Returns:
        List of findings.
    """
    filepath = str(filepath)
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            source = f.read()
    except (OSError, UnicodeDecodeError):
        return []

    try:
        tree = ast.parse(source, filename=filepath)
    except SyntaxError:
        return []

    source_lines = source.splitlines()
    visitor = SASTVisitor(filepath, source_lines)
    visitor.visit(tree)
    return visitor.findings


def scan_directory(
    root: str | pathlib.Path,
    exclude_dirs: Sequence[str] = (".git", ".venv", "venv", "__pycache__", "node_modules", ".mypy_cache", ".pytest_cache", "dist", "build", ".tox"),
    exclude_patterns: Sequence[str] = (),
) -> list[Finding]:
    """Scan all Python files in a directory tree.

    Args:
        root: Root directory to scan.
        exclude_dirs: Directory names to skip.
        exclude_patterns: Regex patterns to skip matching file paths.

    Returns:
        List of findings sorted by file then line.
    """
    root = pathlib.Path(root)
    exclude_set = set(exclude_dirs)
    compiled_excludes = [re.compile(p) for p in exclude_patterns]

    findings: list[Finding] = []

    for dirpath, dirnames, filenames in os.walk(root):
        # Filter excluded dirs in-place (modifies dirnames to prune walk)
        dirnames[:] = [d for d in dirnames if d not in exclude_set]

        for fname in filenames:
            if not fname.endswith(".py"):
                continue
            fpath = pathlib.Path(dirpath) / fname
            relpath = str(fpath.relative_to(root))

            # Check exclude patterns
            if any(p.search(relpath) for p in compiled_excludes):
                continue

            findings.extend(scan_file(fpath))

    findings.sort(key=lambda f: (f.file, f.line))
    return findings


def summarize(findings: list[Finding]) -> dict:
    """Produce a summary of findings by severity."""
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


def format_report(findings: list[Finding], root: str = "") -> str:
    """Format findings as a human-readable report."""
    summary = summarize(findings)
    lines = [
        f"SAST Scan Report — {root or '.'}",
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
            lines.append(f"    {loc}:{f.line}")
            if f.code_snippet:
                lines.append(f"    > {f.code_snippet}")
            lines.append("")

    return "\n".join(lines)
