"""Tests for the secret scanner module."""
import pathlib
import textwrap

from hummbl_sast.secret_scan import scan_file, scan_directory, summarize


def test_aws_access_key_detection(tmp_path):
    """AWS Access Key ID should be detected."""
    f = tmp_path / "test.py"
    f.write_text('aws_key = "AKIAIOSFODNN7EXAMPLE"')
    findings = scan_file(f)
    assert any(r.rule_id == "SEC002" and r.severity == "HIGH" for r in findings)


def test_github_token_detection(tmp_path):
    """GitHub token should be detected."""
    f = tmp_path / "test.py"
    f.write_text('token = "ghp_1234567890abcdefghijklmnopqrstuvwxyz"')
    findings = scan_file(f)
    assert any(r.rule_id == "SEC004" and r.severity == "HIGH" for r in findings)


def test_private_key_detection(tmp_path):
    """PEM private key should be detected."""
    f = tmp_path / "test.py"
    f.write_text("key = '''-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEA...\n-----END RSA PRIVATE KEY-----'''")
    findings = scan_file(f)
    assert any(r.rule_id == "SEC001" and r.severity == "HIGH" for r in findings)


def test_openai_key_detection(tmp_path):
    """OpenAI API key should be detected."""
    f = tmp_path / "test.py"
    f.write_text('api_key = "sk-proj-abcdefghijklmnopqrstuvwxyz1234567890ABCD"')
    findings = scan_file(f)
    assert any(r.rule_id == "SEC012" and r.severity == "HIGH" for r in findings)


def test_database_connection_string_detection(tmp_path):
    """Database connection string with credentials should be detected."""
    f = tmp_path / "test.py"
    f.write_text('url = "postgresql://user:secretpass@db.example.com:5432/mydb"')
    findings = scan_file(f)
    assert any(r.rule_id == "SEC030" and r.severity == "HIGH" for r in findings)


def test_hardcoded_password_detection(tmp_path):
    """Hardcoded password should be detected."""
    f = tmp_path / "test.py"
    f.write_text('password = "mysecret123"')
    findings = scan_file(f)
    assert any(r.rule_id == "SEC022" for r in findings)


def test_clean_file_no_findings(tmp_path):
    """A file without secrets should produce no findings."""
    f = tmp_path / "test.py"
    f.write_text('def hello():\n    return "hello world"')
    findings = scan_file(f)
    assert len(findings) == 0


def test_scan_directory(tmp_path):
    """scan_directory should find secrets across files."""
    (tmp_path / "a.py").write_text('key = "ghp_1234567890abcdefghijklmnopqrstuvwxyz"')
    (tmp_path / "b.py").write_text('aws = "AKIAIOSFODNN7EXAMPLE"')

    findings = scan_directory(tmp_path)
    rule_ids = {f.rule_id for f in findings}
    assert "SEC004" in rule_ids
    assert "SEC002" in rule_ids


def test_scan_directory_excludes_node_modules(tmp_path):
    """scan_directory should skip node_modules."""
    (tmp_path / "good.py").write_text('key = "ghp_1234567890abcdefghijklmnopqrstuvwxyz"')
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "bad.js").write_text('key = "ghp_1234567890abcdefghijklmnopqrstuvwxyz"')

    findings = scan_directory(tmp_path)
    assert all("node_modules" not in f.file for f in findings)


def test_redaction(tmp_path):
    """Findings should not contain the full secret value."""
    f = tmp_path / "test.py"
    secret = "ghp_1234567890abcdefghijklmnopqrstuvwxyz"
    f.write_text(f'token = "{secret}"')
    findings = scan_file(f)
    for finding in findings:
        if finding.rule_id == "SEC004":
            assert secret not in finding.redacted
            assert "***" in finding.redacted


def test_env_file_detection(tmp_path):
    """.env-style files should be scanned."""
    env_file = tmp_path / ".env"
    env_file.write_text("API_KEY=sk-ant-abcdefghijklmnopqrstuvwxyz1234567890ABCD")

    findings = scan_directory(tmp_path)
    assert len(findings) > 0
