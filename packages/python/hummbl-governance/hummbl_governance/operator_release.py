"""Interactive operator-only release: python -m hummbl_governance.operator_release.

Run under a separately protected operator account, never as an agent tool.
See docs/OPERATOR_RELEASE.md for deployment assumptions and credential setup.
No credentials are accepted on the command line or from request metadata.
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import sys
import warnings
from pathlib import Path

from hummbl_governance.kill_switch import (
    KillSwitch,
    KillSwitchAuthorizationError,
    KillSwitchConfigurationError,
    KillSwitchPersistenceError,
    KillSwitchTamperError,
    OperatorReleaseAuthority,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", type=Path, required=True)
    parser.add_argument("--reason", required=True)
    args = parser.parse_args(argv)
    try:
        if not sys.stdin.isatty() or not sys.stderr.isatty():
            raise KillSwitchAuthorizationError("An interactive operator terminal is required")
        if not args.reason.strip():
            raise KillSwitchAuthorizationError("A release reason is required")
        authority = OperatorReleaseAuthority(
            operator_id=os.environ.get("GOVERNANCE_OPERATOR_ID", ""),
            credential_sha256=os.environ.get("GOVERNANCE_OPERATOR_CREDENTIAL_SHA256", ""),
        )
        ks = KillSwitch.load_from_file(
            args.state_dir, require_existing=True, release_authority=authority,
        )
        status = ks.get_status()
        if not status["engaged"]:
            raise KillSwitchAuthorizationError("There is no current halt to release")
        print(json.dumps({"operator": authority.operator_id, "halt": status,
                          "release_reason": args.reason}, indent=2))
        expected = status["event_id"]
        if input(f"Type RELEASE {expected} to confirm: ") != f"RELEASE {expected}":
            raise KillSwitchAuthorizationError("Release was not confirmed")
        with warnings.catch_warnings():
            warnings.simplefilter("error", getpass.GetPassWarning)
            credential = getpass.getpass("Operator credential: ")
        event = ks.disengage(
            reason=args.reason, credential=credential, confirm=True,
            expected_event_id=expected,
        )
        print(json.dumps({"disengaged": True, "operator": event.triggered_by,
                          "event_id": event.event_id}))
        return 0
    except (KillSwitchAuthorizationError, KillSwitchConfigurationError,
            KillSwitchPersistenceError, KillSwitchTamperError, ValueError,
            OSError, EOFError, getpass.GetPassWarning) as exc:
        print(f"Release denied: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
