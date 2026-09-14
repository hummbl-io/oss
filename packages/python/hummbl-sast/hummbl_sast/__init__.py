"""hummbl-sast — stdlib-only security scanner for Python projects.

Experimental checks:
  - sast: AST-based static analysis heuristics
  - secret-scan: Regex-based credential-pattern detection
  - dep-audit: Dependency vulnerability lookups via OSV.dev

Modified by HUMMBL on 2026-09-08: narrow scope claims and export lookup errors.

Zero third-party runtime dependencies. Python 3.11+ (uses tomllib).
"""

__version__ = "0.1.0"

from .sast import Finding, scan_file as sast_scan_file, scan_directory as sast_scan_directory, format_report as sast_report
from .secret_scan import SecretFinding, scan_file as secret_scan_file, scan_directory as secret_scan_directory, format_report as secret_report
from .dep_audit import DependencyAuditError, VulnFinding, audit_directory, format_report as dep_report

__all__ = [
    "Finding", "sast_scan_file", "sast_scan_directory", "sast_report",
    "SecretFinding", "secret_scan_file", "secret_scan_directory", "secret_report",
    "DependencyAuditError", "VulnFinding", "audit_directory", "dep_report",

]
