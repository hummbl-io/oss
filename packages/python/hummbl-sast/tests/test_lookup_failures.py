"""An unavailable vulnerability service must not produce a clean result."""

import json
from unittest.mock import MagicMock, patch
from urllib.error import URLError

import pytest

from hummbl_sast.cli import main
from hummbl_sast.dep_audit import DependencyAuditError, query_osv


@pytest.mark.parametrize("error", [URLError("offline"), TimeoutError("timed out")])
def test_network_failure_is_distinct_from_no_vulnerabilities(error):
    with patch("hummbl_sast.dep_audit.urllib.request.urlopen", side_effect=error):
        with pytest.raises(DependencyAuditError, match="did not complete"):
            query_osv("example-package", "1.0", "PyPI")


@pytest.mark.parametrize("payload", [b"not-json", b"[]", b'{"vulns": null}', b'{"vulns": [42]}'])
def test_malformed_lookup_is_an_error(payload):
    response = MagicMock()
    response.__enter__.return_value.read.return_value = payload
    with patch("hummbl_sast.dep_audit.urllib.request.urlopen", return_value=response):
        with pytest.raises(DependencyAuditError):
            query_osv("example-package", "1.0", "PyPI")


def test_successful_empty_lookup_remains_empty():
    response = MagicMock()
    response.__enter__.return_value.read.return_value = b"{}"
    with patch("hummbl_sast.dep_audit.urllib.request.urlopen", return_value=response):
        assert query_osv("example-package", "1.0", "PyPI") == []


@pytest.mark.parametrize("mode", ["deps", "all"])
def test_cli_returns_incomplete_for_offline_lookup(mode, tmp_path, capsys):
    (tmp_path / "requirements.txt").write_text("example-package==1.0\n", encoding="utf-8")
    arguments = [mode, str(tmp_path), "--rate-limit", "0"]
    if mode == "deps":
        arguments.append("--json")
    with patch("hummbl_sast.dep_audit.urllib.request.urlopen", side_effect=URLError("offline")):
        assert main(arguments) == 2
    captured = capsys.readouterr()
    if mode == "deps":
        output = json.loads(captured.out)
        assert output["status"] == "incomplete"
        assert "summary" not in output
    else:
        assert "Dependency audit incomplete:" in captured.err
