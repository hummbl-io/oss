"""Read-only release gate for ARCANA artifacts.

The gate composes the first executable sibling workflow:

article.md -> PAIDEIA score -> LINGUA check -> NOMOS note -> EVIDENCE summary
-> RELEASE decision.

It never publishes or mutates the source artifact.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
for path in (ROOT, SCRIPTS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import ecosystem_contracts as ec  # noqa: E402
import score_paideia as paideia  # noqa: E402

SCHEMA_VERSION = "release-gate-v0.1"
RELEASE_VERSION = ec.sibling_contract_spec("RELEASE")["version"]


def now_utc_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def artifact_receipt(path: Path, text: str) -> dict[str, object]:
    data = text.encode("utf-8")
    return {
        "path": str(path),
        "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data),
        "lines": text.count("\n") + (0 if text.endswith("\n") else 1),
    }


def lingua_receipt(text: str) -> dict[str, object]:
    warnings: list[str] = []
    if re.search(r"\bTODO\b|\bFIXME\b", text):
        warnings.append("editorial-placeholder")
    if re.search(r"\bcitation needed\b|\[citation needed\]", text, re.IGNORECASE):
        warnings.append("citation-needed-marker")
    if "http://" in text:
        warnings.append("insecure-link")
    markdown_links = len(re.findall(r"\[[^\]]+\]\([^)]+\)", text))
    return {
        "module": "LINGUA",
        "version": ec.sibling_contract_spec("LINGUA")["version"],
        "status": "hold" if warnings else "pass",
        "markdown_links": markdown_links,
        "warnings": warnings,
    }


def nomos_receipt(*, external_target: bool) -> dict[str, object]:
    frameworks = {
        "nist_ai_rmf": "mapping-required-before-regulated-publication",
        "iso_42001": "mapping-required-before-management-system-claim",
        "eu_ai_act": "mapping-required-before-high-risk-system-claim",
    }
    status = "hold" if external_target else "pass"
    return {
        "module": "NOMOS",
        "version": ec.sibling_contract_spec("NOMOS")["version"],
        "status": status,
        "external_target": external_target,
        "frameworks": frameworks,
        "note": (
            "External publication target requires explicit standards mapping."
            if external_target else
            "Internal read-only gate; standards mapping noted but not required."
        ),
    }


def evidence_receipt(
    *,
    artifact: dict[str, object],
    paideia_score: dict[str, object],
    lingua: dict[str, object],
    nomos: dict[str, object],
) -> dict[str, object]:
    return {
        "module": "EVIDENCE",
        "version": ec.sibling_contract_spec("EVIDENCE")["version"],
        "status": "recorded",
        "artifact_sha256": artifact["sha256"],
        "paideia_signature": paideia_score["signature"],
        "lingua_status": lingua["status"],
        "nomos_status": nomos["status"],
        "warning_count": len(lingua["warnings"]),
    }


def release_decision(
    *,
    text: str,
    lingua: dict[str, object],
    nomos: dict[str, object],
) -> dict[str, object]:
    reasons: list[str] = []
    decision = "pass"
    if not text.strip():
        return {
            "module": "RELEASE",
            "version": RELEASE_VERSION,
            "decision": "blocked",
            "read_only": True,
            "reasons": ["empty-artifact"],
        }
    if lingua["status"] != "pass":
        decision = "hold"
        reasons.extend(f"lingua:{item}" for item in lingua["warnings"])
    if nomos["status"] != "pass":
        decision = "hold"
        reasons.append("nomos:external-target-requires-standards-mapping")
    return {
        "module": "RELEASE",
        "version": RELEASE_VERSION,
        "decision": decision,
        "read_only": True,
        "reasons": reasons,
    }


def build_release_gate_bundle(
    article_path: Path,
    *,
    external_target: bool = False,
    instructional_intent: bool = True,
) -> dict[str, object]:
    if not article_path.exists():
        raise FileNotFoundError(article_path)
    text = article_path.read_text(encoding="utf-8")
    artifact = artifact_receipt(article_path, text)
    paideia_score = paideia.score_content(
        text,
        instructional_intent=instructional_intent,
        use_llm=False,
    )
    lingua = lingua_receipt(text)
    nomos = nomos_receipt(external_target=external_target)
    evidence = evidence_receipt(
        artifact=artifact,
        paideia_score=paideia_score,
        lingua=lingua,
        nomos=nomos,
    )
    release = release_decision(text=text, lingua=lingua, nomos=nomos)
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": now_utc_iso(),
        "artifact": artifact,
        "receipts": {
            "paideia": paideia_score,
            "lingua": lingua,
            "nomos": nomos,
            "evidence": evidence,
        },
        "release": release,
    }


def render_summary(bundle: dict[str, object]) -> str:
    artifact = bundle["artifact"]
    receipts = bundle["receipts"]
    release = bundle["release"]
    lines = [
        "# ARCANA Release Gate Summary",
        "",
        f"- Artifact: `{artifact['path']}`",
        f"- SHA256: `{artifact['sha256']}`",
        f"- Decision: `{release['decision']}`",
        f"- Read-only: `{str(release['read_only']).lower()}`",
        f"- PAIDEIA: `{receipts['paideia']['signature']}`",
        f"- LINGUA: `{receipts['lingua']['status']}`",
        f"- NOMOS: `{receipts['nomos']['status']}`",
        f"- EVIDENCE: `{receipts['evidence']['status']}`",
    ]
    reasons = release["reasons"]
    if reasons:
        lines.extend(["", "## Reasons", ""])
        lines.extend(f"- {reason}" for reason in reasons)
    return "\n".join(lines).strip() + "\n"


def write_outputs(bundle: dict[str, object], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "release_gate_receipt.json"
    md_path = output_dir / "release_gate_summary.md"
    json_path.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n",
                         encoding="utf-8")
    md_path.write_text(render_summary(bundle), encoding="utf-8")
    return json_path, md_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--article", required=True,
                        help="article markdown/text artifact to evaluate")
    parser.add_argument("--output-dir", default=None,
                        help="write JSON and Markdown receipts to this directory")
    parser.add_argument("--external-target", action="store_true",
                        help="treat the artifact as intended for external publication")
    parser.add_argument("--instructional-intent", type=lambda s: s.lower() != "false",
                        default=True)
    args = parser.parse_args(argv)

    bundle = build_release_gate_bundle(
        Path(args.article),
        external_target=args.external_target,
        instructional_intent=args.instructional_intent,
    )
    if args.output_dir:
        json_path, md_path = write_outputs(bundle, Path(args.output_dir))
        print(f"wrote {json_path}")
        print(f"wrote {md_path}")
    else:
        print(json.dumps(bundle, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
