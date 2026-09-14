"""Validate public position-document structure, not source truth or adoption.

Python 3.10+, standard library only. No network requests or artifact mutations.
The metadata scan is a targeted guard, not a comprehensive disclosure review.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

DEFAULT_PACKAGE = Path(__file__).resolve().parents[1] / "docs/positions/ai-2026-09-12"
POSITIONS = {f"POS-{n:02}" for n in range(1, 11)}
TOPICS = {
    "RSI",
    "AGI",
    "ASI",
    "open_source",
    "open_weights",
    "frontier_labs",
    "IPO",
    "profitability",
    "receipts",
}
DISPOSITIONS = {
    "supported_with_scope",
    "bounded_conclusion",
    "attributed",
    "proposed_policy",
    "observed",
    "untested",
}
# Match metadata assignments and path syntax, not ordinary technical discussion.
INTERNAL_PATTERNS = (
    r'(?im)(?:^\s*|[,{]\s*)(?:"?(?:host(?:name)?|operator_name|machine_name|session_id|bus_path|receipt_path|pinned_receipt|supplemental_receipt)"?)\s*[:=]',
    r"(?<![\w/])/(?:home|Users)/[^\s/]+/",
    r"(?i)[a-z]:\\(?:Users|PROJECTS)\\",
    r"(?i)https?://[^/\s]+\.ts\.net\b",
    r"(?i)\bid=[a-z0-9]{20,26}\b",
    r"-----BEGIN (?:OPENSSH |RSA |EC )?PRIVATE KEY-----",
)


def text_value(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def https_url(value: object) -> bool:
    if not isinstance(value, str) or any(c.isspace() for c in value):
        return False
    try:
        parsed = urlsplit(value)
        return (
            parsed.scheme == "https"
            and bool(parsed.hostname)
            and not parsed.username
            and not parsed.password
        )
    except ValueError:
        return False


def markdown_body(content: str) -> str:
    return re.sub(r"`[^`\n]*`", "", re.sub(r"```.*?```", "", content, flags=re.DOTALL))


def anchors(content: str) -> set[str]:
    counts: dict[str, int] = {}
    result: set[str] = set()
    for heading in re.findall(
        r"^#{1,6}\s+(.+?)\s*#*\s*$", markdown_body(content), re.MULTILINE
    ):
        slug = re.sub(r"[^\w\s-]", "", heading.lower()).replace(" ", "-")
        n = counts.get(slug, 0)
        result.add(slug if n == 0 else f"{slug}-{n}")
        counts[slug] = n + 1
    return result


def validate(package: Path) -> list[str]:
    """Return defects in the declared public document format."""
    package = package.resolve()
    errors: list[str] = []

    def read(name: str):
        try:
            return json.loads((package / name).read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            errors.append(f"JSON {name}: {exc}")
            return None

    def date(value: object, label: str) -> None:
        try:
            if not isinstance(value, str) or not re.fullmatch(
                r"\d{4}-\d{2}-\d{2}", value
            ):
                raise ValueError("expected ISO date")
            if dt.date.fromisoformat(value) > dt.datetime.now(dt.timezone.utc).date():
                raise ValueError("future date")
        except (TypeError, ValueError):
            errors.append(f"DATE {label}: invalid or future date")

    def records(value: object, label: str) -> list[dict]:
        if not isinstance(value, list) or not value:
            errors.append(f"SHAPE {label}: nonempty object list required")
            return []
        valid = [v for v in value if isinstance(v, dict)]
        if len(valid) != len(value):
            errors.append(f"SHAPE {label}: non-object record")
        return valid

    def identity(record: dict, seen: set, label: str) -> str | None:
        ident = record.get("id")
        if not text_value(ident) or ident in seen:
            errors.append(f"IDENTITY {label}: missing or duplicate ID")
            return None
        seen.add(ident)
        return ident

    source_ids: set[str] = set()
    for source in records(read("sources.json"), "sources"):
        sid = identity(source, source_ids, "source")
        for field in ("title", "kind", "observation", "limitation"):
            if not text_value(source.get(field)):
                errors.append(f"SOURCE {sid}: missing {field}")
        urls = source.get("urls")
        if (
            not isinstance(urls, list)
            or not urls
            or any(not https_url(u) for u in urls)
        ):
            errors.append(f"URL {sid}: nonempty public HTTPS citations required")
        date(source.get("accessed_on"), str(sid))

    ledger = read("claims.json")
    if not isinstance(ledger, dict):
        errors.append("SHAPE claims: object required")
        ledger = {}
    if (
        ledger.get("schema_version") != "1.0"
        or ledger.get("status") != "proposed_canonical_baseline"
    ):
        errors.append("STATUS expected schema 1.0 proposed canonical baseline")
    ids: set[str] = set()
    topics: set[str] = set()
    positions: set[str] = set()
    for claim in records(ledger.get("claims"), "claims"):
        cid = identity(claim, ids, "claim")
        for field in ("claim", "evidence_class", "limitation", "revision_trigger"):
            if not text_value(claim.get(field)):
                errors.append(f"CLAIM {cid}: missing {field}")
        disposition = claim.get("disposition")
        if not isinstance(disposition, str) or disposition not in DISPOSITIONS:
            errors.append(f"CLAIM {cid}: invalid disposition")
        position = claim.get("position_id")
        if not isinstance(position, str) or position not in POSITIONS:
            errors.append(f"POSITION {cid}: unknown position")
        else:
            positions.add(position)
        tags = claim.get("topics")
        if (
            not isinstance(tags, list)
            or not tags
            or any(not text_value(t) for t in tags)
        ):
            errors.append(f"TOPICS {cid}: nonempty string list required")
        else:
            topics.update(tags)
        refs = claim.get("source_ids")
        if (
            not isinstance(refs, list)
            or not refs
            or any(not isinstance(r, str) for r in refs)
        ):
            errors.append(f"REFERENCE {cid}: nonempty string list required")
        elif len(refs) != len(set(refs)) or any(r not in source_ids for r in refs):
            errors.append(f"REFERENCE {cid}: duplicate or unresolved source")
        date(claim.get("as_of"), str(cid))
    if positions != POSITIONS:
        errors.append("COVERAGE all ten positions require claims")
    if not TOPICS <= topics:
        errors.append(f"COVERAGE missing topics: {sorted(TOPICS - topics)}")

    documents: dict[Path, str] = {}
    for path in package.rglob("*"):
        if not path.is_file() or path.suffix not in {".md", ".json"}:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            errors.append(f"TEXT {path.name}: unreadable text")
            continue
        if any(re.search(pattern, content) for pattern in INTERNAL_PATTERNS):
            errors.append(
                f"PUBLIC {path.name}: potential internal metadata requires removal or review"
            )
        if path.suffix == ".md":
            documents[path] = content
    headings = re.findall(
        r"^## (POS-\d+)\b", documents.get(package / "README.md", ""), re.MULTILINE
    )
    if len(headings) != 10 or set(headings) != POSITIONS:
        errors.append(
            "POSITIONS README must contain each of POS-01 through POS-10 once"
        )
    for path, content in documents.items():
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", markdown_body(content)):
            try:
                parsed = urlsplit(target)
            except ValueError:
                errors.append(f"LINK {path.name}: malformed target")
                continue
            if parsed.scheme:
                if parsed.scheme not in {"https", "http", "mailto"}:
                    errors.append(f"LINK {path.name}: unsupported scheme")
                continue
            destination = (
                (path.parent / unquote(parsed.path)).resolve() if parsed.path else path
            )
            if not destination.is_file():
                errors.append(f"LINK {path.name}: missing {target}")
            elif parsed.fragment and destination.suffix == ".md":
                try:
                    if unquote(parsed.fragment) not in anchors(
                        destination.read_text(encoding="utf-8")
                    ):
                        errors.append(f"ANCHOR {path.name}: missing {target}")
                except (OSError, UnicodeError):
                    errors.append(f"LINK {path.name}: unreadable target")

    economics = read("economics.json")
    try:
        if economics["status"] != "illustrative_not_observed":
            raise ValueError("scenarios must remain illustrative")
        a = economics["assumptions"]
        f, r, m = (
            a[k]
            for k in ("collection_fraction", "labor_rate_per_hour", "target_margin")
        )
        scenarios = records(economics["scenarios"], "scenarios")
        seen: set[str] = set()
        for row in scenarios:
            name = row.get("name")
            if not text_value(name) or name in seen:
                raise ValueError("missing or duplicate scenario name")
            seen.add(name)
            p, c, h, contribution, threshold = (
                row[k]
                for k in (
                    "price",
                    "variable_cost",
                    "labor_hours",
                    "expected_contribution",
                    "expected_max_hours",
                )
            )
            values = (p, c, h, f, r, m, contribution, threshold)
            if any(type(n) not in (int, float) or not math.isfinite(n) for n in values):
                raise ValueError("finite numeric inputs required")
            if not (
                p > 0 and c >= 0 and h >= 0 and 0 <= f < 1 and r > 0 and 0 <= m < 1
            ):
                raise ValueError("inputs outside permitted ranges")
            if not math.isclose(
                p * (1 - f) - c - h * r, contribution, rel_tol=0, abs_tol=0.005
            ):
                errors.append(f"ECONOMICS {name}: contribution mismatch")
            if not math.isclose(
                (p * (1 - f - m) - c) / r, threshold, rel_tol=0, abs_tol=0.005
            ):
                errors.append(f"ECONOMICS {name}: labor threshold mismatch")
    except (TypeError, KeyError, ValueError, OverflowError) as exc:
        errors.append(f"ECONOMICS {exc}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, default=DEFAULT_PACKAGE)
    errors = validate(parser.parse_args().package)
    if errors:
        print("\n".join(errors))
        return 1
    print(
        "PASS: references, coverage, dates, local links, scenario arithmetic and targeted metadata scan"
    )
    print(
        "LIMIT: not source-truth, comprehensive disclosure review, adoption or profitability evidence"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
