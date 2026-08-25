#!/usr/bin/env python3
"""Git signing and local toolchain health audit."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from dataclasses import dataclass


@dataclass
class AuditEntry:
    name: str
    status: str
    detail: str


def run(cmd: list[str], cwd: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def read_config(key: str) -> str:
    proc = run(["git", "config", "--get", key])
    if proc.returncode != 0:
        return ""
    return proc.stdout.strip()


def detect_gpg_binary() -> bool:
    return any(
        run(["where", "gpg"], cwd=None).returncode == 0 for _ in [None]
    ) if os.name == "nt" else any(
        run(["which", "gpg"], cwd=None).returncode == 0 for _ in [None]
    )


def audit_remote_actors() -> list[AuditEntry]:
    entries: list[AuditEntry] = []
    for key in ["commit.gpgsign", "tag.gpgsign", "user.signingkey", "gpg.format"]:
        value = read_config(key)
        if value:
            entries.append(AuditEntry(key, "set", value))
        else:
            entries.append(AuditEntry(key, "unset", "not configured"))
    return entries


def last_commit_signature() -> AuditEntry:
    proc = run(["git", "log", "-1", "--format=%H %G? %s"])
    if proc.returncode != 0 or not proc.stdout.strip():
        return AuditEntry("last_commit_signature", "unknown", "git history unavailable")
    parts = proc.stdout.strip().split(maxsplit=2)
    if len(parts) < 2:
        return AuditEntry("last_commit_signature", "unknown", "signature status not parsed")
    status = parts[1]
    mapping = {
        "B": "valid signature",
        "G": "good signature",
        "U": "unsigned",
        "N": "no signature",
        "E": "error in signature",
        "R": "bad signature",
        "X": "expired signature",
        "Y": "expired and expired key",
        "b": "bad signature",
    }
    return AuditEntry("last_commit_signature", mapping.get(status, f"status {status}"), proc.stdout.strip())


def verify_identity() -> AuditEntry:
    name = read_config("user.name")
    email = read_config("user.email")
    if name and email:
        return AuditEntry("identity", "set", f"{name} <{email}>")
    return AuditEntry("identity", "missing", "user.name / user.email not set")


def verify_hooks() -> AuditEntry:
    proc = run(["git", "rev-parse", "--git-path", "hooks"])
    if proc.returncode != 0:
        return AuditEntry("hooks", "unknown", "git hook path unavailable")
    hooks_path = proc.stdout.strip()
    exists = "exists" if os.path.isdir(hooks_path) else "missing"
    return AuditEntry("hooks", exists, hooks_path)


def build_report(strict: bool) -> tuple[list[AuditEntry], str]:
    report = [
        AuditEntry("repo", "ok", os.getcwd()),
        verify_identity(),
        AuditEntry("gpg_available", "yes" if detect_gpg_binary() else "no", "toolchain binary check"),
    ]
    report.extend(audit_remote_actors())
    report.append(last_commit_signature())
    report.append(verify_hooks())

    status = "pass"
    if strict:
        for item in report:
            if item.name in {"commit.gpgsign", "tag.gpgsign", "user.signingkey", "identity", "last_commit_signature"}:
                if item.status in {"unset", "missing", "no"}:
                    status = "fail"

    return report, status


def to_payload(report: list[AuditEntry], status: str) -> dict[str, object]:
    return {
        "status": status,
        "entries": [
            {"name": item.name, "status": item.status, "detail": item.detail}
            for item in report
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit git signing and toolchain settings")
    parser.add_argument("--strict", action="store_true", help="Fail on missing signing controls")
    parser.add_argument("--json", action="store_true", help="Emit JSON summary")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    entries, status = build_report(args.strict)
    if args.json:
        print(json.dumps(to_payload(entries, status), indent=2))
    else:
        print(f"Audit status: {status}")
        for item in entries:
            print(f"- {item.name}: {item.status} ({item.detail})")
    if args.strict and status != "pass":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
