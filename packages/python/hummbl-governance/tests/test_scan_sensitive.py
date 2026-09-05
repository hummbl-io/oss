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

"""Tests for scripts/scan-sensitive-pre-commit.py.

Tests the pattern registry, severity levels, scanning functions,
allowlist, and CLI argument parsing.
"""

import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

# Load the script as a module (it lives in scripts/, not a package)
_SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "scan-sensitive-pre-commit.py"
_spec = importlib.util.spec_from_file_location("scan_sensitive", _SCRIPT_PATH)
scan_sensitive = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(scan_sensitive)


@pytest.fixture(autouse=True)
def isolated_scanner_environment(monkeypatch):
    monkeypatch.delenv("SKIP_SENSITIVE_SCAN", raising=False)
    def forbidden_subprocess(*args, **kwargs):
        raise AssertionError("Focused scanner tests must not invoke external processes")
    monkeypatch.setattr(scan_sensitive.subprocess, "run", forbidden_subprocess)


# --- Pattern detection tests ------------------------------------------------


class TestCriticalPatterns:
    """CRITICAL severity patterns — tokens, passwords, keys, SSN."""

    def test_github_oauth_token(self):
        findings = scan_sensitive.scan_line("export GHO_TOKEN=gho_abc123XYZ")
        labels = [f[2] for f in findings]
        assert any("gho_" in l for l in labels)
        severities = [f[0] for f in findings]
        assert scan_sensitive.CRITICAL in severities

    def test_openrouter_token(self):
        findings = scan_sensitive.scan_line("Authorization: Bearer sk-or-v1abc123")
        labels = [f[2] for f in findings]
        assert any("sk-or-v1" in l for l in labels)
        severities = [f[0] for f in findings]
        assert scan_sensitive.CRITICAL in severities

    def test_anthropic_token(self):
        findings = scan_sensitive.scan_line("ANTHROPIC_KEY=sk-ant-abc123")
        severities = [f[0] for f in findings]
        assert scan_sensitive.CRITICAL in severities

    def test_openai_token(self):
        findings = scan_sensitive.scan_line("OPENAI_KEY=sk-proj-abc123")
        severities = [f[0] for f in findings]
        assert scan_sensitive.CRITICAL in severities

    def test_dashboard_token_ref(self):
        findings = scan_sensitive.scan_line("Uses DASHBOARD_TOKEN for auth")
        severities = [f[0] for f in findings]
        assert scan_sensitive.CRITICAL in severities

    def test_password_assignment(self):
        findings = scan_sensitive.scan_line("PASSWORD=hunter2")
        severities = [f[0] for f in findings]
        assert scan_sensitive.CRITICAL in severities

    def test_ssh_private_key_block(self):
        findings = scan_sensitive.scan_line("-----BEGIN RSA PRIVATE KEY-----")
        severities = [f[0] for f in findings]
        assert scan_sensitive.CRITICAL in severities

    def test_ssh_private_key_ed25519(self):
        findings = scan_sensitive.scan_line("-----BEGIN OPENSSH PRIVATE KEY-----")
        severities = [f[0] for f in findings]
        assert scan_sensitive.CRITICAL in severities

    def test_ssh_key_filename(self):
        findings = scan_sensitive.scan_line("cp ~/.ssh/id_ed25519_synthetic /tmp/")
        severities = [f[0] for f in findings]
        assert scan_sensitive.CRITICAL in severities

    @pytest.mark.parametrize("name", ["id_ed25519.pub", "id_rsa_synthetic.pub",
                                      "id_ed25519_synthetic-name.pub"])
    def test_public_key_filename_is_not_private_key(self, name):
        assert not any(f[2] == "SSH private-key filename"
                       for f in scan_sensitive.scan_line(name))

    def test_ssn(self):
        findings = scan_sensitive.scan_line("SSN: 123-45-6789")
        severities = [f[0] for f in findings]
        assert scan_sensitive.CRITICAL in severities


class TestHighPatterns:
    @pytest.mark.parametrize("text", [
        "node.example.ts.net", "Patient MRN:123456",
        "C:" + "/Users/" + "synthetic/.config",
        "c:" + "\\users\\" + "synthetic/data",
        "D:" + "\\\\Users\\\\" + "synthetic/data",
        "/" + "home/synthetic/projects",
        "/" + "Users/synthetic/projects",
        "node at 100." + "64.0.1", "node at 100." + "127.255.255",
    ])
    def test_generic_high_shapes(self, text):
        assert scan_sensitive.HIGH in [f[0] for f in scan_sensitive.scan_line(text)]

    @pytest.mark.parametrize("address", [
        "100.63.255.255", "100.128.0.0", "100.255.0.1", "100." + "64.256.1",
        "192.0.2.10", "203.0.113.7",
    ])
    def test_non_cgnat_or_invalid_not_classified_as_cgnat(self, address):
        assert not any(f[2] == "CGNAT IPv4 address"
                       for f in scan_sensitive.scan_line(address))

    def test_public_address_and_port_need_private_custom_config(self):
        text = "server at 192.0.2.10 port 45678"
        assert scan_sensitive.scan_line(text) == []
        patterns = scan_sensitive._build_active_patterns({"custom_patterns": [
            {"severity": "HIGH", "category": "ip", "label": "site address",
             "pattern": r"\b192\.0\.2\.10\b"},
            {"severity": "HIGH", "category": "port", "label": "site service port",
             "pattern": r"\bport\s+45678\b"},
        ]})
        findings = scan_sensitive.scan_line(text, patterns)
        assert {f[2] for f in findings} == {"site address", "site service port"}


class TestMediumPatterns:
    @pytest.mark.parametrize("text", ["host=fixture-node", "machine = fixture-node.example"])
    def test_explicit_host_assignment(self, text):
        assert scan_sensitive.MEDIUM in [f[0] for f in scan_sensitive.scan_line(text)]

    def test_bare_hostname_not_inferred(self):
        assert scan_sensitive.scan_line("fixture-node is offline") == []
        patterns = scan_sensitive._build_active_patterns({"custom_patterns": [
            {"severity": "MEDIUM", "category": "hostname", "label": "site host",
             "pattern": r"\bfixture-node\b"},
        ]})
        assert any(f[2] == "site host" for f in
                   scan_sensitive.scan_line("fixture-node is offline", patterns))

    def test_email_address(self):
        assert scan_sensitive.MEDIUM in [f[0] for f in
               scan_sensitive.scan_line("contact: person@fixture.invalid")]

    @pytest.mark.parametrize("text", ["contact: user@example.com", "git@github.com:",
                                      "timestamp 1719600901"])
    def test_public_examples_and_numeric_ids(self, text):
        assert scan_sensitive.scan_line(text) == []

    @pytest.mark.parametrize("text", ["call 202-555-0100", "call 202.555.0100"])
    def test_phone_shape(self, text):
        assert scan_sensitive.MEDIUM in [f[0] for f in scan_sensitive.scan_line(text)]


class TestLowPatterns:
    def test_personal_names_only_when_configured(self):
        text = "Authored by Synthetic Example"
        assert scan_sensitive.scan_line(text) == []
        patterns = scan_sensitive._build_active_patterns({"custom_patterns": [
            {"severity": "LOW", "category": "pii", "label": "site person",
             "pattern": "Synthetic Example"},
        ]})
        assert [f[0] for f in scan_sensitive.scan_line(text, patterns)] == [scan_sensitive.LOW]


# --- Config system tests ----------------------------------------------------


class TestConfigSystem:
    """Test .vet-config.json support — disable, override, custom patterns."""

    def test_disable_pattern_by_label(self):
        config = {
            "disable_patterns": ["email address"],
            "severity_overrides": {},
            "custom_patterns": [],
        }
        active = scan_sensitive._build_active_patterns(config)
        labels = [p[2] for p in active]
        assert "email address" not in labels

    def test_severity_override(self):
        config = {
            "disable_patterns": [],
            "severity_overrides": {"explicit host assignment": "LOW"},
            "custom_patterns": [],
        }
        active = scan_sensitive._build_active_patterns(config)
        host_rules = [p for p in active if p[2] == "explicit host assignment"]
        assert len(host_rules) == 1
        assert host_rules[0][0] == "LOW"

    def test_custom_pattern_added(self):
        config = {
            "disable_patterns": [],
            "severity_overrides": {},
            "custom_patterns": [
                {"severity": "HIGH", "category": "custom",
                 "label": "project codename", "pattern": r"\bPROJECT_X\b"},
            ],
        }
        active = scan_sensitive._build_active_patterns(config)
        custom = [p for p in active if p[2] == "project codename"]
        assert len(custom) == 1
        assert custom[0][0] == "HIGH"
        # Verify it actually matches
        findings = scan_sensitive.scan_line("PROJECT_X is live", active)
        labels = [f[2] for f in findings]
        assert "project codename" in labels

    def test_disabled_pattern_not_detected(self):
        config = {
            "disable_patterns": ["email address"],
            "severity_overrides": {},
            "custom_patterns": [],
        }
        active = scan_sensitive._build_active_patterns(config)
        findings = scan_sensitive.scan_line("contact: person@fixture.invalid", active)
        labels = [f[2] for f in findings]
        assert "email address" not in labels

    def test_load_config_no_file(self, tmp_path):
        config = scan_sensitive._load_config(tmp_path)
        assert config["disable_patterns"] == []
        assert config["severity_overrides"] == {}
        assert config["custom_patterns"] == []

    def test_load_config_with_file(self, tmp_path):
        config_file = tmp_path / ".vet-config.json"
        config_file.write_text(json.dumps({
            "disable_patterns": ["test pattern"],
            "severity_overrides": {"another": "LOW"},
        }))
        config = scan_sensitive._load_config(tmp_path)
        assert config["disable_patterns"] == ["test pattern"]
        assert config["severity_overrides"] == {"another": "LOW"}

    def test_load_config_invalid_json(self, tmp_path):
        config_file = tmp_path / ".vet-config.json"
        config_file.write_text("not json {{{")
        config = scan_sensitive._load_config(tmp_path)
        # Falls back to defaults on parse error
        assert config["disable_patterns"] == []

    def test_config_in_main_integration(self, tmp_path, monkeypatch):
        """End-to-end: config file disables a pattern, main() respects it."""
        f = tmp_path / "bio.md"
        f.write_text("contact: person@fixture.invalid\n")
        config_file = tmp_path / ".vet-config.json"
        config_file.write_text(json.dumps({
            "disable_patterns": [
                "email address",
                "email address",
            ],
        }))
        monkeypatch.chdir(tmp_path)
        result = scan_sensitive.main(["--file", str(f)])
        assert result == scan_sensitive.EXIT_CLEAN

    def test_severity_override_in_main(self, tmp_path, monkeypatch):
        """End-to-end: severity override downgrades MEDIUM to LOW,
        --allow-warnings lets it through."""
        f = tmp_path / "fleet.md"
        f.write_text("host=fixture-node status=OK\n")
        config_file = tmp_path / ".vet-config.json"
        config_file.write_text(json.dumps({
            "severity_overrides": {"explicit host assignment": "LOW"},
        }))
        monkeypatch.chdir(tmp_path)
        # Without --allow-warnings, LOW still blocks by default
        result = scan_sensitive.main(["--file", str(f)])
        assert result == scan_sensitive.EXIT_BLOCKED
        # With --allow-warnings, LOW passes
        result = scan_sensitive.main(["--file", str(f), "--allow-warnings"])
        assert result == scan_sensitive.EXIT_CLEAN


# --- Scanning function tests ------------------------------------------------


class TestScanFile:
    """Test scan_file with real files."""

    def test_clean_file(self, tmp_path):
        f = tmp_path / "clean.md"
        f.write_text("# Clean doc\n\nNo sensitive content here.\n")
        findings = scan_sensitive.scan_file(f)
        assert findings == []

    def test_file_with_findings(self, tmp_path):
        f = tmp_path / "secret.md"
        f.write_text("# Config\n\nTOKEN=gho_abc123\nnode.example.ts.net\n")
        findings = scan_sensitive.scan_file(f)
        assert len(findings) >= 2
        severities = [f[1] for f in findings]
        assert scan_sensitive.CRITICAL in severities
        assert scan_sensitive.HIGH in severities

    def test_line_numbers_correct(self, tmp_path):
        f = tmp_path / "lined.md"
        f.write_text("line 1 clean\nline 2 clean\nline 3 has gho_token123\n")
        findings = scan_sensitive.scan_file(f)
        assert findings[0][0] == 3  # line number


class TestScanText:
    """Test scan_text with arbitrary strings."""

    def test_clean_text(self):
        findings = scan_sensitive.scan_text("Just a normal doc about governance.")
        assert findings == []

    def test_multiple_findings_one_line(self):
        findings = scan_sensitive.scan_text("ssh to node.example.ts.net with gho_abc123")
        assert len(findings) >= 2

    def test_multiline_text(self):
        text = "line 1 clean\nline 2 has gho_token\nline 3 clean\nline 4 has node.example.ts.net"
        findings = scan_sensitive.scan_text(text)
        assert len(findings) == 2
        assert findings[0][0] == 2  # line 2
        assert findings[1][0] == 4  # line 4


# --- Allowlist tests --------------------------------------------------------


class TestAllowlist:
    """Test .vet-allowlist file support."""

    def test_allowlist_exempts_file(self, tmp_path):
        allowlist = ["docs/REPO_STATUS_*.md"]
        assert scan_sensitive._is_allowlisted("docs/REPO_STATUS_DECISION.md", allowlist)

    def test_allowlist_does_not_match_unlisted(self, tmp_path):
        allowlist = ["docs/REPO_STATUS_*.md"]
        assert not scan_sensitive._is_allowlisted("docs/OTHER.md", allowlist)

    def test_allowlist_empty(self):
        assert not scan_sensitive._is_allowlisted("any/file.md", [])

    def test_load_allowlist_no_file(self, tmp_path):
        result = scan_sensitive._load_allowlist(tmp_path)
        assert result == []

    def test_load_allowlist_with_file(self, tmp_path):
        allowlist_file = tmp_path / ".vet-allowlist"
        allowlist_file.write_text("# Comment\ndocs/sensitive/*.md\nscripts/internal/*.py\n")
        result = scan_sensitive._load_allowlist(tmp_path)
        assert result == ["docs/sensitive/*.md", "scripts/internal/*.py"]


# --- CLI argument parsing tests ---------------------------------------------


class TestArgParsing:
    """Test _parse_args function."""

    def test_default_mode(self):
        mode, extra, allow_sensitive, allow_warnings = scan_sensitive._parse_args([])
        assert mode == "staged"
        assert allow_sensitive is False
        assert allow_warnings is False

    def test_allow_sensitive_flag(self):
        mode, extra, allow_sensitive, _ = scan_sensitive._parse_args(["--allow-sensitive"])
        assert allow_sensitive is True

    def test_allow_warnings_flag(self):
        mode, extra, _, allow_warnings = scan_sensitive._parse_args(["--allow-warnings"])
        assert allow_warnings is True

    def test_diff_mode(self):
        mode, extra, _, _ = scan_sensitive._parse_args(["--diff"])
        assert mode == "diff"

    def test_branch_mode_default_ref(self):
        mode, extra, _, _ = scan_sensitive._parse_args(["--branch"])
        assert mode == "branch"
        assert extra == ["origin/main"]

    def test_branch_mode_custom_ref(self):
        mode, extra, _, _ = scan_sensitive._parse_args(["--branch", "main"])
        assert mode == "branch"
        assert extra == ["main"]

    def test_file_mode(self):
        mode, extra, _, _ = scan_sensitive._parse_args(["--file", "docs/readme.md"])
        assert mode == "file"
        assert extra == ["docs/readme.md"]


# --- Integration: main() tests ----------------------------------------------


class TestMainIntegration:
    """Test main() function with real file scanning."""

    def test_clean_file_returns_zero(self, tmp_path, monkeypatch):
        f = tmp_path / "clean.md"
        f.write_text("# Clean\n\nNo issues.\n")
        monkeypatch.chdir(tmp_path)
        result = scan_sensitive.main(["--file", str(f)])
        assert result == scan_sensitive.EXIT_CLEAN

    def test_critical_finding_blocks(self, tmp_path, monkeypatch):
        f = tmp_path / "secret.md"
        f.write_text("token: gho_abc123\n")
        monkeypatch.chdir(tmp_path)
        result = scan_sensitive.main(["--file", str(f)])
        assert result == scan_sensitive.EXIT_BLOCKED

    def test_high_finding_blocks(self, tmp_path, monkeypatch):
        f = tmp_path / "infra.md"
        f.write_text("server at node.example.ts.net\n")
        monkeypatch.chdir(tmp_path)
        result = scan_sensitive.main(["--file", str(f)])
        assert result == scan_sensitive.EXIT_BLOCKED

    def test_medium_only_blocks_without_allow_warnings(self, tmp_path, monkeypatch):
        f = tmp_path / "fleet.md"
        f.write_text("host=fixture-node status=OK\n")
        monkeypatch.chdir(tmp_path)
        result = scan_sensitive.main(["--file", str(f)])
        assert result == scan_sensitive.EXIT_BLOCKED

    def test_medium_only_passes_with_allow_warnings(self, tmp_path, monkeypatch):
        f = tmp_path / "fleet.md"
        f.write_text("host=fixture-node status=OK\n")
        monkeypatch.chdir(tmp_path)
        result = scan_sensitive.main(["--file", str(f), "--allow-warnings"])
        assert result == scan_sensitive.EXIT_CLEAN

    def test_allow_sensitive_bypasses_everything(self, tmp_path, monkeypatch):
        f = tmp_path / "secret.md"
        f.write_text("gho_abc123 and node.example.ts.net\n")
        monkeypatch.chdir(tmp_path)
        result = scan_sensitive.main(["--file", str(f), "--allow-sensitive"])
        assert result == scan_sensitive.EXIT_CLEAN

    def test_skip_env_var_bypasses(self, tmp_path, monkeypatch):
        f = tmp_path / "secret.md"
        f.write_text("gho_abc123\n")
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("SKIP_SENSITIVE_SCAN", "1")
        result = scan_sensitive.main(["--file", str(f)])
        assert result == scan_sensitive.EXIT_CLEAN

    def test_allowlist_exempts_file(self, tmp_path, monkeypatch):
        f = tmp_path / "docs" / "REPO_STATUS.md"
        f.parent.mkdir()
        f.write_text("node.example.ts.net with gho_token123\n")
        allowlist = tmp_path / ".vet-allowlist"
        allowlist.write_text("docs/REPO_STATUS*.md\n")
        monkeypatch.chdir(tmp_path)
        result = scan_sensitive.main(["--file", "docs/REPO_STATUS.md"])
        assert result == scan_sensitive.EXIT_CLEAN

    def test_mixed_critical_and_medium_blocks(self, tmp_path, monkeypatch):
        f = tmp_path / "mixed.md"
        f.write_text("host=fixture-node status=OK\ntoken=gho_abc123\n")
        monkeypatch.chdir(tmp_path)
        result = scan_sensitive.main(["--file", str(f), "--allow-warnings"])
        assert result == scan_sensitive.EXIT_BLOCKED

    def test_low_only_blocks_without_allow_warnings(self, tmp_path, monkeypatch):
        f = tmp_path / "bio.md"
        f.write_text("contact: person@fixture.invalid\n")
        (tmp_path / ".vet-config.json").write_text(json.dumps({
            "severity_overrides": {"email address": "LOW"},
        }))
        monkeypatch.chdir(tmp_path)
        result = scan_sensitive.main(["--file", str(f)])
        assert result == scan_sensitive.EXIT_BLOCKED

    def test_low_only_passes_with_allow_warnings(self, tmp_path, monkeypatch):
        f = tmp_path / "bio.md"
        f.write_text("contact: person@fixture.invalid\n")
        (tmp_path / ".vet-config.json").write_text(json.dumps({
            "severity_overrides": {"email address": "LOW"},
        }))
        monkeypatch.chdir(tmp_path)
        result = scan_sensitive.main(["--file", str(f), "--allow-warnings"])
        assert result == scan_sensitive.EXIT_CLEAN
