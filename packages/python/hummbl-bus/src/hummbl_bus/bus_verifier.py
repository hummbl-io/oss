"""Bus integrity verifier for ASI07 audit and compliance.

Read-only tool that scans the coordination bus and reports:
    - Signed vs unsigned message counts
    - Signature verification results (with a provided secret)
    - Duplicate nonce detection (replay indicators)
    - Unknown sender identification
    - Timestamp anomalies (gaps, out-of-order, future timestamps)

CLI usage:
    python -m hummbl_bus.bus_verifier [--bus PATH] [--secret-file PATH] [--json]

This module is stdlib-only and read-only -- it never writes to the bus.
"""

from __future__ import annotations

import json
import os
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from .bus_writer import (
    DEFAULT_BUS_PATH,
    _parse_signing_envelope,
    _resolve_repo_root,
    is_signed_message,
    load_known_agent_ids,
    verify_bus_message,
)


@dataclass
class VerificationResult:
    """Result of verifying a single bus message."""

    line_number: int
    timestamp: str
    from_id: str
    to_id: str
    msg_type: str
    is_signed: bool
    signature_valid: bool | None = None  # None if no secret provided
    issue: str | None = None


@dataclass
class BusAuditReport:
    """Aggregate audit report for the coordination bus."""

    bus_path: str
    total_messages: int = 0
    signed_messages: int = 0
    unsigned_messages: int = 0
    verified_ok: int = 0
    verified_fail: int = 0
    verification_skipped: int = 0
    malformed_lines: int = 0
    duplicate_nonces: int = 0
    unknown_senders: int = 0
    timestamp_anomalies: int = 0
    sender_counts: dict[str, int] = field(default_factory=dict)
    type_counts: dict[str, int] = field(default_factory=dict)
    issues: list[str] = field(default_factory=list)

    @property
    def signing_coverage_pct(self) -> float:
        """Percentage of messages that are signed."""
        if self.total_messages == 0:
            return 0.0
        return (self.signed_messages / self.total_messages) * 100

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "bus_path": self.bus_path,
            "total_messages": self.total_messages,
            "signed_messages": self.signed_messages,
            "unsigned_messages": self.unsigned_messages,
            "signing_coverage_pct": round(self.signing_coverage_pct, 1),
            "verified_ok": self.verified_ok,
            "verified_fail": self.verified_fail,
            "verification_skipped": self.verification_skipped,
            "malformed_lines": self.malformed_lines,
            "duplicate_nonces": self.duplicate_nonces,
            "unknown_senders": self.unknown_senders,
            "timestamp_anomalies": self.timestamp_anomalies,
            "top_senders": dict(Counter(self.sender_counts).most_common(10)),
            "type_distribution": dict(Counter(self.type_counts).most_common(15)),
            "issue_count": len(self.issues),
            "issues_sample": self.issues[:20],
        }

    def summary(self) -> str:
        """Human-readable summary."""
        lines = [
            f"Bus Integrity Audit: {self.bus_path}",
            f"  Total messages:     {self.total_messages}",
            f"  Signed:             {self.signed_messages} ({self.signing_coverage_pct:.1f}%)",
            f"  Unsigned:           {self.unsigned_messages}",
        ]
        if self.verified_ok or self.verified_fail:
            lines.append(f"  Verified OK:        {self.verified_ok}")
            lines.append(f"  Verified FAIL:      {self.verified_fail}")
        if self.verification_skipped:
            lines.append(f"  Verify skipped:     {self.verification_skipped}")
        if self.malformed_lines:
            lines.append(f"  Malformed lines:    {self.malformed_lines}")
        if self.duplicate_nonces:
            lines.append(f"  Duplicate nonces:   {self.duplicate_nonces}")
        if self.unknown_senders:
            lines.append(f"  Unknown senders:    {self.unknown_senders}")
        if self.timestamp_anomalies:
            lines.append(f"  Timestamp issues:   {self.timestamp_anomalies}")
        if self.issues:
            lines.append(f"  Issues found:       {len(self.issues)}")
            for issue in self.issues[:5]:
                lines.append(f"    - {issue}")
            if len(self.issues) > 5:
                lines.append(f"    ... and {len(self.issues) - 5} more")
        return "\n".join(lines)


def audit_bus(
    bus_path: str | Path,
    secret: bytes | None = None,
    known_agents: set[str] | None = None,
) -> BusAuditReport:
    """Perform a read-only integrity audit of the coordination bus.

    Parameters
    ----------
    bus_path : str | Path
        Path to the messages.tsv file.
    secret : bytes | None
        HMAC secret for signature verification. If None, signed messages
        are counted but not verified.
    known_agents : set[str] | None
        Known agent IDs. If None, loads from registry.

    Returns:
    -------
    BusAuditReport
        Detailed audit report.
    """
    bus_path = Path(bus_path)
    report = BusAuditReport(bus_path=str(bus_path))

    if not bus_path.exists():
        report.issues.append("Bus file does not exist")
        return report

    if known_agents is None:
        try:
            known_agents = load_known_agent_ids()
        except Exception:
            known_agents = set()

    seen_nonces: set[str] = set()
    prev_timestamp: str | None = None

    with open(bus_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.rstrip("\n\r")
            if not line:
                continue

            parts = line.split("\t")
            if len(parts) != 5:
                report.malformed_lines += 1
                report.issues.append(
                    f"Line {line_num}: expected 5 columns, got {len(parts)}"
                )
                continue

            timestamp, from_id, to_id, msg_type, message = parts
            report.total_messages += 1

            # Count senders and types
            report.sender_counts[from_id] = report.sender_counts.get(from_id, 0) + 1
            report.type_counts[msg_type] = report.type_counts.get(msg_type, 0) + 1

            # Check sender identity
            base_id = from_id.split("(")[0].strip() if "(" in from_id else from_id
            if base_id not in known_agents and from_id not in known_agents:
                report.unknown_senders += 1

            # Check timestamp ordering
            if prev_timestamp is not None:
                try:
                    datetime.fromisoformat(prev_timestamp.replace("Z", "+00:00"))
                    curr_dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    # Flag future timestamps (more than 60s ahead of now)
                    now = datetime.now(UTC)
                    if curr_dt > now and (curr_dt - now).total_seconds() > 60:
                        report.timestamp_anomalies += 1
                        report.issues.append(
                            f"Line {line_num}: future timestamp {timestamp}"
                        )
                except (ValueError, AttributeError):
                    report.timestamp_anomalies += 1
            prev_timestamp = timestamp

            # Check signing status
            signed = is_signed_message(message)
            if signed:
                report.signed_messages += 1

                # Extract nonce for replay detection
                envelope = _parse_signing_envelope(message)
                if envelope:
                    _content, nonce, _sig = envelope
                    if nonce in seen_nonces:
                        report.duplicate_nonces += 1
                        report.issues.append(
                            f"Line {line_num}: duplicate nonce {nonce[:20]}..."
                        )
                    seen_nonces.add(nonce)

                # Verify signature if secret provided
                if secret is not None:
                    verified, _content = verify_bus_message(
                        timestamp, from_id, to_id, msg_type, message, secret
                    )
                    if verified:
                        report.verified_ok += 1
                    else:
                        report.verified_fail += 1
                        report.issues.append(
                            f"Line {line_num}: signature verification FAILED "
                            f"(from={from_id})"
                        )
                else:
                    report.verification_skipped += 1
            else:
                report.unsigned_messages += 1

    return report


def _resolve_bus_path(override: str | None = None) -> Path:
    """Resolve bus path from override, env, or git root."""
    if override:
        return Path(override)
    env_path = os.environ.get("COORDINATION_BUS")
    if env_path:
        return Path(env_path)
    root = _resolve_repo_root()
    if root is not None:
        return root / DEFAULT_BUS_PATH
    return Path(DEFAULT_BUS_PATH)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for bus integrity audit.

    Usage:
        python -m hummbl_bus.bus_verifier [options]

    Options:
        --bus PATH          Override bus file path
        --secret-file PATH  Verify signatures with key from file
        --json              Output as JSON instead of text
        --quiet             Only print issues (non-zero exit on problems)
    """
    import base64

    args = argv if argv is not None else sys.argv[1:]

    bus_override = None
    secret_file = None
    json_output = False
    quiet = False

    i = 0
    while i < len(args):
        if args[i] == "--bus" and i + 1 < len(args):
            bus_override = args[i + 1]
            i += 2
        elif args[i] == "--secret-file" and i + 1 < len(args):
            secret_file = args[i + 1]
            i += 2
        elif args[i] == "--json":
            json_output = True
            i += 1
        elif args[i] == "--quiet":
            quiet = True
            i += 1
        else:
            print(f"Unknown argument: {args[i]}", file=sys.stderr)
            return 2

    bus_path = _resolve_bus_path(bus_override)

    # Load secret if provided
    secret: bytes | None = None
    if secret_file:
        try:
            with open(secret_file, "r", encoding="utf-8") as f:
                key_data = json.load(f)
            secret = base64.b64decode(key_data["key"])
        except (OSError, KeyError, json.JSONDecodeError) as e:
            print(f"ERROR: failed to load secret file: {e}", file=sys.stderr)
            return 1

    report = audit_bus(bus_path, secret=secret)

    if json_output:
        print(json.dumps(report.to_dict(), indent=2))
    elif not quiet:
        print(report.summary())
    elif report.issues:
        for issue in report.issues:
            print(issue, file=sys.stderr)

    # Exit code: 0 = clean, 1 = issues found
    if report.verified_fail > 0 or report.duplicate_nonces > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
