"""Regression tests for scan_pii() pattern precision.

phone_us must match formatted US numbers while rejecting bare 10-digit
runs that collide with HRESULT error codes, numeric IDs, and timestamps.
"""

import pytest

from hummbl_cognition.ledger_writer import scan_pii


@pytest.mark.parametrize(
    "text",
    [
        "call 214-702-4894",
        "ph (214) 702-4894",
        "+1-214-702-4894",
        "214.702.4894",
        "214 702 4894",
        "+1 214 702 4894",
        "(214)702-4894",
        "214-7024894",
    ],
)
def test_phone_us_matches_formatted_numbers(text: str) -> None:
    assert "phone_us" in [t for t, _ in scan_pii(text)]


@pytest.mark.parametrize(
    "text",
    [
        "Last Result: -2147024894",  # Windows HRESULT 0x80070002
        "id 2147024894",
        "ts 1694557890123",
        "n=1234567890",
    ],
)
def test_phone_us_rejects_bare_digit_runs(text: str) -> None:
    assert "phone_us" not in [t for t, _ in scan_pii(text)]


def test_email_still_detected() -> None:
    assert "email" in [t for t, _ in scan_pii("contact user@example.com")]


def test_ssn_still_detected() -> None:
    assert "ssn" in [t for t, _ in scan_pii("ssn 123-45-6789")]
