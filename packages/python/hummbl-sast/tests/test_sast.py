"""Tests for the SAST scanner module."""
import pathlib
import tempfile
import textwrap

from hummbl_sast.sast import scan_file, scan_directory, summarize


def _write_tmp(content: str, tmpdir: pathlib.Path, name: str = "test.py") -> pathlib.Path:
    """Write content to a file in tmpdir and return the path."""
    fpath = tmpdir / name
    fpath.write_text(textwrap.dedent(content))
    return fpath


def test_eval_detection(tmp_path):
    """eval() should be detected as HIGH."""
    f = _write_tmp("x = eval('1 + 1')", tmp_path)
    findings = scan_file(f)
    assert any(r.rule_id == "S001" and r.severity == "HIGH" for r in findings)


def test_exec_detection(tmp_path):
    """exec() should be detected as HIGH."""
    f = _write_tmp("exec(\"print('hello')\")", tmp_path)
    findings = scan_file(f)
    assert any(r.rule_id == "S002" and r.severity == "HIGH" for r in findings)


def test_os_system_detection(tmp_path):
    """os.system() should be detected as HIGH."""
    f = _write_tmp("import os\nos.system('ls -la')", tmp_path)
    findings = scan_file(f)
    assert any(r.rule_id == "S004" and r.severity == "HIGH" for r in findings)


def test_subprocess_shell_true_detection(tmp_path):
    """subprocess.run(shell=True) should be detected as HIGH."""
    f = _write_tmp("import subprocess\nsubprocess.run('ls', shell=True)", tmp_path)
    findings = scan_file(f)
    assert any(r.rule_id == "S007" and r.severity == "HIGH" for r in findings)


def test_subprocess_shell_false_ok(tmp_path):
    """subprocess.run(shell=False) should not be flagged."""
    f = _write_tmp("import subprocess\nsubprocess.run(['ls', '-la'], shell=False)", tmp_path)
    findings = scan_file(f)
    assert not any(r.rule_id == "S007" for r in findings)


def test_pickle_detection(tmp_path):
    """pickle.loads() should be detected as HIGH."""
    f = _write_tmp("import pickle\ndata = pickle.loads(b'...')", tmp_path)
    findings = scan_file(f)
    assert any(r.rule_id == "S010" and r.severity == "HIGH" for r in findings)


def test_urllib_urlopen_detection(tmp_path):
    """urllib.request.urlopen() should be detected as MEDIUM."""
    f = _write_tmp('import urllib.request\nresp = urllib.request.urlopen("https://example.com")', tmp_path)
    findings = scan_file(f)
    assert any(r.rule_id == "S015" and r.severity == "MEDIUM" for r in findings)


def test_yaml_load_unsafe_detection(tmp_path):
    """yaml.load() without SafeLoader should be detected."""
    f = _write_tmp("import yaml\ndata = yaml.load(open('config.yaml'))", tmp_path)
    findings = scan_file(f)
    assert any(r.rule_id == "S014" for r in findings)


def test_yaml_load_safe_ok(tmp_path):
    """yaml.load() with SafeLoader should not be flagged."""
    f = _write_tmp("import yaml\ndata = yaml.load(open('config.yaml'), Loader=yaml.SafeLoader)", tmp_path)
    findings = scan_file(f)
    assert not any(r.rule_id == "S014" for r in findings)


def test_hardcoded_password_detection(tmp_path):
    """Hardcoded password should be detected."""
    f = _write_tmp('password = "mysecret123"', tmp_path)
    findings = scan_file(f)
    assert any(r.rule_id in ("S030", "S032") for r in findings)


def test_bind_all_interfaces_detection(tmp_path):
    """Binding to 0.0.0.0 should be detected."""
    f = _write_tmp('host = "0.0.0.0"', tmp_path)
    findings = scan_file(f)
    assert any(r.rule_id == "S041" for r in findings)


def test_md5_detection(tmp_path):
    """hashlib.md5() should be detected as MEDIUM."""
    f = _write_tmp("import hashlib\nh = hashlib.md5(b'data')", tmp_path)
    findings = scan_file(f)
    assert any(r.rule_id == "S017" and r.severity == "MEDIUM" for r in findings)


def test_assert_detection(tmp_path):
    """assert statements should be detected as LOW."""
    f = _write_tmp("x = 1\nassert x == 1", tmp_path)
    findings = scan_file(f)
    assert any(r.rule_id == "S050" and r.severity == "LOW" for r in findings)


def test_clean_file_no_findings(tmp_path):
    """A clean file should produce no findings."""
    f = _write_tmp('import json\ndef hello():\n    return json.dumps({"msg": "safe"})', tmp_path)
    findings = scan_file(f)
    assert len(findings) == 0


def test_scan_directory(tmp_path):
    """scan_directory should find issues across multiple files."""
    (tmp_path / "a.py").write_text("eval('x')")
    (tmp_path / "b.py").write_text("import os\nos.system('ls')")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "c.py").write_text("import pickle\npickle.loads(b'x')")

    findings = scan_directory(tmp_path)
    rule_ids = {f.rule_id for f in findings}
    assert "S001" in rule_ids  # eval
    assert "S004" in rule_ids  # os.system
    assert "S010" in rule_ids  # pickle


def test_scan_directory_excludes(tmp_path):
    """scan_directory should respect exclude_dirs."""
    (tmp_path / "good.py").write_text("eval('x')")
    (tmp_path / ".venv").mkdir()
    (tmp_path / ".venv" / "bad.py").write_text("eval('y')")

    findings = scan_directory(tmp_path)
    assert all(".venv" not in f.file for f in findings)


def test_summarize(tmp_path):
    """summarize should group by severity."""
    f = _write_tmp("eval('x')", tmp_path)
    findings = scan_file(f)
    summary = summarize(findings)
    assert summary["total"] >= 1
    assert summary["by_severity"]["HIGH"] >= 1


def test_syntax_error_no_crash(tmp_path):
    """Files with syntax errors should not crash the scanner."""
    f = _write_tmp("def broken(:\n  pass", tmp_path)
    findings = scan_file(f)
    assert findings == []
