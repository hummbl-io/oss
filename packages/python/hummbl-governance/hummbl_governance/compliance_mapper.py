# Copyright 2024-2026 HUMMBL, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

"""Compliance Mapper -- Map governance traces to common security and AI controls.

This module parses append-only governance bus JSONL files and extracts
cryptographic evidence to satisfy specific regulatory controls.

SOC2 Controls Mapped:
- CC6.1: Logical Access Security (mapped to DCT tuples)
- CC7.2: Monitoring and Logging (mapped to governance bus integrity)
- CC6.3: Identity & Authentication (mapped to subject/issuer in DCTs)

GDPR Articles Mapped:
- Article 30: Records of Processing (mapped to DCTX/CONTRACT/ATTEST tuples)
- Article 32: Security of Processing (mapped to signed entries)

OWASP Top 10 for Agentic Applications (ASI01-ASI10) Mapped:
- ASI01: Agent Goal Hijack (mapped to INTENT tuples)
- ASI03: Identity & Privilege Abuse (mapped to DCT tuples)
- ASI04: Supply Chain Vulnerabilities (mapped to signed entries)
- ASI07: Insecure Inter-Agent Communication (mapped to DCTX + signed entries)
- ASI08: Cascading Failures (mapped to CIRCUIT_BREAKER/KILLSWITCH tuples)

NIST AI RMF (GOVERN/MAP/MEASURE/MANAGE) Mapped:
- GOVERN 1.1: AI risk management policies (INTENT tuples prove stated objectives)
- GOVERN 1.7: Processes for risk identification (CIRCUIT_BREAKER/KILLSWITCH events)
- MAP 1.1: Organizational context (CONTRACT/DCTX tuples)
- MAP 2.2: Scientific basis for risk assessment (ATTEST/EVIDENCE tuples)
- MEASURE 2.5: Trustworthiness evaluations (signed governance entries)
- MEASURE 2.8: Impact metrics logged (COST_GOVERNOR events)
- MANAGE 1.3: Response plans executed (KILLSWITCH events)
- MANAGE 2.4: Risk treatment applied (CIRCUIT_BREAKER state transitions)

EU AI Act Articles Mapped (High-Risk AI per Annex III):
- Art.9: Risk management system (KILLSWITCH + CIRCUIT_BREAKER evidence)
- Art.10: Data and data governance (ATTEST/EVIDENCE tuples)
- Art.12: Record-keeping and logging (all signed governance entries)
- Art.13: Transparency and information provision (INTENT tuples)
- Art.14: Human oversight (KILLSWITCH tuples with human-initiated state)
- Art.17: Quality management system (DCTX delegation chain integrity)

Standard library only.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from hummbl_governance.compliance_frameworks import (
    FrameworkSpec,
    MappingRule,
    get_framework,
    list_frameworks,
)

logger = logging.getLogger(__name__)


@dataclass
class ComplianceReport:
    """A structured compliance report containing evidence for multiple controls."""

    generated_at: str
    framework: str
    controls: dict[str, list[dict[str, Any]]] = field(default_factory=dict)

    def to_json(self) -> str:
        """Serialize report to JSON."""
        return json.dumps(
            {
                "generated_at": self.generated_at,
                "framework": self.framework,
                "controls": self.controls,
            },
            indent=2,
            sort_keys=True,
        )


class ComplianceMapper:
    """Maps governance entries to regulatory controls."""

    def __init__(self, governance_dir: Path | str | None = None):
        if governance_dir is None:
            self.governance_dir = Path("governance")
        else:
            self.governance_dir = Path(governance_dir)

    def _parse_line(self, line: str) -> dict[str, Any] | None:
        """Safely parse a single JSONL line."""
        try:
            return json.loads(line.strip())
        except json.JSONDecodeError:
            logger.warning("Failed to parse governance line: %s", line[:100])
            return None

    def _collect_files(self, days: int) -> list[Path]:
        """Collect governance JSONL files within the date window."""
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=days)

        files = sorted(self.governance_dir.glob("governance-*.jsonl"), reverse=True)
        result = []

        for file_path in files:
            try:
                file_date_str = file_path.stem.split("governance-")[-1]
                file_date = datetime.strptime(file_date_str, "%Y-%m-%d").replace(
                    tzinfo=timezone.utc
                )
                if file_date < cutoff.replace(hour=0, minute=0, second=0, microsecond=0):
                    continue
            except (ValueError, IndexError):
                continue
            result.append(file_path)

        return result

    def _read_entries(self, files: list[Path]) -> list[dict[str, Any]]:
        """Read and parse all entries from governance files."""
        entries: list[dict[str, Any]] = []
        for file_path in files:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    entry = self._parse_line(line)
                    if entry:
                        entries.append(entry)
        return entries

    @staticmethod
    def _base_evidence(entry: dict[str, Any]) -> dict[str, Any]:
        """Extract common evidence fields from an entry."""
        return {
            "entry_id": entry.get("entry_id"),
            "timestamp": entry.get("timestamp"),
            "task_id": entry.get("task_id"),
            "intent_id": entry.get("intent_id"),
            "signature": entry.get("signature"),
        }

    # ------------------------------------------------------------------
    # Generic engine (registry-driven)
    # ------------------------------------------------------------------

    @staticmethod
    def _rule_matches(
        rule: MappingRule,
        entry: dict[str, Any],
        tuple_type: str | None,
        tuple_data: dict[str, Any],
    ) -> bool:
        """Return True when *rule* matches *entry*."""
        if rule.tuple_types and tuple_type not in rule.tuple_types:
            return False
        if rule.require_signed and not entry.get("signature"):
            return False
        if rule.states is not None and tuple_data.get("state") not in rule.states:
            return False
        return True

    @staticmethod
    def _build_evidence(
        rule: MappingRule,
        base: dict[str, Any],
        entry: dict[str, Any],
        tuple_type: str | None,
        tuple_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Build an evidence dict for a matched rule."""
        ev = base.copy()
        ev["tuple_type"] = tuple_type
        for ev_key, td_key in rule.extract:
            ev[ev_key] = tuple_data.get(td_key)
        for ev_key, td_keys in rule.extract_fallback:
            for k in td_keys:
                val = tuple_data.get(k)
                if val:
                    ev[ev_key] = val
                    break
        if rule.derive is not None:
            ev.update(rule.derive(entry, tuple_data))
        return ev

    def generate_report(
        self,
        framework_id: str,
        days: int | None = None,
    ) -> ComplianceReport:
        """Generate a compliance report for any registered framework.

        This is the generic, registry-driven generator.  All framework-specific
        ``generate_*_report`` methods delegate here.  Adding a new framework
        requires only a ``register_framework`` call in
        ``compliance_frameworks`` -- no changes to this method or the CLI.
        """
        spec: FrameworkSpec = get_framework(framework_id)
        if days is None:
            days = spec.default_days

        now = datetime.now(timezone.utc)
        report = ComplianceReport(
            generated_at=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            framework=spec.name,
        )

        for control in spec.controls:
            report.controls[control.id] = []

        files = self._collect_files(days)
        entries = self._read_entries(files)

        for entry in entries:
            base = self._base_evidence(entry)
            tuple_type = entry.get("tuple_type")
            tuple_data = entry.get("tuple_data", {})
            for control in spec.controls:
                for rule in control.rules:
                    if not self._rule_matches(rule, entry, tuple_type, tuple_data):
                        continue
                    report.controls[control.id].append(
                        self._build_evidence(rule, base, entry, tuple_type, tuple_data)
                    )

        return report

    # ------------------------------------------------------------------
    # Backward-compatible framework wrappers
    # ------------------------------------------------------------------
    # Each delegates to generate_report(<id>, days).  Preserved so existing
    # callers and tests continue to work without changes.

    def generate_soc2_report(self, days: int = 7) -> ComplianceReport:
        """Generate a SOC2 compliance report from recent governance traces."""
        return self.generate_report("soc2", days)

    def generate_gdpr_report(self, days: int = 30) -> ComplianceReport:
        """Generate a GDPR compliance report from recent governance traces.

        Maps governance entries to Articles 5, 6, 25, 28, 30, and 32.
        These are the articles with direct technical evidence addressable
        by code-level governance primitives.
        """
        return self.generate_report("gdpr", days)

    def generate_owasp_report(self, days: int = 7) -> ComplianceReport:
        """Generate an OWASP Agentic Top 10 compliance report from governance traces.

        Maps governance entries to OWASP ASI01-ASI10 controls. Controls that
        lack runtime governance traces (ASI02, ASI05, ASI06, ASI09, ASI10) are
        initialized empty -- they are evidenced by code audit, not runtime logs.
        """
        return self.generate_report("owasp", days)

    def generate_nist_rmf_report(self, days: int = 30) -> ComplianceReport:
        """Generate a NIST AI Risk Management Framework compliance report.

        Maps governance traces to the four NIST AI RMF core functions:
        GOVERN, MAP, MEASURE, and MANAGE. Controls with no runtime evidence
        (e.g. policy documents) are initialised empty -- they are satisfied by
        artefact review, not runtime logs.

        Reference: NIST AI 100-1 (2023), AI RMF Playbook.
        """
        return self.generate_report("nist-rmf", days)

    def generate_eu_ai_act_report(self, days: int = 30) -> ComplianceReport:
        """Generate an EU AI Act compliance report (High-Risk AI, Annex III).

        Maps governance traces to Articles 9, 10, 11, 12, 13, 14, 15, 16, 17, and 19.
        These are the core operational obligations for high-risk AI systems.

        Controls with no runtime evidence are initialised empty; they are
        satisfied by design documentation and human review artefacts.

        Reference: Regulation (EU) 2024/1689 (AI Act), in force 2024-08-01.
        """
        return self.generate_report("eu-ai-act", days)

    def generate_iso27001_report(self, days: int = 30) -> ComplianceReport:
        """Generate an ISO/IEC 27001:2022 compliance report from governance traces.

        Maps governance entries to Annex A organizational controls (A.5-A.9, A.12).
        These are the control families most directly addressable by code-level
        governance primitives for AI agent orchestration.

        Controls with no runtime evidence are initialised empty; they are
        satisfied by organizational process documentation outside the library.

        Reference: ISO/IEC 27001:2022, Annex A.
        """
        return self.generate_report("iso27001", days)

    def generate_iso42001_report(self, days: int = 30) -> ComplianceReport:
        """Generate an ISO/IEC 42001:2023 compliance report from governance traces.

        Maps governance entries to Annex A reference controls (A.2-A.10).
        These are the control objectives most directly addressable by code-level
        governance primitives for AI agent orchestration.

        Controls with no runtime evidence are initialised empty; they are
        satisfied by organizational process documentation outside the library
        (AIMS leadership, policy authorship, HR, etc.).

        Reference: ISO/IEC 42001:2023, Annex A (~38 controls across 9
        control objectives).
        """
        return self.generate_report("iso42001", days)

    def generate_nist_csf_report(self, days: int = 30) -> ComplianceReport:
        """Generate a NIST Cybersecurity Framework 2.0 compliance report.

        Maps governance traces to the six CSF Functions: GOVERN, IDENTIFY,
        PROTECT, DETECT, RESPOND, RECOVER. Each function is mapped to the
        governance primitives that produce technical evidence for that
        function's outcomes.

        Reference: NIST CSF 2.0 (2024).
        """
        return self.generate_report("nist-csf", days)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point.

    Framework choices are auto-discovered from the registry in
    ``compliance_frameworks``.  Adding a new framework requires only a
    ``register_framework`` call -- no CLI changes needed here.
    """
    parser = argparse.ArgumentParser(
        description="Map governance traces to compliance controls."
    )
    parser.add_argument(
        "--days", type=int, default=7, help="Number of days to include in report"
    )
    parser.add_argument(
        "--framework",
        choices=list_frameworks(),
        default="soc2",
        help="Compliance framework",
    )
    parser.add_argument(
        "--dir", type=str, default="governance", help="Governance directory"
    )
    parser.add_argument("--output", type=str, help="Output JSON file path")
    parser.add_argument(
        "--validate", type=str, metavar="MATRIX.md",
        help="Validate a coverage matrix .md file and report pass/fail per cell",
    )
    parser.add_argument(
        "--repo-root", type=str, default=".",
        help="Repository root for resolving relative evidence paths (default: CWD)",
    )
    parser.add_argument(
        "--validate-json", action="store_true",
        help="Output validation results as JSON instead of terminal table",
    )

    args = parser.parse_args(argv)

    if args.validate:
        return _validate_matrix(
            args.validate,
            repo_root=args.repo_root,
            json_output=args.validate_json,
        )

    mapper = ComplianceMapper(governance_dir=Path(args.dir))
    report = mapper.generate_report(args.framework, days=args.days)

    json_output = report.to_json()

    if args.output:
        Path(args.output).write_text(json_output, encoding="utf-8")
        print(f"Report written to {args.output}")
    else:
        print(json_output)

    return 0


# Module alias map: legacy reference paths (hummbl-governance services/ layout)
# mapped to canonical paths in the standalone hummbl-governance package.
# Origin: matrices were authored against hummbl-governance layout; primitives
# extracted to standalone package use different module names.
_MODULE_ALIASES: dict[str, str] = {
    # kill switch
    "services/kill_switch_core.py": "hummbl_governance/kill_switch.py",
    "services/kill_switch.py": "hummbl_governance/kill_switch.py",
    "kill_switch_core.py": "hummbl_governance/kill_switch.py",
    # circuit breaker
    "services/circuit_breaker.py": "hummbl_governance/circuit_breaker.py",
    # delegation
    "services/delegation_token.py": "hummbl_governance/delegation.py",
    "services/delegation_context.py": "hummbl_governance/delegation.py",
    "delegation_context.py": "hummbl_governance/delegation.py",
    "delegation_token.py": "hummbl_governance/delegation.py",
    # governance bus
    "services/governance_bus.py": "hummbl_governance/coordination_bus.py",
    "governance_bus.py": "hummbl_governance/coordination_bus.py",
    # cognition ledger
    "cognition/ledger_writer.py": "hummbl_governance/audit_log.py",
    # external state surfaces (referenced for evidence; not files in this repo)
    "_state/coordination/messages.tsv": "EXTERNAL:hummbl-governance/_state/coordination/messages.tsv",
    "_state/cognition/ledger.jsonl": "EXTERNAL:hummbl-governance/_state/cognition/ledger.jsonl",
    # services that exist as Tier-2 admission packets (NOT shipped code)
    "services/c2pa_mcp": "TIER2_ADMITTED:services/c2pa_mcp (Tier-2 packet, not shipped)",
    "services/incident_reporting": "TIER2_ADMITTED:services/incident_reporting (Tier-2 packet, not shipped)",
}


# Coverage state glyphs (from docs/coverage/README.md legend)
_STATE_FULFILLED = "\u2705"  # green check
_STATE_PARTIAL = "\U0001f7e1"  # yellow circle
_STATE_BOUNDARY = "\u26aa"  # white circle
_STATE_OUT_OF_SCOPE = "\u26d4"  # no-entry
_ALL_STATES = (_STATE_FULFILLED, _STATE_PARTIAL, _STATE_BOUNDARY, _STATE_OUT_OF_SCOPE)


def _parse_matrix_rows(text: str) -> list[dict]:
    """Parse markdown coverage-matrix data rows.

    Returns a list of dicts: {state, control_id, requirement, coverage, evidence, line_no}.
    Skips legend tables, summary/count tables, and separator rows.
    Only matrix data rows are yielded \u2014 those containing one of the
    four state glyphs in any cell.
    """
    rows: list[dict] = []
    lines = text.split("\n")
    in_legend = False
    in_summary = False
    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped.startswith("|"):
            in_legend = False
            in_summary = False
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if not cells:
            continue
        next_line = lines[idx].strip() if idx < len(lines) else ""
        next_cells = [c.strip() for c in next_line.strip("|").split("|")]
        next_is_separator = next_line.startswith("|") and all(
            set(c) <= set("-: ") for c in next_cells if c
        )
        header_join = " ".join(cells).lower()
        if next_is_separator and "glyph" in header_join and "state" in header_join:
            in_legend = True
            continue
        lower_cells = [c.lower() for c in cells]
        first_cell = lower_cells[0] if lower_cells else ""
        has_state_count_columns = any(g in c for c in cells for g in _ALL_STATES)
        lacks_evidence_column = "evidence" not in lower_cells
        summary_first_cells = {"annex", "chapter", "section", "function", "component", "tsc"}
        if next_is_separator and (
            has_state_count_columns
            or "chapter" in header_join
            or ("section" in header_join and "title" in header_join)
            or (first_cell in summary_first_cells and lacks_evidence_column)
        ):
            in_summary = True
            continue
        # Separator row
        if all(set(c) <= set("-: ") for c in cells if c):
            continue
        if in_legend or in_summary:
            continue
        if len(cells) < 3:
            continue
        state = None
        coverage_idx = None
        for i, c in enumerate(cells):
            for g in _ALL_STATES:
                if g in c:
                    state = g
                    coverage_idx = i
                    break
            if state:
                break
        if state is None:
            continue
        requirement = cells[1] if len(cells) > 1 else ""
        coverage = cells[coverage_idx] if coverage_idx is not None else ""
        evidence = (
            cells[coverage_idx + 1]
            if coverage_idx is not None and coverage_idx + 1 < len(cells)
            else ""
        )
        rows.append({
            "state": state,
            "control_id": cells[0],
            "requirement": requirement,
            "coverage": coverage,
            "evidence": evidence,
            "line_no": idx,
        })
    return rows


def _extract_refs(cell: str) -> list[str]:
    """Extract backtick-quoted file/path references from a single cell.

    Skips generic backtick text (tuple-type identifiers like `INTENT`, `DCT`,
    inline code without path semantics). A token qualifies if it contains
    '/' or ends in a known file extension.
    """
    refs: list[str] = []
    for match in re.finditer(r"`([^`\n]+)`", cell):
        token = match.group(1).strip()
        if not token or len(token) > 200:
            continue
        if token.startswith("http"):
            continue
        has_slash = "/" in token
        has_ext = any(
            token.endswith(ext)
            for ext in (".py", ".md", ".ts", ".tsv", ".jsonl", ".json", ".yml", ".yaml", ".toml")
        )
        if has_slash or has_ext:
            refs.append(token)
    return refs


def _validate_matrix(matrix_path: str, *, repo_root: str = ".", json_output: bool = False) -> int:
    """Validate a coverage matrix .md file (row-aware).

    For each \u2705 Fulfilled row, extract evidence-cell file references and
    resolve them against the package layout (with legacy alias support).
    Reports per-row pass/fail and aggregate coverage %.

    A row is "validated" when ALL of its evidence refs resolve to an
    existing artifact OR to a documented Tier-2/EXTERNAL marker.

    Returns:
      0 \u2014 all \u2705 rows have validated evidence
      1 \u2014 some \u2705 rows have unresolved evidence (hardening needed)
      2 \u2014 matrix file not found
    """
    path = Path(matrix_path)
    if not path.exists():
        print(f"ERROR: Matrix file not found: {matrix_path}", file=sys.stderr)
        return 2

    root = Path(repo_root).resolve()
    text = path.read_text(encoding="utf-8")
    rows = _parse_matrix_rows(text)

    fulfilled_rows = [r for r in rows if r["state"] == _STATE_FULFILLED]
    partial_rows = [r for r in rows if r["state"] == _STATE_PARTIAL]
    boundary_rows = [r for r in rows if r["state"] == _STATE_BOUNDARY]
    oos_rows = [r for r in rows if r["state"] == _STATE_OUT_OF_SCOPE]

    row_results: list[dict] = []
    row_passed = 0
    row_failed = 0
    rows_without_refs = 0

    for row in fulfilled_rows:
        refs = _extract_refs(row["evidence"]) + _extract_refs(row["coverage"])
        seen: set[str] = set()
        refs = [r for r in refs if not (r in seen or seen.add(r))]
        if not refs:
            rows_without_refs += 1
            row_results.append({
                "control_id": row["control_id"],
                "line_no": row["line_no"],
                "refs": [],
                "status": "fail",
                "detail": "no evidence references found in row",
            })
            row_failed += 1
            continue
        resolutions = [_resolve_evidence(r, root) for r in refs]
        all_pass = all(res["status"] in ("pass", "tier2", "external") for res in resolutions)
        row_results.append({
            "control_id": row["control_id"],
            "line_no": row["line_no"],
            "refs": [{"ref": r, **res} for r, res in zip(refs, resolutions)],
            "status": "pass" if all_pass else "fail",
            "detail": (
                "all refs resolve"
                if all_pass
                else f"{sum(1 for r in resolutions if r['status'] == 'fail')} of {len(resolutions)} refs unresolved"
            ),
        })
        if all_pass:
            row_passed += 1
        else:
            row_failed += 1

    summary = {
        "matrix": _display_path(path, root),
        "totals": {
            "fulfilled": len(fulfilled_rows),
            "partial": len(partial_rows),
            "boundary": len(boundary_rows),
            "out_of_scope": len(oos_rows),
        },
        "fulfilled_validation": {
            "rows_passed": row_passed,
            "rows_failed": row_failed,
            "rows_without_refs": rows_without_refs,
            "coverage_pct": (
                round(100.0 * row_passed / len(fulfilled_rows), 1)
                if fulfilled_rows
                else 0.0
            ),
        },
        "rows": row_results,
    }

    if json_output:
        import json as _json
        print(_json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        print(f"Matrix: {path.name}")
        # ASCII-safe terminal output for Windows cp1252 consoles.
        # JSON output above preserves the full unicode state glyphs.
        ful_n = len(fulfilled_rows)
        par_n = len(partial_rows)
        bnd_n = len(boundary_rows)
        oos_n = len(oos_rows)
        pct = summary["fulfilled_validation"]["coverage_pct"]
        print(f"  Rows: FUL {ful_n} | PAR {par_n} | BND {bnd_n} | OOS {oos_n}")
        print(f"  FUL rows validated: {row_passed}/{ful_n} ({pct}%)")
        if rows_without_refs:
            print(f"  WARN: {rows_without_refs} FUL row(s) have NO evidence refs (hardening gap)")
        for r in row_results:
            if r["status"] == "fail":
                print(f"  [FAIL] line {r['line_no']}: {r['control_id']} - {r['detail']}")
                for sub in r["refs"]:
                    if isinstance(sub, dict) and sub.get("status") == "fail":
                        print(f"           -> {sub['ref']} (not found)")

    return 0 if row_failed == 0 else 1


def _resolve_evidence(ref: str, repo_root: Path) -> dict:
    """Resolve an evidence reference to a file path and check existence.

    Resolution order:
    1. Module alias map (legacy path -> canonical, plus TIER2/EXTERNAL markers)
    2. Direct: repo_root / ref
    3. Package: repo_root / hummbl_governance / ref
    4. Tests: repo_root / tests / ref
    5. Workflows: repo_root / .github / ref
    6. Docs: repo_root / docs / ref
    7. Failing those, .py / .md suffix tries
    """
    root = repo_root

    alias = _MODULE_ALIASES.get(ref)
    if alias is not None:
        if alias.startswith("TIER2_ADMITTED:"):
            return {
                "path": alias,
                "status": "tier2",
                "detail": "Tier-2 admitted dependency, not in shipped code",
            }
        if alias.startswith("EXTERNAL:"):
            return {"path": alias, "status": "external", "detail": "external surface (other repo)"}
        candidate = root / alias
        if candidate.exists():
            return {
                "path": _display_path(candidate, root),
                "status": "pass",
                "detail": f"resolved via alias -> {alias}",
            }
        return {
            "path": _display_path(candidate, root),
            "status": "fail",
            "detail": f"alias target missing: {alias}",
        }

    candidates = [
        root / ref,
        root / "hummbl_governance" / ref,
        root / "tests" / ref,
        root / ".github" / ref,
        root / "docs" / ref,
    ]
    for candidate in candidates:
        if candidate.exists():
            return {"path": _display_path(candidate, root), "status": "pass", "detail": "file exists"}

    if not ref.endswith(
        (".py", ".md", ".ts", ".tsv", ".jsonl", ".json", ".yml", ".yaml", ".toml")
    ):
        for candidate in candidates:
            for ext in (".py", ".md"):
                ext_candidate = (
                    candidate.with_suffix(ext)
                    if candidate.suffix
                    else Path(str(candidate) + ext)
                )
                if ext_candidate.exists():
                    return {
                        "path": _display_path(ext_candidate, root),
                        "status": "pass",
                        "detail": f"file exists ({ext})",
                    }

    return {"path": _display_path(candidates[0], root), "status": "fail", "detail": "file not found"}


def _display_path(path: Path, repo_root: Path) -> str:
    """Return a deterministic repo-relative path for validator JSON output."""
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


if __name__ == "__main__":
    sys.exit(main())
