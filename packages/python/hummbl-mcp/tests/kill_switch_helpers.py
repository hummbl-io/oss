"""Synthetic operator authority for tests of successful transitions only."""

from hummbl_governance.kill_switch import KillSwitch, OperatorReleaseAuthority

CREDENTIAL = "synthetic-independent-operator-credential-for-tests"
AUTHORITY = OperatorReleaseAuthority(
    "authenticated-test-operator", OperatorReleaseAuthority.create_verifier(CREDENTIAL),
)


def operator_switch(*args, **kwargs):
    return KillSwitch(*args, release_authority=AUTHORITY, **kwargs)


def release(ks, triggered_by="test-caller", reason="test approval"):
    return ks.disengage(
        triggered_by, reason, credential=CREDENTIAL, confirm=True,
        expected_event_id=ks.get_status()["event_id"],
    )
