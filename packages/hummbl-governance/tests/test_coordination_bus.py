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

"""Tests for hummbl_governance.coordination_bus module.

Covers BusWriter, HMAC signing, PolicyLevel, sanitization, concurrency,
and edge cases. All tests use tmp_path -- no real filesystem side effects.
"""

from __future__ import annotations

import threading

import pytest

from hummbl_governance.coordination_bus import (
    MAX_MESSAGE_BYTES,
    MAX_PAYLOAD_FIELDS,
    BusWriter,
    PolicyLevel,
    _escape_message,
    _normalize_timestamp,
    _sanitize_field,
    _validate_fields,
    generate_secret,
    sign_message,
    verify_message,
)


# -----------------------------------------------------------------------
# TestBusWriter
# -----------------------------------------------------------------------


class TestBusWriterPost:
    """Tests for BusWriter.post()."""

    def test_post_creates_file(self, tmp_path):
        bus_file = tmp_path / "bus" / "messages.tsv"
        bus = BusWriter(bus_file)
        bus.post("agent-1", "all", "STATUS", "hello")
        assert bus_file.exists()

    def test_post_creates_parent_dirs(self, tmp_path):
        bus_file = tmp_path / "deep" / "nested" / "dir" / "messages.tsv"
        bus = BusWriter(bus_file)
        bus.post("agent-1", "all", "STATUS", "hello")
        assert bus_file.exists()
        assert bus_file.parent.is_dir()

    def test_post_appends_tsv_line(self, tmp_path):
        bus_file = tmp_path / "messages.tsv"
        bus = BusWriter(bus_file)
        bus.post("agent-1", "all", "STATUS", "first")
        bus.post("agent-2", "agent-1", "ACK", "second")

        lines = bus_file.read_text().strip().split("\n")
        assert len(lines) == 2
        # Each line has 5 tab-separated fields
        for line in lines:
            assert len(line.split("\t")) == 5

    def test_post_timestamp_format(self, tmp_path):
        bus_file = tmp_path / "messages.tsv"
        bus = BusWriter(bus_file)
        bus.post("a", "b", "STATUS", "msg")

        msgs = bus.read_all()
        ts = msgs[0]["timestamp"]
        # Canonical format: YYYY-MM-DDTHH:MM:SSZ
        assert ts.endswith("Z")
        assert "T" in ts
        assert len(ts) == 20  # 2026-03-20T12:00:00Z

    def test_post_with_explicit_timestamp(self, tmp_path):
        bus_file = tmp_path / "messages.tsv"
        bus = BusWriter(bus_file)
        bus.post("a", "b", "STATUS", "msg", timestamp="2026-01-15T10:30:00Z")

        msgs = bus.read_all()
        assert msgs[0]["timestamp"] == "2026-01-15T10:30:00Z"

    def test_post_normalizes_offset_timestamp(self, tmp_path):
        bus_file = tmp_path / "messages.tsv"
        bus = BusWriter(bus_file)
        bus.post("a", "b", "STATUS", "msg", timestamp="2026-01-15T10:30:00-05:00")

        msgs = bus.read_all()
        assert msgs[0]["timestamp"] == "2026-01-15T15:30:00Z"

    def test_post_validates_empty_from_id(self, tmp_path):
        bus = BusWriter(tmp_path / "messages.tsv")
        with pytest.raises(ValueError, match="from_id"):
            bus.post("", "all", "STATUS", "hello")

    def test_post_validates_empty_message(self, tmp_path):
        bus = BusWriter(tmp_path / "messages.tsv")
        with pytest.raises(ValueError, match="message"):
            bus.post("a", "b", "STATUS", "   ")

    def test_post_validates_oversized_message(self, tmp_path):
        bus = BusWriter(tmp_path / "messages.tsv")
        big_msg = "x" * (MAX_MESSAGE_BYTES + 1)
        with pytest.raises(ValueError, match="exceeds maximum size"):
            bus.post("a", "b", "STATUS", big_msg)

    def test_post_validates_null_bytes(self, tmp_path):
        bus = BusWriter(tmp_path / "messages.tsv")
        with pytest.raises(ValueError, match="null bytes"):
            bus.post("a", "b", "STATUS", "hello\x00world")

    def test_post_skip_validation(self, tmp_path):
        """validate=False skips field checks."""
        bus = BusWriter(tmp_path / "messages.tsv")
        # Empty from_id would fail validation, but passes with validate=False
        bus.post("", "b", "STATUS", "msg", validate=False)
        assert bus.message_count() == 1


class TestBusWriterSanitization:
    """Tests for tab/newline sanitization in bus messages."""

    def test_tabs_replaced_in_message(self, tmp_path):
        bus = BusWriter(tmp_path / "messages.tsv")
        bus.post("a", "b", "STATUS", "col1\tcol2\tcol3")

        raw = (tmp_path / "messages.tsv").read_text()
        # Message field should not contain raw tabs beyond the 4 delimiters
        fields = raw.strip().split("\t")
        assert len(fields) == 5  # exactly 5 columns

    def test_newlines_escaped_in_message(self, tmp_path):
        bus = BusWriter(tmp_path / "messages.tsv")
        bus.post("a", "b", "STATUS", "line1\nline2\nline3")

        raw = (tmp_path / "messages.tsv").read_text()
        # Should be a single line (plus trailing newline)
        lines = raw.strip().split("\n")
        assert len(lines) == 1

    def test_tabs_in_header_fields(self, tmp_path):
        bus = BusWriter(tmp_path / "messages.tsv")
        bus.post("agent\t1", "recipient\t2", "STA\tTUS", "hello")

        msgs = bus.read_all()
        assert len(msgs) == 1
        # Tabs replaced with spaces in from/to/type
        assert "\t" not in msgs[0]["from"]
        assert "\t" not in msgs[0]["to"]
        assert "\t" not in msgs[0]["type"]

    def test_newlines_in_header_fields(self, tmp_path):
        bus = BusWriter(tmp_path / "messages.tsv")
        bus.post("agent\n1", "recip\r\nient", "STATUS", "hello")

        msgs = bus.read_all()
        assert len(msgs) == 1
        assert "\n" not in msgs[0]["from"]
        assert "\n" not in msgs[0]["to"]

    def test_carriage_return_escaped(self, tmp_path):
        bus = BusWriter(tmp_path / "messages.tsv")
        bus.post("a", "b", "STATUS", "line1\r\nline2\rline3")

        raw = (tmp_path / "messages.tsv").read_text()
        lines = raw.strip().split("\n")
        assert len(lines) == 1


class TestBusWriterRead:
    """Tests for BusWriter.read_all(), read_since(), message_count()."""

    def test_read_all_empty_file(self, tmp_path):
        bus_file = tmp_path / "messages.tsv"
        bus_file.write_text("")
        bus = BusWriter(bus_file)
        assert bus.read_all() == []

    def test_read_all_missing_file(self, tmp_path):
        bus = BusWriter(tmp_path / "nonexistent.tsv")
        assert bus.read_all() == []

    def test_read_all_returns_dicts(self, tmp_path):
        bus = BusWriter(tmp_path / "messages.tsv")
        bus.post("agent-1", "all", "STATUS", "hello world")

        msgs = bus.read_all()
        assert len(msgs) == 1
        msg = msgs[0]
        assert msg["from"] == "agent-1"
        assert msg["to"] == "all"
        assert msg["type"] == "STATUS"
        assert msg["message"] == "hello world"

    def test_read_all_skips_malformed_lines(self, tmp_path):
        bus_file = tmp_path / "messages.tsv"
        bus_file.write_text(
            "2026-03-20T00:00:00Z\ta\tb\tSTATUS\tok\n"
            "malformed line\n"
            "too\tfew\tcolumns\n"
            "2026-03-20T00:01:00Z\tc\td\tACK\tgood\n"
        )
        bus = BusWriter(bus_file)
        msgs = bus.read_all()
        assert len(msgs) == 2

    def test_read_since_filters_by_timestamp(self, tmp_path):
        bus_file = tmp_path / "messages.tsv"
        bus_file.write_text(
            "2026-03-01T00:00:00Z\ta\tb\tSTATUS\told\n"
            "2026-03-15T00:00:00Z\ta\tb\tSTATUS\tmid\n"
            "2026-03-20T00:00:00Z\ta\tb\tSTATUS\tnew\n"
        )
        bus = BusWriter(bus_file)

        recent = bus.read_since("2026-03-15T00:00:00Z")
        assert len(recent) == 2
        assert recent[0]["message"] == "mid"
        assert recent[1]["message"] == "new"

    def test_read_since_with_no_matches(self, tmp_path):
        bus_file = tmp_path / "messages.tsv"
        bus_file.write_text("2026-01-01T00:00:00Z\ta\tb\tSTATUS\told\n")
        bus = BusWriter(bus_file)

        recent = bus.read_since("2026-12-01T00:00:00Z")
        assert recent == []

    def test_read_since_missing_file(self, tmp_path):
        bus = BusWriter(tmp_path / "nonexistent.tsv")
        assert bus.read_since("2026-01-01T00:00:00Z") == []

    def test_message_count(self, tmp_path):
        bus = BusWriter(tmp_path / "messages.tsv")
        assert bus.message_count() == 0

        bus.post("a", "b", "STATUS", "one")
        bus.post("a", "b", "STATUS", "two")
        bus.post("a", "b", "STATUS", "three")
        assert bus.message_count() == 3

    def test_message_count_missing_file(self, tmp_path):
        bus = BusWriter(tmp_path / "nonexistent.tsv")
        assert bus.message_count() == 0

    def test_message_count_skips_malformed(self, tmp_path):
        bus_file = tmp_path / "messages.tsv"
        bus_file.write_text(
            "2026-03-20T00:00:00Z\ta\tb\tSTATUS\tok\n"
            "bad line\n"
            "2026-03-20T00:01:00Z\tc\td\tACK\tgood\n"
        )
        bus = BusWriter(bus_file)
        assert bus.message_count() == 2


class TestBusWriterConcurrency:
    """Tests for thread-safe concurrent writes."""

    def test_concurrent_writes_no_corruption(self, tmp_path):
        """Multiple threads writing simultaneously should not corrupt the bus."""
        bus = BusWriter(tmp_path / "messages.tsv")
        n_threads = 10
        n_messages = 20
        errors: list[Exception] = []

        def writer(thread_id: int) -> None:
            try:
                for i in range(n_messages):
                    bus.post(
                        f"thread-{thread_id}",
                        "all",
                        "STATUS",
                        f"msg-{i}",
                    )
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=writer, args=(t,)) for t in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == [], f"Errors during concurrent writes: {errors}"
        assert bus.message_count() == n_threads * n_messages

        # Every line should have exactly 5 fields
        raw = (tmp_path / "messages.tsv").read_text()
        for line in raw.strip().split("\n"):
            assert len(line.split("\t")) == 5


class TestBusWriterPolicy:
    """Tests for policy property."""

    def test_default_policy_is_permissive(self, tmp_path):
        bus = BusWriter(tmp_path / "messages.tsv")
        assert bus.policy == PolicyLevel.PERMISSIVE

    def test_custom_policy(self, tmp_path):
        bus = BusWriter(tmp_path / "messages.tsv", policy=PolicyLevel.STRICT)
        assert bus.policy == PolicyLevel.STRICT


# -----------------------------------------------------------------------
# TestMessageSigning
# -----------------------------------------------------------------------


class TestMessageSigning:
    """Tests for sign_message(), verify_message(), generate_secret()."""

    def test_sign_returns_hex_string(self):
        sig = sign_message("hello", "secret")
        assert isinstance(sig, str)
        assert len(sig) == 64  # SHA-256 hex digest
        # All hex chars
        int(sig, 16)

    def test_sign_deterministic(self):
        sig1 = sign_message("payload", "key")
        sig2 = sign_message("payload", "key")
        assert sig1 == sig2

    def test_sign_different_payloads(self):
        sig1 = sign_message("payload-a", "key")
        sig2 = sign_message("payload-b", "key")
        assert sig1 != sig2

    def test_sign_different_secrets(self):
        sig1 = sign_message("payload", "key-a")
        sig2 = sign_message("payload", "key-b")
        assert sig1 != sig2

    def test_verify_valid_signature(self):
        secret = "my-secret-key"
        payload = "2026-03-20T00:00:00Z\tagent-1\tall\tSTATUS\tok"
        sig = sign_message(payload, secret)
        assert verify_message(payload, sig, secret) is True

    def test_verify_wrong_secret(self):
        payload = "hello"
        sig = sign_message(payload, "correct-secret")
        assert verify_message(payload, sig, "wrong-secret") is False

    def test_verify_tampered_payload(self):
        secret = "shared-key"
        payload = "original message"
        sig = sign_message(payload, secret)
        assert verify_message("tampered message", sig, secret) is False

    def test_verify_empty_signature(self):
        assert verify_message("payload", "", "secret") is False

    def test_verify_garbage_signature(self):
        assert verify_message("payload", "not-a-real-sig", "secret") is False

    def test_generate_secret_default_length(self):
        secret = generate_secret()
        assert isinstance(secret, str)
        assert len(secret) == 64  # 32 bytes = 64 hex chars

    def test_generate_secret_custom_length(self):
        secret = generate_secret(16)
        assert len(secret) == 32  # 16 bytes = 32 hex chars

    def test_generate_secret_uniqueness(self):
        secrets_list = [generate_secret() for _ in range(10)]
        assert len(set(secrets_list)) == 10  # All unique


# -----------------------------------------------------------------------
# TestPolicyLevel
# -----------------------------------------------------------------------


class TestPolicyLevel:
    """Tests for PolicyLevel enum."""

    def test_enum_values(self):
        assert PolicyLevel.PERMISSIVE.value == 1
        assert PolicyLevel.WARN.value == 2
        assert PolicyLevel.STRICT.value == 3

    def test_ordering(self):
        assert PolicyLevel.PERMISSIVE < PolicyLevel.WARN
        assert PolicyLevel.WARN < PolicyLevel.STRICT
        assert PolicyLevel.STRICT > PolicyLevel.PERMISSIVE

    def test_ordering_le_ge(self):
        assert PolicyLevel.PERMISSIVE <= PolicyLevel.PERMISSIVE
        assert PolicyLevel.PERMISSIVE <= PolicyLevel.WARN
        assert PolicyLevel.STRICT >= PolicyLevel.WARN
        assert PolicyLevel.STRICT >= PolicyLevel.STRICT

    def test_all_members(self):
        members = set(PolicyLevel)
        assert members == {PolicyLevel.PERMISSIVE, PolicyLevel.WARN, PolicyLevel.STRICT}

    def test_ordering_not_implemented_for_other_types(self):
        with pytest.raises(TypeError):
            PolicyLevel.PERMISSIVE < 1  # type: ignore[operator]


# -----------------------------------------------------------------------
# TestHelpers
# -----------------------------------------------------------------------


class TestSanitizeField:
    """Tests for _sanitize_field()."""

    def test_strips_whitespace(self):
        assert _sanitize_field("  hello  ") == "hello"

    def test_replaces_tabs(self):
        assert _sanitize_field("a\tb") == "a b"

    def test_escapes_newlines(self):
        assert _sanitize_field("a\nb") == "a\\nb"

    def test_escapes_crlf(self):
        assert _sanitize_field("a\r\nb") == "a\\nb"


class TestEscapeMessage:
    """Tests for _escape_message()."""

    def test_escapes_newline(self):
        assert _escape_message("line1\nline2") == "line1\\nline2"

    def test_escapes_tab(self):
        assert _escape_message("col1\tcol2") == "col1 col2"

    def test_escapes_crlf(self):
        assert _escape_message("a\r\nb") == "a\\nb"

    def test_non_string_coerced(self):
        assert _escape_message(42) == "42"  # type: ignore[arg-type]


class TestNormalizeTimestamp:
    """Tests for _normalize_timestamp()."""

    def test_utc_passthrough(self):
        assert _normalize_timestamp("2026-03-20T12:00:00Z") == "2026-03-20T12:00:00Z"

    def test_strips_subseconds(self):
        assert _normalize_timestamp("2026-03-20T12:00:00.123456Z") == "2026-03-20T12:00:00Z"

    def test_converts_positive_offset(self):
        result = _normalize_timestamp("2026-03-20T17:00:00+05:00")
        assert result == "2026-03-20T12:00:00Z"

    def test_converts_negative_offset(self):
        result = _normalize_timestamp("2026-03-20T07:00:00-05:00")
        assert result == "2026-03-20T12:00:00Z"

    def test_fallback_for_unparseable(self):
        result = _normalize_timestamp("not-a-timestamp")
        assert result == "not-a-timestamp"


class TestValidateFields:
    """Tests for _validate_fields()."""

    def test_valid_fields_pass(self):
        _validate_fields("agent", "all", "STATUS", "hello")  # no exception

    def test_empty_from_raises(self):
        with pytest.raises(ValueError, match="from_id"):
            _validate_fields("", "all", "STATUS", "hello")

    def test_non_string_to_raises(self):
        with pytest.raises(ValueError, match="to_id"):
            _validate_fields("a", 123, "STATUS", "hello")  # type: ignore[arg-type]

    def test_oversized_json_fields_raises(self):
        big_json = "{" + ",".join(f'"k{i}":1' for i in range(MAX_PAYLOAD_FIELDS + 1)) + "}"
        with pytest.raises(ValueError, match="structured payload"):
            _validate_fields("a", "b", "STATUS", big_json)
