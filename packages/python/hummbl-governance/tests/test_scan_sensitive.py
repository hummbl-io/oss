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
        findings = scan_sensitive.scan_line("cp ~/.ssh/id_ed25519_fleet /tmp/")
        severities = [f[0] for f in findings]
        assert scan_sensitive.CRITICAL in severities

    def test_ssn(self):
        findings = scan_sensitive.scan_line("SSN: 123-45-6789")
        severities = [f[0] for f in findings]
        assert scan_sensitive.CRITICAL in severities


class TestHighPatterns:
    """HIGH severity patterns — infrastructure details."""

    def test_hummbl_vps_hostname(self):
        findings = scan_sensitive.scan_line("ssh to hummbl-vps for deployment")
        severities = [f[0] for f in findings]
        assert scan_sensitive.HIGH in severities

    def test_ts_net_domain(self):
        findings = scan_sensitive.scan_line("anvil.tail093e19.ts.net")
        severities = [f[0] for f in findings]
        assert scan_sensitive.HIGH in severities

    def test_public_vps_ip(self):
        findings = scan_sensitive.scan_line("server at 5.161.114.121")
        severities = [f[0] for f in findings]
        assert scan_sensitive.HIGH in severities

    def test_delta_public_ip(self):
        findings = scan_sensitive.scan_line("delta is at 32.140.210.42")
        severities = [f[0] for f in findings]
        assert scan_sensitive.HIGH in severities

    def test_windows_user_path(self):
        findings = scan_sensitive.scan_line("Config at C:\\Users\\reuben\\.config")
        severities = [f[0] for f in findings]
        assert scan_sensitive.HIGH in severities

    def test_windows_user_path_case_insensitive(self):
        findings = scan_sensitive.scan_line("config at c:\\users\\reuben\\data")
        severities = [f[0] for f in findings]
        assert scan_sensitive.HIGH in severities

    def test_unix_home_path(self):
        findings = scan_sensitive.scan_line("cd /home/reuben/projects")
        severities = [f[0] for f in findings]
        assert scan_sensitive.HIGH in severities

    def test_opt_hummbl_path(self):
        findings = scan_sensitive.scan_line("bus at /opt/hummbl-governance/_state/")
        severities = [f[0] for f in findings]
        assert scan_sensitive.HIGH in severities

    def test_bus_cache_path(self):
        findings = scan_sensitive.scan_line("mirror at .cache/bus/messages.tsv")
        severities = [f[0] for f in findings]
        assert scan_sensitive.HIGH in severities

    def test_coordination_path(self):
        findings = scan_sensitive.scan_line("_state/coordination/messages.tsv")
        severities = [f[0] for f in findings]
        assert scan_sensitive.HIGH in severities

    def test_tailscale_ip(self):
        findings = scan_sensitive.scan_line("node at 100.64.0.1")
        severities = [f[0] for f in findings]
        assert scan_sensitive.HIGH in severities

    def test_mrn_phi(self):
        findings = scan_sensitive.scan_line("Patient MRN:123456")
        severities = [f[0] for f in findings]
        assert scan_sensitive.HIGH in severities

    def test_internal_port_in_context(self):
        findings = scan_sensitive.scan_line("bus port 18790 is open")
        severities = [f[0] for f in findings]
        assert scan_sensitive.HIGH in severities

    def test_internal_port_without_context_not_flagged(self):
        findings = scan_sensitive.scan_line("The number 18790 appeared")
        labels = [f[2] for f in findings]
        assert not any("port" in l.lower() for l in labels)


class TestMediumPatterns:
    """MEDIUM severity patterns — fleet hostnames, personal domains, emails."""

    def test_anvil_hostname_in_context(self):
        findings = scan_sensitive.scan_line("running on anvil today")
        severities = [f[0] for f in findings]
        assert scan_sensitive.MEDIUM in severities

    def test_anvil_hostname_host_equals(self):
        findings = scan_sensitive.scan_line("host=anvil status=OK")
        severities = [f[0] for f in findings]
        assert scan_sensitive.MEDIUM in severities

    def test_anvil_hostname_possessive(self):
        findings = scan_sensitive.scan_line("anvil's SQLite database")
        severities = [f[0] for f in findings]
        assert scan_sensitive.MEDIUM in severities

    def test_anvil_word_not_flagged(self):
        """The word 'anvil' as a tool/object should not be flagged."""
        findings = scan_sensitive.scan_line("The blacksmith struck the anvil with a hammer")
        labels = [f[2] for f in findings]
        assert not any("anvil" in l for l in labels)

    def test_delta_hostname_in_context(self):
        findings = scan_sensitive.scan_line("host=delta session started")
        severities = [f[0] for f in findings]
        assert scan_sensitive.MEDIUM in severities

    def test_delta_hostname_devin_delta(self):
        findings = scan_sensitive.scan_line("prior session (devin-delta) closed")
        severities = [f[0] for f in findings]
        assert scan_sensitive.MEDIUM in severities

    def test_delta_word_not_flagged(self):
        """The word 'delta' meaning 'difference' should not be flagged."""
        findings = scan_sensitive.scan_line("- **Delta**: No content delta.")
        labels = [f[2] for f in findings]
        assert not any("delta" in l.lower() for l in labels)

    def test_huxley_hostname_in_context(self):
        findings = scan_sensitive.scan_line("huxley is offline")
        severities = [f[0] for f in findings]
        assert scan_sensitive.MEDIUM in severities

    def test_huxley_hostname_author_tag(self):
        findings = scan_sensitive.scan_line("**Author:** Devin (Huxley)")
        severities = [f[0] for f in findings]
        assert scan_sensitive.MEDIUM in severities

    def test_slate_hostname_in_context(self):
        findings = scan_sensitive.scan_line("host=slate mesh watch")
        severities = [f[0] for f in findings]
        assert scan_sensitive.MEDIUM in severities

    def test_nodezero_hostname(self):
        findings = scan_sensitive.scan_line("nodezero dormant since July")
        severities = [f[0] for f in findings]
        assert scan_sensitive.MEDIUM in severities

    def test_rpbx_domain(self):
        findings = scan_sensitive.scan_line("previously owned rpbx.net")
        severities = [f[0] for f in findings]
        assert scan_sensitive.MEDIUM in severities

    def test_email_address(self):
        findings = scan_sensitive.scan_line("contact: user@notexample.org")
        severities = [f[0] for f in findings]
        assert scan_sensitive.MEDIUM in severities

    def test_email_address_example_com_excluded(self):
        """RFC 2606 reserved example domains should not be flagged."""
        findings = scan_sensitive.scan_line("contact: user@example.com")
        severities = [f[0] for f in findings]
        assert scan_sensitive.MEDIUM not in severities

    def test_email_address_git_github_excluded(self):
        """git@github.com is an SSH protocol string, not an email address."""
        findings = scan_sensitive.scan_line("if raw.startswith(\"git@github.com:\"):")
        severities = [f[0] for f in findings]
        assert scan_sensitive.MEDIUM not in severities

    def test_phone_number(self):
        findings = scan_sensitive.scan_line("call 555-123-4567")
        severities = [f[0] for f in findings]
        assert scan_sensitive.MEDIUM in severities

    def test_phone_number_dots(self):
        findings = scan_sensitive.scan_line("call 555.123.4567")
        severities = [f[0] for f in findings]
        assert scan_sensitive.MEDIUM in severities

    def test_phone_number_no_separators_not_flagged(self):
        """10-digit numbers without separators are likely timestamps/IDs, not phone numbers."""
        findings = scan_sensitive.scan_line("timestamp 1719600901")
        labels = [f[2] for f in findings]
        assert not any("phone" in l.lower() for l in labels)


class TestLowPatterns:
    """LOW severity patterns — personal names."""

    def test_full_name_reuben_paul_bowlby(self):
        findings = scan_sensitive.scan_line("Authored by Reuben Paul Bowlby")
        severities = [f[0] for f in findings]
        assert scan_sensitive.LOW in severities

    def test_full_name_reuben_bowlby(self):
        findings = scan_sensitive.scan_line("Reuben Bowlby committed this")
        severities = [f[0] for f in findings]
        assert scan_sensitive.LOW in severities

    def test_paul_verderber(self):
        findings = scan_sensitive.scan_line("Paul Verderber was his grandfather")
        severities = [f[0] for f in findings]
        assert scan_sensitive.LOW in severities


# --- Config system tests ----------------------------------------------------


class TestConfigSystem:
    """Test .vet-config.json support — disable, override, custom patterns."""

    def test_disable_pattern_by_label(self):
        config = {
            "disable_patterns": ["full name 'Reuben Paul Bowlby'"],
            "severity_overrides": {},
            "custom_patterns": [],
        }
        active = scan_sensitive._build_active_patterns(config)
        labels = [p[2] for p in active]
        assert "full name 'Reuben Paul Bowlby'" not in labels

    def test_severity_override(self):
        config = {
            "disable_patterns": [],
            "severity_overrides": {"fleet hostname 'anvil'": "LOW"},
            "custom_patterns": [],
        }
        active = scan_sensitive._build_active_patterns(config)
        anvil = [p for p in active if p[2] == "fleet hostname 'anvil'"]
        assert len(anvil) == 1
        assert anvil[0][0] == "LOW"

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
            "disable_patterns": ["full name 'Reuben Paul Bowlby'"],
            "severity_overrides": {},
            "custom_patterns": [],
        }
        active = scan_sensitive._build_active_patterns(config)
        findings = scan_sensitive.scan_line("Authored by Reuben Paul Bowlby", active)
        labels = [f[2] for f in findings]
        assert "full name 'Reuben Paul Bowlby'" not in labels

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
        f.write_text("Authored by Reuben Paul Bowlby\n")
        config_file = tmp_path / ".vet-config.json"
        config_file.write_text(json.dumps({
            "disable_patterns": [
                "full name 'Reuben Paul Bowlby'",
                "full name 'Reuben Bowlby'",
            ],
        }))
        monkeypatch.chdir(tmp_path)
        result = scan_sensitive.main(["--file", str(f)])
        assert result == scan_sensitive.EXIT_CLEAN

    def test_severity_override_in_main(self, tmp_path, monkeypatch):
        """End-to-end: severity override downgrades MEDIUM to LOW,
        --allow-warnings lets it through."""
        f = tmp_path / "fleet.md"
        f.write_text("host=anvil status=OK\n")
        config_file = tmp_path / ".vet-config.json"
        config_file.write_text(json.dumps({
            "severity_overrides": {"fleet hostname 'anvil'": "LOW"},
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
        f.write_text("# Config\n\nTOKEN=gho_abc123\nhost=hummbl-vps\n")
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
        findings = scan_sensitive.scan_text("ssh to hummbl-vps with gho_abc123")
        assert len(findings) >= 2

    def test_multiline_text(self):
        text = "line 1 clean\nline 2 has gho_token\nline 3 clean\nline 4 has 5.161.114.121"
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
        f.write_text("server at 5.161.114.121\n")
        monkeypatch.chdir(tmp_path)
        result = scan_sensitive.main(["--file", str(f)])
        assert result == scan_sensitive.EXIT_BLOCKED

    def test_medium_only_blocks_without_allow_warnings(self, tmp_path, monkeypatch):
        f = tmp_path / "fleet.md"
        f.write_text("host=anvil status=OK\n")
        monkeypatch.chdir(tmp_path)
        result = scan_sensitive.main(["--file", str(f)])
        assert result == scan_sensitive.EXIT_BLOCKED

    def test_medium_only_passes_with_allow_warnings(self, tmp_path, monkeypatch):
        f = tmp_path / "fleet.md"
        f.write_text("host=anvil status=OK\n")
        monkeypatch.chdir(tmp_path)
        result = scan_sensitive.main(["--file", str(f), "--allow-warnings"])
        assert result == scan_sensitive.EXIT_CLEAN

    def test_allow_sensitive_bypasses_everything(self, tmp_path, monkeypatch):
        f = tmp_path / "secret.md"
        f.write_text("gho_abc123 and 5.161.114.121\n")
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
        f.write_text("host=hummbl-vps with gho_token123\n")
        allowlist = tmp_path / ".vet-allowlist"
        allowlist.write_text("docs/REPO_STATUS*.md\n")
        monkeypatch.chdir(tmp_path)
        result = scan_sensitive.main(["--file", "docs/REPO_STATUS.md"])
        assert result == scan_sensitive.EXIT_CLEAN

    def test_mixed_critical_and_medium_blocks(self, tmp_path, monkeypatch):
        f = tmp_path / "mixed.md"
        f.write_text("host=anvil status=OK\ntoken=gho_abc123\n")
        monkeypatch.chdir(tmp_path)
        result = scan_sensitive.main(["--file", str(f), "--allow-warnings"])
        assert result == scan_sensitive.EXIT_BLOCKED

    def test_low_only_blocks_without_allow_warnings(self, tmp_path, monkeypatch):
        f = tmp_path / "bio.md"
        f.write_text("Authored by Reuben Paul Bowlby\n")
        monkeypatch.chdir(tmp_path)
        result = scan_sensitive.main(["--file", str(f)])
        assert result == scan_sensitive.EXIT_BLOCKED

    def test_low_only_passes_with_allow_warnings(self, tmp_path, monkeypatch):
        f = tmp_path / "bio.md"
        f.write_text("Authored by Reuben Paul Bowlby\n")
        monkeypatch.chdir(tmp_path)
        result = scan_sensitive.main(["--file", str(f), "--allow-warnings"])
        assert result == scan_sensitive.EXIT_CLEAN
