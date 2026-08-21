#!/usr/bin/env python3
"""
tools/adr_lint.py — ADR Format Compliance Linter

Validates ADR files against the HUMMBL Init Standard v0.1 format.
Designed for CI integration — exits non-zero on violations.

Checks:
    1. Filename format: ADR-NNN-kebab-title.md (3-digit, zero-padded)
    2. Required header fields: Status, Date, Decision owner, Steward
    3. Status value is lowercase (accepted, proposed, superseded, deprecated)
    4. Date format: YYYY-MM-DD
    5. Required sections: Context, Decision
    6. No duplicate ADR numbers within a repo
    7. Superseded ADRs have a "Superseded by" field pointing to a valid ADR

Usage:
    python tools/adr_lint.py [path/to/docs/adr/]
    python tools/adr_lint.py --check-repo <repo-name> --org hummbl-dev
    python tools/adr_lint.py --ci  # CI mode: check all ADRs, exit 1 on violations

Exit codes:
    0 — all ADRs pass
    1 — one or more violations found
    2 — error (no ADR directory found)
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from dataclasses import dataclass, field

# --- Constants ---

# Standard: ADR-NNN-kebab-title.md
FILENAME_PATTERN = re.compile(r'^ADR-(\d{3})-([a-z0-9-]+)\.md$')
# Domain-prefixed: ADR-FM-NNN-title.md, ADR-GOV-NNN-title.md, ADR-ATL-WEDGE-NNN-title.md, etc.
DOMAIN_FILENAME_PATTERN = re.compile(r'^ADR-([A-Z]{2,6}(?:-[A-Z]{2,6})?)-(\d{3})-([a-z0-9-]+)\.md$')
REQUIRED_FIELDS = ["Status", "Date", "Decision owner", "Steward"]
VALID_STATUSES = {"accepted", "proposed", "superseded", "deprecated"}
DATE_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}$')
REQUIRED_SECTIONS = ["Context", "Decision"]

# --- Data classes ---

@dataclass
class Violation:
    file: str
    line: int
    rule: str
    message: str
    severity: str = "error"  # error, warning

@dataclass
class LintResult:
    file: str
    violations: list = field(default_factory=list)
    passed: bool = True

# --- Linting functions ---

def lint_filename(filepath):
    """Check filename format."""
    basename = os.path.basename(filepath)
    violations = []

    if not basename.endswith(".md"):
        return [Violation(
            file=filepath, line=0, rule="F001",
            message=f"ADR file must end with .md, got: {basename}"
        )]

    # Skip non-ADR files (index, template, draft)
    if basename.upper() in ("ADR_INDEX.MD", "ADR_TEMPLATE.MD") or basename.startswith("DRAFT"):
        return []

    m = FILENAME_PATTERN.match(basename)
    if not m:
        # Check domain-prefixed pattern (ADR-FM-NNN-title.md, ADR-GOV-NNN-title.md, etc.)
        dm = DOMAIN_FILENAME_PATTERN.match(basename)
        if dm:
            return violations  # Domain-prefixed filenames are valid

        # Check for common issues
        if re.match(r'^\d{3}-', basename):
            violations.append(Violation(
                file=filepath, line=0, rule="F002",
                message=f"Missing ADR- prefix: {basename} → ADR-{basename}"
            ))
        elif re.match(r'^ADR-0\d{3}-', basename):
            violations.append(Violation(
                file=filepath, line=0, rule="F003",
                message=f"4-digit number should be 3-digit: {basename}"
            ))
        elif re.match(r'^ADR-\d{3}_', basename):
            violations.append(Violation(
                file=filepath, line=0, rule="F005",
                message=f"Underscore instead of hyphen: {basename}"
            ))
        else:
            violations.append(Violation(
                file=filepath, line=0, rule="F000",
                message=f"Filename doesn't match ADR-NNN-kebab-title.md: {basename}"
            ))

    return violations

def lint_header_fields(filepath, content):
    """Check required header fields."""
    violations = []
    lines = content.split("\n")

    for field_name in REQUIRED_FIELDS:
        # Check for field in various formats
        patterns = [
            rf'- \*\*{re.escape(field_name)}:\*\* ',  # Standard: - **Field:** value
            rf'\*\*{re.escape(field_name)}\*\*: ',     # Alt: **Field**: value
            rf'^{re.escape(field_name)}: ',             # Bare: Field: value
        ]

        found = False
        for i, line in enumerate(lines[:20]):  # Check first 20 lines
            for pattern in patterns:
                if re.search(pattern, line, re.MULTILINE):
                    found = True
                    break
            if found:
                break

        if not found:
            violations.append(Violation(
                file=filepath, line=0, rule="H001",
                message=f"Missing required field: {field_name}"
            ))

    return violations

def lint_status_format(filepath, content):
    """Check status field format and value."""
    violations = []
    lines = content.split("\n")

    for i, line in enumerate(lines[:20]):
        # Standard format: - **Status:** accepted
        m = re.search(r'- \*\*Status:\*\* (\w+)', line)
        if m:
            value = m.group(1)
            if value not in VALID_STATUSES:
                violations.append(Violation(
                    file=filepath, line=i+1, rule="S001",
                    message=f"Invalid status value: '{value}' (must be one of: {', '.join(VALID_STATUSES)})"
                ))
            if value != value.lower():
                violations.append(Violation(
                    file=filepath, line=i+1, rule="S002",
                    message=f"Status should be lowercase: '{value}' → '{value.lower()}'"
                ))
            return violations

        # Non-standard format
        m = re.search(r'\*\*Status\*\*:?\s*(\w+)', line)
        if m:
            violations.append(Violation(
                file=filepath, line=i+1, rule="S003",
                message=f"Non-standard status format. Use: - **Status:** {m.group(1).lower()}"
            ))
            return violations

        # ## Status header
        if re.match(r'^## Status', line):
            violations.append(Violation(
                file=filepath, line=i+1, rule="S004",
                message="Use '- **Status:** value' instead of '## Status\\n\\nvalue'"
            ))
            return violations

    return violations

def lint_date_format(filepath, content):
    """Check date field format."""
    violations = []
    lines = content.split("\n")

    for i, line in enumerate(lines[:20]):
        # Standard: - **Date:** YYYY-MM-DD
        m = re.search(r'- \*\*Date:\*\* (\d{4}-\d{2}-\d{2})', line)
        if m:
            return violations  # OK

        # Non-standard: **Date**: or **Decided**:
        m = re.search(r'\*\*(?:Date|Decided)\*\*:?\s*(\d{4}-\d{2}-\d{2})', line)
        if m:
            violations.append(Violation(
                file=filepath, line=i+1, rule="D001",
                message=f"Non-standard date format. Use: - **Date:** {m.group(1)}"
            ))
            return violations

    # No date found
    violations.append(Violation(
        file=filepath, line=0, rule="D002",
        message="Missing date field",
        severity="warning"
    ))
    return violations

def lint_sections(filepath, content):
    """Check required sections."""
    violations = []

    for section in REQUIRED_SECTIONS:
        if not re.search(rf'^##\s+{re.escape(section)}', content, re.MULTILINE):
            violations.append(Violation(
                file=filepath, line=0, rule="SEC001",
                message=f"Missing required section: ## {section}",
                severity="warning"
            ))

    return violations

def lint_duplicate_numbers(adr_files):
    """Check for duplicate ADR numbers within the same directory (per-domain).

    ADR-001 in docs/adr/governance/ and ADR-001 in docs/adr/platform/ are NOT
    duplicates — they're in separate domain directories. Only flag duplicates
    within the same directory.
    """
    violations = []
    # Group files by parent directory
    by_dir = {}
    for filepath in adr_files:
        parent = os.path.dirname(filepath)
        if parent not in by_dir:
            by_dir[parent] = {}
        basename = os.path.basename(filepath)
        # Extract the full ADR identifier (including domain prefix if present)
        m = re.search(r'ADR-(?:([A-Z]{2,6})-)?(\d{3})-', basename)
        if m:
            domain = m.group(1) or ""
            num = m.group(2)
            key = f"{domain}-{num}" if domain else num
            if key in by_dir[parent]:
                violations.append(Violation(
                    file=filepath, line=0, rule="DUP001",
                    message=(
                        f"Duplicate ADR number: ADR-{domain}-{num if domain else num}"
                        f" (also in {os.path.basename(by_dir[parent][key])})"
                    )
                ))
            else:
                by_dir[parent][key] = filepath

    return violations

def lint_superseded_refs(filepath, content, all_adr_numbers):
    """Check that superseded-by references point to valid ADRs.

    Supports both standard (ADR-NNN) and domain-prefixed (ADR-FM-NNN) references.
    """
    violations = []

    # Match both standard (ADR-001) and domain-prefixed (ADR-FM-001) references
    m = re.search(
        r'\*\*Superseded by:\*\* (ADR-(?:[A-Z]{2,6}(?:-[A-Z]{2,6})?-)?\d{3}|none)',
        content,
    )
    if m:
        ref = m.group(1)
        if ref != "none":
            # Extract the full identifier (domain prefix + number or just number)
            id_match = re.search(
                r'ADR-((?:[A-Z]{2,6}(?:-[A-Z]{2,6})?-)?\d{3})',
                ref,
            )
            if id_match:
                ref_id = id_match.group(1)
                if ref_id not in all_adr_numbers:
                    violations.append(Violation(
                        file=filepath, line=0, rule="REF001",
                        message=f"Superseded by references non-existent ADR: {ref}"
                    ))

    return violations

# --- Main lint ---

def lint_adr_file(filepath, all_adr_numbers=None):
    """Run all lint checks on a single ADR file."""
    result = LintResult(file=filepath)

    # Filename check
    result.violations.extend(lint_filename(filepath))

    # Read content
    try:
        content = Path(filepath).read_text()
    except Exception as e:
        result.violations.append(Violation(
            file=filepath, line=0, rule="ERR",
            message=f"Could not read file: {e}"
        ))
        result.passed = False
        return result

    # Header fields
    result.violations.extend(lint_header_fields(filepath, content))

    # Status format
    result.violations.extend(lint_status_format(filepath, content))

    # Date format
    result.violations.extend(lint_date_format(filepath, content))

    # Sections
    result.violations.extend(lint_sections(filepath, content))

    # Superseded refs
    if all_adr_numbers:
        result.violations.extend(lint_superseded_refs(filepath, content, all_adr_numbers))

    result.passed = len([v for v in result.violations if v.severity == "error"]) == 0
    return result

def lint_directory(adr_dir):
    """Lint all ADR files in a directory (recursively)."""
    adr_path = Path(adr_dir)
    if not adr_path.exists():
        print(f"Error: ADR directory not found: {adr_dir}")
        return [], 2

    # Find all .md files
    adr_files = sorted(str(f) for f in adr_path.rglob("*.md")
                       if not f.name.upper().startswith("ADR_INDEX")
                       and not f.name.upper().startswith("ADR_TEMPLATE")
                       and not f.name.startswith("DRAFT"))

    if not adr_files:
        print(f"No ADR files found in {adr_dir}")
        return [], 0

    # Collect all ADR numbers for cross-reference checking
    # Supports both standard (ADR-NNN) and domain-prefixed (ADR-FM-NNN) formats
    all_numbers = set()
    for f in adr_files:
        basename = os.path.basename(f)
        # Standard: ADR-NNN-title.md → "NNN"
        m = re.match(r'^ADR-(\d{3})-', basename)
        if m:
            all_numbers.add(m.group(1))
        # Domain-prefixed: ADR-FM-NNN-title.md → "FM-NNN"
        m = re.match(r'^ADR-([A-Z]{2,6}(?:-[A-Z]{2,6})?)-(\d{3})-', basename)
        if m:
            all_numbers.add(f"{m.group(1)}-{m.group(2)}")

    # Check for duplicates
    dup_violations = lint_duplicate_numbers(adr_files)

    # Lint each file
    results = []
    for filepath in adr_files:
        result = lint_adr_file(filepath, all_numbers)
        results.append(result)

    # Add duplicate violations to the first affected file
    if dup_violations:
        for v in dup_violations:
            # Find the result for this file
            for r in results:
                if r.file == v.file:
                    r.violations.append(v)
                    r.passed = False
                    break

    return results, 0

def lint_repo_via_api(repo, org="hummbl-dev"):
    """Lint ADRs in a remote repo via GitHub API."""
    cmd = ["gh", "api", f"repos/{org}/{repo}/git/trees/HEAD?recursive=1"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error fetching tree for {repo}: {result.stderr}")
        return [], 2

    tree_data = json.loads(result.stdout)
    all_paths = [item["path"] for item in tree_data.get("tree", [])]
    adr_paths = [p for p in all_paths if "docs/adr/" in p and p.endswith(".md")
                 and "ADR_INDEX" not in p.upper() and "ADR_TEMPLATE" not in p.upper()
                 and not os.path.basename(p).startswith("DRAFT")]

    if not adr_paths:
        return [], 0

    # Collect ADR numbers (standard + domain-prefixed)
    all_numbers = set()
    for p in adr_paths:
        basename = os.path.basename(p)
        m = re.match(r'^ADR-(\d{3})-', basename)
        if m:
            all_numbers.add(m.group(1))
        m = re.match(r'^ADR-([A-Z]{2,6}(?:-[A-Z]{2,6})?)-(\d{3})-', basename)
        if m:
            all_numbers.add(f"{m.group(1)}-{m.group(2)}")

    # Fetch and lint each file
    import base64
    results = []
    for adr_path in adr_paths:
        cmd = ["gh", "api", f"repos/{org}/{repo}/contents/{adr_path}", "--jq", ".content"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            continue

        content = base64.b64decode(result.stdout.strip()).decode()

        # Create a temporary result
        lint_result = LintResult(file=f"{repo}:{adr_path}")

        # Filename check
        lint_result.violations.extend(lint_filename(adr_path))

        # Header fields
        lint_result.violations.extend(lint_header_fields(adr_path, content))

        # Status format
        lint_result.violations.extend(lint_status_format(adr_path, content))

        # Date format
        lint_result.violations.extend(lint_date_format(adr_path, content))

        # Superseded refs
        lint_result.violations.extend(lint_superseded_refs(adr_path, content, all_numbers))

        lint_result.passed = len([v for v in lint_result.violations if v.severity == "error"]) == 0
        results.append(lint_result)

    # Check duplicates
    dup_violations = lint_duplicate_numbers(adr_paths)
    for v in dup_violations:
        for r in results:
            if r.file.endswith(os.path.basename(v.file)):
                r.violations.append(v)
                r.passed = False
                break

    return results, 0

# --- CLI ---

def main():
    parser = argparse.ArgumentParser(
        description="ADR Format Compliance Linter (HUMMBL Init Standard v0.1)"
    )
    parser.add_argument("path", nargs="?", default="docs/adr/", help="Path to ADR directory")
    parser.add_argument("--check-repo", help="Lint ADRs in a remote GitHub repo")
    parser.add_argument("--org", default="hummbl-dev", help="GitHub org")
    parser.add_argument("--ci", action="store_true", help="CI mode: exit 1 on violations")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")

    args = parser.parse_args()

    if args.check_repo:
        results, exit_code = lint_repo_via_api(args.check_repo, args.org)
    else:
        results, exit_code = lint_directory(args.path)

    if exit_code != 0:
        sys.exit(exit_code)

    # Collect violations
    all_violations = []
    passed = 0
    failed = 0

    for r in results:
        if r.passed:
            passed += 1
        else:
            failed += 1
        all_violations.extend(r.violations)

    # Output
    if args.format == "json":
        output = {
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "violations": [
                {"file": v.file, "line": v.line, "rule": v.rule, "message": v.message, "severity": v.severity}
                for v in all_violations
            ]
        }
        print(json.dumps(output, indent=2))
    else:
        for r in results:
            status = "PASS" if r.passed else "FAIL"
            print(f"  [{status}] {r.file}")
            for v in r.violations:
                print(f"         {v.rule}: {v.message}")

        print(f"\n{passed} passed, {failed} failed, {len(all_violations)} violations")

    # Exit code
    if args.ci and failed > 0:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
