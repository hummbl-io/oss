"""Dependency vulnerability lookups using the standard library.

Modified by HUMMBL on 2026-09-08: report incomplete OSV lookups explicitly.

Reads pyproject.toml / requirements.txt / package.json / go.mod and checks
each dependency against the OSV.dev vulnerability database (free, no auth).

Uses only stdlib: tomllib, json, urllib.request, re, pathlib.

OSV.dev API: https://api.osv.dev/v1/query
  POST {"package": {"name": "foo", "ecosystem": "PyPI"}, "version": "1.0.0"}
  Returns {"vulns": [...]} if vulnerabilities exist, {} if clean.
"""

from __future__ import annotations

import json
import os
import pathlib
import re
import tomllib
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Sequence


class DependencyAuditError(RuntimeError):
    """A dependency lookup could not produce a usable vulnerability response."""


@dataclass
class Dependency:
    """A parsed dependency."""
    name: str
    version: str
    ecosystem: str  # PyPI, npm, Go, etc.
    source_file: str
    line: int = 0


@dataclass
class VulnFinding:
    """A vulnerability finding for a dependency."""
    dep: Dependency
    vuln_id: str  # e.g., GHSA-xxxx, CVE-xxxx, PYSEC-xxxx
    severity: str  # HIGH, MEDIUM, LOW, UNKNOWN
    summary: str
    fixed_versions: str
    url: str

    def __str__(self) -> str:
        return f"[{self.severity}] {self.vuln_id} — {self.dep.name}@{self.dep.version}: {self.summary[:60]}"


# --- Dependency file parsers ---

def parse_pyproject_toml(filepath: str | pathlib.Path) -> list[Dependency]:
    """Parse pyproject.toml for dependencies."""
    filepath = pathlib.Path(filepath)
    try:
        with open(filepath, "rb") as f:
            data = tomllib.load(f)
    except (OSError, tomllib.TOMLDecodeError):
        return []

    deps: list[Dependency] = []
    project = data.get("project", {})
    deps_list = project.get("dependencies", [])

    # Optional dependencies
    optional = project.get("optional-dependencies", {})
    for group in optional.values():
        deps_list.extend(group)

    for dep_str in deps_list:
        parsed = _parse_pep508(dep_str)
        if parsed:
            name, version = parsed
            deps.append(Dependency(
                name=name, version=version, ecosystem="PyPI",
                source_file=str(filepath),
            ))

    return deps


def _parse_pep508(dep_str: str) -> tuple[str, str] | None:
    """Parse a PEP 508 dependency string like 'foo>=1.0,<2.0' or 'bar==1.2.3'.

    Returns (name, version) or None if unresolvable.
    For version ranges, returns the lower bound (best effort).
    """
    dep_str = dep_str.strip()
    # Strip environment markers
    dep_str = dep_str.split(";")[0].strip()
    # Strip extras
    dep_str = re.sub(r"\[.*?\]", "", dep_str)

    # Match: name==version (exact)
    m = re.match(r"^([A-Za-z0-9_.-]+)\s*==\s*([A-Za-z0-9_.+!-]+)", dep_str)
    if m:
        return (m.group(1), m.group(2))

    # Match: name>=version (lower bound)
    m = re.match(r"^([A-Za-z0-9_.-]+)\s*>=\s*([A-Za-z0-9_.+!-]+)", dep_str)
    if m:
        return (m.group(1), m.group(2))

    # Match: name~=version (compatible release)
    m = re.match(r"^([A-Za-z0-9_.-]+)\s*~=\s*([A-Za-z0-9_.+!-]+)", dep_str)
    if m:
        return (m.group(1), m.group(2))

    # Match: name>version
    m = re.match(r"^([A-Za-z0-9_.-]+)\s*>\s*([A-Za-z0-9_.+!-]+)", dep_str)
    if m:
        return (m.group(1), m.group(2))

    # Match: name<=version
    m = re.match(r"^([A-Za-z0-9_.-]+)\s*<=\s*([A-Za-z0-9_.+!-]+)", dep_str)
    if m:
        return (m.group(1), m.group(2))

    # Match: name<version (upper bound only — can't determine installed version)
    m = re.match(r"^([A-Za-z0-9_.-]+)\s*<\s*([A-Za-z0-9_.+!-]+)", dep_str)
    if m:
        return (m.group(1), "")  # No version — will skip OSV query

    # Match: bare name (no version constraint)
    m = re.match(r"^([A-Za-z0-9_.-]+)$", dep_str)
    if m:
        return (m.group(1), "")

    return None


def parse_requirements_txt(filepath: str | pathlib.Path) -> list[Dependency]:
    """Parse requirements.txt for dependencies."""
    filepath = pathlib.Path(filepath)
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except OSError:
        return []

    deps: list[Dependency] = []
    for i, line in enumerate(lines, 1):
        line = line.strip()
        # Skip comments, empty lines, options
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        # Strip inline comments
        line = line.split("#")[0].strip()
        # Strip environment markers
        line = line.split(";")[0].strip()

        parsed = _parse_pep508(line)
        if parsed:
            name, version = parsed
            deps.append(Dependency(
                name=name, version=version, ecosystem="PyPI",
                source_file=str(filepath), line=i,
            ))

    return deps


def parse_package_json(filepath: str | pathlib.Path) -> list[Dependency]:
    """Parse package.json for dependencies."""
    filepath = pathlib.Path(filepath)
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return []

    deps: list[Dependency] = []
    for section in ("dependencies", "devDependencies", "peerDependencies"):
        section_deps = data.get(section, {})
        for name, version_spec in section_deps.items():
            # npm version specs: "1.2.3", "^1.2.3", "~1.2.3", ">=1.0.0", "*"
            version = version_spec.lstrip("^~>=< ")
            if version == "*" or version == "latest":
                version = ""
            deps.append(Dependency(
                name=name, version=version, ecosystem="npm",
                source_file=str(filepath),
            ))

    return deps


def parse_go_mod(filepath: str | pathlib.Path) -> list[Dependency]:
    """Parse go.mod for dependencies."""
    filepath = pathlib.Path(filepath)
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return []

    deps: list[Dependency] = []
    # Match: require block or single-line require
    in_require_block = False
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("require ("):
            in_require_block = True
            continue
        if line == ")":
            in_require_block = False
            continue
        if in_require_block:
            parts = line.split()
            if len(parts) >= 2:
                deps.append(Dependency(
                    name=parts[0], version=parts[1].lstrip("v"),
                    ecosystem="Go", source_file=str(filepath),
                ))
        elif line.startswith("require "):
            parts = line[len("require "):].split()
            if len(parts) >= 2:
                deps.append(Dependency(
                    name=parts[0], version=parts[1].lstrip("v"),
                    ecosystem="Go", source_file=str(filepath),
                ))

    return deps


# --- OSV.dev API client ---

_OSV_URL = "https://api.osv.dev/v1/query"


def query_osv(name: str, version: str, ecosystem: str, timeout: float = 10.0) -> list[dict]:
    """Query OSV.dev for vulnerabilities affecting a package version.

    Args:
        name: Package name.
        version: Package version.
        ecosystem: Package ecosystem (PyPI, npm, Go, etc.).
        timeout: Request timeout in seconds.

    Returns:
        List of vulnerability dicts from a successful OSV response.

    Raises:
        DependencyAuditError: The request failed or the response is malformed.
    """
    if not version:
        return []

    payload = json.dumps({
        "package": {"name": name, "ecosystem": ecosystem},
        "version": version,
    }).encode("utf-8")

    req = urllib.request.Request(
        _OSV_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (OSError, urllib.error.URLError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise DependencyAuditError(
            f"OSV lookup did not complete for {ecosystem}:{name}@{version}"
        ) from exc

    if not isinstance(data, dict):
        raise DependencyAuditError("OSV response must be an object")
    vulns = data.get("vulns", [])
    if not isinstance(vulns, list) or any(not isinstance(v, dict) for v in vulns):
        raise DependencyAuditError("OSV response has an invalid vulnerabilities list")
    return vulns



def _extract_severity(vuln: dict) -> str:
    """Extract severity from an OSV vulnerability entry."""
    # Check severity field (newer format)
    severity_list = vuln.get("severity", [])
    for sev in severity_list:
        score_str = sev.get("score", "")
        # CVSS vector string — extract base severity
        if "CVSS" in score_str:
            # Try to parse CVSS v3 vector for severity
            if "HIGH" in score_str.upper() or "CRITICAL" in score_str.upper():
                return "HIGH"
            if "MEDIUM" in score_str.upper():
                return "MEDIUM"
            if "LOW" in score_str.upper():
                return "LOW"
            # Try CVSS score number
            m = re.search(r"CVSS:3.[01]/AV:[^/]+/AC:[^/]+/PR:[^/]+/UI:[^/]+/S:[^/]+/C:([HML])", score_str)
            if m:
                c = m.group(1)
                return {"H": "HIGH", "M": "MEDIUM", "L": "LOW"}.get(c, "UNKNOWN")

    # Check database_specific for severity (GitHub Advisory format)
    db_specific = vuln.get("database_specific", {})
    if "severity" in db_specific:
        sev = db_specific["severity"].upper()
        if sev in ("CRITICAL", "HIGH"):
            return "HIGH"
        if sev == "MEDIUM":
            return "MEDIUM"
        if sev == "LOW":
            return "LOW"
        return sev

    return "UNKNOWN"


def _extract_fixed_versions(vuln: dict, ecosystem: str) -> str:
    """Extract fixed version info from an OSV vulnerability entry."""
    fixed: list[str] = []
    for affected in vuln.get("affected", []):
        if affected.get("package", {}).get("ecosystem") != ecosystem:
            continue
        for rng in affected.get("ranges", []):
            for event in rng.get("events", []):
                if "fixed" in event:
                    fixed.append(event["fixed"])

    return ", ".join(sorted(set(fixed))) if fixed else "No fix available"


def _extract_url(vuln: dict) -> str:
    """Extract a reference URL from an OSV vulnerability entry."""
    for ref in vuln.get("references", []):
        if ref.get("type") in ("ADVISORY", "WEB", "PACKAGE"):
            return ref.get("url", "")
    return ""


def audit_dependency(dep: Dependency, timeout: float = 10.0) -> list[VulnFinding]:
    """Check a single dependency against OSV.dev.

    Args:
        dep: Dependency to check.
        timeout: API request timeout.

    Returns:
        List of vulnerability findings (empty if clean).
    """
    vulns = query_osv(dep.name, dep.version, dep.ecosystem, timeout)
    findings: list[VulnFinding] = []

    for vuln in vulns:
        findings.append(VulnFinding(
            dep=dep,
            vuln_id=vuln.get("id", "UNKNOWN"),
            severity=_extract_severity(vuln),
            summary=vuln.get("summary", "No summary available")[:120],
            fixed_versions=_extract_fixed_versions(vuln, dep.ecosystem),
            url=_extract_url(vuln),
        ))

    return findings


def find_dep_files(root: str | pathlib.Path) -> list[pathlib.Path]:
    """Find all dependency files in a directory tree."""
    root = pathlib.Path(root)
    target_names = {
        "pyproject.toml", "requirements.txt", "package.json", "go.mod",
    }
    exclude_dirs = {".git", ".venv", "venv", "__pycache__", "node_modules",
                    ".mypy_cache", ".pytest_cache", "dist", "build", ".tox"}

    results: list[pathlib.Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
        for fname in filenames:
            if fname.lower() in target_names:
                results.append(pathlib.Path(dirpath) / fname)

    return results


def audit_directory(
    root: str | pathlib.Path,
    timeout: float = 10.0,
    rate_limit: float = 0.5,
) -> list[VulnFinding]:
    """Audit all dependencies in a directory tree against OSV.dev.

    Args:
        root: Root directory to scan.
        timeout: Per-request timeout for OSV.dev API.
        rate_limit: Seconds to wait between API calls (be nice to OSV.dev).

    Returns:
        List of vulnerability findings.
    """
    import time

    root = pathlib.Path(root)
    dep_files = find_dep_files(root)

    all_deps: list[Dependency] = []
    for fpath in dep_files:
        name = fpath.name.lower()
        if name == "pyproject.toml":
            all_deps.extend(parse_pyproject_toml(fpath))
        elif name == "requirements.txt":
            all_deps.extend(parse_requirements_txt(fpath))
        elif name == "package.json":
            all_deps.extend(parse_package_json(fpath))
        elif name == "go.mod":
            all_deps.extend(parse_go_mod(fpath))

    # Deduplicate by (name, version, ecosystem)
    seen: set[tuple[str, str, str]] = set()
    unique_deps: list[Dependency] = []
    for dep in all_deps:
        key = (dep.name.lower(), dep.version, dep.ecosystem)
        if key not in seen:
            seen.add(key)
            unique_deps.append(dep)

    findings: list[VulnFinding] = []
    for i, dep in enumerate(unique_deps):
        if not dep.version:
            continue  # Can't check without a version
        dep_findings = audit_dependency(dep, timeout)
        findings.extend(dep_findings)
        if rate_limit and i < len(unique_deps) - 1:
            time.sleep(rate_limit)

    return findings


def summarize(findings: list[VulnFinding]) -> dict:
    """Produce a summary of vulnerability findings."""
    by_sev: dict[str, int] = {}
    by_pkg: dict[str, int] = {}
    for f in findings:
        by_sev[f.severity] = by_sev.get(f.severity, 0) + 1
        by_pkg[f.dep.name] = by_pkg.get(f.dep.name, 0) + 1

    return {
        "total": len(findings),
        "by_severity": dict(sorted(by_sev.items(), key=lambda x: -x[1])),
        "by_package": dict(sorted(by_pkg.items(), key=lambda x: -x[1])[:10]),
    }


def format_report(findings: list[VulnFinding], root: str = "") -> str:
    """Format findings as a human-readable report."""
    summary = summarize(findings)
    lines = [
        f"Dependency Audit Report — {root or '.'}",
        "=" * 60,
        f"Total vulnerabilities: {summary['total']}",
    ]
    for sev, count in summary["by_severity"].items():
        lines.append(f"  {sev}: {count}")
    lines.append("")

    if not findings:
        lines.append("No known vulnerabilities found.")
        return "\n".join(lines)

    # Group by package
    by_pkg: dict[str, list[VulnFinding]] = {}
    for f in findings:
        by_pkg.setdefault(f.dep.name, []).append(f)

    for pkg in sorted(by_pkg):
        pkg_findings = by_pkg[pkg]
        versions = sorted(set(f.dep.version for f in pkg_findings))
        lines.append(f"--- {pkg} ({', '.join(versions)}) ---")
        for f in sorted(pkg_findings, key=lambda x: x.vuln_id):
            lines.append(f"  [{f.severity}] {f.vuln_id}")
            lines.append(f"    {f.summary}")
            if f.fixed_versions:
                lines.append(f"    Fixed in: {f.fixed_versions}")
            if f.url:
                lines.append(f"    {f.url}")
            lines.append("")

    return "\n".join(lines)
